import ast
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

import numpy as np
import torch

from __version__ import VERSION
from demucs.pretrained import get_model
from demucs.repo import ModelLoadingError
from lib_v5 import spec_utils
from lib_v5.tfc_tdf_v3 import STFT
from separate import (
    backend_output_to_tensor,
    load_mdx_checkpoint,
    output_path_for_format,
    prepare_mix,
    select_onnx_providers,
    vr_denoiser,
)


class CoreCompatibilityTests(unittest.TestCase):
    @staticmethod
    def _top_level_imports(path):
        imports = []
        for node in ast.parse(path.read_text(encoding='utf-8')).body:
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        return imports

    def test_uvr_initializes_torch_before_native_gui_and_audio_imports(self):
        imports = self._top_level_imports(Path(__file__).resolve().parents[1] / 'UVR.py')
        self.assertIn('torch', imports)
        torch_index = imports.index('torch')
        for module_name in ('audioread', 'gui_data.sv_ttk', 'librosa', 'pyglet'):
            self.assertIn(module_name, imports)
            self.assertLess(torch_index, imports.index(module_name))

    def test_separator_initializes_torch_before_native_inference_libraries(self):
        imports = self._top_level_imports(Path(__file__).resolve().parents[1] / 'separate.py')
        self.assertIn('torch', imports)
        torch_index = imports.index('torch')
        for module_name in ('scipy', 'audioread', 'librosa', 'onnxruntime'):
            self.assertIn(module_name, imports)
            self.assertLess(torch_index, imports.index(module_name))

    def test_pillow_resize_uses_supported_resampling_api(self):
        source = (
            Path(__file__).resolve().parents[1] / 'gui_data' / 'app_size_values.py'
        ).read_text(encoding='utf-8')
        self.assertNotIn('Image.ANTIALIAS', source)
        self.assertIn('Image.Resampling.LANCZOS', source)

    def test_release_version(self):
        self.assertEqual(VERSION, 'v6.0.0')

    def test_windows_installer_upgrades_original_release(self):
        installer = Path(__file__).resolve().parents[1] / 'UVR-Windows.iss'
        definition = installer.read_text(encoding='utf-8')
        self.assertIn('AppVersion={#AppVersion}', definition)
        self.assertIn('AppId={{652AA21C-E084-435C-8ED9-4A29AC2731F1}', definition)
        self.assertIn('Name: "{app}\\UVR.exe"', definition)
        self.assertIn('Name: "{app}\\UVR_Launcher.exe"', definition)

    def test_windows_builder_validates_every_bundled_binary(self):
        builder = Path(__file__).resolve().parents[1] / 'build_windows.ps1'
        definition = builder.read_text(encoding='utf-8')
        self.assertIn("$SndFileLibrary = Join-Path $BinaryDirectory 'sndfile.dll'", definition)
        self.assertIn(
            'Test-Path -LiteralPath $FfmpegExecutable -PathType Leaf',
            definition,
        )
        self.assertIn(
            'Test-Path -LiteralPath $RubberBandExecutable -PathType Leaf',
            definition,
        )
        self.assertIn(
            'Test-Path -LiteralPath $SndFileLibrary -PathType Leaf',
            definition,
        )
        self.assertIn('$RequiredBinaries = @(', definition)
        self.assertIn('Required bundled binary is missing:', definition)

    def test_missing_demucs_repository_reports_model_loading_error(self):
        with TemporaryDirectory() as directory:
            missing_repository = Path(directory) / 'missing-models'

            with self.assertRaisesRegex(ModelLoadingError, 'must exist'):
                get_model('missing-model', repo=missing_repository)

    def test_stft_round_trip_is_finite(self):
        audio = torch.randn(1, 2, 44_100)
        transform = STFT(2_048, 1_024, 1_025, torch.device('cpu'))

        reconstructed = transform.inverse(transform(audio))

        self.assertEqual(reconstructed.shape[:2], audio.shape[:2])
        self.assertTrue(torch.isfinite(reconstructed).all())

    def test_modern_librosa_resampling_path(self):
        audio = np.random.default_rng(0).normal(size=(2, 22_050)).astype(np.float32)

        shifted, sample_rate = spec_utils.change_pitch_semitones(audio, 44_100, 1)

        self.assertEqual(shifted.shape[0], 2)
        self.assertGreater(sample_rate, 44_100)
        self.assertTrue(np.isfinite(shifted).all())

    def test_bundled_state_dicts_use_safe_torch_loader(self):
        vr_model = torch.load(
            'models/VR_Models/UVR-DeNoise-Lite.pth',
            map_location='cpu',
            weights_only=True,
        )
        mixer = torch.load('lib_v5/mixer.ckpt', map_location='cpu', weights_only=True)

        self.assertGreater(len(vr_model), 0)
        self.assertGreater(len(mixer), 0)

    @patch('separate.MdxnetSet.ConvTDFNet')
    @patch('separate.torch.load')
    def test_mdx_checkpoint_loads_state_dict_into_plain_module(
        self,
        torch_load,
        conv_tdf_net,
    ):
        model_params = {
            'dim_c': 4,
            'hop_length': 1024,
        }
        state_dict = {'first_conv.0.weight': torch.ones(1)}
        model = Mock()
        model.to.return_value = model
        model.eval.return_value = model
        conv_tdf_net.return_value = model
        torch_load.return_value = {
            'hyper_parameters': model_params,
            'state_dict': state_dict,
        }

        loaded_params, loaded_model = load_mdx_checkpoint(
            'model.ckpt',
            torch.device('cpu'),
        )

        torch_load.assert_called_once_with(
            'model.ckpt',
            map_location='cpu',
            weights_only=True,
        )
        conv_tdf_net.assert_called_once_with(**model_params)
        model.load_state_dict.assert_called_once_with(state_dict)
        model.to.assert_called_once_with(torch.device('cpu'))
        model.eval.assert_called_once_with()
        self.assertIs(loaded_params, model_params)
        self.assertIs(loaded_model, model)

    def test_bundled_vr_model_runs_inference(self):
        audio = np.random.default_rng(1).normal(
            0,
            0.01,
            size=(2, 132_300),
        ).astype(np.float32)
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        output = vr_denoiser(
            audio,
            device,
            model_path='models/VR_Models/UVR-DeNoise-Lite.pth',
        )

        self.assertEqual(output.shape, audio.shape)
        self.assertTrue(np.isfinite(output).all())

    def test_vr_denoiser_preserves_finite_silence(self):
        audio = np.zeros((2, 44_100), dtype=np.float32)
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        output = vr_denoiser(
            audio,
            device,
            model_path='models/VR_Models/UVR-DeNoise-Lite.pth',
        )

        self.assertEqual(output.shape, audio.shape)
        self.assertTrue(np.isfinite(output).all())
        self.assertTrue(np.allclose(output, 0))

    def test_mdx_tensor_output_is_not_copied_through_cpu(self):
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        output = torch.ones((1, 2, 4, 4), device=device)

        converted = backend_output_to_tensor(output, device)

        self.assertEqual(converted.device, output.device)
        self.assertEqual(converted.data_ptr(), output.data_ptr())

    def test_prepare_mix_accepts_channel_first_and_sample_first_arrays(self):
        channel_first = np.ones((2, 100), dtype=np.float32)
        sample_first = channel_first.T

        prepared_channel_first = prepare_mix(channel_first)
        prepared_sample_first = prepare_mix(sample_first)

        self.assertEqual(prepared_channel_first.shape, (2, 100))
        self.assertEqual(prepared_sample_first.shape, (2, 100))
        self.assertTrue(prepared_channel_first.flags['F_CONTIGUOUS'])
        self.assertTrue(prepared_sample_first.flags['F_CONTIGUOUS'])

    def test_prepare_mix_expands_mono_arrays_to_stereo(self):
        mono = np.ones((1, 100), dtype=np.float32)

        prepared = prepare_mix(mono)

        self.assertEqual(prepared.shape, (2, 100))
        np.testing.assert_array_equal(prepared[0], prepared[1])

    def test_prepare_mix_preserves_very_short_channel_first_audio(self):
        stereo = np.array([[0.25], [-0.25]], dtype=np.float32)

        prepared = prepare_mix(stereo)

        self.assertEqual(prepared.shape, (2, 1))
        np.testing.assert_array_equal(prepared, stereo)

    def test_prepare_mix_rejects_unsupported_channel_counts(self):
        for audio in (
            np.ones((3, 100), dtype=np.float32),
            np.ones((100, 3), dtype=np.float32),
            np.ones((2, 3, 100), dtype=np.float32),
        ):
            with self.subTest(shape=audio.shape):
                with self.assertRaisesRegex(ValueError, 'one.*two'):
                    prepare_mix(audio)

    @patch('separate.librosa.load')
    def test_prepare_mix_rejects_multichannel_decoded_files(self, librosa_load):
        librosa_load.return_value = (np.ones((3, 100), dtype=np.float32), 44_100)

        with self.assertRaisesRegex(ValueError, 'one or two channels'):
            prepare_mix('multichannel.wav')

    def test_prepare_mix_rejects_empty_audio(self):
        for audio in (
            np.array([], dtype=np.float32),
            np.empty((2, 0), dtype=np.float32),
        ):
            with self.subTest(shape=audio.shape):
                with self.assertRaisesRegex(ValueError, 'at least one sample'):
                    prepare_mix(audio)

    def test_prepare_mix_rejects_non_finite_audio(self):
        for invalid_value in (np.nan, np.inf, -np.inf):
            audio = np.ones((2, 100), dtype=np.float32)
            audio[0, 10] = invalid_value

            with self.subTest(invalid_value=invalid_value):
                with self.assertRaisesRegex(ValueError, 'non-finite'):
                    prepare_mix(audio)

    def test_output_conversion_replaces_only_the_final_suffix(self):
        audio_path = str(Path('folder.wav') / 'Track.WAV')

        mp3_path = output_path_for_format(audio_path, 'MP3')
        flac_path = output_path_for_format(audio_path, 'FLAC')

        self.assertEqual(mp3_path, str(Path('folder.wav') / 'Track.mp3'))
        self.assertEqual(flac_path, str(Path('folder.wav') / 'Track.flac'))

    @patch('separate.rerun_mp3')
    @patch('separate.librosa.load')
    def test_prepare_mix_retries_uppercase_mp3_files(self, librosa_load, rerun_mp3):
        librosa_load.return_value = (np.zeros((2, 100), dtype=np.float32), 44_100)
        rerun_mp3.return_value = np.ones((2, 100), dtype=np.float32)

        prepared = prepare_mix('silent-decode.MP3')

        rerun_mp3.assert_called_once_with('silent-decode.MP3')
        self.assertTrue(np.all(prepared == 1))

    @patch('separate.ort.get_available_providers')
    def test_onnx_cuda_provider_keeps_cpu_fallback(self, available_providers):
        available_providers.return_value = [
            'CUDAExecutionProvider',
            'CPUExecutionProvider',
        ]

        providers = select_onnx_providers(use_cuda=True)

        self.assertEqual(
            providers,
            ['CUDAExecutionProvider', 'CPUExecutionProvider'],
        )

    @patch('separate.ort.get_available_providers')
    def test_onnx_provider_falls_back_when_cuda_is_unavailable(
        self,
        available_providers,
    ):
        available_providers.return_value = ['CPUExecutionProvider']

        providers = select_onnx_providers(use_cuda=True)

        self.assertEqual(providers, ['CPUExecutionProvider'])


if __name__ == '__main__':
    unittest.main()

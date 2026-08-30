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
from separate import backend_output_to_tensor, load_mdx_checkpoint, vr_denoiser


class CoreCompatibilityTests(unittest.TestCase):
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


if __name__ == '__main__':
    unittest.main()

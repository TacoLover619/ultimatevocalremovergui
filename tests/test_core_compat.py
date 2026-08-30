import unittest

import numpy as np
import torch

from __version__ import VERSION
from lib_v5 import spec_utils
from lib_v5.tfc_tdf_v3 import STFT
from separate import vr_denoiser


class CoreCompatibilityTests(unittest.TestCase):
    def test_release_version(self):
        self.assertEqual(VERSION, 'v6.0.0')

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


if __name__ == '__main__':
    unittest.main()

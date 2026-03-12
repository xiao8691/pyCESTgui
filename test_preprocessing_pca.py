import unittest

import numpy as np

from src.modules.preprocessing import Preprocessing


class TestPreprocessingPCA(unittest.TestCase):
    def test_single_slice_mp_pca_reduces_noise(self):
        rng = np.random.default_rng(7)

        x = np.linspace(-1.0, 1.0, 18)
        y = np.linspace(-1.0, 1.0, 18)
        offsets = np.linspace(-4.0, 4.0, 16)

        xx, yy = np.meshgrid(x, y, indexing='ij')
        spatial = np.exp(-(xx ** 2 + yy ** 2) / 0.5)
        spectral = 1.0 - 0.2 * np.exp(-(offsets ** 2) / 3.0)
        clean = spatial[:, :, None, None] * spectral[None, None, None, :]

        noisy = clean + rng.normal(0.0, 0.08, size=clean.shape)
        denoised = Preprocessing.pca_denoise(noisy, patch_radius=1)

        self.assertEqual(noisy.shape, denoised.shape)
        self.assertTrue(np.isfinite(denoised).all())
        self.assertGreater(np.linalg.norm(denoised), 0.0)

        noisy_mse = np.mean((noisy - clean) ** 2)
        denoised_mse = np.mean((denoised - clean) ** 2)
        self.assertLess(denoised_mse, noisy_mse)

    def test_global_pca_mode_still_available(self):
        rng = np.random.default_rng(11)
        data = rng.normal(size=(12, 12, 10))

        denoised = Preprocessing.pca_denoise(data, n_components=6)

        self.assertEqual(data.shape, denoised.shape)
        self.assertTrue(np.isfinite(denoised).all())


if __name__ == '__main__':
    unittest.main()
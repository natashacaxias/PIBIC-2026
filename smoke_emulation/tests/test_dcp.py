import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import cv2
    from dcp import dark_channel, dehaze, dehaze_sequence, estimate_atmospheric_light, guided_filter
    from koschmieder import apply_smoke
except ImportError:
    cv2 = None


def colorful_scene(seed=0, shape=(96, 128)):
    """Cena sem névoa: blocos de cores saturadas (dark channel próximo de zero, como na prior)."""
    rng = np.random.default_rng(seed)
    blocks = rng.integers(0, 3, size=(shape[0] // 16, shape[1] // 16))
    img = np.zeros(shape + (3,), np.uint8)
    for i in range(blocks.shape[0]):
        for j in range(blocks.shape[1]):
            color = np.full(3, 20)
            color[blocks[i, j]] = 200 + rng.integers(0, 50)
            img[i * 16:(i + 1) * 16, j * 16:(j + 1) * 16] = color
    return img


@unittest.skipIf(cv2 is None, "OpenCV não instalado")
class DarkChannelPriorTest(unittest.TestCase):
    def setUp(self):
        self.clean = colorful_scene()
        depth = np.tile(np.linspace(1.0, 4.0, self.clean.shape[1]), (self.clean.shape[0], 1))
        self.hazy = apply_smoke(self.clean, depth, beta=0.3, atmospheric_light=(0.8, 0.8, 0.8))

    def test_dark_channel_is_low_for_clean_and_high_for_hazy(self):
        self.assertLess(dark_channel(self.clean / 255.0).mean(), 0.1)
        self.assertGreater(dark_channel(self.hazy / 255.0).mean(), 0.3)

    def test_airlight_close_to_true_smoke_color_when_some_region_is_opaque(self):
        depth = np.tile(np.linspace(1.0, 20.0, self.clean.shape[1]), (self.clean.shape[0], 1))
        image = apply_smoke(self.clean, depth, beta=0.3, atmospheric_light=(0.8, 0.8, 0.8)) / 255.0
        airlight = estimate_atmospheric_light(image, dark_channel(image))
        self.assertTrue(np.all(np.abs(airlight - 0.8) < 0.05), airlight)

    def test_airlight_biased_by_scene_color_in_shallow_indoor_scene(self):
        # Até 4 m com beta=0.3 nenhuma região fica opaca (t >= 0.3): a prior do DCP
        # superestima a cor da cena. Comportamento esperado; documentado em docs/.
        image = self.hazy / 255.0
        airlight = estimate_atmospheric_light(image, dark_channel(image))
        self.assertGreater(np.ptp(airlight), 0.1)

    def test_dehazing_moves_image_towards_clean_scene(self):
        out, _, mean_t = dehaze(self.hazy, patch=7, radius=15)
        err_hazy = np.abs(self.hazy.astype(float) - self.clean).mean()
        err_out = np.abs(out.astype(float) - self.clean).mean()
        self.assertLess(err_out, 0.6 * err_hazy)
        self.assertGreater(mean_t, 0.1)
        self.assertEqual(out.dtype, np.uint8)

    def test_guided_filter_keeps_constant_signal(self):
        guide = np.random.default_rng(1).random((32, 32))
        np.testing.assert_allclose(guided_filter(guide, np.full((32, 32), 0.4), radius=4), 0.4, atol=1e-6)

    def test_sequence_uses_one_airlight(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "in").mkdir()
            for i in range(3):
                cv2.imwrite(str(root / "in" / f"{i:04d}.png"), cv2.cvtColor(self.hazy, cv2.COLOR_RGB2BGR))
            meta = dehaze_sequence(root / "in", root / "out", patch=7, radius=15)
            self.assertEqual(meta["n_frames"], 3)
            self.assertEqual(meta["airlight_rgb_std"], [0.0, 0.0, 0.0])
            saved = json.loads((root / "out" / "dcp_meta.json").read_text())
            self.assertEqual(saved["airlight_mode"], "sequence")
            self.assertTrue((root / "out" / "0002.png").exists())


if __name__ == "__main__":
    unittest.main()

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

try:
    import cv2
    import scipy  # noqa: F401
    from image_quality import frame_metrics, ssim, to_gray
    from koschmieder import apply_smoke
except ImportError:
    cv2 = None


def textured_scene(seed=0, shape=(120, 160)):
    rng = np.random.default_rng(seed)
    base = cv2.resize(rng.integers(0, 256, (shape[0] // 8, shape[1] // 8, 3), dtype=np.uint8), shape[::-1],
                      interpolation=cv2.INTER_NEAREST)
    return base


@unittest.skipIf(cv2 is None, "OpenCV/SciPy não instalados")
class ImageQualityTest(unittest.TestCase):
    def setUp(self):
        self.clean = textured_scene()
        depth = np.full(self.clean.shape[:2], 3.0)
        self.light = apply_smoke(self.clean, depth, beta=3.912 / 60)
        self.dense = apply_smoke(self.clean, depth, beta=3.912 / 6)

    def test_metrics_move_monotonically_with_smoke(self):
        m = [frame_metrics(img) for img in (self.clean, self.light, self.dense)]
        for key in ("rms_contrast", "edge_density", "orb_keypoints"):
            self.assertGreater(m[0][key], m[2][key], key)
            self.assertGreaterEqual(m[1][key], m[2][key], key)
        self.assertLess(m[0]["dark_channel_mean"], m[1]["dark_channel_mean"])
        self.assertLess(m[1]["dark_channel_mean"], m[2]["dark_channel_mean"])

    def test_ssim_identity_and_ordering(self):
        g = to_gray(self.clean)
        self.assertAlmostEqual(ssim(g, g), 1.0, places=6)
        self.assertGreater(ssim(g, to_gray(self.light)), ssim(g, to_gray(self.dense)))

    def test_cli_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, imgs in (("clean", [self.clean]), ("synthetic", [self.dense]), ("real", [self.dense, self.light])):
                (root / name).mkdir()
                for i, img in enumerate(imgs * 3):
                    cv2.imwrite(str(root / name / f"{i:04d}.png"), cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
            subprocess.run([sys.executable, str(HERE / "validate_smoke.py"), "--synthetic", str(root / "synthetic"),
                            "--real", str(root / "real"), "--clean", str(root / "clean"), "--out", str(root / "out"),
                            "--size", "160", "120"], check=True, cwd=HERE, capture_output=True)
            report = (root / "out" / "report.md").read_text()
            self.assertIn("rms_contrast", report)
            self.assertIn("SSIM sintético × limpo", report)
            self.assertTrue((root / "out" / "comparison.csv").exists())


if __name__ == "__main__":
    unittest.main()

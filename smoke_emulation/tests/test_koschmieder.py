import math
import os
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from koschmieder import (  # noqa: E402
    apply_smoke,
    beta_for_mean_transmission,
    beta_from_visibility,
    fill_depth_holes,
    mean_transmission,
    transmission,
    visibility_from_beta,
)

try:
    import cv2
    from emulate_sequence import emulate_sequence
except ImportError:
    cv2 = None


class VisibilityTest(unittest.TestCase):
    def test_beta_matches_proposal_constant(self):
        self.assertAlmostEqual(beta_from_visibility(20.0), 3.912 / 20.0, places=3)

    def test_round_trip(self):
        self.assertAlmostEqual(visibility_from_beta(beta_from_visibility(6.0)), 6.0)

    def test_transmission_at_visibility_is_threshold(self):
        beta = beta_from_visibility(60.0)
        self.assertAlmostEqual(float(transmission(60.0, beta)), 0.02)

    def test_rejects_non_positive(self):
        with self.assertRaises(ValueError):
            beta_from_visibility(0.0)


class DepthHolesTest(unittest.TestCase):
    def test_holes_get_max_valid_depth(self):
        depth = np.array([[0.0, 2.0], [np.nan, 4.0]])
        filled = fill_depth_holes(depth)
        np.testing.assert_array_equal(filled, [[4.0, 2.0], [4.0, 4.0]])

    def test_all_invalid_raises(self):
        with self.assertRaises(ValueError):
            fill_depth_holes(np.zeros((2, 2)))

    def test_dilate_uses_local_background_not_global_max(self):
        depth = np.array([[1.0, 1.0, 9.0, 9.0],
                          [1.0, 0.0, 9.0, 9.0],
                          [1.0, 1.0, 9.0, 9.0]])
        self.assertEqual(fill_depth_holes(depth)[1, 1], 9.0)
        far_hole = np.full((3, 7), 2.0)
        far_hole[:, 0] = 5.0
        far_hole[1, 6] = 0.0
        self.assertEqual(fill_depth_holes(far_hole)[1, 6], 2.0)
        self.assertEqual(fill_depth_holes(far_hole, method="max")[1, 6], 5.0)


class TransmissionLevelTest(unittest.TestCase):
    def test_mean_transmission_of_constant_depth(self):
        self.assertAlmostEqual(mean_transmission(np.full((2, 2), 3.0), 0.2), math.exp(-0.6))

    def test_beta_for_mean_transmission_inverts(self):
        depth = np.linspace(0.5, 6.0, 100).reshape(10, 10)
        beta = beta_for_mean_transmission(depth, 0.5)
        self.assertAlmostEqual(mean_transmission(depth, beta), 0.5, places=4)
        with self.assertRaises(ValueError):
            beta_for_mean_transmission(depth, 1.0)


@unittest.skipIf(cv2 is None, "OpenCV não instalado")
class EmulateSequenceTest(unittest.TestCase):
    def test_sequence_written_with_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "rgb").mkdir()
            (root / "depth").mkdir()
            for i in range(2):
                cv2.imwrite(str(root / "rgb" / f"{i:04d}.png"), np.full((4, 6, 3), 40, np.uint8))
                depth = np.full((4, 6), 3000, np.uint16)
                depth[0, 0] = 0
                cv2.imwrite(str(root / "depth" / f"{i:04d}.png"), depth)
            meta = emulate_sequence(root / "rgb", root / "depth", root / "out", visibility_m=6.0)
            self.assertEqual(meta["n_frames"], 2)
            self.assertAlmostEqual(meta["mean_transmission"]["mean"], math.exp(-3.912 / 6.0 * 3.0), places=3)
            self.assertAlmostEqual(meta["hole_fraction_mean"], 1 / 24)
            out = cv2.imread(str(root / "out" / "0000.png"))
            self.assertTrue(np.all(out > 40))
            self.assertTrue((root / "out" / "smoke_meta.json").exists())


class ApplySmokeTest(unittest.TestCase):
    def setUp(self):
        self.rgb = np.full((2, 2, 3), 0.2)
        self.depth = np.array([[1.0, 2.0], [3.0, 4.0]])

    def test_zero_beta_keeps_image(self):
        out = apply_smoke(self.rgb, self.depth, beta=0.0)
        np.testing.assert_allclose(out, self.rgb)

    def test_dense_smoke_tends_to_atmospheric_light(self):
        out = apply_smoke(self.rgb, self.depth, beta=100.0, atmospheric_light=(0.9, 0.9, 0.9))
        np.testing.assert_allclose(out, 0.9, atol=1e-6)

    def test_farther_pixels_are_closer_to_a(self):
        out = apply_smoke(self.rgb, self.depth, beta=0.5)[..., 0].ravel()
        self.assertTrue(np.all(np.diff(out) > 0))

    def test_matches_closed_form(self):
        beta, a = 0.3, 0.8
        out = apply_smoke(self.rgb, self.depth, beta=beta, atmospheric_light=(a, a, a))
        t = math.exp(-beta * 3.0)
        self.assertAlmostEqual(out[1, 0, 0], 0.2 * t + a * (1 - t))

    def test_uint8_in_uint8_out(self):
        rgb = np.zeros((2, 2, 3), dtype=np.uint8)
        out = apply_smoke(rgb, self.depth, beta=0.2)
        self.assertEqual(out.dtype, np.uint8)
        self.assertTrue(np.all(out > 0))

    def test_shape_mismatch_raises(self):
        with self.assertRaises(ValueError):
            apply_smoke(self.rgb, np.ones((3, 3)), beta=0.1)


if __name__ == "__main__":
    unittest.main()

"""Testes do pipeline que rodam sem GPU nem dataset (layout sintético em diretório temporário)."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))

from lib import queenscamp  # noqa: E402
import run_matrix  # noqa: E402

try:
    from evo.core.trajectory import PoseTrajectory3D
    import evaluate
except ImportError:  # evo é dependência do host do laboratório
    evaluate = None


def make_config(tmp):
    cfg = json.loads((ROOT / 'config/experiment.json').read_text())
    cfg['dataset']['root'] = str(tmp / 'qc')
    cfg['paths'].update(smoke_root=str(tmp / 'smoke'), runs_root=str(tmp / 'runs'), results_root=str(tmp / 'res'))
    cfg['camera'].update(fx=380.0, fy=380.0, cx=320.0, cy=240.0)
    cfg['_camera_ready'] = True
    return cfg


class LayoutTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.cfg = make_config(self.root)
        seq = self.root / 'qc' / '09'
        for sub in ('images', 'depths'):
            (seq / sub).mkdir(parents=True)
            for i in range(3):
                (seq / sub / f'{i:04d}.png').write_bytes(b'')
        (seq / 'timestamps.txt').write_text('0000 100.0\n0001 100.066\n0002 100.133\n')

    def tearDown(self):
        self.tmp.cleanup()

    def test_frame_list_uses_dataset_timestamps(self):
        frames = queenscamp.frame_list(self.cfg, '09', 'original')
        self.assertEqual([round(t, 3) for t, _, _ in frames], [100.0, 100.066, 100.133])
        self.assertTrue(str(frames[0][2]).endswith('depths/0000.png'))

    def test_smoke_condition_points_to_generated_dir(self):
        self.assertEqual(queenscamp.condition_rgb_dir(self.cfg, '09', 'smoke_densa'), self.root / 'smoke/09/smoke_densa')

    def test_expand_runs_respects_enabled_and_repetitions(self):
        runs = queenscamp.expand_runs(self.cfg, sequences=['09'], conditions=['original'])
        counts = {}
        for r in runs:
            counts[r['algorithm']] = counts.get(r['algorithm'], 0) + 1
        self.assertEqual(counts, {'orbslam2_mono': 5, 'orbslam2_rgbd': 5, 'tartanvo': 2, 'dpvo': 5})

    def test_full_matrix_size(self):
        runs = queenscamp.expand_runs(self.cfg)
        self.assertEqual(len(runs), 16 * 10 * (5 + 5 + 2 + 5))

    def test_orbslam2_settings_and_docker_command(self):
        settings = queenscamp.orbslam2_settings(self.cfg)
        self.assertIn('DepthMapFactor: 1000.0', settings)
        self.assertIn('Camera.bf: 19.0', settings)
        run = queenscamp.expand_runs(self.cfg, ['orbslam2_rgbd'], ['09'], ['original'])[0]
        cmd = run_matrix.docker_command(self.cfg, run, self.cfg['algorithms']['orbslam2_rgbd'])
        self.assertIn('ORBSLAM2_NO_LOOP=1', cmd)
        run_dir = run['run_dir']
        self.assertEqual(cmd[-4:], ['rgbd', f'{run_dir}/input/assoc.txt', run_dir, '--realtime'])

    def test_write_calib_requires_intrinsics(self):
        self.cfg['_camera_ready'] = False
        with self.assertRaises(ValueError):
            queenscamp.write_calib(self.cfg, self.root / 'calib.txt')


def trajectory(positions, yaws=None):
    poses = []
    for i, p in enumerate(positions):
        T = np.eye(4)
        if yaws is not None:
            c, s = np.cos(yaws[i]), np.sin(yaws[i])
            T[:2, :2] = [[c, -s], [s, c]]
        T[:3, 3] = p
        poses.append(T)
    return PoseTrajectory3D(poses_se3=poses, timestamps=np.arange(len(poses), dtype=float))


@unittest.skipIf(evaluate is None, 'evo não instalado')
class MetricTests(unittest.TestCase):
    def setUp(self):
        t = np.linspace(0, 2 * np.pi, 60)
        self.gt_positions = np.stack([np.cos(t), np.sin(t), 0.1 * t], axis=1)
        self.ref = trajectory(self.gt_positions, t)

    def test_perfect_monocular_up_to_scale_has_zero_error(self):
        est = trajectory(3.0 * self.gt_positions, np.linspace(0, 2 * np.pi, 60))
        m = evaluate.trajectory_metrics(self.ref, est, monocular=True, delta=15)
        self.assertEqual(m['ate_metric'], 'sim3')
        self.assertLess(m['ate_m'], 1e-6)
        self.assertLess(m['ate_stepscale_m'], 1e-6)

    def test_step_scale_removes_inconsistent_step_lengths(self):
        # velocidade variável; estimativa com direções corretas e cada passo de comprimento 1
        # (como a saída normalizada do TartanVO)
        t = np.linspace(0, 2 * np.pi, 60) ** 2 / (2 * np.pi)
        gt_positions = np.stack([np.cos(t), np.sin(t), 0.1 * t], axis=1)
        ref = trajectory(gt_positions, t)
        steps = np.diff(gt_positions, axis=0)
        unit = steps / np.linalg.norm(steps, axis=1, keepdims=True)
        est = trajectory(np.vstack([np.zeros(3), np.cumsum(unit, axis=0)]), t)
        m = evaluate.trajectory_metrics(ref, est, monocular=True, delta=15, primary='stepscale')
        self.assertLess(m['ate_m'], 1e-6)
        self.assertGreater(m['ate_sim3_m'], 0.05)  # Sim(3) não corrige escala inconsistente entre passos

    def test_rgbd_uses_se3_so_scale_error_counts(self):
        est = trajectory(2.0 * self.gt_positions, np.linspace(0, 2 * np.pi, 60))
        self.assertGreater(evaluate.trajectory_metrics(self.ref, est, monocular=False, delta=15)['ate_m'], 0.1)

    def test_summary_degradation_relative_to_original(self):
        rows = [dict(algorithm='a', sequence='09', condition=c, status='ok', ate_m=v, tracked_fraction=1.0,
                     rpe_trans_pct=1.0, rpe_rot_deg=1.0) for c, v in [('original', 0.2), ('original', 0.4), ('wet', 0.6)]]
        summary = {s['condition']: s for s in evaluate.summarize(rows)}
        self.assertAlmostEqual(summary['original']['ate_m_median'], 0.3)
        self.assertAlmostEqual(summary['wet']['ate_degradation_pct'], 100.0)


if __name__ == '__main__':
    unittest.main()

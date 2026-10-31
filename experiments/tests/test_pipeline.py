"""Testes do pipeline que rodam sem GPU nem dataset (layout sintético em diretório temporário)."""
import argparse
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

try:
    import stats_analysis
except ImportError:  # scipy também
    stats_analysis = None


def make_config(tmp):
    cfg = json.loads((ROOT / 'config/experiment.json').read_text())
    cfg['dataset']['root'] = str(tmp / 'qc')
    cfg['paths'].update(smoke_root=str(tmp / 'smoke'), dehaze_root=str(tmp / 'dcp'), runs_root=str(tmp / 'runs'),
                        results_root=str(tmp / 'res'))
    cfg['camera'].update(fx=380.0, fy=380.0, cx=320.0, cy=240.0)
    cfg['_camera_ready'] = True
    return cfg


class LayoutTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.cfg = make_config(self.root)
        seq = self.root / 'qc' / '09'
        for sub in ('images', self.cfg['dataset']['depth_dir']):
            (seq / sub).mkdir(parents=True)
            for i in range(3):
                (seq / sub / f'{i:04d}.png').write_bytes(b'')
        (seq / self.cfg['dataset']['timestamps_file']).write_text('0000 100.0\n0001 100.066\n0002 100.133\n')

    def tearDown(self):
        self.tmp.cleanup()

    def test_frame_list_uses_dataset_timestamps(self):
        frames = queenscamp.frame_list(self.cfg, '09', 'original')
        self.assertEqual([round(t, 3) for t, _, _ in frames], [100.0, 100.066, 100.133])
        self.assertTrue(str(frames[0][2]).endswith(self.cfg['dataset']['depth_dir'] + '/0000.png'))

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

    def test_disabled_dehaze_conditions_only_when_requested(self):
        default = {r['condition'] for r in queenscamp.expand_runs(self.cfg, sequences=['09'])}
        self.assertFalse(any(c.startswith('dcp_') for c in default))
        runs = queenscamp.expand_runs(self.cfg, ['dpvo'], ['09'], ['dcp_smoke_densa', 'dcp_original'])
        self.assertEqual(len(runs), 2 * 5)
        self.assertEqual(queenscamp.condition_rgb_dir(self.cfg, '09', 'dcp_original'), self.root / 'dcp/09/dcp_original')

    def test_disabled_algorithm_runs_when_requested(self):
        self.assertEqual(len(queenscamp.expand_runs(self.cfg, ['droidvo'], ['09'], ['original'])), 5)

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

    def test_docker_limits_follow_algorithm_override_and_forbid_core_dumps(self):
        def option(cmd, name):
            return cmd[cmd.index(name) + 1]

        orb = queenscamp.expand_runs(self.cfg, ['orbslam2_rgbd'], ['09'], ['original'])[0]
        dpvo = queenscamp.expand_runs(self.cfg, ['dpvo'], ['09'], ['original'])[0]
        cmd_orb = run_matrix.docker_command(self.cfg, orb, self.cfg['algorithms']['orbslam2_rgbd'])
        cmd_dpvo = run_matrix.docker_command(self.cfg, dpvo, self.cfg['algorithms']['dpvo'])
        self.assertEqual((option(cmd_orb, '--memory'), option(cmd_orb, '--cpus')), ('4g', '4'))
        self.assertEqual((option(cmd_dpvo, '--memory'), option(cmd_dpvo, '--cpus')), ('8g', '8'))
        self.assertEqual(option(cmd_orb, '--memory-swap'), option(cmd_orb, '--memory'))
        for cmd in (cmd_orb, cmd_dpvo):
            self.assertEqual(option(cmd, '--ulimit'), 'core=0')
            self.assertEqual(option(cmd, '--cpu-shares'), '512')
        self.assertNotIn('--gpus', cmd_orb)  # só CPU: não passa pelo runtime da NVIDIA
        self.assertEqual(option(cmd_dpvo, '--gpus'), 'all')


class ShardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.runs = queenscamp.expand_runs(make_config(Path(self.tmp.name)), ['orbslam2_mono', 'orbslam2_rgbd'])

    def tearDown(self):
        self.tmp.cleanup()

    def test_shards_partition_the_matrix(self):
        shards = [run_matrix.shard_runs(self.runs, (k, 4)) for k in range(4)]
        keys = [r['run_dir'] for shard in shards for r in shard]
        self.assertEqual(sorted(keys), sorted(r['run_dir'] for r in self.runs))
        self.assertEqual(len(keys), len(set(keys)))
        self.assertLessEqual(max(map(len, shards)) - min(map(len, shards)), 1)

    def test_no_shard_keeps_every_run(self):
        self.assertEqual(run_matrix.shard_runs(self.runs, None), self.runs)

    def test_shard_does_not_depend_on_what_is_already_done(self):
        # a fatia é calculada na matriz inteira, não nos pendentes: reiniciar não troca execuções de fatia
        self.assertEqual(run_matrix.shard_runs(self.runs, (2, 4))[0]['run_dir'], self.runs[2]['run_dir'])

    def test_parse_shard(self):
        self.assertEqual(run_matrix.parse_shard('3/4'), (3, 4))
        for bad in ('4/4', '-1/4', 'a/b', '1', '0/0'):
            with self.assertRaises(argparse.ArgumentTypeError):
                run_matrix.parse_shard(bad)


class HardwareTests(unittest.TestCase):
    LIMITS = {**run_matrix.RESOURCE_DEFAULTS, 'max_wait_min': 10}
    COOL = dict(gpu_temp_c=60, gpu_free_mib=15000, cpu_temp_c=60, mem_available_gb=50, disk_free_gb=900)

    def test_cool_host_has_no_problems(self):
        self.assertEqual(run_matrix.hardware_problems(self.COOL, self.LIMITS, uses_gpu=True), [])

    def test_hot_cpu_blocks_every_run_but_gpu_limits_only_gpu_runs(self):
        hot_cpu = {**self.COOL, 'cpu_temp_c': 95}
        self.assertEqual(len(run_matrix.hardware_problems(hot_cpu, self.LIMITS, uses_gpu=False)), 1)
        busy_gpu = {**self.COOL, 'gpu_temp_c': 90, 'gpu_free_mib': 2000}
        self.assertEqual(len(run_matrix.hardware_problems(busy_gpu, self.LIMITS, uses_gpu=True)), 2)
        self.assertEqual(run_matrix.hardware_problems(busy_gpu, self.LIMITS, uses_gpu=False), [])

    def test_low_memory_and_disk_block(self):
        low = {**self.COOL, 'mem_available_gb': 5, 'disk_free_gb': 50}
        self.assertEqual(len(run_matrix.hardware_problems(low, self.LIMITS, uses_gpu=False)), 2)

    def test_unreadable_sensor_does_not_block(self):
        blind = {key: None for key in self.COOL}
        self.assertEqual(run_matrix.hardware_problems(blind, self.LIMITS, uses_gpu=True), [])

    def test_wait_resumes_when_host_cools_down(self):
        readings = iter([{**self.COOL, 'cpu_temp_c': 95}, {**self.COOL, 'cpu_temp_c': 92}, self.COOL])
        waited = []
        ok = run_matrix.wait_for_hardware(self.LIMITS, False, '.', reader=lambda _: next(readings), sleep=waited.append)
        self.assertTrue(ok)
        self.assertEqual(len(waited), 2)

    def test_wait_gives_up_after_max_wait(self):
        ok = run_matrix.wait_for_hardware({**self.LIMITS, 'max_wait_min': 0}, False, '.',
                                          reader=lambda _: {**self.COOL, 'cpu_temp_c': 95}, sleep=lambda _: None)
        self.assertFalse(ok)

    def test_never_initialized_needs_every_frame_in_state_not_initialized(self):
        with tempfile.TemporaryDirectory() as tmp:
            frames = Path(tmp) / 'frames.csv'
            frames.write_text('timestamp,tracking_state,track_ms\n' + ''.join(f'{i},1,8.0\n' for i in range(4)))
            self.assertTrue(run_matrix.never_initialized(tmp, 4))
            self.assertFalse(run_matrix.never_initialized(tmp, 5))  # parou antes do fim: não é falha de rastreamento
            frames.write_text('timestamp,tracking_state,track_ms\n1,1,8.0\n2,0,8.0\n3,1,8.0\n')  # reset: quadro em estado 0
            self.assertTrue(run_matrix.never_initialized(tmp, 3))
            frames.write_text('timestamp,tracking_state,track_ms\n1,1,8.0\n2,2,8.0\n')
            self.assertFalse(run_matrix.never_initialized(tmp, 2))
            frames.write_text('timestamp,tracking_state,track_ms\n1,1,8.0\n2,3,8.0\n')  # já esteve inicializado e perdeu
            self.assertFalse(run_matrix.never_initialized(tmp, 2))
            frames.unlink()
            self.assertFalse(run_matrix.never_initialized(tmp, 2))

    def test_empty_map_at_save_needs_complete_frames_and_crash_in_save(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'frames.csv').write_text('timestamp,tracking_state,track_ms\n1,1,8.0\n2,2,8.0\n3,3,8.0\n4,0,8.0\n')
            log = Path(tmp) / 'stdout.log'
            log.write_text('System Reseting\n\nSaving camera trajectory to /x/trajectory_tum.txt ...\n')
            self.assertTrue(run_matrix.empty_map_at_save(tmp, 4))
            self.assertFalse(run_matrix.empty_map_at_save(tmp, 5))  # parou antes do fim
            log.write_text('System Reseting\nTracking...\n')  # caiu no meio, não ao salvar
            self.assertFalse(run_matrix.empty_map_at_save(tmp, 4))
            log.unlink()
            self.assertFalse(run_matrix.empty_map_at_save(tmp, 4))

    def test_crashed_after_reset_reads_stdout_when_frames_csv_is_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'frames.csv').write_text('')  # a queda descarta o buffer
            log = Path(tmp) / 'stdout.log'
            log.write_text('New map created with 381 points\nTrack lost soon after initialisation, reseting...\n'
                           'System Reseting\nReseting Database... done\nNew map created with 250 points\n')
            self.assertTrue(run_matrix.crashed_after_reset(tmp))
            log.write_text('New map created with 381 points\n')  # caiu sem nunca resetar: segue failed
            self.assertFalse(run_matrix.crashed_after_reset(tmp))
            log.write_text('System Reseting\n\nSaving camera trajectory to /x/trajectory_tum.txt ...\n')  # caso de empty_map_at_save
            self.assertFalse(run_matrix.crashed_after_reset(tmp))
            log.unlink()
            self.assertFalse(run_matrix.crashed_after_reset(tmp))

    def test_failure_streak_counts_only_failed_and_timeout(self):
        streak = 0
        for status in ('failed', 'timeout', 'failed'):
            streak = run_matrix.failure_streak(streak, status)
        self.assertEqual(streak, 3)
        for status in ('ok', 'not_initialized', 'tracking_lost'):
            self.assertEqual(run_matrix.failure_streak(3, status), 0)

    def test_xid_count_reads_only_nvrm_xid_lines_and_tolerates_missing_journal(self):
        import datetime, subprocess
        log = ('kernel: NVRM: Xid (PCI:0000:01:00): 8, pid=1, name=python3, channel 0x09\n'
               'kernel: NVRM: GPU at PCI:0000:01:00: GPU-b6b9\n'
               'kernel: NVRM: krcWatchdog_IMPL: RC watchdog: GPU is probably locked!\n'
               'kernel: NVRM: Xid (PCI:0000:01:00): 31, pid=2, name=python3\n')
        since = datetime.datetime(2026, 10, 30, 18, 0, 0)
        seen = {}

        def fake_run(cmd, **kw):
            seen['cmd'] = cmd
            return subprocess.CompletedProcess(cmd, 0, stdout=log)
        self.assertEqual(run_matrix.xid_count(since, run=fake_run), 2)
        self.assertIn('2026-10-30 18:00:00', seen['cmd'])

        def no_journal(cmd, **kw):
            raise FileNotFoundError('journalctl')
        self.assertEqual(run_matrix.xid_count(since, run=no_journal), 0)


class DpvoPoseChainTests(unittest.TestCase):
    """get_pose iterativo do DPVO: mesmo resultado do recursivo e sem limite de profundidade."""

    class SE3:
        def __init__(self, m):
            self.m = m

        def __mul__(self, other):
            return DpvoPoseChainTests.SE3(self.m @ other.m)

    class Fake:
        def __init__(self, n, rng):
            def step():
                m = np.eye(4)
                m[:3, 3] = rng.normal(size=3) * 0.01
                return m
            self.traj = {0: np.eye(4)}
            self.pg = type('PG', (), {})()
            self.pg.delta = {t: (t - 1, DpvoPoseChainTests.SE3(step())) for t in range(1, n)}

    def test_matches_recursive_version_and_survives_deep_chains(self):
        sys.path.insert(0, str(ROOT / 'algorithms/dpvo'))
        try:
            from pose_chain import iterative_get_pose
        finally:
            sys.path.pop(0)
        SE3 = self.SE3
        iterative = iterative_get_pose(SE3)

        def recursive(self, t):  # o get_pose original do DPVO
            if t in self.traj:
                return SE3(self.traj[t])
            t0, dP = self.pg.delta[t]
            return dP * recursive(self, t0)

        short = self.Fake(40, np.random.default_rng(0))
        np.testing.assert_allclose(iterative(short, 39).m, recursive(short, 39).m, atol=1e-12)
        deep = self.Fake(5000, np.random.default_rng(1))
        with self.assertRaises(RecursionError):
            recursive(deep, 4999)
        self.assertTrue(np.isfinite(iterative(deep, 4999).m).all())


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
        m = evaluate.trajectory_metrics(self.ref, est, monocular=False, delta=15)
        self.assertGreater(m['ate_m'], 0.1)
        # o diagnóstico Sim(3) recupera o erro de escala: ATE ~ 0 e escala 0,5 (estimativa 2x maior que o GT)
        self.assertLess(m['ate_sim3_m'], 1e-6)
        self.assertAlmostEqual(m['sim3_scale'], 0.5, places=3)

    def test_rgbd_primary_is_configurable_and_both_alignments_are_recorded(self):
        est = trajectory(2.0 * self.gt_positions, np.linspace(0, 2 * np.pi, 60))
        se3 = evaluate.trajectory_metrics(self.ref, est, monocular=False, delta=15, rgbd_primary='se3')
        sim3 = evaluate.trajectory_metrics(self.ref, est, monocular=False, delta=15, rgbd_primary='sim3')
        self.assertEqual((se3['ate_metric'], sim3['ate_metric']), ('se3', 'sim3'))
        self.assertGreater(se3['ate_m'], 0.1)
        self.assertLess(sim3['ate_m'], 1e-6)
        for m in (se3, sim3):  # os dois ficam gravados para a análise de sensibilidade
            self.assertAlmostEqual(m['ate_se3_m'], se3['ate_m'])
            self.assertLess(m['ate_sim3_m'], 1e-6)

    def test_summary_counts_lost_seeds_as_zero_tracking(self):
        def row(status, tracked, ate=None):
            return dict(algorithm='mono', sequence='09', condition='dirt', status=status, tracked_fraction=tracked,
                        ate_m=ate, rpe_trans_pct=1.0, rpe_rot_deg=1.0)

        rows = [row('ok', 0.9, 0.2), row('ok', 0.9, 0.4), row('not_initialized', 0.0),
                row('not_initialized', 0.0), row('not_initialized', 0.0)]
        s = evaluate.summarize(rows)[0]
        self.assertEqual(s['tracked_fraction_median'], 0.0)  # antes saía 0,9, só das sementes boas
        self.assertAlmostEqual(s['ate_m_median'], 0.3)
        self.assertAlmostEqual(s['success_rate'], 0.4)

    def test_summary_leaves_runs_below_half_tracking_out_of_the_ate(self):
        def row(condition, tracked, ate):
            return dict(algorithm='rgbd', sequence='09', condition=condition, status='ok', tracked_fraction=tracked,
                        ate_m=ate, rpe_trans_pct=1.0, rpe_rot_deg=1.0)

        rows = [row('original', 1.0, 0.15), row('condensation', 0.12, 0.08), row('breakage', 0.6, 0.30)]
        summary = {s['condition']: s for s in evaluate.summarize(rows)}
        self.assertIsNone(summary['condensation']['ate_m_median'])  # 12% da trajetória não vira "melhor que a original"
        self.assertIsNone(summary['condensation']['ate_degradation_pct'])
        self.assertAlmostEqual(summary['condensation']['tracked_fraction_median'], 0.12)
        self.assertAlmostEqual(summary['breakage']['ate_degradation_pct'], 100.0)
        self.assertEqual(summary['condensation']['n_valid'], 0)

    def test_orbslam2_latency_comes_from_frames_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            self.assertIsNone(evaluate.frames_latency(run))  # sem frames.csv
            (run / 'frames.csv').write_text('timestamp,tracking_state,track_ms\n')
            self.assertIsNone(evaluate.frames_latency(run))  # processo caiu, arquivo vazio
            (run / 'frames.csv').write_text('timestamp,tracking_state,track_ms\n1.0,2,10.0\n1.1,2,20.0\n1.2,3,30.0\n')
            self.assertAlmostEqual(evaluate.frames_latency(run), 20.0)

    def test_static_trajectory_is_detected(self):
        # DPVO em wet/condensation: poses todas iguais, o Umeyama não tem solução
        t = np.linspace(0, 2 * np.pi, 60)
        self.assertTrue(evaluate.is_static(trajectory(np.zeros((60, 3)), t)))
        two_points = np.zeros((60, 3))
        two_points[30:, 0] = 0.015  # 2 posições distintas, como o DPVO 11/wet/seed1
        self.assertTrue(evaluate.is_static(trajectory(two_points, t)))
        self.assertFalse(evaluate.is_static(trajectory(self.gt_positions, t)))

    def test_flag_degenerate_uses_original_scale_of_metric_sensors(self):
        algos = {'rgbd': {'monocular': False}, 'mono': {'monocular': True}}

        def row(algorithm, condition, scale, status='ok', sequence='09'):
            return dict(algorithm=algorithm, sequence=sequence, condition=condition, status=status, sim3_scale=scale)

        rows = [row('rgbd', 'original', 1.12), row('rgbd', 'original', 1.14),  # referência: mediana 1,13
                row('rgbd', 'dirt', 0.70),            # degradou, mas a escala continua plausível
                row('rgbd', 'wet', 90.0),             # trajetória quase parada, estado "OK" no algoritmo
                row('rgbd', 'breakage', 0.4),         # encolhida abaixo de 1/f
                row('mono', 'original', 3.0), row('mono', 'wet', 300.0),  # escala monocular é arbitrária
                row('rgbd', 'dirt', None, status='failed'),
                row('rgbd', 'wet', 90.0, sequence='10')]  # sem original nessa sequência
        evaluate.flag_degenerate(rows, algos, factor=2.0)
        flags = [r['degenerate'] for r in rows]
        self.assertEqual(flags, [False, False, False, True, True, None, None, None, None])
        self.assertAlmostEqual(rows[3]['scale_vs_original'], 90.0 / 1.13)
        self.assertIsNone(rows[5]['scale_vs_original'])

    def test_summary_counts_degenerate_runs(self):
        rows = [dict(algorithm='a', sequence='09', condition='wet', status='ok', ate_m=1.0, tracked_fraction=1.0,
                     rpe_trans_pct=1.0, rpe_rot_deg=1.0, degenerate=d) for d in (True, False, None)]
        self.assertEqual(evaluate.summarize(rows)[0]['n_degenerate'], 1)

    def test_summary_degradation_relative_to_original(self):
        rows = [dict(algorithm='a', sequence='09', condition=c, status='ok', ate_m=v, tracked_fraction=1.0,
                     rpe_trans_pct=1.0, rpe_rot_deg=1.0) for c, v in [('original', 0.2), ('original', 0.4), ('wet', 0.6)]]
        summary = {s['condition']: s for s in evaluate.summarize(rows)}
        self.assertAlmostEqual(summary['original']['ate_m_median'], 0.3)
        self.assertAlmostEqual(summary['wet']['ate_degradation_pct'], 100.0)


if __name__ == '__main__':
    unittest.main()


@unittest.skipIf(stats_analysis is None, 'scipy não instalado')
class ExploratoryConditionTests(unittest.TestCase):
    def rows(self):
        out = []
        for algorithm in ('dpvo', 'tartanvo', 'orbslam2_rgbd'):
            for seq in range(8):
                for condition, ate in (('original', 0.2), ('smoke_densa', 0.21), ('smoke_extrema', 0.8)):
                    if algorithm == 'orbslam2_rgbd' and condition == 'smoke_extrema':
                        continue  # o ORB-SLAM2 não roda a exploratória
                    out.append(dict(algorithm=algorithm, sequence=f'{seq:02d}', condition=condition,
                                    ate_m_median=ate + 0.01 * seq, tracked_fraction_median=1.0,
                                    ate_degradation_pct=0.0 if condition == 'original' else 100 * (ate - 0.2) / 0.2))
        return out

    def test_exploratory_condition_stays_out_of_the_main_families(self):
        main, exploratory = stats_analysis.split_exploratory(self.rows(), ['smoke_extrema'])
        self.assertNotIn('smoke_extrema', {r['condition'] for r in main})
        self.assertEqual({r['algorithm'] for r in exploratory}, {'dpvo', 'tartanvo'})  # original só de quem a tem
        self.assertEqual({r['condition'] for r in exploratory}, {'original', 'smoke_extrema'})
        # os testes principais não mudam de tamanho com a exploratória presente
        self.assertEqual(len(stats_analysis.vs_original(main, n_boot=50)), 3 * 1)

    def test_exploratory_results_have_their_own_bonferroni_family(self):
        results = stats_analysis.exploratory_results(self.rows(), ['smoke_extrema'], n_boot=50)
        self.assertEqual({(r['algorithm'], r['condition']) for r in results},
                         {('dpvo', 'smoke_extrema'), ('tartanvo', 'smoke_extrema')})
        self.assertTrue(all(r['m_tests'] == 2 for r in results))
        self.assertTrue(all(r['robust'] is False for r in results))  # +300% de degradação
        self.assertEqual(stats_analysis.exploratory_results(self.rows(), [], n_boot=50), [])

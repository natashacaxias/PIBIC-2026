#!/usr/bin/env python3
"""Calcula as métricas de trajetória de todas as execuções e agrega os resultados.

Saídas em <results_root>/:
  metrics.csv  uma linha por execução (status, rastreamento, ATE, RPE, tempo, GPU)
  summary.csv  mediana e IQR por algoritmo × sequência × condição, com a degradação
               percentual em relação à condição original do mesmo algoritmo

Alinhamento (ver docs/protocolo_experimental.md):
  monocular -> `ate_sim3_m` (Sim(3)) e `ate_stepscale_m` (escala de cada passo tirada do
               ground truth) são sempre calculados; `ate_m` é o definido em
               evaluation.monocular_primary, exceto para algoritmos com step_scale_only
               (TartanVO, cuja saída não tem escala consistente entre quadros)
  RGB-D     -> SE(3) (`ate_m`)
"""
import argparse
import copy
import csv
import json
from pathlib import Path
import sys

import numpy as np
from evo.core import metrics, sync
from evo.core.trajectory import PoseTrajectory3D
from evo.tools import file_interface

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.queenscamp import load_config, sequence_dir  # noqa: E402

RUN_FIELDS = ['algorithm', 'sequence', 'condition', 'seed', 'status', 'n_frames', 'n_matched', 'tracked_fraction',
              'ate_m', 'ate_metric', 'ate_sim3_m', 'ate_stepscale_m', 'rpe_trans_m', 'rpe_trans_pct', 'rpe_rot_deg',
              'wall_s', 'mean_ms_per_frame', 'peak_gpu_mib', 'error']
SUMMARY_METRICS = ['ate_m', 'tracked_fraction', 'rpe_trans_pct', 'rpe_rot_deg']


def step_scaled(est, ref):
    """Reescala cada passo da estimativa para o comprimento do passo correspondente do ground truth.

    Mantém rotações e direções de translação estimadas; elimina o erro de escala.
    É o "oráculo de escala" que o TartanVO usa com --pose-file, aplicado igualmente
    a todos os métodos monoculares.
    """
    est_poses, ref_poses = est.poses_se3, ref.poses_se3
    out = [est_poses[0].copy()]
    for k in range(1, len(est_poses)):
        rel = np.linalg.inv(est_poses[k - 1]) @ est_poses[k]
        norm = np.linalg.norm(rel[:3, 3])
        gt_step = np.linalg.norm(ref_poses[k][:3, 3] - ref_poses[k - 1][:3, 3])
        rel[:3, 3] = rel[:3, 3] * (gt_step / norm) if norm > 1e-12 else 0.0
        out.append(out[-1] @ rel)
    return PoseTrajectory3D(poses_se3=out, timestamps=np.array(est.timestamps, copy=True))


def ate(ref, est, correct_scale):
    aligned = copy.deepcopy(est)
    aligned.align(ref, correct_scale=correct_scale)
    metric = metrics.APE(metrics.PoseRelation.translation_part)
    metric.process_data((ref, aligned))
    return metric.get_statistic(metrics.StatisticsType.rmse), aligned


def rpe(ref, est, delta):
    trans = metrics.RPE(metrics.PoseRelation.translation_part, delta=delta, delta_unit=metrics.Unit.frames)
    trans.process_data((ref, est))
    rot = metrics.RPE(metrics.PoseRelation.rotation_angle_deg, delta=delta, delta_unit=metrics.Unit.frames)
    rot.process_data((ref, est))
    gt_disp = [np.linalg.norm(ref.positions_xyz[i + delta] - ref.positions_xyz[i]) for i in range(ref.num_poses - delta)]
    mean_disp = float(np.mean(gt_disp)) if gt_disp else float('nan')
    pct = 100.0 * trans.get_statistic(metrics.StatisticsType.mean) / mean_disp if mean_disp > 0 else float('nan')
    return trans.get_statistic(metrics.StatisticsType.rmse), pct, rot.get_statistic(metrics.StatisticsType.rmse)


def trajectory_metrics(ref, est, monocular, delta, primary='sim3'):
    """Métricas de uma trajetória já associada ao ground truth; o RPE usa o alinhamento principal."""
    out = {'ate_sim3_m': None, 'ate_stepscale_m': None}
    if monocular:
        out['ate_sim3_m'], sim3 = ate(ref, est, correct_scale=True)
        out['ate_stepscale_m'], stepped = ate(ref, step_scaled(est, ref), correct_scale=False)
        out['ate_metric'], aligned = (primary, sim3 if primary == 'sim3' else stepped)
        out['ate_m'] = out[f'ate_{primary}_m']
    else:
        out['ate_m'], aligned = ate(ref, est, correct_scale=False)
        out['ate_metric'] = 'se3'
    out['rpe_trans_m'], out['rpe_trans_pct'], out['rpe_rot_deg'] = rpe(ref, aligned, min(delta, ref.num_poses - 1))
    return out


def evaluate_run(cfg, meta):
    algo_meta = meta.get('algo') or {}
    row = {k: meta.get(k) for k in ('algorithm', 'sequence', 'condition', 'seed', 'status', 'n_frames', 'wall_s')}
    row['mean_ms_per_frame'] = algo_meta.get('mean_ms_per_frame')
    row['peak_gpu_mib'] = algo_meta.get('peak_gpu_mib', meta.get('peak_gpu_mib_host'))
    if meta['status'] != 'ok':
        row['tracked_fraction'] = 0.0
        return row
    try:
        gt_file = sequence_dir(cfg, meta['sequence']) / cfg['dataset']['groundtruth_file']
        gt = file_interface.read_tum_trajectory_file(str(gt_file))
        est = file_interface.read_tum_trajectory_file(str(Path(meta['run_dir']) / 'trajectory_tum.txt'))
        ref, est = sync.associate_trajectories(gt, est, cfg['evaluation']['max_time_diff_s'])
        row['n_matched'] = ref.num_poses
        row['tracked_fraction'] = ref.num_poses / meta['n_frames']
        delta = max(1, round(cfg['evaluation']['rpe_delta_s'] * cfg['dataset']['fps']))
        algo = cfg['algorithms'][meta['algorithm']]
        primary = 'stepscale' if algo.get('step_scale_only') else cfg['evaluation']['monocular_primary']
        row.update(trajectory_metrics(ref, est, algo['monocular'], delta, primary))
    except Exception as exc:  # trajetória curta demais, arquivo corrompido etc.: registrar e seguir
        row['status'], row['error'] = 'eval_error', f'{type(exc).__name__}: {exc}'
    return row


def summarize(rows):
    groups = {}
    for row in rows:
        groups.setdefault((row['algorithm'], row['sequence'], row['condition']), []).append(row)
    summary = []
    for (algorithm, sequence, condition), items in sorted(groups.items()):
        out = {'algorithm': algorithm, 'sequence': sequence, 'condition': condition,
               'n_runs': len(items), 'n_ok': sum(r['status'] == 'ok' for r in items)}
        for name in SUMMARY_METRICS:
            values = [r[name] for r in items if r.get(name) is not None and r['status'] == 'ok']
            values = [v for v in values if not np.isnan(v)]
            out[f'{name}_median'] = float(np.median(values)) if values else None
            out[f'{name}_iqr'] = float(np.subtract(*np.percentile(values, [75, 25]))) if values else None
        summary.append(out)
    originals = {(s['algorithm'], s['sequence']): s for s in summary if s['condition'] == 'original'}
    for s in summary:
        base = originals.get((s['algorithm'], s['sequence']))
        ok = base and base['ate_m_median'] and s['ate_m_median'] is not None
        s['ate_degradation_pct'] = 100.0 * (s['ate_m_median'] - base['ate_m_median']) / base['ate_m_median'] if ok else None
    return summary


def write_csv(rows, path, fields=None):
    fields = fields or list(rows[0])
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--config', default=str(Path(__file__).resolve().parents[1] / 'config/experiment.json'))
    args = parser.parse_args()
    cfg = load_config(args.config)
    metas = [json.loads(p.read_text()) for p in sorted(Path(cfg['paths']['runs_root']).rglob('meta.json'))]
    if not metas:
        print('nenhuma execução encontrada em', cfg['paths']['runs_root'])
        return 1
    rows = [evaluate_run(cfg, m) for m in metas]
    out = Path(cfg['paths']['results_root'])
    out.mkdir(parents=True, exist_ok=True)
    write_csv(rows, out / 'metrics.csv', RUN_FIELDS)
    summary = summarize(rows)
    write_csv(summary, out / 'summary.csv')
    print(f'{len(rows)} execuções avaliadas → {out / "metrics.csv"} e {out / "summary.csv"}')
    return 0


if __name__ == '__main__':
    sys.exit(main())

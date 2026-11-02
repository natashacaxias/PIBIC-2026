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
  RGB-D     -> `ate_m` é o definido em evaluation.rgbd_primary (Sim(3) na decisão de 31/10, que reproduz o
               artigo); `ate_se3_m`, `ate_sim3_m` e `sim3_scale` ficam sempre gravados

Trajetória degenerada (`degenerate`): em sensores métricos a escala do Sim(3) deve ficar perto da
da condição original; fora de [1/f, f] vezes a mediana do original (f = evaluation.degenerate_scale_factor)
a trajetória é marcada. Pega falhas em que o algoritmo informa rastreamento OK (ORB-SLAM2 RGB-D no `wet`).
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
              'ate_m', 'ate_metric', 'ate_se3_m', 'ate_sim3_m', 'ate_stepscale_m', 'sim3_scale', 'scale_vs_original', 'degenerate',
              'rpe_trans_m', 'rpe_trans_pct', 'rpe_rot_deg',
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


def ate(ref, est, correct_scale, return_scale=False):
    aligned = copy.deepcopy(est)
    _, _, scale = aligned.align(ref, correct_scale=correct_scale)
    metric = metrics.APE(metrics.PoseRelation.translation_part)
    metric.process_data((ref, aligned))
    rmse = metric.get_statistic(metrics.StatisticsType.rmse)
    return (rmse, aligned, float(scale)) if return_scale else (rmse, aligned)


def rpe(ref, est, delta):
    trans = metrics.RPE(metrics.PoseRelation.translation_part, delta=delta, delta_unit=metrics.Unit.frames)
    trans.process_data((ref, est))
    rot = metrics.RPE(metrics.PoseRelation.rotation_angle_deg, delta=delta, delta_unit=metrics.Unit.frames)
    rot.process_data((ref, est))
    gt_disp = [np.linalg.norm(ref.positions_xyz[i + delta] - ref.positions_xyz[i]) for i in range(ref.num_poses - delta)]
    mean_disp = float(np.mean(gt_disp)) if gt_disp else float('nan')
    pct = 100.0 * trans.get_statistic(metrics.StatisticsType.mean) / mean_disp if mean_disp > 0 else float('nan')
    return trans.get_statistic(metrics.StatisticsType.rmse), pct, rot.get_statistic(metrics.StatisticsType.rmse)


def trajectory_metrics(ref, est, monocular, delta, primary='sim3', rgbd_primary='se3'):
    """Métricas de uma trajetória já associada ao ground truth; o RPE usa o alinhamento principal."""
    out = {'ate_se3_m': None, 'ate_sim3_m': None, 'ate_stepscale_m': None, 'sim3_scale': None}
    if monocular:
        # o fator de escala do Sim(3) fica registrado: valores muito longe da mediana do
        # método indicam trajetória degenerada "encolhida" para caber no ground truth
        out['ate_sim3_m'], sim3, out['sim3_scale'] = ate(ref, est, correct_scale=True, return_scale=True)
        out['ate_stepscale_m'], stepped = ate(ref, step_scaled(est, ref), correct_scale=False)
        out['ate_metric'], aligned = (primary, sim3 if primary == 'sim3' else stepped)
        out['ate_m'] = out[f'ate_{primary}_m']
    else:
        out['ate_se3_m'], se3 = ate(ref, est, correct_scale=False)
        # a escala Sim(3) num sensor métrico (RGB-D) varia de 0,8 a 1,2 entre sequências sem apontar bug de
        # depth_scale ou de calibração; longe disso (ver flag_degenerate) é falha do algoritmo
        out['ate_sim3_m'], sim3, out['sim3_scale'] = ate(ref, est, correct_scale=True, return_scale=True)
        out['ate_metric'], aligned = (rgbd_primary, sim3 if rgbd_primary == 'sim3' else se3)
        out['ate_m'] = out[f'ate_{rgbd_primary}_m']
    out['rpe_trans_m'], out['rpe_trans_pct'], out['rpe_rot_deg'] = rpe(ref, aligned, min(delta, ref.num_poses - 1))
    return out


def is_static(est, tol_m=1e-6):
    """Trajetória sem deslocamento: menos de 3 posições distintas, nada que dê para alinhar ao ground truth.

    O DPVO termina 'ok' com isso em `wet` e `condensation` (18 execuções; uma delas com 2 posições a 1,5 cm uma da
    outra): o algoritmo não falha, mas também não rastreia nada, e o alinhamento de Umeyama não existe (covariância
    degenerada). Conta como perda de rastreamento.
    """
    return len(np.unique(np.round(est.positions_xyz / tol_m), axis=0)) < 3


def frames_latency(run_dir):
    """Média de `track_ms` do frames.csv do ORB-SLAM2 (só o tracking, sem as threads de mapeamento).

    O wrapper do ORB-SLAM2 não grava `mean_ms_per_frame` no meta.json; o `--realtime` espera depois de medir,
    então o ritmo de 15 fps não entra no valor. None se o arquivo não existe ou ficou vazio (queda do processo).
    """
    path = Path(run_dir) / 'frames.csv'
    if not path.exists():
        return None
    with open(path, newline='', encoding='utf-8') as f:
        values = [float(r['track_ms']) for r in csv.DictReader(f) if r.get('track_ms')]
    return float(np.mean(values)) if values else None


def evaluate_run(cfg, meta):
    algo_meta = meta.get('algo') or {}
    row = {k: meta.get(k) for k in ('algorithm', 'sequence', 'condition', 'seed', 'status', 'n_frames', 'wall_s')}
    row['mean_ms_per_frame'] = algo_meta.get('mean_ms_per_frame')
    if row['mean_ms_per_frame'] is None and cfg['algorithms'][meta['algorithm']]['kind'] == 'orbslam2':
        row['mean_ms_per_frame'] = frames_latency(meta['run_dir'])
    row['peak_gpu_mib'] = algo_meta.get('peak_gpu_mib', meta.get('peak_gpu_mib_host'))
    if cfg['algorithms'][meta['algorithm']]['kind'] == 'orbslam2':
        row['peak_gpu_mib'] = None  # roda só em CPU; o valor do host seria ruído de outros processos
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
        if is_static(est):
            row['status'], row['tracked_fraction'] = 'tracking_lost', 0.0
            row['error'] = 'trajetória estática: todas as poses na mesma posição'
            return row
        delta = max(1, round(cfg['evaluation']['rpe_delta_s'] * cfg['dataset']['fps']))
        algo = cfg['algorithms'][meta['algorithm']]
        primary = 'stepscale' if algo.get('step_scale_only') else cfg['evaluation']['monocular_primary']
        row.update(trajectory_metrics(ref, est, algo['monocular'], delta, primary,
                                      cfg['evaluation'].get('rgbd_primary', 'se3')))
    except Exception as exc:  # trajetória curta demais, arquivo corrompido etc.: registrar e seguir
        row['status'], row['error'] = 'eval_error', f'{type(exc).__name__}: {exc}'
    return row


def flag_degenerate(rows, algorithms, factor):
    """Preenche `scale_vs_original` e `degenerate` nas execuções de sensores métricos (não monoculares).

    A referência é a mediana da escala Sim(3) da condição original do mesmo algoritmo e sequência. Em
    monoculares a escala é arbitrária por execução, então ficam None, assim como as execuções sem referência.
    """
    scales = {}
    for r in rows:
        if r['condition'] == 'original' and r['status'] == 'ok' and r.get('sim3_scale') is not None:
            scales.setdefault((r['algorithm'], r['sequence']), []).append(r['sim3_scale'])
    reference = {key: float(np.median(values)) for key, values in scales.items()}
    for r in rows:
        ref, scale = reference.get((r['algorithm'], r['sequence'])), r.get('sim3_scale')
        if algorithms[r['algorithm']]['monocular'] or not ref or scale is None:
            r['scale_vs_original'] = r['degenerate'] = None
            continue
        r['scale_vs_original'] = scale / ref
        r['degenerate'] = not (1 / factor <= r['scale_vs_original'] <= factor)


def summarize(rows, min_tracked_for_ate=0.5):
    """Mediana e IQR por algoritmo × sequência × condição, e degradação do ATE em relação à original.

    - `tracked_fraction` usa todas as execuções: as que não terminam `ok` já entram com 0, senão a mediana
      de um grupo com 3 de 5 sementes perdidas sairia só das sementes boas.
    - O ATE e o RPE só entram das execuções `ok` com fração rastreada >= `min_tracked_for_ate` (protocolo §4:
      abaixo de 50% é falha, como no QueensCAMP). Sem isso o ATE de um trecho de 12% da trajetória parece
      melhor que o da original (RGB-D em `condensation`).
    - `success_rate`: fração das execuções que passam nessas duas condições.
    """
    def valid(r):
        return r['status'] == 'ok' and (r.get('tracked_fraction') or 0.0) >= min_tracked_for_ate

    groups = {}
    for row in rows:
        groups.setdefault((row['algorithm'], row['sequence'], row['condition']), []).append(row)
    summary = []
    for (algorithm, sequence, condition), items in sorted(groups.items()):
        out = {'algorithm': algorithm, 'sequence': sequence, 'condition': condition,
               'n_runs': len(items), 'n_ok': sum(r['status'] == 'ok' for r in items),
               'n_valid': sum(valid(r) for r in items), 'success_rate': sum(valid(r) for r in items) / len(items),
               'n_degenerate': sum(bool(r.get('degenerate')) for r in items)}
        for name in SUMMARY_METRICS:
            pool = items if name == 'tracked_fraction' else [r for r in items if valid(r)]
            values = [r[name] for r in pool if r.get(name) is not None]
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
    flag_degenerate(rows, cfg['algorithms'], cfg['evaluation']['degenerate_scale_factor'])
    out = Path(cfg['paths']['results_root'])
    out.mkdir(parents=True, exist_ok=True)
    write_csv(rows, out / 'metrics.csv', RUN_FIELDS)
    summary = summarize(rows, cfg['evaluation'].get('min_tracked_for_ate', 0.5))
    write_csv(summary, out / 'summary.csv')
    print(f'{len(rows)} execuções avaliadas → {out / "metrics.csv"} e {out / "summary.csv"}')
    return 0


if __name__ == '__main__':
    sys.exit(main())

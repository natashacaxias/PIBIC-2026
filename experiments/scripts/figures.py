#!/usr/bin/env python3
"""Figuras do relatório e do artigo a partir de results/summary.csv (NATASHA-18/20).

  python scripts/figures.py                         # todas as figuras de resumo
  python scripts/figures.py --trajectory RUN_DIR    # + trajetória (vista superior) de uma execução

Gera PDF (vetorial, para o LaTeX) e PNG em <results_root>/figures/:
  degradacao_heatmap   mediana da degradação do ATE (%) por método × condição
  rastreamento         mediana da fração rastreada por método × condição
  erro_cumulativo      fração de sequências com ATE ≤ x (falhas nunca chegam a 1)
  trajetoria_<...>     ground truth × estimativa alinhada

Cores: paleta categórica de referência validada (ordem fixa; cada método mantém sua
cor), marcador distinto por método (codificação secundária, legível em P&B) e escala
divergente azul–cinza–vermelho centrada em zero para a degradação.
"""
import argparse
import csv
import math
from pathlib import Path
import sys

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.queenscamp import load_config, sequence_dir  # noqa: E402

SERIES = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#4a3aa7', '#e34948']
MARKERS = ['o', 's', '^', 'D', 'v', 'P', 'X', '*']
TEXT, TEXT_2, GRID, SURFACE = '#0b0b0b', '#52514e', '#e4e3df', '#fcfcfb'
DIVERGING = LinearSegmentedColormap.from_list('azul_cinza_vermelho', ['#1c5cab', '#86b6ef', '#f0efec', '#ec8f8e', '#b3292a'])
CONDITION_ORDER = ['original', 'underexposure', 'overexposure', 'breakage', 'wet', 'condensation', 'dirt',
                   'smoke_leve', 'smoke_moderada', 'smoke_densa',
                   'dcp_original', 'dcp_smoke_leve', 'dcp_smoke_moderada', 'dcp_smoke_densa']
LABELS = {'original': 'original', 'underexposure': 'subexp.', 'overexposure': 'superexp.', 'breakage': 'quebra',
          'wet': 'molhada', 'condensation': 'condens.', 'dirt': 'sujeira', 'smoke_leve': 'fumaça L',
          'smoke_moderada': 'fumaça M', 'smoke_densa': 'fumaça D', 'dcp_original': 'DCP orig.',
          'dcp_smoke_leve': 'DCP L', 'dcp_smoke_moderada': 'DCP M', 'dcp_smoke_densa': 'DCP D'}


def style():
    plt.rcParams.update({
        'figure.facecolor': SURFACE, 'axes.facecolor': SURFACE, 'savefig.facecolor': SURFACE,
        'axes.edgecolor': GRID, 'axes.labelcolor': TEXT_2, 'axes.titlecolor': TEXT, 'axes.titlesize': 10,
        'axes.labelsize': 9, 'xtick.color': TEXT_2, 'ytick.color': TEXT_2, 'xtick.labelsize': 8, 'ytick.labelsize': 8,
        'axes.grid': True, 'grid.color': GRID, 'grid.linewidth': 0.6, 'axes.spines.top': False,
        'axes.spines.right': False, 'legend.frameon': False, 'legend.fontsize': 8, 'lines.linewidth': 1.5,
        'font.size': 9, 'pdf.fonttype': 42})


def load_summary(path):
    rows = []
    with open(path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            for k, v in row.items():
                if k not in ('algorithm', 'sequence', 'condition'):
                    row[k] = float(v) if v not in ('', None) else None
            rows.append(row)
    return rows


def ordered(values, order):
    return [v for v in order if v in values] + sorted(set(values) - set(order))


def colors_for(algorithms):
    """Cor e marcador seguem o método (ordem fixa da configuração), nunca a posição no gráfico."""
    return {a: (SERIES[i % len(SERIES)], MARKERS[i % len(MARKERS)]) for i, a in enumerate(algorithms)}


def median_table(rows, metric, algorithms, conditions):
    table = np.full((len(algorithms), len(conditions)), np.nan)
    for i, a in enumerate(algorithms):
        for j, c in enumerate(conditions):
            values = [r[metric] for r in rows if r['algorithm'] == a and r['condition'] == c and r.get(metric) is not None]
            if values:
                table[i, j] = np.median(values)
    return table


def save(fig, out, name):
    out.mkdir(parents=True, exist_ok=True)
    for ext in ('pdf', 'png'):
        fig.savefig(out / f'{name}.{ext}', dpi=200, bbox_inches='tight')
    plt.close(fig)
    return out / f'{name}.pdf'


def degradation_heatmap(rows, algorithms, conditions, out):
    conds = [c for c in conditions if c != 'original']
    table = median_table(rows, 'ate_degradation_pct', algorithms, conds)
    finite = table[np.isfinite(table)]
    vmax = max(50.0, float(np.nanmax(finite))) if finite.size else 50.0
    vmin = min(-50.0, float(np.nanmin(finite))) if finite.size else -50.0
    fig, ax = plt.subplots(figsize=(0.62 * len(conds) + 1.6, 0.42 * len(algorithms) + 1.2))
    image = ax.imshow(table, cmap=DIVERGING, norm=TwoSlopeNorm(vcenter=0.0, vmin=vmin, vmax=vmax), aspect='auto')
    ax.grid(False)
    for i in range(len(algorithms)):
        for j in range(len(conds)):
            value = table[i, j]
            ax.text(j, i, '–' if math.isnan(value) else f'{value:+.0f}', ha='center', va='center', fontsize=7, color=TEXT)
    ax.set_xticks(range(len(conds)), [LABELS.get(c, c) for c in conds], rotation=40, ha='right')
    ax.set_yticks(range(len(algorithms)), algorithms)
    bar = fig.colorbar(image, ax=ax, fraction=0.04, pad=0.02)
    bar.set_label('degradação do ATE (%)\nvs. original do próprio método')
    bar.outline.set_visible(False)
    ax.set_title('Degradação mediana do ATE por condição (– = sem execução válida)', loc='left')
    return save(fig, out, 'degradacao_heatmap')


def tracking_dots(rows, algorithms, conditions, out):
    table = median_table(rows, 'tracked_fraction_median', algorithms, conditions)
    palette = colors_for(algorithms)
    fig, ax = plt.subplots(figsize=(0.55 * len(conditions) + 1.8, 3.0))
    offsets = np.linspace(-0.25, 0.25, len(algorithms)) if len(algorithms) > 1 else [0.0]
    for i, a in enumerate(algorithms):
        color, marker = palette[a]
        ax.plot(np.arange(len(conditions)) + offsets[i], table[i], linestyle='none', marker=marker, markersize=6,
                color=color, markeredgecolor=SURFACE, markeredgewidth=1.0, label=a)
    ax.axhline(0.8, color=TEXT_2, linewidth=0.8, linestyle='--')
    ax.text(len(conditions) - 0.5, 0.81, 'limiar 0,8', ha='right', va='bottom', fontsize=7, color=TEXT_2)
    ax.set_ylim(-0.03, 1.05)
    ax.set_ylabel('fração rastreada (mediana)')
    ax.set_xticks(range(len(conditions)), [LABELS.get(c, c) for c in conditions], rotation=40, ha='right')
    ax.legend(loc='lower left', ncol=min(4, len(algorithms)))
    ax.set_title('Rastreamento por condição', loc='left')
    return save(fig, out, 'rastreamento')


def cumulative_error(rows, algorithms, conditions, out, panels):
    palette = colors_for(algorithms)
    panels = [c for c in panels if c in conditions] or conditions[:3]
    fig, axes = plt.subplots(1, len(panels), figsize=(3.0 * len(panels), 2.8), sharey=True, squeeze=False)
    all_ate = [r['ate_m_median'] for r in rows if r.get('ate_m_median') is not None]
    xmax = float(np.percentile(all_ate, 95)) * 1.1 if all_ate else 1.0
    grid_x = np.linspace(0, xmax, 200)
    for ax, condition in zip(axes[0], panels):
        for a in algorithms:
            items = [r for r in rows if r['algorithm'] == a and r['condition'] == condition]
            if not items:
                continue
            ate = np.array([r['ate_m_median'] if r.get('ate_m_median') is not None else np.inf for r in items])
            frac = [(ate <= x).mean() for x in grid_x]
            color, marker = palette[a]
            # marcadores espaçados ao longo da curva: identidade sem depender só da cor
            # (rótulos na ponta colidiriam, pois várias curvas terminam em 1)
            offset = 8 * algorithms.index(a)
            ax.plot(grid_x, frac, color=color, label=a, marker=marker, markersize=5, markevery=(offset, 40),
                    markeredgecolor=SURFACE, markeredgewidth=0.8)
        ax.set_title(LABELS.get(condition, condition), loc='left')
        ax.set_xlabel('ATE (m)')
        ax.set_ylim(0, 1.02)
    axes[0][0].set_ylabel('fração de sequências com ATE ≤ x')
    handles, labels = axes[0][0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='lower center', ncol=min(5, len(labels)), bbox_to_anchor=(0.5, -0.12))
    fig.suptitle('Erro cumulativo (curvas que não chegam a 1 = sequências com falha)', x=0.01, y=1.06, ha='left',
                 fontsize=10)
    return save(fig, out, 'erro_cumulativo')


def trajectory(cfg, run_dir, out):
    from evo.core import sync
    from evo.tools import file_interface
    import json
    from evaluate import ate, step_scaled
    meta = json.loads((Path(run_dir) / 'meta.json').read_text())
    gt = file_interface.read_tum_trajectory_file(str(sequence_dir(cfg, meta['sequence']) / cfg['dataset']['groundtruth_file']))
    est = file_interface.read_tum_trajectory_file(str(Path(run_dir) / 'trajectory_tum.txt'))
    ref, est = sync.associate_trajectories(gt, est, cfg['evaluation']['max_time_diff_s'])
    algo = cfg['algorithms'][meta['algorithm']]
    if algo['monocular']:
        stepscale = algo.get('step_scale_only') or cfg['evaluation']['monocular_primary'] == 'stepscale'
        rmse, aligned = ate(ref, step_scaled(est, ref), False) if stepscale else ate(ref, est, True)
    else:
        rmse, aligned = ate(ref, est, False)
    color, marker = colors_for(list(cfg['algorithms']))[meta['algorithm']]
    fig, ax = plt.subplots(figsize=(3.6, 3.6))
    ax.plot(ref.positions_xyz[:, 0], ref.positions_xyz[:, 1], color=TEXT_2, linewidth=1.5, label='ground truth')
    ax.plot(aligned.positions_xyz[:, 0], aligned.positions_xyz[:, 1], color=color, linewidth=1.5, linestyle='--',
            label=f"{meta['algorithm']} (ATE {rmse:.2f} m)")
    ax.plot(*ref.positions_xyz[0, :2], marker=marker, color=TEXT_2, markersize=6)
    ax.set_aspect('equal', adjustable='datalim')
    ax.set_xlabel('x (m)')
    ax.set_ylabel('y (m)')
    ax.legend(loc='upper left', bbox_to_anchor=(0, -0.18))
    ax.set_title(f"seq {meta['sequence']} · {LABELS.get(meta['condition'], meta['condition'])} · seed {meta['seed']}",
                 loc='left')
    return save(fig, out, f"trajetoria_{meta['algorithm']}_{meta['sequence']}_{meta['condition']}_s{meta['seed']}")


def make_all(cfg, summary_path, out, panels):
    style()
    rows = load_summary(summary_path)
    algorithms = ordered({r['algorithm'] for r in rows}, list(cfg['algorithms']))
    conditions = ordered({r['condition'] for r in rows}, CONDITION_ORDER)
    return [degradation_heatmap(rows, algorithms, conditions, out), tracking_dots(rows, algorithms, conditions, out),
            cumulative_error(rows, algorithms, conditions, out, panels)]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--config', default=str(Path(__file__).resolve().parents[1] / 'config/experiment.json'))
    parser.add_argument('--panels', nargs='+', default=['original', 'wet', 'smoke_densa'],
                        help='condições do gráfico de erro cumulativo')
    parser.add_argument('--trajectory', nargs='*', default=[], help='diretórios de execução para plotar')
    args = parser.parse_args()
    cfg = load_config(args.config)
    results = Path(cfg['paths']['results_root'])
    out = results / 'figures'
    files = make_all(cfg, results / 'summary.csv', out, args.panels)
    files += [trajectory(cfg, run, out) for run in args.trajectory]
    print('\n'.join(str(f) for f in files))
    return 0


if __name__ == '__main__':
    sys.exit(main())

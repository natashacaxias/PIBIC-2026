#!/usr/bin/env python3
"""Análise estatística da etapa 5 da proposta, a partir de results/summary.csv.

Unidade de análise: sequência (mediana das repetições), pareada entre métodos ou
entre condições. Três saídas em <results_root>/:

  stats_pairwise.csv      métodos A × B em cada condição, sobre a degradação
                          relativa do ATE (%): Wilcoxon pareado, r bisserial de
                          postos, IC 95% bootstrap da mediana das diferenças,
                          p ajustado por Bonferroni (família: todos os pares × condições)
  stats_vs_original.csv   cada método, condição × original, sobre o ATE:
                          Wilcoxon pareado e Bonferroni (família: métodos × condições)
  stats_robustness.csv    critério relativo de robustez (docs/protocolo_experimental.md §5)
  stats_exploratory.csv   condições de evaluation.exploratory_conditions (ex.: smoke_extrema): contra a original,
                          com Bonferroni só entre elas; ficam fora das famílias acima
  stats_report.md         as tabelas em Markdown

Sequências sem ATE (nenhuma execução válida) ficam fora dos testes de ATE e
contam como falha no critério de rastreamento.
"""
import argparse
import csv
from itertools import combinations
import math
from pathlib import Path
import sys

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.queenscamp import load_config  # noqa: E402

MIN_PAIRS = 6  # abaixo disso o Wilcoxon bilateral não atinge p < 0,05


def load_summary(path):
    rows = []
    with open(path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            for key, value in row.items():
                if key not in ('algorithm', 'sequence', 'condition'):
                    row[key] = float(value) if value not in ('', None) else None
            rows.append(row)
    return rows


def index(rows, metric):
    table = {}
    for r in rows:
        if r.get(metric) is not None and not math.isnan(r[metric]):
            table.setdefault((r['algorithm'], r['condition']), {})[r['sequence']] = r[metric]
    return table


def paired(table, key_a, key_b):
    a, b = table.get(key_a, {}), table.get(key_b, {})
    common = sorted(set(a) & set(b))
    return np.array([a[s] for s in common]), np.array([b[s] for s in common])


def rank_biserial(diff):
    """Correlação bisserial de postos para o Wilcoxon pareado (zeros descartados)."""
    diff = diff[diff != 0]
    if diff.size == 0:
        return 0.0
    ranks = stats.rankdata(np.abs(diff))
    pos, neg = ranks[diff > 0].sum(), ranks[diff < 0].sum()
    return float((pos - neg) / (pos + neg))


def bootstrap_median_ci(diff, n_boot=10000, seed=0, level=0.95):
    rng = np.random.default_rng(seed)
    samples = rng.choice(diff, size=(n_boot, diff.size), replace=True)
    medians = np.median(samples, axis=1)
    alpha = (1 - level) / 2
    return float(np.quantile(medians, alpha)), float(np.quantile(medians, 1 - alpha))


def compare(x, y, n_boot, seed):
    """Teste pareado x − y. Retorna dicionário com n, mediana da diferença, IC, p e efeito."""
    diff = x - y
    out = {'n': int(diff.size), 'median_a': None, 'median_b': None, 'median_diff': None,
           'ci_low': None, 'ci_high': None, 'p': None, 'effect_r': None}
    if diff.size == 0:
        return out
    out.update(median_a=float(np.median(x)), median_b=float(np.median(y)), median_diff=float(np.median(diff)))
    out['ci_low'], out['ci_high'] = bootstrap_median_ci(diff, n_boot, seed)
    out['effect_r'] = rank_biserial(diff)
    if diff.size >= MIN_PAIRS and np.any(diff != 0):
        out['p'] = float(stats.wilcoxon(x, y, zero_method='wilcox', alternative='two-sided').pvalue)
    return out


def bonferroni(results):
    m = sum(r['p'] is not None for r in results)
    for r in results:
        r['p_bonferroni'] = min(1.0, r['p'] * m) if r['p'] is not None else None
        r['m_tests'] = m
    return results


def pairwise(rows, n_boot=10000, seed=0):
    table = index(rows, 'ate_degradation_pct')
    algorithms = sorted({r['algorithm'] for r in rows})
    conditions = sorted({r['condition'] for r in rows} - {'original'})
    results = []
    for condition in conditions:
        for a, b in combinations(algorithms, 2):
            x, y = paired(table, (a, condition), (b, condition))
            results.append(dict(condition=condition, algorithm_a=a, algorithm_b=b, metric='ate_degradation_pct',
                                **compare(x, y, n_boot, seed)))
    return bonferroni(results)


def vs_original(rows, n_boot=10000, seed=0):
    table = index(rows, 'ate_m_median')
    results = []
    for algorithm in sorted({r['algorithm'] for r in rows}):
        for condition in sorted({r['condition'] for r in rows if r['algorithm'] == algorithm} - {'original'}):
            x, y = paired(table, (algorithm, condition), (algorithm, 'original'))
            results.append(dict(algorithm=algorithm, condition=condition, metric='ate_m_median',
                                **compare(x, y, n_boot, seed)))
    return bonferroni(results)


def robustness(rows, min_tracking=0.8, coverage=0.75, max_degradation_pct=50.0):
    """Robusto se rastreamento ≥ min_tracking em ≥ coverage das sequências e degradação mediana ≤ limite."""
    groups = {}
    for r in rows:
        groups.setdefault((r['algorithm'], r['condition']), []).append(r)
    out = []
    for (algorithm, condition), items in sorted(groups.items()):
        tracking = [r.get('tracked_fraction_median') or 0.0 for r in items]
        frac_ok = float(np.mean([t >= min_tracking for t in tracking]))
        degr = [r['ate_degradation_pct'] for r in items if r.get('ate_degradation_pct') is not None]
        median_degr = float(np.median(degr)) if degr else None
        robust = frac_ok >= coverage and (condition == 'original' or (median_degr is not None and median_degr <= max_degradation_pct))
        out.append(dict(algorithm=algorithm, condition=condition, n_sequences=len(items),
                        frac_sequences_tracking_ok=frac_ok, median_ate_degradation_pct=median_degr, robust=robust))
    return out


def split_exploratory(rows, names):
    """Separa as condições exploratórias; a original só acompanha os algoritmos que as têm."""
    names = set(names)
    exploratory_algorithms = {r['algorithm'] for r in rows if r['condition'] in names}
    main = [r for r in rows if r['condition'] not in names]
    exploratory = [r for r in rows if r['condition'] in names
                   or (r['condition'] == 'original' and r['algorithm'] in exploratory_algorithms)]
    return main, exploratory


def exploratory_results(rows, names, n_boot=10000, seed=0, **robust_args):
    """ATE contra a original e critério de robustez das condições exploratórias, Bonferroni só entre elas."""
    names = set(names)
    _, exploratory = split_exploratory(rows, names)
    if not any(r['condition'] in names for r in exploratory):
        return []
    robust = {(r['algorithm'], r['condition']): r for r in robustness(exploratory, **robust_args)}
    out = []
    for result in vs_original(exploratory, n_boot, seed):
        extra = robust[(result['algorithm'], result['condition'])]
        out.append({**result, 'n_sequences': extra['n_sequences'],
                    'frac_sequences_tracking_ok': extra['frac_sequences_tracking_ok'],
                    'median_ate_degradation_pct': extra['median_ate_degradation_pct'], 'robust': extra['robust']})
    return out


def write_csv(rows, path):
    if not rows:
        return
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def fmt(value, digits=3):
    if value is None:
        return '–'
    if isinstance(value, bool):
        return 'sim' if value else 'não'
    if isinstance(value, float):
        return f'{value:.{digits}g}'
    return str(value)


def markdown_table(rows, columns):
    lines = ['| ' + ' | '.join(columns) + ' |', '|' + '---|' * len(columns)]
    lines += ['| ' + ' | '.join(fmt(r.get(c)) for c in columns) + ' |' for r in rows]
    return '\n'.join(lines)


def report(pair, vs_orig, robust, params, exploratory=()):
    sections = [
        '# Relatório estatístico',
        f"Parâmetros: bootstrap {params['n_boot']} reamostragens (semente {params['seed']}); "
        f"robustez: rastreamento ≥ {params['min_tracking']} em ≥ {params['coverage']:.0%} das sequências e "
        f"degradação mediana do ATE ≤ {params['max_degradation']}%. Testes com menos de {MIN_PAIRS} pares não têm p.",
        '## Métodos comparados por condição (degradação relativa do ATE, %)',
        markdown_table(pair, ['condition', 'algorithm_a', 'algorithm_b', 'n', 'median_a', 'median_b', 'median_diff',
                              'ci_low', 'ci_high', 'effect_r', 'p', 'p_bonferroni']),
        '## Cada condição contra a original (ATE, m)',
        markdown_table(vs_orig, ['algorithm', 'condition', 'n', 'median_a', 'median_b', 'median_diff', 'ci_low',
                                 'ci_high', 'effect_r', 'p', 'p_bonferroni']),
        '## Critério de robustez',
        markdown_table(robust, ['algorithm', 'condition', 'n_sequences', 'frac_sequences_tracking_ok',
                                'median_ate_degradation_pct', 'robust']),
    ]
    if exploratory:
        sections += ['## Condições exploratórias (fora das famílias de Bonferroni; p ajustado só entre elas)',
                     markdown_table(exploratory, ['algorithm', 'condition', 'n', 'median_a', 'median_b', 'effect_r', 'p',
                                                  'p_bonferroni', 'frac_sequences_tracking_ok',
                                                  'median_ate_degradation_pct', 'robust'])]
    return '\n\n'.join(sections) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--config', default=str(Path(__file__).resolve().parents[1] / 'config/experiment.json'))
    parser.add_argument('--n-boot', type=int, default=10000)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--min-tracking', type=float, default=0.8)
    parser.add_argument('--coverage', type=float, default=0.75)
    parser.add_argument('--max-degradation', type=float, default=50.0, help='limite X da degradação mediana (%%)')
    args = parser.parse_args()
    cfg = load_config(args.config)
    out = Path(cfg['paths']['results_root'])
    all_rows = load_summary(out / 'summary.csv')
    names = cfg['evaluation'].get('exploratory_conditions', [])
    rows, _ = split_exploratory(all_rows, names)
    pair = pairwise(rows, args.n_boot, args.seed)
    vs_orig = vs_original(rows, args.n_boot, args.seed)
    robust = robustness(rows, args.min_tracking, args.coverage, args.max_degradation)
    exploratory = exploratory_results(all_rows, names, args.n_boot, args.seed, min_tracking=args.min_tracking,
                                      coverage=args.coverage, max_degradation_pct=args.max_degradation)
    write_csv(pair, out / 'stats_pairwise.csv')
    write_csv(vs_orig, out / 'stats_vs_original.csv')
    write_csv(robust, out / 'stats_robustness.csv')
    write_csv(exploratory, out / 'stats_exploratory.csv')
    params = dict(n_boot=args.n_boot, seed=args.seed, min_tracking=args.min_tracking, coverage=args.coverage,
                  max_degradation=args.max_degradation)
    (out / 'stats_report.md').write_text(report(pair, vs_orig, robust, params, exploratory), encoding='utf-8')
    print(f'{len(pair)} comparações entre métodos, {len(vs_orig)} contra a original → {out / "stats_report.md"}')
    return 0


if __name__ == '__main__':
    sys.exit(main())

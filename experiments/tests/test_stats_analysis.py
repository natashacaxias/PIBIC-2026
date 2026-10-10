"""Testes do script estatístico com um summary.csv sintético de efeito conhecido."""
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))

import stats_analysis as st  # noqa: E402


def synthetic_rows(n_seq=16, seed=0):
    """'robusto' degrada ~10%, 'fragil' ~120% e perde rastreamento em metade das sequências."""
    rng = np.random.default_rng(seed)
    rows = []
    for algo, degr, lost in (('robusto', 10.0, 0), ('fragil', 120.0, n_seq // 2)):
        for i in range(n_seq):
            base = 0.2 + 0.05 * rng.random()
            rows.append(dict(algorithm=algo, sequence=f'{i:02d}', condition='original', ate_m_median=base,
                             tracked_fraction_median=1.0, ate_degradation_pct=0.0))
            d = degr + rng.normal(0, 5)
            rows.append(dict(algorithm=algo, sequence=f'{i:02d}', condition='smoke_densa',
                             ate_m_median=base * (1 + d / 100), tracked_fraction_median=0.3 if i < lost else 0.95,
                             ate_degradation_pct=d))
    return rows


class StatisticsTest(unittest.TestCase):
    def setUp(self):
        self.rows = synthetic_rows()

    def test_pairwise_detects_known_difference(self):
        res = st.pairwise(self.rows, n_boot=2000)
        self.assertEqual(len(res), 1)
        r = res[0]
        self.assertEqual(r['n'], 16)
        self.assertLess(r['p_bonferroni'], 0.001)
        self.assertEqual((r['algorithm_a'], r['algorithm_b']), ('fragil', 'robusto'))
        self.assertGreater(r['ci_low'], 0)  # diferença fragil − robusto ≈ +110 pontos percentuais
        self.assertGreater(r['effect_r'], 0.9)

    def test_vs_original_and_bonferroni_family(self):
        res = st.vs_original(self.rows, n_boot=2000)
        self.assertEqual({r['m_tests'] for r in res}, {2})
        by_algo = {r['algorithm']: r for r in res}
        self.assertLess(by_algo['fragil']['p_bonferroni'], 0.001)
        self.assertGreater(by_algo['fragil']['median_diff'], 0)

    def test_robustness_criterion(self):
        res = {(r['algorithm'], r['condition']): r for r in st.robustness(self.rows)}
        self.assertTrue(res[('robusto', 'smoke_densa')]['robust'])
        self.assertFalse(res[('fragil', 'smoke_densa')]['robust'])
        self.assertAlmostEqual(res[('fragil', 'smoke_densa')]['frac_sequences_tracking_ok'], 0.5)

    def test_small_samples_have_no_p_value(self):
        res = st.pairwise(synthetic_rows(n_seq=4), n_boot=500)
        self.assertIsNone(res[0]['p'])
        self.assertIsNotNone(res[0]['ci_low'])

    def test_rank_biserial_extremes(self):
        self.assertEqual(st.rank_biserial(np.array([1.0, 2.0, 3.0])), 1.0)
        self.assertEqual(st.rank_biserial(np.array([-1.0, -2.0])), -1.0)


if __name__ == '__main__':
    unittest.main()

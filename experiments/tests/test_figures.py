"""Gera as figuras a partir de resultados sintéticos e confere que os arquivos existem."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'tests'))

try:
    import figures
except ImportError:  # matplotlib/evo ausentes
    figures = None

from test_pipeline import make_config  # noqa: E402


def synthetic_summary(path):
    rng = np.random.default_rng(0)
    fields = ['algorithm', 'sequence', 'condition', 'ate_m_median', 'tracked_fraction_median', 'ate_degradation_pct']
    lines = [','.join(fields)]
    for algo, base, slope in (('orbslam2_mono', 0.2, 3.0), ('tartanvo', 0.6, 0.6), ('dpvo', 0.15, 1.0)):
        for seq in range(16):
            for k, cond in enumerate(['original', 'wet', 'dirt', 'smoke_leve', 'smoke_densa']):
                degr = 0.0 if cond == 'original' else slope * 25 * k + rng.normal(0, 5)
                failed = algo == 'orbslam2_mono' and cond == 'smoke_densa' and seq < 6
                ate = '' if failed else f'{base * (1 + degr / 100):.4f}'
                lines.append(f'{algo},{seq:02d},{cond},{ate},{0.2 if failed else 0.97},{"" if failed else f"{degr:.2f}"}')
    Path(path).write_text('\n'.join(lines) + '\n')


@unittest.skipIf(figures is None, 'matplotlib não instalado')
class FiguresTest(unittest.TestCase):
    def test_summary_figures_and_trajectory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg = make_config(root)
            (root / 'res').mkdir()
            synthetic_summary(root / 'res' / 'summary.csv')
            files = figures.make_all(cfg, root / 'res' / 'summary.csv', root / 'res' / 'figures',
                                     ['original', 'wet', 'smoke_densa'])
            for f in files:
                self.assertGreater(f.stat().st_size, 1000, f)
                self.assertTrue(f.with_suffix('.png').exists())
            # trajetória de uma execução sintética
            t = np.arange(120) / 15.0
            gt = np.stack([np.cos(t), np.sin(t), 0.05 * t], 1)
            seq_dir = root / 'qc' / '09'
            seq_dir.mkdir(parents=True)
            run = root / 'runs' / 'dpvo' / '09' / 'original' / 'seed0'
            run.mkdir(parents=True)
            for path, pts in ((seq_dir / 'groundtruth.txt', gt), (run / 'trajectory_tum.txt', 2 * gt)):
                path.write_text(''.join(f'{ti:.6f} {p[0]} {p[1]} {p[2]} 0 0 0 1\n' for ti, p in zip(t, pts)))
            (run / 'meta.json').write_text(json.dumps(dict(algorithm='dpvo', sequence='09', condition='original',
                                                           seed=0, run_dir=str(run))))
            figures.style()
            pdf = figures.trajectory(cfg, run, root / 'res' / 'figures')
            self.assertTrue(pdf.exists())


if __name__ == '__main__':
    unittest.main()

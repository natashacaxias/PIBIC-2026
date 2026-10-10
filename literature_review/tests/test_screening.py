import csv
from pathlib import Path
import tempfile
import unittest
import review
import screening


class ScreeningTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = review.connect(self.root/'corpus.sqlite3')

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def add(self, title, abstract=None, theme='robustness_corruptions'):
        record = {'title':title,'authors':['A. Author'],'year':2023,'doi':None,'arxiv_id':None,'kind':'publication','abstract':abstract}
        with self.db:
            return review.upsert(self.db,record,('run1','crossref',theme,'q','raw.json'))[0]

    def test_rules(self):
        self.assertEqual(screening.classify('Editorial',None)[0],'EXCLUDE')
        self.assertEqual(screening.classify('Protein folding with transformers',None)[1],'E2 fora do escopo')
        self.assertEqual(screening.classify('Robust visual odometry in fog',None)[0],'INCLUDE')
        self.assertEqual(screening.classify('Visual odometry for cars',None)[0],'MAYBE')
        self.assertEqual(screening.classify('Single image dehazing',None)[0],'MAYBE')
        self.assertEqual(screening.classify('Dehazing of camera images in heavy smoke',None)[0],'MAYBE')
        self.assertEqual(screening.classify('Visual SLAM in smoke-filled rooms',None)[0],'INCLUDE')

    def test_suggest_skips_reviewed_and_never_writes_decisions(self):
        a = self.add('Robust visual SLAM under adverse weather')
        b = self.add('Front matter')
        with self.db:
            review.record_review(self.db,b,'EXCLUDE','já revisado')
        rows = screening.suggest(self.db)
        self.assertEqual([r['paper_id'] for r in rows],[f'P{a:04d}'])
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM reviews').fetchone()[0],1)

    def test_apply_only_filled_rows_and_requires_reason(self):
        a = self.add('Robust visual SLAM under adverse weather')
        b = self.add('Deep visual odometry benchmark')
        rows = screening.suggest(self.db)
        rows[0].update(decisao_humana='include',justificativa_humana='robustez + clima')
        path = self.root/'triagem.csv'
        screening.write_csv(rows,path)
        self.assertEqual(screening.apply(self.db,path),1)
        statuses = dict(self.db.execute('SELECT id,status FROM papers'))
        self.assertEqual(sorted(statuses.values()),['SCREEN_INCLUDED','SCREEN_PENDING'])
        with open(path,newline='',encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
        rows[1].update(decisao_humana='EXCLUDE',justificativa_humana='  ')
        screening.write_csv(rows,path)
        with self.assertRaises(ValueError):
            screening.apply(self.db,path)
        self.assertEqual(self.db.execute('SELECT status FROM papers WHERE id=?',(b,)).fetchone()[0],'SCREEN_PENDING')


if __name__ == '__main__':
    unittest.main()

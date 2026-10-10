import argparse
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import review


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = review.connect(self.root/'corpus.sqlite3')
        self.record = {'title':'DROID-SLAM: Visual SLAM','authors':['A. Author'],'year':2021,'doi':'https://doi.org/10.1234/ABC','arxiv_id':None,'kind':'publication','abstract':None}
        self.origin = ('run1','crossref','deep_vo_slam','query','raw.json')

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def add(self, record=None, origin=None):
        with self.db:
            return review.upsert(self.db,record or self.record,origin or self.origin)

    def test_incremental_ids_and_review_preserved(self):
        pid,_ = self.add()
        self.db.execute('INSERT INTO reviews VALUES(?,?,?,?)',(pid,'INCLUDE','revisado','today'))
        self.db.execute('UPDATE papers SET status=? WHERE id=?',('SCREEN_INCLUDED',pid))
        self.db.commit()
        record = dict(self.record,doi='10.1234/abc',abstract='Resumo recebido depois')
        other,created = self.add(record,('run2','crossref','robustness_corruptions','query2','raw2.json'))
        self.assertEqual(pid,other)
        self.assertFalse(created)
        review.export(self.db,self.root/'exports')
        paper = json.loads((self.root/'exports/papers.json').read_text())[0]
        self.assertEqual(paper['human_review']['decision'],'INCLUDE')
        self.assertEqual(len(paper['search_themes']),2)
        self.assertEqual(paper['abstract'],'Resumo recebido depois')

    def test_preprint_publication_are_separate(self):
        pid,_ = self.add()
        other,created = self.add(dict(self.record,kind='preprint',arxiv_id='2108.00001'))
        self.assertTrue(created)
        self.assertNotEqual(pid,other)

    def test_conflicting_dois_are_not_merged_by_title(self):
        self.add()
        _,created = self.add(dict(self.record,doi='10.1234/different'))
        self.assertTrue(created)

    def test_title_without_identifiers_requires_author_and_year(self):
        self.add(dict(self.record,doi=None))
        _,created = self.add(dict(self.record,doi=None,title='DROID SLAM Visual SLAM'))
        self.assertFalse(created)
        _,created = self.add(dict(self.record,doi=None,authors=['Different Author']))
        self.assertTrue(created)

    def test_arxiv_parse_and_version(self):
        payload = b'''<feed xmlns="http://www.w3.org/2005/Atom" xmlns:o="http://a9.com/-/spec/opensearch/1.1/">
        <o:totalResults>1</o:totalResults><entry><id>http://arxiv.org/abs/2108.00001v2</id><title> Visual SLAM </title><published>2021-08-01T00:00:00Z</published><author><name>A</name></author><summary>Test</summary></entry></feed>'''
        records,total = review.parse_arxiv(payload)
        self.assertEqual(total,1)
        self.assertEqual(records[0]['arxiv_id'],'2108.00001')
        self.assertIsNone(records[0]['doi'])

    def test_pagination_and_raw_preserved(self):
        class FakeClient:
            def __init__(self):
                self.urls=[]
            def get(self,source,url):
                self.urls.append(url)
                size = 100 if len(self.urls)==1 else 1
                return json.dumps({'message':{'items':[{'title':['Paper'],'DOI':f'10.x/{n}'} for n in range(size)],'total-results':101,'next-cursor':'next'}}).encode()
        client = FakeClient()
        audit={'requests':[]}
        result = list(review.fetch(client,'crossref','query',2010,2026,101,self.root,audit))
        self.assertEqual(len(result),101)
        self.assertEqual(len(client.urls),2)
        self.assertIn('cursor=next',client.urls[1])
        self.assertEqual(len(list(self.root.glob('page_*.json'))),2)
        self.assertFalse(audit['limit_reached'])

    def test_malformed_payload_preserved(self):
        class FakeClient:
            def get(self,*args): return b'broken payload'
        audit={'requests':[]}
        with self.assertRaises(ValueError):
            list(review.fetch(FakeClient(),'crossref','query',2010,2026,1,self.root,audit))
        self.assertEqual((self.root/'page_001.json').read_bytes(),b'broken payload')

    def test_partial_failure_keeps_results_and_records_error(self):
        config = self.root/'config.json'
        config.write_text(json.dumps({'sources':['crossref','arxiv'],'year_to':2026,
            'max_results_per_query':1,'themes':{'test':{'year_from':2020,'queries':['visual odometry']}}}))
        def fake_fetch(client,source,query,y1,y2,limit,directory,audit):
            if source == 'arxiv':
                raise ValueError('Falha simulada')
            raw = directory/'page.json'
            raw.write_text('{}')
            yield self.record,raw
        args = argparse.Namespace(config=config,source=None,theme=None,limit=1,
            pilot=False,dry_run=False,no_xlsx=True,data=self.root/'run_data')
        with patch.object(review,'fetch',fake_fetch), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            result = review.run(args)
        self.assertEqual(result,1)
        summary = json.loads(next((args.data/'runs').glob('*/summary.json')).read_text())
        self.assertEqual(summary['status'],'partial_or_failed')
        self.assertEqual(summary['corpus_size'],1)
        self.assertEqual(summary['errors'],1)
        self.assertEqual(summary['new'],1)

    def test_arxiv_translation(self):
        value = review.arxiv_query('"visual odometry" fog',2015,2026)
        self.assertIn('all:"visual odometry" AND all:fog',value)
        self.assertIn('201501010000 TO 202612312359',value)


if __name__ == '__main__':
    unittest.main()

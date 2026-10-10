import json
from pathlib import Path
import tempfile
import unittest

import review
import extraction
from workbook_export import snapshot, text_chunks
from test_extraction import pdf_with_text, document


class WorkbookSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.db=review.connect(self.root/'corpus.sqlite3')
        self.abstract=('Resumo com acentuação e conteúdo longo. '*80)+' Fim.'
        with self.db:
            review.upsert(self.db,{'title':'Visual SLAM Test','authors':['Test Author'],
                'year':2025,'kind':'publication','abstract':self.abstract,'url':'https://example.org/paper'},
                ('run','crossref','test','query','page.json'))

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def test_abstract_preserved_without_truncation(self):
        chunks=list(text_chunks(self.abstract))
        self.assertEqual(''.join(chunks),self.abstract)
        self.assertTrue(all(len(c)<=650 for c in chunks))

    def test_empty_corpus(self):
        db=review.connect(self.root/'empty.sqlite3')
        try:
            data=snapshot(db,self.root)
            self.assertEqual(data['papers'],[])
            self.assertEqual(data['evidence'],[])
        finally:
            db.close()

    def test_pending_does_not_create_scientific_results(self):
        data=snapshot(self.db,self.root)
        self.assertEqual(data['papers'][0][10],'PENDENTE')
        self.assertEqual(data['evidence'],[])
        self.assertEqual(data['synthesis'],[])
        self.assertEqual(''.join(r[2] for r in data['abstracts']),self.abstract)

    def test_saved_human_decision_is_exported(self):
        with self.db:
            self.db.execute('INSERT INTO reviews VALUES(?,?,?,?)',(1,'MAYBE','Conferir texto integral',review.now()))
        data=snapshot(self.db,self.root)
        self.assertEqual(data['papers'][0][10:12],['MAYBE','Conferir texto integral'])

    def accepted(self):
        extraction.setup(self.db)
        pdf=self.root/'test.pdf'
        pdf_with_text(pdf)
        bundle,_=extraction.prepare(self.db,self.root,'P0001',pdf)
        output=self.root/'extraction.json'
        links=self.root/'links.json'
        extraction.write_json(output,document())
        extraction.write_json(links,{'/paper/main_contribution':['E001']})
        path,report=extraction.accept(self.db,bundle,output,links,'synthetic-test')
        self.assertTrue(report['valid'])
        return path

    def test_validated_evidence_and_numeric_types_exported(self):
        self.accepted()
        data=snapshot(self.db,self.root)
        self.assertEqual(len(data['evidence']),1)
        self.assertEqual(data['evidence'][0][5],1)
        self.assertEqual(data['papers'][0][12],'EXTRACTED')
        year=next(r for r in data['synthesis'] if r[2]=='/paper/year')
        self.assertIsNone(year[3])
        self.assertEqual(year[4],2025)
        claim=next(r for r in data['synthesis'] if r[2]=='/paper/main_contribution')
        self.assertEqual(claim[6],'E001')

    def test_tampered_extraction_blocks_export(self):
        path=self.accepted()
        (path/'extraction.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'alterada'):
            snapshot(self.db,self.root)


if __name__=='__main__':
    unittest.main()

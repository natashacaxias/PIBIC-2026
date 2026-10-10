import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject

import extraction as ex
import review


def pdf_with_text(path):
    writer = PdfWriter()
    page = writer.add_blank_page(width=600,height=800)
    font = DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
    page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):writer._add_object(font)})})
    stream = DecodedStreamObject()
    stream.set_data(b'BT /F1 12 Tf 50 750 Td (Visual SLAM Test. The method estimates camera motion. Synthetic fixture for software testing only.) Tj ET')
    page[NameObject('/Contents')] = writer._add_object(stream)
    writer.write(path)


def document():
    return {'schema_version':'1.0.0','paper':{'paper_id':'P0001','title':'Visual SLAM Test','authors':['Test Author'],'year':2025,
        'publication_type':'other','research_problem':None,'main_contribution':'The method estimates camera motion.',
        'main_results':[],'method_family':[],'sensor_modalities':[],'environment':[],'datasets':[],
        'evaluation_metrics':[],'limitations_authors':[],'limitations_reviewer':[],'code_available':'NR','dataset_available':'NR'},
        'classification':{'theme_primary':'other','themes_secondary':[],'review_function':[],
            'priority':'COMPLEMENTARY','relevance_score':0,'relevance_to_project':'Synthetic test fixture.'},
        'evidence':[{'evidence_id':'E001','claim_type':'method','claim':'Estimates motion.',
            'quote_or_paraphrase':'The method estimates camera motion.','location':{'page':1},'support_level':'direct'}],
        'modules':{}}


class ExtractionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = review.connect(self.root/'corpus.sqlite3')
        ex.setup(self.db)
        with self.db:
            review.upsert(self.db,{'title':'Visual SLAM Test','authors':['Test Author'],'year':2025,'kind':'publication'},('test','test','test','test','fixture'))
        self.doc = document()
        self.links = {'/paper/main_contribution':['E001']}
        self.schema = ex.read_json(ex.SCHEMA)
        self.metadata = {'title':'Visual SLAM Test'}

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def validate(self):
        return ex.validate(self.doc,self.links,self.schema,'P0001',1,self.metadata)

    def bundle(self):
        pdf = self.root/'fixture.pdf'
        pdf_with_text(pdf)
        return ex.prepare(self.db,self.root,'P0001',pdf)[0]

    def test_valid_document_and_original_schema(self):
        self.assertTrue(self.validate()['valid'])

    def test_wrong_enum_and_missing_required_field(self):
        self.doc['paper']['publication_type'] = 'invented'
        del self.doc['classification']['priority']
        self.assertGreaterEqual(len(self.validate()['errors']),2)

    def test_missing_central_evidence(self):
        self.links = {}
        self.assertFalse(self.validate()['valid'])

    def test_nonexistent_evidence_reference(self):
        self.links['/paper/main_contribution'] = ['E999']
        self.assertFalse(self.validate()['valid'])

    def test_invalid_reference_type_returns_error(self):
        self.links['/paper/main_contribution'] = 42
        self.assertFalse(self.validate()['valid'])

    def test_duplicate_evidence_ids(self):
        self.doc['evidence'].append(copy.deepcopy(self.doc['evidence'][0]))
        self.assertFalse(self.validate()['valid'])

    def test_invalid_page_range(self):
        for page in (0,2,'1',None):
            self.doc['evidence'][0]['location']['page'] = page
            self.assertFalse(self.validate()['valid'])

    def test_identity_mismatch(self):
        self.doc['paper']['paper_id'] = 'P9999'
        self.assertFalse(self.validate()['valid'])

    def test_module_without_evidence(self):
        self.doc['modules'] = {'fundamentals_taxonomy':{'task_type':['VO']}}
        self.assertFalse(self.validate()['valid'])

    def test_reviewer_inference_not_mislabeled(self):
        self.doc['paper']['limitations_reviewer'] = ['Reviewer interpretation.']
        self.links['/paper/limitations_reviewer/0'] = ['E001']
        self.assertFalse(self.validate()['valid'])
        self.doc['evidence'][0]['support_level'] = 'reviewer_inference'
        self.assertTrue(self.validate()['valid'])

    def test_pdf_preparation_and_integrity(self):
        bundle = self.bundle()
        manifest,pages,_,_ = ex.load_bundle(bundle)
        self.assertEqual(len(pages),1)
        self.assertIn('camera motion',pages[0]['text'])
        self.assertFalse(manifest['human_reviewed'])
        (bundle/'pages.json').write_text('[]')
        with self.assertRaisesRegex(ValueError,'Integridade'):
            ex.load_bundle(bundle)

    def test_blank_pdf_needs_ocr(self):
        pdf = self.root/'blank.pdf'
        writer = PdfWriter()
        writer.add_blank_page(width=600,height=800)
        writer.write(pdf)
        with self.assertRaisesRegex(ValueError,'OCR'):
            ex.prepare(self.db,self.root,'P0001',pdf)

    def test_accept_and_invalid_attempts_preserve_screening(self):
        bundle = self.bundle()
        output,links = self.root/'extraction.json',self.root/'links.json'
        ex.write_json(output,self.doc)
        ex.write_json(links,self.links)
        path,report = ex.accept(self.db,bundle,output,links,'synthetic-test')
        self.assertTrue(report['valid'])
        self.assertTrue((path/'tables/evidence.json').exists())
        self.assertEqual(review.extraction_state(self.db,1)['status'],'EXTRACTED')
        output.write_text('{invalid json')
        failed,report = ex.accept(self.db,bundle,output,links,'synthetic-test')
        self.assertFalse(report['valid'])
        self.assertFalse((failed/'tables').exists())
        self.assertTrue((path/'tables/evidence.json').exists())
        self.assertEqual(self.db.execute('SELECT status FROM papers').fetchone()[0],'SCREEN_PENDING')
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM extraction_attempts').fetchone()[0],2)
        state = review.extraction_state(self.db,1)
        self.assertEqual(state['status'],'EXTRACTED')
        self.assertEqual(state['latest_attempt_status'],'EXTRACTION_INVALID')
        self.assertEqual(state['latest_valid_path'],str(path.resolve()))

    def test_json_duplicate_keys_and_nan_are_rejected(self):
        path = self.root/'invalid.json'
        for value in ('{"x":1,"x":2}','{"x":NaN}'):
            path.write_text(value)
            with self.assertRaises(ValueError):
                ex.read_json(path)

    def test_arxiv_download_rejects_html(self):
        with self.db:
            record = json.loads(self.db.execute('SELECT metadata FROM papers').fetchone()[0])
            record['arxiv_id'] = '2308.14039'
            self.db.execute('UPDATE papers SET metadata=?',(json.dumps(record),))
        class Response:
            def __enter__(self): return self
            def __exit__(self,*args): pass
            def geturl(self): return 'https://arxiv.org/pdf/2308.14039'
            def read(self,*args): return b'<html>error</html>'
        with patch.object(ex,'urlopen',return_value=Response()):
            with self.assertRaisesRegex(ValueError,'PDF'):
                ex.fetch_arxiv(self.db,self.root,'P0001')


if __name__ == '__main__':
    unittest.main()

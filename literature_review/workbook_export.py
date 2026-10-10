"""Snapshot auditável e exportação XLSX pelo runtime Artifact Tool."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

from review import ROOT, extraction_state, now

RUNTIME = Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies'
DEFAULT_OUTPUT = ROOT/'outputs/01a0bf7f-97f2-7032-a298-538c664b2f94/revisao_bibliografica.xlsx'


def text_chunks(text, size=650):
    """Quebrar resumos longos sem perder caracteres e sem exceder células Excel."""
    text = text or ''
    while text:
        stop = min(size,len(text))
        if stop<len(text):
            space = text.rfind(' ',0,stop)
            if space>size//2:
                stop=space+1
        yield text[:stop]
        text=text[stop:]


def scalar_rows(node, path=''):
    if isinstance(node,dict):
        for key,value in node.items():
            yield from scalar_rows(value,path+'/'+key.replace('~','~0').replace('/','~1'))
    elif isinstance(node,list):
        for i,value in enumerate(node):
            yield from scalar_rows(value,path+'/'+str(i))
    elif node is not None:
        yield path,node


def snapshot(db, data):
    result={'created_at':now(),'papers':[],'abstracts':[],'evidence':[],'synthesis':[],'searches':[],'provenance':[]}
    for pid,raw,status,discovered in db.execute('SELECT id,metadata,status,discovered_at FROM papers ORDER BY id'):
        record=json.loads(raw)
        paper_id=f'P{pid:04d}'
        decision=db.execute('SELECT decision,reason,reviewed_at FROM reviews WHERE paper_id=?',(pid,)).fetchone()
        origins=db.execute('SELECT DISTINCT source,theme FROM provenance WHERE paper_id=?',(pid,)).fetchall()
        state=extraction_state(db,pid)
        result['papers'].append([paper_id,record['title'],record.get('year'),'; '.join(record.get('authors',[])),
            record.get('venue'),record.get('doi'),record.get('arxiv_id'),record.get('publication_type'),
            ', '.join(sorted({x[0] for x in origins})),', '.join(sorted({x[1] for x in origins})),
            decision[0] if decision else 'PENDENTE',decision[1] if decision else None,
            state['status'],state.get('latest_attempt_status'),'PENDENTE',record.get('url'),discovered,
            decision[2] if decision else None])
        for i,chunk in enumerate(text_chunks(record.get('abstract')),1):
            result['abstracts'].append([paper_id,i,chunk,record.get('url')])
        valid_path=state.get('latest_valid_path')
        if valid_path:
            directory=Path(valid_path)
            validation=json.loads((directory/'validation.json').read_text())
            raw_bytes=(directory/'extraction.json').read_bytes()
            links_bytes=(directory/'claim_links.json').read_bytes()
            if not validation.get('valid') or hashlib.sha256(raw_bytes).hexdigest()!=validation['extraction_sha256'] or hashlib.sha256(links_bytes).hexdigest()!=validation['claim_links_sha256']:
                raise ValueError('Extração alterada após validação: '+paper_id)
            extraction=json.loads(raw_bytes)
            if extraction['paper']['paper_id']!=paper_id:
                raise ValueError('Identidade inconsistente na extração: '+paper_id)
            links=json.loads(links_bytes)
            for evidence in extraction['evidence']:
                location=evidence['location']
                result['evidence'].append([paper_id,evidence['evidence_id'],evidence['claim_type'],
                    evidence['claim'],evidence['quote_or_paraphrase'],location.get('page'),location.get('section'),
                    location.get('table'),location.get('figure'),evidence['support_level'],record.get('url'),validation.get('producer')])
            for section in ('paper','classification','modules','project_implications'):
                for path,value in scalar_rows(extraction.get(section,{}),'/'+section):
                    refs=links.get(path,[])
                    result['synthesis'].append([paper_id,section,path,
                        value if isinstance(value,str) else None,
                        value if isinstance(value,(int,float)) and not isinstance(value,bool) else None,
                        value if isinstance(value,bool) else None,', '.join(refs),record.get('url')])
    for pid,run_id,source,theme,query,raw_path in db.execute('SELECT * FROM provenance ORDER BY paper_id,run_id,source,theme,query'):
        result['provenance'].append([f'P{pid:04d}',run_id,source,theme,query,Path(raw_path).name])
    for file in sorted((data/'runs').glob('*/summary.json')):
        run=json.loads(file.read_text())
        for search in run.get('searches',[]):
            result['searches'].append([run['run_id'],search['source'],search['theme'],search['query'],
                search['year_from'],search['year_to'],search.get('started_at'),search.get('status'),
                search.get('records',0),search.get('new',0),search.get('duplicates',0),
                search.get('total_reported'),search.get('limit_reached'),search.get('error'),
                '\n'.join(r['url'] for r in search.get('requests',[]))])
    return result


def export_xlsx(db, data, output=DEFAULT_OUTPUT, previews=False):
    node=Path(os.environ.get('LITERATURE_NODE',str(RUNTIME/'node/bin/node')))
    packages=Path(os.environ.get('LITERATURE_NODE_MODULES',str(RUNTIME/'node/node_modules')))
    if not node.is_file() or not (packages/'@oai/artifact-tool').exists():
        raise ValueError('Runtime de planilhas indisponível. Configure LITERATURE_NODE e LITERATURE_NODE_MODULES.')
    output=output.resolve()
    output.parent.mkdir(parents=True,exist_ok=True)
    payload=snapshot(db,data)
    # Não instalar dependências no projeto nem alterar o runtime compartilhado.
    with tempfile.TemporaryDirectory(prefix='bibliography-xlsx-') as temp:
        work=Path(temp)
        (work/'node_modules').symlink_to(packages,target_is_directory=True)
        (work/'build_workbook.mjs').write_bytes((ROOT/'build_workbook.mjs').read_bytes())
        (work/'snapshot.json').write_text(json.dumps(payload,ensure_ascii=False,allow_nan=False))
        command=[str(node),str(work/'build_workbook.mjs'),str(work/'snapshot.json'),str(output)]
        if previews:
            command.append('--previews')
        subprocess.run(command,check=True)
    return output

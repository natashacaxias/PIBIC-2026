#!/usr/bin/env python3
"""Coleta bibliográfica auditável. Python 3.9+, biblioteca padrão."""
import argparse
import hashlib
import html
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import time
import unicodedata
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import uuid
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
VERSION = '0.3.0'


def now():
    return datetime.now(timezone.utc).isoformat()


def clean(value):
    return ' '.join(html.unescape(re.sub(r'<[^>]*>', ' ', value or '')).split())


def doi(value):
    return re.sub(r'^(?:https?://(?:dx\.)?doi.org/|doi:\s*)', '', (value or '').strip(), flags=re.I).lower() or None


def title_key(value):
    value = unicodedata.normalize('NFKD', value).casefold()
    return ''.join(c for c in value if c.isalnum() and not unicodedata.combining(c))


def connect(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.execute('PRAGMA foreign_keys=ON')
    db.executescript('''
        CREATE TABLE IF NOT EXISTS papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metadata TEXT NOT NULL, title_key TEXT NOT NULL,
            doi TEXT, arxiv_id TEXT, kind TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'SCREEN_PENDING',
            discovered_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS by_doi ON papers(doi);
        CREATE INDEX IF NOT EXISTS by_arxiv ON papers(arxiv_id);
        CREATE INDEX IF NOT EXISTS by_title ON papers(title_key);
        CREATE TABLE IF NOT EXISTS provenance (
            paper_id INTEGER NOT NULL REFERENCES papers(id),
            run_id TEXT NOT NULL, source TEXT NOT NULL, theme TEXT NOT NULL,
            query TEXT NOT NULL, raw_path TEXT NOT NULL,
            UNIQUE(paper_id,run_id,source,theme,query,raw_path)
        );
        CREATE TABLE IF NOT EXISTS reviews (
            paper_id INTEGER PRIMARY KEY REFERENCES papers(id),
            decision TEXT NOT NULL, reason TEXT NOT NULL, reviewed_at TEXT NOT NULL
        );
    ''')
    return db


def upsert(db, record, provenance):
    """Identificadores exatos; título só com autor/ano e sem conflito de IDs."""
    record = dict(record)
    record['doi'] = doi(record.get('doi'))
    key = title_key(record['title'])
    match = None
    for field in ('arxiv_id', 'doi'):
        if record.get(field):
            # Preprint/publicação permanecem distintos para revisão de versões.
            match = db.execute('SELECT id,metadata FROM papers WHERE '+field+'=? AND kind=?',
                               (record[field], record['kind'])).fetchone()
            if match:
                break
    if not match and key and record.get('authors') and record.get('year'):
        for candidate in db.execute('SELECT id,metadata FROM papers WHERE title_key=? AND kind=?', (key,record['kind'])):
            old = json.loads(candidate[1])
            conflict = any(old.get(f) and record.get(f) and old[f] != record[f] for f in ('doi','arxiv_id'))
            if not conflict and old.get('year') == record['year'] and old.get('authors') and title_key(old['authors'][0]) == title_key(record['authors'][0]):
                match = candidate
                break
    if match:
        pid, old = match[0], json.loads(match[1])
        for field, value in record.items():
            if not old.get(field) and value:
                old[field] = value
        db.execute('UPDATE papers SET metadata=?,doi=?,arxiv_id=? WHERE id=?',
                   (json.dumps(old,ensure_ascii=False),old.get('doi'),old.get('arxiv_id'),pid))
    else:
        pid = db.execute('INSERT INTO papers(metadata,title_key,doi,arxiv_id,kind,discovered_at) VALUES(?,?,?,?,?,?)',
                         (json.dumps(record,ensure_ascii=False),key,record.get('doi'),record.get('arxiv_id'),record['kind'],now())).lastrowid
    db.execute('INSERT OR IGNORE INTO provenance VALUES(?,?,?,?,?,?)', (pid,*provenance))
    return pid, match is None


def normalize_crossref(item):
    title = clean((item.get('title') or [''])[0])
    if not title:
        raise ValueError('Registro Crossref sem título')
    parts = (item.get('published') or item.get('issued') or {}).get('date-parts') or [[]]
    return {'title':title,'authors':[clean(' '.join(filter(None,[a.get('given'),a.get('family')])) or a.get('name','')) for a in item.get('author',[])],
            'year':parts[0][0] if parts[0] else None,'doi':doi(item.get('DOI')),
            'arxiv_id':None,'venue':(item.get('container-title') or [None])[0],
            'abstract':clean(item.get('abstract')) or None,'url':item.get('URL'),
            'kind':'preprint' if item.get('type') == 'posted-content' else 'publication',
            'publication_type':item.get('type')}


NS = {'a':'http://www.w3.org/2005/Atom','x':'http://arxiv.org/schemas/atom','o':'http://a9.com/-/spec/opensearch/1.1/'}


def parse_arxiv(payload):
    root = ET.fromstring(payload)
    records = []
    for item in root.findall('a:entry', NS):
        get = lambda tag: item.findtext(tag,default='',namespaces=NS)
        url = get('a:id')
        if '/abs/' not in url:
            raise ValueError('Resposta de erro/identificador arXiv inválido: '+clean(get('a:title')))
        ident = re.sub(r'v\d+$','',url.split('/abs/',1)[1])
        records.append({'title':clean(get('a:title')),'authors':[clean(a.findtext('a:name',default='',namespaces=NS)) for a in item.findall('a:author',NS)],
                        'year':int(get('a:published')[:4]),'doi':doi(get('x:doi')),'arxiv_id':ident,
                        'venue':get('x:journal_ref') or None,'abstract':clean(get('a:summary')) or None,
                        'url':url,'kind':'preprint','publication_type':'preprint'})
    return records, int(root.findtext('o:totalResults',default='0',namespaces=NS))


def arxiv_query(query, start_year, end_year):
    terms = re.findall(r'"[^"]+"|\S+',query)
    expression = ' AND '.join('all:'+term for term in terms)
    return '('+expression+') AND submittedDate:[%d01010000 TO %d12312359]' % (start_year,end_year)


class Client:
    def __init__(self):
        self.last = {}

    def get(self, source, url):
        for attempt in range(3):
            delay = (3.1 if source == 'arxiv' else 1.0) - (time.monotonic()-self.last.get(source,0))
            if delay > 0:
                time.sleep(delay)
            self.last[source] = time.monotonic()
            request = Request(url,headers={'User-Agent':'PIBIC-LiteratureReview/'+VERSION,'Accept':'application/json' if source=='crossref' else 'application/atom+xml'})
            try:
                with urlopen(request,timeout=30) as response:
                    return response.read()
            except HTTPError as exc:
                if exc.code not in (429,500,502,503,504) or attempt == 2:
                    raise
                retry = exc.headers.get('Retry-After','')
                if retry.isdigit() and int(retry)>60:
                    raise RuntimeError('Servidor solicitou espera maior que 60s; repetir a busca mais tarde') from exc
                time.sleep(max(2**(attempt+1),int(retry) if retry.isdigit() else 0))
            except (URLError,TimeoutError):
                if attempt == 2:
                    raise
                time.sleep(2**(attempt+1))


def fetch(client, source, query, year_from, year_to, limit, directory, audit):
    cursor, start, pages = '*', 0, 0
    while start < limit:
        size = min(100,limit-start)
        if source == 'crossref':
            params = {'query.title':query,'sort':'score','order':'desc','filter':f'from-pub-date:{year_from}-01-01,until-pub-date:{year_to}-12-31','rows':size,'cursor':cursor}
            if os.getenv('CROSSREF_MAILTO'):
                params['mailto'] = os.environ['CROSSREF_MAILTO']
            url = 'https://api.crossref.org/works?'+urlencode(params)
        else:
            params = {'search_query':arxiv_query(query,year_from,year_to),'start':start,'max_results':size,'sortBy':'relevance','sortOrder':'descending'}
            url = 'https://export.arxiv.org/api/query?'+urlencode(params)
        payload = client.get(source,url)
        pages += 1
        raw = directory / ('page_%03d.%s' % (pages,'json' if source=='crossref' else 'xml'))
        raw.write_bytes(payload)  # salvar antes de interpretar
        audit['requests'].append({'url':url,'retrieved_at':now(),'raw_path':str(raw),'sha256':hashlib.sha256(payload).hexdigest()})
        if source == 'crossref':
            body = json.loads(payload)['message']
            items = body['items']
            records = [normalize_crossref(item) for item in items]
            total = body.get('total-results',len(records))
            next_cursor = body.get('next-cursor')
        else:
            records,total = parse_arxiv(payload)
            next_cursor = None
        audit['total_reported'] = total
        for record in records:
            yield record,raw
        start += len(records)
        if len(records)<size or start>=total:
            break
        if source == 'crossref':
            if not next_cursor or next_cursor==cursor:
                break
            cursor = next_cursor
    audit['limit_reached'] = start>=limit and audit.get('total_reported',0)>start


def extraction_state(db, pid):
    tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if not {'extraction_bundles','extraction_attempts'} <= tables:
        return {'status':'NOT_PREPARED','human_reviewed':False}
    bundle = db.execute('SELECT bundle_id,path FROM extraction_bundles WHERE paper_id=? ORDER BY created_at DESC LIMIT 1',(pid,)).fetchone()
    if not bundle:
        return {'status':'NOT_PREPARED','human_reviewed':False}
    latest = db.execute('SELECT status,path FROM extraction_attempts WHERE bundle_id=? ORDER BY created_at DESC LIMIT 1',(bundle[0],)).fetchone()
    valid = db.execute("SELECT path FROM extraction_attempts WHERE bundle_id=? AND status='EXTRACTED' ORDER BY created_at DESC LIMIT 1",(bundle[0],)).fetchone()
    return {'status':'EXTRACTED' if valid else (latest[0] if latest else 'EXTRACTION_PENDING'),
            'bundle_path':bundle[1],'latest_attempt_status':latest[0] if latest else None,
            'latest_valid_path':valid[0] if valid else None,'human_reviewed':False}


def export(db, directory):
    directory.mkdir(parents=True,exist_ok=True)
    rows = []
    ris = []
    for pid,metadata,status,discovered in db.execute('SELECT id,metadata,status,discovered_at FROM papers ORDER BY id'):
        paper = json.loads(metadata)
        origins = db.execute('SELECT DISTINCT source,theme FROM provenance WHERE paper_id=?',(pid,)).fetchall()
        review = db.execute('SELECT decision,reason,reviewed_at FROM reviews WHERE paper_id=?',(pid,)).fetchone()
        paper.update(paper_id=f'P{pid:04d}',status=status,discovered_at=discovered,
                     source_databases=sorted({x[0] for x in origins}),search_themes=sorted({x[1] for x in origins}),
                     human_review=dict(zip(('decision','reason','reviewed_at'),review)) if review else None)
        paper['extraction'] = extraction_state(db,pid)
        rows.append(paper)
        lines = ['TY  - '+('UNPB' if paper['kind']=='preprint' else 'GEN'),'ID  - '+paper['paper_id'],'TI  - '+clean(paper['title'])]
        lines += ['AU  - '+clean(a) for a in paper['authors']]
        for tag,field in [('PY','year'),('DO','doi'),('UR','url'),('JO','venue'),('AB','abstract')]:
            if paper.get(field):
                lines.append(tag+'  - '+clean(str(paper[field])))
        lines += ['ER  - ','']
        ris.extend(lines)
    (directory/'papers.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    (directory/'bibliography.ris').write_text('\n'.join(ris)+'\n')
    pending = [p for p in rows if not p['human_review']]
    report = ['# Fila de revisão humana','',f'{len(rows)} registros no corpus; {len(pending)} aguardam revisão.','',
              'Temas indicam a consulta de origem, não uma classificação confirmada.','']
    for p in pending:
        report.extend([f"## {p['paper_id']} — {clean(p['title'])}",f"Ano: {p['year']} · Tipo: {p['kind']}",f"DOI: {p['doi'] or 'não informado'}",f"Extração: {p['extraction']['status']}",f"Temas de busca: {', '.join(p['search_themes'])}",'',p['abstract'] or 'Resumo indisponível; requer consulta ao texto integral.',''])
    (directory/'revisao.md').write_text('\n'.join(report)+'\n')
    return len(rows)


def run(args):
    config = json.loads(args.config.read_text())
    sources = [args.source] if args.source else config['sources']
    if not sources or any(s not in ('crossref','arxiv') for s in sources):
        raise ValueError('Fontes suportadas nesta versão: crossref, arxiv')
    themes = config['themes']
    if args.theme:
        themes = {args.theme:themes[args.theme]}
    limit = args.limit if args.limit is not None else config['max_results_per_query']
    if limit<1 or limit>10000:
        raise ValueError('Limite deve estar entre 1 e 10000')
    jobs = [(s,t,q,c['year_from'],config['year_to']) for t,c in themes.items() for q in c['queries'] for s in sources]
    if args.pilot:
        jobs = jobs[:2]
    if args.dry_run:
        print(json.dumps({'jobs':len(jobs),'max_records':len(jobs)*limit,'queries':jobs},ensure_ascii=False,indent=2))
        return 0
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]
    directory = args.data/'runs'/run_id
    directory.mkdir(parents=True)
    (directory/'config.json').write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n')
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    db = connect(args.data/'corpus.sqlite3')
    client = Client()
    summary = {'run_id':run_id,'started_at':now(),'version':VERSION,'code_sha256':code_hash,'jobs':len(jobs),'records':0,'new':0,'duplicates':0,'errors':0,'limit':limit,'searches':[]}
    try:
        for number,(source,theme,query,year_from,year_to) in enumerate(jobs,1):
            raw_dir = directory/'raw'/f'{number:03d}_{source}'
            raw_dir.mkdir(parents=True)
            audit = {'source':source,'theme':theme,'query':query,'year_from':year_from,'year_to':year_to,'started_at':now(),'requests':[],'records':0,'new':0,'duplicates':0,'status':'running'}
            print(f'[{number}/{len(jobs)}] {source}: {query}',flush=True)
            try:
                for record,raw in fetch(client,source,query,year_from,year_to,limit,raw_dir,audit):
                    with db:
                        _,created = upsert(db,record,(run_id,source,theme,query,str(raw.resolve())))
                    audit['records'] += 1
                    audit['new' if created else 'duplicates'] += 1
                audit['status'] = 'complete'
            except (HTTPError,URLError,TimeoutError,ValueError,KeyError,RuntimeError,ET.ParseError) as exc:
                audit['status'] = 'failed'
                audit['error'] = str(exc)
                summary['errors'] += 1
                print(f'Falha registrada: {exc}',file=sys.stderr)
            finally:
                audit['finished_at'] = now()
                (raw_dir/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
                summary['searches'].append(audit)
                for field in ('records','new','duplicates'):
                    summary[field] += audit[field]
    finally:
        summary['finished_at'] = now()
        summary['corpus_size'] = export(db,directory/'exports')
        summary['status'] = 'complete' if len(summary['searches'])==len(jobs) and not summary['errors'] else 'partial_or_failed'
        (directory/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
        db.close()
    print(json.dumps({k:v for k,v in summary.items() if k!='searches'},ensure_ascii=False,indent=2))
    print('Resultados: '+str(directory.resolve()))
    if not getattr(args,'no_xlsx',False):
        from workbook_export import export_xlsx
        with connect(args.data/'corpus.sqlite3') as workbook_db:
            export_xlsx(workbook_db,args.data,directory/'revisao_bibliografica.xlsx')
    return 1 if summary['errors'] else 0


REVIEW_STATUS = {'INCLUDE':'SCREEN_INCLUDED','MAYBE':'SCREEN_MAYBE','EXCLUDE':'SCREEN_EXCLUDED'}


def record_review(db, paper_id, decision, reason):
    """Grava uma decisão humana; o chamador controla a transação."""
    pid = int(str(paper_id).removeprefix('P'))
    if decision not in REVIEW_STATUS:
        raise ValueError(f'Decisão inválida: {decision}')
    if not reason.strip() or not db.execute('SELECT 1 FROM papers WHERE id=?',(pid,)).fetchone():
        raise ValueError('Artigo inexistente ou justificativa vazia')
    db.execute('INSERT OR REPLACE INTO reviews VALUES(?,?,?,?)',(pid,decision,reason,now()))
    db.execute('UPDATE papers SET status=? WHERE id=?',(REVIEW_STATUS[decision],pid))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data',type=Path,default=ROOT/'data')
    sub = parser.add_subparsers(dest='command',required=True)
    collect = sub.add_parser('search',help='Coletar metadados e atualizar corpus')
    collect.add_argument('--config',type=Path,default=ROOT/'config/search_queries.json')
    collect.add_argument('--source',choices=['crossref','arxiv'])
    collect.add_argument('--theme')
    collect.add_argument('--limit',type=int)
    collect.add_argument('--pilot',action='store_true',help='Somente as duas primeiras combinações de consulta/base')
    collect.add_argument('--dry-run',action='store_true')
    collect.add_argument('--no-xlsx',action='store_true',help='Coletar sem gerar planilha nesta execução')
    exp = sub.add_parser('export')
    exp.add_argument('--output',type=Path,default=ROOT/'exports')
    exp.add_argument('--xlsx-output',type=Path,help='Caminho da saída XLSX final')
    exp.add_argument('--previews',action='store_true',help='Renderizar prévias para conferência visual')
    exp.add_argument('--no-xlsx',action='store_true',help='Exportar somente JSON, RIS e Markdown')
    review = sub.add_parser('review',help='Registrar decisão humana explícita')
    review.add_argument('paper_id')
    review.add_argument('decision',choices=['INCLUDE','MAYBE','EXCLUDE'])
    review.add_argument('--reason',required=True)
    args = parser.parse_args()
    if args.command == 'search':
        return run(args)
    db = connect(args.data/'corpus.sqlite3')
    try:
        if args.command == 'export':
            print(f'{export(db,args.output)} registros exportados para {args.output.resolve()}')
            if not args.no_xlsx:
                from workbook_export import export_xlsx, DEFAULT_OUTPUT
                export_xlsx(db,args.data,args.xlsx_output or DEFAULT_OUTPUT,args.previews)
        else:
            with db:
                record_review(db,args.paper_id,args.decision,args.reason)
    finally:
        db.close()
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError,KeyError) as exc:
        print('Erro de configuração/entrada: '+str(exc),file=sys.stderr)
        sys.exit(2)

#!/usr/bin/env python3
"""Pré-triagem por regras explícitas: gera sugestões, não decisões.

`suggest` lê o corpus, aplica os critérios de docs/criterios_triagem.md e grava
um CSV para a revisora conferir. `apply` registra no corpus somente as linhas em
que a coluna decisao_humana foi preenchida, com justificativa obrigatória.
"""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import re
import sys

from review import ROOT, connect, record_review

NON_ARTICLE = re.compile(r'^\s*(editorial|front matter|back matter|index|author index|subject index|erratum|corrigendum|retraction|table of contents|contents|preface|foreword|cover|title page|guest editorial|reviewers?|message from)\b', re.I)
GROUPS = {
    'core': (3, r'odometr|\bslam\b|ego-?motion|visual[- ](inertial|localization|localisation|navigation|positioning|tracking)|camera (pose|tracking|motion)|structure from motion|\bvio\b|trajectory (estimation|evaluation)'),
    'atmos': (2, r'\bfog|foggy|\bhaz[ey]|hazy|dehaz|defog|smoke|smog|atmospheric scattering|koschmieder|dark channel|scattering media|visibility'),
    'robust': (2, r'robust|adverse|degrad|corrupt|perturb|failure|challeng|low[- ]light|illuminat|night|weather|\brain|snow|blur|lens|dust|dirt|condensation|exposure'),
    'deep': (1, r'\bdeep\b|learn|neural|network|transformer|end-to-end'),
    'dataset': (1, r'dataset|benchmark'),
    'field': (1, r'forest|vegetation|canopy|amazon|tropical|\buav|drone|aerial|wildfire|\bfire\b'),
    'metric': (1, r'absolute trajectory error|relative pose error|\bate\b|\brpe\b|trajectory evaluation|image quality assessment|\bssim\b|brisque'),
}
PATTERNS = {name:re.compile(rx,re.I) for name,(_,rx) in GROUPS.items()}
IMAGE = re.compile(r'image|camera|vision|visual|video|photo', re.I)
INCLUDE_SCORE = 5
COLUMNS = ['paper_id','sugestao','regra','pontuacao','criterios','temas','ano','titulo','veiculo','doi','tem_resumo','decisao_humana','justificativa_humana']


def classify(title, abstract):
    """Retorna (sugestão, regra, pontuação, grupos) para um registro."""
    title = (title or '').strip()
    if not title or NON_ARTICLE.match(title):
        return 'EXCLUDE','E1 não é artigo',0,[]
    text = f'{title} {abstract or ""}'
    hits = [name for name,rx in PATTERNS.items() if rx.search(text)]
    score = sum(GROUPS[name][0] for name in hits)
    in_scope = 'core' in hits or 'metric' in hits or ('atmos' in hits and IMAGE.search(text))
    if not in_scope:
        return 'EXCLUDE','E2 fora do escopo',score,hits
    if score >= INCLUDE_SCORE:
        return 'INCLUDE',f'I1 pontuação ≥ {INCLUDE_SCORE}',score,hits
    return 'MAYBE','M1 no escopo, pontuação baixa',score,hits


def suggest(db):
    themes = {}
    for pid,theme in db.execute('SELECT paper_id,theme FROM provenance'):
        themes.setdefault(pid,set()).add(theme)
    rows = []
    for pid,metadata,status in db.execute('SELECT id,metadata,status FROM papers ORDER BY id'):
        if status != 'SCREEN_PENDING':
            continue
        meta = json.loads(metadata)
        decision,rule,score,hits = classify(meta.get('title'),meta.get('abstract'))
        rows.append({'paper_id':f'P{pid:04d}','sugestao':decision,'regra':rule,'pontuacao':score,
                     'criterios':' '.join(hits),'temas':' '.join(sorted(themes.get(pid,()))),
                     'ano':meta.get('year') or '','titulo':meta.get('title') or '','veiculo':meta.get('venue') or '',
                     'doi':meta.get('doi') or '','tem_resumo':'sim' if meta.get('abstract') else 'não',
                     'decisao_humana':'','justificativa_humana':''})
    order = {'INCLUDE':0,'MAYBE':1,'EXCLUDE':2}
    rows.sort(key=lambda r:(order[r['sugestao']],-r['pontuacao'],-int(str(r['ano'] or 0)[:4] or 0)))
    return rows


def write_csv(rows, path):
    path.parent.mkdir(parents=True,exist_ok=True)
    with open(path,'w',newline='',encoding='utf-8') as f:
        writer = csv.DictWriter(f,fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def apply(db, path):
    """Registra as decisões humanas preenchidas no CSV; ignora linhas em branco."""
    applied = 0
    with open(path,newline='',encoding='utf-8') as f, db:
        for row in csv.DictReader(f):
            decision = (row.get('decisao_humana') or '').strip().upper()
            if not decision:
                continue
            record_review(db,row['paper_id'],decision,row.get('justificativa_humana') or '')
            applied += 1
    return applied


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data',type=Path,default=ROOT/'data')
    sub = parser.add_subparsers(dest='command',required=True)
    sug = sub.add_parser('suggest',help='Gerar CSV de sugestões de triagem')
    sug.add_argument('--output',type=Path,default=ROOT/'exports/triagem_sugerida.csv')
    app = sub.add_parser('apply',help='Registrar decisões humanas preenchidas no CSV')
    app.add_argument('csv',type=Path)
    args = parser.parse_args()
    db = connect(args.data/'corpus.sqlite3')
    try:
        if args.command == 'suggest':
            rows = suggest(db)
            write_csv(rows,args.output)
            counts = Counter(r['sugestao'] for r in rows)
            print(f"{len(rows)} pendentes → INCLUDE {counts['INCLUDE']}, MAYBE {counts['MAYBE']}, EXCLUDE {counts['EXCLUDE']}")
            print(f'Sugestões em {args.output.resolve()}')
        else:
            print(f'{apply(db,args.csv)} decisões humanas registradas')
    finally:
        db.close()
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError,KeyError) as exc:
        print('Erro de entrada: '+str(exc),file=sys.stderr)
        sys.exit(2)

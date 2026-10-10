# Arquitetura para Coleta, Triagem e Extração Automatizada da Revisão Bibliográfica

## 1. Objetivo

Esta arquitetura foi pensada para uma revisão bibliográfica sobre **Odometria Visual (VO), Visual SLAM, robustez sob condições adversas, métodos clássicos e baseados em deep learning, degradações atmosféricas/ópticas, datasets, métricas e cenários florestais/UAV/Amazônia**.

O objetivo é automatizar o máximo possível da cadeia:

```text
definição de temas e queries
        ↓
busca em múltiplas bases científicas
        ↓
normalização de metadados
        ↓
deduplicação
        ↓
triagem por título/resumo
        ↓
aquisição de PDF open access ou via acesso institucional autorizado
        ↓
extração estruturada para JSON
        ↓
validação contra JSON Schema
        ↓
conversão para tabelas relacionais
        ↓
revisão humana
        ↓
atualização incremental / living review
```

A arquitetura deve preservar três princípios:

1. **reprodutibilidade**: toda busca deve ser registrada com data, query, base e filtros;
2. **auditabilidade**: toda conclusão extraída deve apontar para uma evidência no artigo;
3. **separação de responsabilidades**: busca, deduplicação, triagem, download, extração e análise são etapas independentes.

---

# 2. Visão geral dos 8 temas

A revisão será organizada em oito eixos:

```text
T1  fundamentals_taxonomy
T2  classical_geometric
T3  deep_vo_slam
T4  robustness_corruptions
T5  atmospheric_optical
T6  datasets_benchmarks
T7  metrics_protocol
T8  forest_uav_amazon
```

Cada artigo pode pertencer a mais de um tema.

Exemplo:

```text
P0001 → deep_vo_slam
P0001 → robustness_corruptions
P0001 → metrics_protocol
```

A classificação temática não deve ser usada como chave primária.

---

# 3. Estratégia de fontes bibliográficas

A melhor estratégia é combinar:

- bases de indexação;
- bibliotecas de editoras/sociedades;
- repositórios de preprints;
- grafos de citações;
- mecanismos de descoberta complementar.

Nenhuma base isolada deve ser tratada como cobertura completa da literatura.

---

## 3.1 Bases prioritárias para este projeto

### IEEE Xplore

**Prioridade: muito alta**

Especialmente relevante para:

- IEEE Transactions on Robotics;
- IEEE Robotics and Automation Letters;
- ICRA;
- IROS;
- IV;
- SBR/LARS relacionados;
- visão, robótica, navegação, SLAM e sensoriamento.

Uso recomendado:

```text
IEEE Xplore
    ↓
metadados
    ↓
DOI
    ↓
resolução do registro canônico
    ↓
PDF se houver acesso autorizado/open access
```

Automação:

- preferir a API oficial IEEE Xplore quando disponível para a conta/instituição;
- armazenar a chave em variável de ambiente;
- respeitar limites de uso;
- não automatizar download massivo fora das permissões da licença institucional.

Campos desejados:

```text
title
authors
abstract
publication_title
publication_year
doi
article_number
index_terms
content_type
pdf_url quando permitido
```

Portal do desenvolvedor:

- https://developer.ieee.org/

---

### ACM Digital Library

**Prioridade: alta**

Relevante para:

- visão computacional;
- sistemas robóticos;
- multimídia;
- algoritmos;
- aprendizado de máquina;
- conferências e periódicos ACM.

Uso recomendado:

```text
ACM DL
    ↓
metadados
    ↓
DOI
    ↓
normalização via Crossref
```

Automação deve respeitar as condições de uso da ACM. Quando não houver uma API pública adequada para o fluxo desejado, use:

- DOI;
- Crossref;
- OpenAlex;
- Semantic Scholar;
- exportação BibTeX/RIS;
- acesso institucional autorizado.

Site:

- https://dl.acm.org/

---

### Scopus

**Prioridade: muito alta para cobertura e rastreamento bibliográfico**

Útil para:

- busca temática ampla;
- citações;
- referências;
- autores;
- venues;
- deduplicação;
- análise bibliométrica.

Automação:

- API Elsevier/Scopus quando houver credencial e acesso institucional;
- pode exigir assinatura institucional;
- registrar a query exata e os filtros aplicados.

Portal:

- https://dev.elsevier.com/

---

### Web of Science

**Prioridade: muito alta para revisão sistemática e rastreamento de citações**

Útil para:

- busca estruturada;
- filtros de publicação;
- forward citation;
- backward citation;
- identificação de versões;
- análise bibliométrica.

Automação:

- utilizar APIs oficiais Clarivate quando disponíveis para sua instituição;
- não assumir acesso irrestrito.

Informações:

- https://developer.clarivate.com/

---

### Google Scholar

**Prioridade: alta como fonte complementar de descoberta**

Google Scholar é excelente para descobrir:

- versões alternativas;
- PDFs hospedados em repositórios;
- teses;
- preprints;
- citações;
- trabalhos que escapam de outras bases.

Porém, ele deve ser tratado com cuidado na automação.

A arquitetura recomendada é:

```text
Google Scholar
      ↓
descoberta complementar
      ↓
DOI / título / autores
      ↓
Crossref / OpenAlex / publisher
      ↓
registro normalizado
```

Não fazer scraping agressivo do Google Scholar.

Para automação, há três opções:

1. **uso manual controlado**, com exportação BibTeX/RIS;
2. **uso em etapa de verificação**, não como coletor primário;
3. **serviço de busca de terceiros**, apenas se seus termos e custos forem aceitáveis.

Evite projetar o pipeline central dependendo de scraping do Scholar.

---

### OpenAlex

**Prioridade: muito alta**

Excelente para:

- descoberta;
- metadados;
- referências;
- citações;
- autores;
- instituições;
- DOI;
- identificação de versões;
- cobertura ampla.

É uma das melhores bases para automação aberta.

Site/API:

- https://openalex.org/
- https://docs.openalex.org/

Uso:

```text
OpenAlex
   ↓
busca por tema
   ↓
DOI / OpenAlex ID
   ↓
references + cited_by
```

---

### Crossref

**Prioridade: muito alta para normalização**

Crossref deve ser usado principalmente como autoridade para:

- DOI;
- título;
- autores;
- ano;
- venue;
- tipo de publicação;
- links registrados.

Não é necessariamente a melhor ferramenta para descoberta temática complexa, mas é excelente para consolidar metadados.

API:

- https://api.crossref.org/

---

### Semantic Scholar

**Prioridade: alta**

Útil para:

- descoberta;
- papers relacionados;
- citations;
- references;
- embeddings/semantic similarity;
- abstracts;
- autores;
- graph traversal.

API:

- https://api.semanticscholar.org/

---

### arXiv

**Prioridade: muito alta para VO/SLAM recente**

Muito relevante em:

- visão computacional;
- robótica;
- machine learning;
- SLAM;
- foundation models;
- datasets;
- métodos ainda não publicados formalmente.

Uso:

```text
arXiv
  ↓
preprint
  ↓
verificar DOI / publicação posterior
  ↓
ligar versões
```

API:

- https://export.arxiv.org/api_help/

---

### CVF Open Access

**Prioridade: muito alta**

Para trabalhos de:

- CVPR;
- ICCV;
- WACV.

Site:

- https://openaccess.thecvf.com/

Pode ser consultado diretamente e cruzado por DOI/título.

---

### OpenReview

**Prioridade: alta para métodos recentes de ML**

Relevante para:

- ICLR;
- workshops;
- algumas conferências de aprendizado de máquina;
- versões submetidas e revisões públicas.

Site/API:

- https://openreview.net/
- https://docs.openreview.net/

---

### DBLP

**Prioridade: média-alta**

Muito útil para:

- normalização de autores;
- conferências de computação;
- identificação de versões;
- metadados de papers;
- validação de venues.

API:

- https://dblp.org/faq/How+to+use+the+dblp+search+API.html

---

### SpringerLink

**Prioridade: média-alta**

Importante para:

- robótica;
- visão;
- conferências;
- livros;
- capítulos;
- LNCS;
- Intelligent Systems.

Site:

- https://link.springer.com/

Quando possível, usar DOI + Crossref/OpenAlex para metadados e apenas resolver o texto integral via acesso institucional/open access.

---

### ScienceDirect / Elsevier

**Prioridade: alta**

Importante para periódicos como:

- Robotics and Autonomous Systems;
- Pattern Recognition;
- Neural Networks;
- Image and Vision Computing;
- outras áreas relacionadas.

API:

- https://dev.elsevier.com/

---

### PubMed

**Prioridade: baixa-média para este tema, mas útil em visão aplicada a ambientes/saúde/sensores**

Pode ser útil para:

- artigos de imagem;
- qualidade visual;
- visão atmosférica aplicada;
- sensoriamento biológico;
- alguns métodos de visão.

API:

- https://www.ncbi.nlm.nih.gov/books/NBK25501/

---

### Lens

**Prioridade: complementar**

Útil para:

- literatura;
- patentes;
- relações ciência-tecnologia.

Site:

- https://www.lens.org/

---

# 4. Papel de cada fonte no pipeline

Uma divisão recomendada:

| Fonte | Descoberta | DOI/Metadados | Citações | PDF | Papel principal |
|---|---:|---:|---:|---:|---|
| IEEE Xplore | alta | alta | média | depende do acesso | literatura IEEE |
| ACM DL | alta | alta | média | depende do acesso | computação |
| Scopus | muito alta | alta | muito alta | não primário | indexação |
| Web of Science | muito alta | alta | muito alta | não primário | indexação |
| Google Scholar | muito alta | média | alta | indireto | descoberta complementar |
| OpenAlex | muito alta | alta | muito alta | indireto | automação aberta |
| Crossref | média | muito alta | baixa | indireto | normalização DOI |
| Semantic Scholar | alta | alta | muito alta | indireto | grafo e similaridade |
| arXiv | alta | alta | média | alta | preprints |
| CVF Open Access | alta | alta | baixa | muito alta | CVPR/ICCV/WACV |
| OpenReview | alta | alta | média | alta | ML recente |
| DBLP | média | alta | média | indireto | metadados de computação |
| SpringerLink | alta | alta | baixa | depende do acesso | publisher |
| ScienceDirect | alta | alta | baixa | depende do acesso | publisher |

---

# 5. Arquivo de configuração das buscas

Criar:

```text
config/search_queries.yaml
```

Exemplo:

```yaml
project:
  name: vo_slam_amazon_review
  review_start_year: 2018
  current_year: 2026

sources:
  openalex:
    enabled: true
    max_results_per_query: 200

  crossref:
    enabled: true
    max_results_per_query: 200

  semantic_scholar:
    enabled: true
    max_results_per_query: 200

  arxiv:
    enabled: true
    max_results_per_query: 200

  ieee_xplore:
    enabled: true
    api_key_env: IEEE_API_KEY

  scopus:
    enabled: true
    api_key_env: SCOPUS_API_KEY

  web_of_science:
    enabled: true
    api_key_env: WOS_API_KEY

  google_scholar:
    enabled: true
    mode: supplementary_manual_or_authorized_service

themes:

  fundamentals_taxonomy:
    year_from: 2010
    queries:
      - '"visual odometry" survey'
      - '"visual SLAM" survey'
      - '"visual odometry" taxonomy'
      - '"visual SLAM" taxonomy'

  classical_geometric:
    year_from: 2010
    queries:
      - '"visual odometry" feature based robustness'
      - '"direct visual odometry" robustness'
      - '"ORB-SLAM" adverse conditions'
      - '"DSO" illumination robustness'

  deep_vo_slam:
    year_from: 2018
    queries:
      - '"deep visual odometry"'
      - '"learning based visual odometry"'
      - '"deep visual SLAM"'
      - '"neural visual odometry"'
      - '"foundation model" "visual odometry"'

  robustness_corruptions:
    year_from: 2018
    queries:
      - '"visual SLAM" image corruption'
      - '"visual odometry" adverse conditions'
      - '"visual SLAM" robustness benchmark'
      - '"visual odometry" failure analysis'

  atmospheric_optical:
    year_from: 2015
    queries:
      - '"visual odometry" fog'
      - '"visual SLAM" fog'
      - '"visual odometry" smoke'
      - '"visual SLAM" smoke'
      - '"camera" smoke atmospheric scattering robotics'

  datasets_benchmarks:
    year_from: 2018
    queries:
      - '"visual SLAM" adverse weather dataset'
      - '"visual odometry" benchmark adverse conditions'
      - '"SLAM" all-weather dataset'
      - '"camera corruption" robotics dataset'

  metrics_protocol:
    year_from: 2015
    queries:
      - '"visual odometry" ATE RPE evaluation'
      - '"SLAM" robustness evaluation protocol'
      - '"visual odometry" tracking failure metric'

  forest_uav_amazon:
    year_from: 2015
    queries:
      - '"visual odometry" UAV forest'
      - '"visual SLAM" forest'
      - '"visual navigation" UAV forest'
      - '"visual odometry" wildfire UAV'
      - '"SLAM" tropical forest'
```

---

# 6. Credenciais

Nunca colocar chaves de API diretamente no código.

Criar:

```text
.env
```

Exemplo:

```bash
IEEE_API_KEY=...
SCOPUS_API_KEY=...
WOS_API_KEY=...
SEMANTIC_SCHOLAR_API_KEY=...
ELSEVIER_API_KEY=...
```

Adicionar ao:

```text
.gitignore
```

```gitignore
.env
*.key
secrets/
```

---

# 7. Estrutura de diretórios

```text
literature_review/
│
├── README.md
├── .gitignore
├── .env
│
├── config/
│   ├── search_queries.yaml
│   ├── inclusion_rules.yaml
│   ├── source_config.yaml
│   └── schema/
│       └── vo_slam_literature_review.schema.json
│
├── src/
│   ├── search/
│   │   ├── openalex.py
│   │   ├── crossref.py
│   │   ├── semantic_scholar.py
│   │   ├── arxiv.py
│   │   ├── ieee.py
│   │   ├── scopus.py
│   │   ├── web_of_science.py
│   │   └── scholar_import.py
│   │
│   ├── normalize.py
│   ├── deduplicate.py
│   ├── screen.py
│   ├── resolve_pdf.py
│   ├── extract.py
│   ├── validate.py
│   ├── snowball.py
│   ├── export.py
│   └── update.py
│
├── metadata/
│   ├── raw/
│   │   ├── openalex/
│   │   ├── crossref/
│   │   ├── ieee/
│   │   ├── scopus/
│   │   ├── wos/
│   │   └── scholar/
│   │
│   ├── normalized/
│   └── deduplicated/
│
├── papers/
│   ├── P0001/
│   │   ├── metadata.json
│   │   ├── paper.pdf
│   │   └── extraction.json
│   └── ...
│
├── screening/
│   ├── title_abstract_screening.csv
│   ├── full_text_screening.csv
│   └── exclusions.csv
│
├── tables/
│   ├── papers.csv
│   ├── methods.csv
│   ├── corruptions.csv
│   ├── datasets.csv
│   ├── metrics.csv
│   ├── evidence.csv
│   └── project_implications.csv
│
├── logs/
│   ├── search_runs.csv
│   ├── api_errors.log
│   ├── download_errors.log
│   └── extraction_errors.log
│
└── reports/
    ├── prisma/
    ├── bibliometrics/
    └── summaries/
```

---

# 8. Pipeline de busca

## 8.1 Camada 1 — busca nas bases

Para cada tema:

```python
for theme in themes:
    for query in theme.queries:
        for source in enabled_sources:
            search(source, query)
```

Cada resultado bruto deve ser salvo antes de qualquer transformação.

Exemplo:

```text
metadata/raw/openalex/2026-09-20_T3_query01.json
metadata/raw/ieee/2026-09-20_T3_query01.json
```

Nunca sobrescrever resultados históricos.

---

# 9. Modelo de registro bruto

Cada conector pode devolver campos diferentes.

Normalizar posteriormente.

Registro bruto:

```json
{
  "source": "ieee_xplore",
  "query": "\"visual odometry\" smoke",
  "retrieved_at": "2026-09-20T10:30:00Z",
  "source_record": {}
}
```

---

# 10. Normalização

Converter registros de todas as bases para um modelo comum.

Exemplo:

```json
{
  "paper_id": null,
  "title": "...",
  "authors": [],
  "year": 2025,
  "venue": "...",
  "doi": "...",
  "arxiv_id": null,
  "openalex_id": null,
  "semantic_scholar_id": null,
  "scopus_id": null,
  "wos_id": null,
  "ieee_document_id": null,
  "url": "...",
  "abstract": "...",
  "source_databases": [
    "ieee_xplore",
    "openalex",
    "crossref"
  ]
}
```

---

# 11. Deduplicação

A deduplicação deve ocorrer antes da triagem por LLM.

Ordem recomendada:

```text
1. DOI exato
2. arXiv ID exato
3. IEEE document ID / Scopus ID / WoS ID
4. título normalizado
5. título + primeiro autor + ano
6. similaridade fuzzy de título
```

Normalização de título:

```text
lowercase
remove punctuation
normalize whitespace
remove accents quando necessário
normalize unicode
```

Exemplo:

```text
"DROID-SLAM: Deep Visual SLAM for Monocular..."
```

e

```text
"DROID SLAM Deep Visual SLAM for Monocular..."
```

devem ser considerados candidatos à mesma obra.

---

## 11.1 Limiar fuzzy

Exemplo:

```text
similaridade >= 0.96
AND
primeiro autor compatível
AND
|ano1 - ano2| <= 1
```

→ provável duplicata.

Não fundir automaticamente preprint e versão publicada se houver diferenças substanciais.

---

# 12. Controle de versões

Um trabalho pode aparecer como:

```text
arXiv
  ↓
conference
  ↓
journal extension
```

Representar explicitamente:

```json
{
  "version_relation": {
    "type": "published_version_of",
    "related_paper_id": "P0032"
  }
}
```

Tipos:

```text
preprint_of
published_version_of
extended_version_of
conference_version_of
journal_version_of
duplicate_of
```

---

# 13. Geração do paper_id

Nunca usar DOI como chave primária.

Usar:

```text
P0001
P0002
P0003
...
```

DOI e outros IDs são identificadores externos.

---

# 14. Triagem automática

Primeira fase:

```text
título + resumo
```

Prompt:

```text
Avalie se este artigo deve seguir para leitura integral na revisão
sobre robustez de Visual Odometry/Visual SLAM em condições adversas.

Classifique:

INCLUDE
MAYBE
EXCLUDE

Critérios de inclusão:
- VO, Visual SLAM ou localização visual;
- robustez, condições adversas, datasets, métricas;
- degradações visuais;
- floresta/UAV;
- métodos relevantes;
- formação/restauração de imagem com ligação clara a percepção robótica.

Critérios de exclusão:
- SLAM exclusivamente LiDAR sem componente visual;
- processamento de imagem sem relação com localização/percepção;
- navegação sem componente de VO/VSLAM;
- artigo sem conexão técnica relevante.

Retorne:
decision:
reason:
themes:
confidence:
```

---

# 15. Regra de triagem

Automatizar priorização, não exclusão irreversível.

Exemplo:

```text
INCLUDE → segue
MAYBE → revisão humana
EXCLUDE + confidence < 0.90 → revisão humana
EXCLUDE + confidence >= 0.90 → fila de exclusão para auditoria
```

Toda exclusão deve manter:

```text
paper_id
reason
model/version
date
confidence
human_confirmed
```

---

# 16. Aquisição de texto integral

A aquisição deve ocorrer depois da deduplicação e triagem.

Ordem:

```text
1. link open access fornecido pela base
2. arXiv
3. CVF Open Access
4. OpenReview
5. repositório institucional
6. Unpaywall / OA resolver
7. acesso institucional autorizado
8. metadata_only
```

Nunca contornar paywall ou controle de acesso.

---

# 17. Google Scholar no pipeline

Google Scholar deve funcionar como **camada complementar**, não como backbone.

Fluxo:

```text
busca manual ou serviço autorizado
        ↓
exportar BibTeX / RIS / CSV
        ↓
importar para metadata/raw/scholar/
        ↓
normalizar
        ↓
deduplicar
```

Assim ele contribui para a cobertura sem comprometer a robustez do sistema.

---

# 18. Snowballing

Duas direções:

## Backward snowballing

```text
paper
 ↓
references
 ↓
novos candidatos
```

## Forward snowballing

```text
paper
 ↓
citing papers
 ↓
novos candidatos
```

Fontes úteis:

```text
OpenAlex
Semantic Scholar
Scopus
Web of Science
Google Scholar
```

---

# 19. Seed papers

Criar uma lista inicial de referências centrais:

```yaml
seed_papers:
  - ORB-SLAM2
  - ORB-SLAM3
  - DSO
  - TartanVO
  - DROID-SLAM
  - DPVO
  - QueensCAMP
  - SubT-MRS
```

Para cada seed:

```text
backward citations
forward citations
related papers
same authors
same venue
similar title/abstract
```

---

# 20. Extração para JSON Schema

Após baixar ou acessar o texto integral:

```text
paper.pdf
   ↓
LLM extraction
   ↓
extraction.json
   ↓
JSON Schema validator
```

Arquivo esperado:

```text
config/schema/vo_slam_literature_review.schema.json
```

---

# 21. Validação

Todo JSON produzido deve passar por:

```python
jsonschema.validate(instance=data, schema=schema)
```

Se falhar:

```text
status = EXTRACTION_INVALID
```

e deve ser reprocessado ou enviado para revisão.

---

# 22. Evidências

Toda conclusão importante deve ter:

```text
evidence_id
claim
quote_or_paraphrase
page
section
table
figure
support_level
```

Exemplo:

```json
{
  "evidence_id": "E004",
  "claim_type": "result",
  "claim": "O método perde rastreamento em fog denso.",
  "quote_or_paraphrase": "...",
  "location": {
    "page": 7,
    "section": "Experiments",
    "table": "Table 3"
  },
  "support_level": "direct"
}
```

---

# 23. Conversão para modelo tabular

O JSON hierárquico deve alimentar tabelas relacionais.

## PAPERS

```text
paper_id
title
year
venue
doi
publication_type
priority
relevance_score
```

## METHODS

```text
paper_id
method_name
method_family
sensor_modalities
architecture_family
training_type
```

## CORRUPTIONS

```text
paper_id
corruption
family
real_synthetic
severity
generation_method
metric
effect
```

## DATASETS

```text
paper_id
dataset_name
environment
platform
sensors
ground_truth
conditions
```

## METRICS

```text
paper_id
metric
definition
alignment
aggregation
```

## EVIDENCE

```text
paper_id
evidence_id
claim
location
support_level
```

## PROJECT_IMPLICATIONS

```text
paper_id
impact_class
affected_component
summary
```

---

# 24. Status operacional

Criar uma state machine simples:

```text
DISCOVERED
NORMALIZED
DEDUPLICATED
SCREEN_PENDING
SCREEN_INCLUDED
SCREEN_MAYBE
SCREEN_EXCLUDED
PDF_FOUND
PDF_UNAVAILABLE
EXTRACTION_PENDING
EXTRACTED
EXTRACTION_INVALID
HUMAN_REVIEWED
```

---

# 25. Tabela de acompanhamento

```text
paper_id
status
discovered_at
sources
screening_decision
pdf_status
extraction_status
human_review_status
```

---

# 26. Atualização incremental

Guardar:

```text
last_search_date
```

Exemplo:

```text
2026-09-20
```

Próxima execução:

```text
buscar apenas registros novos/atualizados
      ↓
deduplicar contra corpus
      ↓
processar apenas novidades
```

Frequência recomendada:

```text
quinzenal ou mensal
```

---

# 27. Living review

A pipeline pode rodar periodicamente:

```text
cron / GitHub Actions / servidor local
```

Exemplo mensal:

```text
dia 1
 ↓
busca incremental
 ↓
normalização
 ↓
deduplicação
 ↓
triagem
 ↓
fila de revisão
```

Não automatizar downloads que dependam de sessão institucional em ambiente CI sem autorização explícita.

---

# 28. Logging

Cada chamada deve ser registrada:

```text
run_id
timestamp
source
theme
query
filters
results_found
results_new
duplicates
errors
duration
```

Arquivo:

```text
logs/search_runs.csv
```

---

# 29. Reprodutibilidade

Registrar:

```text
query
base
data
hora
filtros
API version
número de resultados
código commit hash
```

No artigo final, isso permite relatar exatamente:

> A busca foi realizada nas bases X, Y e Z usando as seguintes strings e filtros...

---

# 30. Exportação para Zotero

Vale integrar o Zotero como biblioteca humana final.

Fluxo:

```text
pipeline
   ↓
BibTeX/RIS
   ↓
Zotero
```

Salvar em coleções:

```text
01_Fundamentals
02_Classical
03_DeepVO
04_Robustness
05_Atmospheric
06_Datasets
07_Metrics
08_Forest_UAV
```

Tags:

```text
essential
important
complementary
included
excluded
fulltext
needs_review
```

---

# 31. Relatório estilo PRISMA

Mesmo que o projeto não seja uma revisão sistemática formal, manter números ajuda muito.

Registrar:

```text
records_identified
duplicates_removed
records_screened
records_excluded
full_text_assessed
full_text_excluded
studies_included
```

Gerar o fluxograma no final.

---

# 32. Estratégia de consulta recomendada

## Camada A — alta precisão

Buscar por frases exatas:

```text
"visual odometry" smoke
"visual SLAM" fog
"visual odometry" robustness
"visual SLAM" adverse conditions
```

## Camada B — alta cobertura

Combinar termos:

```text
("visual odometry" OR "visual SLAM")
AND
(smoke OR fog OR haze OR rain OR condensation OR "wet lens")
```

## Camada C — papers relacionados

```text
seed paper
 ↓
references
citations
related works
```

---

# 33. Estratégia por base

## IEEE Xplore

Usar queries técnicas curtas e filtros por:

```text
publication year
content type
index terms
author keywords
```

## Scopus

Usar:

```text
TITLE-ABS-KEY(...)
```

## Web of Science

Usar:

```text
TS=(...)
```

## Google Scholar

Usar queries menores e verificar:

```text
allintitle:
"exact phrase"
author:
year range
```

## OpenAlex

Usar:

```text
search
filter by publication_year
concept/topic
cited_by
references
```

## Semantic Scholar

Usar:

```text
paper search
paper recommendations
citations
references
```

---

# 34. Controle de qualidade

Criar um conjunto de 10–20 artigos manualmente revisados.

Usá-lo para medir:

```text
recall da busca
precision da triagem
accuracy da classificação temática
qualidade da extração
```

---

# 35. Teste piloto

Antes de processar centenas de artigos:

```text
2 papers de fundamentos
2 clássicos
2 deep
2 robustez
2 atmospheric
2 datasets
2 metrics
2 forest/UAV
```

Total aproximado:

```text
16 artigos
```

Avaliar:

```text
campos vazios
campos ambíguos
enum inadequado
erros de classificação
erros de evidência
```

---

# 36. O que automatizar

```text
busca
normalização
deduplicação
resolução de DOI
snowballing
priorização
download open access permitido
extração estruturada
validação do JSON
conversão para tabelas
atualização periódica
```

---

# 37. O que manter com revisão humana

```text
inclusão/exclusão final
interpretação de resultados contraditórios
avaliação de limitações
mudança metodológica do projeto
comparação entre fumaça real e sintética
conclusões sobre validade externa para a Amazônia
```

---

# 38. Arquitetura de software

```text
search.py
normalize.py
deduplicate.py
screen.py
snowball.py
resolve_pdf.py
extract.py
validate.py
relationalize.py
export.py
update.py
report.py
```

---

# 39. Pseudocódigo principal

```python
config = load_config()

raw_records = []

for theme in config.themes:
    for query in theme.queries:
        for source in enabled_sources:
            records = source.search(
                query=query,
                year_from=theme.year_from,
                year_to=config.current_year
            )
            save_raw(records)
            raw_records.extend(records)

normalized = normalize(raw_records)

deduplicated = deduplicate(normalized)

assign_internal_ids(deduplicated)

screened = screen_titles_and_abstracts(deduplicated)

for paper in screened.included_or_maybe:
    resolve_open_access_or_authorized_fulltext(paper)

for paper in papers_with_fulltext:
    extraction = extract_to_schema(paper)
    validate_schema(extraction)
    save_extraction(extraction)

relationalize_extractions()

export_csv()
export_bibtex()
generate_review_report()
```

---

# 40. Política para Google Scholar

Recomendação operacional:

```text
Google Scholar = ferramenta de cobertura complementar
```

Não depender dele para:

```text
IDs canônicos
metadados finais
download automatizado em massa
estado principal do corpus
```

Após encontrar um artigo no Scholar:

```text
título/DOI
   ↓
Crossref/OpenAlex
   ↓
publisher/arXiv/repositório
```

---

# 41. Política para IEEE, Scopus e Web of Science

Estas bases podem ser fundamentais para a revisão, mas o pipeline deve lidar com dois cenários:

## Com acesso/API institucional

```text
API oficial
 ↓
metadados
 ↓
normalização
 ↓
deduplicação
```

## Sem acesso API

```text
busca manual institucional
 ↓
exportação RIS/BibTeX/CSV
 ↓
importação automática
 ↓
normalização
```

A arquitetura deve aceitar ambos.

---

# 42. Importação manual como fallback

Criar pasta:

```text
metadata/import/
```

Aceitar:

```text
BibTeX
RIS
CSV
JSON
```

Assim qualquer base pode ser incorporada mesmo sem API.

---

# 43. Prioridade recomendada das integrações

## Fase 1

Implementar primeiro:

```text
OpenAlex
Crossref
Semantic Scholar
arXiv
CVF/OpenReview quando relevante
```

São suficientes para validar o pipeline.

## Fase 2

Adicionar:

```text
IEEE Xplore
Scopus
Web of Science
```

quando credenciais/acesso estiverem disponíveis.

## Fase 3

Adicionar:

```text
Google Scholar como fonte complementar
ACM DL
SpringerLink
ScienceDirect
DBLP
Lens
```

---

# 44. Ordem de execução por tema

Para cada tema:

```text
query search
 ↓
deduplicate
 ↓
rank
 ↓
screen
 ↓
snowball
 ↓
screen novamente
```

O snowballing não deve ocorrer antes da primeira triagem, senão o corpus cresce rapidamente com baixa relevância.

---

# 45. Ranking para revisão humana

A ordenação pode usar:

```text
relevance_score
recency
citation count
seed similarity
theme coverage
open access availability
```

Esses fatores devem servir apenas para **priorizar leitura**, não para excluir literatura.

---

# 46. Critérios de inclusão sugeridos

```yaml
include_if:
  - visual_odometry
  - visual_slam
  - visual_localization_with_odometry_relevance
  - robustness
  - adverse_visual_conditions
  - optical_or_atmospheric_degradation
  - relevant_dataset
  - evaluation_protocol
  - UAV_or_forest_navigation
```

---

# 47. Critérios de exclusão sugeridos

```yaml
exclude_if:
  - lidar_only_without_visual_component
  - unrelated_image_enhancement
  - medical_imaging_without_robotics_relation
  - navigation_without_visual_pose_estimation
  - duplicate
  - non_scientific_source
```

Toda exclusão deve ser auditável.

---

# 48. Dados mínimos exigidos por paper

```text
paper_id
title
authors
year
venue
doi ou identificador alternativo
abstract
source_databases
theme
screening_status
fulltext_status
```

---

# 49. Backup e versionamento

Usar Git para:

```text
config
queries
scripts
schemas
logs resumidos
```

Não versionar PDFs protegidos por licença.

Armazenar PDFs conforme permissões de acesso e política institucional.

---

# 50. Resultado final esperado

Ao fim da pipeline, você deverá ter:

```text
1. corpus deduplicado
2. histórico completo de buscas
3. triagem auditável
4. PDFs legalmente acessados quando disponíveis
5. JSON estruturado por artigo
6. tabelas relacionais
7. Zotero/BibTeX atualizado
8. snowballing rastreável
9. revisão incremental
10. base pronta para escrita científica
```

---

# 51. Fontes e documentação úteis

## APIs e bases

- IEEE Developer Portal: https://developer.ieee.org/
- OpenAlex: https://openalex.org/
- OpenAlex Docs: https://docs.openalex.org/
- Crossref REST API: https://api.crossref.org/
- Semantic Scholar API: https://api.semanticscholar.org/
- arXiv API: https://export.arxiv.org/api_help/
- CVF Open Access: https://openaccess.thecvf.com/
- OpenReview: https://openreview.net/
- OpenReview Docs: https://docs.openreview.net/
- DBLP API: https://dblp.org/faq/How+to+use+the+dblp+search+API.html
- Elsevier Developer Portal / Scopus: https://dev.elsevier.com/
- Clarivate Developer Portal / Web of Science: https://developer.clarivate.com/
- ACM Digital Library: https://dl.acm.org/
- SpringerLink: https://link.springer.com/
- ScienceDirect: https://www.sciencedirect.com/
- PubMed/NCBI E-utilities: https://www.ncbi.nlm.nih.gov/books/NBK25501/
- Lens: https://www.lens.org/
- Google Scholar: https://scholar.google.com/

## Metadados e cobertura

Uma referência útil para entender por que é importante combinar bases abertas é:

Delgado-Quirós, L., & Ortega, J. L. (2024). *Completeness degree of publication metadata in eight free-access scholarly databases*. Quantitative Science Studies, 5(1), 31–49.  
https://direct.mit.edu/qss/article/5/1/31/119466

---

# 52. Recomendação final de desenho

A arquitetura recomendada é:

```text
                ┌──────────────────────┐
                │  queries por tema    │
                └─────────┬────────────┘
                          ↓
      ┌───────────────────┼────────────────────┐
      ↓                   ↓                    ↓
 IEEE/ACM/etc.       OpenAlex/Crossref    Scholar/manual
      │                   │                    │
      └───────────────────┼────────────────────┘
                          ↓
                normalização comum
                          ↓
                    deduplicação
                          ↓
                 triagem title/abstract
                          ↓
             forward/backward snowballing
                          ↓
                 resolução de full text
                          ↓
                 extração para JSON
                          ↓
               validação por schema
                          ↓
               tabelas relacionais
                          ↓
                 revisão humana
                          ↓
                  living review
```

Esse desenho permite começar com APIs abertas e, à medida que você tiver acesso institucional, incorporar IEEE Xplore, Scopus e Web of Science sem reescrever o restante do sistema.

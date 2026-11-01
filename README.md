# PIBIC 2026 — Odometria Visual em condições amazônicas

**Análise comparativa de métodos clássicos e baseados em deep learning para odometria
visual em cenários desafiadores representativos de condições amazônicas.**
Natasha Araújo Caxias — PIBIC/UFAM, projeto SAGRES-Pro.

Objetivo: avaliar a robustez de VO clássica (ORB-SLAM2) e aprendida (TartanVO, DPVO ou
DROID-SLAM) sob as falhas de câmera do QueensCAMP e sob fumaça emulada pelo modelo de
Koschmieder, com um dataset piloto coletado em Manaus.

## Estrutura

| Pasta/arquivo | Conteúdo |
|---|---|
| **`docs/roteiro_laboratorio.md`** | **Passo a passo para rodar os experimentos na máquina do laboratório** |
| `docs/plano_inicial.md` | Resumo da proposta, primeiros passos, sugestões, riscos e estado das sprints |
| `docs/leituras/` | Fichamentos (15 referências) e tabela comparativa dos métodos |
| `docs/trabalhos_relacionados.md` | Rascunho de Trabalhos Relacionados (inclui concorrentes de 2026) |
| `docs/protocolo_experimental.md` | Protocolo dos experimentos (rascunho para aprovação) |
| `docs/datasets.md`, `docs/ambiente.md` | QueensCAMP/SubT-MRS e configuração da máquina do laboratório |
| `docs/criterios_triagem.md`, `docs/nota_niveis_fumaca.md` | Critérios da revisão; justificativa dos níveis de fumaça |
| `docs/analise_concorrentes_2026.md` | SAL, Failure or Drift? e Kumar et al.: o que muda na originalidade |
| `docs/relatorio_parcial.md`, `docs/artigo_esqueleto.md` | Rascunho do relatório parcial e plano do artigo |
| `docs/plano_coleta_piloto.md` | Plano de coleta do dataset piloto (aguarda dados do hardware) |
| `docs/publicacao.md` | Auditoria do repositório, licença sugerida, declaração de dados e checklist antes de tornar público |
| `experiments/` | Pipeline para a máquina do laboratório: Docker por algoritmo, matriz de execuções, avaliação |
| `arquitetura_revisao_bibliografica_vo_slam.md` | Arquitetura da revisão bibliográfica (8 temas) |
| `literature_review/` | Coleta, deduplicação, pré-triagem por regras e triagem auditáveis (Crossref/arXiv) |
| `smoke_emulation/` | Emulação de fumaça (Koschmieder), dehazing (DCP) e validação por métricas de imagem |
| `vo_slam_literature_review.schema.json`, `prompt_extracao_revisao_vo_slam.txt` | Schema e prompt de extração |

Dados brutos, corpus SQLite, PDFs, saídas e ambientes virtuais **não** são versionados
(ver `.gitignore`).

## Estado do projeto (01/11/2026)

- **Execuções concluídas:** 3.350 avaliadas. Matriz principal de 2.720 (ORB-SLAM2 monocular e RGB-D, TartanVO, DPVO × 16 sequências do QueensCAMP × 10 condições), 112 de uma fumaça extrema e 518 de dehazing (DCP): piloto na seq. 09 e execução completa no ORB-SLAM2. Resultados e decisões de análise em [`docs/protocolo_experimental.md`](docs/protocolo_experimental.md) §10; rascunho do artigo, com tabelas, em [`docs/artigo_esqueleto.md`](docs/artigo_esqueleto.md).
- **DCP no ORB-SLAM2:** devolve o rastreamento ao RGB-D na fumaça densa (sucesso de 0% para 62,5%), não recupera o monocular e o prejudica na imagem limpa (§10.7).
- **Bloqueado por coleta física:** dataset piloto amazônico e EKF (NATASHA-13/14).
- As decisões de análise de §10 são de trabalho e **ainda não foram revisadas pelo orientador**.

## Como reproduzir

Requisitos: Ubuntu com driver NVIDIA ≥ 570 (a RTX 5070 Ti é Blackwell, sm_120), Docker com NVIDIA Container Toolkit, Python 3.10+ e ~140 GB de disco para os dados mais ~25 GB de imagens. Passo a passo em [`experiments/README.md`](experiments/README.md) e [`docs/ambiente.md`](docs/ambiente.md). Resumo:

```bash
cd experiments
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests            # 45 testes, sem GPU
docker build -t pibic/dpvo:0ac95b6 algorithms/dpvo        # idem tartanvo:ec2ecc3 e orbslam2:f2e6f51
.venv/bin/python scripts/dataset.py download --dest /data/queenscamp_raw --sequences 09 --kind full
.venv/bin/python scripts/dataset.py smoke --sequences 09
.venv/bin/python scripts/run_matrix.py --algorithms dpvo --sequences 09 --conditions original --max-runs 1
.venv/bin/python scripts/evaluate.py && .venv/bin/python scripts/stats_analysis.py && .venv/bin/python scripts/figures.py
```

A matriz principal levou cerca de 43 h neste servidor. Tudo é retomável (`run_matrix.py` pula execuções com `meta.json`).

## Dados e licenças

- **QueensCAMP** e **SubT-MRS** não são redistribuídos aqui: `scripts/dataset.py download` baixa o QueensCAMP do site dos autores. Os quadros reais do SubT-MRS, a fumaça sintética e o dehazing gerados a partir dos dados ficam fora do git. A licença do SubT-MRS não é declarada na página dos autores; a do QueensCAMP não foi conferida. Detalhes em [`docs/datasets.md`](docs/datasets.md).
- Os algoritmos rodam em containers construídos a partir dos repositórios originais em commits fixos: ORB-SLAM2 (GPLv3), TartanVO (BSD 3-Clause), DPVO (MIT).
- **Licença do código e do texto deste repositório: ainda não definida.** A sugestão e a lista do que verificar antes de tornar o repositório público estão em [`docs/publicacao.md`](docs/publicacao.md).

## Como citar

[PENDENTE: preencher com o artigo ou o relatório final; ver `docs/artigo_esqueleto.md`.]

## Planejamento

Backlog e sprints no Jira, projeto **NATASHA**:
<https://robotica-icomp.atlassian.net/jira/software/projects/NATASHA/boards/5/backlog>

| Épico | Etapa da proposta |
|---|---|
| NATASHA-1 Fundamentação e Estado da Arte | 1 — Revisão (meses 1–3) |
| NATASHA-2 Infraestrutura Computacional e Emulação | 2 — Ambiente e emulação (meses 3–6) |
| NATASHA-3 Dataset Piloto Amazônico | 3 — Coleta piloto (meses 5–6) |
| NATASHA-4 Execução de Experimentos em Massa | 4 — Experimentos (meses 6–9) |
| NATASHA-5 Análise Estatística e Divulgação | 5–6 — Análise e redação (meses 9–12) |

Commits devem citar a tarefa, ex.: `NATASHA-11: adiciona preenchimento de buracos`.

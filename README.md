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
| `docs/plano_inicial.md` | Resumo da proposta, primeiros passos, sugestões, riscos e estado das sprints |
| `docs/leituras/` | Fichamentos (15 referências) e tabela comparativa dos métodos |
| `docs/trabalhos_relacionados.md` | Rascunho de Trabalhos Relacionados (inclui concorrentes de 2026) |
| `docs/protocolo_experimental.md` | Protocolo dos experimentos (rascunho para aprovação) |
| `docs/datasets.md`, `docs/ambiente.md` | QueensCAMP/SubT-MRS e configuração da máquina do laboratório |
| `docs/criterios_triagem.md`, `docs/nota_niveis_fumaca.md` | Critérios da revisão; justificativa dos níveis de fumaça |
| `docs/analise_concorrentes_2026.md` | SAL, Failure or Drift? e Kumar et al.: o que muda na originalidade |
| `docs/relatorio_parcial.md`, `docs/artigo_esqueleto.md` | Rascunho do relatório parcial e plano do artigo |
| `docs/plano_coleta_piloto.md` | Plano de coleta do dataset piloto (aguarda dados do hardware) |
| `experiments/` | Pipeline para a máquina do laboratório: Docker por algoritmo, matriz de execuções, avaliação |
| `arquitetura_revisao_bibliografica_vo_slam.md` | Arquitetura da revisão bibliográfica (8 temas) |
| `literature_review/` | Coleta, deduplicação, pré-triagem por regras e triagem auditáveis (Crossref/arXiv) |
| `smoke_emulation/` | Emulação de fumaça (Koschmieder), dehazing (DCP) e validação por métricas de imagem |
| `vo_slam_literature_review.schema.json`, `prompt_extracao_revisao_vo_slam.txt` | Schema e prompt de extração |

Dados brutos, corpus SQLite, PDFs, saídas e ambientes virtuais **não** são versionados
(ver `.gitignore`).

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

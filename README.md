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
| `docs/plano_inicial.md` | Resumo da proposta, primeiros passos, sugestões e riscos |
| `docs/leituras/` | Lista de leitura e fichamentos |
| `arquitetura_revisao_bibliografica_vo_slam.md` | Arquitetura da revisão bibliográfica (8 temas) |
| `literature_review/` | Coleta, deduplicação e triagem auditáveis (Crossref/arXiv) |
| `smoke_emulation/` | Emulação de fumaça/névoa (Koschmieder) |
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

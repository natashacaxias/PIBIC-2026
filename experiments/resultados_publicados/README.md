# Resultados publicáveis (cópia de `experiments/results/`, 01/11/2026)

Cópia dos CSV agregados e das figuras próprias, gerados por `scripts/evaluate.py`, `scripts/stats_analysis.py` e `scripts/figures.py` sobre **3.410 execuções** (2.720 da matriz principal, 112 da fumaça extrema e 578 do DCP) no código do commit que acompanha esta cópia. `results/` continua fora do git; esta pasta é a cópia versionada e só deve ser atualizada ao regenerar tudo.

| Arquivo | Conteúdo |
|---|---|
| `metrics.csv` | uma linha por execução (3.410): status, rastreamento, ATE (Sim(3), SE(3), escala por passo), RPE, tempo, memória de GPU |
| `summary.csv` | agregado por algoritmo, sequência e condição |
| `stats_vs_original.csv`, `stats_pairwise.csv`, `stats_robustness.csv` | testes pareados (Wilcoxon, Bonferroni), comparações entre métodos e critério de robustez |
| `stats_exploratory.csv`, `stats_dcp.csv` | condições exploratórias (fumaça extrema, DCP) e DCP contra a condição de origem |
| `stats_report.md` | relatório em texto |
| `figures/` | mapa de calor da degradação, erro cumulativo, rastreamento e uma trajetória ilustrativa |

Fora desta pasta de propósito: trajetórias e logs das execuções (volume) e a figura `smoke_real_vs_sintetica`, que contém quadros reais do SubT-MRS (licença não declarada). Dados do QueensCAMP não são redistribuídos (`docs/datasets.md`). Licença: CC BY 4.0 (`docs/LICENSE.md`).

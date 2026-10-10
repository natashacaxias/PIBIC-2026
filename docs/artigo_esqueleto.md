# Esqueleto do artigo — v0.1

Jira: NATASHA-20. **Template e venue a definir com o orientador**: a proposta cita SIBGRAPI, LARS/SBR e WRE. Verificar os prazos e o limite de páginas no site de cada evento antes de fixar o escopo.

## Título provisório
*Smoke, Lenses and Learned Odometry: A Statistically Grounded Robustness Study of Classical and Deep Visual Odometry under Real Lens Failures and Physically Calibrated Smoke*
(alternativa em português para o WRE/LARS: "Fumaça, lentes e odometria visual: robustez de métodos clássicos e aprendidos sob degradações representativas da Amazônia")

## Mensagem central (uma frase)
[DEPENDE DOS RESULTADOS] Ex.: "Sob fumaça densa, métodos aprendidos trocam falha por deriva, mas sua vantagem relativa se inverte nas falhas de lente; a fumaça calibrada com fumaça real preserva / não preserva a ordem entre métodos."

## Estrutura (6–8 páginas)
| Seção | Conteúdo | Fonte no repositório | Tamanho |
|---|---|---|---|
| 1. Introdução | motivação SAGRES-Pro e Amazônia; lacuna; 3–4 contribuições numeradas | `relatorio_parcial.md` §1, `analise_concorrentes_2026.md` §3 | 0,75 p |
| 2. Trabalhos relacionados | VO clássica/aprendida; robustez; névoa sintética; concorrentes de 2026 | `trabalhos_relacionados.md` | 0,75 p |
| 3. Emulação de fumaça e validação | modelo, níveis, profundidade, cor da fumaça; validação contra o SubT-MRS | `nota_niveis_fumaca.md`, `smoke_emulation/validate_smoke.py` | 1 p |
| 4. Protocolo experimental | dados, métodos, configuração justa (escala, stride, loop), repetições, métricas, estatística | `protocolo_experimental.md` | 1 p |
| 5. Resultados | reprodução do QueensCAMP; robustez por condição; falha × deriva; DCP; custo | `results/` | 2 p |
| 6. Discussão | gap de domínio; fidelidade da fumaça; implicações para o SAGRES-Pro; limitações (homogêneo, indoor) | — | 0,75 p |
| 7. Conclusão | — | — | 0,25 p |

## Figuras e tabelas planejadas
| # | Conteúdo | Gerada por |
|---|---|---|
| Fig. 1 | Exemplos: original, 3 níveis de fumaça, 1 falha de lente, fumaça real do SubT-MRS | montagem manual a partir de `smoke_emulation/` |
| Fig. 2 | Mapa de calor da degradação do ATE (método × condição) | `experiments/scripts/figures.py` → `degradacao_heatmap` |
| Fig. 3 | Erro cumulativo em original / molhada / fumaça densa | `figures.py` → `erro_cumulativo` |
| Fig. 4 | Rastreamento por condição | `figures.py` → `rastreamento` |
| Fig. 5 | Trajetórias GT × estimativa em um caso ilustrativo | `figures.py --trajectory` |
| Tab. 1 | Reprodução do QueensCAMP (artigo × nosso), seq. selecionadas | `results/summary.csv` |
| Tab. 2 | Comparações pareadas (Wilcoxon + Bonferroni + IC) por condição | `scripts/stats_analysis.py` → `stats_report.md` |
| Tab. 3 | Fumaça sintética × real: métricas de imagem | `validate_smoke.py` → `report.md` |

## Contribuições (rascunho, ajustar após a reunião)
1. Um protocolo de avaliação com **configuração justa entre paradigmas** (escala, stride, loop closure) e **análise estatística pareada** com repetições, aberto e reproduzível em Docker para GPUs Blackwell.
2. **Fumaça emulada sobre profundidade medida, validada contra fumaça real**, combinada às falhas de lente do QueensCAMP.
3. Evidência de **como a degradação se manifesta** (falha × deriva) em ORB-SLAM2, TartanVO e DPVO, e da utilidade (ou não) do dehazing clássico.
4. Estudo de caso descritivo com dados coletados na Amazônia.

## Resumo (rascunho com lacunas)
A odometria visual é essencial para a navegação de veículos autônomos em florestas, mas degradações ópticas como fumaça de queimadas e falhas de lente comprometem seu funcionamento. Avaliamos o ORB-SLAM2, o TartanVO e o DPVO no dataset QueensCAMP sob seis falhas de câmera e três níveis de fumaça emulada fisicamente sobre profundidade medida e validada contra fumaça real. Em [N] execuções com repetições e testes pareados, observamos que [RESULTADO 1] e que [RESULTADO 2]. O pré-processamento com Dark Channel Prior [RESULTADO 3]. Código, configurações e resultados estão disponíveis em [URL].

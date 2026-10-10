# Plano inicial e sugestões — PIBIC VO em condições amazônicas

Documento de trabalho (10/10/2026). Resume a proposta, o estado atual e os primeiros
passos. As sugestões marcadas com **[discutir]** dependem do orientador.

## 1. A pesquisa em uma frase

Medir quanto métodos de odometria visual **clássicos** (ORB-SLAM2, extensão ORB-SLAM3/DSO)
e **baseados em deep learning** (TartanVO, DPVO ou DROID-SLAM) degradam sob falhas de
câmera do QueensCAMP e sob **fumaça emulada** (modelo de Koschmieder), complementando com
um pequeno dataset piloto coletado em Manaus, no contexto do SAGRES-Pro.

Pergunta central: *qual paradigma é mais robusto a cada tipo de degradação, medido pela
degradação percentual de ATE/RPE em relação à própria condição original?*

## 2. Estado atual

| Item | Situação |
|---|---|
| Proposta (`Form-Pibic-Natasha-VO-v3.docx`) | Aprovada; 6 etapas em 12 meses |
| Arquitetura da revisão (`arquitetura_revisao_bibliografica_vo_slam.md`) | Pronta; 8 temas T1–T8 |
| Ferramenta `literature_review/` v0.3 | Coleta Crossref/arXiv, dedup, fila de triagem, RIS/XLSX; 30 testes OK |
| Corpus bibliográfico | 3.016 candidatos (busca completa em 20/09 + atualização em 10/10); 0 triados. 1.828 têm VO/SLAM/localização no título |
| Módulo `smoke_emulation/` | Koschmieder + preenchimento de buracos + CLI por sequência; 16 testes |
| Fichamentos (Sprints 1–2) | 15 referências em `docs/leituras/` + tabela comparativa |
| Experimentos | `experiments/` pronto para a máquina do laboratório (Docker, matriz, métricas); não executado |
| Jira NATASHA | 5 épicos, 21 tarefas, 14 subtarefas; sprints 1–4 com datas já passadas e ainda “futuras” |

> Atualizado em 10/10/2026 (fim do dia): sprints 1–4 executadas no que não depende da GPU nem do dataset. Ver seção 5.

## 3. Primeiros passos (próximas 4 semanas)

1. **Fundamentos** — Scaramuzza & Fraundorfer (VO partes I e II); geometria epipolar,
   PnP e bundle adjustment. Fichamento em `docs/leituras/`.
2. **Artigos-núcleo** — ORB-SLAM2, TartanVO, DPVO, DROID-SLAM, QueensCAMP, SubT-MRS,
   Bujanca et al. (robustez), He et al. (DCP).
3. **Triagem do corpus** — 3.016 candidatos é inviável de triar um a um. Sugestão:
   (a) critérios de inclusão/exclusão escritos antes de começar; (b) pré-filtro
   documentado por palavras-chave no título; (c) triagem com `review.py review` começando
   pelos temas T4 (robustez), T5 (atmosférico) e T6 (datasets); (d) snowballing a partir
   dos artigos-núcleo.
4. **Dataset** — baixar o QueensCAMP, inspecionar formato (fator de escala da
   profundidade, registro RGB-D, ground truth Vicon, como as falhas são aplicadas).
5. **Spike de GPU** — testar cedo se DPVO/DROID-SLAM compilam na RTX 5070 Ti (ver 4.5).
6. **Fumaça** — rodar o protótipo em frames reais do QueensCAMP e comparar visualmente
   com frames de fumaça do SubT-MRS.

## 4. Sugestões e riscos identificados

### 4.1 Modalidade do sensor e alinhamento das trajetórias [discutir]
A proposta não fixa se a comparação será **monocular** ou **RGB-D**. TartanVO e DPVO são
monoculares (escala ambígua); ORB-SLAM2 pode rodar em RGB-D (escala métrica). Misturar
modalidades torna a comparação injusta e o critério “ATE RMSE < 0,3 m” só faz sentido
para métodos monoculares após alinhamento Sim(3) (`evo_ape ... -as`).
Sugestão: comparação principal **monocular para todos**, com alinhamento Sim(3) e relato
explícito do alinhamento; ORB-SLAM2 RGB-D como análise complementar.

### 4.2 Número real de execuções [discutir]
480 = 3 algoritmos × 16 sequências × 10 condições, **sem repetições**. Com 5 sementes
para métodos estocásticos, chega a 2.400. ORB-SLAM2 também não é determinístico
(multithread + RANSAC), então também precisa de repetições. O baseline com DCP adiciona
outra rodada sobre as condições de fumaça. Convém estimar o tempo de GPU por execução
no spike e ajustar o escopo (ex.: repetições só onde a variância for relevante).

### 4.3 Níveis de fumaça em cena interna [discutir]
Com V = 60/20/6 m (pensados para ambiente externo), a transmissão nas profundidades
típicas do QueensCAMP (1–5 m) é:

| nível | V (m) | t(1 m) | t(3 m) | t(5 m) |
|---|---|---|---|---|
| leve | 60 | 0,94 | 0,82 | 0,72 |
| moderada | 20 | 0,82 | 0,56 | 0,38 |
| densa | 6 | 0,52 | 0,14 | 0,04 |

(saída de `smoke_emulation/transmission_table.py`).

**Correção (nota técnica NATASHA-40):** a transmissão *média* numa sala (0,5–6 m) fica em
0,81 / 0,56 / 0,20. A fumaça leve é fraca, mas visível, e os três níveis cobrem bem o
intervalo. Recomendação: manter V = 60/20/6 m e relatar a transmissão média por sequência.
Ver `docs/nota_niveis_fumaca.md`.

### 4.4 Detalhes de implementação da emulação
- Buracos do sensor de profundidade (d = 0) viram “janelas” sem fumaça; o protótipo
  preenche com a profundidade máxima válida (provisório; trocar por inpainting).
- Confirmar o fator de escala da profundidade (ex.: 1000 ou 5000 por metro) e se a
  profundidade está registrada no referencial da câmera RGB.
- A luz atmosférica A (cor da fumaça) deve ser calibrada com o SubT-MRS, não só estimada.
- Fumaça homogênea e estática é consistente entre frames (bom para VO); fumaça
  heterogênea/animada fica como extensão futura.

### 4.5 Compatibilidade da RTX 5070 Ti (risco alto)
A RTX 5070 Ti é arquitetura Blackwell (sm_120): exige CUDA ≥ 12.8 e PyTorch compilado
com suporte a sm_120 — “CUDA 12.x” genérico não basta. DPVO e DROID-SLAM compilam
extensões CUDA próprias (ex.: lietorch), e o TartanVO usa código antigo de PyTorch;
qualquer um pode falhar na compilação. ORB-SLAM2 tem problemas conhecidos de build no
Ubuntu 22.04 (OpenCV 4, Pangolin, C++14). Sugestão: **containers Docker por algoritmo**
e spike de compatibilidade antes da Sprint de instalação.

### 4.6 Pequenas inconsistências no texto da proposta
Úteis de corrigir no relatório parcial:
- Fig. 3 atribui o modelo a He, Sun e Tang como **[18]**, mas [18] é TartanVO; o correto é **[16]**.
- Fig. 4 fala em “cinco etapas”; a metodologia tem **seis** (o dataset piloto ficou fora).
- A referência **[22] (INPE/BDQueimadas)** não é citada no texto; a frase sobre
  queimadas sazonais cita [8] (SubT-MRS) e provavelmente deveria citar [22].

### 4.7 Originalidade: trabalhos de 2026 [discutir — urgente]
O **SLAM Adversarial Lab** (IROS 2026) já implementa névoa por Koschmieder com β = 3,912/V
sobre a profundidade do dataset e avalia ORB-SLAM3 e DROID-SLAM. **"Failure or Drift?"**
(ECCV-W 2026) e **Kumar et al. (2026)** comparam VO/SLAM clássico e aprendido sob névoa ou
"dust haze". A originalidade precisa ser reposicionada (fumaça calibrada com fumaça real,
falhas de lente + fumaça, degradação relativa e gap de domínio, piloto amazônico). Também
vale avaliar o reuso do SAL. Ver `docs/trabalhos_relacionados.md`, seção 5.

### 4.8 Critério de aptidão e escala do TartanVO [discutir]
- No artigo do QueensCAMP, o ATE **original** do TartanVO fica entre 0,38 e 1,13 m: nenhuma
  sequência fica abaixo de 0,3 m. O critério absoluto da proposta reprova todos os métodos
  antes de qualquer degradação. Proposta de critério relativo em `docs/protocolo_experimental.md` §5.
- O TartanVO só tem escala com a **norma de cada passo vinda do ground truth** (código oficial).
  A avaliação calcula essa variante para todos os monoculares, para ninguém ser favorecido.

### 4.9 Cronograma no Jira [discutir]
As sprints 1–4 (jun–out/2026) ainda constam como futuras e nenhuma tarefa saiu de
“A fazer”. Vale replanejar as datas com o orientador a partir do início efetivo da bolsa.

## 5. Execução das Sprints 1–4 (10/10/2026)
| Tarefa | Entrega | Estado |
|---|---|---|
| NATASHA-6 / 27–32 | Fichamentos de fundamentos, ORB-SLAM2/3, DSO, TartanVO, DROID-SLAM, DPVO + tabela comparativa | entregue, aguarda revisão |
| NATASHA-7 / 33–37 | Surveys, Bujanca, QueensCAMP, SubT-MRS; critérios + pré-triagem (`screening.py`); Trabalhos Relacionados v0.1 | entregue; **triagem humana pendente** |
| NATASHA-8 / 38–40 | Koschmieder, DCP, Sakaridis, Xu, SAL; métricas; nota dos níveis de fumaça | entregue, aguarda revisão |
| NATASHA-24 | `docs/datasets.md` + `dataset.py download/inspect` | preparado; **download e inspeção na máquina do lab** |
| NATASHA-9 / 25 | `docs/ambiente.md`, Dockerfiles, `check_gpu.sh` | preparado; **execução na máquina do lab** |
| NATASHA-10 | wrappers + patches ORB-SLAM2, matriz, avaliação | preparado; **validação depende da GPU e dos dados** |
| NATASHA-11 | módulo de fumaça completo com CLI | entregue; falta rodar em dados reais |
| NATASHA-26 | `docs/protocolo_experimental.md` | rascunho para aprovação |
| NATASHA-23 | pauta com o orientador + `docs/analise_concorrentes_2026.md` | **depende da Natasha** |
| NATASHA-17 (adiantada) | DCP com guided filter + condições `dcp_*` no pipeline | implementado e testado; falta rodar em dados reais |
| NATASHA-19 (adiantada) | `stats_analysis.py`: Wilcoxon, Bonferroni, bootstrap e critério de robustez | implementado e testado com dados sintéticos |

## 6. Leituras complementares sugeridas

Verificar antes de citar:
- Sturm et al., *A benchmark for the evaluation of RGB-D SLAM systems*, IROS 2012 — define ATE/RPE.
- Zhang & Scaramuzza, *A Tutorial on Quantitative Trajectory Evaluation for Visual(-Inertial) Odometry*, IROS 2018 — alinhamentos SE(3)/Sim(3).
- Sakaridis, Dai & Van Gool, *Semantic Foggy Scene Understanding with Synthetic Data*, IJCV 2018 — névoa sintética via Koschmieder sobre profundidade (precedente direto da etapa 2).
- Wang et al., *TartanAir: A Dataset to Push the Limits of Visual SLAM*, IROS 2020 — domínio de treino do TartanVO.
- Xu et al., *Customizable Perturbation Synthesis for Robust SLAM Benchmarking*, 2024 — benchmark de perturbações para SLAM.

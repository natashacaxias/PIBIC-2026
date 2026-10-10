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
| Módulo `smoke_emulation/` | Protótipo do modelo de Koschmieder com 12 testes |
| Jira NATASHA | 5 épicos e 16 tarefas; sprints 1–4 com datas já passadas e ainda “futuras” |

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

(saída de `smoke_emulation/transmission_table.py`). A fumaça **leve** quase não altera a
imagem nessas distâncias. Opções: (a) manter V e relatar como limitação; (b) definir os
níveis pela **transmissão média da cena** ou pela queda de contraste; (c) reescalar V
para a geometria indoor. O importante é justificar e validar com os frames do SubT-MRS.

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

### 4.7 Cronograma no Jira [discutir]
As sprints 1–4 (jun–out/2026) ainda constam como futuras e nenhuma tarefa saiu de
“A fazer”. Vale replanejar as datas com o orientador a partir do início efetivo da bolsa.

## 5. Leituras complementares sugeridas

Verificar antes de citar:
- Sturm et al., *A benchmark for the evaluation of RGB-D SLAM systems*, IROS 2012 — define ATE/RPE.
- Zhang & Scaramuzza, *A Tutorial on Quantitative Trajectory Evaluation for Visual(-Inertial) Odometry*, IROS 2018 — alinhamentos SE(3)/Sim(3).
- Sakaridis, Dai & Van Gool, *Semantic Foggy Scene Understanding with Synthetic Data*, IJCV 2018 — névoa sintética via Koschmieder sobre profundidade (precedente direto da etapa 2).
- Wang et al., *TartanAir: A Dataset to Push the Limits of Visual SLAM*, IROS 2020 — domínio de treino do TartanVO.
- Xu et al., *Customizable Perturbation Synthesis for Robust SLAM Benchmarking*, 2024 — benchmark de perturbações para SLAM.

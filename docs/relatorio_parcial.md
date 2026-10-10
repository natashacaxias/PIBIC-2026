# Relatório Parcial PIBIC — rascunho v0.1

> Rascunho gerado em 10/10/2026 a partir dos documentos do repositório. **Antes de enviar:** conferir o modelo oficial da PROPESP/UFAM, preencher os campos [PREENCHER], revisar o texto e substituir os resultados preliminares pelos da máquina do laboratório quando houver. Os trechos marcados com [DISCUTIR] dependem do orientador (NATASHA-23).

## Identificação
- **Título:** Análise Comparativa de Métodos Clássicos e Baseados em Deep Learning para Odometria Visual em Cenários Desafiadores Representativos de Condições Amazônicas
- **Bolsista:** Natasha Araújo Caxias
- **Orientador(a):** [PREENCHER]
- **Projeto vinculado:** SAGRES-Pro (Edital Pró-Defesa V)
- **Período coberto:** [PREENCHER início] a [PREENCHER]

## 1. Introdução
A odometria visual (VO) estima o movimento de um robô a partir de imagens e é peça central da navegação autônoma dos drones, dirigíveis e robôs terrestres do projeto SAGRES-Pro. Seu funcionamento pressupõe iluminação suficiente, cena com textura e sobreposição entre quadros consecutivos (Scaramuzza & Fraundorfer, 2011). Na Amazônia, alta umidade, chuva, vegetação densa e a fumaça das queimadas sazonais violam essas hipóteses. Benchmarks clássicos como KITTI e EuRoC não contemplam degradações ópticas severas, e a garantia de robustez segue como um dos problemas abertos da área (Bujanca et al., 2021).

Este trabalho avalia comparativamente métodos clássicos (ORB-SLAM2) e baseados em aprendizado (TartanVO e DPVO) sob as falhas de câmera do dataset QueensCAMP (Bruno et al., 2024) e sob fumaça emulada fisicamente pelo modelo de espalhamento de Koschmieder, com validação por fumaça real (SubT-MRS) e um estudo de caso com dados coletados em Manaus.

## 2. Objetivos
**Geral:** avaliar comparativamente a robustez de métodos clássicos e baseados em deep learning para odometria visual sob condições adversas representativas de ambientes amazônicos.

**Específicos:** (i) reproduzir os resultados do QueensCAMP com ORB-SLAM2 e TartanVO; (ii) estender a avaliação a um método recente (DPVO); (iii) emular fumaça por espalhamento atmosférico; (iv) analisar o impacto de cada degradação; (v) produzir e submeter um artigo.

## 3. Fundamentação e trabalhos relacionados
*(versão completa: `docs/trabalhos_relacionados.md`; fichamentos: `docs/leituras/`)*

- **Métodos.** Os métodos baseados em features (ORB-SLAM2/3) usam *bundle adjustment* sobre pontos ORB e RANSAC; os diretos (DSO) minimizam o erro fotométrico. Entre os aprendidos, o TartanVO estima a pose a partir de fluxo óptico, sem back-end, e o DROID-SLAM e o DPVO combinam atualização recorrente com BA diferenciável. Os três aprendidos foram treinados só no TartanAir, que é sintético.
- **Robustez.** Bujanca et al. (2021) avaliaram iluminação, movimento e dinâmica e deixaram clima e visibilidade como lacuna. Trabalhos de 2026 começaram a ocupar essa lacuna:
  - o SLAM Adversarial Lab gera névoa por Koschmieder;
  - Thomas et al. ("Failure or Drift?") comparam ORB-SLAM2, DPVO e DROID-SLAM sob corrupções sintéticas e reais;
  - Kumar et al. avaliam *dust haze*.
- **Contribuição deste trabalho** em relação a eles [DISCUTIR]:
  - fumaça calibrada e validada com fumaça real;
  - ambiente interno real com profundidade medida, combinando falhas de lente e fumaça;
  - TartanVO com tratamento justo da escala;
  - repetições com sementes e testes estatísticos pareados;
  - análise de degradação relativa e de gap de domínio;
  - dados amazônicos.
  
  Detalhes em `docs/analise_concorrentes_2026.md`.

## 4. Metodologia
*(versão completa: `docs/protocolo_experimental.md`)*

- **Dados.** QueensCAMP: 16 sequências RGB-D internas (RealSense D435, ground truth Vicon) com 6 falhas de lente/exposição.
- **Fumaça.** Fumaça homogênea I = J·t + A(1 − t), com t = exp(−β·d) e β = 3,912/V, para V = 60, 20 e 6 m. Os buracos de profundidade são preenchidos por dilatação. Os três níveis dão transmissão média de ~0,81, 0,56 e 0,20 na faixa de profundidade da sala (`docs/nota_niveis_fumaca.md`).
- **Baseline de pré-processamento.** Dark Channel Prior com guided filter, com A estimado por sequência.
- **Métodos e configuração.**
  - ORB-SLAM2 monocular e RGB-D, com loop closure desligado por patch;
  - TartanVO;
  - DPVO com stride 1.
  
  Cada um roda em container Docker com versões fixadas, para CUDA 12.8/RTX 5070 Ti; são 5 repetições com sementes (2 no TartanVO, que é determinístico). Total: 2.720 execuções.
- **Métricas.**
  - taxa de rastreamento;
  - ATE (Sim(3) nos monoculares, SE(3) no RGB-D), mais uma variante com escala por passo do ground truth;
  - RPE com Δ = 1 s;
  - latência e memória de GPU.
- **Análise.**
  - degradação relativa à condição original de cada método;
  - Wilcoxon pareado por sequência com correção de Bonferroni;
  - IC 95% por bootstrap;
  - critério relativo de robustez [DISCUTIR].

## 5. Atividades realizadas
| Atividade | Situação |
|---|---|
| Revisão da literatura: 15 referências fichadas, tabela comparativa dos métodos | concluída |
| Coleta bibliográfica automatizada: 3.016 candidatos; pré-triagem por regras (674 / 1.297 / 1.045) | concluída; triagem humana em andamento |
| Estudo de Koschmieder, DCP, métricas de trajetória e de imagem | concluído |
| Módulo de emulação de fumaça, DCP e validação por métricas de imagem | implementado e testado (dados sintéticos) |
| Pipeline experimental (Docker, matriz de execuções, avaliação, estatística, figuras) | implementado e testado sem GPU |
| Configuração da máquina com RTX 5070 Ti e execução dos experimentos | [PREENCHER] |

## 6. Resultados preliminares
1. **Reprodução do QueensCAMP (pelo artigo e pelo código).** O ATE do TartanVO na condição original já fica entre 0,38 e 1,13 m. Por isso o critério absoluto previsto na proposta (ATE < 0,3 m) é inadequado e foi substituído por um critério relativo [DISCUTIR].
2. **Escala do TartanVO.** O código oficial usa a norma de cada passo do ground truth. A avaliação passou a aplicar a mesma ajuda a todos os métodos monoculares.
3. **Níveis de fumaça.** A transmissão média em cena interna cobre o intervalo de ~0,8 a ~0,2 com os níveis da proposta, que foram mantidos.
4. **DCP em cena interna.** Sem região opaca, a estimativa da luz atmosférica é enviesada pela cor da cena, o que gera dominante de cor (verificado nos testes).
5. [PREENCHER com os primeiros resultados da máquina do laboratório: reprodução da sequência 09 e piloto do DPVO.]

## 7. Dificuldades e ajustes
- **Cronograma.** As sprints 1–4 foram concluídas no que não dependia de hardware. A execução depende da configuração da máquina com GPU Blackwell (sm_120), que exige CUDA ≥ 12.8 e a portabilidade de código antigo (TartanVO).
- **Originalidade.** Trabalhos publicados em 2026 exigiram reposicionar a contribuição (seção 3).
- **Recursos de computação.** A estimativa é de ~13 h de GPU e ~53 h de CPU para a matriz principal.

## 8. Próximas etapas
| Período | Etapa |
|---|---|
| [PREENCHER] | Ambiente e imagens Docker na máquina do laboratório; reprodução do QueensCAMP (seq. 09) |
| [PREENCHER] | Geração da fumaça; validação contra SubT-MRS; coleta do piloto em Manaus |
| [PREENCHER] | Matriz completa + baseline DCP; métricas e estatística |
| [PREENCHER] | Redação do artigo e do relatório final |

## Referências
Usar a lista da proposta, acrescida de: Sturm et al. (IROS 2012); Zhang & Scaramuzza (IROS 2018); Sakaridis, Dai & Van Gool (IJCV 2018); Xu et al. (arXiv:2402.08125, 2024); Hefny, Dantu & Ko (IROS 2026, arXiv:2603.17165); Thomas, Agnihotri & Keuper (NeuSLAM@ECCV 2026, arXiv:2608.30690); Kumar, Deepak & Kumar (arXiv:2605.03678, 2026); He, Sun & Tang (TPAMI 2013, guided filter).

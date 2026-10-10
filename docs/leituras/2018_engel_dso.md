# Direct Sparse Odometry (DSO)

- **Referência:** J. Engel, V. Koltun, D. Cremers. IEEE TPAMI, 40(3), 2018. arXiv:1607.02565
- **Jira:** NATASHA-29 (ref. [25])
- **Tema:** T2 clássico (direto)
- **Lido em:** 2026-10-10 (texto completo, ar5iv)

## Problema e ideia central
VO monocular **direta** (minimiza o erro fotométrico nas intensidades dos pixels, sem descritores) e **esparsa** (~2000 pontos ativos amostrados de forma uniforme, inclusive em bordas e gradientes fracos). Otimiza conjuntamente poses, intrínsecos e profundidades inversas.

## Método
- **Calibração fotométrica:** modela tempo de exposição, vinhetamento e função de resposta da câmera. Sem calibração há transferência afim de brilho por frame. Os autores mostram que remover a calibração piora a precisão e a robustez; assumir brilho constante é o pior caso.
- **Janela deslizante:** Gauss-Newton sobre N_f = 7 keyframes; marginalização por complemento de Schur.
- Sem loop closure nem relocalização (VO pura).

## Avaliação
- TUM monoVO (50 seq.), EuRoC (usado como monocular, ATE após **Sim(3)**) e ICL-NUIM. Os resultados são **curvas de erro cumulativo**, que mostram precisão e robustez (quantas sequências não falham) ao mesmo tempo.
- Cada sequência roda para frente e para trás, várias vezes.
- Supera o ORB-SLAM em TUM monoVO e ICL-NUIM. No EuRoC o ORB-SLAM é mais preciso, mas menos robusto.

## Robustez e limitações
- **Mais robusto que o ORB-SLAM a ruído fotométrico (blur)**.
- **Muito menos robusto a ruído geométrico**: rolling shutter, intrínsecos ruins, distorção.
- Inicialização monocular frágil com movimento rápido.

## Relevância para este PIBIC
- É o representante **direto** dos clássicos. Seria interessante porque fumaça e névoa alteram o brilho de forma dependente da profundidade, o que viola o modelo fotométrico afim global do DSO. A hipótese é que o DSO sofra mais com fumaça que métodos de features.
- **Atenção:** a câmera RGB da RealSense D435 usada no QueensCAMP é *rolling shutter* (confirmar na ficha técnica). O DSO é sensível a isso e não há calibração fotométrica do QueensCAMP. Portanto o DSO deve entrar **só como extensão** e com essa ressalva.
- A **curva de erro cumulativo** é uma boa visualização para o artigo, porque combina precisão e taxa de falhas.

## Reprodutibilidade
- Código: https://github.com/JakobEngel/dso (GPLv3), C++, sem GPU. Aceita pastas de imagens com `calib.txt`; a calibração fotométrica é opcional.

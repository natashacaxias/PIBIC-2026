# TartanVO: A Generalizable Learning-based VO

- **Referência:** W. Wang, Y. Hu, S. Scherer. CoRL 2020. arXiv:2011.00359
- **Jira:** NATASHA-30 (ref. [18])
- **Tema:** T3 deep learning
- **Lido em:** 2026-10-10 (texto completo, ar5iv). TartanAir (Wang et al., IROS 2020, arXiv:2003.14338): só o resumo.

## Problema e ideia central
VO aprendida que **generaliza para dados reais sem fine-tuning**, treinada só no TartanAir (sintético, mais de 400 mil frames, "várias condições de clima", luz variável e objetos dinâmicos).

## Método
- **Duas etapas:**
  1. PWC-Net estima o fluxo óptico entre dois frames.
  2. Uma rede de pose (ResNet50 sem batch norm) prevê translação e rotação a partir do fluxo em 1/4 da resolução (160×112 para entrada 640×448).
- **Perda até-escala:** a translação é normalizada, então a rede aprende só a direção.
- **Camada de intrínsecos:** dois canais (X−o_x)/f_x e (Y−o_y)/f_y concatenados ao fluxo. Ela generaliza para outras câmeras.
- **Aumento de dados:** crop-resize que simula campos de visão de 40° a 90°.
- Inferência ≈ 40 ms por par (GTX 1080). Frame a frame, **sem backend** (sem BA nem loop).

## Avaliação
- **A escala da translação é alinhada ao ground truth** na avaliação.
- EuRoC (ATE): 0,45–1,04 m.
- KITTI: deriva de 5,48% de translação e 3,05°/100 m.

## Limitações
- Sem otimização multi-frame, a deriva se acumula.
- Escala não observável (monocular).
- Os autores citam VIO, estéreo e multi-frame como trabalho futuro.

## Relevância para este PIBIC
- É um dos dois métodos do QueensCAMP. **ATE original de 0,38–1,13 m** nas 16 sequências: nenhuma fica abaixo de 0,3 m. Por isso **o critério de aptidão da proposta (ATE < 0,3 m) é inatingível para o TartanVO mesmo sem degradação**. Ver `docs/protocolo_experimental.md`.
- No QueensCAMP ele é quase insensível a sub/superexposição (os ATEs mudam ≤ 0,07 m), mas sensível a lente quebrada, molhada, condensação e sujeira.
- **Gap de domínio:** o treino é sintético e com "clima variado". Não confirmei se o TartanAir tem névoa ou fumaça explícitas; vale verificar no site do dataset, porque isso influencia a interpretação da robustez à fumaça.

## Reprodutibilidade
- Código: https://github.com/castacks/tartanvo (pesos pré-treinados disponíveis).
- **Risco:** o código foi feito para PyTorch 1.x e Python 3.6–3.8 (CUDA 10/11), mas a RTX 5070 Ti exige PyTorch ≥ 2.7 com CUDA 12.8. É provável que precise de pequenos ajustes (ver `experiments/algorithms/tartanvo/`).

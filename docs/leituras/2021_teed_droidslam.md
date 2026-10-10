# DROID-SLAM: Deep Visual SLAM for Monocular, Stereo, and RGB-D Cameras

- **Referência:** Z. Teed, J. Deng. NeurIPS 2021. arXiv:2108.10869
- **Jira:** NATASHA-31 (ref. [20])
- **Tema:** T3 deep learning
- **Lido em:** 2026-10-10 (texto completo, ar5iv)

## Problema e ideia central
SLAM aprendido que **refina iterativamente poses e profundidade densa** sobre um grafo de frames, por meio de uma camada diferenciável de **Dense Bundle Adjustment (DBA)**.

## Método
- **Encoders:** de features e de contexto, em 1/8 da resolução; pirâmide de correlação para cada aresta do grafo.
- **Operador de atualização:** ConvGRU que prevê revisões de fluxo e pesos de confiança.
- **DBA:** Gauss-Newton com complemento de Schur. Converte as revisões em atualizações de pose e profundidade.
- **Frontend:** keyframes + BA local. **Backend:** BA global + arestas de loop.
- **Treinado só em vídeo monocular do TartanAir.** O mesmo modelo roda em estéreo e RGB-D sem retreino.

## Avaliação (ATE)
- TartanAir monocular: média 0,24 (TartanVO: 1,92).
- EuRoC monocular: 2,2 cm.
- TUM-RGBD: 3,8 cm.
- ETH3D RGB-D: 1º lugar, 30 de 32 sequências rastreadas.

## Hardware e limitações
- O **frontend cabe em 8 GB** de GPU; o backend usa mais memória. EuRoC, TartanAir e ETH3D pedem **GPU de 24 GB**.
- Tempo real com 2× RTX 3090.
- A principal limitação declarada é **memória e custo computacional**.

## Relevância para este PIBIC
- **Alternativa ao DPVO.** Na RTX 5070 Ti (16 GB), rodar o SLAM completo com backend global provavelmente estoura a memória em sequências longas. Opções: rodar só o frontend ("DROID-VO", que também é mais justo como VO pura) ou limitar o buffer de frames.
- Como o DROID-SLAM tem loop closure, deve ser comparado como **VO (sem backend global)** para manter a comparação justa com TartanVO e DPVO.

## Reprodutibilidade
- Código: https://github.com/princeton-vl/DROID-SLAM (BSD-3). Compila extensões CUDA próprias (`lietorch`, `droid_backends`). **Risco de compilação em sm_120**: verificar no spike (NATASHA-25).

# ORB-SLAM2: an Open-Source SLAM System for Monocular, Stereo and RGB-D Cameras

- **Referência:** R. Mur-Artal, J. D. Tardós. IEEE T-RO, 33(5), 2017. arXiv:1610.06475
- **Jira:** NATASHA-28 (ref. [17])
- **Tema:** T2 clássico (baseado em features)
- **Lido em:** 2026-10-10 (texto completo, ar5iv)

## Problema e ideia central
SLAM completo em CPU e em tempo real para câmera monocular, estéreo e RGB-D, com loop closure, relocalização e reuso de mapa. A base é *bundle adjustment* sobre features ORB.

## Método
- **Três threads principais + uma extra:**
  - **Tracking:** localiza cada frame casando ORB com o mapa local (BA só de movimento) e decide quando inserir keyframes.
  - **Local Mapping:** BA local sobre keyframes covisíveis.
  - **Loop Closing:** detecção com DBoW2 + otimização de pose-graph (*essential graph*).
  - **Full BA:** thread disparada após o loop; é abortada se surgir um novo loop.
- **RGB-D:** a profundidade de cada ORB vira uma coordenada "direita virtual" u_R = u_L − f_x·b/d, com b ≈ 8 cm para Kinect/Xtion. Pontos são **"próximos"** se d < 40·b. Pontos próximos dão escala, translação e rotação com um único frame; pontos distantes dão principalmente rotação.
- **Modo localização:** desliga Local Mapping e Loop Closing; só faz tracking. **Não existe flag para desligar apenas o loop closing.**

## Avaliação
- Métrica: RMSE de translação absoluta (ATE). **5 execuções por sequência, mediana reportada** (i7-4790, 16 GB).
- TUM RGB-D: fr1/desk 0,016 m; fr2/xyz 0,004 m; fr3/office 0,010 m.
- EuRoC estéreo: 0,018–0,119 m; falha em V2_03 (*motion blur*).
- KITTI estéreo: erro relativo < 1% em geral.

## Robustez e limitações
- Monocular sofre deriva de escala e falha em rotação pura.
- Perde rastreamento com *motion blur* severo (V2_03).
- Mapa esparso, sem fusão densa.

## Relevância para este PIBIC
- **Baseline clássico da proposta.** No QueensCAMP, os autores rodaram **ORB-SLAM2 RGB-D** (ver `2024_bruno_queenscamp.md`).
- **Desligar o loop closure exige patch no código**, por exemplo não iniciar a thread `LoopClosing` em `System.cc` ou não enviar keyframes para ela a partir do `LocalMapping`. O patch está documentado em `experiments/algorithms/orbslam2/`.
- **O ORB-SLAM2 também é não determinístico** (RANSAC + threads), e os próprios autores usam 5 execuções com mediana. A proposta deve repetir as execuções também para ele.
- Bujanca et al. (2021) relatam **segfault em mais de 10% das execuções** do ORB-SLAM2/3. O runner precisa tratar crashes e registrá-los como falha.

## Reprodutibilidade
- Código: https://github.com/raulmur/ORB_SLAM2 (GPLv3, sem manutenção desde ~2017).
- Dependências: Pangolin, OpenCV (o original usa 2.4/3.x), Eigen3, DBoW2 e g2o embutidos. Há problemas conhecidos de compilação com OpenCV 4 / C++14 no Ubuntu 22.04 → usar **Docker com Ubuntu 18.04 + OpenCV 3.2**.
- Pesos/vocabulário: `ORBvoc.txt` (incluso).

# SubT-MRS Dataset: Pushing SLAM Towards All-weather Environments

- **Referência:** S. Zhao et al. (CMU AirLab). CVPR 2024. arXiv:2307.07607
- **Jira:** NATASHA-35 (ref. [8])
- **Tema:** T6 datasets
- **Lido em:** 2026-10-10 (texto completo, HTML)

## Dataset
- **Sensores:** 4 câmeras **RGB fisheye** Leopard Imaging; térmica FLIR Boson; LiDAR Velodyne Puck; IMU Epson M-G365; Jetson AGX Xavier. Sincronização por PPS (< 3 ms). A resolução das câmeras não aparece no artigo.
- **Plataformas:** aéreas, com pernas e com rodas; mais de 30 cenas (túneis, cavernas, corredores, áreas externas).
- **Ground truth:** registro dos scans LiDAR num mapa FARO + fusão com VO/LIO/IMU. O artigo traz duas precisões conflitantes: ±2 mm no texto principal e 10 cm no apêndice.
- **Degradações visuais:** pouca luz, superexposição, lanterna, **fumaça**, noite externa e neve.
- **Sequência com fumaça:** **"Smoke Room"** (carrinho RC, 2 m/s, 104,84 m; fisheye + térmica + IMU, **sem LiDAR**). A Fig. 12 compara features RGB × térmicas sob fumaça.
- **Site:** https://superodometry.com/datasets. O formato de download e a licença não estão no artigo; verificar no site.

## Implicações para o PIBIC
- **Fonte de fumaça real** para validar a emulação (NATASHA-12): usar frames RGB da "Smoke Room".
- **Atenção:**
  - As câmeras são **fisheye**; para comparar estatísticas de imagem com o QueensCAMP (pinhole), retificar ou recortar o centro.
  - **Não existe a mesma cena sem fumaça**, então o SSIM entre frames reais e sintéticos **não é definido**: o SSIM exige uma imagem de referência alinhada pixel a pixel. Para comparar real × sintético, usar métricas **sem referência** (BRISQUE, contraste RMS, estatística do dark channel) e comparar distribuições. Ver `metricas_trajetoria_e_imagem.md`.
  - Os frames de fumaça real podem calibrar a cor da fumaça (luz atmosférica A) com o estimador do DCP.
- Kumar et al. (2026, arXiv:2605.03678) já usaram SubT-MRS para avaliar DPVO, DROID-SLAM e ORB-SLAM3 sob "dust haze". Ver `docs/trabalhos_relacionados.md`.

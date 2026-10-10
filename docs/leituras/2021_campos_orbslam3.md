# ORB-SLAM3: An Accurate Open-Source Library for Visual, Visual-Inertial and Multi-Map SLAM

- **Referência:** C. Campos, R. Elvira, J. J. Gómez Rodríguez, J. M. M. Montiel, J. D. Tardós. IEEE T-RO, 37(6), 2021. arXiv:2007.11898
- **Jira:** NATASHA-28 (ref. [26])
- **Tema:** T2 clássico
- **Lido em:** 2026-10-10 (ar5iv, ~93% do texto)

## Contribuições
- **VI-SLAM com inicialização MAP do IMU:** escala com ~5% de erro em 2 s, ~1% em 15 s.
- **Atlas:** vários mapas desconectados, com fusão quando há reconhecimento de lugar. Isso permite **sobreviver a perdas de rastreamento**: um mapa novo começa e depois é fundido.
- **Reconhecimento de lugar com maior recall:** verificação geométrica + consistência com 3 keyframes covisíveis.
- **Modelo de câmera abstrato:** pinhole e Kannala-Brandt (fisheye); estéreo não retificado.

## Avaliação
- EuRoC: estéreo-inercial com ATE médio de 0,035 m; monocular 0,041 m; estéreo 0,084 m.
- TUM-VI: estéreo-inercial com 0,009 m nas salas.

## Limitações declaradas
- Ambientes com pouca textura são o principal caso de falha.
- Inicialização do IMU difícil com movimento lento.
- Pontos muito distantes (céu) causam deriva em cenas externas.

## Relevância para este PIBIC
- **Extensão opcional** da proposta.
- O **Atlas muda a semântica de "perda de rastreamento"**: o sistema reinicia um mapa em vez de parar. Se for incluído, a taxa de rastreamento e o ATE precisam considerar os múltiplos mapas (só o maior? todos alinhados?). Isso tem que ser decidido no protocolo.
- Bujanca et al. (2021) o apontam como o sistema com **melhor equilíbrio de robustez** entre os avaliados (iluminação, dinâmica, operação longa).
- O QueensCAMP não tem IMU utilizável nas sequências processadas, então seria usado só o modo visual (mono ou RGB-D).

## Reprodutibilidade
- Código: https://github.com/UZ-SLAMLab/ORB_SLAM3 (GPLv3). Compila com OpenCV 4 (mais fácil que o ORB-SLAM2 no Ubuntu 22.04).

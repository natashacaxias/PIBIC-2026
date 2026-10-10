# Datasets

Jira: NATASHA-24. Levantado em 10/10/2026 a partir dos artigos, do site e do código. **Nada foi baixado ainda**: o download e a inspeção acontecem na máquina do laboratório (`experiments/scripts/01_download_queenscamp.sh`).

## QueensCAMP
- **Site:** https://larocs.github.io/queenscamp-dataset · **Código:** https://github.com/larocs/queenscamp-dataset (MIT) · **Artigo:** arXiv:2410.12520 (ICAR 2025)
- **Hospedagem:** Google Drive, um arquivo por sequência.

| Seq | Full (GB) | Bag (GB) | Duração (s) | Imagens | Dinâmica | Pouca luz |
|---|---|---|---|---|---|---|
| 01 | 6,0 | 0,5 | 119,6 | 1732 | ✓ | |
| 02 | 8,1 | 0,7 | 166,1 | 2449 | | |
| 03 | 6,9 | 0,6 | 139,6 | 2029 | | |
| 04 | 6,9 | 0,6 | 140,0 | 2053 | ✓ | |
| 05 | 9,2 | 0,7 | 184,7 | 2689 | ✓ | |
| 06 | 9,0 | 0,7 | 183,6 | 2677 | ✓ | |
| 07 | 7,7 | 0,6 | 158,7 | 2309 | ✓ | |
| 08 | 5,2 | 0,4 | 116,4 | 1705 | | |
| 09 | 4,2 | 0,4 | 87,1 | 1284 | | |
| 10 | 5,7 | 0,5 | 117,9 | 1743 | | |
| 11 | 4,7 | 0,4 | 97,1 | 1437 | | |
| 12 | 4,6 | 0,4 | 92,7 | 1372 | | |
| 13 | 4,7 | 0,4 | 94,5 | 1403 | | |
| 14 | 3,4 | 0,4 | 79,0 | 831 | | ✓ |
| 15 | 6,4 | 0,6 | 119,4 | 1608 | | ✓ |
| 16 | 4,2 | 0,4 | 83,7 | 1202 | | ✓ |
| **Total** | **~97** | **~8** | | 28.523 | | |

- **Full Sequence:** imagens + profundidade + ground truth **já com as 6 falhas**. **Bag:** rosbag bruto, que precisa de `convert_bag_to_files.py` (ROS 1, `rosbag`, `cv_bridge`).
- **Recomendação:** usar **Full Sequence** (dispensa ROS). São ~97 GB, então conferir o espaço em disco da estação.
- **Formato esperado** (pelo código de conversão): `images/0000.png…` (RGB 640×480 depois do redimensionamento), `depths/0000.png…` (uint16 alinhado ao RGB), arquivo de timestamps `id t` e trajetória TUM.

### A confirmar na primeira inspeção (checklist)
- [ ] Estrutura de pastas e nomes reais dentro do Full Sequence.
- [ ] **Escala da profundidade:** esperada em mm (1000/m, padrão RealSense). Conferir a mediana de um frame: deve ficar entre 1 e 5 m numa sala de 5 × 7,5 m.
- [ ] Intrínsecos após o redimensionamento para 640×480 (arquivos "Camera info" RGB e Depth no site).
- [ ] Fração de buracos (profundidade = 0) por frame.
- [ ] Alinhamento entre os timestamps das imagens e do ground truth.
- [ ] Nomes das pastas de cada falha.

## SubT-MRS (apenas para validar a fumaça)
- **Site:** https://superodometry.com/datasets · **Artigo:** CVPR 2024, arXiv:2307.07607
- **Sequência de interesse:** **Smoke Room** (RC car, 104,84 m; fisheye RGB + térmica + IMU).
- **Uso:** extrair ~200 frames RGB com fumaça real, retificados ou recortados no centro, para comparar estatísticas com a fumaça sintética e calibrar a luz atmosférica A.
- **A confirmar:** formato (rosbag?), tamanho, licença e calibração das fisheye.

## TartanAir (referência de domínio de treino)
- Não é necessário baixar. Verificar na documentação se há ambientes com névoa ou fumaça (argumento de gap de domínio).

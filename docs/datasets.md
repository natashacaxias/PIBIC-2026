# Datasets

Jira: NATASHA-24. Levantado em 10/10/2026 a partir dos artigos, do site e do código. As 16 sequências do QueensCAMP (*Full*) foram baixadas, verificadas e extraídas em 29/10/2026 no servidor do laboratório (seção "Registro local"). O SubT-MRS (só a sequência de fumaça, 9,25 GB) foi baixado em 31/10/2026 (seção abaixo).

## QueensCAMP
- **Site:** https://larocs.github.io/queenscamp-dataset · **Código:** https://github.com/larocs/queenscamp-dataset (MIT) · **Artigo:** arXiv:2410.12520 (ICAR 2025)
- **Hospedagem:** Google Drive, um arquivo por sequência.

| Seq | Full (GiB) | Bag (GB) | Duração (s) | Imagens | Dinâmica | Pouca luz |
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
- **Recomendação:** usar **Full Sequence** (dispensa ROS). São ~97 GiB, então conferir o espaço em disco da estação.
- **Formato real** (conferido nas 16 sequências): `NN/images/0000.png…` (RGB 640×480), `NN/depth/0000.png…` (uint16 alinhado ao RGB), uma pasta por falha (`underexposure`, `overexposure`, `breakage`, `wet`, `condensation`, `dirt`; `breakage`, `condensation`, `dirt` e `wet` com 4 canais RGBA), `times.txt` (`id t`) e `traj.txt` (TUM).

### Checklist da primeira inspeção
- [x] Estrutura de pastas e nomes reais dentro do Full Sequence (acima; as 16 têm as 8 pastas de imagens, sem aviso).
- [x] **Escala da profundidade:** milímetros (`depth_scale = 1000`). Na seq. 09 a mediana dos pixels válidos é 0,607 m; a prova é o ORB-SLAM2 RGB-D reproduzir o ATE do artigo (0,151 m com Sim3 contra 0,15 m).
- [ ] Intrínsecos: `rgb_camera_info.txt` e `depth_camera_info.txt` do site já estão em 640×480 e foram para o `config/experiment.json`. Falta conferir `fx` = 465,6 e `fy` = 620,9 (razão 4/3) com a documentação do dataset, por causa do viés de escala de 13% do RGB-D.
- [ ] Fração de buracos (profundidade = 0): medida só na seq. 09 (49%).
- [x] Alinhamento entre os timestamps das imagens e do ground truth: `times.txt` e `traj.txt` têm os mesmos timestamps (diferença máxima 0 s) nas 16 sequências.
- [x] Nomes das pastas de cada falha (acima).

### Registro local (29/10/2026)
- **Zips:** `/data/queenscamp_raw/NN.zip` (16 arquivos, 96,8 GiB). O sha256, o tamanho e a data de cada download estão em `/data/queenscamp_raw/downloads.json`. O Drive não publica hash, então ele registra o que foi baixado e não é comparado com a origem. Os tamanhos reais conferem com a coluna *Full* acima.
- **Extraído:** `/data/queenscamp/NN` (104 GiB), sem aviso de layout; `/data/queenscamp_raw/extract_report.json` guarda o resultado de cada sequência.
- **Verificação antes de extrair:** caminhos seguros, espaço em disco, CRC de todos os membros e layout esperado; extração numa pasta temporária seguida de rename.
- **Dados fora do git.** Os zips podem ser apagados depois que a matriz terminar, se faltar espaço: o `dataset.py download` baixa de novo.

## SubT-MRS (apenas para validar a fumaça)
- **Site:** https://superodometry.com/datasets · **Artigo:** CVPR 2024, arXiv:2307.07607 · **Licença:** não declarada na página (por isso os quadros reais **não entram no repositório**, só métricas e o painel em `results/`, fora do git).
- **Onde está:** a entrada "SmokeRoom" fica em "Sensor Fusion Challenge extension" (RGB, térmica e IMU, "visual degradation"). Os dados são pastas do Google Drive com um zip por sequência, nas versões *rosbag* e *extracted*. Baixado em 31/10/2026 só o zip *extracted* **`SubT_MRS_Hawkins_Smoke_Handheld.zip`**, **9,25 GB** (Drive id `140UJgOCa-2itHUZQfwOK1zISD8XRGw51`), em `/data/subtmrs_raw/` (fora do git). A página lista a plataforma como RC7, e o nome do arquivo diz *Handheld*; as imagens mostram uma plataforma no rodapé do quadro. Isso não afeta a validação da fumaça.
- **Conteúdo** (`SmokeRoom_Folder/`): `cam_0/` com **10.290 PNG RGB de 640×480** e `timestamps.txt`, `thermal/` com 12.510 PNG, `imu/imu_data.csv`. As outras três câmeras RGB não estão no zip. Extraídos só `cam_0`, a térmica e a IMU não foram usadas. Intrínsecos e extrínsecos são arquivos separados do Drive (não baixados).
- **Segmentos da `cam_0`** (índice do quadro; medidos pelo contraste e pelos pontos ORB): 0–2400 cena noturna com outra exposição; **2700–5300 limpo**; **5400–9000 fumaça** (a mais densa em 6300–8100); 9000 em diante limpo, com névoa residual no começo. A mesma cena (galpão) aparece limpa e com névoa, mas sem alinhamento quadro a quadro (carrinho em movimento), então **não existe SSIM com referência**.
- **Resultado da validação:** `docs/nota_niveis_fumaca.md`, seção "Validação contra fumaça real".

## TartanAir (referência de domínio de treino)
- Não é necessário baixar. Verificar na documentação se há ambientes com névoa ou fumaça (argumento de gap de domínio).

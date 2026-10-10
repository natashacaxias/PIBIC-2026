# QueensCAMP: an RGB-D dataset for robust Visual SLAM

- **Referência:** H. M. S. Bruno, E. L. Colombini, S. N. Givigi Jr. arXiv:2410.12520 (2024); ICAR 2025.
- **Jira:** NATASHA-34 (ref. [9])
- **Tema:** T6 datasets
- **Lido em:** 2026-10-10 (artigo em HTML + código em github.com/larocs/queenscamp-dataset, licença MIT)

## Dataset
- **Captura:** Intel RealSense D435 num hexacóptero Tarot 680 Pro **carregado à mão**; ground truth Vicon a 30 Hz.
- **Ambiente:** indoor, **5 m × 7,5 m × 3 m**, com objetos espalhados.
- **Volume:** 16 sequências (78–185 s; 831–2689 imagens) a ~15 fps. As 01 e 04–07 têm pessoas em movimento; as 14–16 têm luzes apagadas.
- **Imagens processadas:** a RGB 1920×1080 é **reduzida para 640×480** e a profundidade (640×480) é reprojetada no referencial RGB (`depth_utils.align_images`). Essa reprojeção deixa buracos e PNG uint16 em unidades do sensor (provavelmente **mm, escala 1000**, que é o padrão da RealSense; **confirmar**).
- **Ground truth:** formato **TUM** (`t tx ty tz qx qy qz qw`), relativo à primeira pose.

## Falhas (script `insert_failures.py`)
| Falha | Implementação |
|---|---|
| Subexposição | correção gama com γ = 2 |
| Superexposição | correção gama com γ = 0,5 |
| Quebra de lente / lente molhada / condensação / sujeira | sobreposição de **um único template PNG** por tipo, com α = 1,0 / 0,75 / 1,0 / 0,65 |
| Blur | gaussiano 35×35; **existe no script, mas não está no artigo** |

As falhas são **estáticas** (o mesmo template em todos os frames) e determinísticas, porque há um template por pasta.

## Avaliação dos autores
- **ORB-SLAM2 em modo RGB-D** e TartanVO (modalidade não declarada; o TartanVO é monocular).
- **Métrica:** `evaluate.py` com evo, `align=True` e `correct_scale` **opcional (padrão desligado)**. RPE com Δ = 1 frame. O texto define ATE como média, mas o script grava o **RMSE**.
- **Regra de rastreamento:** só reportam o ORB-SLAM2 se ≥ 50% da trajetória foi rastreada.

### ATE (m) nas condições originais
| Seq | 01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | 09 | 10 | 11 | 12 | 13 | 14 | 15 | 16 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ORB-SLAM2 | 0,15 | 0,24 | 0,10 | 0,66 | 0,97 | 0,53 | 0,63 | – | 0,15 | – | 0,16 | 0,24 | 0,27 | 0,52 | 0,56 | 0,29 |
| TartanVO | 0,87 | 0,38 | 0,90 | 1,13 | 0,80 | 0,63 | 0,63 | 0,70 | 0,45 | 0,57 | 0,55 | 0,75 | 0,61 | 0,94 | 0,97 | 0,63 |

## Achados principais
- O ORB-SLAM2 perde rastreamento na maior parte dos casos de sujeira e em metade dos de condensação; com lente molhada continua rastreando, mas com erro alto.
- O TartanVO é quase imune a sub/superexposição e degrada com quebra, molhado, condensação e sujeira.

## Implicações para o PIBIC
1. **Critério "ATE < 0,3 m em ≥ 75% das sequências" (proposta, etapa 5):** sem nenhuma degradação, o ORB-SLAM2 atinge isso em 8 de 16 sequências (50%) e o TartanVO em **0 de 16**. O critério absoluto declararia todos os métodos "não aptos" já na condição original. Ver a proposta de critério relativo em `docs/protocolo_experimental.md`.
2. **Comparabilidade:** o ORB-SLAM2 RGB-D (escala métrica, SE(3)) foi comparado ao TartanVO monocular. Para reproduzir os números do artigo (objetivo específico 1), usar a mesma configuração; para a comparação nova, usar monocular + Sim(3) para todos.
3. As falhas já vêm prontas no download "Full Sequence". **Só a fumaça precisa ser gerada.**
4. Os buracos na profundidade reprojetada confirmam a necessidade de preenchimento antes da emulação de fumaça.
5. **Downloads:** Google Drive, "Full Sequence" de 3,4 a 9,2 GB (com falhas) ou "Bag" de 0,4 a 0,7 GB (rosbag bruto). Ver `docs/datasets.md`.

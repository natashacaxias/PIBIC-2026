# Experimentos — máquina do laboratório

Pipeline completo dos experimentos do PIBIC: dados → fumaça → execução dos algoritmos em Docker → métricas. Preparado em 10/10/2026 e executado de 29 a 31/10/2026 no servidor do laboratório (RTX 5070 Ti, 24 núcleos, 62 GB de RAM): **2.720 execuções da matriz principal, mais 112 da fumaça extrema e 68 do piloto do DCP**, avaliadas com este pipeline. Protocolo em [`../docs/protocolo_experimental.md`](../docs/protocolo_experimental.md) e ambiente em [`../docs/ambiente.md`](../docs/ambiente.md).

```
experiments/
├── config/experiment.json      # caminhos, câmera, condições, algoritmos, repetições
├── lib/queenscamp.py           # layout das sequências, listas de entrada, matriz de execuções
├── scripts/
│   ├── check_gpu.sh            # driver, Docker+GPU, sm_120 no PyTorch (NATASHA-25)
│   ├── dataset.py              # download | inspect | smoke | dehaze
│   ├── run_matrix.py           # executa a matriz (retomável)
│   ├── evaluate.py             # metrics.csv + summary.csv
│   ├── stats_analysis.py       # Wilcoxon + Bonferroni + bootstrap + critério de robustez
│   └── figures.py              # mapa de degradação, rastreamento, erro cumulativo, trajetórias
├── algorithms/
│   ├── orbslam2/               # Ubuntu 18.04; patches: sem loop closure, TUM monocular, runner
│   ├── tartanvo/               # CUDA 12.8 + PyTorch 2.7 + cupy
│   ├── dpvo/                   # CUDA 12.8 + PyTorch 2.7, extensões compiladas para sm_120
│   └── droidslam/              # reserva
└── tests/                      # 45 testes, rodam sem GPU
```

## Ordem de execução
```bash
cd PIBIC-2026/experiments
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests

# 1) imagens e GPU (ver docs/ambiente.md)
docker build -t pibic/dpvo:0ac95b6 algorithms/dpvo
docker build -t pibic/tartanvo:ec2ecc3 algorithms/tartanvo
docker build -t pibic/orbslam2:f2e6f51 algorithms/orbslam2
bash scripts/check_gpu.sh

# 2) dados: comece por UMA sequência pequena (09, ~4,2 GB)
.venv/bin/python scripts/dataset.py download --dest /data/queenscamp_raw --sequences 09 --kind full
#    extrair para /data/queenscamp/09 e inspecionar:
.venv/bin/python scripts/dataset.py inspect /data/queenscamp/09
#    → preencher em config/experiment.json: depth_dir, timestamps_file, groundtruth_file,
#      depth_scale, rgb_dir de cada falha e os intrínsecos (arquivo camera_info_rgb baixado junto)

# 3) fumaça
.venv/bin/python scripts/dataset.py smoke --sequences 09

# 4) piloto: um algoritmo, uma sequência, condição original
.venv/bin/python scripts/run_matrix.py --dry-run
.venv/bin/python scripts/run_matrix.py --algorithms dpvo --sequences 09 --conditions original --max-runs 1
.venv/bin/python scripts/evaluate.py && column -s, -t < results/metrics.csv | less -S

# 5) reprodução do QueensCAMP (objetivo 1): comparar com docs/leituras/2024_bruno_queenscamp.md
.venv/bin/python scripts/run_matrix.py --algorithms orbslam2_rgbd tartanvo --sequences 09 \
    --conditions original underexposure overexposure breakage wet condensation dirt

# 6) matriz completa: uma fila de GPU e fatias de CPU em paralelo (a matriz principal levou ~43 h)
#    scripts/matrix.sh start N lança a fila de GPU e N fatias do ORB-SLAM2; stop cria o arquivo STOP; status mostra o andamento
.venv/bin/python scripts/run_matrix.py --algorithms dpvo tartanvo   > gpu.log 2>&1 &
.venv/bin/python scripts/run_matrix.py --algorithms orbslam2_mono orbslam2_rgbd --shard 0/2 > cpu0.log 2>&1 &
.venv/bin/python scripts/run_matrix.py --algorithms orbslam2_mono orbslam2_rgbd --shard 1/2 > cpu1.log 2>&1 &
#    antes de cada execução o run_matrix.py espera CPU, GPU, RAM e disco voltarem aos limites do experiment.json (resources)

# 7) baseline de dehazing e fumaça extrema (condições desligadas por padrão, exploratórias; ver docs/protocolo_experimental.md §10.6 e §10.7)
.venv/bin/python scripts/dataset.py smoke --sequences 09           # gera as 4 condições de fumaça, inclusive a exploratória smoke_extrema
.venv/bin/python scripts/run_matrix.py --algorithms tartanvo dpvo --conditions smoke_extrema
.venv/bin/python scripts/dataset.py dehaze --sequences 09
.venv/bin/python scripts/run_matrix.py --sequences 09 --conditions dcp_original dcp_smoke_leve dcp_smoke_moderada dcp_smoke_densa

# 8) métricas e estatística
.venv/bin/python scripts/evaluate.py
.venv/bin/python scripts/stats_analysis.py      # results/stats_report.md
.venv/bin/python scripts/figures.py             # results/figures/*.pdf|png
```

## Saídas de cada execução
`<runs_root>/<algoritmo>/<seq>/<condição>/seed<k>/` contém:
- `input/`: `rgb.txt`, `assoc.txt`, `calib.txt` (e `settings.yaml` no ORB-SLAM2);
- `trajectory_tum.txt`;
- `meta.json`: status, tempo, memória, comando, commit, parâmetros da fumaça;
- `algo_meta.json`: latência por quadro, pico de memória, versões;
- `stdout.log`;
- `frames.csv` (só ORB-SLAM2): estado de rastreamento por quadro.

Execuções com `meta.json` são puladas. `--retry-failed` refaz as que falharam.

## Verificado e não verificado
- As três imagens Docker (ORB-SLAM2, TartanVO, DPVO) foram construídas e rodaram a matriz inteira; a do DROID-SLAM é reserva e não foi construída.
- Layout do *Full Sequence*, escala da profundidade e intrínsecos já estão preenchidos em `config/experiment.json`.
- Os testes cobrem layout, matriz, comandos, métricas e estatística com trajetórias sintéticas; a reprodução dos números do QueensCAMP está em `docs/protocolo_experimental.md` §10.1 (TartanVO 1,03× e RGB-D 1,04× o artigo, com Sim(3)).
- Lacunas conhecidas (`docs/protocolo_experimental.md` §10): o ORB-SLAM2 RGB-D não rastreia nas sequências 02, 14 e 15; 35 execuções do RGB-D caem por *segfault* depois de reset do mapa; pico de RAM por execução não gravado; BRISQUE não rodado.

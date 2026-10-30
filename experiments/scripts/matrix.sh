#!/bin/bash
# Roda a matriz completa em segundo plano, sem forçar a máquina (servidor compartilhado, ~dezenas de horas).
#
#   bash scripts/matrix.sh start [N]   sobe a fila de GPU (TartanVO e DPVO, um processo de GPU por vez) e N fatias
#                                      do ORB-SLAM2 em CPU (padrão 2); retoma de onde parou
#   bash scripts/matrix.sh stop        pede parada limpa: cada fila termina a execução em curso e sai
#   bash scripts/matrix.sh status      progresso, processos e temperaturas
#
# Os processos ficam desacoplados do terminal (setsid). Logs e pids em $LOGS (padrão /data/matrix_logs).
# Antes de cada execução o run_matrix.py espera o hardware ficar dentro dos limites de `resources` do config.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=.venv/bin/python
LOGS=${LOGS:-/data/matrix_logs}
RUNS=$($PY -c "import json; print(json.load(open('config/experiment.json'))['paths']['runs_root'])")

running() { pgrep -f "^\.venv/bin/python scripts/run_matrix\.py" || true; }
cpu_temp() {
  for zone in /sys/class/thermal/thermal_zone*; do
    if [ "$(cat "$zone/type")" = x86_pkg_temp ]; then echo $(( $(cat "$zone/temp") / 1000 )); return; fi
  done
  echo n/d
}

case "${1:-status}" in
  start)
    N=${2:-2}
    [ -z "$(running)" ] || { echo "já há uma matriz rodando (bash scripts/matrix.sh status)"; exit 1; }
    mkdir -p "$LOGS"
    rm -f "$RUNS/STOP" "$LOGS"/*.pid
    setsid nohup $PY scripts/run_matrix.py --algorithms tartanvo dpvo > "$LOGS/gpu.log" 2>&1 < /dev/null &
    for ((k = 0; k < N; k++)); do
      setsid nohup $PY scripts/run_matrix.py --algorithms orbslam2_mono orbslam2_rgbd --shard "$k/$N" \
        > "$LOGS/orbslam2_$k.log" 2>&1 < /dev/null &
    done
    sleep 2
    running > "$LOGS/run_matrix.pids"
    echo "matriz iniciada: fila de GPU + $N fatia(s) de ORB-SLAM2; logs em $LOGS"
    ;;
  stop)
    touch "$RUNS/STOP"
    echo "STOP criado em $RUNS: cada fila sai depois da execução em curso (até ~3 min)"
    ;;
  status)
    $PY - "$RUNS" <<'EOF'
import collections, glob, json, sys
runs_root = sys.argv[1]
done = collections.Counter()
for path in glob.glob(f'{runs_root}/*/*/*/seed*/meta.json'):
    meta = json.load(open(path))
    done[(meta['algorithm'], meta['status'])] += 1
print(f'{sum(done.values())} execuções com meta.json em {runs_root}')
for (algorithm, status), n in sorted(done.items()):
    print(f'  {algorithm:15} {status:16} {n}')
EOF
    echo "processos: $(running | wc -l) fila(s) rodando; containers: $(docker ps --format '{{.Names}}' | wc -l)"
    echo "CPU $(cpu_temp) °C · GPU $(nvidia-smi --query-gpu=temperature.gpu,power.draw,utilization.gpu --format=csv,noheader) · carga $(cut -d' ' -f1-3 /proc/loadavg)"
    [ -e "$RUNS/STOP" ] && echo "STOP existe: as filas não sobem até apagá-lo (matrix.sh start apaga)" || true
    ;;
  *)
    echo "uso: bash scripts/matrix.sh start [N] | stop | status"; exit 2
    ;;
esac

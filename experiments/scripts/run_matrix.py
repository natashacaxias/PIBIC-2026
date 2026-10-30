#!/usr/bin/env python3
"""Executa a matriz algoritmo × sequência × condição × semente em containers Docker.

Retomável: uma execução com meta.json é pulada (use --retry-failed para refazer
as que falharam). Cada execução grava em <runs_root>/<alg>/<seq>/<cond>/seed<k>/:
trajectory_tum.txt, meta.json, stdout.log e as listas de entrada.

Servidor compartilhado e matriz longa: antes de cada execução espera (sem abortar) o host ficar dentro dos
limites de `resources` (temperatura da CPU e da GPU, RAM disponível, disco livre, memória livre da GPU).
Para parar com limpeza depois da execução em curso: `touch <runs_root>/STOP`.

Paralelismo: `--shard K/N` executa só as execuções de índice i % N == K da matriz (com os mesmos filtros), uma fatia
estável entre reinícios. Rode as N fatias juntas; o ORB-SLAM2 usa ~0,2 núcleo, então várias cabem sem esforço.

Exemplos:
  python scripts/run_matrix.py --dry-run
  python scripts/run_matrix.py --algorithms dpvo --sequences 09 --conditions original
"""
import argparse
import csv
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.queenscamp import (expand_runs, frame_list, load_config, orbslam2_settings,  # noqa: E402
                            write_assoc_list, write_calib, write_rgb_list)

REPO = Path(__file__).resolve().parents[2]


def git_sha():
    try:
        return subprocess.run(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


class GpuMonitor(threading.Thread):
    """Amostra a memória usada da GPU 0 via nvidia-smi; reporta o pico acima da linha de base."""

    def __init__(self, interval=0.5):
        super().__init__(daemon=True)
        self.interval, self.peak, self.baseline = interval, 0, self.read()
        self._halt = threading.Event()

    @staticmethod
    def read():
        try:
            out = subprocess.run(['nvidia-smi', '--query-gpu=memory.used', '--format=csv,noheader,nounits', '-i', '0'],
                                 capture_output=True, text=True, timeout=5).stdout
            return int(out.strip().splitlines()[0])
        except (OSError, ValueError, IndexError, subprocess.SubprocessError):
            return None

    def run(self):
        while not self._halt.is_set():
            value = self.read()
            if value is not None:
                self.peak = max(self.peak, value)
            time.sleep(self.interval)

    def stop(self):
        self._halt.set()
        self.join(timeout=5)
        if self.baseline is None:
            return None
        return max(0, self.peak - self.baseline)


RESOURCE_DEFAULTS = {'memory': '8g', 'cpus': 8, 'pids': 1024, 'min_free_gpu_mib': 10000,
                     'max_gpu_temp_c': 83, 'max_cpu_temp_c': 85, 'min_mem_available_gb': 12, 'min_disk_free_gb': 100,
                     'max_wait_min': 360, 'max_consecutive_failures': 5}
STOP_FILE = 'STOP'


def nvidia_smi(field):
    try:
        out = subprocess.run(['nvidia-smi', f'--query-gpu={field}', '--format=csv,noheader,nounits', '-i', '0'],
                             capture_output=True, text=True, timeout=5).stdout
        return int(float(out.strip().splitlines()[0]))
    except (OSError, ValueError, IndexError, subprocess.SubprocessError):
        return None


def gpu_free_mib():
    return nvidia_smi('memory.free')


def cpu_temp_c():
    temps = []
    for zone in Path('/sys/class/thermal').glob('thermal_zone*'):
        try:
            if (zone / 'type').read_text().strip() == 'x86_pkg_temp':
                temps.append(int((zone / 'temp').read_text()) / 1000)
        except (OSError, ValueError):
            continue
    return max(temps) if temps else None


def mem_available_gb():
    try:
        for line in Path('/proc/meminfo').read_text().splitlines():
            if line.startswith('MemAvailable:'):
                return int(line.split()[1]) / 2**20
    except (OSError, ValueError):
        pass
    return None


def read_hardware(disk_path):
    """Leituras do host que limitam a matriz; None quando uma delas não pode ser lida."""
    try:
        disk = shutil.disk_usage(disk_path).free / 2**30
    except OSError:
        disk = None
    return {'gpu_temp_c': nvidia_smi('temperature.gpu'), 'gpu_free_mib': gpu_free_mib(), 'cpu_temp_c': cpu_temp_c(),
            'mem_available_gb': mem_available_gb(), 'disk_free_gb': disk}


def hardware_problems(readings, limits, uses_gpu):
    """Motivos para não iniciar a próxima execução (lista vazia: pode seguir). Leitura ausente não bloqueia."""
    rules = [('cpu_temp_c', 'max_cpu_temp_c', True, '°C na CPU', False),
             ('mem_available_gb', 'min_mem_available_gb', False, 'GiB de RAM disponível', False),
             ('disk_free_gb', 'min_disk_free_gb', False, 'GiB livres em disco', False),
             ('gpu_temp_c', 'max_gpu_temp_c', True, '°C na GPU', True),
             ('gpu_free_mib', 'min_free_gpu_mib', False, 'MiB livres na GPU', True)]
    problems = []
    for reading, limit, is_ceiling, label, gpu_only in rules:
        value = readings.get(reading)
        if value is None or (gpu_only and not uses_gpu):
            continue
        breached = value > limits[limit] if is_ceiling else value < limits[limit]
        if breached:
            problems.append(f'{value:.0f} {label} (limite {limits[limit]})')
    return problems


def wait_for_hardware(limits, uses_gpu, disk_path, reader=read_hardware, sleep=time.sleep, poll_s=60):
    """Espera o host voltar aos limites; False se passar `max_wait_min` sem voltar (a matriz para e é retomável)."""
    deadline = time.monotonic() + limits['max_wait_min'] * 60
    waiting = False
    while True:
        problems = hardware_problems(reader(disk_path), limits, uses_gpu)
        if not problems:
            if waiting:
                print('hardware dentro dos limites: retomando', flush=True)
            return True
        if time.monotonic() >= deadline:
            print('hardware fora dos limites por mais de {} min, parando: {}'.format(limits['max_wait_min'], '; '.join(problems)),
                  file=sys.stderr)
            return False
        if not waiting:
            print('aguardando o hardware: ' + '; '.join(problems), flush=True)
            waiting = True
        sleep(poll_s)


def failure_streak(streak, status):
    """Execuções seguidas que falharam por motivo que não é rastreamento (failed, timeout). Rastreamento perdido
    (not_initialized, tracking_lost) é resultado do experimento e zera a contagem, como o ok."""
    return streak + 1 if status in ('failed', 'timeout') else 0


def parse_shard(text):
    """'K/N' -> (K, N) com 0 <= K < N."""
    try:
        k, n = (int(x) for x in text.split('/'))
        if not 0 <= k < n:
            raise ValueError
    except ValueError:
        raise argparse.ArgumentTypeError(f"fatia inválida {text!r}: use K/N com 0 <= K < N, por exemplo 0/4")
    return k, n


def shard_runs(runs, shard):
    """Fatia estável: a execução de índice i (na matriz com os mesmos filtros) é da fatia i % N."""
    if shard is None:
        return runs
    k, n = shard
    return [run for i, run in enumerate(runs) if i % n == k]


def read_states(run_dir, n_frames):
    """Estados de rastreamento do frames.csv, ou None se faltar ou se a execução parou antes do fim."""
    frames = Path(run_dir) / 'frames.csv'
    if not frames.exists():
        return None
    with open(frames, newline='', encoding='utf-8') as f:
        states = [row['tracking_state'] for row in csv.DictReader(f)]
    return states if len(states) == n_frames else None


def never_initialized(run_dir, n_frames):
    """ORB-SLAM2 que nunca passou de NOT_INITIALIZED (estado 1): não houve mapa nem keyframe. Um reset por
    "Wrong initialization" põe um quadro em NO_IMAGES_YET (estado 0), então 0 e 1 valem; 2 (OK) ou 3 (LOST) não."""
    states = read_states(run_dir, n_frames)
    return states is not None and '1' in states and set(states) <= {'0', '1'}


def empty_map_at_save(run_dir, n_frames):
    """ORB-SLAM2 que rodou todos os quadros e caiu em SaveTrajectoryTUM: o mapa estava vazio no fim (perdeu o
    rastreamento e foi resetado), então não há keyframe para salvar. Distingue de queda no meio da execução."""
    if read_states(run_dir, n_frames) is None:
        return False
    log = Path(run_dir) / 'stdout.log'
    lines = log.read_text(encoding='utf-8', errors='replace').strip().splitlines() if log.exists() else []
    return bool(lines) and lines[-1].startswith('Saving camera trajectory')


def prepare_inputs(cfg, run, algo):
    run_dir = Path(run['run_dir'])
    inputs = run_dir / 'input'
    inputs.mkdir(parents=True, exist_ok=True)
    frames = frame_list(cfg, run['sequence'], run['condition'])
    write_rgb_list(frames, inputs / 'rgb.txt')
    write_assoc_list(frames, inputs / 'assoc.txt')
    write_calib(cfg, inputs / 'calib.txt')
    if algo['kind'] == 'orbslam2':
        (inputs / 'settings.yaml').write_text(orbslam2_settings(cfg), encoding='utf-8')
    return frames


def docker_command(cfg, run, algo):
    run_dir = run['run_dir']
    inputs = f'{run_dir}/input'
    mounts = {cfg['dataset']['root'], cfg['paths']['smoke_root'], cfg['paths']['dehaze_root']}
    cmd = ['docker', 'run', '--rm', '--ipc=host', '--user', f'{os.getuid()}:{os.getgid()}']
    if algo['kind'] != 'orbslam2':  # ORB-SLAM2 roda só em CPU: não precisa passar pelo runtime da NVIDIA a cada container
        cmd += ['--gpus', 'all']
    # Servidor compartilhado: teto de RAM (sem swap), CPU e processos por container, prioridade de CPU abaixo da
    # padrão (1024) e sem core dump (um segfault repetido por 55 h não deve encher o disco).
    limits = {**RESOURCE_DEFAULTS, **cfg.get('resources', {}), **algo.get('resources', {})}
    cmd += ['--memory', limits['memory'], '--memory-swap', limits['memory'], '--cpus', str(limits['cpus']),
            '--cpu-shares', '512', '--pids-limit', str(limits['pids']), '--ulimit', 'core=0']
    for path in sorted(mounts):
        # Sem isto o Docker cria a origem ausente como root e o usuário perde a escrita nela.
        Path(path).mkdir(parents=True, exist_ok=True)
        cmd += ['-v', f'{path}:{path}:ro']
    cmd += ['-v', f'{run_dir}:{run_dir}', '-e', 'HOME=/tmp', '-e', f'SEED={run["seed"]}']
    kind = algo['kind']
    if kind == 'orbslam2':
        orb = cfg['algorithms_defaults']['orbslam2']
        lst = f'{inputs}/assoc.txt' if algo['mode'] == 'rgbd' else f'{inputs}/rgb.txt'
        cmd += ['-e', 'ORBSLAM2_NO_LOOP=1', algo['image'], '/opt/ORB_SLAM2/Vocabulary/ORBvoc.txt',
                f'{inputs}/settings.yaml', algo['mode'], lst, run_dir] + (['--realtime'] if orb['realtime'] else [])
    elif kind in ('tartanvo', 'dpvo', 'droid'):
        cmd += [algo['image'], '--rgb-list', f'{inputs}/rgb.txt', '--calib', f'{inputs}/calib.txt',
                '--out-dir', run_dir, '--seed', str(run['seed'])]
    else:
        raise ValueError(f'algoritmo desconhecido: {kind}')
    return cmd


def execute(cfg, run, algo, timeout, shard=None):
    run_dir = Path(run['run_dir'])
    frames = prepare_inputs(cfg, run, algo)
    cmd = docker_command(cfg, run, algo)
    condition_meta = None
    kind = cfg['conditions'][run['condition']]['kind']
    if kind in ('smoke', 'dehaze'):
        root, name = (('smoke_root', 'smoke_meta.json') if kind == 'smoke' else ('dehaze_root', 'dcp_meta.json'))
        meta_file = Path(cfg['paths'][root]) / run['sequence'] / run['condition'] / name
        condition_meta = json.loads(meta_file.read_text()) if meta_file.exists() else None
    hardware = read_hardware(run_dir)
    monitor = GpuMonitor()
    monitor.start()
    started, t0 = datetime.now(timezone.utc).isoformat(), time.monotonic()
    status, returncode = 'failed', None
    traj = run_dir / 'trajectory_tum.txt'
    with open(run_dir / 'stdout.log', 'w', encoding='utf-8') as log:
        try:
            returncode = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, timeout=timeout).returncode
            if returncode == 0 and traj.exists() and traj.stat().st_size > 0:
                status = 'ok'
            elif algo['kind'] == 'orbslam2' and returncode == 139 and never_initialized(run_dir, len(frames)):
                # sem keyframe o SaveTrajectoryTUM do ORB-SLAM2 acessa vpKFs[0] vazio e dá segfault (139): falha de
                # rastreamento, não de infraestrutura
                status = 'not_initialized'
            elif algo['kind'] == 'orbslam2' and returncode == 139 and empty_map_at_save(run_dir, len(frames)):
                # inicializou por poucos quadros, perdeu o rastreamento e terminou com o mapa resetado: mesmo segfault
                status = 'tracking_lost'
        except subprocess.TimeoutExpired:
            status = 'timeout'
    wall = time.monotonic() - t0
    meta = dict(run, image=algo['image'], status=status, returncode=returncode, wall_s=round(wall, 2),
                hardware_start=hardware, shard=shard, peak_gpu_mib_host=monitor.stop(), n_frames=len(frames), started_at=started,
                finished_at=datetime.now(timezone.utc).isoformat(), command=shlex.join(cmd),
                repo_sha=git_sha(), condition_meta=condition_meta)
    algo_meta = run_dir / 'algo_meta.json'
    if algo_meta.exists():
        meta['algo'] = json.loads(algo_meta.read_text())
    (run_dir / 'meta.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
    return meta


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--config', default=str(Path(__file__).resolve().parents[1] / 'config/experiment.json'))
    parser.add_argument('--algorithms', nargs='+')
    parser.add_argument('--sequences', nargs='+')
    parser.add_argument('--conditions', nargs='+')
    parser.add_argument('--retry-failed', action='store_true')
    parser.add_argument('--shard', type=parse_shard, metavar='K/N', help='só a fatia K de N da matriz (rode as N juntas)')
    parser.add_argument('--max-runs', type=int, help='parar depois de N execuções (teste)')
    parser.add_argument('--dry-run', action='store_true', help='só listar o que seria executado')
    args = parser.parse_args()
    cfg = load_config(args.config)
    runs = shard_runs(expand_runs(cfg, args.algorithms, args.sequences, args.conditions), args.shard)
    pending = []
    for run in runs:
        meta_file = Path(run['run_dir']) / 'meta.json'
        if meta_file.exists():
            status = json.loads(meta_file.read_text()).get('status')
            if status == 'ok' or not args.retry_failed:
                continue
        pending.append(run)
    print(f'{len(runs)} execuções na matriz, {len(pending)} pendentes')
    if args.dry_run:
        for run in pending[:20]:
            print(f"  {run['algorithm']:15} seq {run['sequence']} {run['condition']:15} seed {run['seed']}")
        if len(pending) > 20:
            print(f'  ... e mais {len(pending) - 20}')
        if not cfg['_camera_ready']:
            print('ATENÇÃO: intrínsecos da câmera não preenchidos em config/experiment.json')
        return 0
    if not cfg['_camera_ready']:
        print('Preencha fx, fy, cx, cy em config/experiment.json antes de executar.', file=sys.stderr)
        return 2
    limits = {**RESOURCE_DEFAULTS, **cfg.get('resources', {})}
    runs_root = Path(cfg['paths']['runs_root'])
    runs_root.mkdir(parents=True, exist_ok=True)
    streak = 0
    for i, run in enumerate(pending[:args.max_runs] if args.max_runs else pending, 1):
        if streak >= limits['max_consecutive_failures']:
            # GPU ou driver caído faria a fila marcar centenas de execuções como failed em minutos
            print(f"{streak} execuções seguidas com failed/timeout: parando para não gastar a matriz (veja o stdout.log da última).")
            return 5
        if (runs_root / STOP_FILE).exists():
            print(f'{runs_root / STOP_FILE} existe: parando antes da próxima execução (apague o arquivo e rode de novo).')
            return 4
        uses_gpu = cfg['algorithms'][run['algorithm']]['kind'] != 'orbslam2'
        if not wait_for_hardware(limits, uses_gpu, runs_root):
            return 3
        meta = execute(cfg, run, cfg['algorithms'][run['algorithm']], cfg['timeout_s'],
                       shard='{}/{}'.format(*args.shard) if args.shard else None)
        print(f"[{i}/{len(pending)}] {run['algorithm']} {run['sequence']} {run['condition']} seed{run['seed']}: "
              f"{meta['status']} ({meta['wall_s']} s)", flush=True)
        streak = failure_streak(streak, meta['status'])
    return 0


if __name__ == '__main__':
    sys.exit(main())

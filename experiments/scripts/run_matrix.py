#!/usr/bin/env python3
"""Executa a matriz algoritmo × sequência × condição × semente em containers Docker.

Retomável: uma execução com meta.json é pulada (use --retry-failed para refazer
as que falharam). Cada execução grava em <runs_root>/<alg>/<seq>/<cond>/seed<k>/:
trajectory_tum.txt, meta.json, stdout.log e as listas de entrada.

Exemplos:
  python scripts/run_matrix.py --dry-run
  python scripts/run_matrix.py --algorithms dpvo --sequences 09 --conditions original
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shlex
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


RESOURCE_DEFAULTS = {'memory': '24g', 'cpus': 8, 'pids': 1024, 'min_free_gpu_mib': 10000}


def gpu_free_mib():
    try:
        out = subprocess.run(['nvidia-smi', '--query-gpu=memory.free', '--format=csv,noheader,nounits', '-i', '0'],
                             capture_output=True, text=True, timeout=5).stdout
        return int(out.strip().splitlines()[0])
    except (OSError, ValueError, IndexError, subprocess.SubprocessError):
        return None


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
    cmd = ['docker', 'run', '--rm', '--gpus', 'all', '--ipc=host', '--user', f'{os.getuid()}:{os.getgid()}']
    # Servidor compartilhado: teto de RAM (sem swap), CPU e processos por container.
    limits = {**RESOURCE_DEFAULTS, **cfg.get('resources', {})}
    cmd += ['--memory', limits['memory'], '--memory-swap', limits['memory'], '--cpus', str(limits['cpus']),
            '--pids-limit', str(limits['pids'])]
    for path in sorted(mounts):
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


def execute(cfg, run, algo, timeout):
    run_dir = Path(run['run_dir'])
    frames = prepare_inputs(cfg, run, algo)
    cmd = docker_command(cfg, run, algo)
    condition_meta = None
    kind = cfg['conditions'][run['condition']]['kind']
    if kind in ('smoke', 'dehaze'):
        root, name = (('smoke_root', 'smoke_meta.json') if kind == 'smoke' else ('dehaze_root', 'dcp_meta.json'))
        meta_file = Path(cfg['paths'][root]) / run['sequence'] / run['condition'] / name
        condition_meta = json.loads(meta_file.read_text()) if meta_file.exists() else None
    monitor = GpuMonitor()
    monitor.start()
    started, t0 = datetime.now(timezone.utc).isoformat(), time.monotonic()
    status, returncode = 'failed', None
    with open(run_dir / 'stdout.log', 'w', encoding='utf-8') as log:
        try:
            returncode = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, timeout=timeout).returncode
            traj = run_dir / 'trajectory_tum.txt'
            if returncode == 0 and traj.exists() and traj.stat().st_size > 0:
                status = 'ok'
        except subprocess.TimeoutExpired:
            status = 'timeout'
    wall = time.monotonic() - t0
    meta = dict(run, image=algo['image'], status=status, returncode=returncode, wall_s=round(wall, 2),
                peak_gpu_mib_host=monitor.stop(), n_frames=len(frames), started_at=started,
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
    parser.add_argument('--max-runs', type=int, help='parar depois de N execuções (teste)')
    parser.add_argument('--dry-run', action='store_true', help='só listar o que seria executado')
    args = parser.parse_args()
    cfg = load_config(args.config)
    runs = expand_runs(cfg, args.algorithms, args.sequences, args.conditions)
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
    min_free = {**RESOURCE_DEFAULTS, **cfg.get('resources', {})}['min_free_gpu_mib']
    for i, run in enumerate(pending[:args.max_runs] if args.max_runs else pending, 1):
        if cfg['algorithms'][run['algorithm']]['kind'] != 'orbslam2':
            free = gpu_free_mib()
            if free is not None and free < min_free:
                print(f'GPU com só {free} MiB livres (mínimo {min_free}): outro processo a está usando. '
                      'Parando; rode de novo quando liberar (execuções concluídas são puladas).', file=sys.stderr)
                return 3
        meta = execute(cfg, run, cfg['algorithms'][run['algorithm']], cfg['timeout_s'])
        print(f"[{i}/{len(pending)}] {run['algorithm']} {run['sequence']} {run['condition']} seed{run['seed']}: "
              f"{meta['status']} ({meta['wall_s']} s)", flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())

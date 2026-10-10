"""Utilidades compartilhadas pelos scripts de experimento.

Configuração, layout das sequências do QueensCAMP, listas de entrada para os
algoritmos e expansão da matriz de execuções. Só biblioteca padrão.
"""
import json
from pathlib import Path

FRAME_SUFFIXES = ('.png', '.jpg', '.jpeg')


def load_config(path):
    with open(path, encoding='utf-8') as f:
        cfg = json.load(f)
    camera = cfg['camera']
    missing = [k for k in ('fx', 'fy', 'cx', 'cy') if camera.get(k) is None]
    cfg['_camera_ready'] = not missing
    return cfg


def sequence_dir(cfg, seq):
    data = cfg['dataset']
    return Path(data['root']) / data['sequence_pattern'].format(seq=seq)


def condition_rgb_dir(cfg, seq, condition):
    cond = cfg['conditions'][condition]
    if cond['kind'] == 'queenscamp':
        return sequence_dir(cfg, seq) / cond['rgb_dir']
    if cond['kind'] == 'smoke':
        return Path(cfg['paths']['smoke_root']) / seq / condition
    if cond['kind'] == 'dehaze':
        return Path(cfg['paths']['dehaze_root']) / seq / condition
    raise ValueError(f'tipo de condição desconhecido: {cond["kind"]}')


def read_timestamps(path):
    """Arquivo `id t` gerado pelo convert_bag_to_files.py do QueensCAMP."""
    stamps = {}
    with open(path, encoding='utf-8') as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 2 and not parts[0].startswith('#'):
                stamps[parts[0]] = float(parts[1])
    return stamps


def frame_list(cfg, seq, condition):
    """Lista ordenada de (timestamp, caminho_rgb, caminho_profundidade)."""
    data = cfg['dataset']
    seq_dir = sequence_dir(cfg, seq)
    rgb_dir = condition_rgb_dir(cfg, seq, condition)
    depth_dir = seq_dir / data['depth_dir']
    stamps_file = seq_dir / data['timestamps_file']
    stamps = read_timestamps(stamps_file) if stamps_file.exists() else {}
    files = sorted(p for p in rgb_dir.iterdir() if p.suffix.lower() in FRAME_SUFFIXES)
    if not files:
        raise FileNotFoundError(f'nenhuma imagem em {rgb_dir}')
    frames = []
    for index, rgb in enumerate(files):
        t = stamps.get(rgb.stem, index / data['fps'])
        frames.append((t, rgb, depth_dir / (rgb.stem + '.png')))
    return frames


def write_rgb_list(frames, path):
    with open(path, 'w', encoding='utf-8') as f:
        for t, rgb, _ in frames:
            f.write(f'{t:.6f} {rgb}\n')


def write_assoc_list(frames, path):
    with open(path, 'w', encoding='utf-8') as f:
        for t, rgb, depth in frames:
            f.write(f'{t:.6f} {rgb} {t:.6f} {depth}\n')


def write_calib(cfg, path):
    cam = cfg['camera']
    if not cfg.get('_camera_ready'):
        raise ValueError('preencha fx, fy, cx, cy em camera (config/experiment.json)')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f"{cam['fx']} {cam['fy']} {cam['cx']} {cam['cy']}\n")


def orbslam2_settings(cfg):
    """Arquivo de configuração OpenCV-YAML do ORB-SLAM2 para o QueensCAMP."""
    cam, data = cfg['camera'], cfg['dataset']
    orb = cfg['algorithms_defaults']['orbslam2']
    return f"""%YAML:1.0
Camera.fx: {cam['fx']}
Camera.fy: {cam['fy']}
Camera.cx: {cam['cx']}
Camera.cy: {cam['cy']}
Camera.k1: 0.0
Camera.k2: 0.0
Camera.p1: 0.0
Camera.p2: 0.0
Camera.width: {cam['width']}
Camera.height: {cam['height']}
Camera.fps: {data['fps']}
Camera.bf: {cam['fx'] * orb['baseline_m']}
Camera.RGB: 0
ThDepth: {orb['th_depth']}
DepthMapFactor: {data['depth_scale']}
ORBextractor.nFeatures: {orb['n_features']}
ORBextractor.scaleFactor: 1.2
ORBextractor.nLevels: 8
ORBextractor.iniThFAST: 20
ORBextractor.minThFAST: 7
Viewer.KeyFrameSize: 0.05
Viewer.KeyFrameLineWidth: 1
Viewer.GraphLineWidth: 0.9
Viewer.PointSize: 2
Viewer.CameraSize: 0.08
Viewer.CameraLineWidth: 3
Viewer.ViewpointX: 0
Viewer.ViewpointY: -0.7
Viewer.ViewpointZ: -1.8
Viewer.ViewpointF: 500
"""


def expand_runs(cfg, algorithms=None, sequences=None, conditions=None):
    """Produto algoritmo × sequência × condição × semente.

    Algoritmos e condições com "enabled": false só entram se pedidos explicitamente.
    """
    runs_root = Path(cfg['paths']['runs_root'])
    conditions = conditions or [c for c, spec in cfg['conditions'].items() if spec.get('enabled', True)]
    runs = []
    for name, algo in cfg['algorithms'].items():
        if (algorithms and name not in algorithms) or (not algorithms and not algo.get('enabled', True)):
            continue
        for seq in sequences or cfg['sequences']:
            for condition in conditions:
                for seed in range(algo.get('repetitions', cfg['repetitions'])):
                    runs.append({'algorithm': name, 'sequence': seq, 'condition': condition, 'seed': seed,
                                 'run_dir': str(runs_root / name / seq / condition / f'seed{seed}')})
    return runs

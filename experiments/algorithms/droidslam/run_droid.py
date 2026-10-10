"""Executa o DROID-SLAM como VO (sem BA global) numa lista de frames; grava trajetória TUM.

Alternativa ao DPVO, desabilitada por padrão em config/experiment.json.
Pré-processamento idêntico ao demo.py oficial (redimensiona para ~384×512),
com stride 1 (o demo usa 3). --vo-only desliga o backend global chamado em
terminate(), para comparar como VO pura; o preenchimento de trajetória dos
quadros que não são keyframes é mantido.
"""
import argparse
import json
from pathlib import Path
import random
import sys
import time

import cv2
import numpy as np
import torch

sys.path.insert(0, '/opt/DROID-SLAM/droid_slam')
from droid import Droid  # noqa: E402


def read_list(path):
    stamps, files = [], []
    for line in Path(path).read_text().splitlines():
        if line.strip() and not line.startswith('#'):
            t, f = line.split()[:2]
            stamps.append(float(t))
            files.append(f)
    return stamps, files


def image_stream(files, calib):
    fx, fy, cx, cy = calib[:4]
    for t, path in enumerate(files):
        image = cv2.imread(path)
        h0, w0, _ = image.shape
        h1 = int(h0 * np.sqrt((384 * 512) / (h0 * w0)))
        w1 = int(w0 * np.sqrt((384 * 512) / (h0 * w0)))
        image = cv2.resize(image, (w1, h1))[:h1 - h1 % 8, :w1 - w1 % 8]
        intrinsics = torch.as_tensor([fx, fy, cx, cy])
        intrinsics[0::2] *= w1 / w0
        intrinsics[1::2] *= h1 / h0
        yield t, torch.as_tensor(image).permute(2, 0, 1)[None], intrinsics


def droid_args(weights):
    """Mesmos padrões do demo.py oficial."""
    return argparse.Namespace(weights=weights, buffer=512, image_size=[240, 320], disable_vis=True, stereo=False,
                              beta=0.3, filter_thresh=2.4, warmup=8, keyframe_thresh=4.0, frontend_thresh=16.0,
                              frontend_window=25, frontend_radius=2, frontend_nms=1, backend_thresh=22.0,
                              backend_radius=2, backend_nms=3, upsample=False, asynchronous=False,
                              frontend_device='cuda', backend_device='cuda')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rgb-list', required=True)
    parser.add_argument('--calib', required=True)
    parser.add_argument('--out-dir', required=True)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--weights', default='/opt/DROID-SLAM/droid.pth')
    parser.add_argument('--full-slam', action='store_true', help='manter o BA global (SLAM completo)')
    args = parser.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.multiprocessing.set_start_method('spawn')
    stamps, files = read_list(args.rgb_list)
    calib = np.loadtxt(args.calib)
    cfg = droid_args(args.weights)
    droid, times = None, []
    for t, image, intrinsics in image_stream(files, calib):
        if droid is None:
            cfg.image_size = [image.shape[2], image.shape[3]]
            droid = Droid(cfg)
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        droid.track(t, image, intrinsics=intrinsics)
        torch.cuda.synchronize()
        times.append(time.perf_counter() - t0)
    if not args.full_slam:
        droid.backend = lambda *a, **k: None  # terminate() chama backend(7) e backend(12)
    traj = droid.terminate(image_stream(files, calib))

    out = Path(args.out_dir)
    with open(out / 'trajectory_tum.txt', 'w') as f:
        for t, pose in zip(stamps, traj):
            f.write(f'{t:.6f} ' + ' '.join(f'{v:.9f}' for v in pose[:7]) + '\n')
    meta = {'algorithm': 'droid', 'mode': 'slam' if args.full_slam else 'vo', 'seed': args.seed,
            'n_input': len(files), 'n_poses': len(traj), 'mean_ms_per_frame': 1e3 * float(np.mean(times)),
            'peak_gpu_mib': torch.cuda.max_memory_allocated() / 2**20, 'torch': torch.__version__}
    (out / 'algo_meta.json').write_text(json.dumps(meta, indent=2))


if __name__ == '__main__':
    main()

"""Executa o DPVO numa lista de frames e grava trajetória TUM com os timestamps reais.

Diferenças em relação ao demo.py oficial (princeton-vl/DPVO):
  - stride 1 (o demo usa 2), para comparar com os demais métodos quadro a quadro;
  - semente fixada e registrada; tempo por frame e pico de memória medidos;
  - timestamps do dataset em vez do índice do frame.
"""
import argparse
import json
from pathlib import Path
import random
import time

import cv2
import numpy as np
import torch

from dpvo.config import cfg
from dpvo.dpvo import DPVO


def read_list(path):
    stamps, files = [], []
    for line in Path(path).read_text().splitlines():
        if line.strip() and not line.startswith('#'):
            t, f = line.split()[:2]
            stamps.append(float(t))
            files.append(f)
    return stamps, files


@torch.no_grad()
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rgb-list', required=True)
    parser.add_argument('--calib', required=True)
    parser.add_argument('--out-dir', required=True)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--network', default='/opt/DPVO/dpvo.pth')
    parser.add_argument('--config', default='/opt/DPVO/config/default.yaml')
    args = parser.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)
    cfg.merge_from_file(args.config)

    stamps, files = read_list(args.rgb_list)
    fx, fy, cx, cy = np.loadtxt(args.calib)[:4]
    intrinsics = torch.from_numpy(np.array([fx, fy, cx, cy])).cuda()
    slam, times = None, []
    for t, path in enumerate(files):
        image = cv2.imread(path)
        if image is None:
            raise FileNotFoundError(path)
        h, w, _ = image.shape
        image = torch.from_numpy(image[:h - h % 16, :w - w % 16]).permute(2, 0, 1).cuda()
        if slam is None:
            slam = DPVO(cfg, args.network, ht=image.shape[1], wd=image.shape[2], viz=False)
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        slam(t, image, intrinsics)
        torch.cuda.synchronize()
        times.append(time.perf_counter() - t0)

    poses, tstamps = slam.terminate()
    out = Path(args.out_dir)
    with open(out / 'trajectory_tum.txt', 'w') as f:
        for pose, t in zip(poses, tstamps):
            tx, ty, tz, qx, qy, qz, qw = pose[:7]
            f.write(f'{stamps[int(round(float(t)))]:.6f} {tx} {ty} {tz} {qx} {qy} {qz} {qw}\n')
    meta = {'algorithm': 'dpvo', 'seed': args.seed, 'n_input': len(files), 'n_poses': len(poses),
            'mean_ms_per_frame': 1e3 * float(np.mean(times)), 'median_ms_per_frame': 1e3 * float(np.median(times)),
            'peak_gpu_mib': torch.cuda.max_memory_allocated() / 2**20, 'torch': torch.__version__,
            'cuda': torch.version.cuda, 'config': {k: v for k, v in cfg.items()}}
    (out / 'algo_meta.json').write_text(json.dumps(meta, indent=2, default=str))


if __name__ == '__main__':
    main()

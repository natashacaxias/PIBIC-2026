"""Executa o TartanVO numa lista de frames e grava trajetória TUM.

O TartanVO estima a translação só até a escala, e quadro a quadro: sem o arquivo
de poses, a magnitude de cada passo não tem significado. Aqui cada passo é
normalizado para comprimento 1; o evaluate.py aplica a escala por passo do ground
truth igualmente a todos os métodos monoculares (é o que o --pose-file do script
oficial faz). Intrínsecos vêm do --calib (o oficial só tem valores fixos por dataset).
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
from torch.utils.data import DataLoader, Dataset

sys.path.insert(0, '/opt/tartanvo')
from Datasets.transformation import ses2poses_quat  # noqa: E402
from Datasets.utils import Compose, CropCenter, DownscaleFlow, ToTensor, make_intrinsics_layer  # noqa: E402
from TartanVO import TartanVO  # noqa: E402


def read_list(path):
    stamps, files = [], []
    for line in Path(path).read_text().splitlines():
        if line.strip() and not line.startswith('#'):
            t, f = line.split()[:2]
            stamps.append(float(t))
            files.append(f)
    return stamps, files


class PairDataset(Dataset):
    def __init__(self, files, intrinsics, transform):
        self.files, self.intrinsics, self.transform = files, intrinsics, transform

    def __len__(self):
        return len(self.files) - 1

    def __getitem__(self, i):
        img1, img2 = cv2.imread(self.files[i]), cv2.imread(self.files[i + 1])
        h, w, _ = img1.shape
        sample = {'img1': img1, 'img2': img2, 'intrinsic': make_intrinsics_layer(w, h, *self.intrinsics)}
        return self.transform(sample)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rgb-list', required=True)
    parser.add_argument('--calib', required=True)
    parser.add_argument('--out-dir', required=True)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--model', default='tartanvo_1914.pkl')
    parser.add_argument('--image-height', type=int, default=448)
    parser.add_argument('--image-width', type=int, default=640)
    args = parser.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    stamps, files = read_list(args.rgb_list)
    intrinsics = tuple(float(v) for v in np.loadtxt(args.calib)[:4])
    transform = Compose([CropCenter((args.image_height, args.image_width)), DownscaleFlow(), ToTensor()])
    loader = DataLoader(PairDataset(files, intrinsics, transform), batch_size=1, shuffle=False, num_workers=2)

    vo = TartanVO(args.model)  # carrega de /opt/tartanvo/models/
    motions, times = [], []
    for sample in loader:
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        motion, _ = vo.test_batch(sample)
        torch.cuda.synchronize()
        times.append(time.perf_counter() - t0)
        motions.extend(motion)
    motions = np.array(motions)
    norms = np.linalg.norm(motions[:, :3], axis=1, keepdims=True)
    motions[:, :3] = np.divide(motions[:, :3], norms, out=np.zeros_like(motions[:, :3]), where=norms > 1e-12)
    poses = ses2poses_quat(motions)
    if len(poses) != len(stamps):
        raise RuntimeError(f'{len(poses)} poses para {len(stamps)} imagens')

    out = Path(args.out_dir)
    with open(out / 'trajectory_tum.txt', 'w') as f:
        for t, pose in zip(stamps, poses):
            f.write(f'{t:.6f} ' + ' '.join(f'{v:.9f}' for v in pose) + '\n')
    meta = {'algorithm': 'tartanvo', 'seed': args.seed, 'n_input': len(files), 'n_poses': len(poses),
            'translation': 'unit_step_normalized', 'mean_ms_per_frame': 1e3 * float(np.mean(times)),
            'median_ms_per_frame': 1e3 * float(np.median(times)),
            'peak_gpu_mib': torch.cuda.max_memory_allocated() / 2**20, 'torch': torch.__version__,
            'cuda': torch.version.cuda, 'crop': [args.image_height, args.image_width]}
    (out / 'algo_meta.json').write_text(json.dumps(meta, indent=2))


if __name__ == '__main__':
    main()

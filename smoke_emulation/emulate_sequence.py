"""Aplica fumaça homogênea (Koschmieder) a uma sequência RGB-D inteira.

Pareia RGB e profundidade pelo nome do arquivo, grava as imagens com fumaça com
o mesmo nome e um smoke_meta.json com todos os parâmetros. O processo é
determinístico: não há aleatoriedade no modelo homogêneo.

Uso: python emulate_sequence.py --rgb-dir R --depth-dir D --out-dir O --visibility 20
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np

from koschmieder import (
    CONTRAST_THRESHOLD,
    DEFAULT_ATMOSPHERIC_LIGHT,
    LEVELS_VISIBILITY_M,
    apply_smoke,
    beta_from_visibility,
    fill_depth_holes,
    transmission,
)

HERE = Path(__file__).resolve().parent


def code_hash():
    digest = hashlib.sha256()
    for name in ("koschmieder.py", "emulate_sequence.py"):
        digest.update((HERE / name).read_bytes())
    return digest.hexdigest()


def load_depth_m(path, depth_scale, max_depth_m):
    raw = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if raw is None:
        raise FileNotFoundError(f"profundidade ausente: {path}")
    depth = raw.astype(np.float64) / depth_scale
    depth[depth > max_depth_m] = 0.0
    return depth


def emulate_sequence(rgb_dir, depth_dir, out_dir, visibility_m, depth_scale=1000.0,
                     atmospheric_light=DEFAULT_ATMOSPHERIC_LIGHT, max_depth_m=10.0):
    rgb_dir, depth_dir, out_dir = Path(rgb_dir), Path(depth_dir), Path(out_dir)
    frames = sorted(p for p in rgb_dir.iterdir() if p.suffix.lower() == ".png")
    if not frames:
        raise FileNotFoundError(f"nenhum PNG em {rgb_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)
    beta = beta_from_visibility(visibility_m)
    mean_t, holes = [], []
    for rgb_path in frames:
        bgr = cv2.imread(str(rgb_path), cv2.IMREAD_COLOR)
        if bgr is None:
            raise FileNotFoundError(f"imagem ilegível: {rgb_path}")
        depth = load_depth_m(depth_dir / rgb_path.name, depth_scale, max_depth_m)
        if depth.shape != bgr.shape[:2]:
            raise ValueError(f"tamanhos diferentes em {rgb_path.name}: rgb {bgr.shape[:2]} × profundidade {depth.shape}")
        holes.append(float((depth <= 0).mean()))
        mean_t.append(float(transmission(fill_depth_holes(depth), beta).mean()))
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        hazy = apply_smoke(rgb, depth, beta, atmospheric_light)
        cv2.imwrite(str(out_dir / rgb_path.name), cv2.cvtColor(hazy, cv2.COLOR_RGB2BGR))
    meta = {
        "model": "koschmieder_homogeneous",
        "visibility_m": visibility_m,
        "contrast_threshold": CONTRAST_THRESHOLD,
        "beta_per_m": beta,
        "atmospheric_light_rgb": list(atmospheric_light),
        "depth_scale": depth_scale,
        "max_depth_m": max_depth_m,
        "hole_fill": "dilate3x3_then_max",
        "n_frames": len(frames),
        "mean_transmission": {"mean": float(np.mean(mean_t)), "p5": float(np.percentile(mean_t, 5)),
                              "p50": float(np.median(mean_t)), "p95": float(np.percentile(mean_t, 95))},
        "hole_fraction_mean": float(np.mean(holes)),
        "source_rgb_dir": str(rgb_dir),
        "source_depth_dir": str(depth_dir),
        "code_sha256": code_hash(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    (out_dir / "smoke_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rgb-dir", required=True)
    parser.add_argument("--depth-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    level = parser.add_mutually_exclusive_group(required=True)
    level.add_argument("--level", choices=sorted(LEVELS_VISIBILITY_M))
    level.add_argument("--visibility", type=float, help="visibilidade alvo em metros (limiar de 2%%)")
    parser.add_argument("--depth-scale", type=float, default=1000.0, help="unidades do PNG por metro")
    parser.add_argument("--max-depth", type=float, default=10.0, help="profundidade acima disso vira buraco (m)")
    parser.add_argument("--atmospheric-light", type=float, nargs=3, default=DEFAULT_ATMOSPHERIC_LIGHT)
    args = parser.parse_args()
    visibility = args.visibility if args.visibility else LEVELS_VISIBILITY_M[args.level]
    meta = emulate_sequence(args.rgb_dir, args.depth_dir, args.out_dir, visibility, args.depth_scale,
                            tuple(args.atmospheric_light), args.max_depth)
    print(f"{meta['n_frames']} frames, beta={meta['beta_per_m']:.4f}/m, "
          f"transmissão média={meta['mean_transmission']['mean']:.3f} → {args.out_dir}")


if __name__ == "__main__":
    main()

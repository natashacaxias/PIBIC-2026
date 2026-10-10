"""Remoção de névoa/fumaça pelo Dark Channel Prior (He, Sun & Tang, TPAMI 2011).

Baseline de pré-processamento da proposta (NATASHA-17). Refinamento da transmissão
pelo guided filter (He, Sun & Tang, TPAMI 2013), que substitui o soft matting do
artigo original. Parâmetros padrão do artigo: patch 15x15, omega 0.95, t0 0.1,
0,1% de pixels mais brilhantes do dark channel para estimar A.

Numa sequência de vídeo, estimar A quadro a quadro faz o brilho oscilar entre
quadros, o que prejudica métodos fotométricos e de fluxo e mistura efeitos. Por
isso o padrão é um único A por sequência (mediana das estimativas por quadro).

Uso: python dcp.py --in-dir ENTRADA --out-dir SAIDA [--airlight sequence|frame]
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np

DEFAULTS = {"patch": 15, "omega": 0.95, "t0": 0.1, "top_fraction": 0.001, "radius": 60, "eps": 1e-4}


def dark_channel(image, patch=DEFAULTS["patch"]):
    """Mínimo sobre os canais e sobre uma janela patch x patch. image: HxWx3 float."""
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (patch, patch))
    return cv2.erode(image.min(axis=2).astype(np.float32), kernel)


def estimate_atmospheric_light(image, dark, top_fraction=DEFAULTS["top_fraction"]):
    """Entre os pixels mais brilhantes do dark channel, o de maior intensidade na imagem."""
    flat = dark.ravel()
    n = max(1, int(round(flat.size * top_fraction)))
    candidates = np.argpartition(flat, -n)[-n:]
    pixels = image.reshape(-1, 3)[candidates]
    return pixels[np.argmax(pixels.sum(axis=1))].astype(np.float64)


def guided_filter(guide, src, radius=DEFAULTS["radius"], eps=DEFAULTS["eps"]):
    """Guided filter em tons de cinza (He et al., 2013), com filtros de média."""
    size = (2 * radius + 1, 2 * radius + 1)
    mean = lambda x: cv2.boxFilter(x, cv2.CV_64F, size, borderType=cv2.BORDER_REFLECT)  # noqa: E731
    mean_i, mean_p = mean(guide), mean(src)
    cov_ip = mean(guide * src) - mean_i * mean_p
    var_i = mean(guide * guide) - mean_i * mean_i
    a = cov_ip / (var_i + eps)
    b = mean_p - a * mean_i
    return mean(a) * guide + mean(b)


def transmission(image, airlight, omega=DEFAULTS["omega"], patch=DEFAULTS["patch"], radius=DEFAULTS["radius"],
                 eps=DEFAULTS["eps"]):
    raw = 1.0 - omega * dark_channel(image / np.maximum(airlight, 1e-6), patch)
    gray = cv2.cvtColor(image.astype(np.float32), cv2.COLOR_RGB2GRAY).astype(np.float64)
    return np.clip(guided_filter(gray, raw.astype(np.float64), radius, eps), 0.0, 1.0)


def dehaze(rgb, airlight=None, t0=DEFAULTS["t0"], **params):
    """Recupera J = (I - A) / max(t, t0) + A. rgb: HxWx3 uint8. Retorna (uint8, A, t médio)."""
    image = rgb.astype(np.float64) / 255.0
    patch = params.get("patch", DEFAULTS["patch"])
    if airlight is None:
        airlight = estimate_atmospheric_light(image, dark_channel(image, patch),
                                              params.get("top_fraction", DEFAULTS["top_fraction"]))
    t = transmission(image, airlight, params.get("omega", DEFAULTS["omega"]), patch,
                     params.get("radius", DEFAULTS["radius"]), params.get("eps", DEFAULTS["eps"]))
    recovered = (image - airlight) / np.maximum(t, t0)[..., None] + airlight
    return np.clip(np.rint(recovered * 255.0), 0, 255).astype(np.uint8), np.asarray(airlight), float(t.mean())


def sequence_airlight(frames, params, sample_every=10):
    """Mediana das estimativas de A numa amostra de quadros (um A para a sequência inteira)."""
    estimates = []
    for path in frames[::sample_every]:
        image = cv2.cvtColor(cv2.imread(str(path), cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB).astype(np.float64) / 255.0
        estimates.append(estimate_atmospheric_light(image, dark_channel(image, params["patch"]), params["top_fraction"]))
    return np.median(estimates, axis=0)


def dehaze_sequence(in_dir, out_dir, airlight_mode="sequence", **overrides):
    in_dir, out_dir = Path(in_dir), Path(out_dir)
    params = dict(DEFAULTS, **overrides)
    frames = sorted(p for p in in_dir.iterdir() if p.suffix.lower() == ".png")
    if not frames:
        raise FileNotFoundError(f"nenhum PNG em {in_dir}")
    if airlight_mode not in ("sequence", "frame"):
        raise ValueError("airlight_mode deve ser 'sequence' ou 'frame'")
    out_dir.mkdir(parents=True, exist_ok=True)
    fixed = sequence_airlight(frames, params) if airlight_mode == "sequence" else None
    airlights, mean_t = [], []
    for path in frames:
        rgb = cv2.cvtColor(cv2.imread(str(path), cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
        out, airlight, t = dehaze(rgb, fixed, **params)
        airlights.append(airlight)
        mean_t.append(t)
        cv2.imwrite(str(out_dir / path.name), cv2.cvtColor(out, cv2.COLOR_RGB2BGR))
    digest = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    meta = {"method": "dark_channel_prior+guided_filter", "params": params, "airlight_mode": airlight_mode,
            "airlight_rgb_median": np.median(airlights, axis=0).tolist(),
            "airlight_rgb_std": np.std(airlights, axis=0).tolist(),
            "mean_transmission": float(np.mean(mean_t)), "n_frames": len(frames), "source_dir": str(in_dir),
            "code_sha256": digest, "created_at": datetime.now(timezone.utc).isoformat()}
    (out_dir / "dcp_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--in-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--airlight", choices=["sequence", "frame"], default="sequence")
    for name, value in DEFAULTS.items():
        parser.add_argument(f"--{name.replace('_', '-')}", type=type(value), default=value)
    args = parser.parse_args()
    overrides = {name: getattr(args, name) for name in DEFAULTS}
    meta = dehaze_sequence(args.in_dir, args.out_dir, args.airlight, **overrides)
    print(f"{meta['n_frames']} quadros, A={np.round(meta['airlight_rgb_median'], 3)}, "
          f"t médio={meta['mean_transmission']:.3f} → {args.out_dir}")


if __name__ == "__main__":
    main()

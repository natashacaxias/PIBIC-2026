"""Compara fumaça sintética com fumaça real por métricas de imagem (NATASHA-12).

  python validate_smoke.py --synthetic SINTETICO --real REAL --out SAIDA \
      [--clean LIMPO] [--real-center-crop 0.6] [--size 640 480] [--max-frames 300] [--brisque]

- --clean: quadros limpos com os mesmos nomes dos sintéticos → SSIM (com referência).
- --real-center-crop: recorta o centro dos quadros reais (as câmeras do SubT-MRS são
  fisheye; o centro tem menos distorção) antes de redimensionar para --size.

Saídas: metrics_frames.csv (por quadro), comparison.csv (por métrica: medianas,
teste KS e distância de Wasserstein normalizada pelo IQR do conjunto real) e report.md.
Distribuições parecidas (KS pequeno) não provam realismo; diferenças grandes indicam
que o nível ou a cor da fumaça precisam de ajuste.
"""

import argparse
import csv
from pathlib import Path

import cv2
import numpy as np
from scipy import stats

from image_quality import frame_metrics, ssim, to_gray


def list_frames(directory, max_frames):
    frames = sorted(p for p in Path(directory).iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg"))
    if max_frames and len(frames) > max_frames:
        frames = [frames[i] for i in np.linspace(0, len(frames) - 1, max_frames).astype(int)]
    return frames


def load_rgb(path, size=None, center_crop=None):
    bgr = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if bgr is None:
        raise FileNotFoundError(path)
    if center_crop:
        h, w = bgr.shape[:2]
        ch, cw = int(h * center_crop), int(w * center_crop)
        bgr = bgr[(h - ch) // 2:(h + ch) // 2, (w - cw) // 2:(w + cw) // 2]
    if size:
        bgr = cv2.resize(bgr, tuple(size), interpolation=cv2.INTER_AREA)
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)


def measure(directory, label, size, max_frames, with_brisque, center_crop=None, clean_dir=None):
    rows = []
    for path in list_frames(directory, max_frames):
        rgb = load_rgb(path, size, center_crop)
        row = {"set": label, "file": path.name, **frame_metrics(rgb, with_brisque)}
        if clean_dir is not None:
            clean_path = Path(clean_dir) / path.name
            row["ssim_vs_clean"] = ssim(to_gray(load_rgb(clean_path, size)), to_gray(rgb)) if clean_path.exists() else None
        rows.append(row)
    return rows


def compare(synthetic, real):
    metrics = [k for k in synthetic[0] if k not in ("set", "file", "ssim_vs_clean") and synthetic[0][k] is not None]
    out = []
    for name in metrics:
        a = np.array([r[name] for r in synthetic], dtype=float)
        b = np.array([r[name] for r in real], dtype=float)
        ks = stats.ks_2samp(a, b)
        iqr = float(np.subtract(*np.percentile(b, [75, 25]))) or 1.0
        out.append({"metric": name, "median_synthetic": float(np.median(a)), "median_real": float(np.median(b)),
                    "ks_statistic": float(ks.statistic), "ks_p": float(ks.pvalue),
                    "wasserstein_over_iqr_real": float(stats.wasserstein_distance(a, b) / iqr)})
    return out


def write_csv(rows, path):
    fields = sorted({k for r in rows for k in r}, key=lambda k: (k not in ("set", "file"), k))
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def report(comparison, synthetic, args):
    lines = ["# Validação da fumaça emulada", "",
             f"Sintético: `{args.synthetic}` ({len(synthetic)} quadros) · Real: `{args.real}` · tamanho {args.size}"
             + (f" · recorte central do real {args.real_center_crop}" if args.real_center_crop else ""), "",
             "| métrica | mediana sintético | mediana real | KS | p (KS) | Wasserstein / IQR real |",
             "|---|---|---|---|---|---|"]
    lines += [f"| {c['metric']} | {c['median_synthetic']:.4g} | {c['median_real']:.4g} | {c['ks_statistic']:.3f} | "
              f"{c['ks_p']:.3g} | {c['wasserstein_over_iqr_real']:.3f} |" for c in comparison]
    ssims = [r["ssim_vs_clean"] for r in synthetic if r.get("ssim_vs_clean") is not None]
    if ssims:
        lines += ["", f"SSIM sintético × limpo: mediana {np.median(ssims):.3f} "
                      f"(p5 {np.percentile(ssims, 5):.3f}, p95 {np.percentile(ssims, 95):.3f}, n = {len(ssims)})."]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--synthetic", required=True)
    parser.add_argument("--real", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--clean")
    parser.add_argument("--real-center-crop", type=float)
    parser.add_argument("--size", type=int, nargs=2, default=[640, 480], metavar=("W", "H"))
    parser.add_argument("--max-frames", type=int, default=300)
    parser.add_argument("--brisque", action="store_true", help="requer o pacote piq (PyTorch)")
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    synthetic = measure(args.synthetic, "synthetic", args.size, args.max_frames, args.brisque, clean_dir=args.clean)
    real = measure(args.real, "real", args.size, args.max_frames, args.brisque, center_crop=args.real_center_crop)
    write_csv(synthetic + real, out / "metrics_frames.csv")
    comparison = compare(synthetic, real)
    write_csv(comparison, out / "comparison.csv")
    (out / "report.md").write_text(report(comparison, synthetic, args), encoding="utf-8")
    print(f"{len(synthetic)} sintéticos × {len(real)} reais → {out / 'report.md'}")


if __name__ == "__main__":
    main()

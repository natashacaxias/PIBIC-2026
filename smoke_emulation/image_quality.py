"""Métricas de imagem para validar a fumaça emulada (NATASHA-12).

Duas finalidades diferentes, que não devem ser misturadas:
  - COM referência (SSIM): quanto a fumaça sintética degrada o quadro limpo
    correspondente. Só faz sentido com o par alinhado (limpo, com fumaça).
  - SEM referência (contraste RMS, dark channel, densidade de bordas, entropia,
    pontos ORB, BRISQUE opcional): comparar a DISTRIBUIÇÃO das imagens sintéticas
    com a de fumaça real (ex.: SubT-MRS "Smoke Room"), que não tem versão limpa.

Os pontos ORB aproximam o que um método de VO baseado em features "enxerga".
"""

import cv2
import numpy as np

from dcp import dark_channel

ORB = cv2.ORB_create(nfeatures=2000, fastThreshold=20)


def to_gray(rgb):
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)


def rms_contrast(gray):
    """Desvio padrão da intensidade normalizada em [0, 1]."""
    return float((gray.astype(np.float64) / 255.0).std())


def dark_channel_mean(rgb, patch=15):
    """Média do dark channel: perto de 0 sem névoa; cresce com a fumaça (He et al., 2011)."""
    return float(dark_channel(rgb.astype(np.float64) / 255.0, patch).mean())


def edge_density(gray, threshold=0.1):
    """Fração de pixels com magnitude de gradiente (Sobel, normalizada) acima do limiar."""
    g = gray.astype(np.float64) / 255.0
    magnitude = np.hypot(cv2.Sobel(g, cv2.CV_64F, 1, 0, ksize=3), cv2.Sobel(g, cv2.CV_64F, 0, 1, ksize=3)) / 4.0
    return float((magnitude > threshold).mean())


def entropy(gray):
    hist = np.bincount(gray.ravel(), minlength=256).astype(np.float64)
    p = hist[hist > 0] / hist.sum()
    return float(-(p * np.log2(p)).sum())


def orb_keypoints(gray):
    return len(ORB.detect(gray, None))


def ssim(a, b, sigma=1.5, k1=0.01, k2=0.03):
    """SSIM médio entre duas imagens em tons de cinza uint8 (Wang et al., 2004), janela gaussiana."""
    x, y = a.astype(np.float64) / 255.0, b.astype(np.float64) / 255.0
    blur = lambda img: cv2.GaussianBlur(img, (11, 11), sigma)  # noqa: E731
    mu_x, mu_y = blur(x), blur(y)
    var_x = blur(x * x) - mu_x ** 2
    var_y = blur(y * y) - mu_y ** 2
    cov = blur(x * y) - mu_x * mu_y
    c1, c2 = k1 ** 2, k2 ** 2
    num = (2 * mu_x * mu_y + c1) * (2 * cov + c2)
    den = (mu_x ** 2 + mu_y ** 2 + c1) * (var_x + var_y + c2)
    return float((num / den).mean())


def brisque(rgb):
    """BRISQUE via piq, se instalado (menor = melhor). Retorna None sem o pacote."""
    try:
        import piq
        import torch
    except ImportError:
        return None
    tensor = torch.from_numpy(rgb.astype(np.float32) / 255.0).permute(2, 0, 1)[None]
    return float(piq.brisque(tensor, data_range=1.0))


def frame_metrics(rgb, with_brisque=False):
    gray = to_gray(rgb)
    out = {"rms_contrast": rms_contrast(gray), "dark_channel_mean": dark_channel_mean(rgb),
           "edge_density": edge_density(gray), "entropy": entropy(gray), "orb_keypoints": orb_keypoints(gray)}
    if with_brisque:
        out["brisque"] = brisque(rgb)
    return out

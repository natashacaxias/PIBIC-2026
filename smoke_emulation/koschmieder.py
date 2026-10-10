"""Emulação de fumaça/névoa homogênea pelo modelo de espalhamento de Koschmieder.

    I(x) = J(x) * t(x) + A * (1 - t(x)),   t(x) = exp(-beta * d(x))

J é a imagem limpa, d a profundidade em metros, A a luz atmosférica (cor da
fumaça) e beta o coeficiente de extinção. A visibilidade meteorológica V se
relaciona com beta pelo limiar de contraste de 2%: V = -ln(0.02) / beta ≈ 3.912 / beta.

Limitações assumidas (ver proposta, etapa 1): meio homogêneo, espalhamento
isotrópico, sem distinção física entre fumaça e névoa, A constante na cena.
"""

import math

import numpy as np

CONTRAST_THRESHOLD = 0.02

# Níveis da proposta, em visibilidade alvo (metros).
LEVELS_VISIBILITY_M = {"leve": 60.0, "moderada": 20.0, "densa": 6.0}

# Fumaça de queimada tende ao cinza claro; valor provisório, a calibrar com SubT-MRS.
DEFAULT_ATMOSPHERIC_LIGHT = (0.80, 0.80, 0.80)


def beta_from_visibility(visibility_m, contrast_threshold=CONTRAST_THRESHOLD):
    if visibility_m <= 0:
        raise ValueError("visibility_m deve ser positiva")
    return -math.log(contrast_threshold) / visibility_m


def visibility_from_beta(beta, contrast_threshold=CONTRAST_THRESHOLD):
    if beta <= 0:
        raise ValueError("beta deve ser positivo")
    return -math.log(contrast_threshold) / beta


def _dilate_max(values):
    padded = np.pad(values, 1, constant_values=-np.inf)
    h, w = values.shape
    return np.max([padded[i:i + h, j:j + w] for i in range(3) for j in range(3)], axis=0)


def fill_depth_holes(depth_m, fill_value=None, method="dilate", max_iterations=50):
    """Substitui pixels sem medida (<= 0 ou não finitos).

    Deixar d=0 produziria "janelas" sem fumaça. method="dilate" propaga o maior
    vizinho válido (3x3) iterativamente: buracos de reprojeção RGB-D ficam nas
    bordas de objetos e o fundo é o valor mais plausível. O que sobra após
    max_iterations, ou tudo com method="max", recebe fill_value (padrão: a maior
    profundidade válida, pois buracos grandes costumam ser superfícies distantes
    ou reflexivas).
    """
    depth = np.asarray(depth_m, dtype=np.float64)
    invalid = ~np.isfinite(depth) | (depth <= 0)
    if not invalid.any():
        return depth.copy()
    if invalid.all():
        raise ValueError("mapa de profundidade sem nenhum pixel válido")
    filled = np.where(invalid, -np.inf, depth)
    if method == "dilate":
        for _ in range(max_iterations):
            grown = _dilate_max(filled)
            newly = invalid & np.isfinite(grown)
            if not newly.any():
                break
            filled[newly] = grown[newly]
            invalid &= ~newly
            if not invalid.any():
                break
    elif method != "max":
        raise ValueError(f"método de preenchimento desconhecido: {method}")
    if invalid.any():
        filled[invalid] = float(depth[np.isfinite(depth) & (depth > 0)].max()) if fill_value is None else fill_value
    return filled


def transmission(depth_m, beta):
    return np.exp(-beta * np.asarray(depth_m, dtype=np.float64))


def mean_transmission(depth_m, beta):
    """Transmissão média da cena, usada para relatar a "densidade efetiva" por sequência."""
    return float(transmission(fill_depth_holes(depth_m), beta).mean())


def beta_for_mean_transmission(depth_m, target, tolerance=1e-6):
    """Beta que produz a transmissão média `target` (0 < target < 1) na profundidade dada."""
    if not 0.0 < target < 1.0:
        raise ValueError("target deve estar entre 0 e 1")
    depth = fill_depth_holes(depth_m)
    low, high = 0.0, 1.0
    while transmission(depth, high).mean() > target:
        high *= 2.0
    while high - low > tolerance:
        mid = (low + high) / 2.0
        if transmission(depth, mid).mean() > target:
            low = mid
        else:
            high = mid
    return (low + high) / 2.0


def apply_smoke(rgb, depth_m, beta, atmospheric_light=DEFAULT_ATMOSPHERIC_LIGHT):
    """Aplica o modelo de Koschmieder a uma imagem RGB.

    rgb: HxWx3, uint8 [0, 255] ou float [0, 1]; o tipo de saída acompanha o de entrada.
    depth_m: HxW em metros (converter antes pelo fator de escala do dataset).
    atmospheric_light: 3 valores em [0, 1].
    """
    rgb = np.asarray(rgb)
    if rgb.ndim != 3 or rgb.shape[2] != 3:
        raise ValueError("rgb deve ter formato HxWx3")
    depth = np.asarray(depth_m)
    if depth.shape != rgb.shape[:2]:
        raise ValueError("depth_m deve ter a mesma altura e largura de rgb")

    is_uint8 = rgb.dtype == np.uint8
    clean = rgb.astype(np.float64) / 255.0 if is_uint8 else rgb.astype(np.float64)
    a = np.asarray(atmospheric_light, dtype=np.float64).reshape(1, 1, 3)

    t = transmission(fill_depth_holes(depth), beta)[..., None]
    hazy = clean * t + a * (1.0 - t)

    if is_uint8:
        return np.clip(np.rint(hazy * 255.0), 0, 255).astype(np.uint8)
    return np.clip(hazy, 0.0, 1.0)

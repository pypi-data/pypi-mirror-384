from __future__ import annotations
import math


__all__ = ["clamp01", "radial_d_to_nearest_apex"]


def clamp01(x: float) -> float:
    if x < 0.0: return 0.0
    if x > 1.0: return 1.0
    return x


def radial_d_to_nearest_apex(mu: float, lam: float) -> float:
    sqrt_half = math.sqrt(0.5)
    d_v = ((1.0 - mu)**2 + (0.0 - lam)**2) ** 0.5
    d_f = ((0.0 - mu)**2 + (1.0 - lam)**2) ** 0.5
    return min(d_v, d_f) / sqrt_half
from __future__ import annotations
from typing import Dict, TypedDict


__all__ = ["Complete"]


class Complete(TypedDict):
    # parâmetros
    FL: float; FtC: float; FD: float
    VSSC: float; VICC: float; VSSCT: float; VICCT: float
    VlV: float; VlF: float; L: float
    # entradas
    mu: float; lam: float; mu_p: float; lam_p: float
    # graus e derivados
    gc: float; gct: float; gct_adj: float
    d: float; D: float; gcr: float
    # evidências
    muE: float; muE_p: float; muECT: float; muER: float; phi: float; phiE: float
    label: str
    regions: dict[str, bool]
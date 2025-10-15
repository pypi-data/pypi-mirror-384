from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ThresholdsAsym:
    ftc_pos: float; ftc_neg: float
    fd_pos: float;  fd_neg: float
    eps: float = 1e-12

def classify_12_regions_asymmetric(gc: float, gct: float, th: ThresholdsAsym) -> str:
    eps = th.eps

    # 0) centro exato
    if abs(gc) <= eps and abs(gct) <= eps:
        return "I"

    # 1) certeza dominante (assimétrica)
    if gc >= th.ftc_pos:  # V
        return "V"
    if gc <= -th.ftc_neg: # F
        return "F"

    # 2) contradição dominante (assimétrica)
    if gct >= th.fd_pos:   # ┬
        return "┬"
    if gct <= -th.fd_neg:  # ┴
        return "┴"

    # 3) quadrado central
    in_central = (gc < th.ftc_pos and gc > -th.ftc_neg and gct < th.fd_pos and gct > -th.fd_neg)
    if in_central:
        a, b = abs(gc), abs(gct)
        if b > a:
            # contradição domina
            return "Q┬→V" if gc >= 0 else "Q┬→F"
        elif a > b:
            # certeza domina
            if gc >= 0:
                return "QV→┬" if gct >= 0 else "QV→┴"
            else:
                return "QF→┬" if gct >= 0 else "QF→┴"
        else:
            # empate: preferir QV/QF e setar seta pelo sinal de GCT
            if gc >= 0:
                return "QV→┬" if gct >= 0 else "QV→┴"
            else:
                return "QF→┬" if gct >= 0 else "QF→┴"

    # fallback
    return "I"


def regions_flags(label: str) -> dict:
    # booleans por região para paridade com estruturas antigas
    keys = ["V","F","┬","┴","Q┬→V","Q┬→F","QV→┬","QF→┬","QV→┴","QF→┴","QV","QF","I"]
    return {k: (k == label) for k in keys}
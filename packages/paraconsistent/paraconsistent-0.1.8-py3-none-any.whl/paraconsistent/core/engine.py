from __future__ import annotations
from types import SimpleNamespace
from typing import Dict, Tuple


from paraconsistent.core.metrics import clamp01, radial_d_to_nearest_apex
from paraconsistent.core.config import BlockParams
from paraconsistent.core.types import Complete
from paraconsistent.core.labels import ThresholdsAsym, classify_12_regions_asymmetric, regions_flags


__all__ = ["ParaconsistentEngine"]


class ParaconsistentEngine:


    @staticmethod
    def preprocess_inputs(mu: float, lam: float, P: BlockParams) -> Tuple[float, float, float, float]:
        mu = clamp01(mu)
        lam = clamp01(lam)
        mu_p = clamp01(mu / P.FL if P.FL != 0 else mu)
        lam_p = clamp01(lam / P.FL if P.FL != 0 else lam)
        return mu, lam, mu_p, lam_p


    @staticmethod
    def core_degrees(mu: float, lam: float) -> Tuple[float, float]:
        gc = mu - lam
        gct = mu + lam - 1.0
        return gc, gct


    @staticmethod
    def adjust_contradiction(gct: float, P: BlockParams) -> float:
        return max(-1.0, min(1.0, gct + P.FL * (P.VSSCT + P.VICCT) * 0.5))


    @staticmethod
    def geometry(mu: float, lam: float, gc: float) -> Tuple[float, float, float]:
        d = radial_d_to_nearest_apex(mu, lam)
        D = d
        gcr = (1.0 - D) * (1.0 if gc >= 0 else -1.0)
        return d, D, gcr

    @staticmethod
    def classify(ftc: float, fd: float,vssc: float, vssct:float,vicc:float, vicct:float,vlv:float,vlf:float, gc: float, gct: float) -> Tuple[str, dict]:
        FtC_pos = max(ftc, abs(vssc))   # GC>0
        FtC_neg = max(ftc, abs(vicc))   # GC<0
        FD_pos  = max(fd,  abs(vssct))  # GCT>0
        FD_neg  = max(fd,  abs(vicct))  # GCT<0

        FtC_pos_eff = max(FtC_pos - vlv, ftc)  # nunca abaixo de FtC
        FtC_neg_eff = max(FtC_neg - vlf, ftc)
        label = classify_12_regions_asymmetric(
            gc, gct,
            ThresholdsAsym(
                ftc_pos=FtC_pos_eff,
                ftc_neg=FtC_neg_eff,
                fd_pos=FD_pos,
                fd_neg=FD_neg,
            )
        )
        regs = regions_flags(label)
        return label,regs

    @staticmethod
    def evidences(mu_p: float, lam_p: float, gc: float, gct: float, gcr: float) -> Dict[str, float]:
        phi = 1.0 - abs(gct)
        muE = (gc + 1.0) / 2.0
        muECT = (gct + 1.0) / 2.0
        muER = (gc + gct + 1.0) / 2.0  
        muE_p = ((mu_p - lam_p) + 1.0) / 2.0
        phiE = phi
        return {"phi": phi, "muE": muE, "muECT": muECT, "muER": muER, "muE_p": muE_p, "phiE": phiE}



    @classmethod
    def compute(cls, *, mu: float, lam: float, params: BlockParams) -> SimpleNamespace:
        mu, lam, mu_p, lam_p = cls.preprocess_inputs(mu, lam, params)
        gc, gct = cls.core_degrees(mu, lam)
        gct_adj = cls.adjust_contradiction(gct, params)
        d, D, gcr = cls.geometry(mu, lam, gc)
        ev = cls.evidences(mu_p, lam_p, gc, gct, gcr)
        label,regs_flag = cls.classify(params.FtC, params.FD, params.VSSC, params.VSSCT, params.VICC, params.VICCT, params.VlV, params.VlF, gc, gct)
        complete: Complete = {
            # parâmetros
            "FL": params.FL, "FtC": params.FtC, "FD": params.FD,
            "VSSC": params.VSSC, "VICC": params.VICC, "VSSCT": params.VSSCT, "VICCT": params.VICCT,
            "VlV": params.VlV, "VlF": params.VlF, "L": params.L,
            # entradas
            "mu": mu, "lam": lam, "mu_p": mu_p, "lam_p": lam_p,
            # graus / derivados
            "gc": gc, "gct": gct, "gct_adj": gct_adj,
            "d": d, "D": D, "gcr": gcr,
            "label": label, "Regions": regs_flag,
            # evidências
            **ev,
        }
        return SimpleNamespace(**complete)
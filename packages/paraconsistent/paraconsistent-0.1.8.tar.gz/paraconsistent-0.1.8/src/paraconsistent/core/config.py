# mrn/core/config.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional
import warnings

__all__ = ["BlockParams", "DEFAULT_PARAMS", "validate_and_merge"]

@dataclass(frozen=True)
class BlockParams:
    FL: float   = 1.0
    FtC: float  = 0.50
    FD: float   = 0.0
    VSSC: float  = 0.50
    VICC: float  = -0.50
    VSSCT: float = 0.50
    VICCT: float = -0.50
    VlV: float  = 0.50
    VlF: float  = 0.50
    L: float    = 0.05

DEFAULT_PARAMS = BlockParams()

_NUMERIC_FIELDS = {f.name for f in BlockParams.__dataclass_fields__.values()}

def _warn(msg: str):
    warnings.warn(msg, RuntimeWarning, stacklevel=2)

def _clamp01(name: str, v: float) -> float:
    if v < 0.0 or v > 1.0:
        _warn(f"{name} fora de [0,1]: {v} — será truncado")
    return 0.0 if v < 0.0 else 1.0 if v > 1.0 else v

def _clamp11(name: str, v: float) -> float:
    if v < -1.0 or v > 1.0:
        _warn(f"{name} fora de [-1,1]: {v} — será truncado")
    return -1.0 if v < -1.0 else 1.0 if v > 1.0 else v

def _pos(name: str, v: float) -> float:
    if v <= 0.0:
        _warn(f"{name} deve ser > 0; ajustado para 1.0 (era {v})")
        return 1.0
    return v

_CLAMP01_FIELDS = {"FtC", "FD", "VlV", "VlF", "L"}
_CLAMP11_FIELDS = {"VSSC", "VICC", "VSSCT", "VICCT"}
_POSITIVE_FIELDS = {"FL"}

def validate_and_merge(overrides: Optional[Dict[str, Any]] = None) -> BlockParams:
    """Valida e mescla overrides com defaults. Tolerante a None/mappings e
    nunca referencia variáveis fora de escopo em mensagens de erro."""
    data = DEFAULT_PARAMS.__dict__.copy()

    # normaliza overrides
    if overrides is None:
        overrides = {}
    elif not isinstance(overrides, dict):
        try:
            overrides = dict(overrides)  # tenta converter mapping-like
        except Exception:
            _warn(f"overrides não é dict/mapping; ignorado: {type(overrides)!r}")
            overrides = {}

    for key, value in overrides.items():
        if key not in _NUMERIC_FIELDS:
            raise AttributeError(f"Parâmetro inválido: {key}")
        try:
            data[key] = float(value)
        except Exception as e:
            # usa key/value locais (evita UnboundLocalError)
            raise TypeError(f"Parâmetro {key} deve ser numérico: {value!r}") from e

    # aplica clamps/validações
    for key in list(data.keys()):
        val = data[key]
        if key in _CLAMP01_FIELDS:
            data[key] = _clamp01(key, val)
        elif key in _CLAMP11_FIELDS:
            data[key] = _clamp11(key, val)
        elif key in _POSITIVE_FIELDS:
            data[key] = _pos(key, val)

    return BlockParams(**data)

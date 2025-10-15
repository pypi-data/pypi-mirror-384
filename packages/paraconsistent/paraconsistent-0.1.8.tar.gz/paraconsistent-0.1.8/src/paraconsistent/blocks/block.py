from __future__ import annotations
from types import SimpleNamespace
from typing import Optional, Dict

from paraconsistent.core.config import BlockParams, validate_and_merge
from paraconsistent.core.engine import ParaconsistentEngine
from paraconsistent.core.metrics import clamp01
from paraconsistent.core.types import Complete

__all__ = ["ParaconsistentBlock"]

class ParaconsistentBlock:
    """Wrapper fino em torno do Engine.
    - Mantém ergonomia b.input.mu, b.config.FL e b.complete.
    - Cacheia o resultado (lazy) e invalida ao alterar input/config.
    """

    class _InputProxy:
        def __init__(self, owner: "ParaconsistentBlock"):
            self._o = owner
        @property
        def mu(self) -> float: return self._o._mu_in
        @mu.setter
        def mu(self, v: float) -> None:
            self._o._mu_in = clamp01(float(v)); self._o._dirty = True
        @property
        def lam(self) -> float: return self._o._lam_in
        @lam.setter
        def lam(self, v: float) -> None:
            self._o._lam_in = clamp01(float(v)); self._o._dirty = True
        def __call__(self, *, mu: Optional[float]=None, lam: Optional[float]=None):
            if mu is not None: self.mu = mu
            if lam is not None: self.lam = lam
            return self

    class _ConfigProxy:
        def __init__(self, owner: "ParaconsistentBlock"):
            self._o = owner
        def __getattr__(self, name):
            return getattr(self._o._params, name)
        def __setattr__(self, name, value):
            if name == "_o": return super().__setattr__(name, value)
            self._o.set_params(**{name: value})

    def __init__(self, *, mu: Optional[float]=None, lam: Optional[float]=None, **param_overrides):
        """Construtor minimalista (sem block_id).
        Args:
            mu: valor inicial de mu (0..1)
            lam: valor inicial de lam (0..1)
            **param_overrides: sobrescritas de parâmetros (ver BlockParams)
        """
        self._mu_in = float(mu) if mu is not None else 0.0
        self._lam_in = float(lam) if lam is not None else 0.0
        self._params: BlockParams = validate_and_merge(param_overrides)

        self._dirty = True
        self._complete_ns: Optional[SimpleNamespace] = None

        self.input  = ParaconsistentBlock._InputProxy(self)
        self.config = ParaconsistentBlock._ConfigProxy(self)

    def set_params(self, **kwargs) -> None:
        self._params = validate_and_merge({**self._params.__dict__, **kwargs})
        self._dirty = True

    @property
    def complete(self) -> SimpleNamespace:
        if self._dirty or self._complete_ns is None:
            self._complete_ns = ParaconsistentEngine.compute(
                mu=self._mu_in, lam=self._lam_in, params=self._params
            )
            self._dirty = False
        return self._complete_ns

    def to_dict(self) -> Complete:
        # garante tipagem forte do dicionário de saída
        return Complete(**self.complete.__dict__)  # type: ignore[call-arg]

    def print_complete(self, *, sort: bool = True, precision: int = 4, prefix: str = "") -> None:
        data: Dict[str, float | str] = dict(self.complete.__dict__)
        items = sorted(data.items()) if sort else data.items()
        for k, v in items:
            if isinstance(v, (int, float)):
                print(f"{prefix}{k}: {v:.{precision}f}")
            else:
                print(f"{prefix}{k}: {v}")

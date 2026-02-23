"""Unified GKSL interface to compose sector contributions into H and D.

This wrapper sits on top of the 2-flavor solver and allows registering
sector-provided Hamiltonian or mass-squared corrections and damping terms.

Designed to be minimal and safe to use inside `integration_artifacts/`.
"""
from __future__ import annotations
import math
import numpy as np
from typing import Callable, List

try:
    # Prefer a cleaned solver copy if present
    from mastereq.gk_sl_solver_clean import (
        integrate_rho,
        vacuum_hamiltonian_2flavor,
        KCONST,
    )
except Exception:
    from mastereq.gk_sl_solver import (
        integrate_rho,
        vacuum_hamiltonian_2flavor,
        KCONST,
    )

# Type aliases
MatrixFn = Callable[[float, float], np.ndarray]  # (L_km, E_GeV) -> 2x2 matrix
DampingFn = Callable[[float, float, np.ndarray], np.ndarray]  # (L,E,rho) -> D(rho)


class UnifiedGKSL:
    def __init__(self, dm2: float, theta: float):
        self.dm2 = float(dm2)
        self.theta = float(theta)
        # sectors that provide mass-basis delta M^2 matrices
        self.mass_sector_fns: List[Callable[[float, float], np.ndarray]] = []
        # sectors that provide flavor-basis Hamiltonian directly (units 1/km)
        self.flav_sector_fns: List[MatrixFn] = []
        # damping contributions (they return a D matrix same shape as rho)
        self.damping_fns: List[DampingFn] = []

    def add_mass_sector(self, fn: Callable[[float, float], np.ndarray]) -> None:
        """Register a sector providing a mass-basis delta M^2 matrix."""
        self.mass_sector_fns.append(fn)

    def add_flavor_sector(self, fn: MatrixFn) -> None:
        """Register a sector providing a flavor-basis Hamiltonian term (1/km units)."""
        self.flav_sector_fns.append(fn)

    def add_damping(self, fn: DampingFn) -> None:
        self.damping_fns.append(fn)

    def _U_matrix(self) -> np.ndarray:
        c = math.cos(self.theta)
        s = math.sin(self.theta)
        return np.array([[c, s], [-s, c]], dtype=complex)

    def _mass_to_flavor(self, deltaM2_mass: np.ndarray, E_GeV: float) -> np.ndarray:
        """Convert a mass-basis delta M^2 matrix into a flavor-basis Hamiltonian (1/km).

        Uses the same rotation as the vacuum Hamiltonian builder: delta/(2E) * KCONST rotated by U.
        """
        U = self._U_matrix()
        delta_mass_over_2E = deltaM2_mass / (2.0 * max(E_GeV, 1e-12))
        delta_flav = U @ delta_mass_over_2E @ U.conj().T
        delta_flav *= KCONST
        return delta_flav

    def build_Hfn(self) -> Callable[[float, float], np.ndarray]:
        def Hfn(L_km: float, E_GeV: float) -> np.ndarray:
            Hvac = vacuum_hamiltonian_2flavor(self.dm2, self.theta, E_GeV)
            Htot = Hvac.copy()
            # add mass-basis sectors converted to flavor
            for f in self.mass_sector_fns:
                deltaM2_mass = f(L_km, E_GeV)
                if deltaM2_mass is None:
                    continue
                Htot = Htot + self._mass_to_flavor(deltaM2_mass, E_GeV)
            # add flavor-basis sectors directly
            for f in self.flav_sector_fns:
                Hterm = f(L_km, E_GeV)
                if Hterm is None:
                    continue
                Htot = Htot + Hterm
            return Htot
        return Hfn

    def build_Dfn(self) -> Callable[[float, float, np.ndarray], np.ndarray]:
        def Dfn(L_km: float, E_GeV: float, rho: np.ndarray) -> np.ndarray:
            if not self.damping_fns:
                return np.zeros_like(rho, dtype=complex)
            Dtot = np.zeros_like(rho, dtype=complex)
            for f in self.damping_fns:
                Dpart = f(L_km, E_GeV, rho)
                if Dpart is None:
                    continue
                Dtot = Dtot + Dpart
            return Dtot
        return Dfn

    def integrate(self, L_km: float, E_GeV: float, steps: int = 500) -> np.ndarray:
        Hfn = self.build_Hfn()
        Dfn = self.build_Dfn()
        return integrate_rho(L_km, E_GeV, Hfn, Dfn, steps=steps)


__all__ = ["UnifiedGKSL"]

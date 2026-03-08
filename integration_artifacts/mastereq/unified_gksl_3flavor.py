"""Unified 3-flavor GKSL interface.

This mirrors `unified_gksl.UnifiedGKSL` (2-flavor) but uses the 3-flavor solver.

- Vacuum Hamiltonian from PMNS parameters + dm21/dm31
- Optional sector hooks:
    * mass-sector delta M^2 in mass basis (3x3, eV^2)
    * flavor-sector Hamiltonian terms in 1/km (3x3)
    * damping terms D(rho)

This is the basis for WEAK runners that genuinely evolve internal neutrino
state dynamics (3-flavor + MSW + decoherence).
"""

from __future__ import annotations

import numpy as np
from typing import Callable, List

from mastereq.gk_sl_solver_3flavor import (
    Flavor,
    integrate_rho_3flavor,
    pmns_matrix,
    vacuum_hamiltonian_3flavor,
    KCONST,
)

MatrixFn3 = Callable[[float, float], np.ndarray]  # (L_km, E_GeV) -> 3x3
DampingFn3 = Callable[[float, float, np.ndarray], np.ndarray]  # (L,E,rho)->3x3


class UnifiedGKSL3:
    def __init__(
        self,
        *,
        dm21: float,
        dm31: float,
        theta12: float,
        theta13: float,
        theta23: float,
        delta_cp: float,
        flavor_in: Flavor = "mu",
    ):
        self.dm21 = float(dm21)
        self.dm31 = float(dm31)
        self.theta12 = float(theta12)
        self.theta13 = float(theta13)
        self.theta23 = float(theta23)
        self.delta_cp = float(delta_cp)
        self.flavor_in: Flavor = flavor_in

        self.mass_sector_fns: List[Callable[[float, float], np.ndarray]] = []
        self.flav_sector_fns: List[MatrixFn3] = []
        self.damping_fns: List[DampingFn3] = []

    def add_mass_sector(self, fn: Callable[[float, float], np.ndarray]) -> None:
        self.mass_sector_fns.append(fn)

    def add_flavor_sector(self, fn: MatrixFn3) -> None:
        self.flav_sector_fns.append(fn)

    def add_damping(self, fn: DampingFn3) -> None:
        self.damping_fns.append(fn)

    def _mass_to_flavor(self, deltaM2_mass: np.ndarray, E_GeV: float) -> np.ndarray:
        U = pmns_matrix(self.theta12, self.theta13, self.theta23, self.delta_cp)
        delta_mass_over_2E = deltaM2_mass / (2.0 * max(float(E_GeV), 1e-12))
        delta_flav = U @ delta_mass_over_2E @ U.conj().T
        delta_flav *= KCONST
        return delta_flav

    def build_Hfn(self) -> Callable[[float, float], np.ndarray]:
        def Hfn(L_km: float, E_GeV: float) -> np.ndarray:
            Hvac = vacuum_hamiltonian_3flavor(
                self.dm21, self.dm31, self.theta12, self.theta13, self.theta23, self.delta_cp, E_GeV
            )
            Htot = Hvac.copy()

            for f in self.mass_sector_fns:
                deltaM2_mass = f(L_km, E_GeV)
                if deltaM2_mass is None:
                    continue
                Htot = Htot + self._mass_to_flavor(deltaM2_mass, E_GeV)

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

    def integrate(self, L_km: float, E_GeV: float, *, steps: int = 1000) -> np.ndarray:
        Hfn = self.build_Hfn()
        Dfn = self.build_Dfn()
        return integrate_rho_3flavor(L_km, E_GeV, Hfn, Dfn, steps=steps, flavor_in=self.flavor_in)


__all__ = ["UnifiedGKSL3"]

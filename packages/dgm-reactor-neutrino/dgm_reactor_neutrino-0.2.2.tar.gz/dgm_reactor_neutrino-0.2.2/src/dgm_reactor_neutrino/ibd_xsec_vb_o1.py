from __future__ import annotations

from typing import TYPE_CHECKING

from dag_modelling.core.global_parameters import NUMBA_CACHE_ENABLE
from dag_modelling.core.input_strategy import AddNewInputAddNewOutput
from dag_modelling.core.node import Node
from dag_modelling.core.type_functions import (
    assign_axes_from_inputs_to_outputs,
    check_dimension_of_inputs,
    check_dtype_of_inputs,
    check_inputs_equivalence,
    copy_from_inputs_to_outputs,
)
from numba import njit
from numpy import pi, power, sqrt
from scipy.constants import value as constant

if TYPE_CHECKING:
    from dag_modelling.core.input import Input
    from dag_modelling.core.output import Output
    from numpy import double
    from numpy.typing import NDArray


class IBDXsecVBO1(Node):
    """Inverse beta decay cross section by Vogel and Beacom."""

    __slots__ = (
        "_enu",
        "_ctheta",
        "_result",
        "_const_me",
        "_const_mp",
        "_const_mn",
        "_const_taun",
        "_const_fps",
        "_const_g",
        "_const_f",
        "_const_f2",
    )

    _enu: Input
    _ctheta: Input
    _result: Output

    _const_me: Input
    _const_mp: Input
    _const_mn: Input
    _const_taun: Input
    _const_fps: Input
    _const_g: Input
    _const_f: Input
    _const_f2: Input

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs, input_strategy=AddNewInputAddNewOutput())
        self.labels.setdefaults(
            {
                "text": r"IBD cross section σ(Eν,cosθ), cm⁻²",
                "plot_title": r"IBD cross section $\sigma(E_{\nu}, \cos\theta)$, cm$^{-2}$",
                "latex": r"IBD cross section $\sigma(E_{\nu}, \cos\theta)$, cm$^{-2}$",
                "axis": r"$\sigma(E_{\nu}, \cos\theta)$, cm$^{-2}$",
            }
        )

        self._enu = self._add_input("enu", positional=True, keyword=True)
        self._ctheta = self._add_input("costheta", positional=True, keyword=True)
        self._result = self._add_output("result", positional=True, keyword=True)

        self._const_me = self._add_input("ElectronMass", positional=False, keyword=True)
        self._const_mp = self._add_input("ProtonMass", positional=False, keyword=True)
        self._const_mn = self._add_input("NeutronMass", positional=False, keyword=True)
        self._const_taun = self._add_input("NeutronLifeTime", positional=False, keyword=True)
        self._const_fps = self._add_input("PhaseSpaceFactor", positional=False, keyword=True)
        self._const_g = self._add_input("g", positional=False, keyword=True)
        self._const_f = self._add_input("f", positional=False, keyword=True)
        self._const_f2 = self._add_input("f2", positional=False, keyword=True)

    def _function(self):
        _ibdxsecO1(
            self._enu.data,
            self._ctheta.data,
            self._result._data,
            self._const_me.data[0],
            self._const_mp.data[0],
            self._const_mn.data[0],
            self._const_taun.data[0],
            self._const_fps.data[0],
            self._const_g.data[0],
            self._const_f.data[0],
            self._const_f2.data[0],
        )

    def _type_function(self) -> None:
        """A output takes this function to determine the dtype and shape."""
        check_dtype_of_inputs(self, slice(None), dtype="d")
        check_dimension_of_inputs(self, slice(0, 1), 2)
        check_inputs_equivalence(self, slice(0, 1))
        copy_from_inputs_to_outputs(self, "enu", "result", edges=False, meshes=False)
        assign_axes_from_inputs_to_outputs(
            self,
            ("enu", "costheta"),
            "result",
            assign_meshes=True,
            merge_input_axes=True,
        )


_constant_hbar = constant("reduced Planck constant")
_constant_qe = constant("elementary charge")
_constant_c = constant("speed of light in vacuum")


@njit(cache=NUMBA_CACHE_ENABLE)
def _ibdxsecO1(
    EnuIn: NDArray[double],
    CosThetaIn: NDArray[double],
    Result: NDArray[double],
    ElectronMass: float,
    ProtonMass: float,
    NeutronMass: float,
    NeutronLifeTime: float,
    const_fps: float,
    const_g: float,
    const_f: float,
    const_f2: float,
):
    ElectronMass2 = ElectronMass * ElectronMass
    NeutronMass2 = NeutronMass * NeutronMass
    NucleonMass = 0.5 * (NeutronMass + ProtonMass)
    EnuThreshold = 0.5 * (NeutronMass2 / (ProtonMass - ElectronMass) - ProtonMass + ElectronMass)

    DeltaNP = NeutronMass - ProtonMass
    const_y2 = 0.5 * (DeltaNP * DeltaNP - ElectronMass2)

    const_gsq = const_g * const_g
    const_fsq = const_f * const_f

    sigma0_constant = 1.0e6 * _constant_qe / _constant_hbar
    ElectronMass5 = ElectronMass2 * ElectronMass2 * ElectronMass
    sigma0 = (2.0 * pi * pi) / (
        const_fps
        * (const_fsq + 3.0 * const_gsq)
        * ElectronMass5
        * NeutronLifeTime
        * sigma0_constant
    )

    MeV2J = 1.0e6 * _constant_qe
    J2MeV = 1.0 / MeV2J
    MeV2cm = power(_constant_hbar * _constant_c * J2MeV, 2) * 1.0e4

    result = Result.ravel()
    for i, (Enu, ctheta) in enumerate(zip(EnuIn.ravel(), CosThetaIn.ravel())):
        if Enu < EnuThreshold:
            result[i] = 0.0
            continue

        Ee0 = Enu - DeltaNP
        if Ee0 <= ElectronMass:
            result[i] = 0.0
            continue

        pe0 = sqrt(Ee0 * Ee0 - ElectronMass2)
        ve0 = pe0 / Ee0

        Ee1 = Ee0 * (1.0 - Enu / NucleonMass * (1.0 - ve0 * ctheta)) - const_y2 / NucleonMass
        if Ee1 <= ElectronMass:
            result[i] = 0.0
            continue
        pe1 = sqrt(Ee1 * Ee1 - ElectronMass2)
        ve1 = pe1 / Ee1

        sigma1a = (
            sigma0
            * 0.5
            * ((const_fsq + 3.0 * const_gsq) + (const_fsq - const_gsq) * ve1 * ctheta)
            * Ee1
            * pe1
        )

        gamma_1 = (
            2.0
            * const_g
            * (const_f + const_f2)
            * ((2.0 * Ee0 + DeltaNP) * (1.0 - ve0 * ctheta) - ElectronMass2 / Ee0)
        )
        gamma_2 = (const_fsq + const_gsq) * (DeltaNP * (1.0 + ve0 * ctheta) + ElectronMass2 / Ee0)
        A = (Ee0 + DeltaNP) * (1.0 - ctheta / ve0) - DeltaNP
        gamma_3 = (const_fsq + 3.0 * const_gsq) * A
        gamma_4 = (const_fsq - const_gsq) * A * ve0 * ctheta

        sigma1b = -0.5 * sigma0 * Ee0 * pe0 * (gamma_1 + gamma_2 + gamma_3 + gamma_4) / NucleonMass

        result[i] = MeV2cm * (sigma1a + sigma1b)

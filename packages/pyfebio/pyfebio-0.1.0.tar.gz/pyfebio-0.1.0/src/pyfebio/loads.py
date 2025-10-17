from typing import Literal

from pydantic_xml import BaseXmlModel, attr, element

from ._types import (
    StringFloatVec3,
)


class Scale(BaseXmlModel, validate_assignment=True):
    lc: int = attr()
    text: float = 1.0


class NodalLoad(BaseXmlModel, validate_assignment=True):
    type: Literal["nodal_load"] = attr(default="nodal_load", frozen=True)
    dof: Literal["x", "y", "z", "p"] = element(default="x")


class TractionLoad(BaseXmlModel, tag="surface_load", validate_assignment=True):
    type: Literal["traction"] = attr(default="traction", frozen=True)
    surface: str = attr()
    scale: Scale = element()
    traction: StringFloatVec3 = element(default="0,0,1")


class PressureLoad(BaseXmlModel, tag="surface_load", validate_assignment=True):
    type: Literal["pressure"] = attr(default="pressure", frozen=True)
    surface: str = attr()
    symmetric_stiffness: Literal[0, 1] = element(default=0)
    linear: Literal[0, 1] = element(default=0)
    shell_bottom: Literal[0, 1] = element(default=0)
    pressure: Scale = element()


class FluidFlux(BaseXmlModel, tag="surface_load", validate_assignment=True):
    flux: Scale = element()
    linear: Literal[0, 1] = element(default=0)
    mixture: Literal[0, 1] = element(default=1)


class FluidPressure(BaseXmlModel, tag="surface_load", validate_assignment=True):
    type: Literal["fluid pressure"] = attr(default="fluid pressure", frozen=True)
    pressure: float = element(default=1.0)


class Loads(BaseXmlModel, validate_assignment=True):
    all_surface_loads: list[TractionLoad | PressureLoad | FluidFlux | FluidPressure] = element(default=[])
    all_nodal_loads: list[NodalLoad] = element(default=[])

    def add_surface_load(self, new_load: PressureLoad | TractionLoad | FluidFlux | FluidPressure):
        self.all_surface_loads.append(new_load)

    def add_nodal_load(self, new_load: NodalLoad):
        self.all_nodal_loads.append(new_load)

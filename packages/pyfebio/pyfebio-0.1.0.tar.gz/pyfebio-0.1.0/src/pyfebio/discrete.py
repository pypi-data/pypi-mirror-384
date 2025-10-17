from typing import Literal

from pydantic_xml import BaseXmlModel, attr, element


class Spring(BaseXmlModel, tag="discrete_material", validate_assignment=True):
    id: int = attr()
    name: str = attr()
    type: str = attr(default="linear spring", frozen=True)
    E: float = element(default=1.0)


class NonlinearSpringForce(BaseXmlModel, tag="force", validate_assignment=True):
    type: Literal["math"] = attr(default="math", frozen=True)
    math: str = element()


class NonlinearSpring(BaseXmlModel, tag="discrete_material", validate_assignment=True):
    id: int = attr()
    name: str = attr()
    type: str = attr(default="nonlinear spring", frozen=True)
    scale: float = element(default=1.0)
    measure: Literal["strain"] = element(default="strain", frozen=True)
    force: NonlinearSpringForce = element()


class DiscreteEntry(BaseXmlModel, tag="discrete", validate_assignment=True):
    dmat: int = attr()
    discrete_set: str = attr()


class Discrete(BaseXmlModel, validate_assignment=True):
    discrete_materials: list[NonlinearSpring | Spring] = element(default=[])
    discrete_elements: list[DiscreteEntry] = element(default=[])

    def add_discrete_material(self, new_material: NonlinearSpring | Spring):
        self.discrete_materials.append(new_material)

    def add_discrete_element(self, new_element: DiscreteEntry):
        self.discrete_elements.append(new_element)

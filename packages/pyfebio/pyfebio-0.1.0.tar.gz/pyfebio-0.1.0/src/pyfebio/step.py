from pydantic_xml import BaseXmlModel, attr, element

from .boundary import Boundary
from .constraints import Constraints
from .contact import Contact
from .control import Control
from .initial import Initial
from .loads import Loads
from .rigid import Rigid


class StepEntry(BaseXmlModel, validate_assignment=True):
    id: int = attr()
    name: str = attr(default="Step")
    control: Control | None = element(default=None, tag="Control")
    initial: Initial | None = element(default=None, tag="Initial")
    boundary: Boundary | None = element(default=None, tag="Boundary")
    loads: Loads | None = element(default=None, tag="Loads")
    constraints: Constraints | None = element(default=None, tag="Constraints")
    contact: Contact | None = element(default=None, tag="Contact")
    rigid: Rigid | None = element(default=None, tag="Rigid")


class Step(BaseXmlModel, validate_assignment=True):
    all_steps: list[StepEntry] = element(default=[], tag="step")

    def add_step(self, new_step: StepEntry):
        self.all_steps.append(new_step)

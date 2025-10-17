from pydantic_xml import BaseXmlModel


class Include(BaseXmlModel, tag="Include", validate_assignment=True):
    text: str

from attrs import field

from pbi_core.attrs import BaseValidation, define

base_val = bool | int | str


@define()
class QueryNameMapping(BaseValidation):
    Key: str
    Value: str


@define()
class Metadata(BaseValidation):
    Version: int
    AutoCreatedRelationships: list[int] = field(factory=list)
    CreatedFrom: str
    CreatedFromRelease: str
    FileDescription: str | None = None
    QueryNameToKeyMapping: list[QueryNameMapping] = field(alias="_queryNameToKeyMapping", factory=list)

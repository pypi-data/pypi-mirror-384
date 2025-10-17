from pbi_core.attrs import BaseValidation, define

base_val = bool | int | str


@define()
class Settings(BaseValidation):
    Version: int
    ReportSettings: dict[str, base_val]
    QueriesSettings: dict[str, base_val]

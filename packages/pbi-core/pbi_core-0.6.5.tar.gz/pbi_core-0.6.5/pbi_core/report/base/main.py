from pbi_core.ssas.server import BaseTabularModel
from pbi_core.static_files import StaticFiles

from .ssas import BaseSsasReport
from .static_files import BaseStaticReport


class BaseReport(BaseStaticReport, BaseSsasReport):
    def __init__(self, ssas: BaseTabularModel, static_files: StaticFiles) -> None:
        self.ssas = ssas
        self.static_files = static_files

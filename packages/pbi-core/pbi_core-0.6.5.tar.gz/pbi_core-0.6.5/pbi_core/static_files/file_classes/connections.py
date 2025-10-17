from uuid import UUID

from pbi_core.attrs import BaseValidation, define


@define()
class RemoteArtifact(BaseValidation):
    DatasetId: UUID
    ReportId: UUID


@define()
class Connections(BaseValidation):
    Version: int
    RemoteArtifacts: list[RemoteArtifact]

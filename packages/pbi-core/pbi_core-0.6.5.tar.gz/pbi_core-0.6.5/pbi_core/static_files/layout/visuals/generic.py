from pbi_core.attrs import define

from .base import BaseVisual, PropertyDef


@define()
class GenericVisual(BaseVisual):
    """A generic visual representation."""

    objects: dict[str, list[PropertyDef]] | None = None

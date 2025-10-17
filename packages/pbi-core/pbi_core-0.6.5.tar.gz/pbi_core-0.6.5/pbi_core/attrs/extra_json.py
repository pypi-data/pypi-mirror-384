from typing import TYPE_CHECKING, Annotated, TypeVar

AnyType = TypeVar("AnyType")

if TYPE_CHECKING:
    Json = Annotated[AnyType, ...]
    # TODO: subclass to JSON dict and list

else:

    class Json:
        @classmethod
        def __class_getitem__(cls, item: AnyType) -> AnyType:
            return Annotated[item, cls()]

        def __repr__(self) -> str:
            return "Json"

        def __hash__(self) -> int:
            return hash(type(self))

        def __eq__(self, other: object) -> bool:
            return type(other) is type(self)

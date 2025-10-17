import json
from collections.abc import Callable
from enum import Enum
from typing import TYPE_CHECKING, Any, Literal, TypeVar

from pbi_core.attrs import BaseValidation, fields
from pbi_core.lineage import LineageNode

if TYPE_CHECKING:
    from pbi_core.ssas.server import BaseTabularModel

LAYOUT_ENCODING = "utf-16-le"


T = TypeVar("T", bound="LayoutNode")


class LayoutNode(BaseValidation):
    _name_field: str | None = None  # name of the field used to populate __repr__

    def __repr__(self) -> str:
        return json.dumps(self.serialize(), indent=2)

    @staticmethod
    def serialize_helper(value: Any) -> Any:
        """Helper function to serialize a value.

        We need to separate from the main function to handle cases where there is a list of
        dictionaries such as the visual container properties.
        """
        if hasattr(value, "serialize"):
            return value.serialize()
        if isinstance(value, list):
            return [LayoutNode.serialize_helper(val) for val in value]
        if isinstance(value, dict):
            return {key: LayoutNode.serialize_helper(val) for key, val in value.items()}
        if isinstance(value, Enum):
            return value.name
        return value

    def serialize(self) -> dict[str, Any]:
        """Serialize the node to a dictionary.

        Differs from the model_dump_json method in that it does not convert the JSON models back to strings.
        """
        ret = {}
        for field in fields(self.__class__):
            if field.init is False:
                continue
            ret[field.name] = self.serialize_helper(getattr(self, field.name))
        return ret

    def pbi_core_name(self) -> str:
        raise NotImplementedError

    def find_all(
        self,
        cls_type: type[T] | tuple[type[T], ...],
        attributes: dict[str, Any] | Callable[[T], bool] | None = None,
    ) -> list["T"]:
        ret: list[T] = []
        if attributes is None:
            attribute_lambda: Callable[[T], bool] = lambda _: True  # noqa: E731
        elif isinstance(attributes, dict):
            attribute_lambda = lambda x: all(  # noqa: E731
                getattr(x, field_name) == field_value for field_name, field_value in attributes.items()
            )
        else:
            attribute_lambda = attributes
        if isinstance(self, cls_type) and attribute_lambda(self):
            ret.append(self)
        for child in self._children():
            ret.extend(child.find_all(cls_type, attributes))
        return ret

    def find(self, cls_type: type[T], attributes: dict[str, Any] | Callable[[T], bool] | None = None) -> "T":
        if attributes is None:
            attribute_lambda: Callable[[T], bool] = lambda _: True  # noqa: E731
        elif isinstance(attributes, dict):
            attribute_lambda = lambda x: all(  # noqa: E731
                getattr(x, field_name) == field_value for field_name, field_value in attributes.items()
            )
        else:
            attribute_lambda = attributes
        if isinstance(self, cls_type) and attribute_lambda(self):
            return self
        for child in self._children():
            try:
                return child.find(cls_type, attributes)
            except ValueError:
                pass
        msg = f"Object not found: {cls_type}"
        raise ValueError(msg)

    def _children(self) -> list["LayoutNode"]:
        ret: list[LayoutNode] = []
        for attr in dir(self):
            if attr.startswith("_"):
                continue
            child_candidate: list[Any] | dict[str, Any] | LayoutNode | int | str = getattr(self, attr)
            if isinstance(child_candidate, list):
                ret.extend(val for val in child_candidate if isinstance(val, LayoutNode))
            elif isinstance(child_candidate, dict):
                ret.extend(val for val in child_candidate.values() if isinstance(val, LayoutNode))
            elif isinstance(child_candidate, LayoutNode):
                ret.append(child_candidate)
        return ret

    def get_lineage(
        self,
        lineage_type: Literal["children", "parents"],
        tabular_model: "BaseTabularModel",
    ) -> LineageNode:
        raise NotImplementedError

    def find_xpath(self, xpath: list[str | int]) -> "LayoutNode":
        """Find a node in the layout using an XPath-like list of attributes.

        Note: This method currently uses a DFS approach to find the node.
            Eventually, I'll find a way to type-safely include element parents in the LayoutNode.

        Raises:
            TypeError: If the XPath is invalid or if the node is not found.

        """
        if len(xpath) == 0:
            return self

        next_step = xpath.pop(0)
        if isinstance(next_step, int):
            msg = f"Cannot index {self.__class__.__name__} with an integer: {next_step}"
            raise TypeError(msg)
        attr = getattr(self, next_step)

        while isinstance(attr, (dict, list)):
            next_step = xpath.pop(0)
            attr = attr[next_step]  # pyright: ignore[reportCallIssue, reportArgumentType]

        if not isinstance(attr, LayoutNode):
            msg = f"Cannot index {self.__class__.__name__} with a non-LayoutNode: {attr}"
            raise TypeError(msg)
        return attr.find_xpath(xpath)

    def get_xpath(self, parent: "LayoutNode") -> list[str | int]:
        """Get the [XPath](https://developer.mozilla.org/en-US/docs/Web/XML/XPath) of this node.

        Args:
            parent (LayoutNode): The parent node to which the XPath is relative.

        Raises:
            ValueError: If the node is not found in the parent.

        """
        ret = _get_xpath(parent, self)
        if ret is None:
            msg = f"Node {self.pbi_core_name()} not found in parent {parent.pbi_core_name()}"
            raise ValueError(msg)
        return ret


def _get_xpath(  # noqa: C901  # too complex, but it's actually not that complex
    parent: LayoutNode | list | dict,
    child: LayoutNode,
    xpath: list[str | int] | None = None,
) -> list[str | int] | None:
    def _xpath_attrs(parent: LayoutNode, child: LayoutNode, xpath: list[str | int]) -> list[str | int] | None:
        for attr in fields(parent.__class__):
            val = getattr(parent, attr.name)
            ret = _get_xpath(val, child, xpath=[*xpath, attr.name])
            if ret is not None:
                return ret
        return None

    def _xpath_list(parent: list, child: LayoutNode, xpath: list[str | int]) -> list[str | int] | None:
        for i, val in enumerate(parent):
            ret = _get_xpath(val, child, xpath=[*xpath, i])
            if ret is not None:
                return ret
        return None

    def _xpath_dict(parent: dict, child: LayoutNode, xpath: list[str | int]) -> list[str | int] | None:
        for key, val in parent.items():
            ret = _get_xpath(val, child, xpath=[*xpath, key])
            if ret is not None:
                return ret
        return None

    xpath = xpath or []
    # print(id(parent), id(child), child.pbi_core_name(), xpath)
    if parent is child:
        return xpath

    if isinstance(parent, LayoutNode):
        return _xpath_attrs(parent, child, xpath)
    if isinstance(parent, list):
        return _xpath_list(parent, child, xpath)
    if isinstance(parent, dict):
        return _xpath_dict(parent, child, xpath)
    return None

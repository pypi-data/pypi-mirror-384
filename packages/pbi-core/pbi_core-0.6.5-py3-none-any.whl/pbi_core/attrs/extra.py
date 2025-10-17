from typing import Any, NewType

Color = NewType("Color", str)


def repr_len(x: list | dict | None) -> str:
    if x is None:
        return "None"
    if isinstance(x, dict):
        return str(len(x))
    return str(len(x))


def repr_exists(x: Any) -> str:
    if x is None:
        return "None"
    return "Exists"

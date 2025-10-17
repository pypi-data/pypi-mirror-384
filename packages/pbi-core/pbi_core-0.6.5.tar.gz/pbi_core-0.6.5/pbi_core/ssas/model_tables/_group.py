from collections.abc import Callable
from typing import Any, TypeVar


class IdBase:
    id: int


T = TypeVar("T", bound=IdBase)


class RowNotFoundError(Exception):
    pass


class Group(list[T]):  # noqa: FURB189
    def find(self, match_val: int | dict[str, Any] | Callable[[T], bool]) -> T:
        """Gets a matching value from the group.

        Finds a matching SSAS record from the group using the following rules:
        1. If match_val is an int, it finds a record with a matching `id`
        2. If match_val is a dictionary, it uses the keys as field names and values as field values.
            It returns the first record to match all items
        3. If match_val is a function, it returns the first record to return true when passed to the function

        Raises:
            RowNotFoundError: when no value matches the match_val

        """
        if isinstance(match_val, int):
            for val in self:
                if val.id == match_val:
                    return val
        elif isinstance(match_val, dict):
            for val in self:
                if all(getattr(val, field_name) == field_value for field_name, field_value in match_val.items()):
                    return val

        else:
            for val in self:
                if match_val(val) is True:
                    return val
        raise RowNotFoundError

    def find_all(self, match_val: int | dict[str, Any] | Callable[[T], bool]) -> set[T]:
        ret: set[T] = set()
        if isinstance(match_val, int):
            ret.update(val for val in self if val.id == match_val)
        elif isinstance(match_val, dict):
            ret.update(
                val
                for val in self
                if all(getattr(val, field_name) == field_value for field_name, field_value in match_val.items())
            )
        else:
            ret.update(val for val in self if match_val(val) is True)
        return ret

    def sync_to_server(self) -> None:
        pass

    def sync_from_server(self) -> None:
        pass

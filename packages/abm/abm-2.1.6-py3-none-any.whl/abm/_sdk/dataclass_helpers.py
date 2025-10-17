from dataclasses import Field, fields
from typing import Any, ClassVar, Protocol


# https://github.com/python/typeshed/blob/e1c74f08f12b8bec6afe266951f0756dc1b43ebe/stdlib/_typeshed/__init__.pyi#L349
class DataclassInstance(Protocol):
    __dataclass_fields__: ClassVar[dict[str, Field[Any]]]


def ignore_extra_kwargs[T: DataclassInstance](cls: type[T]) -> type[T]:
    init = cls.__init__

    def init_with_filter(self, *args, **kwargs):
        field_names = {field.name for field in fields(cls)}
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in field_names}
        init(self, *args, **filtered_kwargs)

    cls.__init__ = init_with_filter
    return cls

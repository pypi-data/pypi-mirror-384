from __future__ import annotations

__all__ = ["get_all_subclasses"]


def get_all_subclasses[T](cls: type[T]) -> dict[str, type[T]]:
    # abstract_serializable only works on direct subclasses
    # Recurse over subclasses to find them all
    subclasses: dict[str, type[T]] = {}
    for subclass in cls.__subclasses__():
        if hasattr(subclass, "__fields_serializer__"):
            subclasses[subclass.__name__] = subclass
        subclasses.update(get_all_subclasses(subclass))
    return subclasses

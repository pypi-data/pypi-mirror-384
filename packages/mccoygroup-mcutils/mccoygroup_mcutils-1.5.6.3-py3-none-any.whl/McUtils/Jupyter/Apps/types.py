import types, typing

__all__ = [
    "HTMLableType",
    "WidgetableType",
    "InterfaceElementType",
    "ElementType",
    "ClassListType",
    "AttrsType"
]

@typing.runtime_checkable
class HTMLableType(typing.Protocol):
    def to_tree(self):
        ...
@typing.runtime_checkable
class WidgetableType(typing.Protocol):
    def to_widget(self):
        ...
InterfaceElementBaseType = typing.Union[
    str,
    typing.Mapping,
    HTMLableType,
    WidgetableType
]
InterfaceElementType = typing.Union[
    InterfaceElementBaseType,
    typing.Tuple[InterfaceElementBaseType, typing.Mapping],
]
ElementType = typing.Union[InterfaceElementType, None, typing.Iterable[InterfaceElementType]]
ClassListType = typing.Union[None, str, typing.Iterable[str]]
AttrsType = typing.Union[None, typing.Mapping]
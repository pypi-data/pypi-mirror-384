import builtins
import datetime
import enum
import pathlib
import types
import typing
import uuid
import xml.etree.ElementTree as ET

from .base_types import XmlBaseType
from .base_types import XmlTextField
from .error_handlers import XmlParserError, error_handler

from .xml_elementTree_utils import _get_child_from
from .xml_elementTree_utils import _get_value_with_fallback


@typing.dataclass_transform()
class XmlClass:
    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)

        def init(self: XmlClass, **kwargs) -> None:
            for k in kwargs:
                if k not in cls.__annotations__:
                    msg = f"got an unexpected keyword argument '{k}'"
                    raise TypeError(msg)
            for k, k_type in cls.__annotations__.items():
                # TODO: Convert to k_type or cast error on wrong type.
                setattr(self, k, kwargs[k])

        init.__name__ = "__init__"
        cls.__init__ = init

        def eq(self: XmlClass, other: XmlClass) -> bool:
            if set(self.__annotations__.keys()) ^ set(other.__annotations__.keys()):
                return False
            return all(getattr(self, k) == getattr(other, k) for k in self.__annotations__)

        eq.__name__ = "__eq__"
        cls.__eq__ = eq
        cls.__ne__ = lambda self, x: not cls.__eq__(self, x)
        cls.__slots__ = tuple(cls.__annotations__.keys())

        ## TODO: Use this to generate the wanted stuff.
        ## cls.__dataclass_transform__

    # TODO: Add def to_string(self) -> str:

    @classmethod
    def from_element(cls, dom: ET.Element) -> typing.Self:
        arguments: dict = {}
        for key, field in cls.__annotations__.items():
            arguments[key] = _get_value(key, field, dom, cls.__name__)

        if text_data := unexpected_text_field(dom, cls):
            msg = f"Unexpected text field: {text_data}"
            raise XmlParserError(msg)

        if extra_attributes := unexpected_attributes(dom, cls):
            msg = f"Unexpected attribute(s): {extra_attributes}"
            raise XmlParserError(msg)

        if extra_children := unexpected_children(dom, cls):
            msg = f"Unexpected child(ren): {extra_children}"
            raise XmlParserError(msg)

        return cls(**arguments)

    @classmethod
    def from_string(cls, string: str) -> typing.Self:
        dom = ET.fromstring(string.strip())  # NOTE: Is unsecure, but do not want to import defusedxml
        return cls.from_element(dom)


def unexpected_text_field(dom: ET.Element, cls: type) -> str:
    expecting_text_field = any(filter(lambda x: is_xml_text_field(x), cls.__annotations__.values()))
    if not expecting_text_field and dom.text is not None:
        return dom.text.strip()
    return ""


def unexpected_attributes(dom: ET.Element, cls: type) -> list[str]:
    cls_annotations = [
        x.rstrip("_").replace("_", "-") for x in cls.__annotations__ if not is_xml_class(cls.__annotations__.get(x))
    ]
    return [x for x in dom.attrib if x not in cls_annotations]


def unexpected_children(dom: ET.Element, cls: type) -> list[str]:
    cls_annotations = [
        x.rstrip("_").replace("_", "-")
        for x in cls.__annotations__
        if is_xml_class(cls.__annotations__.get(x))
        or is_union_contains_xml_class(cls.__annotations__.get(x))
        or is_list(cls.__annotations__.get(x))
        or is_tuple(cls.__annotations__.get(x))  # TODO: Also check sub_annotations.
    ]
    return list({x.tag for x in dom if x.tag.rstrip("_") not in cls_annotations})


def is_xml_text_field(obj: type) -> typing.TypeGuard[type[XmlTextField]]:
    return typing.get_origin(obj) is XmlTextField


def is_list(obj: type) -> typing.TypeGuard[type[list]]:
    return typing.get_origin(obj) is list


def is_tuple(obj: type) -> typing.TypeGuard[type[tuple]]:
    return typing.get_origin(obj) is tuple


def is_set(obj: type) -> typing.TypeGuard[type[set]]:
    return typing.get_origin(obj) is set


def is_union(obj: type) -> typing.TypeGuard[type[types.UnionType]]:
    return isinstance(obj, types.UnionType)


def is_union_contains_xml_class(obj: type) -> typing.TypeGuard[type[types.UnionType]]:
    return is_union(obj) and any(map(is_xml_class, typing.get_args(obj)))


def is_xml_class(obj: type) -> typing.TypeGuard[type[XmlClass]]:
    return isinstance(obj, type) and issubclass(obj, XmlClass)


def is_literal(obj: type) -> typing.TypeGuard[type[typing.Literal]]:
    return typing.get_origin(obj) == typing.Literal


def is_enum(obj: type) -> typing.TypeGuard[type[enum.EnumMeta]]:
    return type(obj) is enum.EnumMeta


# TODO: Change this to take make use of the more modern typing features.
T = typing.TypeVar("T", str, int, float, bool, datetime.datetime, uuid.UUID, XmlClass)

bool_true_values = ["true", "1", "yes", "on"]
bool_false_values = ["false", "0", "no", "off"]


def _convert_boolean(data: str) -> bool:
    if data.lower() not in bool_true_values + bool_false_values:
        msg = f"Boolean value {data} not in {bool_true_values} or {bool_false_values}"
        raise ValueError(msg)
    return data.lower() in bool_true_values


def _convert_literal(data: str, field_type: typing.Literal) -> T:
    for data_type in typing.get_args(field_type):
        try:
            if type(data_type)(data) == data_type:
                return data_type
        except ValueError:
            pass
    msg = f'Literal value "{data}" not in the defined values: {typing.get_args(field_type)}'
    raise ValueError(msg)


def _handle_none(field_type: types.UnionType, data: ET.Element | str | None) -> None:
    # UNSURE: Should check the data, right?
    return None


def _handle_union(name: str, field_type: XmlBaseType, dom: ET.Element | str, parent_name: str) -> T:
    # TODO: Refactor this.
    # NOTE: dom can also be a data type.
    child_tags = {x.tag for x in dom} | {x.tag + "_" for x in dom} | {x.tag.replace("-", "_") for x in dom}
    if (
        name not in dom.keys()
        and name not in dom.keys()
        and name not in child_tags
        and not is_xml_text_field(field_type)
    ):
        if types.NoneType not in typing.get_args(field_type):
            msg = f'Missing "{name}" in "{dom.tag}", with attributes: {dom.attrib} and children: {child_tags}'
            raise ValueError(msg)
        return _handle_none(field_type, dom)

    for d_type in typing.get_args(field_type):
        try:
            # TODO(MBK): If d_type is a XmlClass, and Element is present, it should not ignore the ValueError and try it as a attribute.
            # UNSURE: How do I make a test for this?
            return _get_value(name, d_type, dom, parent_name)
        except ValueError as e:
            # print(f"{d_type=}", e)
            pass
    msg = f'Unable to convert "{name}"\'s value: "{dom.attrib[name]}" to any of ({", ".join(x.__name__ for x in typing.get_args(field_type))})'
    with error_handler(dom, name):
        raise ValueError(msg)


def _handle_textfield_union(name: str, field_type: XmlBaseType, dom: ET.Element, parent_name: str) -> T:
    for d_type in typing.get_args(field_type):
        try:
            return _convert_text(d_type, dom)
        except ValueError:
            pass
    msg = f'Unable to convert "{name}"\'s value: "{dom.text.strip()}" to any of ({", ".join(x.__name__ for x in typing.get_args(field_type))})'
    with error_handler(dom, name):
        raise ValueError(msg)


def _handle_xml_text_field(
    name: str,
    field_type: XmlTextField,
    dom: ET.Element,
    parent_name: str,
) -> T:
    # NOTE: Assume that it can only be Union or "normal" data types.
    sub_type = typing.get_args(field_type)[0]
    if is_union(sub_type):
        return _handle_textfield_union(name, sub_type, dom, parent_name)
    return _convert_text(sub_type, dom)


def _handle_list(
    field_alias: str,
    field_type: type[list[T]],
    dom: ET.Element,
    parent_name: str,
) -> list[T]:
    # NOTE: Assume that this children can only be of type: XmlClass.
    return [
        # NOTE: Temporary fix.
        typing.get_args(field_type)[0].from_element(x)
        for x in _get_child_from(field_alias, dom)
    ]


def _handle_tuple(
    field_alias: str,
    field_type: type[tuple],
    dom: ET.Element,
    parent_name: str,
) -> tuple:
    # NOTE: Assume that these children can only be of type: XmlClass.
    data = list(_get_child_from(field_alias, dom))
    if len(typing.get_args(field_type)) != len(data):
        msg = f"Tuple expected {len(typing.get_args(field_type))} elements. Found: {len(data)}"
        raise ValueError(msg)
    return tuple(
        # NOTE: Temporary fix.
        d_type.from_element(d_data)
        for d_type, d_data in zip(typing.get_args(field_type), data, strict=True)
    )


def _get_value(
    name: str,
    field_type: type[T] | types.UnionType | list[type[T]] | set[type[T]] | tuple[type[T], ...] | None,
    dom: ET.Element,
    parent_name: str,
) -> T | str | None:
    with error_handler(dom, name):
        match field_type:
            case _ if is_xml_text_field(field_type):
                return _handle_xml_text_field(name, field_type, dom, parent_name)
            case _ if is_xml_class(field_type):
                return field_type.from_element(
                    _get_child_from(name, dom, single=True),
                )
            case _ if is_list(field_type):
                return _handle_list(name, field_type, dom, parent_name)
            case _ if is_set(field_type):
                msg = "Sets are not supported"
                raise NotImplementedError(msg)
            case _ if is_tuple(field_type):
                return _handle_tuple(name, field_type, dom, parent_name)
            case _ if is_union(field_type):
                return _handle_union(name, field_type, dom, parent_name)
            case _:
                return _convert_attribute(field_type, name, dom)


def _convert_attribute(
    field_type: type[T] | None,
    name: str,
    dom: ET.Element,
) -> T | str | None:
    value = _get_value_with_fallback(dom, name)
    if value is None and field_type is not None:
        msg = f'Missing attribute: "{name}"'
        raise KeyError(msg)
    return _convert(field_type, value)


def _convert_text(
    field_type: type[T] | None,
    dom: ET.Element,
) -> T | str | None:
    return _convert(field_type, dom.text.strip())


def _convert(
    field_type: type[T] | None,
    data: str | ET.Element | None,
) -> T | str | None:
    match field_type:
        case builtins.int | builtins.float | builtins.str | uuid.UUID | pathlib.Path:
            return field_type(data)

        case builtins.bool:
            return _convert_boolean(data)

        case datetime.datetime:
            return datetime.datetime.fromisoformat(data)

        case typing.Any:
            return data

        case None:
            return _handle_none(field_type, data)

        case _ if is_literal(field_type):
            return _convert_literal(data, field_type)

        case _ if is_enum(field_type):
            return field_type(data)

        case _:
            msg = f"Unknown type: {field_type.__name__}"
            raise ValueError(msg)

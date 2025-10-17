import datetime
import enum
import pathlib
import typing
import uuid

import pytest

from xmlclasses import XmlClass


def test_with_string() -> None:
    xml_with_string = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root data="data">
    </root>
    """

    class RootString(XmlClass):
        data: str

    root = RootString.from_string(xml_with_string.strip())
    assert isinstance(root.data, str)
    assert root.data == "data"


def test_with_int() -> None:
    int_value = 42
    xml_with_string = f"""
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root data="{int_value}">
    </root>
    """

    class RootString(XmlClass):
        data: int

    root = RootString.from_string(xml_with_string.strip())
    assert isinstance(root.data, int)
    assert root.data == int_value


def test_with_float() -> None:
    float_value = 42.22
    xml_with_string = f"""
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root data="{float_value}">
    </root>
    """

    class RootString(XmlClass):
        data: float

    root = RootString.from_string(xml_with_string.strip())
    assert isinstance(root.data, float)
    assert root.data == float_value


def test_with_null() -> None:
    xml_with_none = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root data="null"/>
    """

    class RootString(XmlClass):
        data: None

    root = RootString.from_string(xml_with_none.strip())
    assert root.data is None


def test_with_none() -> None:
    xml_with_none = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root />
    """

    class RootString(XmlClass):
        data: None

    root = RootString.from_string(xml_with_none.strip())
    assert root.data is None

def test_with_uuid() -> None:
    uuid_value = uuid.uuid4()
    xml_with_uuid = f"""
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root data="{uuid_value}" />
    """

    class RootString(XmlClass):
        data: uuid.UUID

    root = RootString.from_string(xml_with_uuid.strip())
    assert isinstance(root.data, uuid.UUID)
    assert root.data == uuid_value


def test_with_any() -> None:
    xml_with_uuid = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root data="fff">
    </root>
    """

    class RootString(XmlClass):
        data: typing.Any

    root = RootString.from_string(xml_with_uuid.strip())
    assert isinstance(root.data, str)
    assert root.data == "fff"


@pytest.mark.parametrize(
    "value",
    [
        "/home/User/Projects/xmlclasses/test/test_simple.py",
        "C:\\Users\\User\\Projects\\xmlclasses\\test\\test_simple.py",
    ],
)
def test_path(value: str) -> None:
    xml_with_path = f"""
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root data="{value}">
    </root>
    """

    class RootString(XmlClass):
        data: pathlib.Path

    root = RootString.from_string(xml_with_path.strip())
    assert isinstance(root.data, pathlib.Path)
    assert root.data == pathlib.Path(value)


@pytest.mark.parametrize(
    "value",
    [
        "2025-09-27T22:22:41",
        "2025-09-27T22:22:41.123456",
        "2025-09-27T22:22:41+06:15",
    ],
)
def test_datetime(value: str) -> None:
    xml_with_datetime = f"""
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root data="{value}">
    </root>
    """

    class RootString(XmlClass):
        data: datetime.datetime

    root = RootString.from_string(xml_with_datetime.strip())
    assert isinstance(root.data, datetime.datetime)
    assert root.data == datetime.datetime.fromisoformat(value)


def test_nested_element() -> None:
    xml_with_element = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root>
        <value>
            <data data="data" />
        </value>
    </root>
    """

    class Data(XmlClass):
        data: str

    class Value(XmlClass):
        data: Data

    class RootElement(XmlClass):
        value: Value

    root = RootElement.from_string(xml_with_element.strip())
    assert isinstance(root.value.data.data, str)
    assert isinstance(root.value.data, Data)
    assert isinstance(root.value, Value)
    assert root.value.data.data == "data"


@pytest.mark.parametrize(
    "value",
    ["true", "1", "yes", "on"],
)
def test_with_boolean_trues(value: str) -> None:
    xml_with_attribute = f"""
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root value="{value}" />
    """

    class RootAttribute(XmlClass):
        value: bool

    root = RootAttribute.from_string(xml_with_attribute.strip())
    assert isinstance(root.value, bool)
    assert root.value is True


@pytest.mark.parametrize(
    "value",
    ["false", "0", "no", "off"],
)
def test_with_boolean_falses(value: str) -> None:
    xml_with_attribute = f"""
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root value="{value}" />
    """

    class RootAttribute(XmlClass):
        value: bool

    root = RootAttribute.from_string(xml_with_attribute.strip())
    assert isinstance(root.value, bool)
    assert root.value is False


def test_with_literal_str() -> None:
    xml_with_attribute = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root value="data" />
    """

    class RootAttribute(XmlClass):
        value: typing.Literal["data"]

    root = RootAttribute.from_string(xml_with_attribute.strip())
    assert isinstance(root.value, str)
    assert root.value == "data"


def test_with_literal_int() -> None:
    xml_with_attribute = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root value="1" />
    """

    class RootAttribute(XmlClass):
        value: typing.Literal[1]

    root = RootAttribute.from_string(xml_with_attribute.strip())
    assert isinstance(root.value, int)
    assert root.value == 1


def test_with_enum() -> None:
    xml_with_attribute = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root value="data" />
    """

    class DataEnum(enum.Enum):
        DATA = "data"
        NO_DATA = "no_data"

    class RootAttribute(XmlClass):
        value: DataEnum

    root = RootAttribute.from_string(xml_with_attribute.strip())
    assert isinstance(root.value, DataEnum)
    assert root.value == DataEnum.DATA


def test_with_element_list_with_attribute_union() -> None:
    the_int = 2
    the_str = "data"

    xml_with_int = f"""
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root value="{the_int}">
    </root>
    """
    xml_with_str = f"""
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root value="{the_str}">
    </root>
    """

    class RootElement(XmlClass):
        value: int | str

    root = RootElement.from_string(xml_with_int.strip())
    assert isinstance(root.value, int)
    assert root.value == the_int

    root = RootElement.from_string(xml_with_str.strip())
    assert isinstance(root.value, str)
    assert root.value == the_str


def test_optional_attribute() -> None:
    xml_with_element = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root>
        <value data="data" />
    </root>
    """

    class Value(XmlClass):
        data: str

    class RootElement(XmlClass):
        value: Value
        not_value: str | None

    root = RootElement.from_string(xml_with_element.strip())
    assert isinstance(root.value.data, str)
    assert root.value.data == "data"
    assert root.not_value is None


def test_attribute_name_padding() -> None:
    int_value = 2
    xml_with_element = f"""
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root value="{int_value}">
    </root>
    """

    class RootElement(XmlClass):
        value_: int

    root = RootElement.from_string(xml_with_element.strip())
    assert isinstance(root.value_, int)
    assert root.value_ == int_value


def test_attribute_dash_name() -> None:
    int_value = 2
    xml_with_element = f"""
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root value-with-dash="{int_value}">
    </root>
    """

    class RootElement(XmlClass):
        value_with_dash: int

    root = RootElement.from_string(xml_with_element.strip())
    assert isinstance(root.value_with_dash, int)
    assert root.value_with_dash == int_value

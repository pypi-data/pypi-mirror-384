import datetime
import enum
import pathlib
import typing
import uuid

import pytest

from xmlclasses import XmlClass
from xmlclasses import XmlTextField


def test_with_string() -> None:
    xml_with_string = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root>
        data
    </root>
    """

    class RootString(XmlClass):
        data: XmlTextField[str]

    root = RootString.from_string(xml_with_string.strip())
    assert isinstance(root.data, str)
    assert root.data == "data"


def test_with_int() -> None:
    int_value = 42
    xml_with_string = f"""
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root>
        {int_value}
    </root>
    """

    class RootString(XmlClass):
        data: XmlTextField[int]

    root = RootString.from_string(xml_with_string.strip())
    assert isinstance(root.data, int)
    assert root.data == int_value


def test_with_float() -> None:
    float_value = 42.22
    xml_with_string = f"""
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root>
        {float_value}
    </root>
    """

    class RootString(XmlClass):
        data: XmlTextField[float]

    root = RootString.from_string(xml_with_string.strip())
    assert isinstance(root.data, float)
    assert root.data == float_value


def test_with_cdata() -> None:  # CDATA
    xml_with_cdata = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root>
<![CDATA[
let message = (login == 'Employee') ? 'Hello' :
  (login == 'Director') ? 'Hello, boss' :
  (login == '') ? 'No login' :
  '';
]]>
    </root>
    """

    class RootElement(XmlClass):
        code: XmlTextField[str]

    root = RootElement.from_string(xml_with_cdata.strip())
    assert isinstance(root.code, str)
    assert root.code == (
        "let message = (login == 'Employee') ? 'Hello' :\n"
        "  (login == 'Director') ? 'Hello, boss' :\n"
        "  (login == '') ? 'No login' :\n"
        "  '';"
    )


def test_with_uuid() -> None:
    uuid_value = uuid.uuid4()
    xml_with_uuid = f"""
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root>
        {uuid_value}
    </root>
    """

    class RootString(XmlClass):
        data: XmlTextField[uuid.UUID]

    root = RootString.from_string(xml_with_uuid.strip())
    assert isinstance(root.data, uuid.UUID)
    assert root.data == uuid_value


def test_with_any() -> None:
    xml_with_uuid = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root>
        fff
    </root>
    """

    class RootString(XmlClass):
        data: XmlTextField[typing.Any]

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
    <root>
        {value}
    </root>
    """

    class RootString(XmlClass):
        data: XmlTextField[pathlib.Path]

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
    <root>
        {value}
    </root>
    """

    class RootString(XmlClass):
        data: XmlTextField[datetime.datetime]

    root = RootString.from_string(xml_with_datetime.strip())
    assert isinstance(root.data, datetime.datetime)
    assert root.data == datetime.datetime.fromisoformat(value)


# UNSURE: Do this even make sense?
def test_with_none() -> None:
    xml_with_none = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root>
        NULL
    </root>
    """

    class RootString(XmlClass):
        data: XmlTextField[None]

    root = RootString.from_string(xml_with_none.strip())
    assert root.data is None


def test_nested_element() -> None:
    xml_with_element = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root>
        <value>
            <data>data</data>
        </value>
    </root>
    """

    class Data(XmlClass):
        data: XmlTextField[str]

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
    <root>
        {value}
    </root>
    """

    class RootAttribute(XmlClass):
        value: XmlTextField[bool]

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
    <root>
        {value}
    </root>
    """

    class RootAttribute(XmlClass):
        value: XmlTextField[bool]

    root = RootAttribute.from_string(xml_with_attribute.strip())
    assert isinstance(root.value, bool)
    assert root.value is False


def test_with_literal_str() -> None:
    xml_with_attribute = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root>
        data
    </root>
    """

    class RootAttribute(XmlClass):
        value: XmlTextField[typing.Literal["data"]]

    root = RootAttribute.from_string(xml_with_attribute.strip())
    assert isinstance(root.value, str)
    assert root.value == "data"


def test_with_literal_int() -> None:
    xml_with_attribute = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root>
        1
    </root>
    """

    class RootAttribute(XmlClass):
        value: XmlTextField[typing.Literal[1]]

    root = RootAttribute.from_string(xml_with_attribute.strip())
    assert isinstance(root.value, int)
    assert root.value == 1


def test_with_enum() -> None:
    xml_with_attribute = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root>
        data
    </root>
    """

    class DataEnum(enum.Enum):
        DATA = "data"
        NO_DATA = "no_data"

    class RootAttribute(XmlClass):
        value: XmlTextField[DataEnum]

    root = RootAttribute.from_string(xml_with_attribute.strip())
    assert isinstance(root.value, DataEnum)
    assert root.value == DataEnum.DATA


def test_with_element_list_with_attribute_union() -> None:
    the_int = 2
    the_str = "data"

    xml_with_int = f"""
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root>
        {the_int}
    </root>
    """
    xml_with_str = f"""
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root>
        {the_str}
    </root>
    """

    class RootElement(XmlClass):
        value: XmlTextField[int | str]

    root = RootElement.from_string(xml_with_int.strip())
    assert isinstance(root.value, int)
    assert root.value == the_int

    root = RootElement.from_string(xml_with_str.strip())
    assert isinstance(root.value, str)
    assert root.value == the_str


def test_optional_field() -> None:
    xml_with_element = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root>
        <value></value>
    </root>
    """

    class Value(XmlClass):
        data: XmlTextField[str] | None

    class RootElement(XmlClass):
        value: Value

    root = RootElement.from_string(xml_with_element.strip())
    assert root.value.data is None

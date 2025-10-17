from typing import Literal
import re
import pytest

from xmlclasses import XmlClass
from xmlclasses import XmlParserError
from xmlclasses import XmlTextField


def test_with_boolean() -> None:
    xml_with_attribute = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root value="some_value" />
    """

    class RootAttribute(XmlClass):
        value: bool

    with pytest.raises(
        XmlParserError,
        match=re.escape(
            "Error in \"value\" while parsing element: \"root\", with attributes: {'value': 'some_value'}\n"
            "Boolean value some_value not in ['true', '1', 'yes', 'on'] or ['false', '0', 'no', 'off']",
        ),
    ):
        RootAttribute.from_string(xml_with_attribute.strip())


def test_with_literal() -> None:
    xml_with_attribute = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root value="notData" />
    """

    class RootAttribute(XmlClass):
        value: Literal["data"]

    with pytest.raises(XmlParserError, match=r"Literal value \"notData\" not in the defined values: \('data',\)"):
        RootAttribute.from_string(xml_with_attribute.strip())


def test_with_literal_different_type() -> None:
    xml_with_attribute = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root value="notData" />
    """

    class RootAttribute(XmlClass):
        value: Literal[111]

    with pytest.raises(XmlParserError, match=r"Literal value \"notData\" not in the defined values: \(111,\)"):
        RootAttribute.from_string(xml_with_attribute.strip())


def test_fail_on_data_flatting_element() -> None:
    xml_with_element = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root>
        <value>
            <subValue>
                data
            </subValue>
        </value>
    </root>
    """

    class Value(XmlClass):
        data: XmlTextField[str]

    class RootElement(XmlClass):
        sub_value: Value

    with pytest.raises(XmlParserError, match=r'Could not find "sub_value" in "root"'):
        RootElement.from_string(xml_with_element.strip())


def test_unknown_type() -> None:
    xml_with_attribute = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root value="some_value" />
    """

    class RootAttribute(XmlClass):
        value: pytest

    with pytest.raises(XmlParserError, match=re.escape("Unknown type: pytest")):
        RootAttribute.from_string(xml_with_attribute.strip())


def test_union_covert_error() -> None:
    xml_with_attribute = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root value="some_value"/>
    """

    class RootAttribute(XmlClass):
        value: int | float

    with pytest.raises(
        XmlParserError, match=re.escape('Unable to convert "value"\'s value: "some_value" to any of (int, float)'),
    ):
        RootAttribute.from_string(xml_with_attribute.strip())


def test_text_field_covert_error() -> None:
    xml_with_attribute = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root>
        some_value
    </root>
    """

    class RootAttribute(XmlClass):
        value: XmlTextField[int | float]

    with pytest.raises(
        XmlParserError, match=re.escape('Unable to convert "value"\'s value: "some_value" to any of (int, float)'),
    ):
        RootAttribute.from_string(xml_with_attribute.strip())


def test_missing_tuple_element() -> None:
    xml_with_attribute = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root>
        <value>data</value>
        <extra>data</extra>
    </root>
    """

    class Value(XmlClass):
        data: XmlTextField[str]

    class RootAttribute(XmlClass):
        value: tuple[Value, Value]

    with pytest.raises(XmlParserError, match=re.escape("Tuple expected 2 elements. Found: 1")):
        RootAttribute.from_string(xml_with_attribute.strip())


def test_extra_tuple_element() -> None:
    xml_with_attribute = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root>
        <value>data</value>
        <value>data</value>
        <value>data</value>
        <extra>data</extra>
    </root>
    """

    class Value(XmlClass):
        data: XmlTextField[str]

    class RootAttribute(XmlClass):
        value: tuple[Value, Value]

    with pytest.raises(XmlParserError, match=re.escape("Tuple expected 2 elements. Found: 3")):
        RootAttribute.from_string(xml_with_attribute.strip())


def test_extra_attribute() -> None:
    xml_with_attribute = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root value="your_value" extra="your_value" />
    """

    class RootAttribute(XmlClass):
        value: str

    with pytest.raises(XmlParserError, match=re.escape("Unexpected attribute(s): ['extra']")):
        RootAttribute.from_string(xml_with_attribute.strip())


def test_extra_attribute_with_element() -> None:
    xml_with_attribute = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root value="your_value" extra="your_value" >
        <extra data="your_value"/>
    </root>
    """

    class Extra(XmlClass):
        data: str

    class RootAttribute(XmlClass):
        value: str
        extra: Extra

    with pytest.raises(XmlParserError, match=re.escape("Unexpected attribute(s): ['extra']")):
        RootAttribute.from_string(xml_with_attribute.strip())


def test_missing_attribute_union() -> None:
    xml_with_attribute = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root/>
    """

    class RootAttribute(XmlClass):
        value: int | float

    with pytest.raises(
        XmlParserError, match=re.escape('Missing "value" in "root", with attributes: {} and children: '),
    ):
        RootAttribute.from_string(xml_with_attribute.strip())


def test_missing_attribute() -> None:
    xml_with_attribute = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root/>
    """

    class RootAttribute(XmlClass):
        value: int

    with pytest.raises(XmlParserError, match=re.escape('Missing attribute: "value"')):
        RootAttribute.from_string(xml_with_attribute.strip())


def test_extra_text_field() -> None:
    xml_with_attribute = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root value="data">data</root>
    """

    class RootAttribute(XmlClass):
        value: str

    with pytest.raises(XmlParserError, match=re.escape("Unexpected text field: data")):
        RootAttribute.from_string(xml_with_attribute.strip())


def test_extra_element() -> None:
    xml_with_attribute = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root>
        <value>data</value>
        <extra>data</extra>
    </root>
    """

    class Value(XmlClass):
        data: XmlTextField[str]

    class RootAttribute(XmlClass):
        value: Value

    with pytest.raises(XmlParserError, match=re.escape("Unexpected child(ren): ['extra']")):
        RootAttribute.from_string(xml_with_attribute.strip())


def test_nested_deep_element_error() -> None:
    xml_with_attribute = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root>
        <value>
            <sub_value>
                <sub_sub_value>data</sub_sub_value>
            </sub_value>
        </value>
    </root>
    """

    class SubSubValue(XmlClass):
        value_sub_sub_value: XmlTextField[int | float]

    class SubValue(XmlClass):
        sub_sub_value: SubSubValue

    class Value(XmlClass):
        sub_value: SubValue

    class RootAttribute(XmlClass):
        value: Value

    with pytest.raises(
        XmlParserError,
        match=re.escape(
            """Error in "value" while parsing element: "root".
Error in "sub_value" while parsing element: "value".
Error in "sub_sub_value" while parsing element: "sub_value".
Error in "value_sub_sub_value" while parsing element: "sub_sub_value".
Error in "value_sub_sub_value" while parsing element: "sub_sub_value", with attributes: {}
Unable to convert "value_sub_sub_value"'s value: "data" to any of (int, float)""",
        ),
    ):
        RootAttribute.from_string(xml_with_attribute.strip())

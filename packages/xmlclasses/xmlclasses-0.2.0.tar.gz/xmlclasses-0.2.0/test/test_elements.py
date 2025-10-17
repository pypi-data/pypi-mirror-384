import pytest

from xmlclasses import XmlClass
from xmlclasses import XmlTextField
from xmlclasses import XmlParserError


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


def test_with_element() -> None:
    xml_with_element = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root>
        <value>data</value>
    </root>
    """

    class Value(XmlClass):
        data: XmlTextField[str]

    class RootElement(XmlClass):
        value: Value

    root = RootElement.from_string(xml_with_element.strip())
    assert isinstance(root.value.data, str)
    assert isinstance(root.value, Value)
    assert root.value.data == "data"


def test_with_element_list() -> None:
    xml_with_element = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root>
        <value>data1</value>
        <value>data2</value>
    </root>
    """
    value_count = 2

    class Value(XmlClass):
        data: XmlTextField[str]

    class RootElement(XmlClass):
        value: list[Value]

    root = RootElement.from_string(xml_with_element.strip())
    assert isinstance(root.value, list)
    assert len(root.value) == value_count
    assert root.value[0].data == "data1"
    assert root.value[1].data == "data2"


def test_with_element_tuple() -> None:
    xml_with_element = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root>
        <value>data1</value>
        <value>data2</value>
    </root>
    """
    value_count = 2

    class Value(XmlClass):
        data: XmlTextField[str]

    class RootElement(XmlClass):
        value: tuple[Value, Value]

    root = RootElement.from_string(xml_with_element.strip())
    assert isinstance(root.value, tuple)
    assert len(root.value) == value_count
    assert root.value[0].data == "data1"
    assert root.value[1].data == "data2"


def test_no_xml_tag() -> None:
    xml_with_element = "<root />"

    class RootElement(XmlClass):
        value: None

    root = RootElement.from_string(xml_with_element.strip())
    assert root.value is None


def test_with_element_set() -> None:
    xml_with_element = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root>
        <value>data1</value>
    </root>
    """

    class Value(XmlClass):
        data: XmlTextField[str]

    class RootElement(XmlClass):
        value: set[Value]

    with pytest.raises(XmlParserError, match=r"Sets are not supported"):
        RootElement.from_string(xml_with_element.strip())


def test_optional_element() -> None:
    xml_with_element = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root>
        <value>data</value>
    </root>
    """

    class Value(XmlClass):
        data: XmlTextField[str]

    class RootElement(XmlClass):
        value: Value
        not_value: Value | None

    root = RootElement.from_string(xml_with_element.strip())
    assert isinstance(root.value.data, str)
    assert root.value.data == "data"
    assert root.not_value is None


def test_element_name_padding() -> None:
    xml_with_element = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root>
        <value data="data" />
    </root>
    """

    class Value(XmlClass):
        data: str

    class RootElement(XmlClass):
        value_: Value

    root = RootElement.from_string(xml_with_element.strip())
    assert isinstance(root.value_.data, str)
    assert root.value_.data == "data"


def test_element_name_padding_list() -> None:
    xml_with_element = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root>
        <value data="first" />
        <value data="second" />
    </root>
    """

    class Value(XmlClass):
        data: str

    class RootElement(XmlClass):
        value_: list[Value]

    root = RootElement.from_string(xml_with_element.strip())
    assert isinstance(root.value_, list)
    assert root.value_[0].data == "first"
    assert root.value_[1].data == "second"


def test_element_name_padding_union() -> None:
    xml_with_element = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root>
        <value data="first" />
    </root>
    """

    class Value(XmlClass):
        data: str

    class RootElement(XmlClass):
        value_: Value | list[Value]

    root = RootElement.from_string(xml_with_element.strip())
    assert isinstance(root.value_, Value)
    assert root.value_.data == "first"


def test_element_name_padding_union_none() -> None:
    xml_with_element = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root>
        <value data="first" />
    </root>
    """

    class Value(XmlClass):
        data: str

    class RootElement(XmlClass):
        value_: None | Value

    root = RootElement.from_string(xml_with_element.strip())
    assert isinstance(root.value_, Value)
    assert root.value_.data == "first"


def test_element_name_padding_union_none_empty() -> None:
    xml_with_element = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root />
    """

    class Value(XmlClass):
        data: str

    class RootElement(XmlClass):
        value_: None | Value

    root = RootElement.from_string(xml_with_element.strip())
    assert root.value_ is None


def test_element_name_with_dash() -> None:
    xml_with_element = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root>
        <value-with-dash data="first" />
    </root>
    """

    class Value(XmlClass):
        data: str

    class RootElement(XmlClass):
        value_with_dash: Value

    root = RootElement.from_string(xml_with_element.strip())
    assert isinstance(root.value_with_dash, Value)
    assert root.value_with_dash.data == "first"


def test_element_name_with_dash_union_none() -> None:
    xml_with_element = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root>
        <value-with-dash data="first" />
    </root>
    """

    class Value(XmlClass):
        data: str

    class RootElement(XmlClass):
        value_with_dash: None | Value

    root = RootElement.from_string(xml_with_element.strip())
    assert isinstance(root.value_with_dash, Value)
    assert root.value_with_dash.data == "first"


def test_element_name_with_dash_union() -> None:
    xml_with_element = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root>
        <value-with-dash data="first" />
    </root>
    """

    class Value(XmlClass):
        data: str

    class RootElement(XmlClass):
        value_with_dash: Value | list[Value]

    root = RootElement.from_string(xml_with_element.strip())
    assert isinstance(root.value_with_dash, Value)
    assert root.value_with_dash.data == "first"


def test_element_name_with_dash_union_none_empty() -> None:
    xml_with_element = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root />
    """

    class Value(XmlClass):
        data: str

    class RootElement(XmlClass):
        value_with_dash: None | Value

    root = RootElement.from_string(xml_with_element.strip())
    assert root.value_with_dash is None

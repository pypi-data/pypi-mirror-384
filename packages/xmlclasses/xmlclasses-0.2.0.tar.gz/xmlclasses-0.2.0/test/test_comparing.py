from xmlclasses import XmlClass
from xmlclasses import XmlTextField



def test_equal_with_text_field_string() -> None:
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
    root2 = RootElement.from_string(xml_with_element.strip())
    assert root == root2


def test_equal_with_attribute_string() -> None:
    xml_with_string = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root data="data">
    </root>
    """

    class RootString(XmlClass):
        data: str

    root = RootString.from_string(xml_with_string.strip())
    root2 = RootString.from_string(xml_with_string.strip())
    assert root == root2


def test_not_equal_with_text_field_string() -> None:
    xml_with_element = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root>
        <value>data</value>
    </root>
    """
    xml_with_element2 = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root>
        <value>data2</value>
    </root>
    """

    class Value(XmlClass):
        data: XmlTextField[str]

    class RootElement(XmlClass):
        value: Value

    root = RootElement.from_string(xml_with_element.strip())
    root2 = RootElement.from_string(xml_with_element2.strip())
    assert root != root2


def test_not_equal_with_attribute_string() -> None:
    xml_with_string = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root data="data">
    </root>
    """
    xml_with_string2 = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root data="data2">
    </root>
    """

    class RootString(XmlClass):
        data: str

    root = RootString.from_string(xml_with_string.strip())
    root2 = RootString.from_string(xml_with_string2.strip())
    assert root != root2


def test_equal_different_types() -> None:
    xml_with_string = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root data="data">
    </root>
    """
    xml_with_string2 = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <root bla="data">
    </root>
    """

    class RootString(XmlClass):
        data: str

    class RootString2(XmlClass):
        bla: str

    root = RootString.from_string(xml_with_string.strip())
    root2 = RootString2.from_string(xml_with_string2.strip())
    assert (root == root2) is False

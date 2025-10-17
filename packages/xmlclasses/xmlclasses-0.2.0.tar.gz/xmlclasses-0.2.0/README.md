XML Classes
===================================================================

Simple, fast, lightweight xml parser and validator defined by classes,
and useful error messages.

Reason to pick this over other xml parsers:
 * Non alias. (Harder to match tag/attribute name with the class variable name)
 * Need advanced features. (Like default factory, custom decoder, custom encoder etc.)


TODO: Speed test against `pydantic-xml` and `xmltodict` with `pydantic`.

Basic examples:
-------------------------------------------------------------------

For the following XML:
```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<root value="data" />
```

The following python class can be used to parse it:
```python
class RootAttribute(XmlClass):
    value: str
```
It automatically assumes it is an xml tag attribute.

And then parse it:
```python
    root = RootAttribute.from_string(xml_string)
```

For the following XML:
```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<root>
    <value value="data"/>
</root>
```

The following python class can be used to parse it:
```python
class Value(XmlClass):
    value: str

class RootElement(XmlClass):
    value: Value
```

When the type is set to be of XmlClass, it will be parsed as a sub element.

For xml text field, it is a bit more complex.
For the following XML:
"""
<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<root>
    data1
</root>
"""

The following python class can be used to parse it:
```python
class Value(XmlClass):
    data: XmlTextField[str]
```

When the type is set to be of XmlTextField, it will be parsed as a text field,
where the text-field is of the type given in the square brackets.


Supported Annotations type:
-------------------------------------------------------------------
 * int
 * float
 * str
 * bool [^4]
 * None
 * datetime.datetime [^2]
 * uuid.UUID
 * pathlib.Path
 * typing.Any [^3]
 * Literal
 * Enum
 * list [^1]
 * tuple [^1]
 * union
 * XmlClass
 * XmlTextField

[^1]: Assume that the children can only be of type: XmlClass.
    Since multiple attributes are not allowed, and a data separator
    is not defined.
[^2]: Is parsed by the `datetime.datetime.fromisoformat` method.
[^3]: Is parsed as is (as string). Only check if there is data. 
[^4]: Where ["true", "1", "yes", "on"] is true and ["false", "0", "no", "off"] is false.


Other Info:
-------------------------------------------------------------------

### Trailing underscore
Trailing underscore is ignored when mapping from XML to python class.
It is used in the casses where a child element tag and a attribute 
have the same name. Through not a requirement, the trailing underscore
should be used in the attribute name.

### Dash in tag or Attribute names
Since dash in python name is not allowed, dash in tag or attribute name
is replaced with underscore.



NOTE:
===================================================================
 * This is a work in progress, ATM it only parses the XML data, to a python class.
 * UNSURE: Do None type hint as the only one even make sense?
 * UNSURE: Should null value be None type hint, and something else for optional?

Tests TODO:
===================================================================
 * [ ] Test `XmlClass | None` case, where there is parsing error in XmlClass.
 * [ ] Test `OneTwo: typing.Literal["firstPasser", "secondPasser"] | None` case, where it do not Exist.
 * [ ] Test `xmlClass | AnotherXmlClass` case, with different Names.

TODO:
===================================================================
 * [ ] Make the error messages better for when there is a error deep inside a xmlClass.
 * [x] Make a test for typing.Any.
 * [ ] Added `defusedxml` as dependency. (Security reasons)
 * [x] Fix ALL type hints...
 * [ ] Add support for decoder and encoder.
 * [ ] Add support for custom parsers. (XmlDataParser[MyParserOfData])
 * [x] Make good and useful error messages.

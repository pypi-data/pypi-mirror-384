from __future__ import annotations

import contextlib
import typing

if typing.TYPE_CHECKING:
    import xml.etree.ElementTree as ET


class XmlParserError(ValueError):
    pass
    # TODO: Add a append error for better error messages.


@contextlib.contextmanager
def error_handler(data: ET.Element, name: str) -> typing.Generator[None, None, None]:
    try:
        yield
    except XmlParserError as e:
        error_msg = f'Error in "{name}" while parsing element: "{data.tag}".\n'
        error_msg += str(e)
        raise XmlParserError(error_msg) from e
    except KeyError as e:
        error_msg = f'Error in "{name}" while parsing element: "{data.tag}", with attributes: {data.attrib}\n'
        error_msg += f"Could not find key: {e!s}"
        raise XmlParserError(error_msg) from e
    except ValueError as e:
        error_msg = f'Error in "{name}" while parsing element: "{data.tag}", with attributes: {data.attrib}\n'
        error_msg += str(e)
        raise XmlParserError(error_msg) from e
    except Exception as e:
        error_msg = f'Error in "{name}" while parsing element: "{data.tag}", with attributes: {data.attrib}\n'
        error_msg += str(e)
        raise XmlParserError(error_msg) from e

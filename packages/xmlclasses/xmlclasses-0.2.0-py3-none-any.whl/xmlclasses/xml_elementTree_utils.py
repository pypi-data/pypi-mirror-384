import xml.etree.ElementTree as ET


def _get_child_from(tag: str, dom: ET.Element, *, single: bool = False) -> list[ET.Element] | ET.Element:
    """
    Retrieve child element from Element, if exists else remove trailing '_' and try again.

    Args:
        tag: The tag to look for (potentially padded with underscores).
        dom: The Element to search within.
        single: If True, return only the first matching child.

    Returns:
        The child element associated with the tag, or ValueError if neither tag is found.

    """
    if not single:
        return [x for x in dom if x.tag == tag or x.tag == tag.rstrip("_") or x.tag == tag.replace("_", "-")]

    for child in dom:
        if child.tag == tag or child.tag == tag.rstrip("_") or child.tag == tag.replace("_", "-"):
            return child
    msg = f'Could not find "{tag}" in "{dom.tag}"'
    raise ValueError(msg)


def _get_value_with_fallback(dom: ET.Element, name: str) -> str | None:
    """
    Retrieve value from Element, if exists else remove trailing '_' and try again.

    Args:
        dom: The Element to search within.
        name: The key to look for (potentially padded with underscores).

    Returns:
        The value associated with the key, or None if neither key is found.

    """
    if name in dom.attrib:
        return dom.attrib[name]
    if name.replace("_", "-") in dom.attrib:
        return dom.attrib[name.replace("_", "-")]
    return dom.attrib.get(name.rstrip("_"))

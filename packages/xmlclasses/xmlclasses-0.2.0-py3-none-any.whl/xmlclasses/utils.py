from __future__ import annotations

import dataclasses

from .base_types import XmlAttributeField
from .base_types import XmlElementField
from .base_types import XmlTextField


def field(
    *,
    attribute: bool = False,
    element: bool = False,
    text: bool = False,
    alias=dataclasses.MISSING,
    default=dataclasses.MISSING,
    default_factory=dataclasses.MISSING,
    init=True,
    repr=True,
    hash=None,
    compare=True,
    metadata=None,
    kw_only=dataclasses.MISSING,
):
    """
    Return an object to identify dataclass fields.

    attribute is a boolean that indicates whether the field is an
    attribute.  element is a boolean that indicates whether the field
    is an element.  alias is the name of the alias of the field.
    default is the default value of the field.  default_factory is a
    0-argument function called to initialize a field's value.  If init
    is true, the field will be a parameter to the class's __init__()
    function.  If repr is true, the field will be included in the
    object's repr().  If hash is true, the field will be included in the
    object's hash().  If compare is true, the field will be used in
    comparison functions.  metadata, if specified, must be a mapping
    which is stored but not otherwise examined by dataclass.  If kw_only
    is true, the field will become a keyword-only parameter to
    __init__().

    It is an error to specify both default and default_factory.
    It is an error to specify both attribute and element, it should be one or the other.
    """
    if default is not dataclasses.MISSING and default_factory is not dataclasses.MISSING:
        msg = "cannot specify both default and default_factory"
        raise ValueError(msg)
    if attribute is True and element is False and text is False:
        return XmlAttributeField(
            alias,
            default,
            default_factory,
            init,
            repr,
            hash,
            compare,
            metadata,
            kw_only,
        )
    if element is True and attribute is False and text is False:
        return XmlElementField(
            alias,
            default,
            default_factory,
            init,
            repr,
            hash,
            compare,
            metadata,
            kw_only,
        )
    if text is True and attribute is False and element is False:
        return XmlTextField(
            alias,
            default,
            default_factory,
            init,
            repr,
            hash,
            compare,
            metadata,
            kw_only,
        )
    msg = "One of attribute, element or text should be Set to True."
    raise ValueError(msg)

from __future__ import annotations

import dataclasses


class XmlBaseType(dataclasses.Field):
    __slots__ = (
        "_field_type",  # Private: not to be used by user code.
        "alias",
        "compare",
        "default",
        "default_factory",
        "hash",
        "init",
        "kw_only",
        "metadata",
        "name",
        "repr",
        "type",
    )

    def __init__(self, alias, default, default_factory, init, repr, hash, compare, metadata, kw_only) -> None:
        self.alias = alias
        super().__init__(default, default_factory, init, repr, hash, compare, metadata, kw_only)


class XmlAttributeField(XmlBaseType):
    pass


class XmlElementField(XmlBaseType):
    pass


class XmlTextField(XmlBaseType):
    pass

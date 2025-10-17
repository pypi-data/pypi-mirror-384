from __future__ import annotations

from mcdplib.core.string import contains_only


class Identifier:
    @classmethod
    def identifier(cls, identifier: IdentifierLike) -> Identifier:
        if isinstance(identifier, str):
            if identifier.count(":") != 1:
                raise ValueError("Invalid identifier format")
            namespace, name = identifier.split(":")
            return Identifier(
                namespace=namespace,
                name=name
            )
        if isinstance(identifier, Identifier):
            return identifier
        raise TypeError(f"Wrong identifier-like type: {type(identifier)}")

    def __init__(self, namespace: str, name: str):
        if not contains_only(namespace, "0123456789abcdefghijklmnopqrstuvwxyz_-."):
            raise ValueError(f"Invalid identifier namespace: {namespace}")
        if not contains_only(name, "0123456789abcdefghijklmnopqrstuvwxyz_-./"):
            raise ValueError(f"Invalid identifier name: {name}")
        self.namespace: str = namespace
        self.name: str = name

    def __str__(self):
        return f"{self.namespace}:{self.name}"


IdentifierLike = str | Identifier

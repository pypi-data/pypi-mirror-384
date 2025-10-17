from __future__ import annotations
from mcdplib.core.identifier import Identifier, IdentifierLike
from mcdplib.core.string import contains_only
import os


class Resource:
    def __init__(self, registry: str, identifier: IdentifierLike):
        self.registry: str = registry
        self.identifier: Identifier = Identifier.identifier(identifier)

    def write(self, file: str) -> None:
        pass


class ResourceRegistry:
    def __init__(self, name: str, allowed_resource_types: list[type], file_extension: str):
        if not contains_only(name, "0123456789abcdefghijklmnopqrstuvwxyz_-./"):
            raise ValueError(f"Invalid registry name: {name}")
        self.name: str = name
        self.allowed_resource_types: list[type] = allowed_resource_types
        self.file_extension: str = file_extension
        self.__resources: dict[str, Resource] = dict()

    def add(self, resource: Resource) -> Resource:
        for allowed_resource_type in self.allowed_resource_types:
            if isinstance(resource, allowed_resource_type):
                break
        else:
            raise TypeError(f"Wrong resource type: {type(resource)}")
        if resource.identifier.__str__() in self.__resources:
            raise KeyError(f"Resource with identifier {resource.identifier} already exists")
        self.__resources[resource.identifier.__str__()] = resource
        return resource

    def write(self, data_directory: str) -> None:
        for resource in self.__resources.values():
            resource_file = f"{data_directory}/{resource.identifier.namespace}/{self.name}/{resource.identifier.name}.{self.file_extension}"
            resource_directory = os.path.dirname(resource_file)
            os.makedirs(resource_directory, exist_ok=True)
            resource.write(resource_file)

    def __iter__(self):
        return self.__resources.values().__iter__()


class ResourceBuilder:
    def __init__(self, registry: str, identifier: IdentifierLike):
        self.registry: str = registry
        self.identifier: Identifier = Identifier.identifier(identifier)

    def build(self, context: dict) -> list[Resource]:
        resources: list[Resource] = list()
        return resources


class ResourceBuilderLoader:
    def __init__(self, file_extensions: list[str]):
        self.file_extensions: list[str] = file_extensions

    def load(self, directory: str, file: str, registry: str, identifier: Identifier) -> ResourceBuilder:
        return ResourceBuilder(
            registry=registry,
            identifier=identifier
        )

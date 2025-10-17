from mcdplib.core.identifier import Identifier, IdentifierLike
from mcdplib.core.resource.resource import Resource, ResourceBuilder, ResourceBuilderLoader
from mcdplib.core.file import read_binary_file, write_binary_file


class BinaryResource(Resource):
    def __init__(self, registry: str, identifier: IdentifierLike, data: bytes):
        super().__init__(registry, identifier)
        self.data: bytes = data

    def write(self, file: str) -> None:
        write_binary_file(file, self.data)

class BinaryResourceBuilder(ResourceBuilder):
    def build(self, context: dict) -> list[BinaryResource]:
        resources: list[BinaryResource] = list()
        return resources


class StaticBinaryResourceBuilder(BinaryResourceBuilder):
    def __init__(self, registry: str, identifier: IdentifierLike, resource_data: bytes):
        super().__init__(registry, identifier)
        self.resource_data: bytes = resource_data

    def build(self, context: dict) -> list[BinaryResource]:
        resources: list[BinaryResource] = list()
        resources.append(BinaryResource(
            registry=self.registry,
            identifier=self.identifier,
            data=self.resource_data
        ))
        return resources


class StaticBinaryResourceBuilderLoader(ResourceBuilderLoader):
    def load(self, directory: str, file: str, registry: str, identifier: Identifier) -> StaticBinaryResourceBuilder:
        return StaticBinaryResourceBuilder(
            registry=registry,
            identifier=identifier,
            resource_data=read_binary_file(file)
        )

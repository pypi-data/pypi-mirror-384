from mcdplib.core.identifier import Identifier, IdentifierLike
from mcdplib.core.resource.resource import Resource, ResourceBuilder, ResourceBuilderLoader
from mcdplib.core.file import read_text_file, write_text_file


class StringResource(Resource):
    def __init__(self, registry: str, identifier: IdentifierLike, data: str):
        super().__init__(registry, identifier)
        self.data: str = data

    def write(self, file: str) -> None:
        write_text_file(file, self.data)


class StringResourceBuilder(ResourceBuilder):
    def build(self, context: dict) -> list[StringResource]:
        resources: list[StringResource] = list()
        return resources


class StaticStringResourceBuilder(StringResourceBuilder):
    def __init__(self, registry: str, identifier: IdentifierLike, resource_data: str):
        super().__init__(registry, identifier)
        self.resource_data: str = resource_data

    def build(self, context: dict) -> list[StringResource]:
        resources: list[StringResource] = list()
        resources.append(StringResource(
            registry=self.registry,
            identifier=self.identifier,
            data=self.resource_data
        ))
        return resources


class StaticStringResourceBuilderLoader(ResourceBuilderLoader):
    def load(self, directory: str, file: str, registry: str, identifier: Identifier) -> StaticStringResourceBuilder:
        return StaticStringResourceBuilder(
            registry=registry,
            identifier=identifier,
            resource_data=read_text_file(file)
        )

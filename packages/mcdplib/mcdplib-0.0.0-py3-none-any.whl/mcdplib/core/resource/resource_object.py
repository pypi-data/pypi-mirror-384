from mcdplib.core.identifier import IdentifierLike, Identifier
from mcdplib.core.evaluation import execute
from mcdplib.core.resource.resource import Resource, ResourceBuilder, ResourceBuilderLoader
from mcdplib.core.file import read_text_file, read_json_file, write_json_file


class ObjectResource(Resource):
    def __init__(self, registry: str, identifier: IdentifierLike, data: dict):
        super().__init__(registry, identifier)
        self.data: dict = data

    def write(self, file: str) -> None:
        write_json_file(file, self.data)


class ObjectResourceBuilder(ResourceBuilder):
    REGISTRY_FIELD = "registry"
    IDENTIFIER_FIELD = "id"

    def create_resource(self, resource_data: dict) -> ObjectResource:
        registry: str = self.registry
        identifier: IdentifierLike = self.identifier
        if ObjectResourceBuilder.REGISTRY_FIELD in resource_data:
            registry = resource_data[ObjectResourceBuilder.REGISTRY_FIELD]
            resource_data.pop(ObjectResourceBuilder.REGISTRY_FIELD)
        if ObjectResourceBuilder.IDENTIFIER_FIELD in resource_data:
            identifier = resource_data[ObjectResourceBuilder.IDENTIFIER_FIELD]
            resource_data.pop(ObjectResourceBuilder.IDENTIFIER_FIELD)
        return ObjectResource(
            registry=registry,
            identifier=identifier,
            data=resource_data
        )

    def build(self, context: dict) -> list[ObjectResource]:
        resources: list[ObjectResource] = list()
        return resources


class StaticObjectResourceBuilder(ObjectResourceBuilder):
    def __init__(self, registry: str, identifier: IdentifierLike, resource_data: dict):
        super().__init__(registry, identifier)
        self.resource_data: dict = resource_data

    def build(self, context: dict) -> list[ObjectResource]:
        resources: list[ObjectResource] = list()
        resources.append(self.create_resource(self.resource_data))
        return resources


class DynamicObjectResourceBuilder(ObjectResourceBuilder):
    RESOURCE_FIELD = "resource"
    RESOURCES_FIELD = "resources"

    def __init__(self, registry: str, identifier: IdentifierLike, source: str):
        super().__init__(registry, identifier)
        self.source: str = source

    def build(self, context: dict) -> list[ObjectResource]:
        resources: list[ObjectResource] = list()
        execute(self.source, context)
        if DynamicObjectResourceBuilder.RESOURCE_FIELD in context:
            resources.append(self.create_resource(context[DynamicObjectResourceBuilder.RESOURCE_FIELD]))
        if DynamicObjectResourceBuilder.RESOURCES_FIELD in context:
            for resource_data in context[DynamicObjectResourceBuilder.RESOURCES_FIELD]:
                resources.append(self.create_resource(resource_data))
        return resources


class StaticObjectResourceBuilderLoader(ResourceBuilderLoader):
    def load(self, directory: str, file: str, registry: str, identifier: Identifier) -> StaticObjectResourceBuilder:
        return StaticObjectResourceBuilder(
            registry=registry,
            identifier=identifier,
            resource_data=read_json_file(file)
        )


class DynamicObjectResourceBuilderLoader(ResourceBuilderLoader):
    def load(self, directory: str, file: str, registry: str, identifier: Identifier) -> DynamicObjectResourceBuilder:
        return DynamicObjectResourceBuilder(
            registry=registry,
            identifier=identifier,
            source=read_text_file(file)
        )

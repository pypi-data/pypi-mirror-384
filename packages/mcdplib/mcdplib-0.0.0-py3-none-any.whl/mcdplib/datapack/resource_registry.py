from mcdplib.core.resource.resource import ResourceRegistry, ResourceBuilderLoader


class DatapackResourceRegistry(ResourceRegistry):
    def __init__(self, name: str, allowed_resource_types: list[type], file_extension: str, resource_builder_loaders: list[ResourceBuilderLoader]):
        super().__init__(name, allowed_resource_types, file_extension)
        self.resource_builder_loaders: list[ResourceBuilderLoader] = resource_builder_loaders

from mcdplib.core.resource.resource import ResourceRegistry, Resource

r = ResourceRegistry(
    name="a",
    allowed_resource_types=[Resource],
    file_extension="test"
)
r.add(Resource(
    registry="a",
    identifier="a:b"
))
r.add(1)
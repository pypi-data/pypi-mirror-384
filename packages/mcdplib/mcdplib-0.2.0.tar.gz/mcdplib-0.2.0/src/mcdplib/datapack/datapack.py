from __future__ import annotations
from mcdplib.core.identifier import Identifier
from mcdplib.core.file import write_json_file
from mcdplib.core.resource.resource import Resource, ResourceBuilder
from mcdplib.core.resource.resource_binary import BinaryResource, StaticBinaryResourceBuilderLoader
from mcdplib.core.resource.resource_object import ObjectResource, StaticObjectResourceBuilderLoader, DynamicObjectResourceBuilderLoader
from mcdplib.core.resource.resource_string import StringResource, StaticStringResourceBuilderLoader
from mcdplib.datapack.function import FunctionResourceBuilderLoader
from mcdplib.core.pack import Pack
from mcdplib.datapack.function_template import FunctionTemplateResourceBuilderLoader
from mcdplib.datapack.resource_registry import DatapackResourceRegistry
import shutil
import os


class Datapack(Pack):
    DATAPACK_FIELD = "datapack"
    RESOURCE_BUILDER_FIELD = "resource_builder"

    def __init__(self, information: dict):
        super().__init__(information)
        self.__registries: dict[str, DatapackResourceRegistry] = dict()

        self.resource_builders: list[ResourceBuilder] = list()

        self.functions: DatapackResourceRegistry = self.add_registry(DatapackResourceRegistry(
            name="function",
            allowed_resource_types=[StringResource],
            file_extension="mcfunction",
            resource_builder_loaders=[
                StaticStringResourceBuilderLoader(
                    file_extensions=["mcfunction"]
                ),
                FunctionResourceBuilderLoader(
                    file_extensions=["mcf"]
                ),
                FunctionTemplateResourceBuilderLoader(
                    file_extensions=["mcft"]
                )
            ]
        ))
        self.structures: DatapackResourceRegistry = self.add_registry(DatapackResourceRegistry(
            name="structure",
            allowed_resource_types=[BinaryResource],
            file_extension="nbt",
            resource_builder_loaders=[StaticBinaryResourceBuilderLoader(
                file_extensions=["nbt"]
            )]
        ))

        def create_object_resource_registry(registry_name: str) -> DatapackResourceRegistry:
            return self.add_registry(DatapackResourceRegistry(
                name=registry_name,
                allowed_resource_types=[ObjectResource],
                file_extension="json",
                resource_builder_loaders=[
                    StaticObjectResourceBuilderLoader(
                        file_extensions=["json"]
                    ),
                    DynamicObjectResourceBuilderLoader(
                        file_extensions=["py"]
                    )
                ]
            ))

        self.banner_pattern_tags: DatapackResourceRegistry = create_object_resource_registry("tags/banner_pattern")
        self.block_tags: DatapackResourceRegistry = create_object_resource_registry("tags/block")
        self.damage_type_tags: DatapackResourceRegistry = create_object_resource_registry("tags/damage_type")
        self.dialog_tags: DatapackResourceRegistry = create_object_resource_registry("tags/dialog")
        self.enchantment_tags: DatapackResourceRegistry = create_object_resource_registry("tags/enchantment")
        self.entity_type_tags: DatapackResourceRegistry = create_object_resource_registry("tags/entity_type")
        self.fluid_tags: DatapackResourceRegistry = create_object_resource_registry("tags/fluid")
        self.function_tags: DatapackResourceRegistry = create_object_resource_registry("tags/function")
        self.game_event_tags: DatapackResourceRegistry = create_object_resource_registry("tags/game_event")
        self.instrument_tags: DatapackResourceRegistry = create_object_resource_registry("tags/instrument")
        self.item_tags: DatapackResourceRegistry = create_object_resource_registry("tags/item")
        self.painting_variant_tags: DatapackResourceRegistry = create_object_resource_registry("tags/painting_variant")
        self.point_of_interest_type_tags: DatapackResourceRegistry = create_object_resource_registry("tags/point_of_interest_type")
        self.worldgen_biome_tags: DatapackResourceRegistry = create_object_resource_registry("tags/worldgen/biome")
        self.worldgen_flat_level_generator_preset_tags: DatapackResourceRegistry = create_object_resource_registry("tags/worldgen/flat_level_generator_preset")
        self.worldgen_structure_tags: DatapackResourceRegistry = create_object_resource_registry("tags/worldgen/structure")
        self.worldgen_world_preset_tags: DatapackResourceRegistry = create_object_resource_registry("tags/worldgen/world_preset")

        self.advancements: DatapackResourceRegistry = create_object_resource_registry("advancement")
        self.banner_patterns: DatapackResourceRegistry = create_object_resource_registry("banner_pattern")
        self.cat_variants: DatapackResourceRegistry = create_object_resource_registry("cat_variant")
        self.chat_types: DatapackResourceRegistry = create_object_resource_registry("chat_type")
        self.chicken_variants: DatapackResourceRegistry = create_object_resource_registry("chicken_variant")
        self.cow_variants: DatapackResourceRegistry = create_object_resource_registry("cow_variant")
        self.damage_types: DatapackResourceRegistry = create_object_resource_registry("damage_type")
        self.dialogs: DatapackResourceRegistry = create_object_resource_registry("dialog")
        self.dimensions: DatapackResourceRegistry = create_object_resource_registry("dimension")
        self.dimension_types: DatapackResourceRegistry = create_object_resource_registry("dimension_type")
        self.enchantments: DatapackResourceRegistry = create_object_resource_registry("enchantment")
        self.enchantment_providers: DatapackResourceRegistry = create_object_resource_registry("enchantment_provider")
        self.frog_variants: DatapackResourceRegistry = create_object_resource_registry("frog_variant")
        self.instruments: DatapackResourceRegistry = create_object_resource_registry("instrument")
        self.item_modifiers: DatapackResourceRegistry = create_object_resource_registry("item_modifier")
        self.jukebox_songs: DatapackResourceRegistry = create_object_resource_registry("jukebox_song")
        self.loot_tables: DatapackResourceRegistry = create_object_resource_registry("loot_table")
        self.painting_variants: DatapackResourceRegistry = create_object_resource_registry("painting_variant")
        self.pig_variants: DatapackResourceRegistry = create_object_resource_registry("pig_variant")
        self.predicates: DatapackResourceRegistry = create_object_resource_registry("predicate")
        self.recipes: DatapackResourceRegistry = create_object_resource_registry("recipe")
        self.test_environments: DatapackResourceRegistry = create_object_resource_registry("test_environment")
        self.test_instances: DatapackResourceRegistry = create_object_resource_registry("test_instance")
        self.trial_spawners: DatapackResourceRegistry = create_object_resource_registry("trial_spawner")
        self.trim_materials: DatapackResourceRegistry = create_object_resource_registry("trim_material")
        self.trim_patterns: DatapackResourceRegistry = create_object_resource_registry("trim_pattern")
        self.wolf_sound_variants: DatapackResourceRegistry = create_object_resource_registry("wolf_sound_variant")
        self.wolf_variants: DatapackResourceRegistry = create_object_resource_registry("wolf_variant")

        self.worldgen_biomes: DatapackResourceRegistry = create_object_resource_registry("worldgen/biome")
        self.worldgen_configured_carvers: DatapackResourceRegistry = create_object_resource_registry("worldgen/configured_carver")
        self.worldgen_configured_features: DatapackResourceRegistry = create_object_resource_registry("worldgen/configured_feature")
        self.worldgen_density_functions: DatapackResourceRegistry = create_object_resource_registry("worldgen/density_function")
        self.worldgen_noises: DatapackResourceRegistry = create_object_resource_registry("worldgen/noise")
        self.worldgen_noise_settings: DatapackResourceRegistry = create_object_resource_registry("worldgen/noise_settings")
        self.worldgen_placed_features: DatapackResourceRegistry = create_object_resource_registry("worldgen/placed_feature")
        self.worldgen_processor_lists: DatapackResourceRegistry = create_object_resource_registry("worldgen/processor_list")
        self.worldgen_structures: DatapackResourceRegistry = create_object_resource_registry("worldgen/structure")
        self.worldgen_structure_sets: DatapackResourceRegistry = create_object_resource_registry("worldgen/structure_set")
        self.worldgen_template_pools: DatapackResourceRegistry = create_object_resource_registry("worldgen/template_pool")
        self.worldgen_world_presets: DatapackResourceRegistry = create_object_resource_registry("worldgen/world_preset")
        self.worldgen_flat_level_generator_presets: DatapackResourceRegistry = create_object_resource_registry("worldgen/flat_level_generator_preset")
        self.worldgen_multi_noise_biome_source_parameter_lists: DatapackResourceRegistry = create_object_resource_registry("worldgen/multi_noise_biome_source_parameter_list")

    def get_registry(self, name: str) -> DatapackResourceRegistry:
        if name not in self.__registries:
            raise KeyError(f"Registry with name {name} does not exist")
        return self.__registries[name]

    def add_registry(self, registry: DatapackResourceRegistry) -> DatapackResourceRegistry:
        if registry.name in self.__registries:
            raise KeyError(f"Registry with name {registry.name} already exists")
        self.__registries[registry.name] = registry
        return registry

    def load(self, data_directory: str) -> Datapack:
        def load_resource_builders_in_directory(directory: str, parent_name: str | None = None) -> list[ResourceBuilder]:
            resource_builders: list[ResourceBuilder] = list()
            for local_entry in os.listdir(directory):
                entry: str = f"{directory}/{local_entry}"
                if os.path.isdir(entry):
                    child_name: str = local_entry
                    if parent_name is not None:
                        child_name = f"{parent_name}/{local_entry}"
                    resource_builders.extend(load_resource_builders_in_directory(entry, child_name))
                elif os.path.isfile(entry):
                    local_name, extension = os.path.splitext(local_entry)
                    extension = extension.removeprefix(".")
                    name: str = local_name
                    if parent_name is not None:
                        name = f"{parent_name}/{local_name}"
                    for resource_builder_loader in registry.resource_builder_loaders:
                        if extension in resource_builder_loader.file_extensions:
                            resource_builders.append(resource_builder_loader.load(directory, entry, registry.name, Identifier(namespace, name)))
            return resource_builders

        for registry in self.__registries.values():
            for namespace in os.listdir(data_directory):
                namespace_directory: str = f"{data_directory}/{namespace}"
                registry_directory: str = f"{namespace_directory}/{registry.name}"
                if not os.path.exists(registry_directory):
                    continue
                self.resource_builders.extend(load_resource_builders_in_directory(registry_directory))

        return self

    def build(self, context: dict) -> Datapack:
        context[Datapack.DATAPACK_FIELD] = self
        for resource_builder in self.resource_builders:
            context[Datapack.RESOURCE_BUILDER_FIELD] = resource_builder
            resources: list[Resource] = resource_builder.build(context)
            for resource in resources:
                self.get_registry(resource.registry).add(resource)
        return self

    def write(self, directory: str) -> Datapack:
        if os.path.exists(directory):
            shutil.rmtree(directory)
        os.makedirs(directory, exist_ok=True)
        write_json_file(f"{directory}/pack.mcmeta", self.information)
        data_directory = f"{directory}/data"
        for registry in self.__registries.values():
            registry.write(data_directory)
        return self

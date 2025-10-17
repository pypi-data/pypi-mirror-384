from __future__ import annotations
from mcdplib.core.evaluation import evaluate, evaluate_substrings
from mcdplib.core.identifier import Identifier, IdentifierLike
from mcdplib.core.resource.resource_string import StringResource, StringResourceBuilder
from mcdplib.core.resource.resource import ResourceBuilderLoader
from mcdplib.core.file import read_text_file
from typing import Callable


class FunctionSegment:
    def __init__(self, parent: FunctionSegment | None = None):
        self.parent: FunctionSegment | None = parent

    def build(self, function: Function, context: dict) -> str:
        pass


class LineFunctionSegment(FunctionSegment):
    def __init__(self, code: str, parent: FunctionSegment | None = None):
        super().__init__(parent)
        self.code: str = code

    def build(self, function: Function, context: dict) -> str:
        return evaluate_substrings(self.code, context, expression_boundary_characters=Function.EXPRESSION_BOUNDARY_CHARACTERS)


class ContainerFunctionSegment(FunctionSegment):
    def __init__(self, entries: list[FunctionSegment], parent: FunctionSegment | None = None):
        super().__init__(parent)
        self.entries: list[FunctionSegment] = entries

    def build(self, function: Function, context: dict) -> str:
        string = ""
        for entry in self.entries:
            string += entry.build(function, context) + "\n"
        return string


class ForeachRepeaterContainerFunctionSegment(ContainerFunctionSegment):
    def __init__(self, item_name: str, iterable_expression: str, entries: list[FunctionSegment], parent: FunctionSegment | None = None):
        super().__init__(entries, parent)
        self.item_name: str = item_name
        self.iterable_expression: str = iterable_expression

    def build(self, function: Function, context: dict) -> str:
        string = ""
        iterable = evaluate(self.iterable_expression, context)
        for item in iterable:
            context[self.item_name] = item
            string += super().build(function, context)
        return string


class FunctionSegmentType:
    def __init__(self, name: str, read: Callable[[str], FunctionSegment]):
        self.name: str = name
        self.read: Callable[[str], FunctionSegment] = read


class Function(StringResourceBuilder):
    DATAPACK_FUNCTIONS_REGISTRY = "function"

    EXPRESSION_BOUNDARY_CHARACTERS = "%"
    COMMENT_PREFIX = "//"
    SEGMENT_PREFIX = "#"
    SEGMENT_END = "end"

    SEGMENT_TYPES: list[FunctionSegmentType] = [
        # EXAMPLE: #repeat foreach number in [1, 2, 3]
        FunctionSegmentType(
            name="repeat",
            read=lambda line: ForeachRepeaterContainerFunctionSegment(
                item_name=line.split(" ", maxsplit=4)[2],
                iterable_expression=line.split(" ", maxsplit=4)[4],
                entries=list()
            )
        )
    ]

    @classmethod
    def function(cls, identifier: IdentifierLike, code: str) -> Function:
        lines = code.split("\n")

        head_segment = ContainerFunctionSegment(list())
        segment = head_segment
        for line_index in range(lines.__len__()):
            line = lines[line_index]

            # Comment
            if line.startswith(Function.COMMENT_PREFIX):
                continue

            # Segment
            if line.startswith(Function.SEGMENT_PREFIX):
                segment_type_name = line.split(" ")[0].removeprefix(Function.SEGMENT_PREFIX)
                if segment_type_name == Function.SEGMENT_END:
                    segment = segment.parent
                    continue
                for segment_type in cls.SEGMENT_TYPES:
                    if segment_type_name == segment_type.name:
                        segment.entries.append(segment_type.read(line))
                        segment.entries[-1].parent = segment
                        segment = segment.entries[-1]
                        break
                continue

            # Code
            segment.entries.append(LineFunctionSegment(
                code=line,
                parent=segment
            ))

        return Function(
            identifier=identifier,
            head_segment=head_segment
        )

    def __init__(self, identifier: IdentifierLike, head_segment: FunctionSegment):
        super().__init__(Function.DATAPACK_FUNCTIONS_REGISTRY, identifier)
        self.head_segment: FunctionSegment = head_segment

    def build(self, context: dict) -> list[StringResource]:
        resources: list[StringResource] = list()
        resources.append(StringResource(
            registry=Function.DATAPACK_FUNCTIONS_REGISTRY,
            identifier=self.identifier,
            data=self.head_segment.build(self, context)
        ))
        return resources


class FunctionResourceBuilderLoader(ResourceBuilderLoader):
    def load(self, directory: str, file: str, registry: str, identifier: Identifier) -> Function:
        return Function.function(identifier, read_text_file(file))

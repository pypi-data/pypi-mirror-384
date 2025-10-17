from __future__ import annotations
from mcdplib.core.evaluation import evaluate, evaluate_substrings
from mcdplib.datapack.function import Function
from mcdplib.core.resource.resource_string import StringResource, StringResourceBuilder
from mcdplib.core.resource.resource import ResourceBuilderLoader
from mcdplib.core.file import read_text_file
from mcdplib.core.identifier import Identifier, IdentifierLike


class FunctionTemplateSkipCondition:
    def __init__(self, expression: str):
        self.expression = expression

    def skip(self, context: dict) -> bool:
        return evaluate(self.expression, context)


class FunctionTemplateRepeater:
    def __init__(self, child: FunctionTemplateRepeater | None = None):
        self.child: FunctionTemplateRepeater | None = child

    def build_function(self, template: FunctionTemplate, context: dict) -> Function:
        return Function.function(
            identifier=evaluate_substrings(template.function_identifier_template, context, expression_boundary_characters=FunctionTemplate.EXPRESSION_BOUNDARY_CHARACTERS),
            code=evaluate_substrings(template.function_code_template, context, expression_boundary_characters=FunctionTemplate.EXPRESSION_BOUNDARY_CHARACTERS)
        )

    def repeat(self, template: FunctionTemplate, context: dict) -> list[Function]:
        pass


class OneTimeFunctionTemplateRepeater(FunctionTemplateRepeater):
    def __init__(self, child: FunctionTemplateRepeater | None = None):
        super().__init__(child)

    def repeat(self, template: FunctionTemplate, context: dict) -> list[Function]:
        if self.child is None:
            return [self.build_function(template, context)]
        return self.child.repeat(template, context)


class ForeachFunctionTemplateRepeater(FunctionTemplateRepeater):
    def __init__(self, item_name: str, iterable_expression: str, child: FunctionTemplateRepeater | None = None):
        super().__init__(child)
        self.item_name: str = item_name
        self.iterable_expression: str = iterable_expression

    def repeat(self, template: FunctionTemplate, context: dict) -> list[Function]:
        function_variants = list()
        iterable = evaluate(self.iterable_expression, context)
        if self.child is None:
            for item in iterable:
                context[self.item_name] = item
                skip = False
                for skip_condition in template.skip_conditions:
                    skip = skip or skip_condition.skip(context)
                if skip:
                    continue
                function_variants.append(self.build_function(template, context))
        else:
            for item in iterable:
                context[self.item_name] = item
                function_variants.extend(self.child.repeat(template, context))
        return function_variants


class FunctionTemplate(StringResourceBuilder):
    DATAPACK_FUNCTION_TEMPLATES_REGISTRY = "function_template"

    EXPRESSION_BOUNDARY_CHARACTERS = "%%"
    FUNCTION_IDENTIFIER_PREFIX = "TEMPLATE FUNCTION IDENTIFIER "
    SKIP_CONDITION_PREFIX = "TEMPLATE SKIP IF "
    FOREACH_REPEATER_PREFIX = "TEMPLATE REPEAT "

    @classmethod
    def function_template(cls, identifier: IdentifierLike, code: str):
        lines = code.split("\n")

        function_identifier_template = ""
        function_code_template = ""
        skip_conditions = list()
        head_repeater = OneTimeFunctionTemplateRepeater()
        repeater = head_repeater
        for line_index in range(lines.__len__()):
            line = lines[line_index]

            # Function identifier
            # EXAMPLE: TEMPLATE FUNCTION IDENTIFIER namespace:function_%%number%%
            if line.startswith(FunctionTemplate.FUNCTION_IDENTIFIER_PREFIX):
                function_identifier_template = line.removeprefix(FunctionTemplate.FUNCTION_IDENTIFIER_PREFIX).split(" ")[0]
                continue

            # Skip condition
            # EXAMPLE: TEMPLATE SKIP IF number % 2 == 0
            if line.startswith(FunctionTemplate.SKIP_CONDITION_PREFIX):
                expression = line.removeprefix(FunctionTemplate.SKIP_CONDITION_PREFIX)
                skip_conditions.append(FunctionTemplateSkipCondition(
                    expression=expression
                ))
                continue

            # Foreach repeater
            # EXAMPLE: TEMPLATE REPEAT FOREACH number IN [1, 2, 3]
            if line.startswith(FunctionTemplate.FOREACH_REPEATER_PREFIX):
                _, repeater_item_name, _, repeater_iterable_expression = line.removeprefix(FunctionTemplate.FOREACH_REPEATER_PREFIX).split(" ", maxsplit=3)
                repeater.child = ForeachFunctionTemplateRepeater(
                    item_name=repeater_item_name,
                    iterable_expression=repeater_iterable_expression
                )
                repeater = repeater.child
                continue

            # Code
            function_code_template += line + "\n"

        return FunctionTemplate(
            identifier=identifier,
            function_identifier_template=function_identifier_template,
            function_code_template=function_code_template,
            skip_conditions=skip_conditions,
            head_repeater=head_repeater
        )

    def __init__(self, identifier: IdentifierLike, function_identifier_template: str, function_code_template: str, skip_conditions: list[FunctionTemplateSkipCondition], head_repeater: FunctionTemplateRepeater):
        super().__init__(FunctionTemplate.DATAPACK_FUNCTION_TEMPLATES_REGISTRY, identifier)
        self.function_identifier_template: str = function_identifier_template
        self.function_code_template: str = function_code_template
        self.skip_conditions: list[FunctionTemplateSkipCondition] = skip_conditions
        self.head_repeater: FunctionTemplateRepeater = head_repeater

    def build(self, context: dict) -> list[StringResource]:
        resources: list[StringResource] = list()
        function_variants = self.head_repeater.repeat(self, context)
        for function_variant in function_variants:
            resources.extend(function_variant.build(context))
        return resources


class FunctionTemplateResourceBuilderLoader(ResourceBuilderLoader):
    def load(self, directory: str, file: str, registry: str, identifier: Identifier) -> FunctionTemplate:
        return FunctionTemplate.function_template(identifier, read_text_file(file))

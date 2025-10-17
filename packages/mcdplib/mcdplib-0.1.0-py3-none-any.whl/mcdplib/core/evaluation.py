from mcdplib.core.string import substring


def evaluate(expression: str, context: dict) -> any:
    return eval(expression, dict(), context)


def evaluate_substrings(string: str, context: dict, expression_boundary_characters: str) -> str:
    formatted_string = ""
    expression = ""
    reading_expression = False
    character_index = 0
    while character_index < string.__len__():
        if substring(string, character_index, expression_boundary_characters.__len__()) == expression_boundary_characters:
            if reading_expression:
                formatted_string += evaluate(expression, context).__str__()
                expression = ""
            reading_expression = not reading_expression
            character_index += expression_boundary_characters.__len__() - 1
        else:
            if reading_expression:
                expression += string[character_index]
            else:
                formatted_string += string[character_index]
        character_index += 1
    return formatted_string


def execute(code: str, context: dict, output_value_name: str | None = None) -> any:
    exec(code, dict(), context)
    if output_value_name is not None:
        return context[output_value_name]
    return None

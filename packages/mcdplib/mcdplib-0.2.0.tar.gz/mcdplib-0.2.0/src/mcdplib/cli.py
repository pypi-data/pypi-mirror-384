from mcdplib.datapack.datapack import Datapack
import argparse


# EXAMPLE: python main.py write -w build/datapack
def cli(datapack: Datapack) -> None:
    argument_parser: argparse.ArgumentParser = argparse.ArgumentParser(
        prog="mcdplib"
    )
    argument_parser.add_argument("action")
    argument_parser.add_argument("-w", "--writedirectory")

    arguments = argument_parser.parse_args()

    if arguments.action == "write":
        if "writedirectory" not in arguments:
            raise ValueError("Argument --writedirectory (-w) is required for write action")
        datapack.write(arguments.writedirectory)
    else:
        raise ValueError(f"Action {arguments['action']} does not exist")

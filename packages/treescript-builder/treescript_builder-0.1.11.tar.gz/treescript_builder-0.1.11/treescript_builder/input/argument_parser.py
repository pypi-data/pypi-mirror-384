""" Defines and Validates Argument Syntax.
 - Encapsulates Argument Parser.
 - Returns Argument Data, the args provided by the User.
 Author: DK96-OS 2024 - 2025
"""
from argparse import ArgumentParser
from sys import exit

from treescript_builder.input.argument_data import ArgumentData
from treescript_builder.input.string_validation import validate_name


def parse_arguments(
    args: list[str],
) -> ArgumentData:
    """ Parse command line arguments.

**Parameters:**
 - args(list): A list of argument strings.

**Returns:**
 ArgumentData - Container for Valid Argument Data.
    """
    if args is None or len(args) == 0:
        exit("No Arguments given.")
    try: # Initialize the Parser and Parse Immediately
        parsed_args = _define_arguments().parse_args(args)
    except SystemExit:
        exit("Unable to Parse Arguments.")
    return _validate_arguments(
        parsed_args.tree_file_name,
        parsed_args.data_dir,
        parsed_args.reverse
    )


def _validate_arguments(
    tree_file_name: str,
    data_dir_name: str,
    is_reverse: bool
) -> ArgumentData:
    """ Checks the values received from the ArgParser.
 - Uses Validate Name method from StringValidation.
 - Ensures that Reverse Operations have a Data Directory.
    
**Parameters:**
 - tree_file_name (str): The file name of the tree input.
 - data_dir_name (str): The Data Directory name.
 - is_reverse (bool): Whether the builder operation is reversed.

**Returns:**
 ArgumentData - A DataClass of syntactically correct arguments.
    """
    # Validate Tree Name Syntax
    if not validate_name(tree_file_name):
        exit("The Tree File argument was invalid.")
    # Validate Data Directory Name Syntax if Present
    if data_dir_name is not None and not validate_name(data_dir_name):
        exit("The Data Directory argument was invalid.")
    return ArgumentData(
        tree_file_name,
        data_dir_name,
        is_reverse
    )


def _define_arguments() -> ArgumentParser:
    """ Initializes and Defines Argument Parser.
 - Sets Required/Optional Arguments and Flags.

**Returns:**
 argparse.ArgumentParser - An instance with all supported FTB Arguments.
    """
    parser = ArgumentParser(
        description="""TreeScript-Builder: The File Tree Builder and Trimmer."""
    )
    # Required argument
    parser.add_argument(
        'tree_file_name',
        type=str,
        help='The File containing the Tree Node Structure'
    )
    # Optional arguments
    parser.add_argument(
        '--data_dir',
        default=None,
        help='The Data Directory'
    )
    parser.add_argument(
        '-r',
        '--reverse',
        '--trim',
        action='store_true',
        default=False,
        help='Flag to reverse the File Tree Operation'
    )
    return parser

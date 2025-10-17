"""The Tree Module.
"""
from treescript_builder.input.input_data import InputData
from treescript_builder.input.line_reader import read_input_tree


def build_tree(input_data: InputData) -> tuple[bool, ...]:
    """ Build The Tree as defined by the InputData.

**Parameters:**
 - input_data (str): The InputData produced by the Input Module.

**Returns:**
 tuple[bool, ...] - The results of each individual Builder operation.

**Raises:**
 SystemExit - If a Tree Validation error occurs.
	"""
    if input_data.is_reversed:
        from treescript_builder.tree.trim_validation import validate_trim
        instructions = validate_trim(
            read_input_tree(input_data.tree_input),
            input_data.data_dir
        )
        from treescript_builder.tree.tree_trimmer import trim
        results = trim(instructions)
    else:
        from treescript_builder.tree.build_validation import validate_build
        instructions = validate_build(
            read_input_tree(input_data.tree_input),
            input_data.data_dir
        )
        from treescript_builder.tree.tree_builder import build
        results = build(instructions)
    #
    return results


def process_results(results: tuple[bool, ...]) -> str:
    """ Process and Summarize the Results.

**Parameters:**
 - results (tuple[bool]): A tuple containing the results of the operations.

**Returns:**
 str - A summary of the number of operations that succeeded.
    """
    if (length := len(results)) == 0:
        return 'No operations ran.'
    if (success := sum(iter(results))) == 0:
        return f"All {length} operations failed."
    elif success == length:
        return f"All {length} operations succeeded."
    # Compute the Fraction of success operations
    success_percent = round(100 * success / length, 1)
    return f"{success} out of {length} operations succeeded: {success_percent}%"
import os
import textwrap


def pretty_usage(prog, description, parameters, epilog):
    """Formats and prints a usage message for a command-line script.

    This function takes the name of the program (prog), a description,
    a list of parameters with their descriptions, and an epilog to
    print to the terminal. It formats the message according to the
    terminal size and prints it.

    Parameters:
    - prog (str): The name of the program.
    - description (str): A brief description of what the program does.
    - parameters (list): A list of tuples, where each tuple contains a
      parameter name and its description.
    - epilog (str): A string containing additional information to be
      printed after the parameters.

    Returns:
    - None

    This is loosely based on how argparse thinks about usage().
    """
    # Get terminal size
    try:
        columns, rows = os.get_terminal_size()
    except OSError:  # e.g. when running inside of `watch` or similar
        columns, rows = 80, 24  # default terminal size

    # Header
    print(prog)
    print('-' * len(prog))
    print(textwrap.fill(description, width=columns-4))
    print()

    # Parameters
    param_width = min(20, (columns - 4) // 2)
    desc_width = columns - 4 - param_width
    print("Parameters:")
    for param, desc in parameters:
        wrapped_desc = textwrap.fill(desc, desc_width)
        desc_rows = wrapped_desc.split('\n')
        param_rows = [param] + [''] * (len(desc_rows) - 1)
        for param_row, desc_row in zip(param_rows, desc_rows):
            print(param_row.rjust(param_width), desc_row)

    # Epilog
    wrapped_epilog = textwrap.fill(epilog, width=columns-4)
    print()
    print(wrapped_epilog)


if __name__ == "__main__":
    # Sample data for testing
    prog = "MyScript"
    description = "This is a script that does amazing things. It's really cool and you should definitely use it."
    parameters = [
        ("-f, --file", "Specifies the input file. You can specify this multiple times to include multiple files."),
        ("-d, --directory", "Specifies the directory to operate on. This is optional and defaults to the current directory."),
        ("-o, --output", "Specifies the output file. If not specified, the results will be printed to the console.")
    ]
    epilog = "For more information, visit our website at 127.0.0.1. Happy scripting!"

    # Call the function with the sample data
    pretty_usage(prog, description, parameters, epilog)

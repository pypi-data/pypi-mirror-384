import black


def format_python_code(code_str):
    """
    Format the python code using black.
    Args:
        code_str (str): The python code to format.
    Returns:
        str: The formatted python code.
    """
    return black.format_str(code_str, mode=black.FileMode())

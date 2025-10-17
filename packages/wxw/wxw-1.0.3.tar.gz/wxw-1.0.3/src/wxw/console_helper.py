def highlight_text(text, color="red"):
    if color == "red":
        return f"\033[31m{text}\033[0m"
    elif color == "green":
        return f"\033[32m{text}\033[0m"
    elif color == "blue":
        return f"\033[34m{text}\033[0m"
    elif color == "yellow":
        return f"\033[33m{text}\033[0m"
    elif color == "purple":
        return f"\033[35m{text}\033[0m"
    else:
        return text  # Default behavior if color is not recognized


def print_red(text):
    """Print text in red color."""
    print(f"\033[31m{text}\033[0m")


def print_green(text):
    """Print text in green color."""
    print(f"\033[32m{text}\033[0m")


def print_yellow(text):
    """Print text in yellow color."""
    print(f"\033[33m{text}\033[0m")


def print_blue(text):
    """Print text in blue color."""
    print(f"\033[34m{text}\033[0m")


def print_format(string: str, a: float, func: str, b: float) -> float:
    """
    Format and print a mathematical operation, then return the result.

    Args:
        string (str):The description of the operation.
        a (float):The first operand.
        func (str):The operator as a string (e.g., '+', '-', '*', '/').
        b (float):The second operand.

    Returns:
        float:The result of the operation.
    """
    formatted_string = f"{a:<5.3f} {func} {b:<5.3f}"
    if func == "/":
        b += 1e-4  # Avoid division by zero
    c = eval(f"{a} {func} {b}")
    print(f"{string:<10}:{formatted_string} = {c:.3f}")
    return c

"""mugeshcalcu.calculator
Simple calculator library for addition and multiplication.
"""

def add(*args):
    """Return the sum of all given numbers."""
    if len(args) < 2:
        raise ValueError("At least two numbers required for addition.")
    total = 0
    for num in args:
        if not isinstance(num, (int, float)):
            raise TypeError(f"Invalid type {type(num)}, only int or float allowed.")
        total += num
    return total


def multiply(*args):
    """Return the product of all given numbers."""
    if len(args) < 2:
        raise ValueError("At least two numbers required for multiplication.")
    product = 1
    for num in args:
        if not isinstance(num, (int, float)):
            raise TypeError(f"Invalid type {type(num)}, only int or float allowed.")
        product *= num
    return product

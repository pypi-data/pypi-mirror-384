import math


def nested_list_comparator(l1: list, l2: list) -> bool:
    """Are a and b equal in anything but order?

    Args:
        a (list): A list of lists
        b (list): A list of lists

    Returns:
        bool: whether the lists are equal
    """
    return sorted([sorted(a) for a in l1]) == sorted([sorted(b) for b in l2])


def float_comparator(x: float, y: float) -> bool:
    """Checks equality of x and y of type float.

    This is needed due to floating-point precision errors.

    Args:
        x (float): A float number
        y (float): A float number

    Returns:
        bool: whether the float numbers are equal

    """
    return math.isclose(x, y)

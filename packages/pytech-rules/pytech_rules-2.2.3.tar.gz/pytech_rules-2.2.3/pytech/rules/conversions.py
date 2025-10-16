import ctypes
import math
import statistics
from typing import Any


def _multiply_by(_n: int | float):
    """
    Returns a callable that multiplies the param for a given value

    :param _n: the multiplier to use
    :return: the callable that multiplies for the given value
    """
    return _n.__mul__


def _rotate_angle_by(_n: int | float):
    """
    Returns a callable that rotates the param of a given value
    It then normalize the value between 0° and 360°

    :param _n: the angle to use for the rotation
    :return: the callable that rotates the angle of the given value
    """
    return lambda n: (n + _n) % 360


multiply_10 = _multiply_by(10)
multiply_100 = _multiply_by(100)
divide_10 = _multiply_by(0.1)
divide_100 = _multiply_by(0.01)
divide_1000 = _multiply_by(0.001)
divide_1_million = _multiply_by(0.000001)
divide_square_root_of_3 = _multiply_by(math.sqrt(3))

convert_bar_to_psi = _multiply_by(14.5038)
convert_decibar_to_psi = _multiply_by(1.45038)
convert_hours_to_seconds = _multiply_by(3600)
convert_single_phase_to_three_phase = divide_square_root_of_3

rotate_angle_of_180 = _rotate_angle_by(180)


def last(list_of_elements: tuple | list) -> Any:
    """
    Returns the last element of a list

    :param list_of_elements: a list of elements
    :return: the last element of the list
    """
    return list_of_elements[-1]


def make_false(*_) -> bool:
    """
    A function that always returns False.

    :param _: any number of values
    :return: False
    """
    return False


def no_conversion(n: Any) -> Any:
    """
    A function that returns the param as is.
    :param n: the value to return
    :return: the given param
    """
    return n


def safe_stdev(list_of_elements: tuple | list) -> Any:
    """
    Standard deviation that returns 0 if only one value is provided else stddev value
    :param list_of_elements: a list of elements
    """
    if len(list_of_elements) == 1:
        return 0.0
    return statistics.stdev(list_of_elements)


def to_signed_16bit_int(n: int) -> int:
    """
    Parse the retrieved number as a 16bit signed integer
    :param n: the read number
    :return: the signed value
    """
    return ctypes.c_int16(n).value

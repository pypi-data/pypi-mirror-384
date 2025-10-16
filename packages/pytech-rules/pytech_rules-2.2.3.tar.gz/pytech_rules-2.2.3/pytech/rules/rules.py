from dataclasses import dataclass
from typing import Any, Callable

from pytech.rules.conversions import no_conversion

__all__ = [
    "apply_rules",
    "Rule",
    "validate_rules",
]


@dataclass(frozen=True)
class Rule:
    """
    Rule type dataclass

    fields -> the list of fields to use for the conversion
    convert -> a callable to use to compute the value
    """

    fields: list
    convert: Callable = no_conversion


def validate_rules(rules: dict[Any, Rule]) -> None:
    """
    Check if given rules are valid.
    If the check fails it raises an error, otherwise no action is performed.

    :param rules: a dict of Rules
    :raises: TypeError, ValueError
    """

    if not isinstance(rules, dict):
        raise TypeError("Rules must be a dict.")

    if not all(isinstance(el, Rule) for el in rules.values()):
        raise TypeError("Every rule value must be a Rule.")

    if not all(isinstance(el.fields, list | tuple) for el in rules.values()):
        raise TypeError("Every rule fields value must be a list (or tuple).")

    if not all(len(el.fields) for el in rules.values()):
        raise ValueError("Rule fields must be a non empty list.")

    if not all(callable(el.convert) for el in rules.values()):
        raise ValueError("Rule convert must be a callable.")


def apply_rules(rules: dict[Any, Rule], data: dict[Any, Any]) -> dict:
    """
    Validates the provided rules.
    If the check passes the rules are applied to the data to create a new dict.

    :param rules: a dict of Rules
    :param data: the dict of data to convert
    :return: the dict data created applying the rules
    """
    validate_rules(rules)

    return {
        k: rule.convert(*(data[key] for key in rule.fields))
        for k, rule in rules.items()
    }

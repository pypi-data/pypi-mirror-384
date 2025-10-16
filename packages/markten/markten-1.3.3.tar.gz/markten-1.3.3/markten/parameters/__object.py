from collections.abc import Sequence
from typing import Any


def from_object(
    obj: object,
    param_names: Sequence[str],
) -> dict[str, Sequence[Any]]:
    """Generate a mapping of parameters from an object.

    This is most useful when used with argparse namespaces.

    If a value is a base data type, it will automatically be converted to a
    single-element tuple. Note that although `str` is a `Sequence[str]`,
    strings will not be separated into characters.

    Parameters
    ----------
    obj : object
        Object to gather parameters from.
    param_names : Sequence[str]
        Names of parameters to gather.

    Returns
    -------
    dict[str, Sequence[Any]]
        Mapping of parameters.
    """
    params = {}

    for name in param_names:
        value = getattr(obj, name)
        if isinstance(value, Sequence) and not isinstance(value, str):
            params[name] = value
        else:
            params[name] = (value,)

    return params

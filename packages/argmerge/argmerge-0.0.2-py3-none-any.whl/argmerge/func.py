"""Module to work with retrieving arguments functions"""

import sys
from inspect import Parameter, signature
from typing import Any, Callable

from loguru import logger as LOGGER

from argmerge.base import SourceParser

__all__ = ["parse_func", "parse_func_runtime"]


class FuncDefaultParser(SourceParser):
    """Builds the parser to extract default arguments from a function signature

    This is the lowest-ranked parser.

    params:
        label (str): The debugging label to indicate an argument was set at the CLI.
        rank (int): The priority of the parser. Generally, we aim between [0,100] for
            human-readabilty.

    """

    label: str = "Python Function Default"
    rank: int = 0

    def __call__(
        cls,
        threshold_kwargs: dict,
        change_ledger: dict,
        f: Callable,
        debug: bool = False,
    ) -> tuple[dict, dict]:
        """Lowest level parser - retrieve function defaults as fallback arguments.

        Args:
            threshold_kwargs (dict[str, Any]): kwargs passed around the
                @threshold decorator.
            change_ledger (dict[str, dict[str, str  |  int]]): Tracks when kwargs are
                updated inside the @threshold decorator.
            f (Callable): The function we wrap.
            debug (bool, optional): Flag to turn on more logging. Defaults to False.


        Returns:
            tuple[dict, dict]: an updated `threshold_kwargs` and `change_ledger`.
        """

        if debug:
            LOGGER.remove()
            LOGGER.add(sys.stderr, level="DEBUG")

        _sig = signature(f)
        LOGGER.debug(f"Function {signature=}")
        _default: dict = {}

        for k, v in _sig.parameters.items():
            if v.default is not Parameter.empty:
                _default[k] = v.default

        LOGGER.debug(f"{_default=}")
        for k in _default:
            change_ledger[k] = {"label": cls.label, "rank": cls.rank}

        threshold_kwargs.update(**_default)

        return threshold_kwargs, change_ledger


parse_func = FuncDefaultParser()


class FuncUpdater(SourceParser):
    """Builds the parser to extract default arguments from a function signature

    This is the highest-ranked parser.

    params:
        label (str): The debugging label to indicate an argument was set at Runtime by
            the developer.
        rank (int): The priority of the parser. Generally, we aim between [0,100] for
            human-readabilty.
    """

    label: str = "Developer-provided"
    rank: int = 100

    def __call__(
        cls,
        threshold_kwargs: dict[str, Any],
        change_ledger: dict[str, dict[str, str | int]],
        func_kwargs: dict[str, Any],
        debug: bool = False,
    ) -> tuple[dict, dict]:
        """Update the external values with the function's runtime arguments.

        Args:
            threshold_kwargs (dict[str, Any]): kwargs passed around the
                @threshold decorator.
            change_ledger (dict[str, dict[str, str  |  int]]): Tracks when kwargs are
                updated inside the @threshold decorator.
            func_kwargs (dict[str, Any]): The Runtime kwargs of the function.
            debug (bool, optional): Flag to turn on more logging. Defaults to False.

        Returns:
            Returns:
            tuple[dict, dict]: an updated `threshold_kwargs` and `change_ledger`.
        """
        if debug:
            LOGGER.remove()
            LOGGER.add(sys.stderr, level="DEBUG")

        LOGGER.debug(f"{threshold_kwargs=}")
        LOGGER.debug(f"{func_kwargs=}")

        threshold_kwargs.update(**func_kwargs)

        for key in func_kwargs:
            change_ledger[key] = {"label": cls.label, "rank": cls.rank}

        return threshold_kwargs, change_ledger


parse_func_runtime = FuncUpdater()

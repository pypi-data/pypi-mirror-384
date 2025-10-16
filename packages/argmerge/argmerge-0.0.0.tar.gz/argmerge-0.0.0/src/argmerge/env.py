# cython: linetrace=True
# distutils: define_macros=CYTHON_TRACE=1
import os
import re
import sys
from typing import Any

from loguru import logger as LOGGER

from argmerge.base import SourceParser
from argmerge.utils import extract_literals

__all__ = ["ENV_PREFIX", "parse_env"]

ENV_PREFIX = os.environ.get("PYTHRESH", "THRESH")


class EnvParser(SourceParser):
    """The parser the extracts relevant environment variables.

    Args:
        label (str): The debugging label to indicate an argument was set by environment
            variables.
        rank (int): The priority of the parser. Generally, we aim between [0,100] for
            human-readabilty.
    """

    rank: int = 30
    label: str = "Environment Variable"

    def __call__(
        cls,
        threshold_kwargs: dict[str, Any],
        change_ledger: dict[str, dict[str, str | int]],
        env_prefix: str | re.Pattern[str] = ENV_PREFIX,
        debug=False,
        **kwargs,
    ):
        """Parse the environment variables using the `env_prefix` and update inputs.

        Args:
            threshold_kwargs (dict[str, Any]): kwargs passed around the
                @threshold decorator.
            change_ledger (dict[str, dict[str, str  |  int]]): Tracks when kwargs are
                updated inside the @threshold decorator.
            env_prefix (str | re.Pattern[str], optional): The prefix used to search for
                set environment variables. Defaults to ENV_PREFIX, which is 'THRESH_'.
            debug (bool, optional): Flag to turn on more logging. Defaults to False.

        Raises:
            ValueError: `env_prefix` must either be a string or Regex string pattern.

        Returns:
            tuple[dict, dict]: an updated `threshold_kwargs` and `change_ledger`.
        """
        if debug:
            LOGGER.remove()
            LOGGER.add(sys.stderr, level="DEBUG")

        if isinstance(env_prefix, re.Pattern):
            pattern = env_prefix

        elif isinstance(env_prefix, str):
            pattern = re.compile(rf"(?:{env_prefix.upper()}.)([A-Za-z0\-\_]+)")

        else:
            raise ValueError(
                f"'env_prefix' must be either a string or Regex string pattern. Received: {env_prefix} ({type(env_prefix)})."
            )

        LOGGER.debug(f"{env_prefix=}")
        LOGGER.debug(f"{pattern=}")

        _env_kwargs = {}

        for k, v in os.environ.items():
            _search = pattern.search(k)

            if _search is not None:
                try:
                    key = _search.group(1).lower()
                    LOGGER.debug(f"{key=} {v=}")
                    _env_kwargs[key] = extract_literals(v)

                except IndexError:
                    LOGGER.debug(f"Regex search failed on environment variable {k}.")

            else:
                LOGGER.debug(f"Miss: {k=}")

        LOGGER.debug(f"{_env_kwargs=}")
        threshold_kwargs.update(_env_kwargs)

        LOGGER.debug(f"Updated {threshold_kwargs=}")

        for key in _env_kwargs:
            change_ledger[key] = {"label": cls.label, "rank": cls.rank}

        return threshold_kwargs, change_ledger


# Make EnvParser appear as a function when it uses __call__.
parse_env = EnvParser()

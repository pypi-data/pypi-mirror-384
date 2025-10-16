"""Module that provides a flexible CLI parser component in the decorator.


```py
CLI_PATTERN: re.Pattern = re.compile(r"--([A-Za-z_-]+)=([0-9A-Za-z_-\.]+)")
```

- matches `'--arg=value'`
- does not match `'--arg value'`
"""

import re
import sys
from typing import Any

from loguru import logger as LOGGER

from argmerge.base import SourceParser

__all__ = ["CLI_PATTERN", "parse_cli"]

# matches '--arg=value'
# does not match '--arg value'
CLI_PATTERN: re.Pattern = re.compile(r"--([A-Za-z_-]+)=([0-9A-Za-z_-\.]+)")


class CLIParser(SourceParser):
    """The parser the extracts relevant CLI arguments.

    params:
        label (str): The debugging label to indicate an argument was set at the CLI.
        rank (int): The priority of the parser. Generally, we aim between [0,100] for
            human-readabilty.

    """

    label: str = "CLI"
    rank: int = 40

    def __call__(
        cls,
        threshold_kwargs: dict[str, Any],
        change_ledger: dict[str, dict[str, str | int]],
        cli_pattern: re.Pattern[str] = CLI_PATTERN,
        debug: bool = False,
        **kwargs,
    ) -> tuple[dict, dict]:
        """Parse the CLI commands using the cli_pattern regular expression.

        Args:
            threshold_kwargs (dict[str, Any]): kwargs passed around the
                @threshold decorator.
            change_ledger (dict[str, dict[str, str  |  int]]): Tracks when kwargs are
                updated inside the @threshold decorator.
            cli_pattern (re.Pattern[str], optional): The regular expression pattern
                used to extract arguments from the CLI. Defaults to CLI_PATTERN.
            debug (bool, optional): Flag to turn on more logging. Defaults to False.

        Returns:
            tuple[dict, dict]: an updated `threshold_kwargs` and `change_ledger`.
        """
        _cli_kwargs: dict
        _cli_input: str

        if debug:
            LOGGER.remove()
            LOGGER.add(sys.stderr, level="DEBUG")

        if isinstance(cli_pattern, re.Pattern):
            _cli_pattern = cli_pattern

        else:
            _cli_pattern = re.compile(rf"{cli_pattern}")

        LOGGER.debug(f"{cli_pattern=}")
        LOGGER.debug(f"{_cli_pattern=}")
        LOGGER.debug(f"{sys.argv=}")
        _cli_input = " ".join(sys.argv[1:])
        LOGGER.debug(f"{_cli_input}")

        _cli_kwargs = dict(_cli_pattern.findall(_cli_input))
        LOGGER.debug(f"{_cli_kwargs=}")

        threshold_kwargs.update(_cli_kwargs)
        LOGGER.debug(f"Updated {threshold_kwargs=}")

        for key in _cli_kwargs:
            change_ledger[key] = {"label": cls.label, "rank": cls.rank}

        return threshold_kwargs, change_ledger


parse_cli = CLIParser()

"""Module that contains the main decorator, `@threshold`.

Usage:
    ```py
    # main.py
    from argmerge import threshold

    @threshold
    def main(first: int, second: str, third: float = 3.0):
        ...

    if __name__ == '__main__':
        main()
    ```
    Many more examples of how to use this can be found in [the Examples section](/examples/)
"""

import functools
import re
from pathlib import Path

from argmerge.cli import CLI_PATTERN, parse_cli
from argmerge.env import ENV_PREFIX, parse_env
from argmerge.func import parse_func, parse_func_runtime
from argmerge.json import parse_json
from argmerge.trace import LOG_LEVELS, trace_arg_lineage
from argmerge.yaml import parse_yaml


def threshold(
    *args,
    fpath_json: str | Path = "",
    fpath_yaml: str | Path = "",
    env_prefix: str | re.Pattern[str] = ENV_PREFIX,  # 'THRESH', also set at PYTHRESH
    cli_pattern: str | re.Pattern[str] = CLI_PATTERN,
    trace_level: str = "",
    debug: bool = False,
    **kwargs,
):
    """Merge arguments from external environment sources into the program.

    We allow syntax of both @threshold and @threshold(), depending whether you want to
    allow for defaults or override them.

    Args:
        fpath_json (str | Path, optional): The path to find a JSON configuration file.
            Defaults to "".
        fpath_yaml (str | Path, optional): The path to find a YAML configuration file.
            Defaults to "".
        env_prefix (str | re.Pattern[str], optional): The string or Regex to match
            environment variables against. Defaults to ENV_PREFIX, which is 'THRESH'.
        cli_pattern (str | re.Pattern[str], optional): The string or Regex to match
            CLI arguments against. Defaults to CLI_PATTERN.
        trace_level (str, optional): Trace the source of each kwarg and display at the
            specified trace log level. Defaults to "", which skips the trace entirely.
        debug (bool, optional): Turns on debugging for all the parsers.
            Defaults to False.

    Raises:
        ValueError: `level` must be in one of the default loguru logger levels:
            `("critical", "warning", "success", "info", "debug")`

    Returns:
        callable: A wrapped, yet-to-be-called function with resolved arguments.
    """
    if len(args) == 1:
        # allow syntax of @threshold and @threshold()
        return threshold()(args[0])

    else:

        def wrapped(f):
            @functools.wraps(f)
            def wrapped_f(*_args, **_kwargs):
                _threshold_kwargs, _change_ledger = dict(), dict()
                _threshold_kwargs, _change_ledger = parse_func(
                    _threshold_kwargs, _change_ledger, f, debug=debug
                )

                _threshold_kwargs, _change_ledger = parse_json(
                    _threshold_kwargs,
                    _change_ledger,
                    fpath_json=fpath_json,
                    debug=debug,
                )

                _threshold_kwargs, _change_ledger = parse_yaml(
                    _threshold_kwargs,
                    _change_ledger,
                    fpath_yaml=fpath_yaml,
                    debug=debug,
                )

                _threshold_kwargs, _change_ledger = parse_env(
                    _threshold_kwargs,
                    _change_ledger,
                    env_prefix=env_prefix,
                    debug=debug,
                )

                _threshold_kwargs, _change_ledger = parse_cli(
                    _threshold_kwargs,
                    _change_ledger,
                    cli_pattern=cli_pattern,
                    debug=debug,
                )

                _threshold_kwargs, _change_ledger = parse_func_runtime(
                    _threshold_kwargs, _change_ledger, func_kwargs=_kwargs, debug=debug
                )

                if trace_level.lower() in LOG_LEVELS:
                    trace_arg_lineage(
                        f,
                        _change_ledger,
                        level=trace_level,
                    )

                elif trace_level == "":
                    # default behavior
                    pass

                else:
                    raise ValueError(
                        f"'trace_level' has been set to '{trace_level}', which is not "
                        "supported. Please set 'trace_level' to an empty string or one"
                        f" of: {LOG_LEVELS}."
                    )

                return f(*_args, **_threshold_kwargs)

            return wrapped_f

        return wrapped

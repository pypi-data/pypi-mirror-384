# cython: linetrace=True
# distutils: define_macros=CYTHON_TRACE=1

import sys
from pathlib import Path

import yaml
from loguru import logger as LOGGER

from argmerge.base import SourceParser

__all__ = ["parse_yaml"]


class YAMLParser(SourceParser):
    """The parser the extracts relevant arguments from a YAML file.

    params:
        label (str): The debugging label to indicate an argument was set in a YAML
            config file.
        rank (int): The priority of the parser. Generally, we aim between [0,100] for
            human-readabilty.

    """

    label: str = "YAML"
    rank: int = 20

    def __call__(
        cls,
        threshold_kwargs: dict[str, str],
        change_ledger: dict[str, dict[str, str | int]],
        fpath_yaml: str | Path,
        debug: bool = False,
    ) -> tuple[dict, dict]:
        """Parse a YAML configuration file for arguments

         Args:
            threshold_kwargs (dict[str, Any]): kwargs passed around the
                @threshold decorator.
            change_ledger (dict[str, dict[str, str  |  int]]): Tracks when kwargs are
                updated inside the @threshold decorator.
            fpath_yaml (str | Path): The filepath to the YAML configuration file.
            debug (bool, optional): Flag to turn on more logging. Defaults to False.

        Raises:
            ValueError: If filepath extension is not `yml` or `yaml`.

        Returns:
            tuple[dict, dict]: an updated `threshold_kwargs` and `change_ledger`.
        """
        _yaml_kwargs: dict

        if debug:
            LOGGER.remove()
            LOGGER.add(sys.stderr, level="DEBUG")

        LOGGER.debug(f"{threshold_kwargs=}")
        LOGGER.debug(f"{fpath_yaml=}")

        _fpath_yaml = Path(fpath_yaml)
        if _fpath_yaml == Path(""):
            LOGGER.debug("fpath_yaml not provided, skipping.")

        else:
            if _fpath_yaml.suffix not in (".yml", ".yaml"):
                raise ValueError(
                    f"The YAML suffix of '{_fpath_yaml.suffix}' is not correct."
                    " Please use '.yml' or '.yaml'."
                )

            cls.label = f"YAML ({_fpath_yaml})"

            with open(fpath_yaml, "rb") as fy:
                _yaml_kwargs = yaml.safe_load(fy)

            LOGGER.debug(f"{_yaml_kwargs=}")
            threshold_kwargs.update(_yaml_kwargs)
            LOGGER.debug(f"Updated {threshold_kwargs=}")

            for key in _yaml_kwargs:
                change_ledger[key] = {"label": cls.label, "rank": cls.rank}

        return threshold_kwargs, change_ledger


parse_yaml = YAMLParser()

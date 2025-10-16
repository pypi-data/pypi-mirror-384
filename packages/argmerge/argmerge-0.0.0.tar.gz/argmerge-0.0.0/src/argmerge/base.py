"""Module that holds the Abstract Base Class for all external parsers."""

from abc import ABC, abstractmethod

__all__ = ["SourceParser"]


class SourceParser(ABC):
    """The base parser from which all other parsers are built.

    To build a new parser, you will need to subclass this one. Set 'rank' and 'label'
    as class variables and overwrite `__call__` with your parser. You MUST include
    three parameters: `threshold_kwargs`, `ledger`, and `debug`. This will allow you
    to add your own with other keyword arguments. You can look at any of the existing
    subclasses for how this works. After you build your subclass, you will instantiate
    it, setting it equal to a variable, ideally beginning with `'parse_'`. This will
    allow you to treat it like a function by invoking the `__call__` method, which calls
    your parser.

    Args:
        rank (int): The priority of the parser. Generally, we aim between [0,100] for
            human-readabilty.
        label (str): The debugging label to indicate an argument was set at the
            <source level>.
    """

    rank: int = -100
    label: str = ""

    def __init__(cls):
        cls.label
        cls.rank

    @abstractmethod
    def __call__(
        cls, threshold_kwargs: dict, ledger: dict, debug: bool = False, **kwargs
    ) -> tuple[dict, dict]:
        """This is too abstract to be covered"""

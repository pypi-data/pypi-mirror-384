import pytest

from argmerge.base import SourceParser


def test_empty(monkeypatch):
    monkeypatch.setattr(SourceParser, "__abstractmethods__", set())
    SourceParser()
    # did this for coverage


def test_bad_class_declaration():
    with pytest.raises(TypeError):

        class Bad(SourceParser):
            label: str = "Bad"
            rank = int = -100

        Bad()

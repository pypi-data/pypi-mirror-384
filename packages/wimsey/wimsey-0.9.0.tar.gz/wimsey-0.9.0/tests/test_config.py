import json
from collections.abc import Callable
from typing import NoReturn

import narwhals.stable.v1 as nw
import pytest
import yaml

from wimsey import config
from wimsey.types import _MagicExpr


@pytest.fixture
def test_suite():
    return [
        {"test": "mean_should", "column": "a", "be_exactly": 34},
        {"test": "type_should", "column": "y", "be_one_of": ["int64", "float64"]},
    ]


def throw_import_error(*args, **kwargs) -> NoReturn:
    raise ImportError


def test_collect_tests_returns_list_of_tuples_with_expressions_and_callables(
    test_suite,
) -> None:
    actual = config._collect_tests(test_suite)
    for expr, callable in actual:
        assert isinstance(expr, (nw.Expr, _MagicExpr))
        assert isinstance(callable, Callable)


def test_collect_tests_returns_friendly_error_when_required_value_not_give(test_suite) -> None:
    test_suite[0].pop("column")
    with pytest.raises(TypeError, match="column"):
        config._collect_tests(test_suite)


def test_collect_tests_returns_friendly_error_when_no_test_is_given(test_suite) -> None:
    test_suite[1].pop("test")
    with pytest.raises(ValueError, match="test"):
        config._collect_tests(test_suite)


def test_collect_tests_returns_input_when_input_is_already_test_functions(test_suite) -> None:
    initial = config._collect_tests(test_suite)
    actual = config._collect_tests(initial)
    assert actual == initial


def test_read_config_parses_yaml(monkeypatch, test_suite) -> None:
    class DummyOpenFile:
        def __enter__(self, *args, **kwargs):
            return self

        def __exit__(self, *args, **kwargs): ...

        def read(self, *args, **kwargs):
            return yaml.dump(test_suite)

    def open_file_patch(*args, **kwargs):
        return DummyOpenFile()

    monkeypatch.setattr(config.fsspec, "open", open_file_patch)
    actual = config._read_config("file.yaml")
    for expr, callable in actual:
        assert isinstance(expr, (nw.Expr, _MagicExpr))
        assert isinstance(callable, Callable)


def test_read_config_parses_yaml_with_test_section(monkeypatch, test_suite) -> None:
    class DummyOpenFile:
        def __enter__(self, *args, **kwargs):
            return self

        def __exit__(self, *args, **kwargs): ...

        def read(self, *args, **kwargs):
            return yaml.dump({"cool": ["some", "cool", "stuff"], "tests": test_suite})

    def open_file_patch(*args, **kwargs):
        return DummyOpenFile()

    monkeypatch.setattr(config.fsspec, "open", open_file_patch)
    actual = config._read_config("file.yaml")
    for expr, callable in actual:
        assert isinstance(expr, (nw.Expr, _MagicExpr))
        assert isinstance(callable, Callable)


def test_read_config_parses_yaml_with_only_one_test(monkeypatch, test_suite) -> None:
    class DummyOpenFile:
        def __enter__(self, *args, **kwargs):
            return self

        def __exit__(self, *args, **kwargs): ...

        def read(self, *args, **kwargs):
            return yaml.dump(test_suite[0])

    def open_file_patch(*args, **kwargs):
        return DummyOpenFile()

    monkeypatch.setattr(config.fsspec, "open", open_file_patch)
    actual = config._read_config("file.yaml")
    for expr, callable in actual:
        assert isinstance(expr, (nw.Expr, _MagicExpr))
        assert isinstance(callable, Callable)


def test_read_config_parses_json(monkeypatch, test_suite) -> None:
    class DummyOpenFile:
        def __enter__(self, *args, **kwargs):
            return self

        def __exit__(self, *args, **kwargs): ...

        def read(self, *args, **kwargs):
            return json.dumps(test_suite)

    def open_file_patch(*args, **kwargs):
        return DummyOpenFile()

    monkeypatch.setattr(config.fsspec, "open", open_file_patch)
    actual = config._read_config("file.json")
    for expr, callable in actual:
        assert isinstance(expr, (nw.Expr, _MagicExpr))
        assert isinstance(callable, Callable)


def test_friendly_message_is_raised_when_yaml_is_unimportable(test_suite, monkeypatch) -> None:
    class DummyOpenFile:
        def __enter__(self, *args, **kwargs):
            return self

        def __exit__(self, *args, **kwargs): ...

        def read(self, *args, **kwargs):
            return json.dumps(test_suite)

    def open_file_patch(*args, **kwargs):
        return DummyOpenFile()

    monkeypatch.setattr(config.fsspec, "open", open_file_patch)
    monkeypatch.setattr(config, "_collect_tests", throw_import_error)
    with pytest.raises(ImportError, match="pip install pyyaml"):
        config._read_config("file.yaml")


def test_friendly_message_is_raised_when_yaml_does_not_return_contents(
    test_suite,
    monkeypatch,
) -> None:
    class DummyOpenFile:
        def __enter__(self, *args, **kwargs):
            return self

        def __exit__(self, *args, **kwargs): ...

        def read(self, *args, **kwargs) -> str:
            return "dsafasdfasdf"

    def open_file_patch(*args, **kwargs):
        return DummyOpenFile()

    monkeypatch.setattr(config.fsspec, "open", open_file_patch)
    with pytest.raises(ValueError, match="json/yaml"):
        config._read_config("file.yaml")

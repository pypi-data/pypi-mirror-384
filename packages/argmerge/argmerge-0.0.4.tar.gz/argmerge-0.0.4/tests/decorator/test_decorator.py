import pytest

from argmerge import threshold
from argmerge.cli import CLI_PATTERN
from argmerge.env import ENV_PREFIX
from tests.utils import no_error

EMPTY_TEST_CASES = [
    # Environment doesn't provide enough arguments
    (None, {}, pytest.raises(TypeError)),
]


@pytest.mark.parametrize("cli_args, env_mapping, context", EMPTY_TEST_CASES)
def test_threshold_empty(
    monkeypatch,
    cli_args,
    env_mapping,
    context,
):
    @threshold
    def show_hierarchy_empty(first: int, second: str, third: float = 0.0):
        return first, second, third

    if isinstance(cli_args, list) and all(isinstance(x, str) for x in cli_args):
        monkeypatch.setattr("sys.argv", cli_args)

    else:
        monkeypatch.setattr("sys.argv", ["None"])

    with monkeypatch.context() as m, context:
        for env_var_name, env_var_value in env_mapping.items():
            m.setenv(env_var_name, env_var_value)

        show_hierarchy_empty()


PARAMETRIZED_TEST_CASES = [
    # Default empty, recreated for parity
    ("", {}, "", "", ENV_PREFIX, CLI_PATTERN, "", False, pytest.raises(TypeError)),
    # Add tracing with correct log level - WARNING
    (
        "",
        {},
        "",
        "",
        ENV_PREFIX,
        CLI_PATTERN,
        "WARNING",
        False,
        pytest.raises(TypeError),
    ),
    # Add tracing with incorrect log level - TURING
    (
        "",
        {},
        "",
        "",
        ENV_PREFIX,
        CLI_PATTERN,
        "TURING",
        False,
        pytest.raises(ValueError),
    ),
    # Add fpath_json only
    (
        "",
        {},
        "tests/json/good_config.json",  # tests are run from base directory
        "",
        ENV_PREFIX,
        CLI_PATTERN,
        "",
        False,
        no_error,
    ),
    # Add fpath_yaml to previous - also debug = True
    (
        "",
        {},
        "tests/json/good_config.json",  # tests are run from base directory
        "tests/yaml/good_config.yaml",
        ENV_PREFIX,
        CLI_PATTERN,
        "SUCCESS",
        True,
        no_error,
    ),
    # Add Environment Variables to previous
    (
        "",
        {"THRESH_FIRST": "99"},
        "tests/json/good_config.json",  # tests are run from base directory
        "tests/yaml/good_config.yaml",
        ENV_PREFIX,
        CLI_PATTERN,
        "SUCCESS",
        True,
        no_error,
    ),
    # Add CLI to previous
    (
        "--second=Liskov",
        {"THRESH_FIRST": "99"},
        "tests/json/good_config.json",  # tests are run from base directory
        "tests/yaml/good_config.yaml",
        ENV_PREFIX,
        CLI_PATTERN,
        "SUCCESS",
        True,
        no_error,
    ),
]


@pytest.mark.parametrize(
    "cli_args,env_mapping,fpath_json,fpath_yaml,env_prefix,"
    "cli_pattern,trace_level,debug,context",
    PARAMETRIZED_TEST_CASES,
)
def test_threshold_parametrized(
    monkeypatch,
    cli_args,
    env_mapping,
    fpath_json,
    fpath_yaml,
    env_prefix,
    cli_pattern,
    trace_level,
    debug,
    context,
):
    @threshold(
        fpath_json=fpath_json,
        fpath_yaml=fpath_yaml,
        env_prefix=env_prefix,
        cli_pattern=cli_pattern,
        trace_level=trace_level,
        debug=debug,
    )
    def show_hierarchy(first: int, second: str, third: float = 0.0):
        return first, second, third

    if isinstance(cli_args, list) and all(isinstance(x, str) for x in cli_args):
        monkeypatch.setattr("sys.argv", cli_args)

    else:
        monkeypatch.setattr("sys.argv", ["None"])

    with monkeypatch.context() as m, context:
        for env_var_name, env_var_value in env_mapping.items():
            m.setenv(env_var_name, env_var_value)

        show_hierarchy()


OVERRIDE_TEST_CASES = [
    # Normally an error, the argument is overriden at runtime by the developer
    ("", {}, "", "", ENV_PREFIX, CLI_PATTERN, "", False, no_error),
    (
        "--second=Liskov",
        {"THRESH_FIRST": "99"},
        "tests/json/good_config.json",  # tests are run from base directory
        "tests/yaml/good_config.yaml",
        ENV_PREFIX,
        CLI_PATTERN,
        "SUCCESS",
        True,
        no_error,
    ),
]


@pytest.mark.parametrize(
    "cli_args,env_mapping,fpath_json,fpath_yaml,env_prefix,"
    "cli_pattern,trace_level,debug,context",
    OVERRIDE_TEST_CASES,
)
def test_override_threshold(
    monkeypatch,
    cli_args,
    env_mapping,
    fpath_json,
    fpath_yaml,
    env_prefix,
    cli_pattern,
    trace_level,
    debug,
    context,
):
    @threshold(
        fpath_json=fpath_json,
        fpath_yaml=fpath_yaml,
        env_prefix=env_prefix,
        cli_pattern=cli_pattern,
        trace_level=trace_level,
        debug=debug,
    )
    def show_hierarchy(first: int, second: str, third: float = 0.0):
        return first, second, third

    if isinstance(cli_args, list) and all(isinstance(x, str) for x in cli_args):
        monkeypatch.setattr("sys.argv", cli_args)

    else:
        monkeypatch.setattr("sys.argv", ["None"])

    with monkeypatch.context() as m, context:
        for env_var_name, env_var_value in env_mapping.items():
            m.setenv(env_var_name, env_var_value)

        show_hierarchy(first=1, second="two", third=3.0)

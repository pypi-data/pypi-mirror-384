import argparse
import ast
import os
import sys
from io import StringIO
from pathlib import Path
from unittest import mock

from boa_restrictor.cli.main import main
from boa_restrictor.common.rule import Rule
from boa_restrictor.projections.occurrence import Occurrence
from boa_restrictor.rules import BOA_RESTRICTOR_RULES, DJANGO_BOA_RULES, AsteriskRequiredRule


@mock.patch.object(argparse.ArgumentParser, "parse_args")
def test_main_arguments_parsed(mocked_parse_args):
    main(
        argv=(
            "boa-restrictor",
            os.path.abspath(sys.argv[0]),
            "--config",
            "pyproject.toml",
        )
    )

    mocked_parse_args.assert_called_once_with(
        ("boa-restrictor", os.path.abspath(sys.argv[0]), "--config", "pyproject.toml"),
    )


@mock.patch("boa_restrictor.cli.main.load_configuration", return_value={"exclude": ["PBR001"]})
@mock.patch("builtins.open", mock.mock_open(read_data="# test file"))
@mock.patch.object(Rule, "run_check")
@mock.patch.object(AsteriskRequiredRule, "run_check")
def test_main_exclude_config_active(mocked_run_checks_asterisk, mocked_rule_run_checks, *args):
    main(
        argv=(
            os.path.abspath(sys.argv[0]),
            "--config",
            "pyproject.toml",
        )
    )

    mocked_run_checks_asterisk.assert_not_called()
    assert mocked_rule_run_checks.call_count == len(BOA_RESTRICTOR_RULES) + len(DJANGO_BOA_RULES) - 1, (
        "We expect all but one rule to be called."
    )


@mock.patch("boa_restrictor.cli.main.load_configuration", return_value={"per-file-excludes": {"*.py": ["PBR001"]}})
@mock.patch("builtins.open", mock.mock_open(read_data="# test file"))
@mock.patch.object(Rule, "run_check")
@mock.patch.object(AsteriskRequiredRule, "run_check")
def test_main_per_file_exclude_config_active(mocked_run_checks_asterisk, mocked_rule_run_checks, *args):
    main(
        argv=(
            "test_file.py",
            "--config",
            "pyproject.toml",
        )
    )

    mocked_run_checks_asterisk.assert_not_called()
    assert mocked_rule_run_checks.call_count == len(BOA_RESTRICTOR_RULES) + len(DJANGO_BOA_RULES) - 1, (
        "We expect all but one rule to be called."
    )


@mock.patch("boa_restrictor.cli.main.load_configuration", return_value={})
@mock.patch("builtins.open", mock.mock_open(read_data="# test file"))
@mock.patch("boa_restrictor.cli.main.get_rules")
def test_main_django_rules_default_enabled(mocked_get_rule, *args):
    main(
        argv=(
            os.path.abspath(sys.argv[0]),
            "--config",
            "pyproject.toml",
        )
    )

    mocked_get_rule.assert_called_with(use_django_rules=True)


@mock.patch("boa_restrictor.cli.main.load_configuration", return_value={"enable_django_rules": True})
@mock.patch("builtins.open", mock.mock_open(read_data="# test file"))
@mock.patch("boa_restrictor.cli.main.get_rules")
def test_main_django_rules_enabled(mocked_get_rule, *args):
    main(
        argv=(
            os.path.abspath(sys.argv[0]),
            "--config",
            "pyproject.toml",
        )
    )

    mocked_get_rule.assert_called_with(use_django_rules=True)


@mock.patch("boa_restrictor.cli.main.load_configuration", return_value={"enable_django_rules": False})
@mock.patch("builtins.open", mock.mock_open(read_data="# test file"))
@mock.patch("boa_restrictor.cli.main.get_rules")
def test_main_django_rules_disabled(mocked_get_rule, *args):
    main(
        argv=(
            os.path.abspath(sys.argv[0]),
            "--config",
            "pyproject.toml",
        )
    )

    mocked_get_rule.assert_called_with(use_django_rules=False)


def test_main_noqa_comments_called():
    with mock.patch("boa_restrictor.cli.main.get_noqa_comments", return_value=[]) as mocked_get_noqa_comments:
        with mock.patch("boa_restrictor.cli.main.load_configuration", return_value={}):
            with mock.patch("builtins.open", mock.mock_open(read_data="# test file")):
                main(
                    argv=(
                        os.path.abspath(sys.argv[0]),
                        "--config",
                        "pyproject.toml",
                    )
                )

                mocked_get_noqa_comments.assert_called_once()


@mock.patch.object(ast, "parse", side_effect=SyntaxError)
@mock.patch("boa_restrictor.cli.main.load_configuration", return_value={})
@mock.patch("builtins.open", mock.mock_open(read_data="# test file"))
def test_main_invalid_syntax(*args):
    # With syntax error in parsing, the function should raise the SyntaxError
    # since exception handling was removed in the revert
    try:
        main(
            argv=(
                os.path.abspath(sys.argv[0]),
                "--config",
                "pyproject.toml",
            )
        )
        # If no exception was raised, this test should fail
        raise AssertionError
    except SyntaxError:
        # This is expected behavior after the revert
        pass


def test_main_occurrences_are_written_to_cli():
    occurrence = Occurrence(
        rule_id="PBR000",
        rule_label="One to rule them all.",
        filename="my_file.py",
        file_path=Path("/path/to/file/my_file.py"),
        line_number=42,
        identifier="my_function",
    )

    with mock.patch.object(sys.stdout, "write") as mocked_write:
        with mock.patch("boa_restrictor.cli.main.load_configuration", return_value={}):
            with mock.patch("builtins.open", mock.mock_open(read_data="# test file")):
                with mock.patch.object(
                    Rule,
                    "run_check",
                    return_value=[occurrence],
                ) as mocked_run_checks:
                    main(
                        argv=(
                            os.path.abspath(sys.argv[0]),
                            "--config",
                            "pyproject.toml",
                        )
                    )

                    # We have more than one rule
                    assert mocked_run_checks.call_count > 1

                    # We expect one line per occurrence
                    assert mocked_write.call_count == mocked_run_checks.call_count


@mock.patch("boa_restrictor.cli.main.load_configuration", return_value={})
@mock.patch("builtins.open", mock.mock_open(read_data="# test file"))
def test_main_occurrences_cli_output_correctly_formatted(mocked_load_config):
    occurrence = Occurrence(
        rule_id="PBR000",
        rule_label="One to rule them all.",
        filename="my_file.py",
        file_path=Path("/path/to/file/my_file.py"),
        line_number=42,
        identifier="my_function",
    )

    with mock.patch("sys.stdout", new=StringIO()) as mock_stdout:
        with mock.patch.object(Rule, "run_check", return_value=[occurrence]):
            main(
                argv=(
                    os.path.abspath(sys.argv[0]),
                    "--config",
                    "pyproject.toml",
                )
            )
    actual_output = mock_stdout.getvalue()

    # Make test OS-independent
    actual_output = actual_output.replace("\\", "/")

    # Check that the formatting is correct
    assert '/path/to/file/my_file.py:42": ' in actual_output
    assert "(PBR000) One to rule them all." in actual_output


@mock.patch("boa_restrictor.cli.main.load_configuration", return_value={"per-file-excludes": {"*.py": ["PBR001"]}})
@mock.patch("builtins.open", mock.mock_open(read_data="# test file"))
@mock.patch("boa_restrictor.cli.main.is_rule_excluded_per_file", return_value=True)
@mock.patch.object(AsteriskRequiredRule, "run_check")
def test_main_per_file_exclusion_skips_rule(mocked_run_check, mocked_is_excluded, *args):
    """Test that line 59 continue statement is executed when per-file exclusion matches"""
    main(
        argv=(
            os.path.abspath(sys.argv[0]),
            "--config",
            "pyproject.toml",
        )
    )

    # Verify the rule was excluded via per-file config
    mocked_is_excluded.assert_called()
    # Verify that the rule check was NOT called for the excluded rule
    mocked_run_check.assert_not_called()

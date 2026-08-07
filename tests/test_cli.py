"""CLI smoke tests."""

from click.testing import CliRunner

from jinx.cli import cli


def test_cli_help() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "marker" in result.output
    assert "translator" in result.output


def test_cli_subcommand_help() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["marker", "--help"])
    assert result.exit_code == 0
    assert "target-path" in result.output or "target_path" in result.output

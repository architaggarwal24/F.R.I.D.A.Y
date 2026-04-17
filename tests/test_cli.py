import os
import json
import pytest
from click.testing import CliRunner
from uuid import uuid4

import friday.tools.memory as memory_module
from friday.tools.memory import remember


@pytest.fixture(autouse=True)
def dashboard_test_setup():
    memory_module._collection_name_override = f"test_{uuid4().hex}"
    memory_module._chroma_client = None
    memory_module._embedding_model = None
    yield
    try:
        client = memory_module._get_client()
        client.delete_collection(memory_module._collection_name_override)
    except Exception:
        pass
    memory_module._collection_name_override = None
    memory_module._chroma_client = None
    memory_module._embedding_model = None


@pytest.fixture
def cli_runner():
    return CliRunner()


def test_cli_list_invokes_list_all(cli_runner):
    from friday.dashboard.cli import memory
    remember("I like blue", category="preference", source="voice")
    result = cli_runner.invoke(memory, ["list"])
    assert result.exit_code == 0
    assert "preference" in result.output.lower() or "UNCATEGORIZED" in result.output


def test_cli_search_invokes_search(cli_runner):
    from friday.dashboard.cli import memory
    remember("Boss uses dark mode", category="fact", source="voice")
    result = cli_runner.invoke(memory, ["search", "dark mode"])
    assert result.exit_code == 0


def test_cli_delete_invokes_delete(cli_runner):
    from friday.dashboard.cli import memory
    mem = remember("To be deleted", category="fact", source="voice")
    memory_id = mem["memory_id"]
    result = cli_runner.invoke(memory, ["delete", memory_id])
    assert result.exit_code == 0
    assert "deleted" in result.output.lower() or "not_found" in result.output.lower()


def test_cli_bulk_delete(cli_runner):
    from friday.dashboard.cli import memory
    remember("Reminder one", category="reminder", source="voice")
    remember("Reminder two", category="reminder", source="voice")
    result = cli_runner.invoke(memory, ["delete", "--category", "reminder"])
    assert result.exit_code == 0


def test_cli_export_creates_file(cli_runner):
    from friday.dashboard.cli import memory
    remember("A fact", category="fact", source="voice")
    with cli_runner.isolated_filesystem():
        result = cli_runner.invoke(memory, ["export"])
        assert result.exit_code == 0


def test_cli_stats_shows_counts(cli_runner):
    from friday.dashboard.cli import memory
    remember("A pref", category="preference", source="voice")
    result = cli_runner.invoke(memory, ["stats"])
    assert result.exit_code == 0
    assert "total" in result.output.lower()


def test_cli_serve_command_exists(cli_runner):
    from friday.dashboard.cli import memory
    result = cli_runner.invoke(memory, ["serve", "--help"])
    assert result.exit_code == 0
    assert "port" in result.output

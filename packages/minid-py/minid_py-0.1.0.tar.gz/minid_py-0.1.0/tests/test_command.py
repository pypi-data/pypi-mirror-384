from datetime import datetime, timezone
from unittest.mock import patch

from click.testing import CliRunner

from minid.command import find_entries, get_entry, main, new_entry, prefix
from minid.exceptions import NotFound


class TestRegisterPrefix:
    @patch("minid.command._db")
    def test_prefix_new(self, mock_db):
        runner = CliRunner()
        result = runner.invoke(prefix, ["NEWPREFIX"])

        assert result.exit_code == 0
        mock_db.register_prefix.assert_called_once_with("NEWPREFIX")
        assert "NEWPREFIX" in result.output

    @patch("minid.command._db")
    def test_prefix_list_empty(self, mock_db):
        mock_db.list_prefixes.return_value = []

        runner = CliRunner()
        result = runner.invoke(prefix, [])

        assert result.exit_code == 0
        assert "No prefixes registered" in result.output

    @patch("minid.command._db")
    def test_prefix_list_with_prefixes(self, mock_db):
        mock_db.list_prefixes.return_value = ["SLACK", "GHPR"]

        runner = CliRunner()
        result = runner.invoke(prefix, [])

        assert result.exit_code == 0
        assert "SLACK" in result.output
        assert "GHPR" in result.output


class TestNewEntry:
    @patch("minid.command.require_prefix")
    @patch("minid.command._db")
    def test_new_entry_with_content(self, mock_db, mock_require_prefix):
        mock_require_prefix.return_value = "SLACK"
        mock_db.store_entry.return_value = {"id": 100}

        runner = CliRunner()
        result = runner.invoke(new_entry, ["slack", "test content"])

        assert result.exit_code == 0
        mock_require_prefix.assert_called_once()
        mock_db.store_entry.assert_called_once_with("SLACK", "test content")
        assert "SLACK-100" in result.output

    @patch("minid.command.require_prefix")
    @patch("minid.command.read_multiline_input")
    @patch("minid.command._db")
    def test_new_entry_multiline(self, mock_db, mock_read_input, mock_require_prefix):
        mock_require_prefix.return_value = "SLACK"
        mock_read_input.return_value = "multiline content"
        mock_db.store_entry.return_value = {"id": 101}

        runner = CliRunner()
        result = runner.invoke(new_entry, ["slack"])

        assert result.exit_code == 0
        mock_read_input.assert_called_once()
        mock_db.store_entry.assert_called_once_with("SLACK", "multiline content")
        assert "SLACK-101" in result.output

    @patch("minid.command.require_prefix")
    @patch("minid.command.read_multiline_input")
    def test_new_entry_empty_content(self, mock_read_input, mock_require_prefix):
        mock_require_prefix.return_value = "SLACK"
        mock_read_input.return_value = "   "  # just whitespace

        runner = CliRunner()
        result = runner.invoke(new_entry, ["slack"])

        assert result.exit_code == 0
        assert "No content entered" in result.output


class TestFindEntries:
    entries = [
        {
            "prefix": "SLACK",
            "id": 100,
            "content": "test content",
            "timestamp": datetime(2025, 1, 1, tzinfo=timezone.utc),
        }
    ]

    @patch("minid.command.require_prefix")
    @patch("minid.command._db")
    def test_find_entries_with_prefix(self, mock_db, mock_require_prefix):
        mock_require_prefix.return_value = "SLACK"
        mock_db.search_entries.return_value = self.entries

        runner = CliRunner()
        result = runner.invoke(find_entries, ["test", "--prefix", "slack"])

        assert result.exit_code == 0
        mock_require_prefix.assert_called_once()
        mock_db.search_entries.assert_called_once_with("test", "SLACK")
        assert "test content" in result.output
        assert "SLACK-100" in result.output

    @patch("minid.command._db")
    def test_find_entries_no_query(self, mock_db):
        mock_db.search_entries.return_value = self.entries

        runner = CliRunner()
        result = runner.invoke(find_entries, [])

        assert result.exit_code == 0
        mock_db.search_entries.assert_called_once_with("", None)
        assert "test content" in result.output
        assert "SLACK-100" in result.output

    @patch("minid.command._db")
    def test_find_entries_no_results(self, mock_db):
        mock_db.search_entries.return_value = []

        runner = CliRunner()
        result = runner.invoke(find_entries, ["nonexistent"])

        assert result.exit_code == 0
        assert "No entries found" in result.output


class TestGetEntry:
    @patch("minid.command.require_prefix")
    @patch("minid.command._db")
    @patch("minid.command.process_links")
    def test_get_entry_success(self, mock_process_links, mock_db, mock_require_prefix):
        mock_require_prefix.return_value = "SLACK"
        mock_entry = {"content": "test content", "timestamp": datetime(2025, 1, 1, tzinfo=timezone.utc)}
        mock_db.get_entry.return_value = mock_entry
        mock_process_links.return_value = "processed content"

        runner = CliRunner()
        result = runner.invoke(get_entry, ["slack", "100"])

        assert result.exit_code == 0
        mock_require_prefix.assert_called_once()
        mock_db.get_entry.assert_called_once_with("SLACK", 100)
        mock_process_links.assert_called_once_with("test content")

    @patch("minid.command.require_prefix")
    @patch("minid.command._db")
    @patch("minid.command.print")
    def test_get_entry_not_found(self, mock_print, mock_db, mock_require_prefix):
        mock_require_prefix.return_value = "SLACK"
        mock_db.get_entry.side_effect = NotFound()

        runner = CliRunner()
        result = runner.invoke(get_entry, ["slack", "999"])

        assert result.exit_code == 1
        mock_print.assert_any_call("[red]Entry SLACK:999 not found[/red]")


class TestMain:
    def test_main_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "Usage: minid [OPTIONS] COMMAND [ARGS]" in result.output

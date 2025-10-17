from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from minid.utils import (
    FuzzyCommandGroup,
    _handle_github_links,
    _handle_urls,
    print_entries_table,
    process_links,
    read_multiline_input,
    require_prefix,
)


class TestLinkProcessing:
    def test_simple_url(self):
        text = "Check out https://github.com/user/repo"
        result = process_links(text)
        expected = "Check out [link=https://github.com/user/repo]https://github.com/user/repo[/link]"
        assert result == expected

    def test_long_url(self):
        text = "https://github.com/user/repo/commit/6d96270004515a0486bb7f76196a72b40c55a47f"
        result = process_links(text)
        expected = "[link=https://github.com/user/repo/commit/6d96270004515a0486bb7f76196a72b40c55a47f]https://github.com/user/repo/commit/6d96270004515a0486bb7f76196a72b40c55a47f[/link]"
        assert result == expected

    def test_github_issue_reference(self):
        text = "See user/repo#2222"
        result = process_links(text)
        expected = "See [link=https://github.com/user/repo/issues/2222]user/repo#2222[/link]"
        assert result == expected

    def test_multiple_urls(self):
        text = "Check https://example.com and https://github.com/user/repo"
        result = process_links(text)
        expected = "Check [link=https://example.com]https://example.com[/link] and [link=https://github.com/user/repo]https://github.com/user/repo[/link]"
        assert result == expected

    def test_url_with_query_params(self):
        text = "https://pypi.org/search/?q=minid-py&o=newest"
        result = process_links(text)
        expected = (
            "[link=https://pypi.org/search/?q=minid-py&o=newest]https://pypi.org/search/?q=minid-py&o=newest[/link]"
        )
        assert result == expected

    def test_no_urls(self):
        text = "Just some plain text with no links"
        result = process_links(text)
        assert result == text

    def test_existing_link_markup_not_double_processed(self):
        text = "Already linked: [link=https://example.com]example[/link]"
        result = process_links(text)
        # should not double-process existing links
        assert result == text

    def test_custom_link_markup_preserved(self):
        text = "Custom link: [link=https://example.com]LOL[/link]"
        result = process_links(text)
        # should not modify custom link text
        assert result == text

    def test_mixed_linked_and_unlinked_urls(self):
        text = "Already linked: [link=https://example.com]custom text[/link] and unlinked: https://github.com/user/repo"
        result = process_links(text)
        expected = "Already linked: [link=https://example.com]custom text[/link] and unlinked: [link=https://github.com/user/repo]https://github.com/user/repo[/link]"
        assert result == expected

    def test_mixed_content(self):
        text = "I've created user/repo#2222 and see https://example.com for more"
        result = process_links(text)
        expected = "I've created [link=https://github.com/user/repo/issues/2222]user/repo#2222[/link] and see [link=https://example.com]https://example.com[/link] for more"
        assert result == expected

    def test_github_with_underscores_and_dots(self):
        text = "Check out some_org/repo.name#456"
        result = process_links(text)
        expected = "Check out [link=https://github.com/some_org/repo.name/issues/456]some_org/repo.name#456[/link]"
        assert result == expected

    def test_url_at_end_of_sentence(self):
        text = "Visit https://example.com."
        result = process_links(text)
        # should not include the period
        expected = "Visit [link=https://example.com]https://example.com[/link]."
        assert result == expected

    def test_url_in_parentheses(self):
        text = "See documentation (https://docs.example.com) for details"
        result = process_links(text)
        expected = "See documentation ([link=https://docs.example.com]https://docs.example.com[/link]) for details"
        assert result == expected

    def test_actual_failing_case(self):
        text = "https://github.com/user/repo/commit/6d96270004515a0486bb7f76196a72b40c55a47f"
        result = process_links(text)
        print(f"Input: {text}")
        print(f"Output: {result}")
        expected = "[link=https://github.com/user/repo/commit/6d96270004515a0486bb7f76196a72b40c55a47f]https://github.com/user/repo/commit/6d96270004515a0486bb7f76196a72b40c55a47f[/link]"
        assert result == expected


class TestUrlHandling:
    def test_handle_urls_basic(self):
        text = "https://example.com"
        result = _handle_urls(text)
        expected = "[link=https://example.com]https://example.com[/link]"
        assert result == expected

    def test_handle_urls_with_path(self):
        text = "https://github.com/user/repo/issues/123"
        result = _handle_urls(text)
        expected = "[link=https://github.com/user/repo/issues/123]https://github.com/user/repo/issues/123[/link]"
        assert result == expected


class TestGithubHandling:
    def test_handle_github_basic(self):
        text = "owner/repo#123"
        result = _handle_github_links(text)
        expected = "[link=https://github.com/owner/repo/issues/123]owner/repo#123[/link]"
        assert result == expected

    def test_handle_github_in_sentence(self):
        text = "Fixed in user/repo#456 yesterday"
        result = _handle_github_links(text)
        expected = "Fixed in [link=https://github.com/user/repo/issues/456]user/repo#456[/link] yesterday"
        assert result == expected


class TestReadMultilineInput:
    @patch("builtins.input", side_effect=["line 1", "line 2", "", "", ""])
    @patch("minid.utils.print")
    def test_read_multiline_input_double_newline(self, mock_print, mock_input):
        result = read_multiline_input()
        assert result == "line 1\nline 2"
        mock_print.assert_called_once_with("Content (Ctrl+D or 2 blank lines to finish):")

    @patch("builtins.input", side_effect=["line 1", "line 2", EOFError()])
    @patch("minid.utils.print")
    def test_read_multiline_input_ctrl_d(self, mock_print, mock_input):
        result = read_multiline_input()
        assert result == "line 1\nline 2"

    @patch("builtins.input", side_effect=["", "", ""])
    @patch("minid.utils.print")
    def test_read_multiline_input_empty(self, mock_print, mock_input):
        result = read_multiline_input()
        assert result == ""


class TestRequirePrefix:
    def test_require_prefix_found(self):
        mock_db = MagicMock()
        mock_db.find_prefix_match.return_value = "SLACK"

        result = require_prefix(mock_db, "sl")
        assert result == "SLACK"
        mock_db.find_prefix_match.assert_called_once_with("sl")

    @patch("minid.utils.print")
    @patch("minid.utils.exit")
    def test_require_prefix_not_found_no_prefixes(self, mock_exit, mock_print):
        mock_db = MagicMock()
        mock_db.find_prefix_match.return_value = None
        mock_db.list_prefixes.return_value = []

        require_prefix(mock_db, "nonexistent")

        mock_print.assert_called_with("[red]Error: No registered prefix matches 'nonexistent'[/red]")
        mock_exit.assert_called_once_with(1)

    @patch("minid.utils.print")
    @patch("minid.utils.exit")
    def test_require_prefix_not_found_with_prefixes(self, mock_exit, mock_print):
        mock_db = MagicMock()
        mock_db.find_prefix_match.return_value = None
        mock_db.list_prefixes.return_value = ["SLACK", "GITHUB"]

        require_prefix(mock_db, "nonexistent")

        assert mock_print.call_count == 2
        mock_print.assert_any_call("[red]Error: No registered prefix matches 'nonexistent'[/red]")
        mock_print.assert_any_call("Registered prefixes: SLACK, GITHUB")
        mock_exit.assert_called_once_with(1)


class TestFuzzyCommandGroup:
    def test_get_command_exact_match(self):
        from click import Command

        group = FuzzyCommandGroup()
        cmd = Command("test")
        group.add_command(cmd)

        ctx = MagicMock()
        result = group.get_command(ctx, "test")
        assert result == cmd

    def test_get_command_fuzzy_match(self):
        from click import Command

        group = FuzzyCommandGroup()
        cmd = Command("test")
        group.add_command(cmd)

        ctx = MagicMock()
        result = group.get_command(ctx, "t")
        assert result == cmd

    def test_get_command_alias_match(self):
        from click import Command

        group = FuzzyCommandGroup()
        group.aliases = {"query": "find"}
        cmd = Command("find")
        group.add_command(cmd)

        ctx = MagicMock()
        result = group.get_command(ctx, "query")
        assert result == cmd

    def test_get_command_ambiguous(self):
        from click import Command

        group = FuzzyCommandGroup()
        group.add_command(Command("test1"))
        group.add_command(Command("test2"))

        ctx = MagicMock()
        group.get_command(ctx, "t")
        ctx.fail.assert_called_with("Ambiguous command: t. Could be: test1, test2")

    def test_get_command_no_match(self):
        from click import Command

        group = FuzzyCommandGroup()
        group.add_command(Command("test"))

        ctx = MagicMock()
        group.get_command(ctx, "x")
        ctx.fail.assert_called_with("No such command: x")


class TestPrintEntriesTable:
    @patch("minid.utils.print")
    def test_print_table_with_single_entry_short(self, mock_print):
        entries = [
            {
                "prefix": "SLACK",
                "id": 100,
                "content": "Single line content",
                "timestamp": datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc),
            }
        ]
        print_entries_table(entries, long=False)

        # should be called twice: once for table, once for total
        assert mock_print.call_count == 2
        assert "Total entries: 1" in str(mock_print.call_args_list[1])

    @patch("minid.utils.print")
    def test_print_table_with_multiline_entry_short(self, mock_print):
        entries = [
            {
                "prefix": "SLACK",
                "id": 101,
                "content": "First line\nSecond line\nThird line",
                "timestamp": datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc),
            }
        ]
        print_entries_table(entries, long=False)

        assert mock_print.call_count == 2

        # in short mode with multiline content,
        # should show first line + "more lines" indicator
        table = mock_print.call_args_list[0][0][0]
        assert len(table.rows) == 1
        content_cell = table.columns[1]._cells[0]
        assert "First line" in content_cell
        assert "+ 2 more lines" in content_cell

    @patch("minid.utils.print")
    def test_print_table_with_two_line_entry_short(self, mock_print):
        entries = [
            {
                "prefix": "SLACK",
                "id": 102,
                "content": "First line\nSecond line",
                "timestamp": datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc),
            }
        ]
        print_entries_table(entries, long=False)

        assert mock_print.call_count == 2
        table = mock_print.call_args_list[0][0][0]
        content_cell = table.columns[1]._cells[0]
        assert "First line" in content_cell
        assert "+ 1 more line" in content_cell

    @patch("minid.utils.print")
    def test_print_table_with_entries_long_mode(self, mock_print):
        entries = [
            {
                "prefix": "GHPR",
                "id": 200,
                "content": "Long mode\nShows all content",
                "timestamp": datetime(2025, 1, 15, 14, 30, tzinfo=timezone.utc),
            }
        ]
        print_entries_table(entries, long=True)

        assert mock_print.call_count == 2
        table = mock_print.call_args_list[0][0][0]
        # long mode shows full content, no truncation
        content_cell = table.columns[1]._cells[0]
        assert "Long mode\nShows all content" in content_cell
        assert "+ " not in content_cell  # no "more lines" indicator in long mode

    @patch("minid.utils.print")
    def test_print_table_with_multiple_entries(self, mock_print):
        entries = [
            {
                "prefix": "SLACK",
                "id": 1,
                "content": "First entry",
                "timestamp": datetime(2025, 1, 1, tzinfo=timezone.utc),
            },
            {
                "prefix": "GHPR",
                "id": 2,
                "content": "Second entry",
                "timestamp": datetime(2025, 1, 2, tzinfo=timezone.utc),
            },
            {
                "prefix": "SLACK",
                "id": 3,
                "content": "Third entry",
                "timestamp": datetime(2025, 1, 3, tzinfo=timezone.utc),
            },
        ]
        print_entries_table(entries, long=False)

        assert mock_print.call_count == 2
        assert "Total entries: 3" in str(mock_print.call_args_list[1])

    @patch("minid.utils.print")
    def test_print_table_with_url_content(self, mock_print):
        entries = [
            {
                "prefix": "SLACK",
                "id": 50,
                "content": "Check out https://github.com/user/repo",
                "timestamp": datetime(2025, 1, 1, tzinfo=timezone.utc),
            }
        ]
        print_entries_table(entries, long=False)

        assert mock_print.call_count == 2
        table = mock_print.call_args_list[0][0][0]
        content_cell = table.columns[1]._cells[0]
        assert "[link=https://github.com/user/repo]" in content_cell

    @patch("minid.utils.print")
    def test_print_table_empty_content(self, mock_print):
        entries = [
            {
                "prefix": "TEST",
                "id": 999,
                "content": "",
                "timestamp": datetime(2025, 1, 1, tzinfo=timezone.utc),
            }
        ]
        print_entries_table(entries, long=False)

        assert mock_print.call_count == 2
        assert "Total entries: 1" in str(mock_print.call_args_list[1])

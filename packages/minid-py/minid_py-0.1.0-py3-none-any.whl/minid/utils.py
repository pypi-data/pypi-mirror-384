from re import sub
from sys import exit

from click import Group
from rich import print
from rich.table import Table
from urlextract import URLExtract

from minid.db import DB


def read_multiline_input() -> str:
    print("Content (Ctrl+D or 2 blank lines to finish):")

    lines = []
    consecutive_empty = 0

    try:
        while True:
            line = input()
            if line == "":
                consecutive_empty += 1
                if consecutive_empty >= 2:
                    break
            else:
                consecutive_empty = 0
            lines.append(line)
    except EOFError:
        pass

    return "\n".join(lines).rstrip()


def require_prefix(db: DB, query: str) -> str:
    matched_prefix = db.find_prefix_match(query)
    if not matched_prefix:
        print(f"[red]Error: No registered prefix matches '{query}'[/red]")
        registered = db.list_prefixes()
        if registered:
            print(f"Registered prefixes: {', '.join(registered)}")
        exit(1)
    return matched_prefix


class FuzzyCommandGroup(Group):
    aliases = {
        "query": "find",
    }

    def get_command(self, ctx, cmd_name):
        rv = Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv

        # fuzzy matching
        matches = []
        for command in self.list_commands(ctx) + list(self.aliases.keys()):
            if command.startswith(cmd_name.lower()):
                if command in self.aliases:
                    matches.append(self.aliases[command])
                else:
                    matches.append(command)

        if len(matches) == 1:
            return Group.get_command(self, ctx, matches[0])
        elif len(matches) > 1:
            ctx.fail(f"Ambiguous command: {cmd_name}. Could be: {', '.join(matches)}")
        else:
            ctx.fail(f"No such command: {cmd_name}")


def process_links(text: str) -> str:
    """Convert URLs and GitHub references to clickable Rich links"""
    text = _handle_urls(text)
    text = _handle_github_links(text)
    return text


def _handle_urls(text: str) -> str:
    extractor = URLExtract()
    urls = extractor.find_urls(text, only_unique=True)

    # process URLs from longest to shortest to avoid partial replacements
    urls = sorted(urls, key=len, reverse=True)

    for url in urls:
        # ensure url is a string (handle tuple case)
        if isinstance(url, tuple):
            url = url[0]  # pragma: no cover

        # skip URLs that are already inside Rich link markup
        # look for [link=URL] pattern
        if f"[link={url}]" in text:
            continue

        # replace unlinked URLs with Rich link markup
        replacement = f"[link={url}]{url}[/link]"
        text = text.replace(url, replacement)

    return text


def _handle_github_links(text: str) -> str:
    github_pattern = r"([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+)#(\d+)"

    def replace_github_ref(match):
        full_match = match.group(0)
        owner_repo = match.group(1)
        issue_num = match.group(2)
        github_url = f"https://github.com/{owner_repo}/issues/{issue_num}"
        return f"[link={github_url}]{full_match}[/link]"

    return sub(github_pattern, replace_github_ref, text)


def print_entries_table(entries: list[dict], long: bool = False) -> None:
    table = Table(
        show_header=long,
        header_style="bold dim",
        expand=True,
        show_edge=long,
        show_lines=long,
    )
    table.add_column("ID", no_wrap=True, style="cyan")
    table.add_column("Content", style="white", no_wrap=False)
    if long:
        table.add_column("Timestamp", style="green")

    for entry in entries:
        args = []

        args.append(f"{entry['prefix']}-{entry['id']}")

        content = entry.get("content", "")
        if long:
            args.append(process_links(content))
        else:
            lines = content.split("\n")
            first_line = lines.pop(0).rstrip()
            display_line = process_links(first_line)
            more_info = ""
            if lines:
                more_info = f" [dim]+ {len(lines)} more line{'s' if len(lines) != 1 else ''}[/dim]"
            args.append(display_line + more_info)

        if long:
            args.append(entry["timestamp"].strftime("%Y-%m-%d\nat %H:%M"))

        table.add_row(*args)

    print(table)
    print(f"\n[bold]Total entries: {len(entries)}[/bold]")

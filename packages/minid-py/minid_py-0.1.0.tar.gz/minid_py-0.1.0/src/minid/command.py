from sys import exit
from typing import cast

from click import argument, group, option
from rich import print

from minid.db import DB, init_db
from minid.exceptions import NotFound
from minid.utils import (
    FuzzyCommandGroup,
    print_entries_table,
    process_links,
    read_multiline_input,
    require_prefix,
)

_db = cast(DB, None)  # lie to pyright


@group(cls=FuzzyCommandGroup, name="minid")
def main():
    """Minid - Generate and store minimal IDs for links and content"""
    global _db
    _db = init_db()  # pragma: no cover


@main.command("prefix", short_help="Register a new prefix or list all prefixes")
@argument("newprefix", required=False)
def prefix(newprefix: str | None):
    """Register a new prefix for storing entries, or list all prefixes if no argument provided"""

    if newprefix:
        _db.register_prefix(newprefix)
        print(f"[green]Registered prefix: {newprefix}[/green]")
    else:
        prefixes = _db.list_prefixes()
        if prefixes:
            print("[blue]Registered prefixes:[/blue]")
            for prefix in prefixes:
                print(f"  {prefix}")
        else:
            print("[yellow]No prefixes registered[/yellow]")


@main.command("new", short_help="Create a new entry")
@argument("prefix")
@argument("content", required=False)
def new_entry(prefix: str, content: str | None = None):
    """Create a new entry under the specified prefix"""
    matched_prefix = require_prefix(_db, prefix)
    print(f"[blue]Using prefix: {matched_prefix}[/blue]")

    if not content:
        content = read_multiline_input()

    if content.strip():
        entry = _db.store_entry(matched_prefix, content)
        print(f"[green]Stored as [bold]{matched_prefix}-{entry['id']}[/bold][/green]")
    else:
        print("[yellow]No content entered[/yellow]")


@main.command("find", short_help="Search for entries")
@argument("query", required=False)
@option("--prefix", "-p", help="Limit search to specific prefix")
@option("--long", "-l", is_flag=True, help="Show full content instead of preview")
def find_entries(query: str, prefix: str | None = None, long: bool = False):
    """Search for entries containing the specified text"""
    search_prefix = None
    if prefix:
        search_prefix = require_prefix(_db, prefix)
        print(f"[blue]Searching in prefix: {search_prefix}[/blue]")

    if not query:
        query = ""

    entries = _db.search_entries(query, search_prefix)

    if not entries:
        print("[yellow]No entries found[/yellow]")
        return

    print_entries_table(entries, long=long)


@main.command("get", short_help="Get a specific entry")
@argument("prefix")
@argument("entry_id", type=int)
def get_entry(prefix: str, entry_id: int):
    """Get a specific entry by prefix and ID"""
    matched_prefix = require_prefix(_db, prefix)

    try:
        entry = _db.get_entry(matched_prefix, entry_id)
        print(f"[bold cyan]{matched_prefix}:{entry_id}[/bold cyan]")
        local_time = entry["timestamp"].astimezone()
        print(f"[green]Created: {local_time.strftime('%Y-%m-%d %H:%M:%S %Z')}[/green]")
        print()
        print(process_links(entry.get("content", "")))
    except NotFound:
        print(f"[red]Entry {matched_prefix}:{entry_id} not found[/red]")
        exit(1)

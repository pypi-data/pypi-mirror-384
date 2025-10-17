from datetime import datetime

from pytest import fixture, raises

import minid.db
from minid.db import DB, NotFound, init_db


@fixture()
def db() -> DB:
    return init_db()


class TestPrefixes:
    def test_register_prefix(self, db: DB):
        db.register_prefix("SLACK")
        prefixes = db.list_prefixes()
        assert "SLACK" in prefixes

    def test_register_multiple_prefixes(self, db: DB):
        db.register_prefix("SLACK")
        db.register_prefix("GITHUB")
        db.register_prefix("JIRA")

        prefixes = db.list_prefixes()
        assert "SLACK" in prefixes
        assert "GITHUB" in prefixes
        assert "JIRA" in prefixes
        assert len(prefixes) == 3

    def test_list_prefixes_empty(self, db: DB):
        prefixes = db.list_prefixes()
        assert prefixes == []

    def test_list_prefixes_corrupted_data(self, db: DB):
        # test edge case where __prefixes is not a list
        with db._transaction(write=True) as txn:
            txn.put("__prefixes", "not a list")

        prefixes = db.list_prefixes()
        assert prefixes == []  # should return empty list for non-list data

    def test_register_duplicate_prefix(self, db: DB):
        db.register_prefix("SLACK")
        db.register_prefix("SLACK")

        prefixes = db.list_prefixes()
        assert prefixes.count("SLACK") == 1


class TestEntries:
    def test_store_entry(self, db: DB):
        content = "This is a test entry with multiple lines\nand some more content"
        entry = db.store_entry("SLACK", content)

        assert entry["id"] >= 100
        retrieved = db.get_entry("SLACK", entry["id"])
        assert retrieved == entry
        assert isinstance(retrieved["timestamp"], datetime)

    def test_store_multiple_entries(self, db: DB):
        content1 = "First entry"
        content2 = "Second entry with\nmultiple lines"

        entry1 = db.store_entry("SLACK", content1)
        entry2 = db.store_entry("SLACK", content2)

        assert entry2["id"] == entry1["id"] + 1

        entry1 = db.get_entry("SLACK", entry1["id"])
        entry2 = db.get_entry("SLACK", entry2["id"])

        assert entry1["content"] == content1
        assert entry2["content"] == content2

    def test_store_entry_different_prefixes(self, db: DB):
        content = "Test content"

        slack = db.store_entry("SLACK", content)
        github = db.store_entry("GITHUB", content)

        assert slack["id"] == github["id"]  # both should start at 100

        slack_entry = db.get_entry("SLACK", slack["id"])
        github_entry = db.get_entry("GITHUB", github["id"])

        assert slack_entry["content"] == content
        assert github_entry["content"] == content

    def test_get_nonexistent_entry(self, db: DB):
        with raises(NotFound):
            db.get_entry("NONEXISTENT", 100)

    def test_get_corrupted_entry_data(self, db: DB):
        # test edge case where stored data is not a dict
        with db._transaction(write=True) as txn:
            txn.put("CORRUPT:100", "not a dict")

        with raises(NotFound):
            db.get_entry("CORRUPT", 100)  # should raise NotFound for non-dict data

    def test_process_entry_with_none(self, db: DB):
        # test _process_entry with None (edge case)
        with raises(NotFound):
            db._process_entry(None)

    def test_store_entry_with_newlines(self, db: DB):
        content = "Line 1\n\nLine 3\nLine 4\n\n\nLine 7"
        entry = db.store_entry("TEST", content)

        retrieved = db.get_entry("TEST", entry["id"])
        assert retrieved["content"] == content

    def test_store_empty_content(self, db: DB):
        content = ""
        entry = db.store_entry("EMPTY", content)

        retrieved = db.get_entry("EMPTY", entry["id"])
        assert retrieved["content"] == content

    def test_search_entries(self, db: DB):
        db.store_entry("SEARCH", "This is a test entry")
        db.store_entry("SEARCH", "Another entry with different content")
        db.store_entry("OTHER", "This contains test keyword too")

        # search all entries
        results = db.search_entries("test")
        assert len(results) == 2
        assert all("test" in entry["content"].lower() for entry in results)

        # search with prefix filter
        results = db.search_entries("test", "SEARCH")
        assert len(results) == 1
        assert results[0]["prefix"] == "SEARCH"

        # search with no matches
        results = db.search_entries("nomatch")
        assert len(results) == 0

    def test_get_all_entries(self, db: DB):
        db.store_entry("ALL1", "Entry 1")
        db.store_entry("ALL2", "Entry 2")
        db.store_entry("ALL1", "Entry 3")

        # get all entries
        all_entries = db.get_all_entries()
        assert len(all_entries) == 3

        # should be sorted by timestamp (newest first)
        timestamps = [entry["timestamp"] for entry in all_entries]
        assert timestamps == sorted(timestamps, reverse=True)

        # get entries for specific prefix
        prefix_entries = db.get_all_entries("ALL1")
        assert len(prefix_entries) == 2
        assert all(entry["prefix"] == "ALL1" for entry in prefix_entries)

    def test_find_prefix_match(self, db: DB):
        db.register_prefix("SLACK")
        db.register_prefix("SLACKCORP")
        db.register_prefix("GITHUB")

        # exact match
        assert db.find_prefix_match("SLACK") == "SLACK"

        # partial match (returns first match)
        assert db.find_prefix_match("SL") == "SLACK"

        # case insensitive
        assert db.find_prefix_match("slack") == "SLACK"
        assert db.find_prefix_match("git") == "GITHUB"

        # no match
        assert db.find_prefix_match("NOMATCH") is None


class TestRawDB:
    def test_put_and_get(self, db: DB):
        data = {"title": "Test Item", "url": "https://example.com"}

        id = db._put("item", data)
        retrieved = db._get("item", id)
        data["_key"] = f"item:{id}"

        assert retrieved == data

    def test_patch(self, db: DB):
        data = {"title": "Test Item"}

        id = db._put("item", data)

        with raises(NotFound):
            db._patch("item", id - 1, {"nonsense": "here"})

        db._patch("item", id, {"title": "Test Item Again"})
        retrieved = db._get("item", id)
        assert retrieved["title"] == "Test Item Again"

    def test_get_nonexistent(self, db: DB):
        with raises(NotFound):
            db._get("item", 5)

    def test_delete(self, db: DB):
        data = {"title": "Test Item"}

        id = db._put("item", data)
        db._delete("item", id)

        with raises(NotFound):
            db._get("item", id)

    def test_all_with_prefix(self, db: DB):
        data1: dict = {"title": "Item 1"}
        data2: dict = {"title": "Item 2"}
        data3: dict = {"title": "Other"}

        data1_id = db._put("item", data1)
        data2_id = db._put("item", data2)
        data3_id = db._put("other", data3)

        items = list(db._all(prefix="item"))
        assert len(items) == 2

        # check that we have the right items with prefix information
        item_ids = [item["_key"] for item in items]
        assert len(item_ids) == 2
        assert f"item:{data1_id}" in item_ids
        assert f"item:{data2_id}" in item_ids

    def test_all_no_prefix(self, db: DB):
        data1: dict = {"title": "Item 1"}
        data2: dict = {"title": "Item 2"}
        data3: dict = {"title": "Other"}

        data1["id"] = db._put("item", data1)
        data2["id"] = db._put("item", data2)
        data3["id"] = db._put("other", data3)

        items = list(db._all())
        assert len(items) == 3

        # check that we have the right items and prefixes
        item_entries = [item for item in items if item["_key"].split(":")[0] == "item"]
        other_entries = [item for item in items if item["_key"].split(":")[0] == "other"]

        assert len(item_entries) == 2
        assert len(other_entries) == 1

        # check that all item entries have the correct titles
        item_titles = [item["title"] for item in item_entries]
        assert "Item 1" in item_titles
        assert "Item 2" in item_titles

        # check other entry
        assert other_entries[0]["title"] == "Other"

    def test_all_empty_prefix(self, db: DB):
        items = list(db._all(prefix="nonexistent"))
        assert items == []

    def test_put_generates_sequential_ids(self, db: DB):
        data = {"title": "Test"}

        id1 = db._put("item", data)
        id2 = db._put("item", data)
        id3 = db._put("other", data)

        assert id1 == 100
        assert id2 == 101
        assert id3 == 100

    def test_put_with_corrupted_hwm(self, db: DB):
        # test edge case where __hwm is not an int
        data = {"title": "Test"}

        # put corrupted hwm data
        with db._transaction(write=True) as txn:
            txn.put("__hwm:item", "not an int")

        # should still work and start from 100
        id1 = db._put("item", data)
        assert id1 == 100

    def test_id_hwm(self, db: DB):
        data = {"title": "Test"}

        id1 = db._put("item", data)
        id2 = db._put("item", data)
        id3 = db._put("item", data)

        # delete all items
        for entry in db._all():
            db._delete("item", int(entry["_key"].split(":")[1]))

        # next item should continue from highest id still
        id4 = db._put("item", data)

        assert id1 == 100
        assert id2 == 101
        assert id3 == 102
        assert id4 == 103


class TestInitDB:
    def test_init_db_singleton(self):
        # Test that init_db returns the same instance when called multiple times
        # First reset the instance to None
        minid.db._db_instance = None

        db1 = init_db()
        db2 = init_db()

        assert db1 is db2  # Should be the exact same object

from contextlib import contextmanager
from datetime import UTC, datetime
from json import dumps, loads
from typing import Generator, cast

from lmdb import open

from minid.config import config
from minid.exceptions import NotFound

_ONE_GB = 2**30


class DB:
    def __init__(self, path: str):
        self.env = open(path, map_size=_ONE_GB)

    def register_prefix(self, prefix: str) -> None:
        prefixes = self.list_prefixes()
        if prefix not in prefixes:
            prefixes.append(prefix)
            with self._transaction(write=True) as txn:
                txn.put("__prefixes", prefixes)

    def list_prefixes(self) -> list:
        try:
            with self._transaction() as txn:
                if isinstance(r := txn.get("__prefixes"), list):
                    return r
                else:
                    return []
        except NotFound:
            return []

    def find_prefix_match(self, query: str) -> str | None:
        query_upper = query.upper()
        prefixes = self.list_prefixes()

        for prefix in prefixes:
            if prefix.upper().startswith(query_upper):
                return prefix

        return None

    def search_entries(self, query: str, prefix: str | None = None) -> list[dict]:
        results = []
        query_lower = query.lower()

        for entry in self._all(prefix):
            if query_lower in entry.get("content", "").lower():
                entry = self._process_entry(entry)
                results.append(entry)

        return sorted(results, key=lambda x: x["timestamp"], reverse=True)

    def get_all_entries(self, prefix: str | None = None) -> list[dict]:
        entries = list(self._all(prefix))
        entries = [self._process_entry(entry) for entry in entries]
        entries.sort(key=lambda x: x["timestamp"], reverse=True)
        return entries

    def store_entry(self, prefix: str, content: str) -> dict:
        id = self._put(
            prefix,
            {
                "content": content,
                "timestamp": datetime.now(UTC).timestamp(),
            },
        )
        return self.get_entry(prefix, id)

    def get_entry(self, prefix: str, id: int) -> dict:
        entry = self._get(prefix, id)
        return self._process_entry(entry)

    def _process_entry(self, entry: dict | None) -> dict:
        if entry is None:
            raise NotFound()
        key_parts = entry.pop("_key").split(":")
        entry["prefix"] = key_parts[0]
        entry["id"] = int(key_parts[-1])
        entry["timestamp"] = datetime.fromtimestamp(entry["timestamp"], UTC)
        return entry

    @contextmanager
    def _transaction(self, write=False):
        with self.env.begin(write=write) as txn:
            yield TransactionWrapper(txn)

    def _put(self, prefix: str, data: dict) -> int:
        next_number = 100

        try:
            with self._transaction() as txn:
                r = txn.get(f"__hwm:{prefix}")
                if isinstance(r, int):
                    next_number = max(r + 1, 100)
        except NotFound:
            pass

        with self._transaction(write=True) as txn:
            txn.put(f"{prefix}:{next_number}", data)
            txn.put(f"__hwm:{prefix}", next_number)
            return next_number

    def _patch(self, prefix: str, number: int, data: dict) -> None:
        current = self._get(prefix, number)

        data = {**current, **data}

        with self._transaction(write=True) as txn:
            txn.put(f"{prefix}:{str(number)}", data)

    def _get(self, prefix: str, number: int) -> dict:
        with self._transaction() as txn:
            r = txn.get(f"{prefix}:{str(number)}")
            if isinstance(r, dict):
                return r
            else:
                raise NotFound()

    def _delete(self, prefix: str, number: int) -> None:
        with self._transaction(write=True) as txn:
            txn.delete(f"{prefix}:{str(number)}")

    def _all(self, prefix: str | None = None) -> Generator[dict]:
        with self._transaction() as txn:
            for data in txn.cursor(prefix):
                yield data


class TransactionWrapper:
    def __init__(self, txn):
        self.txn = txn

    def cursor(self, prefix: str | None) -> Generator[dict]:
        c = self.txn.cursor()
        if prefix:
            c.set_range(prefix.encode())

        for key, value in c:
            key = key.decode()
            if prefix and not key.startswith(f"{prefix}:"):
                break
            if key.startswith("__"):
                continue

            data = loads(value.decode())
            data["_key"] = key
            yield data

    def put(self, key: str, value: dict | list | int | str | None) -> None:
        self.txn.put(key.encode(), dumps(value).encode())

    def get(self, key: str) -> dict | list | int | str | None:
        value = self.txn.get(key.encode())
        if value:
            data = loads(value.decode())
            if isinstance(data, dict):
                data["_key"] = key
            return data
        else:
            raise NotFound()

    def delete(self, key: str):
        self.txn.delete(key.encode())


_db_instance = cast(DB, None)


def init_db() -> DB:
    global _db_instance
    if _db_instance is None:
        db_path = config.db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _db_instance = DB(str(db_path))
    return _db_instance

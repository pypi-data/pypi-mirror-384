from pathlib import Path
from tempfile import TemporaryDirectory

from pytest import fixture

import minid.db
from minid.config import config


@fixture(autouse=True)
def setup_test_db():
    with TemporaryDirectory() as temp_dir:
        # reset the DB instance so init_db() creates it fresh
        minid.db._db_instance = None

        # set config to point to new temp directory
        config._config = {"db_path": str(Path(temp_dir) / "test_db")}
        yield temp_dir

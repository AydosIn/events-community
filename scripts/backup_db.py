#!/usr/bin/env python3
"""Create a timestamped SQLite backup of the Events Community database."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from config import DATABASE_URL


def resolve_database_path() -> Path:
    if not DATABASE_URL.startswith("sqlite:///"):
        raise RuntimeError("Backup script only supports SQLite databases.")

    db_path = DATABASE_URL.removeprefix("sqlite:///")
    if db_path == ":memory:":
        raise RuntimeError("Cannot back up an in-memory database.")

    return Path(db_path)


def create_backup(destination_dir: Path | None = None) -> Path:
    source = resolve_database_path()
    if not source.exists():
        raise FileNotFoundError(f"Database file not found: {source}")

    backup_dir = destination_dir or source.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    destination = backup_dir / f"events_community_{timestamp}.db"
    shutil.copy2(source, destination)
    return destination


if __name__ == "__main__":
    backup_path = create_backup()
    print(f"Backup created: {backup_path}")

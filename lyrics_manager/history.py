"""Historia zmian tekstu - migawki w bazie SQLite + porownywanie wersji."""

from __future__ import annotations

import difflib
import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .config import data_dir

DB_NAME = "history.db"


@dataclass
class Snapshot:
    id: int
    song_key: str
    created_at: str
    label: str
    kind: str          # "auto" | "manual"
    content: str
    lines: int
    words: int
    chars: int

    @property
    def timestamp(self) -> datetime:
        try:
            return datetime.fromisoformat(self.created_at)
        except ValueError:
            return datetime.now()

    def display(self) -> str:
        return f"{self.timestamp:%Y-%m-%d %H:%M:%S}  ·  {self.label}"


def song_key(path: str | None, title: str) -> str:
    """Stabilny identyfikator utworu: sciezka pliku albo hash tytulu."""
    base = path or f"untitled::{title}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:16]


class HistoryStore:
    def __init__(self, db_path: Path | None = None) -> None:
        self.path = db_path or (data_dir() / DB_NAME)
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS snapshots (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                song_key   TEXT NOT NULL,
                created_at TEXT NOT NULL,
                label      TEXT NOT NULL DEFAULT '',
                kind       TEXT NOT NULL DEFAULT 'auto',
                content    TEXT NOT NULL,
                hash       TEXT NOT NULL,
                lines      INTEGER NOT NULL DEFAULT 0,
                words      INTEGER NOT NULL DEFAULT 0,
                chars      INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_snapshots_song ON snapshots(song_key, created_at DESC)"
        )
        self._conn.commit()

    # -- zapis ------------------------------------------------------------

    def add(self, key: str, content: str, label: str = "", kind: str = "auto") -> Snapshot | None:
        """Dodaje migawke. Zwraca None, jesli tresc jest identyczna z ostatnia."""
        digest = hashlib.sha1(content.encode("utf-8")).hexdigest()
        row = self._conn.execute(
            "SELECT hash FROM snapshots WHERE song_key = ? ORDER BY id DESC LIMIT 1", (key,)
        ).fetchone()
        if row and row["hash"] == digest:
            return None
        if not content.strip():
            return None

        now = datetime.now().isoformat(timespec="seconds")
        lines = len([ln for ln in content.splitlines() if ln.strip()])
        words = len(content.split())
        cur = self._conn.execute(
            """INSERT INTO snapshots (song_key, created_at, label, kind, content, hash,
                                      lines, words, chars)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (key, now, label, kind, content, digest, lines, words, len(content)),
        )
        self._conn.commit()
        return Snapshot(cur.lastrowid, key, now, label, kind, content, lines, words, len(content))

    def delete(self, snapshot_id: int) -> None:
        self._conn.execute("DELETE FROM snapshots WHERE id = ?", (snapshot_id,))
        self._conn.commit()

    def prune(self, key: str, keep: int = 200) -> None:
        self._conn.execute(
            """DELETE FROM snapshots WHERE song_key = ? AND id NOT IN
               (SELECT id FROM snapshots WHERE song_key = ? ORDER BY id DESC LIMIT ?)""",
            (key, key, keep),
        )
        self._conn.commit()

    # -- odczyt -----------------------------------------------------------

    def list(self, key: str, limit: int = 200) -> list[Snapshot]:
        rows = self._conn.execute(
            "SELECT * FROM snapshots WHERE song_key = ? ORDER BY id DESC LIMIT ?", (key, limit)
        ).fetchall()
        return [self._to_snapshot(r) for r in rows]

    def get(self, snapshot_id: int) -> Snapshot | None:
        row = self._conn.execute(
            "SELECT * FROM snapshots WHERE id = ?", (snapshot_id,)
        ).fetchone()
        return self._to_snapshot(row) if row else None

    @staticmethod
    def _to_snapshot(row: sqlite3.Row) -> Snapshot:
        return Snapshot(
            id=row["id"], song_key=row["song_key"], created_at=row["created_at"],
            label=row["label"], kind=row["kind"], content=row["content"],
            lines=row["lines"], words=row["words"], chars=row["chars"],
        )

    def close(self) -> None:
        try:
            self._conn.close()
        except Exception:
            pass


def diff_text(old: str, new: str, label_old: str = "", label_new: str = "") -> str:
    """Czytelny diff wersowy."""
    diff = difflib.unified_diff(
        old.splitlines(), new.splitlines(),
        fromfile=label_old or "poprzednia", tofile=label_new or "aktualna",
        lineterm="", n=2,
    )
    return "\n".join(diff)


def changed_line_count(old: str, new: str) -> int:
    sm = difflib.SequenceMatcher(None, old.splitlines(), new.splitlines())
    changed = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != "equal":
            changed += max(i2 - i1, j2 - j1)
    return changed

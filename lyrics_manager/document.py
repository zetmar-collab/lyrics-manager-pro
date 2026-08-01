"""Model dokumentu utworu i zapis/odczyt plikow .lyr (JSON) oraz .txt."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

from .export import SongMeta

FILE_EXT = ".lyr"
FILE_MAGIC = "lyrics-manager-pro"


@dataclass
class Document:
    meta: SongMeta = field(default_factory=SongMeta)
    text: str = ""
    text_language: str = "pl"
    path: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    modified_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    # --- serializacja ----------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "format": FILE_MAGIC,
            "version": 1,
            "meta": asdict(self.meta),
            "text": self.text,
            "text_language": self.text_language,
            "created_at": self.created_at,
            "modified_at": datetime.now().isoformat(timespec="seconds"),
        }

    @classmethod
    def from_dict(cls, data: dict, path: str | None = None) -> "Document":
        meta_data = data.get("meta") or {}
        meta = SongMeta(**{k: meta_data.get(k, "") for k in SongMeta().__dict__})
        return cls(
            meta=meta,
            text=data.get("text", ""),
            text_language=data.get("text_language", "pl"),
            path=path,
            created_at=data.get("created_at") or datetime.now().isoformat(timespec="seconds"),
            modified_at=data.get("modified_at") or datetime.now().isoformat(timespec="seconds"),
        )

    # --- pliki -----------------------------------------------------------

    def save(self, path: str | None = None) -> str:
        target = Path(path or self.path or "")
        if not str(target):
            raise ValueError("No path given")
        if target.suffix.lower() in {".txt", ".md"}:
            target.write_text(self.text, encoding="utf-8")
        else:
            if not target.suffix:
                target = target.with_suffix(FILE_EXT)
            target.write_text(
                json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
            )
        self.path = str(target)
        self.modified_at = datetime.now().isoformat(timespec="seconds")
        return self.path

    @classmethod
    def load(cls, path: str) -> "Document":
        p = Path(path)
        raw = p.read_text(encoding="utf-8")
        if p.suffix.lower() in {".txt", ".md"}:
            doc = cls(text=raw, path=str(p))
            doc.meta.title = p.stem
            return doc
        try:
            data = json.loads(raw)
        except ValueError:
            doc = cls(text=raw, path=str(p))
            doc.meta.title = p.stem
            return doc
        if not isinstance(data, dict) or data.get("format") != FILE_MAGIC:
            doc = cls(text=raw, path=str(p))
            doc.meta.title = p.stem
            return doc
        return cls.from_dict(data, str(p))

    # --- pomocnicze ------------------------------------------------------

    @property
    def display_title(self) -> str:
        if self.meta.title.strip():
            return self.meta.title.strip()
        if self.path:
            return Path(self.path).stem
        return ""

    @property
    def filename(self) -> str:
        return Path(self.path).name if self.path else ""

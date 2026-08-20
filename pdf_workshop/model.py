from __future__ import annotations
from dataclasses import dataclass, asdict, field
from pathlib import Path
from uuid import uuid4
import hashlib
import json


def _id() -> str:
    return str(uuid4())


@dataclass
class Crop:
    top_mm: float = 0.0
    bottom_mm: float = 0.0
    left_mm: float = 0.0
    right_mm: float = 0.0


@dataclass
class SourceDocument:
    id: str
    path: str
    sha256: str
    page_count: int

    @staticmethod
    def make(path: str, page_count: int) -> "SourceDocument":
        p = Path(path)
        h = hashlib.sha256()
        with p.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return SourceDocument(_id(), str(p.resolve()), h.hexdigest(), page_count)


@dataclass
class Page:
    id: str = field(default_factory=_id)
    source_document_id: str = ""
    source_page_index: int = 0
    region: str = "FULL"  # FULL LEFT RIGHT
    split_ratio: float = 0.5
    rotation: int = 0
    crop: Crop = field(default_factory=Crop)
    excluded: bool = False
    detected_page_number: str | None = None


@dataclass
class Project:
    title: str = "Untitled"
    schema_version: int = 1
    sources: list[SourceDocument] = field(default_factory=list)
    pages: list[Page] = field(default_factory=list)

    def source_by_id(self, source_id: str) -> SourceDocument:
        return next(s for s in self.sources if s.id == source_id)

    def save(self, path: str) -> None:
        payload = asdict(self)
        tmp = Path(path).with_suffix(Path(path).suffix + ".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)

    @staticmethod
    def load(path: str) -> "Project":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        pr = Project(title=raw.get("title", "Untitled"), schema_version=raw.get("schema_version", 1))
        pr.sources = [SourceDocument(**s) for s in raw.get("sources", [])]
        pages = []
        for p in raw.get("pages", []):
            p = dict(p)
            p["crop"] = Crop(**p.get("crop", {}))
            pages.append(Page(**p))
        pr.pages = pages
        return pr

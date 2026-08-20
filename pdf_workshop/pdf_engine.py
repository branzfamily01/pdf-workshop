from __future__ import annotations
from pathlib import Path
from copy import deepcopy
from pypdf import PdfReader, PdfWriter
from .model import Project, SourceDocument, Page

PT_PER_MM = 72.0 / 25.4


def import_pdf(project: Project, path: str) -> SourceDocument:
    reader = PdfReader(path)
    src = SourceDocument.make(path, len(reader.pages))
    project.sources.append(src)
    for i in range(len(reader.pages)):
        project.pages.append(Page(source_document_id=src.id, source_page_index=i))
    if project.title == "Untitled":
        project.title = Path(path).stem
    return src


def page_dimensions_mm(path: str, index: int) -> tuple[float, float]:
    page = PdfReader(path).pages[index]
    w = float(page.mediabox.width) / PT_PER_MM
    h = float(page.mediabox.height) / PT_PER_MM
    return w, h


def has_text(path: str, index: int) -> bool:
    try:
        txt = PdfReader(path).pages[index].extract_text() or ""
        return bool(txt.strip())
    except Exception:
        return False


def diagnose(project: Project) -> dict[str, int]:
    stats = {"pages": 0, "landscape": 0, "a3_like": 0, "no_text": 0, "spread_candidates": 0}
    readers: dict[str, PdfReader] = {}
    for page in project.pages:
        if page.excluded:
            continue
        src = project.source_by_id(page.source_document_id)
        if src.id not in readers:
            readers[src.id] = PdfReader(src.path)
        p = readers[src.id].pages[page.source_page_index]
        w_pt, h_pt = float(p.mediabox.width), float(p.mediabox.height)
        w, h = w_pt / PT_PER_MM, h_pt / PT_PER_MM
        stats["pages"] += 1
        landscape = w > h
        if landscape:
            stats["landscape"] += 1
        # A3 tolerance; accepts portrait/landscape
        dims = sorted((w, h))
        a3 = abs(dims[0] - 297) < 18 and abs(dims[1] - 420) < 22
        if a3:
            stats["a3_like"] += 1
        if not ((p.extract_text() or "").strip()):
            stats["no_text"] += 1
        if landscape and (w / h) > 1.30:
            stats["spread_candidates"] += 1
    return stats


def _apply_region_and_crop(out_page, model_page: Page) -> None:
    box = out_page.mediabox
    left, bottom, right, top = map(float, [box.left, box.bottom, box.right, box.top])
    if model_page.region == "LEFT":
        right = left + (right - left) * model_page.split_ratio
    elif model_page.region == "RIGHT":
        left = left + (right - left) * model_page.split_ratio
    left += model_page.crop.left_mm * PT_PER_MM
    right -= model_page.crop.right_mm * PT_PER_MM
    bottom += model_page.crop.bottom_mm * PT_PER_MM
    top -= model_page.crop.top_mm * PT_PER_MM
    if right <= left or top <= bottom:
        raise ValueError("crop results in an empty page")
    out_page.mediabox.lower_left = (left, bottom)
    out_page.mediabox.upper_right = (right, top)
    out_page.cropbox.lower_left = (left, bottom)
    out_page.cropbox.upper_right = (right, top)


def export_project(project: Project, output_path: str) -> None:
    readers: dict[str, PdfReader] = {}
    writer = PdfWriter()
    for mp in project.pages:
        if mp.excluded:
            continue
        src = project.source_by_id(mp.source_document_id)
        if src.id not in readers:
            readers[src.id] = PdfReader(src.path)
        page = deepcopy(readers[src.id].pages[mp.source_page_index])
        _apply_region_and_crop(page, mp)
        if mp.rotation:
            page.rotate(mp.rotation)
        writer.add_page(page)
    out = Path(output_path)
    tmp = out.with_suffix(out.suffix + ".partial")
    with tmp.open("wb") as f:
        writer.write(f)
    # Validation before replacing destination
    check = PdfReader(str(tmp))
    expected = sum(1 for p in project.pages if not p.excluded)
    if len(check.pages) != expected:
        tmp.unlink(missing_ok=True)
        raise RuntimeError("export validation failed: page count mismatch")
    tmp.replace(out)

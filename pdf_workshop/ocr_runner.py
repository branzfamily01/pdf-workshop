from __future__ import annotations
import importlib.util
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class OCRResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""


def _bundled_tesseract_dir() -> Path | None:
    candidates = []
    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).resolve().parent / "runtime" / "tesseract")
    candidates.append(Path(__file__).resolve().parents[1] / "runtime" / "tesseract")
    for path in candidates:
        if (path / "tesseract.exe").exists():
            return path
    return None


def _prepare_ocr_environment() -> None:
    bundled = _bundled_tesseract_dir()
    if not bundled:
        return
    os.environ["PATH"] = str(bundled) + os.pathsep + os.environ.get("PATH", "")
    tessdata = bundled / "tessdata"
    if tessdata.exists():
        os.environ["TESSDATA_PREFIX"] = str(tessdata)


def availability() -> tuple[bool, str]:
    _prepare_ocr_environment()
    if importlib.util.find_spec("ocrmypdf") is None:
        return False, "OCR機能を読み込めません。配布版をもう一度ダウンロードしてください。"
    if shutil.which("tesseract") is None:
        return False, "OCR本体を読み込めません。配布版をもう一度ダウンロードしてください。"
    return True, "OCR利用可能"


def run_ocr(input_pdf: str, output_pdf: str, language: str = "jpn+eng", rotate: bool = True, deskew: bool = True) -> OCRResult:
    _prepare_ocr_environment()
    try:
        import ocrmypdf
        ocrmypdf.ocr(
            input_pdf,
            output_pdf,
            language=[x for x in language.split("+") if x],
            skip_text=True,
            rotate_pages=rotate,
            deskew=deskew,
            progress_bar=False,
        )
        return OCRResult(0, stdout="OCR completed")
    except Exception as exc:
        return OCRResult(1, stderr=str(exc))

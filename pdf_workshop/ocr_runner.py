from __future__ import annotations
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path


def availability() -> tuple[bool, str]:
    if importlib.util.find_spec("ocrmypdf") is None:
        return False, "OCRmyPDF がPython環境にありません。setup_windows.bat を再実行してください。"
    if shutil.which("tesseract") is None:
        return False, "Tesseract が見つかりません。Tesseract 5 と jpn/eng 言語データをインストールしてください。"
    return True, "OCR利用可能"


def run_ocr(input_pdf: str, output_pdf: str, language: str = "jpn+eng", rotate: bool = True, deskew: bool = True) -> subprocess.CompletedProcess:
    cmd = [sys.executable, "-m", "ocrmypdf", "--skip-text", "-l", language]
    if rotate:
        cmd.append("--rotate-pages")
    if deskew:
        cmd.append("--deskew")
    cmd.extend([input_pdf, output_pdf])
    return subprocess.run(cmd, capture_output=True, text=True)

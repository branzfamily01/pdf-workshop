# Third-party components

This MVP is designed to use the following components. Verify the exact installed versions and include their full license texts when creating a distributable Windows build.

- PySide6 / Qt for Python — LGPLv3 / GPLv3 / commercial options depending on module and distribution terms.
- pypdf — BSD-3-Clause.
- pypdfium2 — Apache-2.0 / BSD-3-Clause project licensing; bundled PDFium and binary dependencies have their own notices that must accompany binary distribution.
- PDFium — BSD-style license and bundled third-party notices.
- Pillow — HPND-style open-source license.
- OpenCV — Apache-2.0 for modern OpenCV 4.x.
- OCRmyPDF — MPL-2.0.
- Tesseract OCR — Apache-2.0.
- Leptonica (used by Tesseract) — BSD-style license.

Ghostscript is intentionally NOT part of the standard MVP dependency list.

Before public binary distribution, generate a version-locked dependency manifest and copy each exact dependency license/NOTICE file into a `licenses/` directory.

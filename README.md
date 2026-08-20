# PDF Workshop MVP

教材PDFをローカルで整理・復元する Windows 向けデスクトップアプリです。

## まず使いたい方へ

**Pythonを自分でインストールする必要はありません。**

GitHub Actionsで作成される `PDFWorkshop-Windows-Portable.zip` を使います。

1. ZIPをダウンロード
2. ZIPを解凍
3. 中の `PDFWorkshop.exe` をダブルクリック
4. PDFを画面へドラッグ

OCR用のTesseractも配布フォルダへ同梱する構成です。

> 現在はMVP開発版です。Windows自動ビルドが成功したものをテスト用配布版として扱います。

## 実装済み

- PDF/複数PDF読込、ドラッグ&ドロップ
- ページプレビュー
- 回転、除外（非破壊削除）、並べ替え
- A3等の見開き左右分割
- 冊子面付け順 → 通常ページ順
- 上下左右クロップ（mm）
- プロジェクト保存/読込（`.pdfwork`）
- PDF書き出し
- OCRmyPDF + Tesseractによる日本語/英語OCR
- 基本診断（ページ数、横向き、A3相当、OCRなし、見開き候補）

## 開発者向け

ソースから実行する場合のみPython 3.12以上を使用します。通常利用者はこの手順を行いません。

```text
setup_windows.bat
run_windows.bat
```

## Windows配布版の作り方

`.github/workflows/build-windows.yml` がWindows上で自動的に以下を行います。

- Python環境をビルド用に準備
- テスト実行
- PyInstallerで `PDFWorkshop.exe` を生成
- Tesseractと日本語/英語言語データを同梱
- `PDFWorkshop-Windows-Portable.zip` をArtifactとして作成

## 注意

まだMVPです。見開き境界の高度な自動検出、白紙判定、完全なUndo/Redo、クラッシュ復旧、正式インストーラーは今後強化します。

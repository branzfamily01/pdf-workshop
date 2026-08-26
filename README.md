# PDF Workshop

教材PDFをローカルで整理・復元する Windows 向けデスクトップアプリです。

## まず使いたい方へ

**Pythonを自分でインストールする必要はありません。**

GitHub Actionsで作成される `PDFWorkshop-Windows-Portable.zip` を使います。

1. ZIPをダウンロード
2. ZIPを「すべて展開」
3. 中の `PDFWorkshop.exe` をダブルクリック
4. PDFを画面へドラッグ
5. 分からないときは画面上部の **「？ 使い方」** を押す

OCR用のTesseractと日本語データも配布フォルダへ同梱する構成です。

## 主な機能

- PDF/複数PDF読込、ドラッグ&ドロップ
- ページプレビュー
- 回転、除外/復元、並べ替え
- Undo / Redo
- A3等の見開き左右分割
- 冊子面付け順 → 通常ページ順
- 上下左右クロップ（mm）
- プロジェクト保存/読込（`.pdfwork`）
- PDF書き出し
- OCRmyPDF + Tesseractによる日本語/英語OCR
- 基本診断（ページ数、横向き、A3相当、OCRなし、見開き候補）
- HTMLマニュアル（`manual.html`）

## 使い方

`manual.html` をブラウザで開くか、アプリ内の **「？ 使い方」** を押してください。

## ローカル処理

PDFは基本的にPC内で処理します。WebサービスへPDF本文をアップロードする方式ではありません。

## 開発者向け

ソースから実行する場合のみPython 3.12以上を使用します。通常利用者はこの手順を行いません。

```text
setup_windows.bat
run_windows.bat
```

## Windows配布版

`.github/workflows/build-windows.yml` がWindows上で自動的に以下を行います。

- ビルド専用Python環境を準備
- コアテスト実行
- PyInstallerで `PDFWorkshop.exe` を生成
- Tesseractと日本語OCRデータを同梱
- `manual.html` とライセンス表記を同梱
- `PDFWorkshop-Windows-Portable.zip` をArtifactとして生成

## GitHub

正本: https://github.com/branzfamily01/pdf-workshop

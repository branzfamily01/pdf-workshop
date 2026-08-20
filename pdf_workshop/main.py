from __future__ import annotations
import sys
from pathlib import Path
from copy import deepcopy

try:
    from PySide6.QtCore import Qt, QSize, QThread, Signal, QObject
    from PySide6.QtGui import QAction, QPixmap, QImage
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
        QPushButton, QFileDialog, QListWidget, QListWidgetItem, QMessageBox,
        QSplitter, QInputDialog, QProgressDialog, QDialog, QFormLayout,
        QDoubleSpinBox, QDialogButtonBox, QComboBox
    )
except ImportError as e:
    raise SystemExit("PySide6 が必要です。setup_windows.bat を実行してください。") from e

import pypdfium2 as pdfium
from .model import Project, Crop, Page
from .pdf_engine import import_pdf, diagnose, export_project
from .booklet import deimpose
from .ocr_runner import availability as ocr_availability, run_ocr


class OCRWorker(QObject):
    finished = Signal(bool, str)
    def __init__(self, input_pdf: str, output_pdf: str):
        super().__init__(); self.input_pdf=input_pdf; self.output_pdf=output_pdf
    def run(self):
        try:
            p = run_ocr(self.input_pdf, self.output_pdf)
            if p.returncode == 0:
                self.finished.emit(True, self.output_pdf)
            else:
                self.finished.emit(False, (p.stderr or p.stdout)[-3000:])
        except Exception as e:
            self.finished.emit(False, str(e))


class CropDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent); self.setWindowTitle("クロップ (mm)")
        form=QFormLayout(self); self.fields={}
        for key,label in [("top_mm","上"),("bottom_mm","下"),("left_mm","左"),("right_mm","右")]:
            s=QDoubleSpinBox(); s.setRange(0,100); s.setDecimals(1); s.setSuffix(" mm")
            self.fields[key]=s; form.addRow(label,s)
        buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); form.addRow(buttons)
    def crop(self): return Crop(**{k:v.value() for k,v in self.fields.items()})


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("PDF Workshop MVP"); self.resize(1200,800)
        self.setAcceptDrops(True); self.project=Project(); self.project_path=None
        self._build_ui(); self._build_menu()

    def _build_ui(self):
        root=QWidget(); outer=QVBoxLayout(root)
        header=QHBoxLayout(); self.summary=QLabel("PDFをここへドロップ、または『PDF追加』")
        add=QPushButton("PDF追加"); add.clicked.connect(self.add_files)
        diag=QPushButton("PDF診断"); diag.clicked.connect(self.show_diagnosis)
        export=QPushButton("PDFを書き出す"); export.clicked.connect(self.export_pdf)
        for w in [self.summary, add, diag, export]: header.addWidget(w)
        outer.addLayout(header)
        split=QSplitter(); self.list=QListWidget(); self.list.setSelectionMode(QListWidget.ExtendedSelection)
        self.list.setDragDropMode(QListWidget.InternalMove); self.list.model().rowsMoved.connect(self.sync_order_from_list)
        self.preview=QLabel("ページを選択"); self.preview.setAlignment(Qt.AlignCenter); self.preview.setMinimumWidth(500)
        self.list.currentRowChanged.connect(self.render_preview)
        actions=QWidget(); al=QVBoxLayout(actions)
        for text,fn in [("左90°",lambda:self.rotate_selected(270)),("右90°",lambda:self.rotate_selected(90)),("除外/復元",self.toggle_excluded),("クロップ",self.crop_selected),("見開き左右分割",self.split_selected),("冊子順→通常順",self.deimpose_pages),("OCR",self.ocr_current_project)]:
            b=QPushButton(text); b.clicked.connect(fn); al.addWidget(b)
        al.addStretch()
        split.addWidget(self.list); split.addWidget(self.preview); split.addWidget(actions); split.setStretchFactor(1,1)
        outer.addWidget(split); self.setCentralWidget(root)

    def _build_menu(self):
        m=self.menuBar().addMenu("ファイル")
        for text,fn in [("PDF追加",self.add_files),("プロジェクト保存",self.save_project),("プロジェクトを開く",self.load_project),("PDF書き出し",self.export_pdf)]:
            a=QAction(text,self); a.triggered.connect(fn); m.addAction(a)

    def dragEnterEvent(self,e):
        if e.mimeData().hasUrls(): e.acceptProposedAction()
    def dropEvent(self,e):
        paths=[u.toLocalFile() for u in e.mimeData().urls() if u.toLocalFile().lower().endswith('.pdf')]
        self.import_paths(paths)

    def add_files(self):
        paths,_=QFileDialog.getOpenFileNames(self,"PDFを追加",filter="PDF (*.pdf)"); self.import_paths(paths)
    def import_paths(self,paths):
        try:
            for p in paths: import_pdf(self.project,p)
            self.refresh_list(); self.show_diagnosis()
        except Exception as e: QMessageBox.critical(self,"読み込みエラー",str(e))

    def refresh_list(self):
        self.list.clear()
        for i,p in enumerate(self.project.pages):
            src=self.project.source_by_id(p.source_document_id)
            label=f"{i+1:03d}  {Path(src.path).name} / {p.source_page_index+1}"
            if p.region!="FULL": label+=f" [{p.region}]"
            if p.rotation: label+=f" ↻{p.rotation}°"
            if p.excluded: label+="  [除外]"
            it=QListWidgetItem(label); it.setData(Qt.UserRole,p.id); self.list.addItem(it)
        self.summary.setText(f"{len(self.project.pages)}ページ / {len(self.project.sources)} PDF")

    def selected_page_ids(self): return [x.data(Qt.UserRole) for x in self.list.selectedItems()]
    def selected_pages(self):
        ids=set(self.selected_page_ids()); return [p for p in self.project.pages if p.id in ids]

    def sync_order_from_list(self,*_):
        ids=[self.list.item(i).data(Qt.UserRole) for i in range(self.list.count())]
        by={p.id:p for p in self.project.pages}; self.project.pages=[by[i] for i in ids]

    def render_preview(self,row):
        if row<0 or row>=len(self.project.pages): return
        p=self.project.pages[row]; src=self.project.source_by_id(p.source_document_id)
        try:
            doc=pdfium.PdfDocument(src.path); page=doc[p.source_page_index]; bmp=page.render(scale=1.2); pil=bmp.to_pil()
            if p.region in ('LEFT','RIGHT'):
                mid=int(pil.width*p.split_ratio); pil=pil.crop((0,0,mid,pil.height) if p.region=='LEFT' else (mid,0,pil.width,pil.height))
            c=p.crop; px_per_mm=pil.width / (float(page.get_size()[0])*25.4/72.0)
            box=(int(c.left_mm*px_per_mm),int(c.top_mm*px_per_mm),pil.width-int(c.right_mm*px_per_mm),pil.height-int(c.bottom_mm*px_per_mm))
            if box[2]>box[0] and box[3]>box[1]: pil=pil.crop(box)
            if p.rotation: pil=pil.rotate(-p.rotation,expand=True)
            pil.thumbnail((760,680)); raw=pil.convert('RGB').tobytes('raw','RGB'); q=QImage(raw,pil.width,pil.height,pil.width*3,QImage.Format_RGB888).copy(); self.preview.setPixmap(QPixmap.fromImage(q))
        except Exception as e: self.preview.setText(str(e))

    def rotate_selected(self,deg):
        for p in self.selected_pages(): p.rotation=(p.rotation+deg)%360
        self.refresh_list()
    def toggle_excluded(self):
        for p in self.selected_pages(): p.excluded=not p.excluded
        self.refresh_list()
    def crop_selected(self):
        pages=self.selected_pages()
        if not pages: return
        d=CropDialog(self)
        if d.exec():
            c=d.crop()
            for p in pages: p.crop=deepcopy(c)
            self.refresh_list(); self.render_preview(self.list.currentRow())
    def split_selected(self):
        ids=set(self.selected_page_ids())
        if not ids: return
        direction=QMessageBox.question(self,"読み順","左→右で分割しますか？\n「いいえ」で右→左",QMessageBox.Yes|QMessageBox.No|QMessageBox.Cancel)
        if direction==QMessageBox.Cancel:return
        new=[]
        for p in self.project.pages:
            if p.id not in ids: new.append(p); continue
            a,b=deepcopy(p),deepcopy(p); from uuid import uuid4; a.id=str(uuid4()); b.id=str(uuid4()); a.region='LEFT'; b.region='RIGHT'
            new.extend([a,b] if direction==QMessageBox.Yes else [b,a])
        self.project.pages=new; self.refresh_list()
    def deimpose_pages(self):
        pages=[p for p in self.project.pages if not p.excluded]
        if not pages or len(pages)%4:
            QMessageBox.warning(self,"冊子解除","対象ページ数は4の倍数にしてください。"); return
        try:
            logical=deimpose(pages); excluded=[p for p in self.project.pages if p.excluded]; self.project.pages=logical+excluded; self.refresh_list()
        except Exception as e: QMessageBox.critical(self,"冊子解除",str(e))

    def show_diagnosis(self):
        if not self.project.pages:return
        try:
            s=diagnose(self.project)
            text=(f"総ページ: {s['pages']}\n横向き: {s['landscape']}\nA3相当: {s['a3_like']}\n"
                  f"OCR/文字情報なし: {s['no_text']}\n見開き候補: {s['spread_candidates']}")
            if s['spread_candidates'] and s['no_text']:
                text += "\n\nおすすめ: 見開き分割 → 冊子順確認 → クロップ → OCR"
            QMessageBox.information(self,"PDF診断",text)
        except Exception as e: QMessageBox.critical(self,"診断エラー",str(e))

    def save_project(self):
        path=self.project_path
        if not path: path,_=QFileDialog.getSaveFileName(self,"プロジェクト保存",self.project.title+".pdfwork","PDF Workshop (*.pdfwork)")
        if path:
            self.project.save(path); self.project_path=path
    def load_project(self):
        path,_=QFileDialog.getOpenFileName(self,"プロジェクトを開く",filter="PDF Workshop (*.pdfwork)")
        if path:
            try: self.project=Project.load(path); self.project_path=path; self.refresh_list()
            except Exception as e: QMessageBox.critical(self,"読込エラー",str(e))
    def export_pdf(self):
        if not self.project.pages:return
        path,_=QFileDialog.getSaveFileName(self,"PDFを書き出す",self.project.title+"_整理済み.pdf","PDF (*.pdf)")
        if path:
            try: export_project(self.project,path); QMessageBox.information(self,"完了",f"PDFを書き出しました。\n{path}")
            except Exception as e: QMessageBox.critical(self,"出力エラー",str(e))

    def ocr_current_project(self):
        ok,msg=ocr_availability()
        if not ok: QMessageBox.warning(self,"OCR",msg); return
        tmp=str(Path.home()/"PDFWorkshop-ocr-input.pdf")
        out,_=QFileDialog.getSaveFileName(self,"OCR済みPDF保存",self.project.title+"_OCR.pdf","PDF (*.pdf)")
        if not out:return
        try: export_project(self.project,tmp)
        except Exception as e: QMessageBox.critical(self,"OCR準備エラー",str(e)); return
        self.progress=QProgressDialog("OCR処理中…（ページ単位進捗は次版で強化）","閉じる",0,0,self); self.progress.setWindowModality(Qt.NonModal); self.progress.show()
        self.thread=QThread(); self.worker=OCRWorker(tmp,out); self.worker.moveToThread(self.thread); self.thread.started.connect(self.worker.run); self.worker.finished.connect(self.ocr_done); self.worker.finished.connect(self.thread.quit); self.thread.start()
    def ocr_done(self,ok,msg):
        self.progress.close()
        if ok: QMessageBox.information(self,"OCR完了",f"検索可能PDFを作成しました。\n{msg}")
        else: QMessageBox.critical(self,"OCR失敗",msg)


def main():
    app=QApplication(sys.argv); w=MainWindow(); w.show(); return app.exec()

if __name__=="__main__": raise SystemExit(main())

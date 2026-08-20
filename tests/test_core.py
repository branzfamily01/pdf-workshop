import tempfile
from pathlib import Path
import unittest
from pypdf import PdfWriter, PdfReader
from pdf_workshop.booklet import imposed_page_numbers, deimpose
from pdf_workshop.model import Project, Crop
from pdf_workshop.pdf_engine import import_pdf, export_project


class CoreTests(unittest.TestCase):
    def test_booklet_8(self):
        self.assertEqual(imposed_page_numbers(8), [8,1,2,7,6,3,4,5])
        self.assertEqual(deimpose([8,1,2,7,6,3,4,5]), list(range(1,9)))

    def test_booklet_sizes(self):
        for n in [4,8,12,16,20,24,32,64]:
            physical=imposed_page_numbers(n)
            self.assertEqual(deimpose(physical), list(range(1,n+1)))

    def test_project_roundtrip_and_export_split(self):
        with tempfile.TemporaryDirectory() as td:
            src=Path(td)/"a3.pdf"; out=Path(td)/"out.pdf"; prjfile=Path(td)/"x.pdfwork"
            w=PdfWriter(); w.add_blank_page(width=1190.55,height=841.89)
            with src.open('wb') as f:w.write(f)
            p=Project(); import_pdf(p,str(src)); original=p.pages[0]
            import copy
            left,right=copy.deepcopy(original),copy.deepcopy(original)
            left.id='L'; right.id='R'; left.region='LEFT'; right.region='RIGHT'; left.crop=Crop(top_mm=5); right.crop=Crop(bottom_mm=5)
            p.pages=[left,right]; p.save(str(prjfile)); p2=Project.load(str(prjfile)); export_project(p2,str(out))
            r=PdfReader(str(out)); self.assertEqual(len(r.pages),2)
            self.assertLess(float(r.pages[0].mediabox.width), 700)

if __name__ == '__main__': unittest.main()

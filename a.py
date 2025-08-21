# -*- coding: utf-8 -*-
"""
Single-file PySide6 app that MERGES code1 (PDF→Text→Fields→QR/Code128→Embed) into code2 GUI.
- Removes QProcess / mainqr.py indirection
- Runs pipeline directly on a Worker(QThread) to keep UI responsive
- Keeps original UI assumptions: widgets.lineEdit_2 (input PDF), widgets.lineEdit_3 (output dir)

Dependencies: PySide6, PyMuPDF (fitz), pdfminer.six, pdf2image, pytesseract, qrcode[pil],
python-barcode[images], Pillow
"""

from __future__ import annotations

import sys, os, re, unicodedata
from pathlib import Path
from typing import Optional, List
import sys
import os
import platform
from pathlib import Path

# IMPORT / GUI AND MODULES AND WIDGETS
# ///////////////////////////////////////////////////////////////
from modules import *
from widgets import *
# ====== GUI Imports (assumes your project modules/widgets stay the same) ======
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox, QHeaderView
)
from PySide6.QtGui import QIcon

# If you have the same helpers as original code2
try:
    from modules import *  # noqa
    from widgets import *  # noqa
    from modules.ui_functions import UIFunctions  # noqa
    from modules.app_functions import AppFunctions  # noqa
    from modules.app_settings import Settings  # noqa
except Exception:
    # Minimal fallbacks so this file can run standalone for testing without theme
    class Settings:
        ENABLE_CUSTOM_TITLE_BAR = False
    class UIFunctions:
        @staticmethod
        def theme(*args, **kwargs):
            pass
        @staticmethod
        def resize_grips(*args, **kwargs):
            pass
    class AppFunctions:
        @staticmethod
        def setThemeHack(*args, **kwargs):
            pass
    class Ui_MainWindow:
        def setupUi(self, win):
            from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLineEdit, QLabel, QTableWidget
            win.resize(800, 480)
            cw = QWidget(); win.setCentralWidget(cw)
            lay = QVBoxLayout(cw)
            self.titleRightInfo = QLabel("KINGDOM FLOW CONTROL")
            lay.addWidget(self.titleRightInfo)
            self.lineEdit_2 = QLineEdit(); self.lineEdit_2.setPlaceholderText("Chọn PDF đầu vào...")
            self.lineEdit_3 = QLineEdit(); self.lineEdit_3.setPlaceholderText("Chọn thư mục lưu PDF (sẽ tạo qrpdf.pdf)")
            lay.addWidget(self.lineEdit_2); lay.addWidget(self.lineEdit_3)
            self.pushButton_2 = QPushButton("Chọn PDF")
            self.pushButton_3 = QPushButton("Chọn thư mục & Chạy")
            lay.addWidget(self.pushButton_2); lay.addWidget(self.pushButton_3)
            self.tableWidget = QTableWidget(0, 3); lay.addWidget(self.tableWidget)
            self.stackedWidget = QWidget(); lay.addWidget(self.stackedWidget)

# ====== Third-party libs for pipeline ======
import fitz  # PyMuPDF
from pdfminer.high_level import extract_pages
from pdfminer.layout import LAParams, LTTextContainer, LTTextLine
from pdf2image import convert_from_path
import pytesseract
import qrcode
from qrcode.constants import ERROR_CORRECT_Q
import qrcode.image.svg as qrcode_svg
from barcode import Code128
from barcode.writer import ImageWriter
from PIL import Image

# =========================
# 1) TEXT EXTRACTION (from code1)
# =========================

def extract_pdfminer_topdown_ltr(pdf_path: str, page_index: Optional[int] = None) -> str:
    """pdfminer → sort lines top→down (−y1) then left→right (x0)."""
    laparams = LAParams(char_margin=2.0, line_margin=0.5, word_margin=0.1, boxes_flow=0.5)
    page_numbers = [page_index] if page_index is not None else None
    pages_text: List[str] = []
    for page_layout in extract_pages(pdf_path, page_numbers=page_numbers, laparams=laparams):
        lines = []
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                for text_line in element:
                    if isinstance(text_line, LTTextLine):
                        x0, y0, x1, y1 = text_line.bbox
                        s = text_line.get_text().strip()
                        if s:
                            lines.append((-y1, x0, s))
        lines.sort(key=lambda t: (t[0], t[1]))
        page_text = "\n".join(t[2] for t in lines)
        pages_text.append(page_text)
    return "\n\f\n".join(pages_text)


def extract_pymupdf_sorted(pdf_path: str, page_index: Optional[int] = None) -> str:
    try:
        txt_parts: List[str] = []
        with fitz.open(pdf_path) as doc:
            if doc.is_encrypted:
                try:
                    doc.authenticate("")
                except Exception:
                    return ""
            if page_index is None:
                for page in doc:
                    txt_parts.append(page.get_text("text", sort=True))
            else:
                page = doc[page_index]
                txt_parts.append(page.get_text("text", sort=True))
        return "\n".join(txt_parts)
    except Exception:
        return ""


def extract_ocr(pdf_path: str, lang: str = "vie+eng", dpi: int = 300, page_index: Optional[int] = None) -> str:
    kwargs = {"dpi": dpi}
    if page_index is not None:
        kwargs.update({"first_page": page_index + 1, "last_page": page_index + 1})
    images = convert_from_path(pdf_path, **kwargs)
    texts = []
    for img in images:
        t = pytesseract.image_to_string(img, lang=lang, config="--oem 1 --psm 6")
        texts.append(t.strip())
    return "\n".join(texts)


def pdf_to_txt(pdf_path: str, out_txt: Optional[str] = None, page_index: Optional[int] = None) -> str:
    pdf = Path(pdf_path)
    if not pdf.exists():
        raise FileNotFoundError(pdf)
    txt = extract_pdfminer_topdown_ltr(str(pdf), page_index=page_index)
    if len(txt.strip()) < 10:
        txt = extract_pymupdf_sorted(str(pdf), page_index=page_index)
    if len(txt.strip()) < 10:
        txt = extract_ocr(str(pdf), page_index=page_index)
    if out_txt:
        Path(out_txt).parent.mkdir(parents=True, exist_ok=True)
        Path(out_txt).write_text(txt, encoding="utf-8")
    return txt

# ======================
# 2) FIELD EXTRACTION (from code1)
# ======================

def read_lines(path: Path) -> List[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return [ln.rstrip("\r\n") for ln in text.splitlines()]


def next_non_empty(lines: List[str], start_idx: int) -> Optional[str]:
    for i in range(start_idx + 1, len(lines)):
        s = lines[i].strip()
        if s:
            return s
    return None


def find_value_after_label(lines: List[str], label: str) -> Optional[str]:
    for i, line in enumerate(lines):
        if line.strip() == label.strip():
            return next_non_empty(lines, i)
    return None


def find_nps_line(lines: List[str]) -> Optional[str]:
    for line in lines:
        if "NPS" in line:
            m = re.search(r"(NPS.*)", line)
            if not m:
                continue
            chunk = m.group(1).strip()
            close_idx = chunk.rfind(")")
            if close_idx != -1:
                return chunk[: close_idx + 1]
            return chunk
    return None


def strip_accents(s: str) -> str:
    if not s:
        return ""
    s_norm = unicodedata.normalize("NFKD", s)
    return s_norm.encode("ascii", "ignore").decode("ascii")


def extract_fields_to_qr_text(input_txt: Path, output_qr_txt: Path) -> None:
    if not input_txt.exists():
        raise FileNotFoundError(f"Không thấy file: {input_txt}")

    lines = read_lines(input_txt)

    ms_don        = find_value_after_label(lines, "MS đơn công lệnh:")
    so_luong      = find_value_after_label(lines, "Số lượng sản xuất:")
    ngay_hoan_tat = find_value_after_label(lines, "Ngày Hoàn tất:")
    nps_fallback  = find_nps_line(lines)

    def _norm_cmp(s: str) -> str:
        s = strip_accents(s or "")
        s = re.sub(r"\s+", " ", s).strip().lower()
        return s

    STOP_LABELS = [
        "Số lượng sản xuất:", "Số lượng:", "Ngày phát thực tế:", "Mã đơn đặt hàng:",
        "Đơn đặt hàng", "Ghi chú:", "Hạng mục", "Ngày bắt đầu theo dự tính:",
        "Ngày Hoàn tất:", "Ngày có hiệu lực BOM:", "NVL sản xuất:"
    ]

    def find_fnw_nps_block_after_nvl(lines):
        idx = None
        for i, l in enumerate(lines):
            if _norm_cmp(l).startswith(_norm_cmp("NVL sản xuất:")):
                idx = i
                break
        if idx is None:
            return None
        j = idx + 1
        if j < len(lines) and re.search(r"\bM\b", lines[j]):
            j += 1
        got_fnw = False; got_nps = False; pieces = []
        nps_re = re.compile(r"\bNPS\s*\d", re.IGNORECASE)
        while j < len(lines):
            raw = lines[j]; s = raw.strip()
            if not s:
                break
            if any(_norm_cmp(s).startswith(_norm_cmp(lbl)) for lbl in STOP_LABELS):
                break
            if (not got_fnw) and ("FNW" in s):
                pieces.append(s); got_fnw = True
            elif (not got_nps) and nps_re.search(s):
                pieces.append(s); got_nps = True
            if got_fnw and got_nps:
                break
            j += 1
        if not pieces:
            return None
        merged = " ".join(pieces)
        last_paren = merged.rfind(")")
        if last_paren != -1:
            merged = merged[: last_paren + 1]
        return merged

    raw_desc = find_fnw_nps_block_after_nvl(lines) or nps_fallback

    def norm(s: Optional[str]) -> str:
        s = strip_accents(s or "")
        s = re.sub(r"\s+", " ", s).strip()
        return s

    ms   = norm(ms_don)
    desc = norm(raw_desc)
    sl   = norm(so_luong)
    ngay = norm(ngay_hoan_tat)

    ddh_line = next((l for l in lines if l.strip().startswith("SV")), None)
    ddh = norm(ddh_line)

    parts = []
    if ms:   parts.append(f"MS:{ms}")
    if desc: parts.append(f"con hang:{desc}")
    if sl:   parts.append(f"sl:{sl}")
    if ngay: parts.append(f"Ngay Hoan tat:{ngay}")
    if ddh:  parts.append(f"Don dat hang:{ddh}")

    payload = ";".join(parts)
    output_qr_txt.parent.mkdir(parents=True, exist_ok=True)
    output_qr_txt.write_text(payload + "\n", encoding="utf-8")

# ============================
# 3) QR + CODE128 (from code1)
# ============================

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace").strip()


def make_qr(data: str, out_png: Path, out_svg: Path) -> None:
    qr = qrcode.QRCode(version=None, error_correction=ERROR_CORRECT_Q, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    out_png.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_png)
    img_svg = qrcode.make(data, image_factory=qrcode_svg.SvgImage)
    img_svg.save(out_svg)


def to_ascii_one_line(s: str, sep: str = " | ") -> str:
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    lines = [ln.strip() for ln in s.splitlines() if ln.strip()]
    lines = [re.sub(r"\s+", " ", ln) for ln in lines]
    return sep.join(lines)


def split_for_1d(payload: str, maxlen: int = 80, sep: str = " | ") -> List[str]:
    if len(payload) <= maxlen:
        return [payload]
    parts: List[str] = []
    current = ""
    tokens = payload.split(sep)
    for tk in tokens:
        candidate = (current + sep + tk) if current else tk
        if len(candidate) <= maxlen:
            current = candidate
        else:
            if current:
                parts.append(current); current = tk
            else:
                parts.append(tk[:maxlen]); current = tk[maxlen:]
    if current:
        parts.append(current)
    return parts


def make_code128(payload: str, out_base: Path, maxlen: int = 80) -> None:
    chunks = split_for_1d(payload, maxlen=maxlen)
    out_base.parent.mkdir(parents=True, exist_ok=True)
    if len(chunks) == 1:
        code = Code128(chunks[0], writer=ImageWriter())
        code.save(str(out_base), options={
            "module_width": 0.3,
            "module_height": 30.0,
            "quiet_zone": 6.5,
            "font_size": 10,
            "text_distance": 2.0,
            "write_text": False,
        })
    else:
        for idx, chunk in enumerate(chunks, 1):
            code = Code128(chunk, writer=ImageWriter())
            code.save(str(out_base.with_name(out_base.stem + f"_part{idx}")), options={
                "module_width": 0.3,
                "module_height": 30.0,
                "quiet_zone": 6.5,
                "font_size": 10,
                "text_distance": 2.0,
                "write_text": False,
            })

# ======================
# 4) EMBED QR INTO PDF (from code1)
# ======================

def embed_qr_into_pdf(pdf_path: Path, qr_png: Path, output_pdf: Path, page_index: int = 0, width_fraction: float = 4.0) -> None:
    doc = fitz.open(str(pdf_path))
    try:
        page = doc[page_index]
        page_rect = page.rect
        page_width, page_height = page_rect.width, page_rect.height
        img = Image.open(qr_png)
        qr_w_px, qr_h_px = img.size
        scale = page_width / (width_fraction * qr_w_px)
        qr_w = qr_w_px * scale
        qr_h = qr_h_px * scale
        x0 = (page_width - qr_w) / 2
        y0 = (page_height - qr_h) / 2
        rect = fitz.Rect(x0, y0, x0 + qr_w, y0 + qr_h)
        page.insert_image(rect, filename=str(qr_png))
        output_pdf.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(output_pdf))
    finally:
        doc.close()

# ======================
# Worker thread to run pipeline without freezing UI
# ======================
class PipelineWorker(QThread):
    log = Signal(str)
    done = Signal(bool, str)  # success, result_pdf_path

    def __init__(self, base_path: Path, pdf_path: Path, outpdf_dir: Path, page:int=0, qr_fraction:float=4.0, max1d:int=80):
        super().__init__()
        self.base_path = base_path
        self.pdf_path = pdf_path
        self.outpdf_dir = outpdf_dir
        self.page = page
        self.qr_fraction = qr_fraction
        self.max1d = max1d

    def _print(self, s: str):
        self.log.emit(s + "\n")

    def run(self):
        try:
            outdir = self.base_path / "scan" / "output"
            outdir.mkdir(parents=True, exist_ok=True)
            self.outpdf_dir.mkdir(parents=True, exist_ok=True)

            txt_out = outdir / "a.txt"
            qr_txt  = self.base_path / "scan" / "input" / "a_qr.txt"
            qr_png  = outdir / "a_qr.png"
            qr_svg  = outdir / "a_qr.svg"
            code128_base = outdir / "a_code128"
            in_path = Path(self.pdf_path)
            in_name = in_path.name
            pdf_with_qr = self.outpdf_dir / in_name

            # Nếu output dir trùng với thư mục của file gốc → thêm hậu tố _qr để không ghi đè
            if in_path.parent.resolve() == self.outpdf_dir.resolve():
                pdf_with_qr = self.outpdf_dir / f"{in_path.stem}_qr{in_path.suffix}"

            self._print("[1] Extracting text from PDF…")
            text = extract_pdfminer_topdown_ltr(str(self.pdf_path), page_index=self.page)
            if len(text.strip()) < 10:
                text = extract_pymupdf_sorted(str(self.pdf_path), page_index=self.page)
            if len(text.strip()) < 10:
                self._print("    (Fallback to OCR)")
                text = extract_ocr(str(self.pdf_path), page_index=self.page)
            if len(text.strip()) < 1:
                raise RuntimeError("Không trích xuất được văn bản từ PDF.")
            txt_out.write_text(text, encoding="utf-8")
            self._print(f"    Saved text -> {txt_out}")

            self._print("[2] Parsing fields to QR text…")
            extract_fields_to_qr_text(txt_out, qr_txt)
            self._print(f"    Saved QR payload -> {qr_txt}")

            self._print("[3] Generating QR & Code128…")
            qr_payload = read_text(qr_txt)
            make_qr(qr_payload, qr_png, qr_svg)
            self._print(f"    QR -> {qr_png}, {qr_svg}")
            payload_1d = to_ascii_one_line(qr_payload)
            make_code128(payload_1d, code128_base, maxlen=self.max1d)
            self._print(f"    Code128 -> {outdir} (a_code128*.png)")

            self._print("[4] Embedding QR into PDF…")
            embed_qr_into_pdf(self.pdf_path, qr_png, pdf_with_qr, page_index=self.page, width_fraction=self.qr_fraction)
            self._print(f"    PDF with QR -> {pdf_with_qr}")

            self.done.emit(True, str(pdf_with_qr))
        except Exception as e:
            self._print(f"[ERROR] {e}")
            self.done.emit(False, "")

# ======================
#  MainWindow (merged behavior from code2)
# ======================
widgets = None
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow(); self.ui.setupUi(self)
        global widgets; widgets = self.ui

        Settings.ENABLE_CUSTOM_TITLE_BAR = False
        title = "Ứng dụng thêm mã qr cho file pdf"; description = "KINGDOM FLOW CONTROL"
        # self.setWindowTitle(title); widgets.titleRightInfo.setText(description)

        self.ui.pushButton_2.clicked.connect(self.choose_input_pdf)
        self.ui.pushButton_3.clicked.connect(self.choose_output_dir)
        try:
            widgets.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        except Exception:
            pass

        self.show()

        # Resolve theme path against base_path
        # base_path = self._base_path()
        # # themeFile = os.path.join(base_path, "themes", "py_dracula_light.qss")
        # # if os.path.exists(themeFile):
        # #     UIFunctions.theme(self, themeFile, True)
        # #     # AppFunctions.setThemeHack(self)

    def _base_path(self) -> str:
        if getattr(sys, 'frozen', False):
            return sys._MEIPASS
        return os.path.dirname(__file__)

    def choose_input_pdf(self):
        start_dir = self.ui.lineEdit_2.text().strip() or str(Path.home())
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Chọn file PDF", start_dir, "PDF files (*.pdf);;All files (*.*)"
        )
        if file_path:
            self.ui.lineEdit_2.setText(file_path)

    def choose_output_dir(self):
        project_root = Path(self._base_path()).resolve()
        suggested = self.ui.lineEdit_3.text().strip() or str(project_root / "pdf" / "output")
        dir_path = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu PDF", suggested)
        if not dir_path:
            return
        self.ui.lineEdit_3.setText(dir_path)
        self.run_pipeline()

    def run_pipeline(self):
        pdf_path = self.ui.lineEdit_2.text().strip()
        outpdf_dir = self.ui.lineEdit_3.text().strip()
        if not pdf_path:
            QMessageBox.warning(self, "Thiếu đường dẫn", "Vui lòng chọn file PDF (nút 2).")
            return
        base_path = Path(self._base_path())
        outpdf = Path(outpdf_dir) if outpdf_dir else base_path / "pdf" / "output"
        outpdf.mkdir(parents=True, exist_ok=True)

        # Disable run button while processing
        self.ui.pushButton_3.setEnabled(False)

        # Start worker
        self.worker = PipelineWorker(
            base_path=base_path,
            pdf_path=Path(pdf_path),
            outpdf_dir=outpdf,
            page=0,
            qr_fraction=4.0,
            max1d=80,
        )
        self.worker.log.connect(lambda s: print(s, end=""))
        self.worker.done.connect(self._on_pipeline_done)
        self.worker.start()

    from PySide6.QtWidgets import QMessageBox, QApplication, QStyleFactory
    from PySide6.QtCore import Qt

    def show_native_message(self, title: str, text: str, level: str = "info"):
        msg = QMessageBox(self)
        msg.setWindowModality(Qt.ApplicationModal)
        msg.setIcon(QMessageBox.Information if level == "info" else QMessageBox.Critical)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setStandardButtons(QMessageBox.Ok)

        # Xóa ảnh hưởng theme cũ
        msg.setStyleSheet("")
        msg.setAttribute(Qt.WA_StyledBackground, False)

        # Dùng style trung tính cho RIÊNG dialog (không ảnh hưởng toàn app)
        st = QStyleFactory.create("Fusion")
        if st:
            msg.setStyle(st)

        # Style scoped CHỈ CHO QMessageBox và nút bên trong
        msg.setStyleSheet("""
            QMessageBox { background: #ffffff; }
            QMessageBox QLabel { color: #000000; }
            QMessageBox QPushButton {
                background: #f2f2f2;
                color: #000000;
                border: 1px solid #c8c8c8;
                border-radius: 6px;
                padding: 6px 14px;
                min-width: 72px;
                min-height: 26px;
            }
            QMessageBox QPushButton:hover   { background: #e8e8e8; }
            QMessageBox QPushButton:pressed { background: #dddddd; }
            QMessageBox QPushButton:default { border: 2px solid #3778ff; }
            QMessageBox QPushButton:disabled {
                background: #f2f2f2; color: #888888; border: 1px solid #d0d0d0;
            }
        """)

        # Đặt default button và ép style trực tiếp cho nút OK (thắng mọi QSS ngoài)
        msg.setDefaultButton(QMessageBox.Ok)
        ok_btn = msg.button(QMessageBox.Ok)
        if ok_btn:
            ok_btn.setEnabled(True)
            ok_btn.setStyleSheet(
                "background:#f2f2f2; color:#000; border:1px solid #c8c8c8; "
                "border-radius:4px; padding:4px 8px;"
            )

        # exec tương thích
        (msg.exec if hasattr(msg, "exec") else msg.exec_)()


    def _on_pipeline_done(self, ok: bool, result_pdf: str):
        self.ui.pushButton_3.setEnabled(True)
        if ok and result_pdf:
            self.ui.lineEdit_3.setText(result_pdf)
            self.show_native_message("Hoàn tất", f"Đã tạo: {result_pdf}", level="info")
        else:
            self.show_native_message("Lỗi", "Pipeline thất bại. Xem log console để biết thêm chi tiết.", level="error")
    # Keep original helpers
    def resizeEvent(self, event):
        UIFunctions.resize_grips(self)
        return super().resizeEvent(event)

    def mousePressEvent(self, event):
        self.dragPos = event.globalPos()
        if event.buttons() == Qt.LeftButton:
            print('Mouse click: LEFT CLICK')
        if event.buttons() == Qt.RightButton:
            print('Mouse click: RIGHT CLICK')
        return super().mousePressEvent(event)

# ======================
# Entrypoint
# ======================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        base_path = getattr(sys, 'frozen', False) and sys._MEIPASS or os.path.dirname(__file__)
        icon_path = os.path.join(base_path, "icon.ico")
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
    except Exception:
        pass
    w = MainWindow()

    # Tương thích cả PySide6 mới và cũ
    if hasattr(app, "exec"):
        sys.exit(app.exec())
    else:
        sys.exit(app.exec_())

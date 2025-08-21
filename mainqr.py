from __future__ import annotations
from pathlib import Path
from typing import Optional, List
import argparse
import re
import unicodedata
import sys

# --- PDF text extractors ---
import fitz  # PyMuPDF
from pdfminer.high_level import extract_pages
from pdfminer.layout import LAParams, LTTextContainer, LTTextLine
from pdf2image import convert_from_path
import pytesseract

# --- QR & 1D barcode ---
import qrcode
from qrcode.constants import ERROR_CORRECT_Q
import qrcode.image.svg as qrcode_svg
from barcode import Code128
from barcode.writer import ImageWriter

# --- Images ---
from PIL import Image


# =========================
# 1) TEXT EXTRACTION (code1)
# =========================

def extract_pdfminer_topdown_ltr(pdf_path: str, page_index: Optional[int] = None) -> str:
    """
    Đọc PDF bằng pdfminer, gom từng dòng (LTTextLine) và sort theo:
      -y1 (đỉnh dòng) giảm dần => từ trên xuống
      x0 tăng dần               => từ trái sang phải
    Nếu page_index=None: đọc toàn bộ trang.
    """
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
        lines.sort(key=lambda t: (t[0], t[1]))  # y xuống, x trái→phải
        page_text = "\n".join(t[2] for t in lines)
        pages_text.append(page_text)

    # Ngăn trang bằng form-feed cho an toàn, bạn có thể đổi thành "\n\n"
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
        # pdf2image dùng chỉ số trang bắt đầu từ 1
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

    # 1) Thử pdfminer (top→down, left→right)
    txt = extract_pdfminer_topdown_ltr(str(pdf), page_index=page_index)

    # 2) Nếu kết quả quá ít, thử PyMuPDF (đã sort)
    if len(txt.strip()) < 10:
        txt = extract_pymupdf_sorted(str(pdf), page_index=page_index)

    # 3) Nếu vẫn rỗng, chạy OCR (cho PDF scan)
    if len(txt.strip()) < 10:
        txt = extract_ocr(str(pdf), page_index=page_index)

    if out_txt:
        Path(out_txt).parent.mkdir(parents=True, exist_ok=True)
        Path(out_txt).write_text(txt, encoding="utf-8")
    return txt


# ======================
# 2) FIELD EXTRACTION (code2)
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
    """Bỏ dấu, giữ ASCII"""
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
    nps_fallback  = find_nps_line(lines)  # dự phòng

    # ---- tiện ích so sánh/so khớp không dấu ----
    def _norm_cmp(s: str) -> str:
        s = strip_accents(s or "")
        s = re.sub(r"\s+", " ", s).strip().lower()
        return s

    STOP_LABELS = [
        "Số lượng sản xuất:", "Số lượng:", "Ngày phát thực tế:", "Mã đơn đặt hàng:",
        "Đơn đặt hàng", "Ghi chú:", "Hạng mục", "Ngày bắt đầu theo dự tính:",
        "Ngày Hoàn tất:", "Ngày có hiệu lực BOM:", "NVL sản xuất:"
    ]

    # ---- lấy FNW đầu tiên + NPS đầu tiên sau NVL ----
    def find_fnw_nps_block_after_nvl(lines):
        idx = None
        for i, l in enumerate(lines):
            if _norm_cmp(l).startswith(_norm_cmp("NVL sản xuất:")):
                idx = i
                break
        if idx is None:
            return None

        j = idx + 1
        # bỏ qua dòng mã “…  M” nếu có
        if j < len(lines) and re.search(r"\bM\b", lines[j]):
            j += 1

        got_fnw = False
        got_nps = False
        pieces = []

        nps_re = re.compile(r"\bNPS\s*\d", re.IGNORECASE)

        while j < len(lines):
            raw = lines[j]
            s = raw.strip()
            if not s:
                break
            if any(_norm_cmp(s).startswith(_norm_cmp(lbl)) for lbl in STOP_LABELS):
                break

            # chỉ lấy FNW đầu tiên
            if (not got_fnw) and ("FNW" in s):
                pieces.append(s)
                got_fnw = True
            # chỉ lấy NPS đầu tiên
            elif (not got_nps) and nps_re.search(s):
                pieces.append(s)
                got_nps = True

            # nếu đã có đủ FNW + NPS thì dừng (tránh dính các dòng song ngữ lặp lại)
            if got_fnw and got_nps:
                break

            j += 1

        if not pieces:
            return None

        merged = " ".join(pieces)

        # --- cắt đến dấu ngoặc ')' cuối cùng (bao gồm dấu ')') ---
        last_paren = merged.rfind(")")
        if last_paren != -1:
            merged = merged[: last_paren + 1]

        return merged

    raw_desc = find_fnw_nps_block_after_nvl(lines) or nps_fallback

    # ---- chuẩn hoá: bỏ dấu, nén khoảng trắng ----
    def norm(s: Optional[str]) -> str:
        s = strip_accents(s or "")
        s = re.sub(r"\s+", " ", s).strip()
        return s

    ms   = norm(ms_don)
    desc = norm(raw_desc)          # FNW + NPS (đã cắt tới ')')
    sl   = norm(so_luong)
    ngay = norm(ngay_hoan_tat)

    # ---- mã đơn đặt hàng (SV...) nếu có ----
    ddh_line = next((l for l in lines if l.strip().startswith("SV")), None)
    ddh = norm(ddh_line)

    # ---- ghép payload ----
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
# 3) QR + CODE128 GENERATION (code3)
# ============================

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace").strip()


def make_qr(data: str, out_png: Path, out_svg: Path) -> None:
    # Tạo QR linh hoạt kích thước, EC mức Q (ổn cho in tem)
    qr = qrcode.QRCode(
        version=None,  # auto-size
        error_correction=ERROR_CORRECT_Q,
        box_size=10,
        border=4,      # quiet zone = 4 modules
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    out_png.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_png)

    # SVG vector để in sắc nét
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
                parts.append(current)
                current = tk
            else:
                parts.append(tk[:maxlen])
                current = tk[maxlen:]
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
# 4) EMBED QR INTO PDF (code4)
# ======================

def embed_qr_into_pdf(pdf_path: Path, qr_png: Path, output_pdf: Path, page_index: int = 0, width_fraction: float = 4.0) -> None:
    """Chèn ảnh QR vào giữa trang `page_index`. width_fraction=4.0 -> QR rộng ~1/4 chiều rộng trang."""
    doc = fitz.open(str(pdf_path))
    try:
        page = doc[page_index]
        page_rect = page.rect
        page_width, page_height = page_rect.width, page_rect.height

        # Kích thước ảnh QR
        img = Image.open(qr_png)
        qr_w_px, qr_h_px = img.size

        # Tỉ lệ: chiếm 1/width_fraction chiều rộng trang
        scale = page_width / (width_fraction * qr_w_px)
        qr_w = qr_w_px * scale
        qr_h = qr_h_px * scale

        # Căn giữa
        x0 = (page_width - qr_w) / 2
        y0 = (page_height - qr_h) / 2
        x1 = x0 + qr_w
        y1 = y0 + qr_h
        rect = fitz.Rect(x0, y0, x1, y1)

        page.insert_image(rect, filename=str(qr_png))
        output_pdf.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(output_pdf))
    finally:
        doc.close()


# ======================
# 5) MAIN PIPELINE
# ======================

def main():
    ap = argparse.ArgumentParser(description="PDF→Text→Fields→QR/Code128→Embed QR (all-in-one)")
    ap.add_argument("--pdf", required=True, help="Đường dẫn file PDF đầu vào")
    ap.add_argument("--outdir", default="scan/output", help="Thư mục output")
    ap.add_argument("--outpdf", default="pdf/output", help="Thư mục outputpdf")
    ap.add_argument("--page", type=int, default=0, help="Chỉ số trang để trích/xử lý (0=trang đầu)")
    ap.add_argument("--no-ocr", action="store_true", help="Không dùng OCR (nếu muốn bắt buộc text-based)")
    ap.add_argument("--qr-fraction", type=float, default=4.0, help="QR sẽ rộng ~1/fraction chiều rộng trang (mặc định 4)")
    ap.add_argument("--max1d", type=int, default=80, help="Độ dài tối đa mỗi mã Code128")
    args = ap.parse_args()

    pdf_path = Path(args.pdf)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    outpdf = Path(args.outpdf)
    outpdf.mkdir(parents=True, exist_ok=True)

    # Các đường dẫn trung gian/đầu ra
    txt_out = outdir / "a.txt"
    qr_txt = Path("scan/input/a_qr.txt")  # giữ đúng như cấu trúc trước
    qr_png = outdir / "a_qr.png"
    qr_svg = outdir / "a_qr.svg"
    code128_base = outdir / "a_code128"
    pdf_with_qr = outpdf / "qrpdf.pdf"


    # 1) PDF → TXT
    print("[1] Extracting text from PDF…")
    text = extract_pdfminer_topdown_ltr(str(pdf_path), page_index=args.page)
    if len(text.strip()) < 10:
        text = extract_pymupdf_sorted(str(pdf_path), page_index=args.page)
    if len(text.strip()) < 10 and not args.no_ocr:
        print("    (Fallback to OCR)")
        text = extract_ocr(str(pdf_path), page_index=args.page)
    if len(text.strip()) < 1:
        print("[ERROR] Không trích xuất được văn bản từ PDF.")
        sys.exit(1)
    txt_out.write_text(text, encoding="utf-8")
    print(f"    Saved text -> {txt_out}")

    # 2) Parse fields → a_qr.txt
    print("[2] Parsing fields to QR text…")
    extract_fields_to_qr_text(txt_out, qr_txt)
    print(f"    Saved QR payload -> {qr_txt}")

    # 3) Tạo QR & Code128
    print("[3] Generating QR & Code128…")
    qr_payload = read_text(qr_txt)
    make_qr(qr_payload, qr_png, qr_svg)
    print(f"    QR -> {qr_png}, {qr_svg}")

    payload_1d = to_ascii_one_line(qr_payload)
    make_code128(payload_1d, code128_base, maxlen=args.max1d)
    print(f"    Code128 -> {outdir} (a_code128*.png)")

    # 4) Nhúng QR vào PDF đầu vào → a.pdf
    print("[4] Embedding QR into PDF…")
    embed_qr_into_pdf(pdf_path, qr_png, pdf_with_qr, page_index=args.page, width_fraction=args.qr_fraction)
    print(f"    PDF with QR -> {pdf_with_qr}")

    print("[DONE] Pipeline completed.")


if __name__ == "__main__":
    main()

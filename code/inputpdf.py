from pathlib import Path
from typing import Optional

# --- PDF text extractors ---
import fitz  # PyMuPDF
from pdfminer.high_level import extract_pages
from pdfminer.layout import LAParams, LTTextContainer, LTTextLine
from pdfminer.high_level import extract_text as pdfminer_extract  # (giữ lại nếu bạn muốn so sánh)
from pdf2image import convert_from_path
import pytesseract


# 1) pdfminer.six: sort theo "trên→xuống, trái→phải"
def extract_pdfminer_topdown_ltr(pdf_path: str, page_index: Optional[int] = None) -> str:
    """
    Đọc PDF bằng pdfminer, gom từng dòng (LTTextLine) và sort theo:
      -y1 (đỉnh dòng) giảm dần => từ trên xuống
      x0 tăng dần               => từ trái sang phải
    Nếu page_index=None: đọc toàn bộ trang.
    """
    laparams = LAParams(char_margin=2.0, line_margin=0.5, word_margin=0.1, boxes_flow=0.5)

    page_numbers = [page_index] if page_index is not None else None
    pages_text = []

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


# 2) PyMuPDF: có bật sort (phòng khi pdfminer ra rỗng)
def extract_pymupdf_sorted(pdf_path: str, page_index: Optional[int] = None) -> str:
    try:
        txt_parts = []
        with fitz.open(pdf_path) as doc:
            if doc.is_encrypted:
                try:
                    doc.authenticate("")
                except Exception:
                    return ""
            if page_index is None:
                for page in doc:
                    # sort=True cố gắng theo thứ tự đọc
                    txt_parts.append(page.get_text("text", sort=True))
            else:
                page = doc[page_index]
                txt_parts.append(page.get_text("text", sort=True))
        return "\n".join(txt_parts)
    except Exception:
        return ""


# 3) OCR cho PDF scan ảnh
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
    """
    - page_index=None  => xuất toàn bộ file
    - page_index=0     => chỉ trang 1 (giống ví dụ bạn yêu cầu)
    """
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


if __name__ == "__main__":
    # Ví dụ 1: chỉ trang 1 (giống output mình đã show)
    src = "../data/input/a.pdf"
    dst = "../data/output/a.txt"
    pdf_to_txt(src, dst, page_index=0)
    print(f"Saved to: {dst}")

    # Ví dụ 2: xuất toàn bộ tài liệu theo top→down, left→right
    # dst_all = "output/a_all_topdown.txt"
    # pdf_to_txt(src, dst_all, page_index=None)
    # print(f"Saved to: {dst_all}")

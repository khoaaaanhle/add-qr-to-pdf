from pathlib import Path
import argparse
import unicodedata
import re

# QR
import qrcode
from qrcode.constants import ERROR_CORRECT_Q
import qrcode.image.svg as qrcode_svg

# Code 128 (1D)
from barcode import Code128
from barcode.writer import ImageWriter


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace").strip()


# ---------- QR (2D, UTF-8, giữ xuống dòng) ----------
def make_qr(data: str, out_png: Path, out_svg: Path) -> None:
    # Tạo QR linh hoạt kích thước, EC mức Q (ổn cho in tem)
    qr = qrcode.QRCode(
        version=None,  # auto-size
        error_correction=ERROR_CORRECT_Q,
        box_size=10,
        border=4,      # quiet zone = 4 modules (khuyến nghị)
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    out_png.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_png)

    # SVG vector để in sắc nét
    img_svg = qrcode.make(data, image_factory=qrcode_svg.SvgImage)
    img_svg.save(out_svg)


# ---------- Code 128 (1D, ASCII) ----------
def to_ascii_one_line(s: str, sep: str = " | ") -> str:
    # Bỏ dấu/kiểu UTF-8: NFKD rồi loại non-ASCII
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    # Ghép các dòng không rỗng thành 1 dòng với phân cách
    lines = [ln.strip() for ln in s.splitlines() if ln.strip()]
    # Nén khoảng trắng
    lines = [re.sub(r"\s+", " ", ln) for ln in lines]
    return sep.join(lines)


def split_for_1d(payload: str, maxlen: int = 80, sep: str = " | "):
    """Tách payload dài thành nhiều đoạn <= maxlen, ưu tiên tách theo sep."""
    if len(payload) <= maxlen:
        return [payload]
    parts, current = [], ""
    tokens = payload.split(sep)
    for i, tk in enumerate(tokens):
        candidate = (current + sep + tk) if current else tk
        if len(candidate) <= maxlen:
            current = candidate
        else:
            if current:
                parts.append(current)
                current = tk
            else:
                # token quá dài -> cắt cứng
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
            "module_width": 0.3,   # ~0.3mm cho vạch nhỏ
            "module_height": 30.0, # chiều cao vạch
            "quiet_zone": 6.5,     # lề trắng
            "font_size": 10,
            "text_distance": 2.0,
            "write_text": False,   # payload dài -> tắt chữ bên dưới
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


def main():
    ap = argparse.ArgumentParser(description="Make QR (2D) and Code128 (1D) from text file.")
    ap.add_argument("--in", dest="inp", default="scan/input/a_qr.txt", help="Input .txt path (UTF-8)")
    ap.add_argument("--outdir", dest="outdir", default="scan/output", help="Output directory")
    ap.add_argument("--no-qr", dest="no_qr", action="store_true", help="Disable QR generation")
    ap.add_argument("--no-1d", dest="no_1d", action="store_true", help="Disable Code128 generation")
    ap.add_argument("--max1d", dest="max1d", type=int, default=80, help="Max length per Code128 barcode")
    args = ap.parse_args()

    inp = Path(args.inp)
    outdir = Path(args.outdir)
    text = read_text(inp)

    if not args.no_qr:
        make_qr(
            data=text,
            out_png=outdir / "a_qr.png",
            out_svg=outdir / "a_qr.svg",
        )
        print(f"[OK] QR saved -> {outdir/'a_qr.png'}, {outdir/'a_qr.svg'}")

    if not args.no_1d:
        payload_1d = to_ascii_one_line(text)  # bỏ dấu & ghép 1 dòng
        make_code128(payload_1d, outdir / "a_code128", maxlen=args.max1d)
        print(f"[OK] Code128 saved -> {outdir} (a_code128*.png)")


if __name__ == "__main__":
    main()

# extract_fields.py
from pathlib import Path
import re
import unicodedata
from typing import Optional, List


INPUT_TXT = Path("../data/output/a.txt")
OUTPUT_TXT = Path("../scan/input/a_qr.txt")


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


def main():
    if not INPUT_TXT.exists():
        raise FileNotFoundError(f"Không thấy file: {INPUT_TXT}")

    lines = read_lines(INPUT_TXT)

    ms_don = find_value_after_label(lines, "MS đơn công lệnh:")
    so_luong = find_value_after_label(lines, "Số lượng sản xuất:")
    ngay_hoan_tat = find_value_after_label(lines, "Ngày Hoàn tất:")
    nps_line = find_nps_line(lines)

    # Ghép đúng định dạng bạn yêu cầu, nhưng bỏ dấu ở giá trị
    out_parts = []
    out_parts.append("MS don cong lenh:")
    out_parts.append(strip_accents(ms_don) or "")
    if nps_line:
        out_parts.append(strip_accents(nps_line))
    out_parts.append("So luong san xuat:")
    out_parts.append(strip_accents(so_luong) or "")
    out_parts.append("Ngay Hoan tat:")
    out_parts.append(strip_accents(ngay_hoan_tat) or "")

    OUTPUT_TXT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_TXT.write_text("\n".join(out_parts) + "\n", encoding="utf-8")
    print(f"Saved to: {OUTPUT_TXT}")


if __name__ == "__main__":
    main()

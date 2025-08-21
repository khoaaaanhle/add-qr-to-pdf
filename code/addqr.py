import fitz  # PyMuPDF
from PIL import Image

# Đường dẫn file gốc và QR
pdf_path = r"C:\Users\khoaa\PycharmProjects\pythorn\pdf_txt\data\input\a.pdf"
qr_path = r"C:\Users\khoaa\PycharmProjects\pythorn\pdf_txt\scan\output\a_qr.png"
output_path = r"C:\Users\khoaa\PycharmProjects\pythorn\pdf_txt\scan\output\a.pdf"


# Mở PDF
doc = fitz.open(pdf_path)
page = doc[0]  # trang đầu tiên

# Lấy kích thước trang
page_rect = page.rect
page_width, page_height = page_rect.width, page_rect.height

# Mở ảnh QR để biết kích thước
img = Image.open(qr_path)
qr_width, qr_height = img.size

# Tỉ lệ resize QR nếu cần (ví dụ chiếm 1/4 chiều rộng trang)
scale = page_width / (4 * qr_width)
qr_width = qr_width * scale
qr_height = qr_height * scale

# Tính tọa độ để căn giữa
x0 = (page_width - qr_width) / 2
y0 = (page_height - qr_height) / 2
x1 = x0 + qr_width
y1 = y0 + qr_height
rect = fitz.Rect(x0, y0, x1, y1)

# Chèn ảnh QR
page.insert_image(rect, filename=qr_path)

# Lưu file mới
doc.save(output_path)
doc.close()

print("Đã thêm QR code vào", output_path)

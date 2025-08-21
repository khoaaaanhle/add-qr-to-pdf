# ///////////////////////////////////////////////////////////////
#
# BY: WANDERSON M.PIMENTA
# PROJECT MADE WITH: Qt Designer and PySide6
# V: 1.0.0
#
# This project can be used freely for all uses, as long as they maintain the
# respective credits only in the Python scripts, any information in the visual
# interface (GUI) can be modified without any implication.
#
# There are limitations on Qt licenses if you want to use your products
# commercially, I recommend reading them on the official website:
# https://doc.qt.io/qtforpython/licenses.html
#
# ///////////////////////////////////////////////////////////////

import sys
import os
import platform
from pathlib import Path

# IMPORT / GUI AND MODULES AND WIDGETS
# ///////////////////////////////////////////////////////////////
from modules import *
from widgets import *
os.environ["QT_FONT_DPI"] = "100" # FIX Problem for High DPI and Scale above 100%

# SET AS GLOBAL WIDGETS
# ///////////////////////////////////////////////////////////////
widgets = None

class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)

        # SET AS GLOBAL WIDGETS
        # ///////////////////////////////////////////////////////////////
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        global widgets
        widgets = self.ui

        # USE CUSTOM TITLE BAR | USE AS "False" FOR MAC OR LINUX
        # ///////////////////////////////////////////////////////////////
        Settings.ENABLE_CUSTOM_TITLE_BAR = False

        # APP NAME
        # ///////////////////////////////////////////////////////////////
        title = "Ứng dụng thêm mã qr cho file pdf"
        description = "KINGDOM FLOW CONTROL"
        # APPLY TEXTS
        self.setWindowTitle(title)
        widgets.titleRightInfo.setText(description)

        self.ui.pushButton_2.clicked.connect(self.choose_input_pdf)  # chọn PDF đầu vào
        self.ui.pushButton_3.clicked.connect(self.choose_output_dir)  # chọn thư mục lưu


        # TOGGLE MENU
        # ///////////////////////////////////////////////////////////////

        # widgets.toggleButton.clicked.connect(lambda: UIFunctions.toggleMenu(self, True))

        # SET UI DEFINITIONS
        # ///////////////////////////////////////////////////////////////
        # UIFunctions.uiDefinitions(self)

        # QTableWidget PARAMETERS
        # ///////////////////////////////////////////////////////////////
        widgets.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # BUTTONS CLICK
        # ///////////////////////////////////////////////////////////////

        # LEFT MENUS
        # widgets.btn_home.clicked.connect(self.buttonClick)


        # EXTRA LEFT BOX
        # def openCloseLeftBox():
        #     UIFunctions.toggleLeftBox(self, True)
        # widgets.toggleLeftBox.clicked.connect(openCloseLeftBox)
        # widgets.extraCloseColumnBtn.clicked.connect(openCloseLeftBox)

        # EXTRA RIGHT BOX
        # def openCloseRightBox():
        #     UIFunctions.toggleRightBox(self, True)
        # widgets.settingsTopBtn.clicked.connect(openCloseRightBox)

        # SHOW APP
        # ///////////////////////////////////////////////////////////////
        self.show()

        # SET CUSTOM THEME
        # ///////////////////////////////////////////////////////////////
        useCustomTheme = True



        themeFile = "themes/py_dracula_light.qss"


        # SET THEME AND HACKS
        if useCustomTheme:
            # LOAD AND APPLY STYLE
            UIFunctions.theme(self, themeFile, True)

            # SET HACKS
            AppFunctions.setThemeHack(self)

        # SET HOME PAGE AND SELECT MENU
        # ///////////////////////////////////////////////////////////////
        widgets.stackedWidget.setCurrentWidget(widgets.home)
        # widgets.btn_home.setStyleSheet(UIFunctions.selectMenu(widgets.btn_home.styleSheet()))

    def choose_input_pdf(self):
        start_dir = self.ui.lineEdit_2.text().strip() or str(Path.home())
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Chọn file PDF", start_dir, "PDF files (*.pdf);;All files (*.*)"
        )
        if file_path:
            self.ui.lineEdit_2.setText(file_path)
        print("1")

    def choose_output_dir(self):
        # mặc định gợi ý: <project_root>/pdf/output
        project_root = Path(__file__).resolve().parent.parent
        suggested = self.ui.lineEdit_3.text().strip() or str(project_root / "pdf" / "output")
        dir_path = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu PDF", suggested)
        if not dir_path:
            return

        # set vào lineEdit_3
        self.ui.lineEdit_3.setText(dir_path)

        # >>> chọn xong thì chạy luôn
        self.run_pipeline()

    def run_pipeline(self):
        pdf_path = self.ui.lineEdit_2.text().strip()
        outpdf_dir = self.ui.lineEdit_3.text().strip()

        if not pdf_path:
            QMessageBox.warning(self, "Thiếu đường dẫn", "Vui lòng chọn file PDF (nút 2).")
            return

        if getattr(sys, 'frozen', False):  # đang chạy trong .exe
            base_path = sys._MEIPASS
        else:  # đang chạy trong Python
            base_path = os.path.dirname(__file__)

            # Các đường dẫn chính dựa trên base_path
        print ("a")
        script_path = os.path.join(base_path, "code", "mainqr.py")
        script_path = os.path.abspath(script_path)

        print("b")

        script_path = os.path.abspath(script_path)  # để chắc chắn ra full path

        outdir = Path(os.path.join(base_path, "scan", "output"))

        # Nếu chưa điền thư mục lưu thì mặc định: <base_path>/pdf/output
        if not outpdf_dir:
            outpdf_dir = os.path.join(base_path, "pdf", "output")
        print("c")

        outpdf = Path(outpdf_dir)
        outdir.mkdir(parents=True, exist_ok=True)
        outpdf.mkdir(parents=True, exist_ok=True)

        # báo trạng thái
        self.ui.pushButton_3.setEnabled(False)

        print("d")

        # chạy mainqr.py bằng QProcess (dùng đúng python của venv)
        self.proc = QProcess(self)
        self.proc.setWorkingDirectory(str(base_path))
        self.proc.setProgram(sys.executable)
        # GỘP STDOUT + STDERR thành một luồng để dễ thấy log
        self.proc.setProcessChannelMode(QProcess.MergedChannels)

        self.proc.setArguments([
            "-u",  # unbuffered: log ra ngay
            str(script_path),
            "--pdf", pdf_path,
            "--outdir", str(outdir),
            "--outpdf", str(outpdf),
            "--page", "0"
        ])

        self.proc.readyReadStandardOutput.connect(
            lambda: print(bytes(self.proc.readAllStandardOutput()).decode("utf-8", "ignore"), end="")
        )
        self.proc.readyReadStandardError.connect(
            lambda: print(self.proc.readAllStandardError().data().decode("utf-8", "ignore"), end="")
        )
        print("e")

        def on_finished(code, status):
            print("f")
            self.ui.pushButton_3.setEnabled(True)
            result_pdf = Path(outpdf) / "qrpdf.pdf"
            print(f"\n===== DEBUG finished: code={code}, status={status} =====")
            print("Expect result:", result_pdf)
            print("Exists:", result_pdf.exists())
            print("================================\n")

            if code == 0 and result_pdf.exists():
                # Ghi đè lineEdit_3 thành đường dẫn file kết quả
                self.ui.lineEdit_3.setText(str(result_pdf))
                # Nếu muốn mở thư mục chứa file ngay:
                # QDesktopServices.openUrl(QUrl.fromLocalFile(str(outpdf)))
            else:
                QMessageBox.critical(self, "Lỗi", f"Return code: {code}")

        self.proc.finished.connect(on_finished)
        self.proc.start()

    # BUTTONS CLICKansfnsaf nam
    # Post here your functions for clicked buttons
    # ///////////////////////////////////////////////////////////////
    def buttonClick(self):
        # GET BUTTON CLICKED
        btn = self.sender()
        btnName = btn.objectName()

        # SHOW HOME PAGE
        if btnName == "btn_home":
            widgets.stackedWidget.setCurrentWidget(widgets.home)
            UIFunctions.resetStyle(self, btnName)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))

        # SHOW WIDGETS PAGE
        # if btnName == "btn_widgets":
        #     widgets.stackedWidget.setCurrentWidget(widgets.widgets)
        #     UIFunctions.resetStyle(self, btnName)
        #     btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))
        #
        # # SHOW NEW PAGE
        # if btnName == "btn_new":
        #     widgets.stackedWidget.setCurrentWidget(widgets.new_page) # SET PAGE
        #     UIFunctions.resetStyle(self, btnName) # RESET ANOTHERS BUTTONS SELECTED
        #     btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet())) # SELECT MENU
        #
        # if btnName == "btn_save":
        #     print("Save BTN clicked!")
        #
        # # PRINT BTN NAME
        # print(f'Button "{btnName}" pressed!')


    # RESIZE EVENTS
    # ///////////////////////////////////////////////////////////////

    def resizeEvent(self, event):
        # Update Size Grips
        UIFunctions.resize_grips(self)

    # MOUSE CLICK EVENTS

    # ///////////////////////////////////////////////////////////////
    def mousePressEvent(self, event):
        # SET DRAG POS WINDOW
        self.dragPos = event.globalPos()

        # PRINT MOUSE EVENTS
        if event.buttons() == Qt.LeftButton:
            print('Mouse click: LEFT CLICK')
        if event.buttons() == Qt.RightButton:
            print('Mouse click: RIGHT CLICK')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("icon.ico"))
    window = MainWindow()
    sys.exit(app.exec_())

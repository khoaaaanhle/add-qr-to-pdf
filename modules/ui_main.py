# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mainRkiNrk.ui'
##
## Created by: Qt User Interface Compiler version 6.0.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from . resources_rc import*

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(545, 569)
        MainWindow.setMinimumSize(QSize(300, 100))
        MainWindow.setMaximumSize(QSize(545, 569))
        font = QFont()
        font.setPointSize(20)
        MainWindow.setFont(font)
        MainWindow.setStyleSheet(u"\n"
"background: transparent;")
        self.styleSheet = QWidget(MainWindow)
        self.styleSheet.setObjectName(u"styleSheet")
        font1 = QFont()
        font1.setFamily(u"Segoe UI")
        font1.setPointSize(10)
        font1.setBold(False)
        font1.setItalic(False)
        self.styleSheet.setFont(font1)
        self.styleSheet.setStyleSheet(u"/* N\u1ec0N: \u1ea3nh auto fit */\n"
"#styleSheet {\n"
"    border-image: url(:/images/images/images/test.jpg) 0 0 0 0 stretch stretch;\n"
"}\n"
"\n"
"/* KHUNG: ch\u1ec9 vi\u1ec1n + n\u1ec1n b\u00e1n trong su\u1ed1t (kh\u00f4ng che n\u1ec1n) */\n"
"#widget_2 {\n"
"    border-radius: 10px;\n"
"    border: 2px solid #009688;\n"
"    background-color: rgba(255, 255, 255, 200);  /* 0..255 => t\u0103ng gi\u1ea3m \u0111\u1ed9 m\u1edd */\n"
"    /* n\u1ebfu mu\u1ed1n ho\u00e0n to\u00e0n trong su\u1ed1t: background-color: transparent; */\n"
"}\n"
"\n"
"/* Label trong khung: ch\u1eef xanh, n\u1ec1n trong su\u1ed1t */\n"
"#widget_2 QLabel {\n"
"    color: #009688;\n"
"    background: transparent;\n"
"    font-weight: 600;\n"
"}\n"
"\n"
"/* LineEdit trong khung: n\u1ec1n tr\u1eafng, vi\u1ec1n xanh \u0111\u1ec3 d\u1ec5 \u0111\u1ecdc */\n"
"#widget_2 QLineEdit {\n"
"    background: #ffffff;\n"
"    color: #000;\n"
"    border: 1px solid #009688;\n"
"    border-radius: 6px;\n"
"    padding: 4px 6px;\n"
"}\n"
"\n"
"/* Button"
                        " trong khung: xanh r\u1ea5t nh\u1ea1t + hover \u0111\u1eadm h\u01a1n */\n"
"#widget_2 QPushButton {\n"
"    background-color: #e0f2f1;      /* xanh nh\u1ea1t */\n"
"    color: #000;\n"
"    border: 1px solid #009688;\n"
"    border-radius: 6px;\n"
"    padding: 6px 10px;\n"
"}\n"
"#widget_2 QPushButton:hover {\n"
"    background-color: #b2dfdb;\n"
"}\n"
"\n"
"/* openGLWidget n\u1ebfu n\u1eb1m trong khung */\n"
"#widget_2 QOpenGLWidget, \n"
"#openGLWidget {\n"
"    background: #ffffff;            /* tr\u00e1nh d\u00ednh \u1ea3nh n\u1ec1n */\n"
"    border: 1px solid #009688;\n"
"    border-radius: 6px;\n"
"}\n"
"")
        self.gridLayout = QGridLayout(self.styleSheet)
        self.gridLayout.setObjectName(u"gridLayout")
        self.frame_2 = QFrame(self.styleSheet)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setMinimumSize(QSize(0, 0))
        self.frame_2.setFont(font1)
        self.frame_2.setLayoutDirection(Qt.LeftToRight)
        self.frame_2.setStyleSheet(u"")
        self.frame_2.setFrameShape(QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Raised)
        self.gridLayout_2 = QGridLayout(self.frame_2)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.widget_2 = QWidget(self.frame_2)
        self.widget_2.setObjectName(u"widget_2")
        self.widget_2.setMaximumSize(QSize(200, 200))
        self.widget_2.setStyleSheet(u"")
        self.gridLayout_3 = QGridLayout(self.widget_2)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.label_2 = QLabel(self.widget_2)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setMaximumSize(QSize(24, 24))
        self.label_2.setPixmap(QPixmap(u":/images/images/images/logo2.jpg"))
        self.label_2.setScaledContents(True)

        self.gridLayout_3.addWidget(self.label_2, 0, 0, 1, 1)

        self.label_3 = QLabel(self.widget_2)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setMaximumSize(QSize(300, 40))
        self.label_3.setStyleSheet(u"font-size: 8pt;\n"
"font-weight: bold;\n"
"color:black;")

        self.gridLayout_3.addWidget(self.label_3, 1, 0, 1, 1)

        self.lineEdit_2 = QLineEdit(self.widget_2)
        self.lineEdit_2.setObjectName(u"lineEdit_2")
        self.lineEdit_2.setMaximumSize(QSize(300, 16777215))
        self.lineEdit_2.setStyleSheet(u"font-size: 8pt;\n"
"font-weight: bold;\n"
"color:black;")

        self.gridLayout_3.addWidget(self.lineEdit_2, 2, 0, 1, 1)

        self.pushButton_2 = QPushButton(self.widget_2)
        self.pushButton_2.setObjectName(u"pushButton_2")
        self.pushButton_2.setMaximumSize(QSize(300, 16777215))
        font2 = QFont()
        font2.setFamily(u"Segoe UI")
        font2.setPointSize(8)
        font2.setBold(True)
        font2.setItalic(False)
        self.pushButton_2.setFont(font2)
        self.pushButton_2.setStyleSheet(u"font-size: 8pt;\n"
"font-weight: bold;\n"
"color:black;")

        self.gridLayout_3.addWidget(self.pushButton_2, 3, 0, 1, 1)

        self.label_5 = QLabel(self.widget_2)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setMaximumSize(QSize(300, 40))
        self.label_5.setStyleSheet(u"font-size: 8pt;\n"
"font-weight: bold;\n"
"color:black;")

        self.gridLayout_3.addWidget(self.label_5, 4, 0, 1, 1)

        self.lineEdit_3 = QLineEdit(self.widget_2)
        self.lineEdit_3.setObjectName(u"lineEdit_3")
        self.lineEdit_3.setMaximumSize(QSize(300, 16777215))
        self.lineEdit_3.setStyleSheet(u"font-size: 8pt;\n"
"font-weight: bold;\n"
"color:black;")

        self.gridLayout_3.addWidget(self.lineEdit_3, 5, 0, 1, 1)

        self.pushButton_3 = QPushButton(self.widget_2)
        self.pushButton_3.setObjectName(u"pushButton_3")
        self.pushButton_3.setMaximumSize(QSize(300, 16777215))
        self.pushButton_3.setStyleSheet(u"font-size: 8pt;\n"
"font-weight: bold;\n"
"color:black;")

        self.gridLayout_3.addWidget(self.pushButton_3, 6, 0, 1, 1)


        self.gridLayout_2.addWidget(self.widget_2, 0, 0, 1, 1)

        self.widget_3 = QWidget(self.frame_2)
        self.widget_3.setObjectName(u"widget_3")

        self.gridLayout_2.addWidget(self.widget_3, 0, 1, 1, 1)

        self.widget = QWidget(self.frame_2)
        self.widget.setObjectName(u"widget")

        self.gridLayout_2.addWidget(self.widget, 1, 0, 1, 1)

        self.widget_4 = QWidget(self.frame_2)
        self.widget_4.setObjectName(u"widget_4")

        self.gridLayout_2.addWidget(self.widget_4, 1, 1, 1, 1)


        self.gridLayout.addWidget(self.frame_2, 0, 0, 1, 1)

        MainWindow.setCentralWidget(self.styleSheet)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.label_2.setText("")
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"Ch\u1ecdn \u0111\u01b0\u1eddng d\u1eabn t\u1edbi th\u01b0 m\u1ee5c pdf", None))
        self.pushButton_2.setText(QCoreApplication.translate("MainWindow", u"Ch\u1ecdn", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"Ch\u1ecdn \u0111\u01b0\u1eddng d\u1eabn l\u01b0u file pdf", None))
        self.pushButton_3.setText(QCoreApplication.translate("MainWindow", u"Xu\u1ea5t file", None))
    # retranslateUi


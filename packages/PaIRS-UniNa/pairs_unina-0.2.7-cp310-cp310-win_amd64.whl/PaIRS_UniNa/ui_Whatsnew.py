from .addwidgets_ps import icons_path
# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'WhatsnewrraxMu.ui'
##
## Created by: Qt User Interface Compiler version 6.7.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QGridLayout, QHBoxLayout, QLabel,
    QMainWindow, QMenuBar, QPushButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

class Ui_Whatsnew(object):
    def setupUi(self, Whatsnew):
        if not Whatsnew.objectName():
            Whatsnew.setObjectName(u"Whatsnew")
        Whatsnew.resize(500, 400)
        self.centralwidget = QWidget(Whatsnew)
        self.centralwidget.setObjectName(u"centralwidget")
        self.mainLay = QGridLayout(self.centralwidget)
        self.mainLay.setSpacing(10)
        self.mainLay.setObjectName(u"mainLay")
        self.mainLay.setContentsMargins(10, 10, 10, 10)
        self.w_Ok = QWidget(self.centralwidget)
        self.w_Ok.setObjectName(u"w_Ok")
        self.w_Ok.setMaximumSize(QSize(16777215, 40))
        self.w_button = QHBoxLayout(self.w_Ok)
        self.w_button.setSpacing(10)
        self.w_button.setObjectName(u"w_button")
        self.w_button.setContentsMargins(0, 0, 0, 0)
        self.hs = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.w_button.addItem(self.hs)

        self.button_Ok = QPushButton(self.w_Ok)
        self.button_Ok.setObjectName(u"button_Ok")
        self.button_Ok.setMinimumSize(QSize(0, 32))
        self.button_Ok.setMaximumSize(QSize(16777215, 32))
        self.button_Ok.setAutoDefault(True)

        self.w_button.addWidget(self.button_Ok)

        self.button_changes = QPushButton(self.w_Ok)
        self.button_changes.setObjectName(u"button_changes")
        self.button_changes.setMinimumSize(QSize(0, 32))
        self.button_changes.setMaximumSize(QSize(16777215, 32))
        self.button_changes.setFlat(False)

        self.w_button.addWidget(self.button_changes)


        self.mainLay.addWidget(self.w_Ok, 1, 1, 1, 1)

        self.lay_Icon = QVBoxLayout()
        self.lay_Icon.setSpacing(0)
        self.lay_Icon.setObjectName(u"lay_Icon")
        self.icon_label = QLabel(self.centralwidget)
        self.icon_label.setObjectName(u"icon_label")
        self.icon_label.setMinimumSize(QSize(64, 64))
        self.icon_label.setMaximumSize(QSize(64, 64))
        self.icon_label.setPixmap(QPixmap(u""+ icons_path +"news.png"))
        self.icon_label.setScaledContents(True)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.icon_label.setWordWrap(False)

        self.lay_Icon.addWidget(self.icon_label)

        self.vs_icon = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.lay_Icon.addItem(self.vs_icon)


        self.mainLay.addLayout(self.lay_Icon, 0, 0, 1, 1)

        self.w_Info = QWidget(self.centralwidget)
        self.w_Info.setObjectName(u"w_Info")
        self.lay_Info = QVBoxLayout(self.w_Info)
        self.lay_Info.setSpacing(0)
        self.lay_Info.setObjectName(u"lay_Info")
        self.lay_Info.setContentsMargins(0, 0, -1, 0)
        self.info = QLabel(self.w_Info)
        self.info.setObjectName(u"info")
        font = QFont()
        font.setFamilies([u"Arial"])
        font.setPointSize(14)
        self.info.setFont(font)
        self.info.setTextFormat(Qt.TextFormat.RichText)
        self.info.setWordWrap(True)
        self.info.setOpenExternalLinks(True)
        self.info.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByKeyboard|Qt.TextInteractionFlag.LinksAccessibleByMouse|Qt.TextInteractionFlag.TextBrowserInteraction|Qt.TextInteractionFlag.TextSelectableByKeyboard|Qt.TextInteractionFlag.TextSelectableByMouse)

        self.lay_Info.addWidget(self.info)

        self.vs_info = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.lay_Info.addItem(self.vs_info)


        self.mainLay.addWidget(self.w_Info, 0, 1, 1, 1)

        Whatsnew.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(Whatsnew)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 500, 43))
        Whatsnew.setMenuBar(self.menubar)

        self.retranslateUi(Whatsnew)

        self.button_Ok.setDefault(True)


        QMetaObject.connectSlotsByName(Whatsnew)
    # setupUi

    def retranslateUi(self, Whatsnew):
        Whatsnew.setWindowTitle(QCoreApplication.translate("Whatsnew", u"What's new", None))
        self.button_Ok.setText(QCoreApplication.translate("Whatsnew", u"OK", None))
        self.button_changes.setText(QCoreApplication.translate("Whatsnew", u"More details", None))
        self.icon_label.setText("")
        self.info.setText(QCoreApplication.translate("Whatsnew", u"<html><head/><body><p><span style=\" font-size:18pt; font-weight:700;\">What's new in PaIRS-UniNa #.#.#</span></p><p><span style=\" font-size:11pt;\">\u2b50</span></p></body></html>", None))
    # retranslateUi


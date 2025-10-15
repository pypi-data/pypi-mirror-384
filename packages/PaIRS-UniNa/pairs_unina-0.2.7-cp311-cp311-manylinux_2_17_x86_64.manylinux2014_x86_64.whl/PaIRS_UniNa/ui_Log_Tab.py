from .addwidgets_ps import icons_path
# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Log_TabEHNRWA.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
    QProgressBar, QScrollArea, QSizePolicy, QTextEdit,
    QToolButton, QVBoxLayout, QWidget)

from .addwidgets_ps import MyTabLabel

class Ui_LogTab(object):
    def setupUi(self, LogTab):
        if not LogTab.objectName():
            LogTab.setObjectName(u"LogTab")
        LogTab.resize(500, 680)
        LogTab.setMinimumSize(QSize(500, 680))
        LogTab.setMaximumSize(QSize(1000, 16777215))
        icon1 = QIcon()
        icon1.addFile(u""+ icons_path +"log_logo.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        LogTab.setWindowIcon(icon1)
        self.verticalLayout_4 = QVBoxLayout(LogTab)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.w_Mode = QWidget(LogTab)
        self.w_Mode.setObjectName(u"w_Mode")
        self.w_Mode.setMinimumSize(QSize(0, 40))
        self.w_Mode.setMaximumSize(QSize(16777215, 40))
        font = QFont()
        font.setPointSize(11)
        self.w_Mode.setFont(font)
        self.horizontalLayout_5 = QHBoxLayout(self.w_Mode)
        self.horizontalLayout_5.setSpacing(3)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 10)
        self.icon = MyTabLabel(self.w_Mode)
        self.icon.setObjectName(u"icon")
        self.icon.setMinimumSize(QSize(35, 35))
        self.icon.setMaximumSize(QSize(35, 35))
        self.icon.setPixmap(QPixmap(u""+ icons_path +"log_logo.png"))
        self.icon.setScaledContents(True)

        self.horizontalLayout_5.addWidget(self.icon)

        self.name_tab = QLabel(self.w_Mode)
        self.name_tab.setObjectName(u"name_tab")
        self.name_tab.setMinimumSize(QSize(200, 35))
        self.name_tab.setMaximumSize(QSize(16777215, 35))
        font1 = QFont()
        font1.setFamilies([u"Arial"])
        font1.setPointSize(20)
        font1.setBold(True)
        self.name_tab.setFont(font1)

        self.horizontalLayout_5.addWidget(self.name_tab)

        self.progress_Proc = QProgressBar(self.w_Mode)
        self.progress_Proc.setObjectName(u"progress_Proc")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.progress_Proc.sizePolicy().hasHeightForWidth())
        self.progress_Proc.setSizePolicy(sizePolicy)
        self.progress_Proc.setMinimumSize(QSize(100, 36))
        self.progress_Proc.setMaximumSize(QSize(100, 36))
        font2 = QFont()
        font2.setPointSize(11)
        font2.setKerning(True)
        self.progress_Proc.setFont(font2)
        self.progress_Proc.setStyleSheet(u"")
        self.progress_Proc.setValue(24)
        self.progress_Proc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_Proc.setInvertedAppearance(False)

        self.horizontalLayout_5.addWidget(self.progress_Proc)

        self.w_button_close_tab = QWidget(self.w_Mode)
        self.w_button_close_tab.setObjectName(u"w_button_close_tab")
        self.w_button_close_tab.setMinimumSize(QSize(18, 24))
        self.w_button_close_tab.setMaximumSize(QSize(18, 24))
        self.horizontalLayout_3 = QHBoxLayout(self.w_button_close_tab)
        self.horizontalLayout_3.setSpacing(0)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, -1)
        self.button_close_tab = QToolButton(self.w_button_close_tab)
        self.button_close_tab.setObjectName(u"button_close_tab")
        self.button_close_tab.setMinimumSize(QSize(18, 18))
        self.button_close_tab.setMaximumSize(QSize(18, 18))
        self.button_close_tab.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.button_close_tab.setStyleSheet(u"QToolButton{\n"
"border-radius: 15px;\n"
"}")
        icon2 = QIcon()
        icon2.addFile(u""+ icons_path +"close.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.button_close_tab.setIcon(icon2)
        self.button_close_tab.setIconSize(QSize(15, 15))

        self.horizontalLayout_3.addWidget(self.button_close_tab)


        self.horizontalLayout_5.addWidget(self.w_button_close_tab)


        self.verticalLayout_4.addWidget(self.w_Mode)

        self.line = QFrame(LogTab)
        self.line.setObjectName(u"line")
        self.line.setMinimumSize(QSize(0, 5))
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_4.addWidget(self.line)

        self.scrollArea = QScrollArea(LogTab)
        self.scrollArea.setObjectName(u"scrollArea")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.scrollArea.sizePolicy().hasHeightForWidth())
        self.scrollArea.setSizePolicy(sizePolicy1)
        self.scrollArea.setMinimumSize(QSize(0, 0))
        self.scrollArea.setStyleSheet(u" QScrollArea {\n"
"        border: 1pix solid gray;\n"
"	    background: transparent;\n"
"    }\n"
"\n"
"QScrollBar:horizontal\n"
"    {\n"
"        height: 15px;\n"
"        margin: 3px 10px 3px 10px;\n"
"        border: 1px transparent #2A2929;\n"
"        border-radius: 4px;\n"
"        background-color:  rgba(200,200,200,50);    /* #2A2929; */\n"
"    }\n"
"\n"
"QScrollBar::handle:horizontal\n"
"    {\n"
"        background-color: rgba(180,180,180,180);      /* #605F5F; */\n"
"        min-width: 30px;\n"
"        border-radius: 4px;\n"
"    }\n"
"\n"
"QScrollBar:vertical\n"
"    {\n"
"        background-color: rgba(200,200,200,50);  ;\n"
"        width: 15px;\n"
"        margin: 10px 3px 10px 3px;\n"
"        border: 1px transparent #2A2929;\n"
"        border-radius: 4px;\n"
"    }\n"
"\n"
"QScrollBar::handle:vertical\n"
"    {\n"
"        background-color: rgba(180,180,180,180);         /* #605F5F; */\n"
"        min-height: 30px;\n"
"        border-radius: 4px;\n"
"    }\n"
"\n"
"QScrollBar::add-line {\n"
""
                        "        border: none;\n"
"        background: none;\n"
"    }\n"
"\n"
"QScrollBar::sub-line {\n"
"        border: none;\n"
"        background: none;\n"
"    }\n"
"")
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 482, 605))
        self.verticalLayout_8 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_8.setSpacing(10)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.verticalLayout_8.setContentsMargins(0, 5, 10, 0)
        self.log = QTextEdit(self.scrollAreaWidgetContents)
        self.log.setObjectName(u"log")
        font3 = QFont()
        font3.setFamilies([u"Courier New"])
        font3.setPointSize(10)
        self.log.setFont(font3)
        self.log.setStyleSheet(u"background-color: rgb(0, 0, 0);\n"
"border-color: rgb(255, 255, 255);\n"
"color: rgb(255, 255, 255);")
        self.log.setLineWrapMode(QTextEdit.LineWrapMode.FixedPixelWidth)
        self.log.setLineWrapColumnOrWidth(600)
        self.log.setReadOnly(True)
        self.log.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByKeyboard|Qt.TextInteractionFlag.TextSelectableByMouse)

        self.verticalLayout_8.addWidget(self.log)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout_4.addWidget(self.scrollArea)

        QWidget.setTabOrder(self.button_close_tab, self.scrollArea)
        QWidget.setTabOrder(self.scrollArea, self.log)

        self.retranslateUi(LogTab)

        QMetaObject.connectSlotsByName(LogTab)
    # setupUi

    def retranslateUi(self, LogTab):
        LogTab.setWindowTitle(QCoreApplication.translate("LogTab", u"Log", None))
        self.icon.setText("")
        self.name_tab.setText(QCoreApplication.translate("LogTab", u" Log", None))
#if QT_CONFIG(tooltip)
        self.button_close_tab.setToolTip(QCoreApplication.translate("LogTab", u"Close tab", None))
#endif // QT_CONFIG(tooltip)
        self.button_close_tab.setText("")
#if QT_CONFIG(shortcut)
        self.button_close_tab.setShortcut(QCoreApplication.translate("LogTab", u"Alt+L", None))
#endif // QT_CONFIG(shortcut)
        self.log.setHtml(QCoreApplication.translate("LogTab", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Courier New'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">PaIRS - version 0.1.4</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Particle Image Reconstruction Software</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">(C) 2023 Gerardo Paolillo &amp; Tommaso Astarita.</p>\n"
"<p style=\" margin-top:"
                        "0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">All rights reserved.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">email: etfd@unina.it</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">****************************************</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">PIV computation (C:/desk/PIV_Img/img1/out_PaIRS/out.pairs.pivproc)</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">PaIRS-v0.1.4_Windows-Gerardo_2023/03/20-15:40:56_proc2_25244-24572_f795e531-a620-4e8c-b516-ea3403d6330d</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Last modified date: 2023/03/"
                        "20 at 15:41:03</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">------------------------------------</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">               OUTPUT               </p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">------------------------------------</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">synthetic00010.jpg-synthetic00011.jpg</p>\n"
"<p style=\" mar"
                        "gin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">It    IW      #IW        #Vect/#Tot      %       CC       CC(avg)   DC%</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"> -2 128x128    8x6         48/48      100.0  0.1740781  0.7743774   0.0</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"> -1  64x64    36x30      1080/1080    100.0  0.8245546  0.8451467   0.0</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">  0  32x32    74x61      4514/4514    100.0  0.8630154  0.8637075   0.9</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">  1  32x32    74x61      4514/4514    100.0  0.8676594  0.8670790   0.1</p>\n"
"<p style=\" margin-top:0px; margin-"
                        "bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">  2  32x32    74x61      4514/4514    100.0  0.8677620  0.8671634   0.0</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>", None))
    # retranslateUi


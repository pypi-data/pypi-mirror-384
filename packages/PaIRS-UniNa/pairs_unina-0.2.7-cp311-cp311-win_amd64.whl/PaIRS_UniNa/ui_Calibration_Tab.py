from .addwidgets_ps import icons_path
# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Calibration_Tab.ui'
##
## Created by: Qt User Interface Compiler version 6.7.0
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
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QFrame, QHBoxLayout,
    QHeaderView, QLabel, QLayout, QScrollArea,
    QSizePolicy, QSpacerItem, QToolButton, QTreeWidgetItem,
    QVBoxLayout, QWidget)

from .Input_Tab_tools import CalibrationTree
from .addwidgets_ps import (ClickableLabel, MyQSpin)

class Ui_CalibrationTab(object):
    def setupUi(self, CalibrationTab):
        if not CalibrationTab.objectName():
            CalibrationTab.setObjectName(u"CalibrationTab")
        CalibrationTab.resize(500, 680)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(CalibrationTab.sizePolicy().hasHeightForWidth())
        CalibrationTab.setSizePolicy(sizePolicy)
        CalibrationTab.setMinimumSize(QSize(500, 680))
        CalibrationTab.setMaximumSize(QSize(1000, 16777215))
        font = QFont()
        font.setPointSize(11)
        CalibrationTab.setFont(font)
        icon1 = QIcon()
        icon1.addFile(u""+ icons_path +"calibration_logo.png", QSize(), QIcon.Normal, QIcon.Off)
        CalibrationTab.setWindowIcon(icon1)
        self.verticalLayout_65 = QVBoxLayout(CalibrationTab)
        self.verticalLayout_65.setSpacing(5)
        self.verticalLayout_65.setObjectName(u"verticalLayout_65")
        self.verticalLayout_65.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.verticalLayout_65.setContentsMargins(10, 10, 10, 10)
        self.w_Mode = QWidget(CalibrationTab)
        self.w_Mode.setObjectName(u"w_Mode")
        self.w_Mode.setMinimumSize(QSize(0, 40))
        self.w_Mode.setMaximumSize(QSize(16777215, 40))
        self.w_Mode.setFont(font)
        self.horizontalLayout_2 = QHBoxLayout(self.w_Mode)
        self.horizontalLayout_2.setSpacing(3)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 10)
        self.icon = QLabel(self.w_Mode)
        self.icon.setObjectName(u"icon")
        self.icon.setMinimumSize(QSize(35, 35))
        self.icon.setMaximumSize(QSize(35, 35))
        self.icon.setPixmap(QPixmap(u""+ icons_path +"calibration_logo.png"))
        self.icon.setScaledContents(True)

        self.horizontalLayout_2.addWidget(self.icon)

        self.name_tab = ClickableLabel(self.w_Mode)
        self.name_tab.setObjectName(u"name_tab")
        self.name_tab.setMinimumSize(QSize(100, 35))
        self.name_tab.setMaximumSize(QSize(16777215, 35))
        font1 = QFont()
        font1.setPointSize(20)
        font1.setBold(True)
        self.name_tab.setFont(font1)

        self.horizontalLayout_2.addWidget(self.name_tab)

        self.w_label_done = QWidget(self.w_Mode)
        self.w_label_done.setObjectName(u"w_label_done")
        self.w_label_done.setMinimumSize(QSize(18, 24))
        self.w_label_done.setMaximumSize(QSize(18, 24))
        self.horizontalLayout_4 = QHBoxLayout(self.w_label_done)
        self.horizontalLayout_4.setSpacing(0)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 12)
        self.label_done = ClickableLabel(self.w_label_done)
        self.label_done.setObjectName(u"label_done")
        self.label_done.setMinimumSize(QSize(12, 12))
        self.label_done.setMaximumSize(QSize(12, 12))
        self.label_done.setPixmap(QPixmap(u""+ icons_path +"completed.png"))
        self.label_done.setScaledContents(True)
        self.label_done.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_4.addWidget(self.label_done)


        self.horizontalLayout_2.addWidget(self.w_label_done)

        self.hs1 = QSpacerItem(30, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.hs1)

        self.button_CalVi = QToolButton(self.w_Mode)
        self.button_CalVi.setObjectName(u"button_CalVi")
        self.button_CalVi.setMinimumSize(QSize(99, 33))
        self.button_CalVi.setMaximumSize(QSize(99, 33))
        self.button_CalVi.setCursor(QCursor(Qt.PointingHandCursor))
        icon2 = QIcon()
        icon2.addFile(u""+ icons_path +"logo_CalVi.png", QSize(), QIcon.Normal, QIcon.Off)
        self.button_CalVi.setIcon(icon2)
        self.button_CalVi.setIconSize(QSize(75, 25))
        self.button_CalVi.setCheckable(True)

        self.horizontalLayout_2.addWidget(self.button_CalVi)

        self.hs2 = QSpacerItem(30, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.hs2)

        self.label_number = QLabel(self.w_Mode)
        self.label_number.setObjectName(u"label_number")
        self.label_number.setMinimumSize(QSize(15, 0))
        self.label_number.setMaximumSize(QSize(30, 16777215))
        font2 = QFont()
        font2.setPointSize(9)
        self.label_number.setFont(font2)
        self.label_number.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_2.addWidget(self.label_number)

        self.hs3 = QSpacerItem(5, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.hs3)

        self.button_back = QToolButton(self.w_Mode)
        self.button_back.setObjectName(u"button_back")
        self.button_back.setMinimumSize(QSize(24, 24))
        self.button_back.setMaximumSize(QSize(24, 24))
        icon3 = QIcon()
        icon3.addFile(u""+ icons_path +"undo.png", QSize(), QIcon.Normal, QIcon.Off)
        self.button_back.setIcon(icon3)
        self.button_back.setIconSize(QSize(20, 20))

        self.horizontalLayout_2.addWidget(self.button_back)

        self.button_forward = QToolButton(self.w_Mode)
        self.button_forward.setObjectName(u"button_forward")
        self.button_forward.setMinimumSize(QSize(24, 24))
        self.button_forward.setMaximumSize(QSize(24, 24))
        icon4 = QIcon()
        icon4.addFile(u""+ icons_path +"redo.png", QSize(), QIcon.Normal, QIcon.Off)
        self.button_forward.setIcon(icon4)
        self.button_forward.setIconSize(QSize(20, 20))

        self.horizontalLayout_2.addWidget(self.button_forward)

        self.w_button_close_tab = QWidget(self.w_Mode)
        self.w_button_close_tab.setObjectName(u"w_button_close_tab")
        self.w_button_close_tab.setMinimumSize(QSize(18, 24))
        self.w_button_close_tab.setMaximumSize(QSize(18, 24))
        self.horizontalLayout_20 = QHBoxLayout(self.w_button_close_tab)
        self.horizontalLayout_20.setSpacing(0)
        self.horizontalLayout_20.setObjectName(u"horizontalLayout_20")
        self.horizontalLayout_20.setContentsMargins(0, 0, 0, -1)
        self.button_close_tab = QToolButton(self.w_button_close_tab)
        self.button_close_tab.setObjectName(u"button_close_tab")
        self.button_close_tab.setMinimumSize(QSize(18, 18))
        self.button_close_tab.setMaximumSize(QSize(18, 18))
        self.button_close_tab.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.button_close_tab.setStyleSheet(u"QToolButton{\n"
"border-radius: 15px;\n"
"}")
        icon5 = QIcon()
        icon5.addFile(u""+ icons_path +"close.png", QSize(), QIcon.Normal, QIcon.Off)
        self.button_close_tab.setIcon(icon5)
        self.button_close_tab.setIconSize(QSize(15, 15))

        self.horizontalLayout_20.addWidget(self.button_close_tab)


        self.horizontalLayout_2.addWidget(self.w_button_close_tab)


        self.verticalLayout_65.addWidget(self.w_Mode)

        self.separator = QFrame(CalibrationTab)
        self.separator.setObjectName(u"separator")
        self.separator.setMinimumSize(QSize(0, 5))
        self.separator.setFrameShape(QFrame.Shape.HLine)
        self.separator.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_65.addWidget(self.separator)

        self.scrollArea = QScrollArea(CalibrationTab)
        self.scrollArea.setObjectName(u"scrollArea")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.scrollArea.sizePolicy().hasHeightForWidth())
        self.scrollArea.setSizePolicy(sizePolicy1)
        self.scrollArea.setMinimumSize(QSize(20, 20))
        self.scrollArea.setMaximumSize(QSize(16777215, 16777215))
        self.scrollArea.setStyleSheet(u" QScrollArea {\n"
"        border: 1pix solid gray;\n"
"	   background: transparent;\n"
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
"        min-width: 5px;\n"
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
"        min-height: 5px;\n"
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
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 480, 607))
        sizePolicy.setHeightForWidth(self.scrollAreaWidgetContents.sizePolicy().hasHeightForWidth())
        self.scrollAreaWidgetContents.setSizePolicy(sizePolicy)
        self.scrollAreaWidgetContents.setMinimumSize(QSize(0, 0))
        self.scrollAreaWidgetContents.setStyleSheet(u"\u2020")
        self.verticalLayout_10 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_10.setSpacing(5)
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.verticalLayout_10.setContentsMargins(0, 15, 10, 5)
        self.w_ncam = QWidget(self.scrollAreaWidgetContents)
        self.w_ncam.setObjectName(u"w_ncam")
        self.horizontalLayout_5 = QHBoxLayout(self.w_ncam)
        self.horizontalLayout_5.setSpacing(10)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.label_ncam = QLabel(self.w_ncam)
        self.label_ncam.setObjectName(u"label_ncam")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.label_ncam.sizePolicy().hasHeightForWidth())
        self.label_ncam.setSizePolicy(sizePolicy2)
        self.label_ncam.setMinimumSize(QSize(0, 20))
        self.label_ncam.setMaximumSize(QSize(80, 20))
        font3 = QFont()
        font3.setPointSize(10)
        font3.setBold(False)
        font3.setItalic(True)
        self.label_ncam.setFont(font3)
        self.label_ncam.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_5.addWidget(self.label_ncam)

        self.spin_ncam = MyQSpin(self.w_ncam)
        self.spin_ncam.setObjectName(u"spin_ncam")
        self.spin_ncam.setEnabled(True)
        self.spin_ncam.setMinimumSize(QSize(50, 24))
        self.spin_ncam.setMaximumSize(QSize(70, 24))
        self.spin_ncam.setFont(font)
        self.spin_ncam.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.spin_ncam.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        self.spin_ncam.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
        self.spin_ncam.setMinimum(1)
        self.spin_ncam.setMaximum(99)
        self.spin_ncam.setValue(1)

        self.horizontalLayout_5.addWidget(self.spin_ncam)

        self.hs_ncam = QSpacerItem(40, 13, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.hs_ncam)


        self.verticalLayout_10.addWidget(self.w_ncam)

        self.buttonBar = QWidget(self.scrollAreaWidgetContents)
        self.buttonBar.setObjectName(u"buttonBar")
        self.buttonBar.setMinimumSize(QSize(0, 24))
        self.buttonBar.setMaximumSize(QSize(16777215, 24))
        self.horizontalLayout_3 = QHBoxLayout(self.buttonBar)
        self.horizontalLayout_3.setSpacing(5)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.label_list = QLabel(self.buttonBar)
        self.label_list.setObjectName(u"label_list")
        sizePolicy2.setHeightForWidth(self.label_list.sizePolicy().hasHeightForWidth())
        self.label_list.setSizePolicy(sizePolicy2)
        self.label_list.setMinimumSize(QSize(110, 20))
        self.label_list.setMaximumSize(QSize(1000, 20))
        self.label_list.setFont(font3)
        self.label_list.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_3.addWidget(self.label_list)

        self.button_scan_list = QToolButton(self.buttonBar)
        self.button_scan_list.setObjectName(u"button_scan_list")
        self.button_scan_list.setMinimumSize(QSize(20, 20))
        self.button_scan_list.setMaximumSize(QSize(20, 20))
        font4 = QFont()
        font4.setPointSize(16)
        self.button_scan_list.setFont(font4)
        icon6 = QIcon()
        icon6.addFile(u""+ icons_path +"scan_list.png", QSize(), QIcon.Normal, QIcon.Off)
        self.button_scan_list.setIcon(icon6)
        self.button_scan_list.setIconSize(QSize(18, 18))
        self.button_scan_list.setCheckable(False)

        self.horizontalLayout_3.addWidget(self.button_scan_list)

        self.hs_buttonBar = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.hs_buttonBar)

        self.button_import = QToolButton(self.buttonBar)
        self.button_import.setObjectName(u"button_import")
        self.button_import.setMinimumSize(QSize(20, 20))
        self.button_import.setMaximumSize(QSize(20, 20))
        self.button_import.setFont(font4)
        icon7 = QIcon()
        icon7.addFile(u""+ icons_path +"read.png", QSize(), QIcon.Normal, QIcon.Off)
        self.button_import.setIcon(icon7)
        self.button_import.setIconSize(QSize(18, 18))
        self.button_import.setCheckable(False)

        self.horizontalLayout_3.addWidget(self.button_import)

        self.line = QFrame(self.buttonBar)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.VLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.horizontalLayout_3.addWidget(self.line)

        self.button_copy = QToolButton(self.buttonBar)
        self.button_copy.setObjectName(u"button_copy")
        self.button_copy.setMinimumSize(QSize(20, 20))
        self.button_copy.setMaximumSize(QSize(20, 20))
        self.button_copy.setFont(font4)
        icon8 = QIcon()
        icon8.addFile(u""+ icons_path +"copy.png", QSize(), QIcon.Normal, QIcon.Off)
        self.button_copy.setIcon(icon8)
        self.button_copy.setIconSize(QSize(18, 18))
        self.button_copy.setCheckable(False)

        self.horizontalLayout_3.addWidget(self.button_copy)

        self.button_cut = QToolButton(self.buttonBar)
        self.button_cut.setObjectName(u"button_cut")
        self.button_cut.setMinimumSize(QSize(20, 20))
        self.button_cut.setMaximumSize(QSize(20, 20))
        self.button_cut.setFont(font4)
        icon9 = QIcon()
        icon9.addFile(u""+ icons_path +"cut.png", QSize(), QIcon.Normal, QIcon.Off)
        self.button_cut.setIcon(icon9)
        self.button_cut.setIconSize(QSize(18, 18))
        self.button_cut.setCheckable(False)

        self.horizontalLayout_3.addWidget(self.button_cut)

        self.button_paste_below = QToolButton(self.buttonBar)
        self.button_paste_below.setObjectName(u"button_paste_below")
        self.button_paste_below.setMinimumSize(QSize(20, 20))
        self.button_paste_below.setMaximumSize(QSize(20, 20))
        self.button_paste_below.setFont(font4)
        icon10 = QIcon()
        icon10.addFile(u""+ icons_path +"paste_below.png", QSize(), QIcon.Normal, QIcon.Off)
        self.button_paste_below.setIcon(icon10)
        self.button_paste_below.setIconSize(QSize(18, 18))
        self.button_paste_below.setCheckable(False)

        self.horizontalLayout_3.addWidget(self.button_paste_below)

        self.button_paste_above = QToolButton(self.buttonBar)
        self.button_paste_above.setObjectName(u"button_paste_above")
        self.button_paste_above.setMinimumSize(QSize(20, 20))
        self.button_paste_above.setMaximumSize(QSize(20, 20))
        self.button_paste_above.setFont(font4)
        icon11 = QIcon()
        icon11.addFile(u""+ icons_path +"paste_above.png", QSize(), QIcon.Normal, QIcon.Off)
        self.button_paste_above.setIcon(icon11)
        self.button_paste_above.setIconSize(QSize(18, 18))
        self.button_paste_above.setCheckable(False)

        self.horizontalLayout_3.addWidget(self.button_paste_above)

        self.line_2 = QFrame(self.buttonBar)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.Shape.VLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.horizontalLayout_3.addWidget(self.line_2)

        self.button_clean = QToolButton(self.buttonBar)
        self.button_clean.setObjectName(u"button_clean")
        self.button_clean.setMinimumSize(QSize(20, 20))
        self.button_clean.setMaximumSize(QSize(20, 20))
        self.button_clean.setFont(font4)
        icon12 = QIcon()
        icon12.addFile(u""+ icons_path +"clean.png", QSize(), QIcon.Normal, QIcon.Off)
        self.button_clean.setIcon(icon12)
        self.button_clean.setIconSize(QSize(18, 18))
        self.button_clean.setCheckable(False)

        self.horizontalLayout_3.addWidget(self.button_clean)


        self.verticalLayout_10.addWidget(self.buttonBar)

        self.calTree = CalibrationTree(self.scrollAreaWidgetContents)
        self.calTree.setObjectName(u"calTree")
        self.calTree.setUniformRowHeights(True)
        self.calTree.header().setVisible(True)

        self.verticalLayout_10.addWidget(self.calTree)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_10.addItem(self.verticalSpacer)

        self.verticalLayout_10.setStretch(2, 1)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout_65.addWidget(self.scrollArea)

        QWidget.setTabOrder(self.button_back, self.button_forward)
        QWidget.setTabOrder(self.button_forward, self.button_close_tab)
        QWidget.setTabOrder(self.button_close_tab, self.scrollArea)

        self.retranslateUi(CalibrationTab)

        QMetaObject.connectSlotsByName(CalibrationTab)
    # setupUi

    def retranslateUi(self, CalibrationTab):
        CalibrationTab.setWindowTitle(QCoreApplication.translate("CalibrationTab", u"Calibration", None))
        self.icon.setText("")
        self.name_tab.setText(QCoreApplication.translate("CalibrationTab", u" Calibration", None))
        self.label_done.setText("")
        self.button_CalVi.setText("")
        self.label_number.setText(QCoreApplication.translate("CalibrationTab", u"1", None))
#if QT_CONFIG(tooltip)
        self.button_back.setToolTip(QCoreApplication.translate("CalibrationTab", u"Undo", None))
#endif // QT_CONFIG(tooltip)
        self.button_back.setText("")
#if QT_CONFIG(tooltip)
        self.button_forward.setToolTip(QCoreApplication.translate("CalibrationTab", u"Redo", None))
#endif // QT_CONFIG(tooltip)
        self.button_forward.setText("")
#if QT_CONFIG(tooltip)
        self.button_close_tab.setToolTip(QCoreApplication.translate("CalibrationTab", u"Close tab", None))
#endif // QT_CONFIG(tooltip)
        self.button_close_tab.setText("")
#if QT_CONFIG(shortcut)
        self.button_close_tab.setShortcut(QCoreApplication.translate("CalibrationTab", u"Alt+P", None))
#endif // QT_CONFIG(shortcut)
        self.label_ncam.setText(QCoreApplication.translate("CalibrationTab", u"# cam:", None))
#if QT_CONFIG(tooltip)
        self.spin_ncam.setToolTip(QCoreApplication.translate("CalibrationTab", u"Number of cameras", None))
#endif // QT_CONFIG(tooltip)
        self.label_list.setText(QCoreApplication.translate("CalibrationTab", u"Calibration file list", None))
#if QT_CONFIG(tooltip)
        self.button_scan_list.setToolTip(QCoreApplication.translate("CalibrationTab", u"Re-scan current list to check for missing files", None))
#endif // QT_CONFIG(tooltip)
        self.button_scan_list.setText("")
#if QT_CONFIG(shortcut)
        self.button_scan_list.setShortcut(QCoreApplication.translate("CalibrationTab", u"F5", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(tooltip)
        self.button_import.setToolTip(QCoreApplication.translate("CalibrationTab", u"Import calibration files", None))
#endif // QT_CONFIG(tooltip)
        self.button_import.setText("")
#if QT_CONFIG(shortcut)
        self.button_import.setShortcut(QCoreApplication.translate("CalibrationTab", u"Ctrl+R", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(tooltip)
        self.button_copy.setToolTip(QCoreApplication.translate("CalibrationTab", u"Copy selected calibration files", None))
#endif // QT_CONFIG(tooltip)
        self.button_copy.setText("")
#if QT_CONFIG(shortcut)
        self.button_copy.setShortcut(QCoreApplication.translate("CalibrationTab", u"Ctrl+C", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(tooltip)
        self.button_cut.setToolTip(QCoreApplication.translate("CalibrationTab", u"Cut selected calibration files", None))
#endif // QT_CONFIG(tooltip)
        self.button_cut.setText("")
#if QT_CONFIG(shortcut)
        self.button_cut.setShortcut(QCoreApplication.translate("CalibrationTab", u"Ctrl+X", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(tooltip)
        self.button_paste_below.setToolTip(QCoreApplication.translate("CalibrationTab", u"Paste below the current item", None))
#endif // QT_CONFIG(tooltip)
        self.button_paste_below.setText("")
#if QT_CONFIG(shortcut)
        self.button_paste_below.setShortcut(QCoreApplication.translate("CalibrationTab", u"Ctrl+V", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(tooltip)
        self.button_paste_above.setToolTip(QCoreApplication.translate("CalibrationTab", u"Paste above the current item", None))
#endif // QT_CONFIG(tooltip)
        self.button_paste_above.setText("")
#if QT_CONFIG(shortcut)
        self.button_paste_above.setShortcut(QCoreApplication.translate("CalibrationTab", u"Ctrl+Shift+V", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(tooltip)
        self.button_clean.setToolTip(QCoreApplication.translate("CalibrationTab", u"Clean the whole list", None))
#endif // QT_CONFIG(tooltip)
        self.button_clean.setText("")
#if QT_CONFIG(shortcut)
        self.button_clean.setShortcut(QCoreApplication.translate("CalibrationTab", u"Ctrl+O", None))
#endif // QT_CONFIG(shortcut)
    # retranslateUi


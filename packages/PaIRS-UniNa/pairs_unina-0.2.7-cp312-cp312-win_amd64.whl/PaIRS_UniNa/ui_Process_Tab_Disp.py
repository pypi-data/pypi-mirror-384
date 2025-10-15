from .addwidgets_ps import icons_path
# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Process_Tab_DispkZBIdD.ui'
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
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QComboBox, QFrame,
    QGridLayout, QGroupBox, QHBoxLayout, QLabel,
    QLayout, QScrollArea, QSizePolicy, QSpacerItem,
    QStackedWidget, QToolButton, QVBoxLayout, QWidget)

from .addwidgets_ps import (ClickableEditLabel, CollapsibleBox, MyQCombo, MyQDoubleSpin,
    MyQLineEditNumber, MyQSpin, MyTabLabel, MyToolButton)

class Ui_ProcessTab_Disp(object):
    def setupUi(self, ProcessTab_Disp):
        if not ProcessTab_Disp.objectName():
            ProcessTab_Disp.setObjectName(u"ProcessTab_Disp")
        ProcessTab_Disp.resize(500, 680)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(ProcessTab_Disp.sizePolicy().hasHeightForWidth())
        ProcessTab_Disp.setSizePolicy(sizePolicy)
        ProcessTab_Disp.setMinimumSize(QSize(500, 680))
        ProcessTab_Disp.setMaximumSize(QSize(1000, 16777215))
        font = QFont()
        font.setPointSize(11)
        ProcessTab_Disp.setFont(font)
        icon1 = QIcon()
        icon1.addFile(u""+ icons_path +"process_logo.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        ProcessTab_Disp.setWindowIcon(icon1)
        self.verticalLayout_65 = QVBoxLayout(ProcessTab_Disp)
        self.verticalLayout_65.setSpacing(5)
        self.verticalLayout_65.setObjectName(u"verticalLayout_65")
        self.verticalLayout_65.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.verticalLayout_65.setContentsMargins(10, 10, 10, 10)
        self.w_Mode = QWidget(ProcessTab_Disp)
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
        self.icon.setPixmap(QPixmap(u""+ icons_path +"process_logo.png"))
        self.icon.setScaledContents(True)

        self.horizontalLayout_2.addWidget(self.icon)

        self.name_tab = MyTabLabel(self.w_Mode)
        self.name_tab.setObjectName(u"name_tab")
        self.name_tab.setMinimumSize(QSize(150, 35))
        self.name_tab.setMaximumSize(QSize(16777215, 35))
        font1 = QFont()
        font1.setPointSize(20)
        font1.setBold(True)
        self.name_tab.setFont(font1)

        self.horizontalLayout_2.addWidget(self.name_tab)

        self.hs1 = QSpacerItem(30, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.hs1)

        self.label_number = QLabel(self.w_Mode)
        self.label_number.setObjectName(u"label_number")
        self.label_number.setMinimumSize(QSize(15, 0))
        self.label_number.setMaximumSize(QSize(30, 16777215))
        font2 = QFont()
        font2.setPointSize(9)
        self.label_number.setFont(font2)
        self.label_number.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_2.addWidget(self.label_number)

        self.hs_2 = QSpacerItem(5, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.hs_2)

        self.button_back = QToolButton(self.w_Mode)
        self.button_back.setObjectName(u"button_back")
        self.button_back.setMinimumSize(QSize(24, 24))
        self.button_back.setMaximumSize(QSize(24, 24))
        icon2 = QIcon()
        icon2.addFile(u""+ icons_path +"undo.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.button_back.setIcon(icon2)
        self.button_back.setIconSize(QSize(20, 20))

        self.horizontalLayout_2.addWidget(self.button_back)

        self.button_forward = QToolButton(self.w_Mode)
        self.button_forward.setObjectName(u"button_forward")
        self.button_forward.setMinimumSize(QSize(24, 24))
        self.button_forward.setMaximumSize(QSize(24, 24))
        icon3 = QIcon()
        icon3.addFile(u""+ icons_path +"redo.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.button_forward.setIcon(icon3)
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
        icon4 = QIcon()
        icon4.addFile(u""+ icons_path +"close.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.button_close_tab.setIcon(icon4)
        self.button_close_tab.setIconSize(QSize(15, 15))

        self.horizontalLayout_20.addWidget(self.button_close_tab)


        self.horizontalLayout_2.addWidget(self.w_button_close_tab)


        self.verticalLayout_65.addWidget(self.w_Mode)

        self.separator = QFrame(ProcessTab_Disp)
        self.separator.setObjectName(u"separator")
        self.separator.setMinimumSize(QSize(0, 5))
        self.separator.setFrameShape(QFrame.Shape.HLine)
        self.separator.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_65.addWidget(self.separator)

        self.scrollArea = QScrollArea(ProcessTab_Disp)
        self.scrollArea.setObjectName(u"scrollArea")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.scrollArea.sizePolicy().hasHeightForWidth())
        self.scrollArea.setSizePolicy(sizePolicy1)
        self.scrollArea.setMinimumSize(QSize(0, 0))
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
        self.verticalLayout_10.setSpacing(20)
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.verticalLayout_10.setContentsMargins(0, 15, 10, 5)
        self.CollapBox_FinIt = CollapsibleBox(self.scrollAreaWidgetContents)
        self.CollapBox_FinIt.setObjectName(u"CollapBox_FinIt")
        sizePolicy.setHeightForWidth(self.CollapBox_FinIt.sizePolicy().hasHeightForWidth())
        self.CollapBox_FinIt.setSizePolicy(sizePolicy)
        self.CollapBox_FinIt.setMinimumSize(QSize(0, 56))
        self.CollapBox_FinIt.setMaximumSize(QSize(16777215, 16777215))
        self.verticalLayout_24 = QVBoxLayout(self.CollapBox_FinIt)
        self.verticalLayout_24.setSpacing(0)
        self.verticalLayout_24.setObjectName(u"verticalLayout_24")
        self.verticalLayout_24.setContentsMargins(0, 0, 0, 0)
        self.lay_CollapBox_FinIt = QHBoxLayout()
        self.lay_CollapBox_FinIt.setSpacing(0)
        self.lay_CollapBox_FinIt.setObjectName(u"lay_CollapBox_FinIt")
        self.lay_CollapBox_FinIt.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.tool_CollapBox_FinIt = QToolButton(self.CollapBox_FinIt)
        self.tool_CollapBox_FinIt.setObjectName(u"tool_CollapBox_FinIt")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.tool_CollapBox_FinIt.sizePolicy().hasHeightForWidth())
        self.tool_CollapBox_FinIt.setSizePolicy(sizePolicy2)
        self.tool_CollapBox_FinIt.setMinimumSize(QSize(0, 20))
        self.tool_CollapBox_FinIt.setMaximumSize(QSize(16777215, 20))
        font3 = QFont()
        font3.setPointSize(10)
        font3.setBold(True)
        self.tool_CollapBox_FinIt.setFont(font3)
        self.tool_CollapBox_FinIt.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.tool_CollapBox_FinIt.setStyleSheet(u"QToolButton { border: none; }")
        self.tool_CollapBox_FinIt.setCheckable(True)
        self.tool_CollapBox_FinIt.setChecked(True)
        self.tool_CollapBox_FinIt.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.tool_CollapBox_FinIt.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.tool_CollapBox_FinIt.setArrowType(Qt.ArrowType.DownArrow)

        self.lay_CollapBox_FinIt.addWidget(self.tool_CollapBox_FinIt)

        self.hsp_CollapBox_FinIt = QSpacerItem(100, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.lay_CollapBox_FinIt.addItem(self.hsp_CollapBox_FinIt)

        self.button_CollapBox_FinIt = MyToolButton(self.CollapBox_FinIt)
        self.button_CollapBox_FinIt.setObjectName(u"button_CollapBox_FinIt")
        self.button_CollapBox_FinIt.setMinimumSize(QSize(18, 18))
        self.button_CollapBox_FinIt.setMaximumSize(QSize(18, 18))
        self.button_CollapBox_FinIt.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.button_CollapBox_FinIt.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.button_CollapBox_FinIt.setIcon(icon2)
        self.button_CollapBox_FinIt.setIconSize(QSize(12, 12))

        self.lay_CollapBox_FinIt.addWidget(self.button_CollapBox_FinIt)


        self.verticalLayout_24.addLayout(self.lay_CollapBox_FinIt)

        self.w_Nit = QGroupBox(self.CollapBox_FinIt)
        self.w_Nit.setObjectName(u"w_Nit")
        sizePolicy.setHeightForWidth(self.w_Nit.sizePolicy().hasHeightForWidth())
        self.w_Nit.setSizePolicy(sizePolicy)
        self.w_Nit.setMinimumSize(QSize(0, 34))
        font4 = QFont()
        font4.setPointSize(10)
        font4.setBold(True)
        font4.setItalic(False)
        font4.setKerning(False)
        self.w_Nit.setFont(font4)
        self.w_Nit.setStyleSheet(u"QGroupBox{border: 1px solid gray; border-radius: 6px;}\n"
"")
        self.horizontalLayout_6 = QHBoxLayout(self.w_Nit)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(6, 6, 6, 6)
        self.label_Nit = QLabel(self.w_Nit)
        self.label_Nit.setObjectName(u"label_Nit")
        self.label_Nit.setMinimumSize(QSize(0, 22))
        self.label_Nit.setMaximumSize(QSize(16777215, 22))
        font5 = QFont()
        font5.setPointSize(10)
        font5.setBold(False)
        font5.setItalic(True)
        self.label_Nit.setFont(font5)
        self.label_Nit.setStyleSheet(u"border: none;")
        self.label_Nit.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_6.addWidget(self.label_Nit)

        self.spin_Nit = MyQSpin(self.w_Nit)
        self.spin_Nit.setObjectName(u"spin_Nit")
        self.spin_Nit.setMinimumSize(QSize(55, 22))
        self.spin_Nit.setMaximumSize(QSize(66, 22))
        self.spin_Nit.setFont(font)
        self.spin_Nit.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_Nit.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
        self.spin_Nit.setMinimum(0)
        self.spin_Nit.setValue(5)

        self.horizontalLayout_6.addWidget(self.spin_Nit)

        self.horizontalSpacer_3 = QSpacerItem(30, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_3)

        self.label_frames = QLabel(self.w_Nit)
        self.label_frames.setObjectName(u"label_frames")
        self.label_frames.setMinimumSize(QSize(0, 22))
        self.label_frames.setMaximumSize(QSize(16777215, 22))
        self.label_frames.setFont(font5)
        self.label_frames.setStyleSheet(u"border: none;")
        self.label_frames.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_6.addWidget(self.label_frames)

        self.combo_frames = MyQCombo(self.w_Nit)
        self.combo_frames.addItem("")
        self.combo_frames.addItem("")
        self.combo_frames.addItem("")
        self.combo_frames.setObjectName(u"combo_frames")
        sizePolicy.setHeightForWidth(self.combo_frames.sizePolicy().hasHeightForWidth())
        self.combo_frames.setSizePolicy(sizePolicy)
        self.combo_frames.setMinimumSize(QSize(130, 24))
        self.combo_frames.setMaximumSize(QSize(180, 24))
        self.combo_frames.setFont(font)
        self.combo_frames.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContentsOnFirstShow)

        self.horizontalLayout_6.addWidget(self.combo_frames)

        self.hs_Nit = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_6.addItem(self.hs_Nit)


        self.verticalLayout_24.addWidget(self.w_Nit)


        self.verticalLayout_10.addWidget(self.CollapBox_FinIt)

        self.CollapBox_Interp = CollapsibleBox(self.scrollAreaWidgetContents)
        self.CollapBox_Interp.setObjectName(u"CollapBox_Interp")
        sizePolicy.setHeightForWidth(self.CollapBox_Interp.sizePolicy().hasHeightForWidth())
        self.CollapBox_Interp.setSizePolicy(sizePolicy)
        self.CollapBox_Interp.setMinimumSize(QSize(0, 80))
        self.CollapBox_Interp.setMaximumSize(QSize(16777215, 80))
        self.verticalLayout_11 = QVBoxLayout(self.CollapBox_Interp)
        self.verticalLayout_11.setSpacing(0)
        self.verticalLayout_11.setObjectName(u"verticalLayout_11")
        self.verticalLayout_11.setContentsMargins(0, 0, 0, 0)
        self.lay_CollapBox_Interp = QHBoxLayout()
        self.lay_CollapBox_Interp.setSpacing(0)
        self.lay_CollapBox_Interp.setObjectName(u"lay_CollapBox_Interp")
        self.lay_CollapBox_Interp.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.tool_CollapBox_Interp = QToolButton(self.CollapBox_Interp)
        self.tool_CollapBox_Interp.setObjectName(u"tool_CollapBox_Interp")
        sizePolicy2.setHeightForWidth(self.tool_CollapBox_Interp.sizePolicy().hasHeightForWidth())
        self.tool_CollapBox_Interp.setSizePolicy(sizePolicy2)
        self.tool_CollapBox_Interp.setMinimumSize(QSize(0, 20))
        self.tool_CollapBox_Interp.setMaximumSize(QSize(16777215, 20))
        self.tool_CollapBox_Interp.setFont(font3)
        self.tool_CollapBox_Interp.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.tool_CollapBox_Interp.setStyleSheet(u"QToolButton { border: none; }")
        self.tool_CollapBox_Interp.setCheckable(True)
        self.tool_CollapBox_Interp.setChecked(True)
        self.tool_CollapBox_Interp.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.tool_CollapBox_Interp.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.tool_CollapBox_Interp.setArrowType(Qt.ArrowType.DownArrow)

        self.lay_CollapBox_Interp.addWidget(self.tool_CollapBox_Interp)

        self.hsp_CollapBox_Interp = QSpacerItem(100, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.lay_CollapBox_Interp.addItem(self.hsp_CollapBox_Interp)

        self.button_CollapBox_Interp = MyToolButton(self.CollapBox_Interp)
        self.button_CollapBox_Interp.setObjectName(u"button_CollapBox_Interp")
        self.button_CollapBox_Interp.setMinimumSize(QSize(18, 18))
        self.button_CollapBox_Interp.setMaximumSize(QSize(18, 18))
        self.button_CollapBox_Interp.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.button_CollapBox_Interp.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.button_CollapBox_Interp.setIcon(icon2)
        self.button_CollapBox_Interp.setIconSize(QSize(12, 12))

        self.lay_CollapBox_Interp.addWidget(self.button_CollapBox_Interp)


        self.verticalLayout_11.addLayout(self.lay_CollapBox_Interp)

        self.group_int = QGroupBox(self.CollapBox_Interp)
        self.group_int.setObjectName(u"group_int")
        sizePolicy1.setHeightForWidth(self.group_int.sizePolicy().hasHeightForWidth())
        self.group_int.setSizePolicy(sizePolicy1)
        self.group_int.setMinimumSize(QSize(0, 60))
        font6 = QFont()
        font6.setPointSize(10)
        font6.setBold(True)
        font6.setItalic(False)
        self.group_int.setFont(font6)
        self.group_int.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.group_int.setStyleSheet(u"QGroupBox{border: 1px solid gray; border-radius: 6px;}")
        self.group_int.setCheckable(False)
        self.gridLayout_4 = QGridLayout(self.group_int)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.gridLayout_4.setHorizontalSpacing(0)
        self.gridLayout_4.setVerticalSpacing(6)
        self.gridLayout_4.setContentsMargins(6, 6, 6, 10)
        self.w_ImInt = QWidget(self.group_int)
        self.w_ImInt.setObjectName(u"w_ImInt")
        self.w_ImInt.setMinimumSize(QSize(0, 44))
        self.w_ImInt.setMaximumSize(QSize(16777215, 44))
        self.verticalLayout_43 = QVBoxLayout(self.w_ImInt)
        self.verticalLayout_43.setSpacing(0)
        self.verticalLayout_43.setObjectName(u"verticalLayout_43")
        self.verticalLayout_43.setContentsMargins(0, 0, 0, 0)
        self.w_label_imint = QWidget(self.w_ImInt)
        self.w_label_imint.setObjectName(u"w_label_imint")
        self.w_label_imint.setMinimumSize(QSize(0, 20))
        self.w_label_imint.setMaximumSize(QSize(16777215, 20))
        self.hlay_ImInt = QHBoxLayout(self.w_label_imint)
        self.hlay_ImInt.setSpacing(0)
        self.hlay_ImInt.setObjectName(u"hlay_ImInt")
        self.hlay_ImInt.setContentsMargins(0, 0, 0, 0)
        self.label_imint = QLabel(self.w_label_imint)
        self.label_imint.setObjectName(u"label_imint")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.label_imint.sizePolicy().hasHeightForWidth())
        self.label_imint.setSizePolicy(sizePolicy3)
        self.label_imint.setMinimumSize(QSize(200, 20))
        self.label_imint.setMaximumSize(QSize(16777215, 20))
        self.label_imint.setFont(font5)

        self.hlay_ImInt.addWidget(self.label_imint)


        self.verticalLayout_43.addWidget(self.w_label_imint)

        self.combo_ImInt = MyQCombo(self.w_ImInt)
        self.combo_ImInt.addItem("")
        self.combo_ImInt.addItem("")
        self.combo_ImInt.addItem("")
        self.combo_ImInt.addItem("")
        self.combo_ImInt.addItem("")
        self.combo_ImInt.addItem("")
        self.combo_ImInt.addItem("")
        self.combo_ImInt.addItem("")
        self.combo_ImInt.setObjectName(u"combo_ImInt")
        sizePolicy.setHeightForWidth(self.combo_ImInt.sizePolicy().hasHeightForWidth())
        self.combo_ImInt.setSizePolicy(sizePolicy)
        self.combo_ImInt.setMinimumSize(QSize(250, 24))
        self.combo_ImInt.setMaximumSize(QSize(16777215, 24))
        self.combo_ImInt.setFont(font)
        self.combo_ImInt.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContentsOnFirstShow)

        self.verticalLayout_43.addWidget(self.combo_ImInt)


        self.gridLayout_4.addWidget(self.w_ImInt, 0, 0, 1, 1)

        self.w_ImInt_par = QStackedWidget(self.group_int)
        self.w_ImInt_par.setObjectName(u"w_ImInt_par")
        self.w_ImInt_par.setMaximumSize(QSize(16777215, 44))
        self.w_ImInt_par_none = QWidget()
        self.w_ImInt_par_none.setObjectName(u"w_ImInt_par_none")
        self.w_ImInt_par.addWidget(self.w_ImInt_par_none)
        self.w_ImInt_par_imshift = QWidget()
        self.w_ImInt_par_imshift.setObjectName(u"w_ImInt_par_imshift")
        self.w_ImInt_par_imshift.setMinimumSize(QSize(0, 44))
        self.w_ImInt_par_imshift.setMaximumSize(QSize(16777215, 44))
        self.verticalLayout_39 = QVBoxLayout(self.w_ImInt_par_imshift)
        self.verticalLayout_39.setSpacing(0)
        self.verticalLayout_39.setObjectName(u"verticalLayout_39")
        self.verticalLayout_39.setContentsMargins(0, 0, 0, 0)
        self.label_par_imshift = QLabel(self.w_ImInt_par_imshift)
        self.label_par_imshift.setObjectName(u"label_par_imshift")
        self.label_par_imshift.setMinimumSize(QSize(0, 20))
        self.label_par_imshift.setMaximumSize(QSize(16777215, 20))
        self.label_par_imshift.setFont(font5)

        self.verticalLayout_39.addWidget(self.label_par_imshift)

        self.combo_par_imshift = MyQCombo(self.w_ImInt_par_imshift)
        self.combo_par_imshift.addItem("")
        self.combo_par_imshift.addItem("")
        self.combo_par_imshift.setObjectName(u"combo_par_imshift")
        sizePolicy3.setHeightForWidth(self.combo_par_imshift.sizePolicy().hasHeightForWidth())
        self.combo_par_imshift.setSizePolicy(sizePolicy3)
        self.combo_par_imshift.setMinimumSize(QSize(0, 24))
        self.combo_par_imshift.setMaximumSize(QSize(16777215, 24))
        self.combo_par_imshift.setFont(font)

        self.verticalLayout_39.addWidget(self.combo_par_imshift)

        self.w_ImInt_par.addWidget(self.w_ImInt_par_imshift)
        self.w_ImInt_par_pol = QWidget()
        self.w_ImInt_par_pol.setObjectName(u"w_ImInt_par_pol")
        self.w_ImInt_par_pol.setMinimumSize(QSize(0, 44))
        self.w_ImInt_par_pol.setMaximumSize(QSize(16777215, 44))
        self.verticalLayout_40 = QVBoxLayout(self.w_ImInt_par_pol)
        self.verticalLayout_40.setSpacing(0)
        self.verticalLayout_40.setObjectName(u"verticalLayout_40")
        self.verticalLayout_40.setContentsMargins(0, 0, 0, 0)
        self.label_par_pol = QLabel(self.w_ImInt_par_pol)
        self.label_par_pol.setObjectName(u"label_par_pol")
        self.label_par_pol.setMaximumSize(QSize(16777215, 20))
        self.label_par_pol.setFont(font5)

        self.verticalLayout_40.addWidget(self.label_par_pol)

        self.combo_par_pol = MyQCombo(self.w_ImInt_par_pol)
        self.combo_par_pol.addItem("")
        self.combo_par_pol.addItem("")
        self.combo_par_pol.addItem("")
        self.combo_par_pol.addItem("")
        self.combo_par_pol.setObjectName(u"combo_par_pol")
        sizePolicy3.setHeightForWidth(self.combo_par_pol.sizePolicy().hasHeightForWidth())
        self.combo_par_pol.setSizePolicy(sizePolicy3)
        self.combo_par_pol.setMinimumSize(QSize(0, 24))
        self.combo_par_pol.setMaximumSize(QSize(16777215, 24))
        self.combo_par_pol.setFont(font)

        self.verticalLayout_40.addWidget(self.combo_par_pol)

        self.w_ImInt_par.addWidget(self.w_ImInt_par_pol)
        self.w_ImInt_order = QWidget()
        self.w_ImInt_order.setObjectName(u"w_ImInt_order")
        self.w_ImInt_order.setMinimumSize(QSize(0, 44))
        self.w_ImInt_order.setMaximumSize(QSize(16777215, 44))
        self.verticalLayout_41 = QVBoxLayout(self.w_ImInt_order)
        self.verticalLayout_41.setSpacing(0)
        self.verticalLayout_41.setObjectName(u"verticalLayout_41")
        self.verticalLayout_41.setContentsMargins(0, 0, 0, 0)
        self.label_par_order = QLabel(self.w_ImInt_order)
        self.label_par_order.setObjectName(u"label_par_order")
        self.label_par_order.setMaximumSize(QSize(16777215, 20))
        self.label_par_order.setFont(font5)

        self.verticalLayout_41.addWidget(self.label_par_order)

        self.spin_order = MyQSpin(self.w_ImInt_order)
        self.spin_order.setObjectName(u"spin_order")
        self.spin_order.setMinimumSize(QSize(0, 24))
        self.spin_order.setMaximumSize(QSize(16777215, 24))
        self.spin_order.setFont(font)
        self.spin_order.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_order.setValue(3)

        self.verticalLayout_41.addWidget(self.spin_order)

        self.w_ImInt_par.addWidget(self.w_ImInt_order)

        self.gridLayout_4.addWidget(self.w_ImInt_par, 0, 2, 1, 1)

        self.hs_ImInt_2 = QSpacerItem(12, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.gridLayout_4.addItem(self.hs_ImInt_2, 0, 1, 1, 1)

        self.gridLayout_4.setColumnStretch(0, 3)

        self.verticalLayout_11.addWidget(self.group_int)


        self.verticalLayout_10.addWidget(self.CollapBox_Interp)

        self.CollapBox_Windowing = CollapsibleBox(self.scrollAreaWidgetContents)
        self.CollapBox_Windowing.setObjectName(u"CollapBox_Windowing")
        sizePolicy.setHeightForWidth(self.CollapBox_Windowing.sizePolicy().hasHeightForWidth())
        self.CollapBox_Windowing.setSizePolicy(sizePolicy)
        self.CollapBox_Windowing.setMinimumSize(QSize(0, 130))
        self.CollapBox_Windowing.setMaximumSize(QSize(16777215, 130))
        self.verticalLayout_12 = QVBoxLayout(self.CollapBox_Windowing)
        self.verticalLayout_12.setSpacing(0)
        self.verticalLayout_12.setObjectName(u"verticalLayout_12")
        self.verticalLayout_12.setContentsMargins(0, 0, 0, 0)
        self.lay_CollapBox_Interp_2 = QHBoxLayout()
        self.lay_CollapBox_Interp_2.setSpacing(0)
        self.lay_CollapBox_Interp_2.setObjectName(u"lay_CollapBox_Interp_2")
        self.lay_CollapBox_Interp_2.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.tool_CollapBox_Interp_2 = QToolButton(self.CollapBox_Windowing)
        self.tool_CollapBox_Interp_2.setObjectName(u"tool_CollapBox_Interp_2")
        sizePolicy2.setHeightForWidth(self.tool_CollapBox_Interp_2.sizePolicy().hasHeightForWidth())
        self.tool_CollapBox_Interp_2.setSizePolicy(sizePolicy2)
        self.tool_CollapBox_Interp_2.setMinimumSize(QSize(0, 20))
        self.tool_CollapBox_Interp_2.setMaximumSize(QSize(16777215, 20))
        self.tool_CollapBox_Interp_2.setFont(font3)
        self.tool_CollapBox_Interp_2.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.tool_CollapBox_Interp_2.setStyleSheet(u"QToolButton { border: none; }")
        self.tool_CollapBox_Interp_2.setCheckable(True)
        self.tool_CollapBox_Interp_2.setChecked(True)
        self.tool_CollapBox_Interp_2.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.tool_CollapBox_Interp_2.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.tool_CollapBox_Interp_2.setArrowType(Qt.ArrowType.DownArrow)

        self.lay_CollapBox_Interp_2.addWidget(self.tool_CollapBox_Interp_2)

        self.hsp_CollapBox_Interp_2 = QSpacerItem(100, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.lay_CollapBox_Interp_2.addItem(self.hsp_CollapBox_Interp_2)

        self.button_CollapBox_Interp_2 = MyToolButton(self.CollapBox_Windowing)
        self.button_CollapBox_Interp_2.setObjectName(u"button_CollapBox_Interp_2")
        self.button_CollapBox_Interp_2.setMinimumSize(QSize(18, 18))
        self.button_CollapBox_Interp_2.setMaximumSize(QSize(18, 18))
        self.button_CollapBox_Interp_2.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.button_CollapBox_Interp_2.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.button_CollapBox_Interp_2.setIcon(icon2)
        self.button_CollapBox_Interp_2.setIconSize(QSize(12, 12))

        self.lay_CollapBox_Interp_2.addWidget(self.button_CollapBox_Interp_2)


        self.verticalLayout_12.addLayout(self.lay_CollapBox_Interp_2)

        self.group_int_2 = QGroupBox(self.CollapBox_Windowing)
        self.group_int_2.setObjectName(u"group_int_2")
        sizePolicy1.setHeightForWidth(self.group_int_2.sizePolicy().hasHeightForWidth())
        self.group_int_2.setSizePolicy(sizePolicy1)
        self.group_int_2.setMinimumSize(QSize(0, 110))
        self.group_int_2.setFont(font6)
        self.group_int_2.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.group_int_2.setStyleSheet(u"QGroupBox{border: 1px solid gray; border-radius: 6px;}")
        self.group_int_2.setCheckable(False)
        self.verticalLayout = QVBoxLayout(self.group_int_2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(6, 6, 6, 10)
        self.w_IW = QWidget(self.group_int_2)
        self.w_IW.setObjectName(u"w_IW")
        self.w_IW.setMinimumSize(QSize(0, 26))
        self.horizontalLayout_22 = QHBoxLayout(self.w_IW)
        self.horizontalLayout_22.setSpacing(5)
        self.horizontalLayout_22.setObjectName(u"horizontalLayout_22")
        self.horizontalLayout_22.setContentsMargins(0, 1, 0, 1)
        self.label_MinVal_2 = QLabel(self.w_IW)
        self.label_MinVal_2.setObjectName(u"label_MinVal_2")
        sizePolicy3.setHeightForWidth(self.label_MinVal_2.sizePolicy().hasHeightForWidth())
        self.label_MinVal_2.setSizePolicy(sizePolicy3)
        self.label_MinVal_2.setMinimumSize(QSize(0, 20))
        self.label_MinVal_2.setMaximumSize(QSize(16777215, 20))
        self.label_MinVal_2.setFont(font5)
        self.label_MinVal_2.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_22.addWidget(self.label_MinVal_2)

        self.edit_IW = QWidget(self.w_IW)
        self.edit_IW.setObjectName(u"edit_IW")
        self.edit_IW.setMinimumSize(QSize(0, 0))
        self.edit_IW.setMaximumSize(QSize(16777215, 22))
        self.horizontalLayout_23 = QHBoxLayout(self.edit_IW)
        self.horizontalLayout_23.setSpacing(0)
        self.horizontalLayout_23.setObjectName(u"horizontalLayout_23")
        self.horizontalLayout_23.setContentsMargins(0, 0, 0, 0)
        self.line_edit_IW = MyQLineEditNumber(self.edit_IW)
        self.line_edit_IW.setObjectName(u"line_edit_IW")
        self.line_edit_IW.setMinimumSize(QSize(200, 0))
        self.line_edit_IW.setMaximumSize(QSize(16777215, 22))
        self.line_edit_IW.setFont(font)
        self.line_edit_IW.setStyleSheet(u"border-top: 1px solid gray;\n"
"border-left: 1px solid gray;\n"
"border-bottom: 1px solid gray;\n"
"\n"
"\n"
"")

        self.horizontalLayout_23.addWidget(self.line_edit_IW)

        self.check_edit_IW = ClickableEditLabel(self.edit_IW)
        self.check_edit_IW.setObjectName(u"check_edit_IW")
        self.check_edit_IW.setMinimumSize(QSize(22, 22))
        self.check_edit_IW.setMaximumSize(QSize(22, 22))
        self.check_edit_IW.setStyleSheet(u"border-top: 1px solid gray;\n"
"border-right: 1px solid gray;\n"
"border-bottom: 1px solid gray;\n"
"padding: 2px;")
        self.check_edit_IW.setPixmap(QPixmap(u""+ icons_path +"greenv.png"))
        self.check_edit_IW.setScaledContents(True)
        self.check_edit_IW.setMargin(0)
        self.check_edit_IW.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)

        self.horizontalLayout_23.addWidget(self.check_edit_IW)


        self.horizontalLayout_22.addWidget(self.edit_IW)

        self.horizontalSpacer = QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_22.addItem(self.horizontalSpacer)


        self.verticalLayout.addWidget(self.w_IW)

        self.w_Correlation = QWidget(self.group_int_2)
        self.w_Correlation.setObjectName(u"w_Correlation")
        self.horizontalLayout = QHBoxLayout(self.w_Correlation)
        self.horizontalLayout.setSpacing(10)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.w_SemiWidth_Epipolar = QWidget(self.w_Correlation)
        self.w_SemiWidth_Epipolar.setObjectName(u"w_SemiWidth_Epipolar")
        self.w_SemiWidth_Epipolar.setMinimumSize(QSize(150, 44))
        self.w_SemiWidth_Epipolar.setMaximumSize(QSize(150, 44))
        self.verticalLayout_15 = QVBoxLayout(self.w_SemiWidth_Epipolar)
        self.verticalLayout_15.setSpacing(0)
        self.verticalLayout_15.setObjectName(u"verticalLayout_15")
        self.verticalLayout_15.setContentsMargins(0, 0, 0, 0)
        self.label_SemiWidth_Epipolar = QLabel(self.w_SemiWidth_Epipolar)
        self.label_SemiWidth_Epipolar.setObjectName(u"label_SemiWidth_Epipolar")
        sizePolicy3.setHeightForWidth(self.label_SemiWidth_Epipolar.sizePolicy().hasHeightForWidth())
        self.label_SemiWidth_Epipolar.setSizePolicy(sizePolicy3)
        self.label_SemiWidth_Epipolar.setMinimumSize(QSize(55, 20))
        self.label_SemiWidth_Epipolar.setMaximumSize(QSize(16777215, 20))
        self.label_SemiWidth_Epipolar.setFont(font5)
        self.label_SemiWidth_Epipolar.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout_15.addWidget(self.label_SemiWidth_Epipolar)

        self.spin_SemiWidth_Epipolar = MyQSpin(self.w_SemiWidth_Epipolar)
        self.spin_SemiWidth_Epipolar.setObjectName(u"spin_SemiWidth_Epipolar")
        self.spin_SemiWidth_Epipolar.setEnabled(True)
        self.spin_SemiWidth_Epipolar.setMinimumSize(QSize(55, 24))
        self.spin_SemiWidth_Epipolar.setMaximumSize(QSize(1000000, 24))
        self.spin_SemiWidth_Epipolar.setFont(font)
        self.spin_SemiWidth_Epipolar.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.spin_SemiWidth_Epipolar.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_SemiWidth_Epipolar.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
        self.spin_SemiWidth_Epipolar.setMinimum(1)
        self.spin_SemiWidth_Epipolar.setValue(40)

        self.verticalLayout_15.addWidget(self.spin_SemiWidth_Epipolar)


        self.horizontalLayout.addWidget(self.w_SemiWidth_Epipolar)

        self.w_Filter_SemiWidth = QWidget(self.w_Correlation)
        self.w_Filter_SemiWidth.setObjectName(u"w_Filter_SemiWidth")
        self.w_Filter_SemiWidth.setMinimumSize(QSize(120, 44))
        self.w_Filter_SemiWidth.setMaximumSize(QSize(120, 44))
        self.verticalLayout_16 = QVBoxLayout(self.w_Filter_SemiWidth)
        self.verticalLayout_16.setSpacing(0)
        self.verticalLayout_16.setObjectName(u"verticalLayout_16")
        self.verticalLayout_16.setContentsMargins(0, 0, 0, 0)
        self.label_Filter_SemiWidth = QLabel(self.w_Filter_SemiWidth)
        self.label_Filter_SemiWidth.setObjectName(u"label_Filter_SemiWidth")
        sizePolicy3.setHeightForWidth(self.label_Filter_SemiWidth.sizePolicy().hasHeightForWidth())
        self.label_Filter_SemiWidth.setSizePolicy(sizePolicy3)
        self.label_Filter_SemiWidth.setMinimumSize(QSize(55, 20))
        self.label_Filter_SemiWidth.setMaximumSize(QSize(16777215, 20))
        self.label_Filter_SemiWidth.setFont(font5)
        self.label_Filter_SemiWidth.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout_16.addWidget(self.label_Filter_SemiWidth)

        self.spin_Filter_SemiWidth = MyQSpin(self.w_Filter_SemiWidth)
        self.spin_Filter_SemiWidth.setObjectName(u"spin_Filter_SemiWidth")
        self.spin_Filter_SemiWidth.setEnabled(True)
        self.spin_Filter_SemiWidth.setMinimumSize(QSize(55, 24))
        self.spin_Filter_SemiWidth.setMaximumSize(QSize(1000000, 24))
        self.spin_Filter_SemiWidth.setFont(font)
        self.spin_Filter_SemiWidth.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.spin_Filter_SemiWidth.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_Filter_SemiWidth.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
        self.spin_Filter_SemiWidth.setValue(9)

        self.verticalLayout_16.addWidget(self.spin_Filter_SemiWidth)


        self.horizontalLayout.addWidget(self.w_Filter_SemiWidth)

        self.w_Threshold = QWidget(self.w_Correlation)
        self.w_Threshold.setObjectName(u"w_Threshold")
        self.w_Threshold.setMinimumSize(QSize(120, 44))
        self.w_Threshold.setMaximumSize(QSize(120, 44))
        self.verticalLayout_17 = QVBoxLayout(self.w_Threshold)
        self.verticalLayout_17.setSpacing(0)
        self.verticalLayout_17.setObjectName(u"verticalLayout_17")
        self.verticalLayout_17.setContentsMargins(0, 0, 0, 0)
        self.label_Threshold = QLabel(self.w_Threshold)
        self.label_Threshold.setObjectName(u"label_Threshold")
        sizePolicy3.setHeightForWidth(self.label_Threshold.sizePolicy().hasHeightForWidth())
        self.label_Threshold.setSizePolicy(sizePolicy3)
        self.label_Threshold.setMinimumSize(QSize(55, 20))
        self.label_Threshold.setMaximumSize(QSize(16777215, 20))
        self.label_Threshold.setFont(font5)
        self.label_Threshold.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout_17.addWidget(self.label_Threshold)

        self.spin_Threshold = MyQDoubleSpin(self.w_Threshold)
        self.spin_Threshold.setObjectName(u"spin_Threshold")
        self.spin_Threshold.setEnabled(True)
        self.spin_Threshold.setMinimumSize(QSize(55, 24))
        self.spin_Threshold.setMaximumSize(QSize(1000000, 24))
        self.spin_Threshold.setFont(font)
        self.spin_Threshold.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.spin_Threshold.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_Threshold.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
        self.spin_Threshold.setMaximum(1.000000000000000)
        self.spin_Threshold.setSingleStep(0.010000000000000)
        self.spin_Threshold.setValue(0.500000000000000)

        self.verticalLayout_17.addWidget(self.spin_Threshold)


        self.horizontalLayout.addWidget(self.w_Threshold)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)


        self.verticalLayout.addWidget(self.w_Correlation)


        self.verticalLayout_12.addWidget(self.group_int_2)


        self.verticalLayout_10.addWidget(self.CollapBox_Windowing)

        self.CollapBox_Validation = CollapsibleBox(self.scrollAreaWidgetContents)
        self.CollapBox_Validation.setObjectName(u"CollapBox_Validation")
        sizePolicy.setHeightForWidth(self.CollapBox_Validation.sizePolicy().hasHeightForWidth())
        self.CollapBox_Validation.setSizePolicy(sizePolicy)
        self.CollapBox_Validation.setMinimumSize(QSize(0, 80))
        self.CollapBox_Validation.setMaximumSize(QSize(16777215, 80))
        self.verticalLayout_13 = QVBoxLayout(self.CollapBox_Validation)
        self.verticalLayout_13.setSpacing(0)
        self.verticalLayout_13.setObjectName(u"verticalLayout_13")
        self.verticalLayout_13.setContentsMargins(0, 0, 0, 0)
        self.lay_CollapBox_Interp_3 = QHBoxLayout()
        self.lay_CollapBox_Interp_3.setSpacing(0)
        self.lay_CollapBox_Interp_3.setObjectName(u"lay_CollapBox_Interp_3")
        self.lay_CollapBox_Interp_3.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.tool_CollapBox_Interp_3 = QToolButton(self.CollapBox_Validation)
        self.tool_CollapBox_Interp_3.setObjectName(u"tool_CollapBox_Interp_3")
        sizePolicy2.setHeightForWidth(self.tool_CollapBox_Interp_3.sizePolicy().hasHeightForWidth())
        self.tool_CollapBox_Interp_3.setSizePolicy(sizePolicy2)
        self.tool_CollapBox_Interp_3.setMinimumSize(QSize(0, 20))
        self.tool_CollapBox_Interp_3.setMaximumSize(QSize(16777215, 20))
        self.tool_CollapBox_Interp_3.setFont(font3)
        self.tool_CollapBox_Interp_3.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.tool_CollapBox_Interp_3.setStyleSheet(u"QToolButton { border: none; }")
        self.tool_CollapBox_Interp_3.setCheckable(True)
        self.tool_CollapBox_Interp_3.setChecked(True)
        self.tool_CollapBox_Interp_3.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.tool_CollapBox_Interp_3.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.tool_CollapBox_Interp_3.setArrowType(Qt.ArrowType.DownArrow)

        self.lay_CollapBox_Interp_3.addWidget(self.tool_CollapBox_Interp_3)

        self.hsp_CollapBox_Interp_3 = QSpacerItem(100, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.lay_CollapBox_Interp_3.addItem(self.hsp_CollapBox_Interp_3)

        self.button_CollapBox_Interp_3 = MyToolButton(self.CollapBox_Validation)
        self.button_CollapBox_Interp_3.setObjectName(u"button_CollapBox_Interp_3")
        self.button_CollapBox_Interp_3.setMinimumSize(QSize(18, 18))
        self.button_CollapBox_Interp_3.setMaximumSize(QSize(18, 18))
        self.button_CollapBox_Interp_3.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.button_CollapBox_Interp_3.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.button_CollapBox_Interp_3.setIcon(icon2)
        self.button_CollapBox_Interp_3.setIconSize(QSize(12, 12))

        self.lay_CollapBox_Interp_3.addWidget(self.button_CollapBox_Interp_3)


        self.verticalLayout_13.addLayout(self.lay_CollapBox_Interp_3)

        self.group_Validation = QGroupBox(self.CollapBox_Validation)
        self.group_Validation.setObjectName(u"group_Validation")
        sizePolicy1.setHeightForWidth(self.group_Validation.sizePolicy().hasHeightForWidth())
        self.group_Validation.setSizePolicy(sizePolicy1)
        self.group_Validation.setMinimumSize(QSize(0, 60))
        self.group_Validation.setMaximumSize(QSize(16777215, 60))
        self.group_Validation.setFont(font6)
        self.group_Validation.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.group_Validation.setStyleSheet(u"QGroupBox{border: 1px solid gray; border-radius: 6px;}")
        self.group_Validation.setCheckable(False)
        self.verticalLayout_2 = QVBoxLayout(self.group_Validation)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(6, 6, 6, 10)
        self.w_Validation = QWidget(self.group_Validation)
        self.w_Validation.setObjectName(u"w_Validation")
        self.horizontalLayout_3 = QHBoxLayout(self.w_Validation)
        self.horizontalLayout_3.setSpacing(10)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.w_Nit_OutDet = QWidget(self.w_Validation)
        self.w_Nit_OutDet.setObjectName(u"w_Nit_OutDet")
        self.w_Nit_OutDet.setMinimumSize(QSize(150, 44))
        self.w_Nit_OutDet.setMaximumSize(QSize(150, 44))
        self.verticalLayout_18 = QVBoxLayout(self.w_Nit_OutDet)
        self.verticalLayout_18.setSpacing(0)
        self.verticalLayout_18.setObjectName(u"verticalLayout_18")
        self.verticalLayout_18.setContentsMargins(0, 0, 0, 0)
        self.label_Nit_OutDet = QLabel(self.w_Nit_OutDet)
        self.label_Nit_OutDet.setObjectName(u"label_Nit_OutDet")
        sizePolicy3.setHeightForWidth(self.label_Nit_OutDet.sizePolicy().hasHeightForWidth())
        self.label_Nit_OutDet.setSizePolicy(sizePolicy3)
        self.label_Nit_OutDet.setMinimumSize(QSize(55, 20))
        self.label_Nit_OutDet.setMaximumSize(QSize(16777215, 20))
        self.label_Nit_OutDet.setFont(font5)
        self.label_Nit_OutDet.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout_18.addWidget(self.label_Nit_OutDet)

        self.spin_Nit_OutDet = MyQSpin(self.w_Nit_OutDet)
        self.spin_Nit_OutDet.setObjectName(u"spin_Nit_OutDet")
        self.spin_Nit_OutDet.setEnabled(True)
        self.spin_Nit_OutDet.setMinimumSize(QSize(55, 24))
        self.spin_Nit_OutDet.setMaximumSize(QSize(1000000, 24))
        self.spin_Nit_OutDet.setFont(font)
        self.spin_Nit_OutDet.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.spin_Nit_OutDet.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_Nit_OutDet.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
        self.spin_Nit_OutDet.setMinimum(0)
        self.spin_Nit_OutDet.setValue(5)

        self.verticalLayout_18.addWidget(self.spin_Nit_OutDet)


        self.horizontalLayout_3.addWidget(self.w_Nit_OutDet)

        self.w_Std_Threshold = QWidget(self.w_Validation)
        self.w_Std_Threshold.setObjectName(u"w_Std_Threshold")
        self.w_Std_Threshold.setMinimumSize(QSize(120, 44))
        self.w_Std_Threshold.setMaximumSize(QSize(120, 44))
        self.verticalLayout_19 = QVBoxLayout(self.w_Std_Threshold)
        self.verticalLayout_19.setSpacing(0)
        self.verticalLayout_19.setObjectName(u"verticalLayout_19")
        self.verticalLayout_19.setContentsMargins(0, 0, 0, 0)
        self.label_Std_Threshold = QLabel(self.w_Std_Threshold)
        self.label_Std_Threshold.setObjectName(u"label_Std_Threshold")
        sizePolicy3.setHeightForWidth(self.label_Std_Threshold.sizePolicy().hasHeightForWidth())
        self.label_Std_Threshold.setSizePolicy(sizePolicy3)
        self.label_Std_Threshold.setMinimumSize(QSize(55, 20))
        self.label_Std_Threshold.setMaximumSize(QSize(16777215, 20))
        self.label_Std_Threshold.setFont(font5)
        self.label_Std_Threshold.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout_19.addWidget(self.label_Std_Threshold)

        self.spin_Std_Threshold = MyQDoubleSpin(self.w_Std_Threshold)
        self.spin_Std_Threshold.setObjectName(u"spin_Std_Threshold")
        self.spin_Std_Threshold.setEnabled(True)
        self.spin_Std_Threshold.setMinimumSize(QSize(55, 24))
        self.spin_Std_Threshold.setMaximumSize(QSize(1000000, 24))
        self.spin_Std_Threshold.setFont(font)
        self.spin_Std_Threshold.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.spin_Std_Threshold.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_Std_Threshold.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
        self.spin_Std_Threshold.setMaximum(1000.000000000000000)
        self.spin_Std_Threshold.setSingleStep(0.010000000000000)
        self.spin_Std_Threshold.setValue(3.000000000000000)

        self.verticalLayout_19.addWidget(self.spin_Std_Threshold)


        self.horizontalLayout_3.addWidget(self.w_Std_Threshold)

        self.hs_Validation = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.hs_Validation)


        self.verticalLayout_2.addWidget(self.w_Validation)


        self.verticalLayout_13.addWidget(self.group_Validation)


        self.verticalLayout_10.addWidget(self.CollapBox_Validation)

        self.verticalSpacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_10.addItem(self.verticalSpacer)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout_65.addWidget(self.scrollArea)

        QWidget.setTabOrder(self.button_back, self.button_forward)
        QWidget.setTabOrder(self.button_forward, self.button_close_tab)
        QWidget.setTabOrder(self.button_close_tab, self.scrollArea)

        self.retranslateUi(ProcessTab_Disp)

        self.w_ImInt_par.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(ProcessTab_Disp)
    # setupUi

    def retranslateUi(self, ProcessTab_Disp):
        ProcessTab_Disp.setWindowTitle(QCoreApplication.translate("ProcessTab_Disp", u"Process", None))
        self.icon.setText("")
        self.name_tab.setText(QCoreApplication.translate("ProcessTab_Disp", u" Process", None))
        self.label_number.setText(QCoreApplication.translate("ProcessTab_Disp", u"1", None))
#if QT_CONFIG(tooltip)
        self.button_back.setToolTip(QCoreApplication.translate("ProcessTab_Disp", u"Undo", None))
#endif // QT_CONFIG(tooltip)
        self.button_back.setText("")
#if QT_CONFIG(tooltip)
        self.button_forward.setToolTip(QCoreApplication.translate("ProcessTab_Disp", u"Redo", None))
#endif // QT_CONFIG(tooltip)
        self.button_forward.setText("")
#if QT_CONFIG(tooltip)
        self.button_close_tab.setToolTip(QCoreApplication.translate("ProcessTab_Disp", u"Close tab", None))
#endif // QT_CONFIG(tooltip)
        self.button_close_tab.setText("")
#if QT_CONFIG(shortcut)
        self.button_close_tab.setShortcut(QCoreApplication.translate("ProcessTab_Disp", u"Alt+P", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(tooltip)
        self.tool_CollapBox_FinIt.setToolTip(QCoreApplication.translate("ProcessTab_Disp", u"Iterations option box", None))
#endif // QT_CONFIG(tooltip)
        self.tool_CollapBox_FinIt.setText(QCoreApplication.translate("ProcessTab_Disp", u"Iterations", None))
#if QT_CONFIG(tooltip)
        self.button_CollapBox_FinIt.setToolTip(QCoreApplication.translate("ProcessTab_Disp", u"Set default options for the selected type of process", None))
#endif // QT_CONFIG(tooltip)
        self.button_CollapBox_FinIt.setText("")
        self.label_Nit.setText(QCoreApplication.translate("ProcessTab_Disp", u"# of iterations: ", None))
#if QT_CONFIG(tooltip)
        self.spin_Nit.setToolTip(QCoreApplication.translate("ProcessTab_Disp", u"Number of final iterations (sizes and spacing from the last element in the above fields)", None))
#endif // QT_CONFIG(tooltip)
        self.label_frames.setText(QCoreApplication.translate("ProcessTab_Disp", u"use: ", None))
        self.combo_frames.setItemText(0, QCoreApplication.translate("ProcessTab_Disp", u"both frames", None))
        self.combo_frames.setItemText(1, QCoreApplication.translate("ProcessTab_Disp", u"frame 1", None))
        self.combo_frames.setItemText(2, QCoreApplication.translate("ProcessTab_Disp", u"frame 2", None))

#if QT_CONFIG(tooltip)
        self.combo_frames.setToolTip(QCoreApplication.translate("ProcessTab_Disp", u"Type of interpolation for image deformation method", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.tool_CollapBox_Interp.setToolTip(QCoreApplication.translate("ProcessTab_Disp", u"Interpolation option box", None))
#endif // QT_CONFIG(tooltip)
        self.tool_CollapBox_Interp.setText(QCoreApplication.translate("ProcessTab_Disp", u"Interpolation", None))
#if QT_CONFIG(tooltip)
        self.button_CollapBox_Interp.setToolTip(QCoreApplication.translate("ProcessTab_Disp", u"Set default options for the selected type of process", None))
#endif // QT_CONFIG(tooltip)
        self.button_CollapBox_Interp.setText("")
        self.group_int.setTitle("")
        self.label_imint.setText(QCoreApplication.translate("ProcessTab_Disp", u"Image interpolation", None))
        self.combo_ImInt.setItemText(0, QCoreApplication.translate("ProcessTab_Disp", u"none", None))
        self.combo_ImInt.setItemText(1, QCoreApplication.translate("ProcessTab_Disp", u"moving window", None))
        self.combo_ImInt.setItemText(2, QCoreApplication.translate("ProcessTab_Disp", u"linear revitalized", None))
        self.combo_ImInt.setItemText(3, QCoreApplication.translate("ProcessTab_Disp", u"bilinear/biquadratic/bicubic", None))
        self.combo_ImInt.setItemText(4, QCoreApplication.translate("ProcessTab_Disp", u"simplex", None))
        self.combo_ImInt.setItemText(5, QCoreApplication.translate("ProcessTab_Disp", u"shift theorem", None))
        self.combo_ImInt.setItemText(6, QCoreApplication.translate("ProcessTab_Disp", u"sinc (Whittaker-Shannon)", None))
        self.combo_ImInt.setItemText(7, QCoreApplication.translate("ProcessTab_Disp", u"B-spline", None))

#if QT_CONFIG(tooltip)
        self.combo_ImInt.setToolTip(QCoreApplication.translate("ProcessTab_Disp", u"Type of interpolation for image deformation method", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.w_ImInt_par.setToolTip(QCoreApplication.translate("ProcessTab_Disp", u"Value of kernel/order (integer)", None))
#endif // QT_CONFIG(tooltip)
        self.label_par_imshift.setText(QCoreApplication.translate("ProcessTab_Disp", u"Type", None))
        self.combo_par_imshift.setItemText(0, QCoreApplication.translate("ProcessTab_Disp", u"symmetric", None))
        self.combo_par_imshift.setItemText(1, QCoreApplication.translate("ProcessTab_Disp", u"asymmetric", None))

#if QT_CONFIG(tooltip)
        self.combo_par_imshift.setToolTip(QCoreApplication.translate("ProcessTab_Disp", u"Type of moving window method", None))
#endif // QT_CONFIG(tooltip)
        self.label_par_pol.setText(QCoreApplication.translate("ProcessTab_Disp", u"Type", None))
        self.combo_par_pol.setItemText(0, QCoreApplication.translate("ProcessTab_Disp", u"bilinear", None))
        self.combo_par_pol.setItemText(1, QCoreApplication.translate("ProcessTab_Disp", u"biquadratic", None))
        self.combo_par_pol.setItemText(2, QCoreApplication.translate("ProcessTab_Disp", u"bicubic", None))
        self.combo_par_pol.setItemText(3, QCoreApplication.translate("ProcessTab_Disp", u"bicubic (spline)", None))

#if QT_CONFIG(tooltip)
        self.combo_par_pol.setToolTip(QCoreApplication.translate("ProcessTab_Disp", u"Type of  (repeated) polynomial interpolation", None))
#endif // QT_CONFIG(tooltip)
        self.label_par_order.setText(QCoreApplication.translate("ProcessTab_Disp", u"Kernel", None))
#if QT_CONFIG(tooltip)
        self.tool_CollapBox_Interp_2.setToolTip(QCoreApplication.translate("ProcessTab_Disp", u"Windowing and correlation option box", None))
#endif // QT_CONFIG(tooltip)
        self.tool_CollapBox_Interp_2.setText(QCoreApplication.translate("ProcessTab_Disp", u"Windowing and correlation", None))
#if QT_CONFIG(tooltip)
        self.button_CollapBox_Interp_2.setToolTip(QCoreApplication.translate("ProcessTab_Disp", u"Set default options for the selected type of process", None))
#endif // QT_CONFIG(tooltip)
        self.button_CollapBox_Interp_2.setText("")
        self.group_int_2.setTitle("")
        self.label_MinVal_2.setText(QCoreApplication.translate("ProcessTab_Disp", u"IW sizes and spacings: ", None))
#if QT_CONFIG(tooltip)
        self.line_edit_IW.setToolTip(QCoreApplication.translate("ProcessTab_Disp", u"IW sizes and spacings: height, width, vertical spacing, horizontal spacing", None))
#endif // QT_CONFIG(tooltip)
        self.line_edit_IW.setText(QCoreApplication.translate("ProcessTab_Disp", u"256, 256, 128, 128", None))
        self.check_edit_IW.setText("")
        self.label_SemiWidth_Epipolar.setText(QCoreApplication.translate("ProcessTab_Disp", u"Semi-width \u22a5 epipolar", None))
#if QT_CONFIG(tooltip)
        self.spin_SemiWidth_Epipolar.setToolTip(QCoreApplication.translate("ProcessTab_Disp", u"Semi-width in the direction normal to the epipolar line", None))
#endif // QT_CONFIG(tooltip)
        self.label_Filter_SemiWidth.setText(QCoreApplication.translate("ProcessTab_Disp", u"Filter semi-width", None))
#if QT_CONFIG(tooltip)
        self.spin_Filter_SemiWidth.setToolTip(QCoreApplication.translate("ProcessTab_Disp", u"Semi-width of the filter for the detection of the maximum in the displacement map", None))
#endif // QT_CONFIG(tooltip)
        self.label_Threshold.setText(QCoreApplication.translate("ProcessTab_Disp", u"Correlation threshold", None))
#if QT_CONFIG(tooltip)
        self.spin_Threshold.setToolTip(QCoreApplication.translate("ProcessTab_Disp", u"Threshold for the determination of point used in the baricentric search of the maximum in the disparity map", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.tool_CollapBox_Interp_3.setToolTip(QCoreApplication.translate("ProcessTab_Disp", u"Windowing and correlation option box", None))
#endif // QT_CONFIG(tooltip)
        self.tool_CollapBox_Interp_3.setText(QCoreApplication.translate("ProcessTab_Disp", u"Validation", None))
#if QT_CONFIG(tooltip)
        self.button_CollapBox_Interp_3.setToolTip(QCoreApplication.translate("ProcessTab_Disp", u"Set default options for the selected type of process", None))
#endif // QT_CONFIG(tooltip)
        self.button_CollapBox_Interp_3.setText("")
        self.group_Validation.setTitle("")
        self.label_Nit_OutDet.setText(QCoreApplication.translate("ProcessTab_Disp", u"# of iterations", None))
#if QT_CONFIG(tooltip)
        self.spin_Nit_OutDet.setToolTip(QCoreApplication.translate("ProcessTab_Disp", u"Number of iterations of the median test for disparity vector outlier detection", None))
#endif // QT_CONFIG(tooltip)
        self.label_Std_Threshold.setText(QCoreApplication.translate("ProcessTab_Disp", u"S.t.d. threshold", None))
#if QT_CONFIG(tooltip)
        self.spin_Std_Threshold.setToolTip(QCoreApplication.translate("ProcessTab_Disp", u"Threshold defined as a number of standard deviations used in the median test for  disparity vector outlier detection", None))
#endif // QT_CONFIG(tooltip)
    # retranslateUi


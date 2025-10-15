from .addwidgets_ps import icons_path
# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Process_Tab_CalVi.ui'
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
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QCheckBox, QComboBox,
    QFrame, QGroupBox, QHBoxLayout, QLabel,
    QLayout, QPushButton, QScrollArea, QSizePolicy,
    QSpacerItem, QStackedWidget, QToolButton, QVBoxLayout,
    QWidget)

from .addwidgets_ps import (CollapsibleBox, MyQCombo, MyQDoubleSpin, MyQSpin,
    MyTabLabel, MyToolButton)

class Ui_ProcessTab_CalVi(object):
    def setupUi(self, ProcessTab_CalVi):
        if not ProcessTab_CalVi.objectName():
            ProcessTab_CalVi.setObjectName(u"ProcessTab_CalVi")
        ProcessTab_CalVi.resize(500, 680)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(ProcessTab_CalVi.sizePolicy().hasHeightForWidth())
        ProcessTab_CalVi.setSizePolicy(sizePolicy)
        ProcessTab_CalVi.setMinimumSize(QSize(500, 680))
        ProcessTab_CalVi.setMaximumSize(QSize(1000, 16777215))
        font = QFont()
        font.setPointSize(11)
        ProcessTab_CalVi.setFont(font)
        icon1 = QIcon()
        icon1.addFile(u""+ icons_path +"process_logo.png", QSize(), QIcon.Normal, QIcon.Off)
        ProcessTab_CalVi.setWindowIcon(icon1)
        self.verticalLayout_65 = QVBoxLayout(ProcessTab_CalVi)
        self.verticalLayout_65.setSpacing(5)
        self.verticalLayout_65.setObjectName(u"verticalLayout_65")
        self.verticalLayout_65.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.verticalLayout_65.setContentsMargins(10, 10, 10, 10)
        self.w_Mode = QWidget(ProcessTab_CalVi)
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
        icon2.addFile(u""+ icons_path +"undo.png", QSize(), QIcon.Normal, QIcon.Off)
        self.button_back.setIcon(icon2)
        self.button_back.setIconSize(QSize(20, 20))

        self.horizontalLayout_2.addWidget(self.button_back)

        self.button_forward = QToolButton(self.w_Mode)
        self.button_forward.setObjectName(u"button_forward")
        self.button_forward.setMinimumSize(QSize(24, 24))
        self.button_forward.setMaximumSize(QSize(24, 24))
        icon3 = QIcon()
        icon3.addFile(u""+ icons_path +"redo.png", QSize(), QIcon.Normal, QIcon.Off)
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
        icon4.addFile(u""+ icons_path +"close.png", QSize(), QIcon.Normal, QIcon.Off)
        self.button_close_tab.setIcon(icon4)
        self.button_close_tab.setIconSize(QSize(15, 15))

        self.horizontalLayout_20.addWidget(self.button_close_tab)


        self.horizontalLayout_2.addWidget(self.w_button_close_tab)


        self.verticalLayout_65.addWidget(self.w_Mode)

        self.separator = QFrame(ProcessTab_CalVi)
        self.separator.setObjectName(u"separator")
        self.separator.setMinimumSize(QSize(0, 5))
        self.separator.setFrameShape(QFrame.Shape.HLine)
        self.separator.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_65.addWidget(self.separator)

        self.scrollArea = QScrollArea(ProcessTab_CalVi)
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
        self.verticalLayout_10.setContentsMargins(0, 0, 10, 5)
        self.CollapBox_Target = CollapsibleBox(self.scrollAreaWidgetContents)
        self.CollapBox_Target.setObjectName(u"CollapBox_Target")
        sizePolicy.setHeightForWidth(self.CollapBox_Target.sizePolicy().hasHeightForWidth())
        self.CollapBox_Target.setSizePolicy(sizePolicy)
        self.CollapBox_Target.setMinimumSize(QSize(0, 204))
        self.CollapBox_Target.setMaximumSize(QSize(16777215, 204))
        self.verticalLayout_2 = QVBoxLayout(self.CollapBox_Target)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.lay_CollapBox_Target = QHBoxLayout()
        self.lay_CollapBox_Target.setSpacing(0)
        self.lay_CollapBox_Target.setObjectName(u"lay_CollapBox_Target")
        self.lay_CollapBox_Target.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.tool_CollapBox_Target = QToolButton(self.CollapBox_Target)
        self.tool_CollapBox_Target.setObjectName(u"tool_CollapBox_Target")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.tool_CollapBox_Target.sizePolicy().hasHeightForWidth())
        self.tool_CollapBox_Target.setSizePolicy(sizePolicy2)
        self.tool_CollapBox_Target.setMinimumSize(QSize(0, 20))
        self.tool_CollapBox_Target.setMaximumSize(QSize(16777215, 20))
        font3 = QFont()
        font3.setPointSize(10)
        font3.setBold(True)
        self.tool_CollapBox_Target.setFont(font3)
        self.tool_CollapBox_Target.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.tool_CollapBox_Target.setStyleSheet(u"QToolButton { border: none; }")
        self.tool_CollapBox_Target.setCheckable(True)
        self.tool_CollapBox_Target.setChecked(True)
        self.tool_CollapBox_Target.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.tool_CollapBox_Target.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.tool_CollapBox_Target.setArrowType(Qt.ArrowType.DownArrow)

        self.lay_CollapBox_Target.addWidget(self.tool_CollapBox_Target)

        self.hsp_CollapBox_Target = QSpacerItem(100, 20, QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        self.lay_CollapBox_Target.addItem(self.hsp_CollapBox_Target)

        self.button_CollapBox_Target = MyToolButton(self.CollapBox_Target)
        self.button_CollapBox_Target.setObjectName(u"button_CollapBox_Target")
        self.button_CollapBox_Target.setMinimumSize(QSize(18, 18))
        self.button_CollapBox_Target.setMaximumSize(QSize(18, 18))
        self.button_CollapBox_Target.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.button_CollapBox_Target.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.button_CollapBox_Target.setIcon(icon2)
        self.button_CollapBox_Target.setIconSize(QSize(12, 12))

        self.lay_CollapBox_Target.addWidget(self.button_CollapBox_Target)


        self.verticalLayout_2.addLayout(self.lay_CollapBox_Target)

        self.w_Target_Parameters = QGroupBox(self.CollapBox_Target)
        self.w_Target_Parameters.setObjectName(u"w_Target_Parameters")
        self.w_Target_Parameters.setMinimumSize(QSize(0, 184))
        self.w_Target_Parameters.setMaximumSize(QSize(16777215, 184))
        font4 = QFont()
        font4.setPointSize(10)
        font4.setBold(True)
        font4.setItalic(False)
        self.w_Target_Parameters.setFont(font4)
        self.w_Target_Parameters.setMouseTracking(True)
        self.w_Target_Parameters.setStyleSheet(u"QGroupBox{border: 1px solid gray; border-radius: 6px;}\n"
"QGroupBox::hover{border: 1px solid lightblue; border-radius: 6px;}")
        self.w_Target_Parameters.setFlat(False)
        self.w_Target_Parameters.setCheckable(False)
        self.verticalLayout_3 = QVBoxLayout(self.w_Target_Parameters)
        self.verticalLayout_3.setSpacing(20)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.verticalLayout_3.setContentsMargins(6, 10, 6, 10)
        self.w_Dot = QWidget(self.w_Target_Parameters)
        self.w_Dot.setObjectName(u"w_Dot")
        sizePolicy.setHeightForWidth(self.w_Dot.sizePolicy().hasHeightForWidth())
        self.w_Dot.setSizePolicy(sizePolicy)
        self.w_Dot.setMinimumSize(QSize(0, 44))
        self.horizontalLayout_4 = QHBoxLayout(self.w_Dot)
        self.horizontalLayout_4.setSpacing(6)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.w_DotColor = QWidget(self.w_Dot)
        self.w_DotColor.setObjectName(u"w_DotColor")
        self.w_DotColor.setMaximumSize(QSize(16777215, 44))
        self.verticalLayout_23 = QVBoxLayout(self.w_DotColor)
        self.verticalLayout_23.setSpacing(0)
        self.verticalLayout_23.setObjectName(u"verticalLayout_23")
        self.verticalLayout_23.setContentsMargins(-1, 0, 9, 0)
        self.label_DotColor = QLabel(self.w_DotColor)
        self.label_DotColor.setObjectName(u"label_DotColor")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.label_DotColor.sizePolicy().hasHeightForWidth())
        self.label_DotColor.setSizePolicy(sizePolicy3)
        self.label_DotColor.setMinimumSize(QSize(80, 20))
        self.label_DotColor.setMaximumSize(QSize(16777215, 20))
        font5 = QFont()
        font5.setPointSize(10)
        font5.setBold(False)
        font5.setItalic(True)
        self.label_DotColor.setFont(font5)
        self.label_DotColor.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout_23.addWidget(self.label_DotColor)

        self.button_DotColor = QPushButton(self.w_DotColor)
        self.button_DotColor.setObjectName(u"button_DotColor")
        sizePolicy3.setHeightForWidth(self.button_DotColor.sizePolicy().hasHeightForWidth())
        self.button_DotColor.setSizePolicy(sizePolicy3)
        self.button_DotColor.setMinimumSize(QSize(0, 22))
        self.button_DotColor.setFont(font)

        self.verticalLayout_23.addWidget(self.button_DotColor)


        self.horizontalLayout_4.addWidget(self.w_DotColor)

        self.w_DotType = QWidget(self.w_Dot)
        self.w_DotType.setObjectName(u"w_DotType")
        self.w_DotType.setMinimumSize(QSize(0, 44))
        self.w_DotType.setMaximumSize(QSize(16777215, 44))
        self.verticalLayout_67 = QVBoxLayout(self.w_DotType)
        self.verticalLayout_67.setSpacing(0)
        self.verticalLayout_67.setObjectName(u"verticalLayout_67")
        self.verticalLayout_67.setContentsMargins(0, 0, 0, 0)
        self.label_DotTypeSearch = QLabel(self.w_DotType)
        self.label_DotTypeSearch.setObjectName(u"label_DotTypeSearch")
        sizePolicy3.setHeightForWidth(self.label_DotTypeSearch.sizePolicy().hasHeightForWidth())
        self.label_DotTypeSearch.setSizePolicy(sizePolicy3)
        self.label_DotTypeSearch.setMinimumSize(QSize(80, 20))
        self.label_DotTypeSearch.setMaximumSize(QSize(16777215, 20))
        self.label_DotTypeSearch.setFont(font5)
        self.label_DotTypeSearch.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout_67.addWidget(self.label_DotTypeSearch)

        self.combo_DotTypeSearch = MyQCombo(self.w_DotType)
        self.combo_DotTypeSearch.addItem("")
        self.combo_DotTypeSearch.addItem("")
        self.combo_DotTypeSearch.addItem("")
        self.combo_DotTypeSearch.addItem("")
        self.combo_DotTypeSearch.addItem("")
        self.combo_DotTypeSearch.addItem("")
        self.combo_DotTypeSearch.setObjectName(u"combo_DotTypeSearch")
        self.combo_DotTypeSearch.setMinimumSize(QSize(85, 0))
        self.combo_DotTypeSearch.setMaximumSize(QSize(16777215, 24))
        self.combo_DotTypeSearch.setFont(font)

        self.verticalLayout_67.addWidget(self.combo_DotTypeSearch)


        self.horizontalLayout_4.addWidget(self.w_DotType)

        self.w_DotThresh = QWidget(self.w_Dot)
        self.w_DotThresh.setObjectName(u"w_DotThresh")
        self.w_DotThresh.setMinimumSize(QSize(0, 44))
        self.w_DotThresh.setMaximumSize(QSize(16777215, 44))
        self.verticalLayout_69 = QVBoxLayout(self.w_DotThresh)
        self.verticalLayout_69.setSpacing(0)
        self.verticalLayout_69.setObjectName(u"verticalLayout_69")
        self.verticalLayout_69.setContentsMargins(0, 0, 0, 0)
        self.label_DotThresh = QLabel(self.w_DotThresh)
        self.label_DotThresh.setObjectName(u"label_DotThresh")
        sizePolicy3.setHeightForWidth(self.label_DotThresh.sizePolicy().hasHeightForWidth())
        self.label_DotThresh.setSizePolicy(sizePolicy3)
        self.label_DotThresh.setMinimumSize(QSize(55, 20))
        self.label_DotThresh.setMaximumSize(QSize(16777215, 20))
        self.label_DotThresh.setFont(font5)
        self.label_DotThresh.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout_69.addWidget(self.label_DotThresh)

        self.spin_DotThresh = MyQDoubleSpin(self.w_DotThresh)
        self.spin_DotThresh.setObjectName(u"spin_DotThresh")
        self.spin_DotThresh.setMinimumSize(QSize(55, 24))
        self.spin_DotThresh.setMaximumSize(QSize(1000000, 24))
        self.spin_DotThresh.setFont(font)
        self.spin_DotThresh.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_DotThresh.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
        self.spin_DotThresh.setMaximum(1.000000000000000)
        self.spin_DotThresh.setSingleStep(0.010000000000000)
        self.spin_DotThresh.setValue(0.500000000000000)

        self.verticalLayout_69.addWidget(self.spin_DotThresh)


        self.horizontalLayout_4.addWidget(self.w_DotThresh)

        self.w_DotDiam = QWidget(self.w_Dot)
        self.w_DotDiam.setObjectName(u"w_DotDiam")
        self.w_DotDiam.setMinimumSize(QSize(0, 44))
        self.w_DotDiam.setMaximumSize(QSize(16777215, 44))
        self.verticalLayout_68 = QVBoxLayout(self.w_DotDiam)
        self.verticalLayout_68.setSpacing(0)
        self.verticalLayout_68.setObjectName(u"verticalLayout_68")
        self.verticalLayout_68.setContentsMargins(0, 0, 0, 0)
        self.label_DotDiam = QLabel(self.w_DotDiam)
        self.label_DotDiam.setObjectName(u"label_DotDiam")
        sizePolicy3.setHeightForWidth(self.label_DotDiam.sizePolicy().hasHeightForWidth())
        self.label_DotDiam.setSizePolicy(sizePolicy3)
        self.label_DotDiam.setMinimumSize(QSize(65, 20))
        self.label_DotDiam.setMaximumSize(QSize(16777215, 20))
        self.label_DotDiam.setFont(font5)
        self.label_DotDiam.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout_68.addWidget(self.label_DotDiam)

        self.spin_DotDiam = MyQSpin(self.w_DotDiam)
        self.spin_DotDiam.setObjectName(u"spin_DotDiam")
        self.spin_DotDiam.setEnabled(True)
        self.spin_DotDiam.setMinimumSize(QSize(65, 24))
        self.spin_DotDiam.setMaximumSize(QSize(1000000, 24))
        self.spin_DotDiam.setFont(font)
        self.spin_DotDiam.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.spin_DotDiam.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_DotDiam.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
        self.spin_DotDiam.setMaximum(999999999)
        self.spin_DotDiam.setValue(1)

        self.verticalLayout_68.addWidget(self.spin_DotDiam)


        self.horizontalLayout_4.addWidget(self.w_DotDiam)

        self.horizontalLayout_4.setStretch(1, 3)
        self.horizontalLayout_4.setStretch(2, 1)
        self.horizontalLayout_4.setStretch(3, 2)

        self.verticalLayout_3.addWidget(self.w_Dot)

        self.w_Target = QWidget(self.w_Target_Parameters)
        self.w_Target.setObjectName(u"w_Target")
        sizePolicy.setHeightForWidth(self.w_Target.sizePolicy().hasHeightForWidth())
        self.w_Target.setSizePolicy(sizePolicy)
        self.w_Target.setMinimumSize(QSize(0, 44))
        self.horizontalLayout_8 = QHBoxLayout(self.w_Target)
        self.horizontalLayout_8.setSpacing(6)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.horizontalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.w_TargetType = QWidget(self.w_Target)
        self.w_TargetType.setObjectName(u"w_TargetType")
        self.w_TargetType.setMinimumSize(QSize(0, 44))
        self.w_TargetType.setMaximumSize(QSize(16777215, 44))
        self.verticalLayout_75 = QVBoxLayout(self.w_TargetType)
        self.verticalLayout_75.setSpacing(0)
        self.verticalLayout_75.setObjectName(u"verticalLayout_75")
        self.verticalLayout_75.setContentsMargins(0, 0, 0, 0)
        self.label_TargetType = QLabel(self.w_TargetType)
        self.label_TargetType.setObjectName(u"label_TargetType")
        sizePolicy3.setHeightForWidth(self.label_TargetType.sizePolicy().hasHeightForWidth())
        self.label_TargetType.setSizePolicy(sizePolicy3)
        self.label_TargetType.setMinimumSize(QSize(80, 20))
        self.label_TargetType.setMaximumSize(QSize(16777215, 20))
        self.label_TargetType.setFont(font5)
        self.label_TargetType.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout_75.addWidget(self.label_TargetType)

        self.combo_TargetType = MyQCombo(self.w_TargetType)
        self.combo_TargetType.addItem("")
        self.combo_TargetType.addItem("")
        self.combo_TargetType.setObjectName(u"combo_TargetType")
        self.combo_TargetType.setMinimumSize(QSize(85, 0))
        self.combo_TargetType.setMaximumSize(QSize(16777215, 24))
        self.combo_TargetType.setFont(font)

        self.verticalLayout_75.addWidget(self.combo_TargetType)


        self.horizontalLayout_8.addWidget(self.w_TargetType)

        self.w_DotDx = QWidget(self.w_Target)
        self.w_DotDx.setObjectName(u"w_DotDx")
        self.w_DotDx.setMinimumSize(QSize(0, 44))
        self.w_DotDx.setMaximumSize(QSize(16777215, 44))
        self.verticalLayout_76 = QVBoxLayout(self.w_DotDx)
        self.verticalLayout_76.setSpacing(0)
        self.verticalLayout_76.setObjectName(u"verticalLayout_76")
        self.verticalLayout_76.setContentsMargins(0, 0, 0, 0)
        self.label_DotDx = QLabel(self.w_DotDx)
        self.label_DotDx.setObjectName(u"label_DotDx")
        sizePolicy3.setHeightForWidth(self.label_DotDx.sizePolicy().hasHeightForWidth())
        self.label_DotDx.setSizePolicy(sizePolicy3)
        self.label_DotDx.setMinimumSize(QSize(55, 20))
        self.label_DotDx.setMaximumSize(QSize(16777215, 20))
        self.label_DotDx.setFont(font5)
        self.label_DotDx.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout_76.addWidget(self.label_DotDx)

        self.spin_DotDx = MyQDoubleSpin(self.w_DotDx)
        self.spin_DotDx.setObjectName(u"spin_DotDx")
        self.spin_DotDx.setMinimumSize(QSize(55, 24))
        self.spin_DotDx.setMaximumSize(QSize(1000000, 24))
        self.spin_DotDx.setFont(font)
        self.spin_DotDx.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_DotDx.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
        self.spin_DotDx.setDecimals(3)
        self.spin_DotDx.setMaximum(10000000000000000000000.000000000000000)
        self.spin_DotDx.setSingleStep(0.100000000000000)
        self.spin_DotDx.setValue(5.000000000000000)

        self.verticalLayout_76.addWidget(self.spin_DotDx)


        self.horizontalLayout_8.addWidget(self.w_DotDx)

        self.w_DotDy = QWidget(self.w_Target)
        self.w_DotDy.setObjectName(u"w_DotDy")
        self.w_DotDy.setMinimumSize(QSize(0, 44))
        self.w_DotDy.setMaximumSize(QSize(16777215, 44))
        self.verticalLayout_77 = QVBoxLayout(self.w_DotDy)
        self.verticalLayout_77.setSpacing(0)
        self.verticalLayout_77.setObjectName(u"verticalLayout_77")
        self.verticalLayout_77.setContentsMargins(0, 0, 0, 0)
        self.label_DotDy = QLabel(self.w_DotDy)
        self.label_DotDy.setObjectName(u"label_DotDy")
        sizePolicy3.setHeightForWidth(self.label_DotDy.sizePolicy().hasHeightForWidth())
        self.label_DotDy.setSizePolicy(sizePolicy3)
        self.label_DotDy.setMinimumSize(QSize(55, 20))
        self.label_DotDy.setMaximumSize(QSize(16777215, 20))
        self.label_DotDy.setFont(font5)
        self.label_DotDy.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout_77.addWidget(self.label_DotDy)

        self.spin_DotDy = MyQDoubleSpin(self.w_DotDy)
        self.spin_DotDy.setObjectName(u"spin_DotDy")
        self.spin_DotDy.setMinimumSize(QSize(55, 24))
        self.spin_DotDy.setMaximumSize(QSize(1000000, 24))
        self.spin_DotDy.setFont(font)
        self.spin_DotDy.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_DotDy.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
        self.spin_DotDy.setDecimals(3)
        self.spin_DotDy.setMaximum(10000000000000000000000.000000000000000)
        self.spin_DotDy.setSingleStep(0.100000000000000)
        self.spin_DotDy.setValue(5.000000000000000)

        self.verticalLayout_77.addWidget(self.spin_DotDy)


        self.horizontalLayout_8.addWidget(self.w_DotDy)


        self.verticalLayout_3.addWidget(self.w_Target)

        self.w_DoublePlane = QWidget(self.w_Target_Parameters)
        self.w_DoublePlane.setObjectName(u"w_DoublePlane")
        sizePolicy.setHeightForWidth(self.w_DoublePlane.sizePolicy().hasHeightForWidth())
        self.w_DoublePlane.setSizePolicy(sizePolicy)
        self.w_DoublePlane.setMinimumSize(QSize(0, 44))
        self.horizontalLayout_9 = QHBoxLayout(self.w_DoublePlane)
        self.horizontalLayout_9.setSpacing(6)
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.horizontalLayout_9.setContentsMargins(0, 0, 0, 0)
        self.w_OriginXShift = QWidget(self.w_DoublePlane)
        self.w_OriginXShift.setObjectName(u"w_OriginXShift")
        self.w_OriginXShift.setMinimumSize(QSize(0, 44))
        self.w_OriginXShift.setMaximumSize(QSize(16777215, 44))
        self.verticalLayout_78 = QVBoxLayout(self.w_OriginXShift)
        self.verticalLayout_78.setSpacing(0)
        self.verticalLayout_78.setObjectName(u"verticalLayout_78")
        self.verticalLayout_78.setContentsMargins(0, 0, 0, 0)
        self.label_OriginXShift = QLabel(self.w_OriginXShift)
        self.label_OriginXShift.setObjectName(u"label_OriginXShift")
        sizePolicy3.setHeightForWidth(self.label_OriginXShift.sizePolicy().hasHeightForWidth())
        self.label_OriginXShift.setSizePolicy(sizePolicy3)
        self.label_OriginXShift.setMinimumSize(QSize(55, 20))
        self.label_OriginXShift.setMaximumSize(QSize(16777215, 20))
        self.label_OriginXShift.setFont(font5)
        self.label_OriginXShift.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout_78.addWidget(self.label_OriginXShift)

        self.spin_OriginXShift = MyQDoubleSpin(self.w_OriginXShift)
        self.spin_OriginXShift.setObjectName(u"spin_OriginXShift")
        self.spin_OriginXShift.setMinimumSize(QSize(55, 24))
        self.spin_OriginXShift.setMaximumSize(QSize(1000000, 24))
        self.spin_OriginXShift.setFont(font)
        self.spin_OriginXShift.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_OriginXShift.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
        self.spin_OriginXShift.setDecimals(3)
        self.spin_OriginXShift.setMaximum(10000000000000000000000.000000000000000)
        self.spin_OriginXShift.setSingleStep(0.100000000000000)
        self.spin_OriginXShift.setValue(5.000000000000000)

        self.verticalLayout_78.addWidget(self.spin_OriginXShift)


        self.horizontalLayout_9.addWidget(self.w_OriginXShift)

        self.w_OriginYShift = QWidget(self.w_DoublePlane)
        self.w_OriginYShift.setObjectName(u"w_OriginYShift")
        self.w_OriginYShift.setMinimumSize(QSize(0, 44))
        self.w_OriginYShift.setMaximumSize(QSize(16777215, 44))
        self.verticalLayout_79 = QVBoxLayout(self.w_OriginYShift)
        self.verticalLayout_79.setSpacing(0)
        self.verticalLayout_79.setObjectName(u"verticalLayout_79")
        self.verticalLayout_79.setContentsMargins(0, 0, 0, 0)
        self.label_OriginYShift = QLabel(self.w_OriginYShift)
        self.label_OriginYShift.setObjectName(u"label_OriginYShift")
        sizePolicy3.setHeightForWidth(self.label_OriginYShift.sizePolicy().hasHeightForWidth())
        self.label_OriginYShift.setSizePolicy(sizePolicy3)
        self.label_OriginYShift.setMinimumSize(QSize(55, 20))
        self.label_OriginYShift.setMaximumSize(QSize(16777215, 20))
        self.label_OriginYShift.setFont(font5)
        self.label_OriginYShift.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout_79.addWidget(self.label_OriginYShift)

        self.spin_OriginYShift = MyQDoubleSpin(self.w_OriginYShift)
        self.spin_OriginYShift.setObjectName(u"spin_OriginYShift")
        self.spin_OriginYShift.setMinimumSize(QSize(55, 24))
        self.spin_OriginYShift.setMaximumSize(QSize(1000000, 24))
        self.spin_OriginYShift.setFont(font)
        self.spin_OriginYShift.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_OriginYShift.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
        self.spin_OriginYShift.setDecimals(3)
        self.spin_OriginYShift.setMaximum(10000000000000000000000.000000000000000)
        self.spin_OriginYShift.setSingleStep(0.100000000000000)
        self.spin_OriginYShift.setValue(5.000000000000000)

        self.verticalLayout_79.addWidget(self.spin_OriginYShift)


        self.horizontalLayout_9.addWidget(self.w_OriginYShift)

        self.w_OriginZShift = QWidget(self.w_DoublePlane)
        self.w_OriginZShift.setObjectName(u"w_OriginZShift")
        self.w_OriginZShift.setMinimumSize(QSize(0, 44))
        self.w_OriginZShift.setMaximumSize(QSize(16777215, 44))
        self.verticalLayout_80 = QVBoxLayout(self.w_OriginZShift)
        self.verticalLayout_80.setSpacing(0)
        self.verticalLayout_80.setObjectName(u"verticalLayout_80")
        self.verticalLayout_80.setContentsMargins(0, 0, 0, 0)
        self.label_OriginZShift = QLabel(self.w_OriginZShift)
        self.label_OriginZShift.setObjectName(u"label_OriginZShift")
        sizePolicy3.setHeightForWidth(self.label_OriginZShift.sizePolicy().hasHeightForWidth())
        self.label_OriginZShift.setSizePolicy(sizePolicy3)
        self.label_OriginZShift.setMinimumSize(QSize(55, 20))
        self.label_OriginZShift.setMaximumSize(QSize(16777215, 20))
        self.label_OriginZShift.setFont(font5)
        self.label_OriginZShift.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout_80.addWidget(self.label_OriginZShift)

        self.spin_OriginZShift = MyQDoubleSpin(self.w_OriginZShift)
        self.spin_OriginZShift.setObjectName(u"spin_OriginZShift")
        self.spin_OriginZShift.setMinimumSize(QSize(55, 24))
        self.spin_OriginZShift.setMaximumSize(QSize(1000000, 24))
        self.spin_OriginZShift.setFont(font)
        self.spin_OriginZShift.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_OriginZShift.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
        self.spin_OriginZShift.setDecimals(3)
        self.spin_OriginZShift.setMaximum(10000000000000000000000.000000000000000)
        self.spin_OriginZShift.setSingleStep(0.100000000000000)
        self.spin_OriginZShift.setValue(5.000000000000000)

        self.verticalLayout_80.addWidget(self.spin_OriginZShift)


        self.horizontalLayout_9.addWidget(self.w_OriginZShift)


        self.verticalLayout_3.addWidget(self.w_DoublePlane)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer_2)


        self.verticalLayout_2.addWidget(self.w_Target_Parameters)


        self.verticalLayout_10.addWidget(self.CollapBox_Target)

        self.CollapBox_Calibration = CollapsibleBox(self.scrollAreaWidgetContents)
        self.CollapBox_Calibration.setObjectName(u"CollapBox_Calibration")
        sizePolicy.setHeightForWidth(self.CollapBox_Calibration.sizePolicy().hasHeightForWidth())
        self.CollapBox_Calibration.setSizePolicy(sizePolicy)
        self.CollapBox_Calibration.setMinimumSize(QSize(0, 268))
        self.CollapBox_Calibration.setMaximumSize(QSize(16777215, 268))
        self.verticalLayout_11 = QVBoxLayout(self.CollapBox_Calibration)
        self.verticalLayout_11.setSpacing(0)
        self.verticalLayout_11.setObjectName(u"verticalLayout_11")
        self.verticalLayout_11.setContentsMargins(0, 0, 0, 0)
        self.lay_CollapBox_CalPar = QHBoxLayout()
        self.lay_CollapBox_CalPar.setSpacing(0)
        self.lay_CollapBox_CalPar.setObjectName(u"lay_CollapBox_CalPar")
        self.lay_CollapBox_CalPar.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.tool_CollapBox_CalPar = QToolButton(self.CollapBox_Calibration)
        self.tool_CollapBox_CalPar.setObjectName(u"tool_CollapBox_CalPar")
        sizePolicy2.setHeightForWidth(self.tool_CollapBox_CalPar.sizePolicy().hasHeightForWidth())
        self.tool_CollapBox_CalPar.setSizePolicy(sizePolicy2)
        self.tool_CollapBox_CalPar.setMinimumSize(QSize(0, 20))
        self.tool_CollapBox_CalPar.setMaximumSize(QSize(16777215, 20))
        self.tool_CollapBox_CalPar.setFont(font3)
        self.tool_CollapBox_CalPar.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.tool_CollapBox_CalPar.setStyleSheet(u"QToolButton { border: none; }")
        self.tool_CollapBox_CalPar.setCheckable(True)
        self.tool_CollapBox_CalPar.setChecked(True)
        self.tool_CollapBox_CalPar.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.tool_CollapBox_CalPar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.tool_CollapBox_CalPar.setArrowType(Qt.ArrowType.DownArrow)

        self.lay_CollapBox_CalPar.addWidget(self.tool_CollapBox_CalPar)

        self.hsp_CollapBox_CalPar = QSpacerItem(100, 20, QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        self.lay_CollapBox_CalPar.addItem(self.hsp_CollapBox_CalPar)

        self.button_CollapBox_CalPar = MyToolButton(self.CollapBox_Calibration)
        self.button_CollapBox_CalPar.setObjectName(u"button_CollapBox_CalPar")
        self.button_CollapBox_CalPar.setMinimumSize(QSize(18, 18))
        self.button_CollapBox_CalPar.setMaximumSize(QSize(18, 18))
        self.button_CollapBox_CalPar.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.button_CollapBox_CalPar.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.button_CollapBox_CalPar.setIcon(icon2)
        self.button_CollapBox_CalPar.setIconSize(QSize(12, 12))

        self.lay_CollapBox_CalPar.addWidget(self.button_CollapBox_CalPar)


        self.verticalLayout_11.addLayout(self.lay_CollapBox_CalPar)

        self.w_Calibration_Parameters = QGroupBox(self.CollapBox_Calibration)
        self.w_Calibration_Parameters.setObjectName(u"w_Calibration_Parameters")
        sizePolicy1.setHeightForWidth(self.w_Calibration_Parameters.sizePolicy().hasHeightForWidth())
        self.w_Calibration_Parameters.setSizePolicy(sizePolicy1)
        self.w_Calibration_Parameters.setMinimumSize(QSize(0, 248))
        self.w_Calibration_Parameters.setMaximumSize(QSize(16777215, 248))
        self.w_Calibration_Parameters.setFont(font4)
        self.w_Calibration_Parameters.setCursor(QCursor(Qt.ArrowCursor))
        self.w_Calibration_Parameters.setStyleSheet(u"QGroupBox{border: 1px solid gray; border-radius: 6px;}")
        self.w_Calibration_Parameters.setCheckable(False)
        self.verticalLayout = QVBoxLayout(self.w_Calibration_Parameters)
        self.verticalLayout.setSpacing(20)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(6, 6, 6, 6)
        self.w_CalibProc = QWidget(self.w_Calibration_Parameters)
        self.w_CalibProc.setObjectName(u"w_CalibProc")
        self.w_CalibProc.setMinimumSize(QSize(0, 44))
        self.w_CalibProc.setMaximumSize(QSize(16777215, 44))
        self.horizontalLayout_17 = QHBoxLayout(self.w_CalibProc)
        self.horizontalLayout_17.setSpacing(12)
        self.horizontalLayout_17.setObjectName(u"horizontalLayout_17")
        self.horizontalLayout_17.setContentsMargins(0, 0, 0, 0)
        self.w_CalibProcType = QWidget(self.w_CalibProc)
        self.w_CalibProcType.setObjectName(u"w_CalibProcType")
        self.w_CalibProcType.setMaximumSize(QSize(150, 16777215))
        self.verticalLayout_6 = QVBoxLayout(self.w_CalibProcType)
        self.verticalLayout_6.setSpacing(0)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.label_CalibProcType = QLabel(self.w_CalibProcType)
        self.label_CalibProcType.setObjectName(u"label_CalibProcType")
        sizePolicy3.setHeightForWidth(self.label_CalibProcType.sizePolicy().hasHeightForWidth())
        self.label_CalibProcType.setSizePolicy(sizePolicy3)
        self.label_CalibProcType.setMinimumSize(QSize(0, 20))
        self.label_CalibProcType.setMaximumSize(QSize(16777215, 20))
        self.label_CalibProcType.setFont(font5)

        self.verticalLayout_6.addWidget(self.label_CalibProcType)

        self.combo_CalibProcType = MyQCombo(self.w_CalibProcType)
        self.combo_CalibProcType.addItem("")
        self.combo_CalibProcType.addItem("")
        self.combo_CalibProcType.addItem("")
        self.combo_CalibProcType.addItem("")
        self.combo_CalibProcType.setObjectName(u"combo_CalibProcType")
        sizePolicy.setHeightForWidth(self.combo_CalibProcType.sizePolicy().hasHeightForWidth())
        self.combo_CalibProcType.setSizePolicy(sizePolicy)
        self.combo_CalibProcType.setMinimumSize(QSize(0, 24))
        self.combo_CalibProcType.setMaximumSize(QSize(16777215, 24))
        self.combo_CalibProcType.setFont(font)
        self.combo_CalibProcType.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContentsOnFirstShow)

        self.verticalLayout_6.addWidget(self.combo_CalibProcType)


        self.horizontalLayout_17.addWidget(self.w_CalibProcType)

        self.check_Plane = QCheckBox(self.w_CalibProc)
        self.check_Plane.setObjectName(u"check_Plane")
        self.check_Plane.setFont(font)

        self.horizontalLayout_17.addWidget(self.check_Plane)

        self.check_Pinhole = QCheckBox(self.w_CalibProc)
        self.check_Pinhole.setObjectName(u"check_Pinhole")
        self.check_Pinhole.setFont(font)

        self.horizontalLayout_17.addWidget(self.check_Pinhole)

        self.hs_CalibProc = QSpacerItem(9, 41, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_17.addItem(self.hs_CalibProc)


        self.verticalLayout.addWidget(self.w_CalibProc)

        self.w_CamModel = QWidget(self.w_Calibration_Parameters)
        self.w_CamModel.setObjectName(u"w_CamModel")
        self.w_CamModel.setMinimumSize(QSize(0, 44))
        self.w_CamModel.setMaximumSize(QSize(16777215, 44))
        self.horizontalLayout_3 = QHBoxLayout(self.w_CamModel)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.w_CamMod = QWidget(self.w_CamModel)
        self.w_CamMod.setObjectName(u"w_CamMod")
        self.w_CamMod.setMinimumSize(QSize(0, 44))
        self.w_CamMod.setMaximumSize(QSize(16777215, 44))
        self.verticalLayout_43 = QVBoxLayout(self.w_CamMod)
        self.verticalLayout_43.setSpacing(0)
        self.verticalLayout_43.setObjectName(u"verticalLayout_43")
        self.verticalLayout_43.setContentsMargins(0, 0, 0, 0)
        self.label_CamMod = QLabel(self.w_CamMod)
        self.label_CamMod.setObjectName(u"label_CamMod")
        sizePolicy3.setHeightForWidth(self.label_CamMod.sizePolicy().hasHeightForWidth())
        self.label_CamMod.setSizePolicy(sizePolicy3)
        self.label_CamMod.setMinimumSize(QSize(0, 20))
        self.label_CamMod.setMaximumSize(QSize(16777215, 20))
        self.label_CamMod.setFont(font5)

        self.verticalLayout_43.addWidget(self.label_CamMod)

        self.combo_CamMod = MyQCombo(self.w_CamMod)
        self.combo_CamMod.addItem("")
        self.combo_CamMod.addItem("")
        self.combo_CamMod.addItem("")
        self.combo_CamMod.addItem("")
        self.combo_CamMod.addItem("")
        self.combo_CamMod.setObjectName(u"combo_CamMod")
        sizePolicy.setHeightForWidth(self.combo_CamMod.sizePolicy().hasHeightForWidth())
        self.combo_CamMod.setSizePolicy(sizePolicy)
        self.combo_CamMod.setMinimumSize(QSize(0, 24))
        self.combo_CamMod.setMaximumSize(QSize(16777215, 24))
        self.combo_CamMod.setFont(font)
        self.combo_CamMod.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContentsOnFirstShow)

        self.verticalLayout_43.addWidget(self.combo_CamMod)


        self.horizontalLayout_3.addWidget(self.w_CamMod)

        self.hs_CamMod = QSpacerItem(9, 41, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.hs_CamMod)

        self.w_CamMod_par = QStackedWidget(self.w_CamModel)
        self.w_CamMod_par.setObjectName(u"w_CamMod_par")
        self.w_CamMod_par.setMaximumSize(QSize(16777215, 44))
        self.w_PolyDegree_par = QWidget()
        self.w_PolyDegree_par.setObjectName(u"w_PolyDegree_par")
        self.w_PolyDegree_par.setMinimumSize(QSize(0, 44))
        self.horizontalLayout_5 = QHBoxLayout(self.w_PolyDegree_par)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.w_PolyDegree = QWidget(self.w_PolyDegree_par)
        self.w_PolyDegree.setObjectName(u"w_PolyDegree")
        sizePolicy.setHeightForWidth(self.w_PolyDegree.sizePolicy().hasHeightForWidth())
        self.w_PolyDegree.setSizePolicy(sizePolicy)
        self.w_PolyDegree.setMinimumSize(QSize(0, 44))
        self.horizontalLayout_6 = QHBoxLayout(self.w_PolyDegree)
        self.horizontalLayout_6.setSpacing(6)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.w_XDeg = QWidget(self.w_PolyDegree)
        self.w_XDeg.setObjectName(u"w_XDeg")
        self.w_XDeg.setMinimumSize(QSize(0, 44))
        self.w_XDeg.setMaximumSize(QSize(16777215, 44))
        self.verticalLayout_84 = QVBoxLayout(self.w_XDeg)
        self.verticalLayout_84.setSpacing(0)
        self.verticalLayout_84.setObjectName(u"verticalLayout_84")
        self.verticalLayout_84.setContentsMargins(0, 0, 0, 0)
        self.label_XDeg = QLabel(self.w_XDeg)
        self.label_XDeg.setObjectName(u"label_XDeg")
        sizePolicy3.setHeightForWidth(self.label_XDeg.sizePolicy().hasHeightForWidth())
        self.label_XDeg.setSizePolicy(sizePolicy3)
        self.label_XDeg.setMinimumSize(QSize(55, 20))
        self.label_XDeg.setMaximumSize(QSize(16777215, 20))
        self.label_XDeg.setFont(font5)
        self.label_XDeg.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout_84.addWidget(self.label_XDeg)

        self.spin_XDeg = MyQSpin(self.w_XDeg)
        self.spin_XDeg.setObjectName(u"spin_XDeg")
        self.spin_XDeg.setMinimumSize(QSize(55, 24))
        self.spin_XDeg.setMaximumSize(QSize(1000000, 24))
        self.spin_XDeg.setFont(font)
        self.spin_XDeg.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_XDeg.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)

        self.verticalLayout_84.addWidget(self.spin_XDeg)


        self.horizontalLayout_6.addWidget(self.w_XDeg)

        self.w_YDeg = QWidget(self.w_PolyDegree)
        self.w_YDeg.setObjectName(u"w_YDeg")
        self.w_YDeg.setMinimumSize(QSize(0, 44))
        self.w_YDeg.setMaximumSize(QSize(16777215, 44))
        self.verticalLayout_85 = QVBoxLayout(self.w_YDeg)
        self.verticalLayout_85.setSpacing(0)
        self.verticalLayout_85.setObjectName(u"verticalLayout_85")
        self.verticalLayout_85.setContentsMargins(0, 0, 0, 0)
        self.label_YDeg = QLabel(self.w_YDeg)
        self.label_YDeg.setObjectName(u"label_YDeg")
        sizePolicy3.setHeightForWidth(self.label_YDeg.sizePolicy().hasHeightForWidth())
        self.label_YDeg.setSizePolicy(sizePolicy3)
        self.label_YDeg.setMinimumSize(QSize(55, 20))
        self.label_YDeg.setMaximumSize(QSize(16777215, 20))
        self.label_YDeg.setFont(font5)
        self.label_YDeg.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout_85.addWidget(self.label_YDeg)

        self.spin_YDeg = MyQSpin(self.w_YDeg)
        self.spin_YDeg.setObjectName(u"spin_YDeg")
        self.spin_YDeg.setMinimumSize(QSize(55, 24))
        self.spin_YDeg.setMaximumSize(QSize(1000000, 24))
        self.spin_YDeg.setFont(font)
        self.spin_YDeg.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_YDeg.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)

        self.verticalLayout_85.addWidget(self.spin_YDeg)


        self.horizontalLayout_6.addWidget(self.w_YDeg)

        self.w_ZDeg = QWidget(self.w_PolyDegree)
        self.w_ZDeg.setObjectName(u"w_ZDeg")
        self.w_ZDeg.setMinimumSize(QSize(0, 44))
        self.w_ZDeg.setMaximumSize(QSize(16777215, 44))
        self.verticalLayout_86 = QVBoxLayout(self.w_ZDeg)
        self.verticalLayout_86.setSpacing(0)
        self.verticalLayout_86.setObjectName(u"verticalLayout_86")
        self.verticalLayout_86.setContentsMargins(0, 0, 0, 0)
        self.label_ZDeg = QLabel(self.w_ZDeg)
        self.label_ZDeg.setObjectName(u"label_ZDeg")
        sizePolicy3.setHeightForWidth(self.label_ZDeg.sizePolicy().hasHeightForWidth())
        self.label_ZDeg.setSizePolicy(sizePolicy3)
        self.label_ZDeg.setMinimumSize(QSize(55, 20))
        self.label_ZDeg.setMaximumSize(QSize(16777215, 20))
        self.label_ZDeg.setFont(font5)
        self.label_ZDeg.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout_86.addWidget(self.label_ZDeg)

        self.spin_ZDeg = MyQSpin(self.w_ZDeg)
        self.spin_ZDeg.setObjectName(u"spin_ZDeg")
        self.spin_ZDeg.setMinimumSize(QSize(55, 24))
        self.spin_ZDeg.setMaximumSize(QSize(1000000, 24))
        self.spin_ZDeg.setFont(font)
        self.spin_ZDeg.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_ZDeg.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)

        self.verticalLayout_86.addWidget(self.spin_ZDeg)


        self.horizontalLayout_6.addWidget(self.w_ZDeg)


        self.horizontalLayout_5.addWidget(self.w_PolyDegree)

        self.w_CamMod_par.addWidget(self.w_PolyDegree_par)
        self.page = QWidget()
        self.page.setObjectName(u"page")
        self.horizontalLayout_11 = QHBoxLayout(self.page)
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.horizontalLayout_11.setContentsMargins(0, 0, 0, 0)
        self.w_PinholePar = QWidget(self.page)
        self.w_PinholePar.setObjectName(u"w_PinholePar")
        sizePolicy.setHeightForWidth(self.w_PinholePar.sizePolicy().hasHeightForWidth())
        self.w_PinholePar.setSizePolicy(sizePolicy)
        self.w_PinholePar.setMinimumSize(QSize(0, 44))
        self.horizontalLayout_10 = QHBoxLayout(self.w_PinholePar)
        self.horizontalLayout_10.setSpacing(6)
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.horizontalLayout_10.setContentsMargins(0, 0, 0, 0)
        self.w_PixAR = QWidget(self.w_PinholePar)
        self.w_PixAR.setObjectName(u"w_PixAR")
        self.w_PixAR.setMinimumSize(QSize(0, 44))
        self.w_PixAR.setMaximumSize(QSize(16777215, 44))
        self.verticalLayout_87 = QVBoxLayout(self.w_PixAR)
        self.verticalLayout_87.setSpacing(0)
        self.verticalLayout_87.setObjectName(u"verticalLayout_87")
        self.verticalLayout_87.setContentsMargins(0, 0, 0, 0)
        self.label_PixAR = QLabel(self.w_PixAR)
        self.label_PixAR.setObjectName(u"label_PixAR")
        sizePolicy3.setHeightForWidth(self.label_PixAR.sizePolicy().hasHeightForWidth())
        self.label_PixAR.setSizePolicy(sizePolicy3)
        self.label_PixAR.setMinimumSize(QSize(55, 20))
        self.label_PixAR.setMaximumSize(QSize(16777215, 20))
        self.label_PixAR.setFont(font5)
        self.label_PixAR.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout_87.addWidget(self.label_PixAR)

        self.spin_PixAR = MyQDoubleSpin(self.w_PixAR)
        self.spin_PixAR.setObjectName(u"spin_PixAR")
        self.spin_PixAR.setMinimumSize(QSize(55, 24))
        self.spin_PixAR.setMaximumSize(QSize(1000000, 24))
        self.spin_PixAR.setFont(font)
        self.spin_PixAR.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_PixAR.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
        self.spin_PixAR.setDecimals(3)
        self.spin_PixAR.setMaximum(10000000000000000000000.000000000000000)
        self.spin_PixAR.setValue(1.000000000000000)

        self.verticalLayout_87.addWidget(self.spin_PixAR)


        self.horizontalLayout_10.addWidget(self.w_PixAR)

        self.w_PixPitch = QWidget(self.w_PinholePar)
        self.w_PixPitch.setObjectName(u"w_PixPitch")
        self.w_PixPitch.setMinimumSize(QSize(0, 44))
        self.w_PixPitch.setMaximumSize(QSize(16777215, 44))
        self.verticalLayout_88 = QVBoxLayout(self.w_PixPitch)
        self.verticalLayout_88.setSpacing(0)
        self.verticalLayout_88.setObjectName(u"verticalLayout_88")
        self.verticalLayout_88.setContentsMargins(0, 0, 0, 0)
        self.label_PixPitch = QLabel(self.w_PixPitch)
        self.label_PixPitch.setObjectName(u"label_PixPitch")
        sizePolicy3.setHeightForWidth(self.label_PixPitch.sizePolicy().hasHeightForWidth())
        self.label_PixPitch.setSizePolicy(sizePolicy3)
        self.label_PixPitch.setMinimumSize(QSize(55, 20))
        self.label_PixPitch.setMaximumSize(QSize(16777215, 20))
        self.label_PixPitch.setFont(font5)
        self.label_PixPitch.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout_88.addWidget(self.label_PixPitch)

        self.spin_PixPitch = MyQDoubleSpin(self.w_PixPitch)
        self.spin_PixPitch.setObjectName(u"spin_PixPitch")
        self.spin_PixPitch.setMinimumSize(QSize(55, 24))
        self.spin_PixPitch.setMaximumSize(QSize(1000000, 24))
        self.spin_PixPitch.setFont(font)
        self.spin_PixPitch.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_PixPitch.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
        self.spin_PixPitch.setDecimals(6)
        self.spin_PixPitch.setMaximum(10000000000000000000000.000000000000000)
        self.spin_PixPitch.setValue(0.006500000000000)

        self.verticalLayout_88.addWidget(self.spin_PixPitch)


        self.horizontalLayout_10.addWidget(self.w_PixPitch)


        self.horizontalLayout_11.addWidget(self.w_PinholePar)

        self.w_CamMod_par.addWidget(self.page)

        self.horizontalLayout_3.addWidget(self.w_CamMod_par)

        self.horizontalLayout_3.setStretch(0, 1)
        self.horizontalLayout_3.setStretch(2, 3)

        self.verticalLayout.addWidget(self.w_CamModel)

        self.w_CorrModel = QWidget(self.w_Calibration_Parameters)
        self.w_CorrModel.setObjectName(u"w_CorrModel")
        self.w_CorrModel.setMinimumSize(QSize(0, 44))
        self.w_CorrModel.setMaximumSize(QSize(16777215, 44))
        self.horizontalLayout_14 = QHBoxLayout(self.w_CorrModel)
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.horizontalLayout_14.setContentsMargins(0, 0, 0, 0)
        self.w_CorrMod = QWidget(self.w_CorrModel)
        self.w_CorrMod.setObjectName(u"w_CorrMod")
        self.w_CorrMod.setMinimumSize(QSize(150, 0))
        self.w_CorrMod.setMaximumSize(QSize(150, 16777215))
        self.verticalLayout_4 = QVBoxLayout(self.w_CorrMod)
        self.verticalLayout_4.setSpacing(0)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.label_CorrMod = QLabel(self.w_CorrMod)
        self.label_CorrMod.setObjectName(u"label_CorrMod")
        sizePolicy3.setHeightForWidth(self.label_CorrMod.sizePolicy().hasHeightForWidth())
        self.label_CorrMod.setSizePolicy(sizePolicy3)
        self.label_CorrMod.setMinimumSize(QSize(0, 20))
        self.label_CorrMod.setMaximumSize(QSize(16777215, 20))
        self.label_CorrMod.setFont(font5)

        self.verticalLayout_4.addWidget(self.label_CorrMod)

        self.combo_CorrMod = MyQCombo(self.w_CorrMod)
        self.combo_CorrMod.addItem("")
        self.combo_CorrMod.addItem("")
        self.combo_CorrMod.addItem("")
        self.combo_CorrMod.addItem("")
        self.combo_CorrMod.addItem("")
        self.combo_CorrMod.addItem("")
        self.combo_CorrMod.addItem("")
        self.combo_CorrMod.addItem("")
        self.combo_CorrMod.setObjectName(u"combo_CorrMod")
        sizePolicy.setHeightForWidth(self.combo_CorrMod.sizePolicy().hasHeightForWidth())
        self.combo_CorrMod.setSizePolicy(sizePolicy)
        self.combo_CorrMod.setMinimumSize(QSize(0, 24))
        self.combo_CorrMod.setMaximumSize(QSize(16777215, 24))
        self.combo_CorrMod.setFont(font)
        self.combo_CorrMod.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContentsOnFirstShow)

        self.verticalLayout_4.addWidget(self.combo_CorrMod)


        self.horizontalLayout_14.addWidget(self.w_CorrMod)

        self.hs_CorrMod = QSpacerItem(9, 41, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_14.addItem(self.hs_CorrMod)

        self.w_CylPar = QWidget(self.w_CorrModel)
        self.w_CylPar.setObjectName(u"w_CylPar")
        sizePolicy.setHeightForWidth(self.w_CylPar.sizePolicy().hasHeightForWidth())
        self.w_CylPar.setSizePolicy(sizePolicy)
        self.w_CylPar.setMinimumSize(QSize(0, 44))
        self.horizontalLayout_15 = QHBoxLayout(self.w_CylPar)
        self.horizontalLayout_15.setSpacing(6)
        self.horizontalLayout_15.setObjectName(u"horizontalLayout_15")
        self.horizontalLayout_15.setContentsMargins(0, 0, 0, 0)
        self.w_CylRad = QWidget(self.w_CylPar)
        self.w_CylRad.setObjectName(u"w_CylRad")
        self.w_CylRad.setMinimumSize(QSize(0, 44))
        self.w_CylRad.setMaximumSize(QSize(16777215, 44))
        self.verticalLayout_89 = QVBoxLayout(self.w_CylRad)
        self.verticalLayout_89.setSpacing(0)
        self.verticalLayout_89.setObjectName(u"verticalLayout_89")
        self.verticalLayout_89.setContentsMargins(0, 0, 0, 0)
        self.label_CylRad = QLabel(self.w_CylRad)
        self.label_CylRad.setObjectName(u"label_CylRad")
        sizePolicy3.setHeightForWidth(self.label_CylRad.sizePolicy().hasHeightForWidth())
        self.label_CylRad.setSizePolicy(sizePolicy3)
        self.label_CylRad.setMinimumSize(QSize(55, 20))
        self.label_CylRad.setMaximumSize(QSize(16777215, 20))
        self.label_CylRad.setFont(font5)
        self.label_CylRad.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout_89.addWidget(self.label_CylRad)

        self.spin_CylRad = MyQDoubleSpin(self.w_CylRad)
        self.spin_CylRad.setObjectName(u"spin_CylRad")
        self.spin_CylRad.setMinimumSize(QSize(55, 24))
        self.spin_CylRad.setMaximumSize(QSize(1000000, 24))
        self.spin_CylRad.setFont(font)
        self.spin_CylRad.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_CylRad.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
        self.spin_CylRad.setDecimals(3)
        self.spin_CylRad.setMaximum(10000000000000000000000.000000000000000)
        self.spin_CylRad.setSingleStep(0.100000000000000)
        self.spin_CylRad.setValue(30.000000000000000)

        self.verticalLayout_89.addWidget(self.spin_CylRad)


        self.horizontalLayout_15.addWidget(self.w_CylRad)

        self.w_CylThick = QWidget(self.w_CylPar)
        self.w_CylThick.setObjectName(u"w_CylThick")
        self.w_CylThick.setMinimumSize(QSize(0, 44))
        self.w_CylThick.setMaximumSize(QSize(16777215, 44))
        self.verticalLayout_90 = QVBoxLayout(self.w_CylThick)
        self.verticalLayout_90.setSpacing(0)
        self.verticalLayout_90.setObjectName(u"verticalLayout_90")
        self.verticalLayout_90.setContentsMargins(0, 0, 0, 0)
        self.label_CylThick = QLabel(self.w_CylThick)
        self.label_CylThick.setObjectName(u"label_CylThick")
        sizePolicy3.setHeightForWidth(self.label_CylThick.sizePolicy().hasHeightForWidth())
        self.label_CylThick.setSizePolicy(sizePolicy3)
        self.label_CylThick.setMinimumSize(QSize(55, 20))
        self.label_CylThick.setMaximumSize(QSize(16777215, 20))
        self.label_CylThick.setFont(font5)
        self.label_CylThick.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout_90.addWidget(self.label_CylThick)

        self.spin_CylThick = MyQDoubleSpin(self.w_CylThick)
        self.spin_CylThick.setObjectName(u"spin_CylThick")
        self.spin_CylThick.setMinimumSize(QSize(55, 24))
        self.spin_CylThick.setMaximumSize(QSize(1000000, 24))
        self.spin_CylThick.setFont(font)
        self.spin_CylThick.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_CylThick.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
        self.spin_CylThick.setDecimals(3)
        self.spin_CylThick.setMaximum(10000000000000000000000.000000000000000)
        self.spin_CylThick.setSingleStep(0.100000000000000)
        self.spin_CylThick.setValue(2.000000000000000)

        self.verticalLayout_90.addWidget(self.spin_CylThick)


        self.horizontalLayout_15.addWidget(self.w_CylThick)

        self.w_CylNRatio = QWidget(self.w_CylPar)
        self.w_CylNRatio.setObjectName(u"w_CylNRatio")
        self.w_CylNRatio.setMinimumSize(QSize(0, 44))
        self.w_CylNRatio.setMaximumSize(QSize(16777215, 44))
        self.verticalLayout_91 = QVBoxLayout(self.w_CylNRatio)
        self.verticalLayout_91.setSpacing(0)
        self.verticalLayout_91.setObjectName(u"verticalLayout_91")
        self.verticalLayout_91.setContentsMargins(0, 0, 0, 0)
        self.label_CylNRatio = QLabel(self.w_CylNRatio)
        self.label_CylNRatio.setObjectName(u"label_CylNRatio")
        sizePolicy3.setHeightForWidth(self.label_CylNRatio.sizePolicy().hasHeightForWidth())
        self.label_CylNRatio.setSizePolicy(sizePolicy3)
        self.label_CylNRatio.setMinimumSize(QSize(55, 20))
        self.label_CylNRatio.setMaximumSize(QSize(16777215, 20))
        self.label_CylNRatio.setFont(font5)
        self.label_CylNRatio.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout_91.addWidget(self.label_CylNRatio)

        self.spin_CylNRatio = MyQDoubleSpin(self.w_CylNRatio)
        self.spin_CylNRatio.setObjectName(u"spin_CylNRatio")
        self.spin_CylNRatio.setMinimumSize(QSize(55, 24))
        self.spin_CylNRatio.setMaximumSize(QSize(1000000, 24))
        self.spin_CylNRatio.setFont(font)
        self.spin_CylNRatio.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_CylNRatio.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
        self.spin_CylNRatio.setDecimals(3)
        self.spin_CylNRatio.setMaximum(10000000000000000000000.000000000000000)
        self.spin_CylNRatio.setSingleStep(0.100000000000000)
        self.spin_CylNRatio.setValue(1.000000000000000)

        self.verticalLayout_91.addWidget(self.spin_CylNRatio)


        self.horizontalLayout_15.addWidget(self.w_CylNRatio)


        self.horizontalLayout_14.addWidget(self.w_CylPar)


        self.verticalLayout.addWidget(self.w_CorrModel)

        self.w_CalibProc_Cyl = QWidget(self.w_Calibration_Parameters)
        self.w_CalibProc_Cyl.setObjectName(u"w_CalibProc_Cyl")
        self.w_CalibProc_Cyl.setMinimumSize(QSize(0, 44))
        self.w_CalibProc_Cyl.setMaximumSize(QSize(16777215, 44))
        self.horizontalLayout_18 = QHBoxLayout(self.w_CalibProc_Cyl)
        self.horizontalLayout_18.setSpacing(12)
        self.horizontalLayout_18.setObjectName(u"horizontalLayout_18")
        self.horizontalLayout_18.setContentsMargins(0, 0, 0, 0)
        self.w_CorrMod_Cyl = QWidget(self.w_CalibProc_Cyl)
        self.w_CorrMod_Cyl.setObjectName(u"w_CorrMod_Cyl")
        self.verticalLayout_7 = QVBoxLayout(self.w_CorrMod_Cyl)
        self.verticalLayout_7.setSpacing(0)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.verticalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.label_CorrMod_Cyl = QLabel(self.w_CorrMod_Cyl)
        self.label_CorrMod_Cyl.setObjectName(u"label_CorrMod_Cyl")
        sizePolicy3.setHeightForWidth(self.label_CorrMod_Cyl.sizePolicy().hasHeightForWidth())
        self.label_CorrMod_Cyl.setSizePolicy(sizePolicy3)
        self.label_CorrMod_Cyl.setMinimumSize(QSize(0, 20))
        self.label_CorrMod_Cyl.setMaximumSize(QSize(16777215, 20))
        self.label_CorrMod_Cyl.setFont(font5)

        self.verticalLayout_7.addWidget(self.label_CorrMod_Cyl)

        self.combo_CorrMod_Cyl = MyQCombo(self.w_CorrMod_Cyl)
        self.combo_CorrMod_Cyl.addItem("")
        self.combo_CorrMod_Cyl.addItem("")
        self.combo_CorrMod_Cyl.addItem("")
        self.combo_CorrMod_Cyl.addItem("")
        self.combo_CorrMod_Cyl.addItem("")
        self.combo_CorrMod_Cyl.addItem("")
        self.combo_CorrMod_Cyl.setObjectName(u"combo_CorrMod_Cyl")
        sizePolicy.setHeightForWidth(self.combo_CorrMod_Cyl.sizePolicy().hasHeightForWidth())
        self.combo_CorrMod_Cyl.setSizePolicy(sizePolicy)
        self.combo_CorrMod_Cyl.setMinimumSize(QSize(0, 24))
        self.combo_CorrMod_Cyl.setMaximumSize(QSize(16777215, 24))
        self.combo_CorrMod_Cyl.setFont(font)
        self.combo_CorrMod_Cyl.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContentsOnFirstShow)

        self.verticalLayout_7.addWidget(self.combo_CorrMod_Cyl)


        self.horizontalLayout_18.addWidget(self.w_CorrMod_Cyl)

        self.check_SaveLOS = QCheckBox(self.w_CalibProc_Cyl)
        self.check_SaveLOS.setObjectName(u"check_SaveLOS")
        self.check_SaveLOS.setFont(font)

        self.horizontalLayout_18.addWidget(self.check_SaveLOS)

        self.hs_CalibProc_Cyl = QSpacerItem(9, 41, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_18.addItem(self.hs_CalibProc_Cyl)


        self.verticalLayout.addWidget(self.w_CalibProc_Cyl)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_3)


        self.verticalLayout_11.addWidget(self.w_Calibration_Parameters)


        self.verticalLayout_10.addWidget(self.CollapBox_Calibration)

        self.verticalSpacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_10.addItem(self.verticalSpacer)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout_65.addWidget(self.scrollArea)

        QWidget.setTabOrder(self.button_back, self.button_forward)
        QWidget.setTabOrder(self.button_forward, self.button_close_tab)
        QWidget.setTabOrder(self.button_close_tab, self.scrollArea)

        self.retranslateUi(ProcessTab_CalVi)

        self.w_CamMod_par.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(ProcessTab_CalVi)
    # setupUi

    def retranslateUi(self, ProcessTab_CalVi):
        ProcessTab_CalVi.setWindowTitle(QCoreApplication.translate("ProcessTab_CalVi", u"Process", None))
        self.icon.setText("")
        self.name_tab.setText(QCoreApplication.translate("ProcessTab_CalVi", u" Process", None))
        self.label_number.setText(QCoreApplication.translate("ProcessTab_CalVi", u"1", None))
#if QT_CONFIG(tooltip)
        self.button_back.setToolTip(QCoreApplication.translate("ProcessTab_CalVi", u"Undo", None))
#endif // QT_CONFIG(tooltip)
        self.button_back.setText("")
#if QT_CONFIG(tooltip)
        self.button_forward.setToolTip(QCoreApplication.translate("ProcessTab_CalVi", u"Redo", None))
#endif // QT_CONFIG(tooltip)
        self.button_forward.setText("")
#if QT_CONFIG(tooltip)
        self.button_close_tab.setToolTip(QCoreApplication.translate("ProcessTab_CalVi", u"Close tab", None))
#endif // QT_CONFIG(tooltip)
        self.button_close_tab.setText("")
#if QT_CONFIG(shortcut)
        self.button_close_tab.setShortcut(QCoreApplication.translate("ProcessTab_CalVi", u"Alt+P", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(tooltip)
        self.tool_CollapBox_Target.setToolTip(QCoreApplication.translate("ProcessTab_CalVi", u"Target parameters option box", None))
#endif // QT_CONFIG(tooltip)
        self.tool_CollapBox_Target.setText(QCoreApplication.translate("ProcessTab_CalVi", u"Target parameters", None))
#if QT_CONFIG(tooltip)
        self.button_CollapBox_Target.setToolTip(QCoreApplication.translate("ProcessTab_CalVi", u"Set default options for this section", None))
#endif // QT_CONFIG(tooltip)
        self.button_CollapBox_Target.setText("")
        self.w_Target_Parameters.setTitle("")
        self.label_DotColor.setText("")
#if QT_CONFIG(tooltip)
        self.button_DotColor.setToolTip(QCoreApplication.translate("ProcessTab_CalVi", u"White/black dot in the image", None))
#endif // QT_CONFIG(tooltip)
        self.button_DotColor.setText(QCoreApplication.translate("ProcessTab_CalVi", u"White dot", None))
        self.label_DotTypeSearch.setText(QCoreApplication.translate("ProcessTab_CalVi", u"Type of search", None))
        self.combo_DotTypeSearch.setItemText(0, QCoreApplication.translate("ProcessTab_CalVi", u"cross-correlation mask", None))
        self.combo_DotTypeSearch.setItemText(1, QCoreApplication.translate("ProcessTab_CalVi", u"top hat mask with tight tails", None))
        self.combo_DotTypeSearch.setItemText(2, QCoreApplication.translate("ProcessTab_CalVi", u"top hat mask with broad tails", None))
        self.combo_DotTypeSearch.setItemText(3, QCoreApplication.translate("ProcessTab_CalVi", u"Gaussian mask", None))
        self.combo_DotTypeSearch.setItemText(4, QCoreApplication.translate("ProcessTab_CalVi", u"interpolation", None))
        self.combo_DotTypeSearch.setItemText(5, QCoreApplication.translate("ProcessTab_CalVi", u"centroid", None))

#if QT_CONFIG(tooltip)
        self.combo_DotTypeSearch.setToolTip(QCoreApplication.translate("ProcessTab_CalVi", u"Type of search for control points", None))
#endif // QT_CONFIG(tooltip)
        self.label_DotThresh.setText(QCoreApplication.translate("ProcessTab_CalVi", u"Threshold", None))
#if QT_CONFIG(tooltip)
        self.spin_DotThresh.setToolTip(QCoreApplication.translate("ProcessTab_CalVi", u"Threshold on maximum/minimum value for search of control points", None))
#endif // QT_CONFIG(tooltip)
        self.label_DotDiam.setText(QCoreApplication.translate("ProcessTab_CalVi", u"Dot diameter (pix.)", None))
#if QT_CONFIG(tooltip)
        self.spin_DotDiam.setToolTip(QCoreApplication.translate("ProcessTab_CalVi", u"Dot diameter in pixels (search radius is 2.5 times this value)", None))
#endif // QT_CONFIG(tooltip)
        self.label_TargetType.setText(QCoreApplication.translate("ProcessTab_CalVi", u"Type of target", None))
        self.combo_TargetType.setItemText(0, QCoreApplication.translate("ProcessTab_CalVi", u"single plane", None))
        self.combo_TargetType.setItemText(1, QCoreApplication.translate("ProcessTab_CalVi", u"double plane", None))

#if QT_CONFIG(tooltip)
        self.combo_TargetType.setToolTip(QCoreApplication.translate("ProcessTab_CalVi", u"Type of target (single or double plane)", None))
#endif // QT_CONFIG(tooltip)
        self.label_DotDx.setText(QCoreApplication.translate("ProcessTab_CalVi", u"x dot spacing (mm)", None))
#if QT_CONFIG(tooltip)
        self.spin_DotDx.setToolTip(QCoreApplication.translate("ProcessTab_CalVi", u"Spacing of dots along x on each level of the target", None))
#endif // QT_CONFIG(tooltip)
        self.label_DotDy.setText(QCoreApplication.translate("ProcessTab_CalVi", u"y dot spacing (mm)", None))
#if QT_CONFIG(tooltip)
        self.spin_DotDy.setToolTip(QCoreApplication.translate("ProcessTab_CalVi", u"Spacing of dots along y on each level of the target", None))
#endif // QT_CONFIG(tooltip)
        self.label_OriginXShift.setText(QCoreApplication.translate("ProcessTab_CalVi", u"Origin x shift (mm)", None))
#if QT_CONFIG(tooltip)
        self.spin_OriginXShift.setToolTip(QCoreApplication.translate("ProcessTab_CalVi", u"Shift of the origin along x on the second level of the target", None))
#endif // QT_CONFIG(tooltip)
        self.label_OriginYShift.setText(QCoreApplication.translate("ProcessTab_CalVi", u"Origin y shift (mm)", None))
#if QT_CONFIG(tooltip)
        self.spin_OriginYShift.setToolTip(QCoreApplication.translate("ProcessTab_CalVi", u"Shift of the origin along y on the second level of the target", None))
#endif // QT_CONFIG(tooltip)
        self.label_OriginZShift.setText(QCoreApplication.translate("ProcessTab_CalVi", u"Origin z shift (mm)", None))
#if QT_CONFIG(tooltip)
        self.spin_OriginZShift.setToolTip(QCoreApplication.translate("ProcessTab_CalVi", u"Shift of the origin along z on the second level of the target", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.tool_CollapBox_CalPar.setToolTip(QCoreApplication.translate("ProcessTab_CalVi", u"Interpolation option box", None))
#endif // QT_CONFIG(tooltip)
        self.tool_CollapBox_CalPar.setText(QCoreApplication.translate("ProcessTab_CalVi", u"Calibration parameters", None))
#if QT_CONFIG(tooltip)
        self.button_CollapBox_CalPar.setToolTip(QCoreApplication.translate("ProcessTab_CalVi", u"Set default options for the selected type of process", None))
#endif // QT_CONFIG(tooltip)
        self.button_CollapBox_CalPar.setText("")
        self.w_Calibration_Parameters.setTitle("")
        self.label_CalibProcType.setText(QCoreApplication.translate("ProcessTab_CalVi", u"Calibration procedure", None))
        self.combo_CalibProcType.setItemText(0, QCoreApplication.translate("ProcessTab_CalVi", u"standard", None))
        self.combo_CalibProcType.setItemText(1, QCoreApplication.translate("ProcessTab_CalVi", u"unknown planes", None))
        self.combo_CalibProcType.setItemText(2, QCoreApplication.translate("ProcessTab_CalVi", u"equation of the plane", None))
        self.combo_CalibProcType.setItemText(3, QCoreApplication.translate("ProcessTab_CalVi", u"cylinder", None))

#if QT_CONFIG(tooltip)
        self.combo_CalibProcType.setToolTip(QCoreApplication.translate("ProcessTab_CalVi", u"Type of calibration procedure", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.check_Plane.setToolTip(QCoreApplication.translate("ProcessTab_CalVi", u"Optimize the plane constants", None))
#endif // QT_CONFIG(tooltip)
        self.check_Plane.setText(QCoreApplication.translate("ProcessTab_CalVi", u"Opt. plane const.", None))
#if QT_CONFIG(tooltip)
        self.check_Pinhole.setToolTip(QCoreApplication.translate("ProcessTab_CalVi", u"Optimize the pinhole parameters", None))
#endif // QT_CONFIG(tooltip)
        self.check_Pinhole.setText(QCoreApplication.translate("ProcessTab_CalVi", u"Opt. pinhole par.", None))
        self.label_CamMod.setText(QCoreApplication.translate("ProcessTab_CalVi", u"Camera calibration model", None))
        self.combo_CamMod.setItemText(0, QCoreApplication.translate("ProcessTab_CalVi", u"polynomial", None))
        self.combo_CamMod.setItemText(1, QCoreApplication.translate("ProcessTab_CalVi", u"rational", None))
        self.combo_CamMod.setItemText(2, QCoreApplication.translate("ProcessTab_CalVi", u"tri-polynomial", None))
        self.combo_CamMod.setItemText(3, QCoreApplication.translate("ProcessTab_CalVi", u"pinhole", None))
        self.combo_CamMod.setItemText(4, QCoreApplication.translate("ProcessTab_CalVi", u"pinhole + cylinder", None))

#if QT_CONFIG(tooltip)
        self.combo_CamMod.setToolTip(QCoreApplication.translate("ProcessTab_CalVi", u"Type of mapping function", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.w_CamMod_par.setToolTip(QCoreApplication.translate("ProcessTab_CalVi", u"Value of kernel/order (integer)", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.label_XDeg.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.label_XDeg.setText(QCoreApplication.translate("ProcessTab_CalVi", u"x degree", None))
#if QT_CONFIG(tooltip)
        self.spin_XDeg.setToolTip(QCoreApplication.translate("ProcessTab_CalVi", u"Degree of polynomial along x", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.label_YDeg.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.label_YDeg.setText(QCoreApplication.translate("ProcessTab_CalVi", u"y degree", None))
#if QT_CONFIG(tooltip)
        self.spin_YDeg.setToolTip(QCoreApplication.translate("ProcessTab_CalVi", u"Degree of polynomial along y", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.label_ZDeg.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.label_ZDeg.setText(QCoreApplication.translate("ProcessTab_CalVi", u"z degree", None))
#if QT_CONFIG(tooltip)
        self.spin_ZDeg.setToolTip(QCoreApplication.translate("ProcessTab_CalVi", u"Degree of polynomial along z", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.label_PixAR.setToolTip(QCoreApplication.translate("ProcessTab_CalVi", u"Pixel aspect ratio (y/x)", None))
#endif // QT_CONFIG(tooltip)
        self.label_PixAR.setText(QCoreApplication.translate("ProcessTab_CalVi", u"Pixel AR (y/x)", None))
#if QT_CONFIG(tooltip)
        self.spin_PixAR.setToolTip(QCoreApplication.translate("ProcessTab_CalVi", u"Pixel aspect ratio (y/x)", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.label_PixPitch.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.label_PixPitch.setText(QCoreApplication.translate("ProcessTab_CalVi", u"Pixel pitch (mm)", None))
#if QT_CONFIG(tooltip)
        self.spin_PixPitch.setToolTip(QCoreApplication.translate("ProcessTab_CalVi", u"Pixel pitch in millimeter units", None))
#endif // QT_CONFIG(tooltip)
        self.label_CorrMod.setText(QCoreApplication.translate("ProcessTab_CalVi", u"Lens distornion model", None))
        self.combo_CorrMod.setItemText(0, QCoreApplication.translate("ProcessTab_CalVi", u"a: no correction (DLT) ", None))
        self.combo_CorrMod.setItemText(1, QCoreApplication.translate("ProcessTab_CalVi", u"b: radial distortions", None))
        self.combo_CorrMod.setItemText(2, QCoreApplication.translate("ProcessTab_CalVi", u"c: b + tangential distortions", None))
        self.combo_CorrMod.setItemText(3, QCoreApplication.translate("ProcessTab_CalVi", u"d: c + cylinder origin", None))
        self.combo_CorrMod.setItemText(4, QCoreApplication.translate("ProcessTab_CalVi", u"e: d + cylinder rotation", None))
        self.combo_CorrMod.setItemText(5, QCoreApplication.translate("ProcessTab_CalVi", u"f: e + cylinder radius", None))
        self.combo_CorrMod.setItemText(6, QCoreApplication.translate("ProcessTab_CalVi", u"g: f + cylinder thickness", None))
        self.combo_CorrMod.setItemText(7, QCoreApplication.translate("ProcessTab_CalVi", u"h: g + refractive index ratio", None))

#if QT_CONFIG(tooltip)
        self.combo_CorrMod.setToolTip(QCoreApplication.translate("ProcessTab_CalVi", u"Parameters of the correction to be optimized", None))
#endif // QT_CONFIG(tooltip)
        self.label_CylRad.setText(QCoreApplication.translate("ProcessTab_CalVi", u"Cyl. radius (mm)", None))
#if QT_CONFIG(tooltip)
        self.spin_CylRad.setToolTip(QCoreApplication.translate("ProcessTab_CalVi", u"Initial value for cylinder internal radius in mm", None))
#endif // QT_CONFIG(tooltip)
        self.label_CylThick.setText(QCoreApplication.translate("ProcessTab_CalVi", u"thickness (mm)", None))
#if QT_CONFIG(tooltip)
        self.spin_CylThick.setToolTip(QCoreApplication.translate("ProcessTab_CalVi", u"Initial value for cylinder wall thickness in mm", None))
#endif // QT_CONFIG(tooltip)
        self.label_CylNRatio.setText(QCoreApplication.translate("ProcessTab_CalVi", u"n ratio", None))
#if QT_CONFIG(tooltip)
        self.spin_CylNRatio.setToolTip(QCoreApplication.translate("ProcessTab_CalVi", u"Refractive index ratio (fluid/solid wall)", None))
#endif // QT_CONFIG(tooltip)
        self.label_CorrMod_Cyl.setText(QCoreApplication.translate("ProcessTab_CalVi", u"Cylinder parameter optimization", None))
        self.combo_CorrMod_Cyl.setItemText(0, QCoreApplication.translate("ProcessTab_CalVi", u"a: cylinder origin and rotation", None))
        self.combo_CorrMod_Cyl.setItemText(1, QCoreApplication.translate("ProcessTab_CalVi", u"b: a + cylinder thickness", None))
        self.combo_CorrMod_Cyl.setItemText(2, QCoreApplication.translate("ProcessTab_CalVi", u"c: b + refraction index (n) ratio", None))
        self.combo_CorrMod_Cyl.setItemText(3, QCoreApplication.translate("ProcessTab_CalVi", u"d: b + internal radius", None))
        self.combo_CorrMod_Cyl.setItemText(4, QCoreApplication.translate("ProcessTab_CalVi", u"e: a + internal radius and n ratio", None))
        self.combo_CorrMod_Cyl.setItemText(5, QCoreApplication.translate("ProcessTab_CalVi", u"f: all cylinder parameters", None))

#if QT_CONFIG(tooltip)
        self.combo_CorrMod_Cyl.setToolTip(QCoreApplication.translate("ProcessTab_CalVi", u"Cylinder parameters of the correction to be optimized", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.check_SaveLOS.setToolTip(QCoreApplication.translate("ProcessTab_CalVi", u"Save physical coordinates of the intersections of the lines of sight with the cylinder", None))
#endif // QT_CONFIG(tooltip)
        self.check_SaveLOS.setText(QCoreApplication.translate("ProcessTab_CalVi", u"Save LOS", None))
    # retranslateUi


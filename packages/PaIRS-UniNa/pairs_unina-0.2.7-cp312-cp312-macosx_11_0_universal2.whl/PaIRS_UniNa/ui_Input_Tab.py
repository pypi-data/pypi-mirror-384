from .addwidgets_ps import icons_path
# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Input_TabYvlWwW.ui'
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
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QCheckBox, QComboBox,
    QFrame, QGroupBox, QHBoxLayout, QLabel,
    QLayout, QScrollArea, QSizePolicy, QSpacerItem,
    QToolButton, QVBoxLayout, QWidget)

from .Input_Tab_tools import ImageTreeWidget
from .addwidgets_ps import (ClickableEditLabel, ClickableLabel, CollapsibleBox, MyQCombo,
    MyQLineEdit, MyQSpin, MyTabLabel, MyToolButton)

class Ui_InputTab(object):
    def setupUi(self, InputTab):
        if not InputTab.objectName():
            InputTab.setObjectName(u"InputTab")
        InputTab.resize(500, 680)
        InputTab.setMinimumSize(QSize(500, 680))
        InputTab.setMaximumSize(QSize(1000, 16777215))
        font = QFont()
        font.setPointSize(11)
        InputTab.setFont(font)
        icon1 = QIcon()
        icon1.addFile(u""+ icons_path +"input_logo.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        InputTab.setWindowIcon(icon1)
        self.verticalLayout_7 = QVBoxLayout(InputTab)
        self.verticalLayout_7.setSpacing(5)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.verticalLayout_7.setContentsMargins(10, 10, 10, 10)
        self.w_Mode = QWidget(InputTab)
        self.w_Mode.setObjectName(u"w_Mode")
        self.w_Mode.setMinimumSize(QSize(0, 40))
        self.w_Mode.setMaximumSize(QSize(16777215, 40))
        self.w_Mode.setFont(font)
        self.horizontalLayout_5 = QHBoxLayout(self.w_Mode)
        self.horizontalLayout_5.setSpacing(3)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 10)
        self.icon = QLabel(self.w_Mode)
        self.icon.setObjectName(u"icon")
        self.icon.setMinimumSize(QSize(35, 35))
        self.icon.setMaximumSize(QSize(35, 35))
        self.icon.setPixmap(QPixmap(u""+ icons_path +"input_logo.png"))
        self.icon.setScaledContents(True)

        self.horizontalLayout_5.addWidget(self.icon)

        self.name_tab = MyTabLabel(self.w_Mode)
        self.name_tab.setObjectName(u"name_tab")
        self.name_tab.setMinimumSize(QSize(0, 35))
        self.name_tab.setMaximumSize(QSize(16777215, 35))
        font1 = QFont()
        font1.setFamilies([u"Arial"])
        font1.setPointSize(20)
        font1.setBold(True)
        self.name_tab.setFont(font1)

        self.horizontalLayout_5.addWidget(self.name_tab)

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


        self.horizontalLayout_5.addWidget(self.w_label_done)

        self.label_process = QLabel(self.w_Mode)
        self.label_process.setObjectName(u"label_process")
        self.label_process.setMinimumSize(QSize(60, 30))
        self.label_process.setMaximumSize(QSize(60, 30))
        font2 = QFont()
        font2.setPointSize(10)
        font2.setItalic(True)
        self.label_process.setFont(font2)
        self.label_process.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_5.addWidget(self.label_process)

        self.combo_process = MyQCombo(self.w_Mode)
        self.combo_process.addItem("")
        self.combo_process.addItem("")
        self.combo_process.addItem("")
        self.combo_process.addItem("")
        self.combo_process.setObjectName(u"combo_process")
        self.combo_process.setMinimumSize(QSize(100, 30))
        self.combo_process.setMaximumSize(QSize(100, 30))
        self.combo_process.setFont(font)

        self.horizontalLayout_5.addWidget(self.combo_process)

        self.hs1 = QSpacerItem(70, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.hs1)

        self.label_number = QLabel(self.w_Mode)
        self.label_number.setObjectName(u"label_number")
        self.label_number.setMinimumSize(QSize(35, 0))
        font3 = QFont()
        font3.setPointSize(9)
        self.label_number.setFont(font3)
        self.label_number.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_5.addWidget(self.label_number)

        self.hs_2 = QSpacerItem(5, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.hs_2)

        self.button_back = QToolButton(self.w_Mode)
        self.button_back.setObjectName(u"button_back")
        self.button_back.setMinimumSize(QSize(24, 24))
        self.button_back.setMaximumSize(QSize(24, 24))
        icon2 = QIcon()
        icon2.addFile(u""+ icons_path +"undo.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.button_back.setIcon(icon2)
        self.button_back.setIconSize(QSize(20, 20))

        self.horizontalLayout_5.addWidget(self.button_back)

        self.button_forward = QToolButton(self.w_Mode)
        self.button_forward.setObjectName(u"button_forward")
        self.button_forward.setMinimumSize(QSize(24, 24))
        self.button_forward.setMaximumSize(QSize(24, 24))
        icon3 = QIcon()
        icon3.addFile(u""+ icons_path +"redo.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.button_forward.setIcon(icon3)
        self.button_forward.setIconSize(QSize(20, 20))

        self.horizontalLayout_5.addWidget(self.button_forward)

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
        icon4 = QIcon()
        icon4.addFile(u""+ icons_path +"close.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.button_close_tab.setIcon(icon4)
        self.button_close_tab.setIconSize(QSize(15, 15))

        self.horizontalLayout_3.addWidget(self.button_close_tab)


        self.horizontalLayout_5.addWidget(self.w_button_close_tab)


        self.verticalLayout_7.addWidget(self.w_Mode)

        self.line = QFrame(InputTab)
        self.line.setObjectName(u"line")
        self.line.setMinimumSize(QSize(0, 5))
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_7.addWidget(self.line)

        self.scrollArea = QScrollArea(InputTab)
        self.scrollArea.setObjectName(u"scrollArea")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollArea.sizePolicy().hasHeightForWidth())
        self.scrollArea.setSizePolicy(sizePolicy)
        self.scrollArea.setMinimumSize(QSize(0, 0))
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
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 480, 605))
        self.scrollAreaWidgetContents.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.verticalLayout_8 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_8.setSpacing(10)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.verticalLayout_8.setContentsMargins(0, 15, 10, 0)
        self.w_InputFold_Button = QWidget(self.scrollAreaWidgetContents)
        self.w_InputFold_Button.setObjectName(u"w_InputFold_Button")
        self.w_InputFold_Button.setMinimumSize(QSize(400, 0))
        self.w_InputFold_Button.setMaximumSize(QSize(16777215, 44))
        self.horizontalLayout = QHBoxLayout(self.w_InputFold_Button)
        self.horizontalLayout.setSpacing(10)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.w_InputFold = QWidget(self.w_InputFold_Button)
        self.w_InputFold.setObjectName(u"w_InputFold")
        self.w_InputFold.setMinimumSize(QSize(320, 0))
        self.w_InputFold.setMaximumSize(QSize(16777215, 42))
        self.verticalLayout = QVBoxLayout(self.w_InputFold)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.w_label_path_2 = QWidget(self.w_InputFold)
        self.w_label_path_2.setObjectName(u"w_label_path_2")
        self.w_label_path = QHBoxLayout(self.w_label_path_2)
        self.w_label_path.setSpacing(10)
        self.w_label_path.setObjectName(u"w_label_path")
        self.w_label_path.setContentsMargins(0, 0, 0, 0)
        self.label_path = QLabel(self.w_label_path_2)
        self.label_path.setObjectName(u"label_path")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label_path.sizePolicy().hasHeightForWidth())
        self.label_path.setSizePolicy(sizePolicy1)
        self.label_path.setMinimumSize(QSize(0, 20))
        self.label_path.setMaximumSize(QSize(16777215, 20))
        font4 = QFont()
        font4.setPointSize(10)
        font4.setBold(False)
        font4.setItalic(True)
        self.label_path.setFont(font4)

        self.w_label_path.addWidget(self.label_path)

        self.layout_button_data = QHBoxLayout()
        self.layout_button_data.setObjectName(u"layout_button_data")
        self.button_data = QToolButton(self.w_label_path_2)
        self.button_data.setObjectName(u"button_data")
        self.button_data.setMinimumSize(QSize(16, 16))
        self.button_data.setMaximumSize(QSize(16, 16))
        self.button_data.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.button_data.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.button_data.setStyleSheet(u"QToolButton{\n"
"border-radius: 15px;\n"
"}")
        icon5 = QIcon()
        icon5.addFile(u""+ icons_path +"flaticon_PaIRS_download.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.button_data.setIcon(icon5)
        self.button_data.setIconSize(QSize(15, 15))

        self.layout_button_data.addWidget(self.button_data)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.layout_button_data.addItem(self.horizontalSpacer)


        self.w_label_path.addLayout(self.layout_button_data)


        self.verticalLayout.addWidget(self.w_label_path_2)

        self.w_edit_path = QWidget(self.w_InputFold)
        self.w_edit_path.setObjectName(u"w_edit_path")
        self.w_edit_path.setMinimumSize(QSize(0, 0))
        self.w_edit_path.setMaximumSize(QSize(16777215, 22))
        palette = QPalette()
        self.w_edit_path.setPalette(palette)
        self.horizontalLayout_8 = QHBoxLayout(self.w_edit_path)
        self.horizontalLayout_8.setSpacing(0)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.horizontalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.line_edit_path = MyQLineEdit(self.w_edit_path)
        self.line_edit_path.setObjectName(u"line_edit_path")
        self.line_edit_path.setMaximumSize(QSize(16777215, 22))
        self.line_edit_path.setFont(font)
        self.line_edit_path.setStyleSheet(u"border-top: 1px solid gray;\n"
"border-left: 1px solid gray;\n"
"border-bottom: 1px solid gray;\n"
"")

        self.horizontalLayout_8.addWidget(self.line_edit_path)

        self.label_check_path = ClickableEditLabel(self.w_edit_path)
        self.label_check_path.setObjectName(u"label_check_path")
        self.label_check_path.setMinimumSize(QSize(22, 22))
        self.label_check_path.setMaximumSize(QSize(22, 22))
        self.label_check_path.setStyleSheet(u"border-top: 1px solid gray;\n"
"border-right: 1px solid gray;\n"
"border-bottom: 1px solid gray;\n"
"padding: 2px;")
        self.label_check_path.setPixmap(QPixmap(u""+ icons_path +"greenv.png"))
        self.label_check_path.setScaledContents(True)
        self.label_check_path.setMargin(0)
        self.label_check_path.setIndent(-1)

        self.horizontalLayout_8.addWidget(self.label_check_path)


        self.verticalLayout.addWidget(self.w_edit_path)


        self.horizontalLayout.addWidget(self.w_InputFold)

        self.w_button_path = QWidget(self.w_InputFold_Button)
        self.w_button_path.setObjectName(u"w_button_path")
        self.w_button_path.setMinimumSize(QSize(0, 44))
        self.w_button_path.setMaximumSize(QSize(16777215, 44))
        self.verticalLayout_2 = QVBoxLayout(self.w_button_path)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.label_path_2 = QLabel(self.w_button_path)
        self.label_path_2.setObjectName(u"label_path_2")
        sizePolicy1.setHeightForWidth(self.label_path_2.sizePolicy().hasHeightForWidth())
        self.label_path_2.setSizePolicy(sizePolicy1)
        self.label_path_2.setMinimumSize(QSize(0, 18))
        self.label_path_2.setMaximumSize(QSize(16777215, 18))
        self.label_path_2.setFont(font4)

        self.verticalLayout_2.addWidget(self.label_path_2)

        self.button_path = QToolButton(self.w_button_path)
        self.button_path.setObjectName(u"button_path")
        self.button_path.setMinimumSize(QSize(26, 26))
        self.button_path.setMaximumSize(QSize(26, 26))
        icon6 = QIcon()
        icon6.addFile(u""+ icons_path +"browse_folder_c.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.button_path.setIcon(icon6)
        self.button_path.setIconSize(QSize(22, 22))

        self.verticalLayout_2.addWidget(self.button_path)


        self.horizontalLayout.addWidget(self.w_button_path)

        self.w_scan_path = QWidget(self.w_InputFold_Button)
        self.w_scan_path.setObjectName(u"w_scan_path")
        self.w_button_automatic_list_3 = QVBoxLayout(self.w_scan_path)
        self.w_button_automatic_list_3.setSpacing(0)
        self.w_button_automatic_list_3.setObjectName(u"w_button_automatic_list_3")
        self.w_button_automatic_list_3.setContentsMargins(0, 0, 0, 0)
        self.label_path_4 = QLabel(self.w_scan_path)
        self.label_path_4.setObjectName(u"label_path_4")
        sizePolicy1.setHeightForWidth(self.label_path_4.sizePolicy().hasHeightForWidth())
        self.label_path_4.setSizePolicy(sizePolicy1)
        self.label_path_4.setMinimumSize(QSize(0, 18))
        self.label_path_4.setMaximumSize(QSize(16777215, 18))
        self.label_path_4.setFont(font4)

        self.w_button_automatic_list_3.addWidget(self.label_path_4)

        self.button_scan_path = QToolButton(self.w_scan_path)
        self.button_scan_path.setObjectName(u"button_scan_path")
        self.button_scan_path.setMinimumSize(QSize(26, 26))
        self.button_scan_path.setMaximumSize(QSize(26, 26))
        icon7 = QIcon()
        icon7.addFile(u""+ icons_path +"scan_path.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.button_scan_path.setIcon(icon7)
        self.button_scan_path.setIconSize(QSize(22, 22))

        self.w_button_automatic_list_3.addWidget(self.button_scan_path)


        self.horizontalLayout.addWidget(self.w_scan_path)

        self.w_button_automatic_list_2 = QWidget(self.w_InputFold_Button)
        self.w_button_automatic_list_2.setObjectName(u"w_button_automatic_list_2")
        self.w_button_automatic_list = QVBoxLayout(self.w_button_automatic_list_2)
        self.w_button_automatic_list.setSpacing(0)
        self.w_button_automatic_list.setObjectName(u"w_button_automatic_list")
        self.w_button_automatic_list.setContentsMargins(0, 0, 0, 0)
        self.label_path_3 = QLabel(self.w_button_automatic_list_2)
        self.label_path_3.setObjectName(u"label_path_3")
        sizePolicy1.setHeightForWidth(self.label_path_3.sizePolicy().hasHeightForWidth())
        self.label_path_3.setSizePolicy(sizePolicy1)
        self.label_path_3.setMinimumSize(QSize(0, 18))
        self.label_path_3.setMaximumSize(QSize(16777215, 18))
        self.label_path_3.setFont(font4)

        self.w_button_automatic_list.addWidget(self.label_path_3)

        self.button_automatic_list = QToolButton(self.w_button_automatic_list_2)
        self.button_automatic_list.setObjectName(u"button_automatic_list")
        self.button_automatic_list.setMinimumSize(QSize(26, 26))
        self.button_automatic_list.setMaximumSize(QSize(26, 26))
        icon8 = QIcon()
        icon8.addFile(u""+ icons_path +"automatic_off.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        icon8.addFile(u""+ icons_path +"automatic_on.png", QSize(), QIcon.Mode.Normal, QIcon.State.On)
        self.button_automatic_list.setIcon(icon8)
        self.button_automatic_list.setIconSize(QSize(22, 22))
        self.button_automatic_list.setCheckable(True)
        self.button_automatic_list.setChecked(True)

        self.w_button_automatic_list.addWidget(self.button_automatic_list)


        self.horizontalLayout.addWidget(self.w_button_automatic_list_2)

        self.horizontalLayout.setStretch(0, 1)

        self.verticalLayout_8.addWidget(self.w_InputFold_Button)

        self.CollapBox_ImSet = CollapsibleBox(self.scrollAreaWidgetContents)
        self.CollapBox_ImSet.setObjectName(u"CollapBox_ImSet")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.CollapBox_ImSet.sizePolicy().hasHeightForWidth())
        self.CollapBox_ImSet.setSizePolicy(sizePolicy2)
        self.CollapBox_ImSet.setMinimumSize(QSize(0, 160))
        self.CollapBox_ImSet.setMaximumSize(QSize(16777215, 160))
        self.verticalLayout_24 = QVBoxLayout(self.CollapBox_ImSet)
        self.verticalLayout_24.setSpacing(0)
        self.verticalLayout_24.setObjectName(u"verticalLayout_24")
        self.verticalLayout_24.setContentsMargins(0, 0, 0, 0)
        self.lay_CollapBox_ImSet = QHBoxLayout()
        self.lay_CollapBox_ImSet.setSpacing(0)
        self.lay_CollapBox_ImSet.setObjectName(u"lay_CollapBox_ImSet")
        self.lay_CollapBox_ImSet.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.tool_CollapBox_ImSet = QToolButton(self.CollapBox_ImSet)
        self.tool_CollapBox_ImSet.setObjectName(u"tool_CollapBox_ImSet")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.tool_CollapBox_ImSet.sizePolicy().hasHeightForWidth())
        self.tool_CollapBox_ImSet.setSizePolicy(sizePolicy3)
        self.tool_CollapBox_ImSet.setMinimumSize(QSize(0, 20))
        self.tool_CollapBox_ImSet.setMaximumSize(QSize(16777215, 20))
        font5 = QFont()
        font5.setPointSize(10)
        font5.setBold(True)
        self.tool_CollapBox_ImSet.setFont(font5)
        self.tool_CollapBox_ImSet.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.tool_CollapBox_ImSet.setStyleSheet(u"QToolButton { border: none; }")
        self.tool_CollapBox_ImSet.setCheckable(True)
        self.tool_CollapBox_ImSet.setChecked(True)
        self.tool_CollapBox_ImSet.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.tool_CollapBox_ImSet.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.tool_CollapBox_ImSet.setArrowType(Qt.ArrowType.DownArrow)

        self.lay_CollapBox_ImSet.addWidget(self.tool_CollapBox_ImSet)

        self.hsp_CollapBox_ImSet = QSpacerItem(100, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.lay_CollapBox_ImSet.addItem(self.hsp_CollapBox_ImSet)

        self.button_CollapBox_ImSet = MyToolButton(self.CollapBox_ImSet)
        self.button_CollapBox_ImSet.setObjectName(u"button_CollapBox_ImSet")
        self.button_CollapBox_ImSet.setMinimumSize(QSize(18, 18))
        self.button_CollapBox_ImSet.setMaximumSize(QSize(18, 18))
        self.button_CollapBox_ImSet.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.button_CollapBox_ImSet.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.button_CollapBox_ImSet.setIcon(icon2)
        self.button_CollapBox_ImSet.setIconSize(QSize(12, 12))

        self.lay_CollapBox_ImSet.addWidget(self.button_CollapBox_ImSet)


        self.verticalLayout_24.addLayout(self.lay_CollapBox_ImSet)

        self.g_ImSet = QGroupBox(self.CollapBox_ImSet)
        self.g_ImSet.setObjectName(u"g_ImSet")
        self.g_ImSet.setMinimumSize(QSize(0, 140))
        self.g_ImSet.setMaximumSize(QSize(16777215, 140))
        self.g_ImSet.setStyleSheet(u"QGroupBox{border: 1px solid gray; border-radius: 6px;}\n"
"")
        self.g_ImSet_layout = QVBoxLayout(self.g_ImSet)
        self.g_ImSet_layout.setSpacing(5)
        self.g_ImSet_layout.setObjectName(u"g_ImSet_layout")
        self.g_ImSet_layout.setContentsMargins(10, 5, 10, 5)
        self.w_frames = QWidget(self.g_ImSet)
        self.w_frames.setObjectName(u"w_frames")
        self.w_frames.setMinimumSize(QSize(0, 44))
        self.w_frames.setMaximumSize(QSize(16777215, 44))
        self.horizontalLayout_7 = QHBoxLayout(self.w_frames)
        self.horizontalLayout_7.setSpacing(10)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalLayout_7.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.horizontalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.w_frame_combos = QWidget(self.w_frames)
        self.w_frame_combos.setObjectName(u"w_frame_combos")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.w_frame_combos.sizePolicy().hasHeightForWidth())
        self.w_frame_combos.setSizePolicy(sizePolicy4)
        self.w_frame_combos.setMinimumSize(QSize(0, 44))
        self.w_frame_combos.setMaximumSize(QSize(16777215, 44))
        self.horizontalLayout_6 = QHBoxLayout(self.w_frame_combos)
        self.horizontalLayout_6.setSpacing(10)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.w_frame_a = QWidget(self.w_frame_combos)
        self.w_frame_a.setObjectName(u"w_frame_a")
        self.w_frame_a.setMaximumSize(QSize(16777215, 16777215))
        self.lay_frame_a = QVBoxLayout(self.w_frame_a)
        self.lay_frame_a.setSpacing(0)
        self.lay_frame_a.setObjectName(u"lay_frame_a")
        self.lay_frame_a.setContentsMargins(0, 0, 0, 0)
        self.w_frame_a_label = QWidget(self.w_frame_a)
        self.w_frame_a_label.setObjectName(u"w_frame_a_label")
        self.w_automatic = QHBoxLayout(self.w_frame_a_label)
        self.w_automatic.setSpacing(0)
        self.w_automatic.setObjectName(u"w_automatic")
        self.w_automatic.setContentsMargins(0, 0, 0, 0)
        self.label_frame_a = QLabel(self.w_frame_a_label)
        self.label_frame_a.setObjectName(u"label_frame_a")
        sizePolicy1.setHeightForWidth(self.label_frame_a.sizePolicy().hasHeightForWidth())
        self.label_frame_a.setSizePolicy(sizePolicy1)
        self.label_frame_a.setMinimumSize(QSize(65, 20))
        self.label_frame_a.setMaximumSize(QSize(16777215, 20))
        self.label_frame_a.setFont(font4)
        self.label_frame_a.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.w_automatic.addWidget(self.label_frame_a)

        self.button_automatic_frame = QToolButton(self.w_frame_a_label)
        self.button_automatic_frame.setObjectName(u"button_automatic_frame")
        self.button_automatic_frame.setMinimumSize(QSize(18, 18))
        self.button_automatic_frame.setMaximumSize(QSize(18, 18))
        self.button_automatic_frame.setIcon(icon8)
        self.button_automatic_frame.setIconSize(QSize(14, 14))
        self.button_automatic_frame.setCheckable(True)
        self.button_automatic_frame.setChecked(True)

        self.w_automatic.addWidget(self.button_automatic_frame)


        self.lay_frame_a.addWidget(self.w_frame_a_label)

        self.combo_frame_a = QComboBox(self.w_frame_a)
        self.combo_frame_a.setObjectName(u"combo_frame_a")
        self.combo_frame_a.setMinimumSize(QSize(0, 24))
        self.combo_frame_a.setMaximumSize(QSize(16777215, 24))
        self.combo_frame_a.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.combo_frame_a.setMinimumContentsLength(1)

        self.lay_frame_a.addWidget(self.combo_frame_a)


        self.horizontalLayout_6.addWidget(self.w_frame_a)

        self.w_frame_b = QWidget(self.w_frame_combos)
        self.w_frame_b.setObjectName(u"w_frame_b")
        self.w_frame_b.setMaximumSize(QSize(16777215, 16777215))
        self.lay_frame_b = QVBoxLayout(self.w_frame_b)
        self.lay_frame_b.setSpacing(0)
        self.lay_frame_b.setObjectName(u"lay_frame_b")
        self.lay_frame_b.setContentsMargins(0, 0, 0, 0)
        self.label_frame_b = QLabel(self.w_frame_b)
        self.label_frame_b.setObjectName(u"label_frame_b")
        sizePolicy1.setHeightForWidth(self.label_frame_b.sizePolicy().hasHeightForWidth())
        self.label_frame_b.setSizePolicy(sizePolicy1)
        self.label_frame_b.setMinimumSize(QSize(65, 20))
        self.label_frame_b.setMaximumSize(QSize(16777215, 20))
        self.label_frame_b.setFont(font4)
        self.label_frame_b.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.lay_frame_b.addWidget(self.label_frame_b)

        self.combo_frame_b = QComboBox(self.w_frame_b)
        self.combo_frame_b.setObjectName(u"combo_frame_b")
        self.combo_frame_b.setMinimumSize(QSize(0, 24))
        self.combo_frame_b.setMaximumSize(QSize(16777215, 24))
        self.combo_frame_b.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.combo_frame_b.setMinimumContentsLength(1)

        self.lay_frame_b.addWidget(self.combo_frame_b)


        self.horizontalLayout_6.addWidget(self.w_frame_b)


        self.horizontalLayout_7.addWidget(self.w_frame_combos)

        self.hs_frames = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_7.addItem(self.hs_frames)

        self.w_inp_cameras_2 = QWidget(self.w_frames)
        self.w_inp_cameras_2.setObjectName(u"w_inp_cameras_2")
        self.w_inp_cameras = QHBoxLayout(self.w_inp_cameras_2)
        self.w_inp_cameras.setSpacing(1)
        self.w_inp_cameras.setObjectName(u"w_inp_cameras")
        self.w_inp_cameras.setContentsMargins(0, 0, 0, 0)
        self.w_inp_cam = QWidget(self.w_inp_cameras_2)
        self.w_inp_cam.setObjectName(u"w_inp_cam")
        self.w_inp_cam.setMinimumSize(QSize(0, 44))
        self.w_inp_cam.setMaximumSize(QSize(16777215, 44))
        self.verticalLayout_6 = QVBoxLayout(self.w_inp_cam)
        self.verticalLayout_6.setSpacing(0)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.label_inp_cam = QLabel(self.w_inp_cam)
        self.label_inp_cam.setObjectName(u"label_inp_cam")
        sizePolicy1.setHeightForWidth(self.label_inp_cam.sizePolicy().hasHeightForWidth())
        self.label_inp_cam.setSizePolicy(sizePolicy1)
        self.label_inp_cam.setMinimumSize(QSize(50, 20))
        self.label_inp_cam.setMaximumSize(QSize(50, 20))
        self.label_inp_cam.setFont(font4)
        self.label_inp_cam.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout_6.addWidget(self.label_inp_cam)

        self.spin_inp_cam = MyQSpin(self.w_inp_cam)
        self.spin_inp_cam.setObjectName(u"spin_inp_cam")
        self.spin_inp_cam.setEnabled(True)
        self.spin_inp_cam.setMinimumSize(QSize(50, 24))
        self.spin_inp_cam.setMaximumSize(QSize(70, 24))
        self.spin_inp_cam.setFont(font)
        self.spin_inp_cam.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.spin_inp_cam.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        self.spin_inp_cam.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
        self.spin_inp_cam.setMinimum(1)
        self.spin_inp_cam.setValue(1)

        self.verticalLayout_6.addWidget(self.spin_inp_cam)


        self.w_inp_cameras.addWidget(self.w_inp_cam)

        self.w_inp_cam_2 = QWidget(self.w_inp_cameras_2)
        self.w_inp_cam_2.setObjectName(u"w_inp_cam_2")
        self.w_inp_cam_2.setMinimumSize(QSize(14, 44))
        self.w_inp_cam_2.setMaximumSize(QSize(14, 44))
        self.verticalLayout_9 = QVBoxLayout(self.w_inp_cam_2)
        self.verticalLayout_9.setSpacing(0)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.verticalLayout_9.setContentsMargins(0, 20, 0, 0)
        self.label_inp_cam_2 = QLabel(self.w_inp_cam_2)
        self.label_inp_cam_2.setObjectName(u"label_inp_cam_2")
        sizePolicy1.setHeightForWidth(self.label_inp_cam_2.sizePolicy().hasHeightForWidth())
        self.label_inp_cam_2.setSizePolicy(sizePolicy1)
        self.label_inp_cam_2.setMinimumSize(QSize(14, 24))
        self.label_inp_cam_2.setMaximumSize(QSize(14, 24))
        font6 = QFont()
        font6.setPointSize(15)
        font6.setBold(False)
        font6.setItalic(True)
        self.label_inp_cam_2.setFont(font6)
        self.label_inp_cam_2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_inp_cam_2.setIndent(0)

        self.verticalLayout_9.addWidget(self.label_inp_cam_2)


        self.w_inp_cameras.addWidget(self.w_inp_cam_2)

        self.w_inp_ncam = QWidget(self.w_inp_cameras_2)
        self.w_inp_ncam.setObjectName(u"w_inp_ncam")
        self.w_inp_ncam.setMinimumSize(QSize(0, 44))
        self.w_inp_ncam.setMaximumSize(QSize(16777215, 44))
        self.verticalLayout_3 = QVBoxLayout(self.w_inp_ncam)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.label_ncam = QLabel(self.w_inp_ncam)
        self.label_ncam.setObjectName(u"label_ncam")
        sizePolicy1.setHeightForWidth(self.label_ncam.sizePolicy().hasHeightForWidth())
        self.label_ncam.setSizePolicy(sizePolicy1)
        self.label_ncam.setMinimumSize(QSize(50, 20))
        self.label_ncam.setMaximumSize(QSize(50, 20))
        self.label_ncam.setFont(font4)
        self.label_ncam.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout_3.addWidget(self.label_ncam)

        self.spin_inp_ncam = MyQSpin(self.w_inp_ncam)
        self.spin_inp_ncam.setObjectName(u"spin_inp_ncam")
        self.spin_inp_ncam.setEnabled(True)
        self.spin_inp_ncam.setMinimumSize(QSize(50, 24))
        self.spin_inp_ncam.setMaximumSize(QSize(70, 24))
        self.spin_inp_ncam.setFont(font)
        self.spin_inp_ncam.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.spin_inp_ncam.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        self.spin_inp_ncam.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
        self.spin_inp_ncam.setMinimum(1)
        self.spin_inp_ncam.setMaximum(99)
        self.spin_inp_ncam.setValue(1)

        self.verticalLayout_3.addWidget(self.spin_inp_ncam)


        self.w_inp_cameras.addWidget(self.w_inp_ncam)


        self.horizontalLayout_7.addWidget(self.w_inp_cameras_2)

        self.horizontalLayout_7.setStretch(0, 1)

        self.g_ImSet_layout.addWidget(self.w_frames)

        self.w_nimg = QWidget(self.g_ImSet)
        self.w_nimg.setObjectName(u"w_nimg")
        self.w_nimg.setMinimumSize(QSize(0, 44))
        self.w_nimg.setMaximumSize(QSize(16777215, 44))
        self.horizontalLayout_10 = QHBoxLayout(self.w_nimg)
        self.horizontalLayout_10.setSpacing(5)
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.horizontalLayout_10.setContentsMargins(0, 0, 0, 0)
        self.w_ind_in = QWidget(self.w_nimg)
        self.w_ind_in.setObjectName(u"w_ind_in")
        self.w_ind_in.setMinimumSize(QSize(75, 44))
        self.w_ind_in.setMaximumSize(QSize(100, 44))
        self.verticalLayout_29 = QVBoxLayout(self.w_ind_in)
        self.verticalLayout_29.setSpacing(0)
        self.verticalLayout_29.setObjectName(u"verticalLayout_29")
        self.verticalLayout_29.setContentsMargins(0, 0, 0, 0)
        self.label_ind_in = QLabel(self.w_ind_in)
        self.label_ind_in.setObjectName(u"label_ind_in")
        sizePolicy1.setHeightForWidth(self.label_ind_in.sizePolicy().hasHeightForWidth())
        self.label_ind_in.setSizePolicy(sizePolicy1)
        self.label_ind_in.setMinimumSize(QSize(65, 20))
        self.label_ind_in.setMaximumSize(QSize(16777215, 20))
        self.label_ind_in.setFont(font4)
        self.label_ind_in.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout_29.addWidget(self.label_ind_in)

        self.spin_ind_in = MyQSpin(self.w_ind_in)
        self.spin_ind_in.setObjectName(u"spin_ind_in")
        self.spin_ind_in.setEnabled(True)
        self.spin_ind_in.setMinimumSize(QSize(75, 24))
        self.spin_ind_in.setMaximumSize(QSize(100, 24))
        self.spin_ind_in.setFont(font)
        self.spin_ind_in.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.spin_ind_in.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        self.spin_ind_in.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
        self.spin_ind_in.setValue(1)

        self.verticalLayout_29.addWidget(self.spin_ind_in)


        self.horizontalLayout_10.addWidget(self.w_ind_in)

        self.w_npairs = QWidget(self.w_nimg)
        self.w_npairs.setObjectName(u"w_npairs")
        self.w_npairs.setMinimumSize(QSize(75, 44))
        self.w_npairs.setMaximumSize(QSize(100, 44))
        self.verticalLayout_30 = QVBoxLayout(self.w_npairs)
        self.verticalLayout_30.setSpacing(0)
        self.verticalLayout_30.setObjectName(u"verticalLayout_30")
        self.verticalLayout_30.setContentsMargins(0, 0, 0, 0)
        self.label_npairs = QLabel(self.w_npairs)
        self.label_npairs.setObjectName(u"label_npairs")
        sizePolicy1.setHeightForWidth(self.label_npairs.sizePolicy().hasHeightForWidth())
        self.label_npairs.setSizePolicy(sizePolicy1)
        self.label_npairs.setMinimumSize(QSize(65, 20))
        self.label_npairs.setMaximumSize(QSize(16777215, 20))
        self.label_npairs.setFont(font4)
        self.label_npairs.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout_30.addWidget(self.label_npairs)

        self.spin_npairs = MyQSpin(self.w_npairs)
        self.spin_npairs.setObjectName(u"spin_npairs")
        self.spin_npairs.setEnabled(True)
        self.spin_npairs.setMinimumSize(QSize(75, 24))
        self.spin_npairs.setMaximumSize(QSize(100, 24))
        self.spin_npairs.setFont(font)
        self.spin_npairs.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.spin_npairs.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        self.spin_npairs.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
        self.spin_npairs.setValue(1)

        self.verticalLayout_30.addWidget(self.spin_npairs)


        self.horizontalLayout_10.addWidget(self.w_npairs)

        self.w_step = QWidget(self.w_nimg)
        self.w_step.setObjectName(u"w_step")
        self.w_step.setMinimumSize(QSize(75, 44))
        self.w_step.setMaximumSize(QSize(100, 44))
        self.verticalLayout_31 = QVBoxLayout(self.w_step)
        self.verticalLayout_31.setSpacing(0)
        self.verticalLayout_31.setObjectName(u"verticalLayout_31")
        self.verticalLayout_31.setContentsMargins(0, 0, 0, 0)
        self.label_step = QLabel(self.w_step)
        self.label_step.setObjectName(u"label_step")
        sizePolicy1.setHeightForWidth(self.label_step.sizePolicy().hasHeightForWidth())
        self.label_step.setSizePolicy(sizePolicy1)
        self.label_step.setMinimumSize(QSize(65, 20))
        self.label_step.setMaximumSize(QSize(16777215, 20))
        self.label_step.setFont(font4)
        self.label_step.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout_31.addWidget(self.label_step)

        self.spin_step = MyQSpin(self.w_step)
        self.spin_step.setObjectName(u"spin_step")
        self.spin_step.setEnabled(True)
        self.spin_step.setMinimumSize(QSize(75, 24))
        self.spin_step.setMaximumSize(QSize(100, 24))
        self.spin_step.setFont(font)
        self.spin_step.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.spin_step.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        self.spin_step.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
        self.spin_step.setValue(1)

        self.verticalLayout_31.addWidget(self.spin_step)


        self.horizontalLayout_10.addWidget(self.w_step)

        self.w_TR_Import = QWidget(self.w_nimg)
        self.w_TR_Import.setObjectName(u"w_TR_Import")
        self.verticalLayout_4 = QVBoxLayout(self.w_TR_Import)
        self.verticalLayout_4.setSpacing(0)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.label_TR_Import = QLabel(self.w_TR_Import)
        self.label_TR_Import.setObjectName(u"label_TR_Import")
        sizePolicy1.setHeightForWidth(self.label_TR_Import.sizePolicy().hasHeightForWidth())
        self.label_TR_Import.setSizePolicy(sizePolicy1)
        self.label_TR_Import.setMinimumSize(QSize(65, 20))
        self.label_TR_Import.setMaximumSize(QSize(16777215, 20))
        self.label_TR_Import.setFont(font4)
        self.label_TR_Import.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout_4.addWidget(self.label_TR_Import)

        self.check_TR_Import = QCheckBox(self.w_TR_Import)
        self.check_TR_Import.setObjectName(u"check_TR_Import")
        self.check_TR_Import.setMinimumSize(QSize(0, 24))
        self.check_TR_Import.setMaximumSize(QSize(16777215, 24))
        self.check_TR_Import.setFont(font)
        self.check_TR_Import.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.check_TR_Import.setStyleSheet(u"")

        self.verticalLayout_4.addWidget(self.check_TR_Import)


        self.horizontalLayout_10.addWidget(self.w_TR_Import)

        self.hs_nimg = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_10.addItem(self.hs_nimg)

        self.button_example_list = QToolButton(self.w_nimg)
        self.button_example_list.setObjectName(u"button_example_list")
        self.button_example_list.setMinimumSize(QSize(36, 36))
        self.button_example_list.setMaximumSize(QSize(36, 36))
        icon9 = QIcon()
        icon9.addFile(u""+ icons_path +"example_list.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.button_example_list.setIcon(icon9)
        self.button_example_list.setIconSize(QSize(30, 30))
        self.button_example_list.setCheckable(True)
        self.button_example_list.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.button_example_list.setAutoRaise(False)

        self.horizontalLayout_10.addWidget(self.button_example_list)

        self.button_import = QToolButton(self.w_nimg)
        self.button_import.setObjectName(u"button_import")
        self.button_import.setMinimumSize(QSize(36, 36))
        self.button_import.setMaximumSize(QSize(36, 36))
        icon10 = QIcon()
        icon10.addFile(u""+ icons_path +"import_set.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.button_import.setIcon(icon10)
        self.button_import.setIconSize(QSize(30, 30))
        self.button_import.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.button_import.setAutoRaise(False)

        self.horizontalLayout_10.addWidget(self.button_import)


        self.g_ImSet_layout.addWidget(self.w_nimg)

        self.vs_ImSet = QSpacerItem(20, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.g_ImSet_layout.addItem(self.vs_ImSet)


        self.verticalLayout_24.addWidget(self.g_ImSet)


        self.verticalLayout_8.addWidget(self.CollapBox_ImSet)

        self.imTreeWidget = ImageTreeWidget(self.scrollAreaWidgetContents)
        self.imTreeWidget.setObjectName(u"imTreeWidget")

        self.verticalLayout_8.addWidget(self.imTreeWidget)

        self.verticalLayout_8.setStretch(2, 1)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout_7.addWidget(self.scrollArea)

        QWidget.setTabOrder(self.combo_process, self.button_back)
        QWidget.setTabOrder(self.button_back, self.button_forward)
        QWidget.setTabOrder(self.button_forward, self.button_close_tab)
        QWidget.setTabOrder(self.button_close_tab, self.button_data)
        QWidget.setTabOrder(self.button_data, self.line_edit_path)
        QWidget.setTabOrder(self.line_edit_path, self.button_path)
        QWidget.setTabOrder(self.button_path, self.button_scan_path)
        QWidget.setTabOrder(self.button_scan_path, self.button_automatic_list)
        QWidget.setTabOrder(self.button_automatic_list, self.spin_inp_cam)
        QWidget.setTabOrder(self.spin_inp_cam, self.spin_inp_ncam)
        QWidget.setTabOrder(self.spin_inp_ncam, self.spin_ind_in)
        QWidget.setTabOrder(self.spin_ind_in, self.spin_npairs)
        QWidget.setTabOrder(self.spin_npairs, self.spin_step)
        QWidget.setTabOrder(self.spin_step, self.check_TR_Import)
        QWidget.setTabOrder(self.check_TR_Import, self.button_example_list)
        QWidget.setTabOrder(self.button_example_list, self.button_import)
        QWidget.setTabOrder(self.button_import, self.scrollArea)

        self.retranslateUi(InputTab)

        QMetaObject.connectSlotsByName(InputTab)
    # setupUi

    def retranslateUi(self, InputTab):
        InputTab.setWindowTitle(QCoreApplication.translate("InputTab", u"Import", None))
#if QT_CONFIG(accessibility)
        InputTab.setAccessibleName("")
#endif // QT_CONFIG(accessibility)
        self.icon.setText("")
        self.name_tab.setText(QCoreApplication.translate("InputTab", u" Input", None))
        self.label_done.setText("")
        self.label_process.setText(QCoreApplication.translate("InputTab", u"Process", None))
        self.combo_process.setItemText(0, QCoreApplication.translate("InputTab", u"minimum", None))
        self.combo_process.setItemText(1, QCoreApplication.translate("InputTab", u"PIV", None))
        self.combo_process.setItemText(2, QCoreApplication.translate("InputTab", u"SPIV", None))
        self.combo_process.setItemText(3, QCoreApplication.translate("InputTab", u"TPIV", None))

#if QT_CONFIG(tooltip)
        self.combo_process.setToolTip(QCoreApplication.translate("InputTab", u"Select mode", None))
#endif // QT_CONFIG(tooltip)
        self.label_number.setText(QCoreApplication.translate("InputTab", u"1", None))
#if QT_CONFIG(tooltip)
        self.button_back.setToolTip(QCoreApplication.translate("InputTab", u"Undo", None))
#endif // QT_CONFIG(tooltip)
        self.button_back.setText("")
#if QT_CONFIG(tooltip)
        self.button_forward.setToolTip(QCoreApplication.translate("InputTab", u"Redo", None))
#endif // QT_CONFIG(tooltip)
        self.button_forward.setText("")
#if QT_CONFIG(tooltip)
        self.button_close_tab.setToolTip(QCoreApplication.translate("InputTab", u"Close tab", None))
#endif // QT_CONFIG(tooltip)
        self.button_close_tab.setText("")
#if QT_CONFIG(shortcut)
        self.button_close_tab.setShortcut(QCoreApplication.translate("InputTab", u"Alt+I", None))
#endif // QT_CONFIG(shortcut)
        self.label_path.setText(QCoreApplication.translate("InputTab", u"Input folder path", None))
#if QT_CONFIG(tooltip)
        self.button_data.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.button_data.setText("")
#if QT_CONFIG(tooltip)
        self.line_edit_path.setToolTip(QCoreApplication.translate("InputTab", u"Path of the directory containing the image files", None))
#endif // QT_CONFIG(tooltip)
        self.line_edit_path.setText(QCoreApplication.translate("InputTab", u".\\img\\fold3\\", None))
        self.label_check_path.setText("")
        self.label_path_2.setText("")
#if QT_CONFIG(tooltip)
        self.button_path.setToolTip(QCoreApplication.translate("InputTab", u"Explore and find the path of the directory containing the image files", None))
#endif // QT_CONFIG(tooltip)
        self.button_path.setText("")
#if QT_CONFIG(shortcut)
        self.button_path.setShortcut(QCoreApplication.translate("InputTab", u"Ctrl+Alt+I", None))
#endif // QT_CONFIG(shortcut)
        self.label_path_4.setText("")
#if QT_CONFIG(tooltip)
        self.button_scan_path.setToolTip(QCoreApplication.translate("InputTab", u"Re-scan the input folder to update the list of images", None))
#endif // QT_CONFIG(tooltip)
        self.button_scan_path.setText("")
        self.label_path_3.setText("")
#if QT_CONFIG(tooltip)
        self.button_automatic_list.setToolTip(QCoreApplication.translate("InputTab", u"If activated, the image list is generated automatically after selection of input path", None))
#endif // QT_CONFIG(tooltip)
        self.button_automatic_list.setText("")
#if QT_CONFIG(tooltip)
        self.tool_CollapBox_ImSet.setToolTip(QCoreApplication.translate("InputTab", u"Final iterations option box", None))
#endif // QT_CONFIG(tooltip)
        self.tool_CollapBox_ImSet.setText(QCoreApplication.translate("InputTab", u"Image import tool", None))
#if QT_CONFIG(tooltip)
        self.button_CollapBox_ImSet.setToolTip(QCoreApplication.translate("InputTab", u"Set default options for the selected type of process", None))
#endif // QT_CONFIG(tooltip)
        self.button_CollapBox_ImSet.setText("")
        self.label_frame_a.setText(QCoreApplication.translate("InputTab", u"frame 1", None))
#if QT_CONFIG(tooltip)
        self.button_automatic_frame.setToolTip(QCoreApplication.translate("InputTab", u"If activated, frames are assigned automatically after selection of frame 1", None))
#endif // QT_CONFIG(tooltip)
        self.button_automatic_frame.setText("")
#if QT_CONFIG(tooltip)
        self.combo_frame_a.setToolTip(QCoreApplication.translate("InputTab", u"Pattern of image filename for frame 1", None))
#endif // QT_CONFIG(tooltip)
        self.label_frame_b.setText(QCoreApplication.translate("InputTab", u"frame 2", None))
#if QT_CONFIG(tooltip)
        self.combo_frame_b.setToolTip(QCoreApplication.translate("InputTab", u"Pattern of image filename for frame 2", None))
#endif // QT_CONFIG(tooltip)
        self.label_inp_cam.setText(QCoreApplication.translate("InputTab", u"cam ", None))
#if QT_CONFIG(tooltip)
        self.spin_inp_cam.setToolTip(QCoreApplication.translate("InputTab", u"Current camera", None))
#endif // QT_CONFIG(tooltip)
        self.label_inp_cam_2.setText(QCoreApplication.translate("InputTab", u"/", None))
        self.label_ncam.setText(QCoreApplication.translate("InputTab", u"# cam", None))
#if QT_CONFIG(tooltip)
        self.spin_inp_ncam.setToolTip(QCoreApplication.translate("InputTab", u"Number of cameras", None))
#endif // QT_CONFIG(tooltip)
        self.label_ind_in.setText(QCoreApplication.translate("InputTab", u"from", None))
#if QT_CONFIG(tooltip)
        self.spin_ind_in.setToolTip(QCoreApplication.translate("InputTab", u"Number of the first image in the sequence to process", None))
#endif // QT_CONFIG(tooltip)
        self.label_npairs.setText(QCoreApplication.translate("InputTab", u"# pairs", None))
#if QT_CONFIG(tooltip)
        self.spin_npairs.setToolTip(QCoreApplication.translate("InputTab", u"Number of image pairs to process", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.label_step.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.label_step.setText(QCoreApplication.translate("InputTab", u"step", None))
#if QT_CONFIG(tooltip)
        self.spin_step.setToolTip(QCoreApplication.translate("InputTab", u"Step through the number of images in the sequence.", None))
#endif // QT_CONFIG(tooltip)
        self.label_TR_Import.setText("")
#if QT_CONFIG(tooltip)
        self.check_TR_Import.setToolTip(QCoreApplication.translate("InputTab", u"If activated, the images are listed in time-resolved mode", None))
#endif // QT_CONFIG(tooltip)
        self.check_TR_Import.setText(QCoreApplication.translate("InputTab", u"Time-res.", None))
#if QT_CONFIG(tooltip)
        self.button_example_list.setToolTip(QCoreApplication.translate("InputTab", u"Show example list of images", None))
#endif // QT_CONFIG(tooltip)
        self.button_example_list.setText("")
#if QT_CONFIG(tooltip)
        self.button_import.setToolTip(QCoreApplication.translate("InputTab", u"Import the current set of images", None))
#endif // QT_CONFIG(tooltip)
        self.button_import.setText("")
#if QT_CONFIG(shortcut)
        self.button_import.setShortcut(QCoreApplication.translate("InputTab", u"Ctrl+Alt+J", None))
#endif // QT_CONFIG(shortcut)
    # retranslateUi


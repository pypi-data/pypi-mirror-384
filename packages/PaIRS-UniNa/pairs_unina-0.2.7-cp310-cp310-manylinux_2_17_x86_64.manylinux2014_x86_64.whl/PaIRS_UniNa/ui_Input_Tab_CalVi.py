from .addwidgets_ps import icons_path
# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Input_Tab_CalVimbnaVV.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QAbstractSpinBox, QApplication, QFrame,
    QHBoxLayout, QHeaderView, QLabel, QRadioButton,
    QScrollArea, QSizePolicy, QSpacerItem, QTableWidgetItem,
    QToolButton, QVBoxLayout, QWidget)

from .Input_Tab_tools import ImageTable
from .addwidgets_ps import (ClickableEditLabel, MyQLineEdit, MyQLineEditNumber, MyQSpin,
    MyQSpinXW, MyTabLabel)

class Ui_InputTab_CalVi(object):
    def setupUi(self, InputTab_CalVi):
        if not InputTab_CalVi.objectName():
            InputTab_CalVi.setObjectName(u"InputTab_CalVi")
        InputTab_CalVi.resize(500, 680)
        InputTab_CalVi.setMinimumSize(QSize(500, 680))
        InputTab_CalVi.setMaximumSize(QSize(1000, 16777215))
        font = QFont()
        font.setPointSize(11)
        InputTab_CalVi.setFont(font)
        icon1 = QIcon()
        icon1.addFile(u""+ icons_path +"input_logo.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        InputTab_CalVi.setWindowIcon(icon1)
        self.verticalLayout_7 = QVBoxLayout(InputTab_CalVi)
        self.verticalLayout_7.setSpacing(5)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.verticalLayout_7.setContentsMargins(10, 10, 10, 10)
        self.w_Mode = QWidget(InputTab_CalVi)
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

        self.hs1 = QSpacerItem(70, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.hs1)

        self.bfLayout = QHBoxLayout()
        self.bfLayout.setSpacing(3)
        self.bfLayout.setObjectName(u"bfLayout")
        self.label_number = QLabel(self.w_Mode)
        self.label_number.setObjectName(u"label_number")
        self.label_number.setMinimumSize(QSize(35, 0))
        font2 = QFont()
        font2.setPointSize(9)
        self.label_number.setFont(font2)
        self.label_number.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.bfLayout.addWidget(self.label_number)

        self.hs_bf = QSpacerItem(2, 27, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.bfLayout.addItem(self.hs_bf)

        self.button_back = QToolButton(self.w_Mode)
        self.button_back.setObjectName(u"button_back")
        self.button_back.setMinimumSize(QSize(24, 24))
        self.button_back.setMaximumSize(QSize(24, 24))
        icon2 = QIcon()
        icon2.addFile(u""+ icons_path +"undo.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.button_back.setIcon(icon2)
        self.button_back.setIconSize(QSize(20, 20))

        self.bfLayout.addWidget(self.button_back)

        self.button_forward = QToolButton(self.w_Mode)
        self.button_forward.setObjectName(u"button_forward")
        self.button_forward.setMinimumSize(QSize(24, 24))
        self.button_forward.setMaximumSize(QSize(24, 24))
        icon3 = QIcon()
        icon3.addFile(u""+ icons_path +"redo.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.button_forward.setIcon(icon3)
        self.button_forward.setIconSize(QSize(20, 20))

        self.bfLayout.addWidget(self.button_forward)


        self.horizontalLayout_5.addLayout(self.bfLayout)

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

        self.line = QFrame(InputTab_CalVi)
        self.line.setObjectName(u"line")
        self.line.setMinimumSize(QSize(0, 5))
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_7.addWidget(self.line)

        self.scrollArea = QScrollArea(InputTab_CalVi)
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
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 480, 491))
        self.scrollAreaWidgetContents.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.verticalLayout_8 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_8.setSpacing(10)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.verticalLayout_8.setContentsMargins(0, 0, 10, 0)
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
        font3 = QFont()
        font3.setPointSize(10)
        font3.setBold(False)
        font3.setItalic(True)
        self.label_path.setFont(font3)

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

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.layout_button_data.addItem(self.horizontalSpacer_2)


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
        self.label_path_2.setFont(font3)

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


        self.verticalLayout_8.addWidget(self.w_InputFold_Button)

        self.w_InputImg_Button = QWidget(self.scrollAreaWidgetContents)
        self.w_InputImg_Button.setObjectName(u"w_InputImg_Button")
        self.w_InputImg_Button.setMinimumSize(QSize(400, 0))
        self.w_InputImg_Button.setMaximumSize(QSize(16777215, 44))
        self.horizontalLayout_2 = QHBoxLayout(self.w_InputImg_Button)
        self.horizontalLayout_2.setSpacing(3)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.radio_Cam = QRadioButton(self.w_InputImg_Button)
        self.radio_Cam.setObjectName(u"radio_Cam")
        self.radio_Cam.setFont(font)

        self.horizontalLayout_2.addWidget(self.radio_Cam)

        self.w_InputImg = QWidget(self.w_InputImg_Button)
        self.w_InputImg.setObjectName(u"w_InputImg")
        self.w_InputImg.setMinimumSize(QSize(130, 0))
        self.w_InputImg.setMaximumSize(QSize(16777215, 42))
        self.verticalLayout_3 = QVBoxLayout(self.w_InputImg)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.label_edit_cams = QLabel(self.w_InputImg)
        self.label_edit_cams.setObjectName(u"label_edit_cams")
        sizePolicy1.setHeightForWidth(self.label_edit_cams.sizePolicy().hasHeightForWidth())
        self.label_edit_cams.setSizePolicy(sizePolicy1)
        self.label_edit_cams.setMinimumSize(QSize(0, 20))
        self.label_edit_cams.setMaximumSize(QSize(16777215, 20))
        palette1 = QPalette()
        brush = QBrush(QColor(0, 0, 0, 255))
        brush.setStyle(Qt.SolidPattern)
        palette1.setBrush(QPalette.Active, QPalette.Window, brush)
        palette1.setBrush(QPalette.Active, QPalette.ToolTipBase, brush)
        brush1 = QBrush(QColor(50, 50, 50, 255))
        brush1.setStyle(Qt.SolidPattern)
        palette1.setBrush(QPalette.Inactive, QPalette.Window, brush1)
        brush2 = QBrush(QColor(255, 255, 255, 63))
        brush2.setStyle(Qt.SolidPattern)
        palette1.setBrush(QPalette.Inactive, QPalette.ToolTipBase, brush2)
        palette1.setBrush(QPalette.Disabled, QPalette.Window, brush)
        palette1.setBrush(QPalette.Disabled, QPalette.ToolTipBase, brush2)
        self.label_edit_cams.setPalette(palette1)
        self.label_edit_cams.setFont(font3)

        self.verticalLayout_3.addWidget(self.label_edit_cams)

        self.w_edit_cams = QWidget(self.w_InputImg)
        self.w_edit_cams.setObjectName(u"w_edit_cams")
        self.w_edit_cams.setMinimumSize(QSize(0, 0))
        self.w_edit_cams.setMaximumSize(QSize(16777215, 22))
        self.horizontalLayout_9 = QHBoxLayout(self.w_edit_cams)
        self.horizontalLayout_9.setSpacing(0)
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.horizontalLayout_9.setContentsMargins(0, 0, 0, 0)
        self.line_edit_cameras = MyQLineEditNumber(self.w_edit_cams)
        self.line_edit_cameras.setObjectName(u"line_edit_cameras")
        self.line_edit_cameras.setMaximumSize(QSize(16777215, 22))
        self.line_edit_cameras.setFont(font)
        self.line_edit_cameras.setStyleSheet(u"border-top: 1px solid gray;\n"
"border-left: 1px solid gray;\n"
"border-bottom: 1px solid gray;\n"
"border-right: 1px solid gray;\n"
"\n"
"")

        self.horizontalLayout_9.addWidget(self.line_edit_cameras)


        self.verticalLayout_3.addWidget(self.w_edit_cams)


        self.horizontalLayout_2.addWidget(self.w_InputImg)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.w_button_import = QWidget(self.w_InputImg_Button)
        self.w_button_import.setObjectName(u"w_button_import")
        self.w_button_import.setMinimumSize(QSize(0, 44))
        self.w_button_import.setMaximumSize(QSize(16777215, 44))
        self.verticalLayout_4 = QVBoxLayout(self.w_button_import)
        self.verticalLayout_4.setSpacing(0)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.label_root_2 = QLabel(self.w_button_import)
        self.label_root_2.setObjectName(u"label_root_2")
        sizePolicy1.setHeightForWidth(self.label_root_2.sizePolicy().hasHeightForWidth())
        self.label_root_2.setSizePolicy(sizePolicy1)
        self.label_root_2.setMinimumSize(QSize(0, 18))
        self.label_root_2.setMaximumSize(QSize(16777215, 18))
        self.label_root_2.setFont(font3)

        self.verticalLayout_4.addWidget(self.label_root_2)

        self.button_import = QToolButton(self.w_button_import)
        self.button_import.setObjectName(u"button_import")
        self.button_import.setMinimumSize(QSize(26, 26))
        self.button_import.setMaximumSize(QSize(26, 26))
        icon7 = QIcon()
        icon7.addFile(u""+ icons_path +"browse_file_c.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.button_import.setIcon(icon7)
        self.button_import.setIconSize(QSize(20, 20))

        self.verticalLayout_4.addWidget(self.button_import)


        self.horizontalLayout_2.addWidget(self.w_button_import)

        self.w_button_import_plane = QWidget(self.w_InputImg_Button)
        self.w_button_import_plane.setObjectName(u"w_button_import_plane")
        self.w_button_import_plane.setMinimumSize(QSize(0, 44))
        self.w_button_import_plane.setMaximumSize(QSize(16777215, 44))
        self.verticalLayout_17 = QVBoxLayout(self.w_button_import_plane)
        self.verticalLayout_17.setSpacing(0)
        self.verticalLayout_17.setObjectName(u"verticalLayout_17")
        self.verticalLayout_17.setContentsMargins(0, 0, 0, 0)
        self.label_import_plane = QLabel(self.w_button_import_plane)
        self.label_import_plane.setObjectName(u"label_import_plane")
        sizePolicy1.setHeightForWidth(self.label_import_plane.sizePolicy().hasHeightForWidth())
        self.label_import_plane.setSizePolicy(sizePolicy1)
        self.label_import_plane.setMinimumSize(QSize(0, 18))
        self.label_import_plane.setMaximumSize(QSize(16777215, 18))
        self.label_import_plane.setFont(font3)

        self.verticalLayout_17.addWidget(self.label_import_plane)

        self.button_import_plane = QToolButton(self.w_button_import_plane)
        self.button_import_plane.setObjectName(u"button_import_plane")
        self.button_import_plane.setMinimumSize(QSize(26, 26))
        self.button_import_plane.setMaximumSize(QSize(26, 26))
        icon8 = QIcon()
        icon8.addFile(u""+ icons_path +"plane.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.button_import_plane.setIcon(icon8)
        self.button_import_plane.setIconSize(QSize(20, 20))

        self.verticalLayout_17.addWidget(self.button_import_plane)


        self.horizontalLayout_2.addWidget(self.w_button_import_plane)

        self.w_button_down = QWidget(self.w_InputImg_Button)
        self.w_button_down.setObjectName(u"w_button_down")
        self.w_button_down.setMinimumSize(QSize(0, 44))
        self.w_button_down.setMaximumSize(QSize(16777215, 44))
        self.verticalLayout_11 = QVBoxLayout(self.w_button_down)
        self.verticalLayout_11.setSpacing(0)
        self.verticalLayout_11.setObjectName(u"verticalLayout_11")
        self.verticalLayout_11.setContentsMargins(0, 0, 0, 0)
        self.label_down = QLabel(self.w_button_down)
        self.label_down.setObjectName(u"label_down")
        sizePolicy1.setHeightForWidth(self.label_down.sizePolicy().hasHeightForWidth())
        self.label_down.setSizePolicy(sizePolicy1)
        self.label_down.setMinimumSize(QSize(0, 18))
        self.label_down.setMaximumSize(QSize(16777215, 18))
        self.label_down.setFont(font3)

        self.verticalLayout_11.addWidget(self.label_down)

        self.button_down = QToolButton(self.w_button_down)
        self.button_down.setObjectName(u"button_down")
        self.button_down.setMinimumSize(QSize(25, 25))
        self.button_down.setMaximumSize(QSize(25, 25))
        icon9 = QIcon()
        icon9.addFile(u""+ icons_path +"down.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.button_down.setIcon(icon9)
        self.button_down.setIconSize(QSize(18, 18))
        self.button_down.setArrowType(Qt.ArrowType.NoArrow)

        self.verticalLayout_11.addWidget(self.button_down)


        self.horizontalLayout_2.addWidget(self.w_button_down)

        self.w_button_up = QWidget(self.w_InputImg_Button)
        self.w_button_up.setObjectName(u"w_button_up")
        self.w_button_up.setMinimumSize(QSize(0, 44))
        self.w_button_up.setMaximumSize(QSize(16777215, 44))
        self.verticalLayout_13 = QVBoxLayout(self.w_button_up)
        self.verticalLayout_13.setSpacing(0)
        self.verticalLayout_13.setObjectName(u"verticalLayout_13")
        self.verticalLayout_13.setContentsMargins(0, 0, 0, 0)
        self.label_up = QLabel(self.w_button_up)
        self.label_up.setObjectName(u"label_up")
        sizePolicy1.setHeightForWidth(self.label_up.sizePolicy().hasHeightForWidth())
        self.label_up.setSizePolicy(sizePolicy1)
        self.label_up.setMinimumSize(QSize(0, 18))
        self.label_up.setMaximumSize(QSize(16777215, 18))
        self.label_up.setFont(font3)

        self.verticalLayout_13.addWidget(self.label_up)

        self.button_up = QToolButton(self.w_button_up)
        self.button_up.setObjectName(u"button_up")
        self.button_up.setMinimumSize(QSize(25, 25))
        self.button_up.setMaximumSize(QSize(25, 25))
        icon10 = QIcon()
        icon10.addFile(u""+ icons_path +"up.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.button_up.setIcon(icon10)
        self.button_up.setIconSize(QSize(18, 18))
        self.button_up.setArrowType(Qt.ArrowType.NoArrow)

        self.verticalLayout_13.addWidget(self.button_up)


        self.horizontalLayout_2.addWidget(self.w_button_up)

        self.w_button_delete = QWidget(self.w_InputImg_Button)
        self.w_button_delete.setObjectName(u"w_button_delete")
        self.w_button_delete.setMinimumSize(QSize(0, 44))
        self.w_button_delete.setMaximumSize(QSize(16777215, 44))
        self.verticalLayout_9 = QVBoxLayout(self.w_button_delete)
        self.verticalLayout_9.setSpacing(0)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.verticalLayout_9.setContentsMargins(0, 0, 0, 0)
        self.label_root_3 = QLabel(self.w_button_delete)
        self.label_root_3.setObjectName(u"label_root_3")
        sizePolicy1.setHeightForWidth(self.label_root_3.sizePolicy().hasHeightForWidth())
        self.label_root_3.setSizePolicy(sizePolicy1)
        self.label_root_3.setMinimumSize(QSize(0, 18))
        self.label_root_3.setMaximumSize(QSize(16777215, 18))
        self.label_root_3.setFont(font3)

        self.verticalLayout_9.addWidget(self.label_root_3)

        self.button_delete = QToolButton(self.w_button_delete)
        self.button_delete.setObjectName(u"button_delete")
        self.button_delete.setMinimumSize(QSize(26, 26))
        self.button_delete.setMaximumSize(QSize(26, 26))
        icon11 = QIcon()
        icon11.addFile(u""+ icons_path +"delete.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.button_delete.setIcon(icon11)
        self.button_delete.setIconSize(QSize(20, 20))

        self.verticalLayout_9.addWidget(self.button_delete)


        self.horizontalLayout_2.addWidget(self.w_button_delete)

        self.w_button_clean = QWidget(self.w_InputImg_Button)
        self.w_button_clean.setObjectName(u"w_button_clean")
        self.w_button_clean.setMinimumSize(QSize(0, 44))
        self.w_button_clean.setMaximumSize(QSize(16777215, 44))
        self.verticalLayout_10 = QVBoxLayout(self.w_button_clean)
        self.verticalLayout_10.setSpacing(0)
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.verticalLayout_10.setContentsMargins(0, 0, 0, 0)
        self.label_root_4 = QLabel(self.w_button_clean)
        self.label_root_4.setObjectName(u"label_root_4")
        sizePolicy1.setHeightForWidth(self.label_root_4.sizePolicy().hasHeightForWidth())
        self.label_root_4.setSizePolicy(sizePolicy1)
        self.label_root_4.setMinimumSize(QSize(0, 18))
        self.label_root_4.setMaximumSize(QSize(16777215, 18))
        self.label_root_4.setFont(font3)

        self.verticalLayout_10.addWidget(self.label_root_4)

        self.button_clean = QToolButton(self.w_button_clean)
        self.button_clean.setObjectName(u"button_clean")
        self.button_clean.setMinimumSize(QSize(26, 26))
        self.button_clean.setMaximumSize(QSize(26, 26))
        icon12 = QIcon()
        icon12.addFile(u""+ icons_path +"clean.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.button_clean.setIcon(icon12)
        self.button_clean.setIconSize(QSize(20, 20))

        self.verticalLayout_10.addWidget(self.button_clean)


        self.horizontalLayout_2.addWidget(self.w_button_clean)


        self.verticalLayout_8.addWidget(self.w_InputImg_Button)

        self.w_SelectImages = QWidget(self.scrollAreaWidgetContents)
        self.w_SelectImages.setObjectName(u"w_SelectImages")
        self.verticalLayout_12 = QVBoxLayout(self.w_SelectImages)
        self.verticalLayout_12.setSpacing(0)
        self.verticalLayout_12.setObjectName(u"verticalLayout_12")
        self.verticalLayout_12.setContentsMargins(0, 0, 0, 0)
        self.list_images = ImageTable(self.w_SelectImages)
        if (self.list_images.columnCount() < 3):
            self.list_images.setColumnCount(3)
        __qtablewidgetitem = QTableWidgetItem()
        self.list_images.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.list_images.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.list_images.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        if (self.list_images.rowCount() < 2):
            self.list_images.setRowCount(2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.list_images.setVerticalHeaderItem(0, __qtablewidgetitem3)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.list_images.setVerticalHeaderItem(1, __qtablewidgetitem4)
        self.list_images.setObjectName(u"list_images")
        self.list_images.setMinimumSize(QSize(0, 0))
        self.list_images.setFont(font)
        self.list_images.setDragDropOverwriteMode(False)
        self.list_images.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.list_images.setAlternatingRowColors(True)
        self.list_images.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list_images.horizontalHeader().setCascadingSectionResizes(True)
        self.list_images.horizontalHeader().setDefaultSectionSize(200)
        self.list_images.horizontalHeader().setProperty("showSortIndicator", False)
        self.list_images.verticalHeader().setCascadingSectionResizes(True)
        self.list_images.verticalHeader().setStretchLastSection(False)

        self.verticalLayout_12.addWidget(self.list_images)

        self.label_info = QLabel(self.w_SelectImages)
        self.label_info.setObjectName(u"label_info")
        sizePolicy1.setHeightForWidth(self.label_info.sizePolicy().hasHeightForWidth())
        self.label_info.setSizePolicy(sizePolicy1)
        self.label_info.setMinimumSize(QSize(0, 20))
        self.label_info.setMaximumSize(QSize(16777215, 60))
        font4 = QFont()
        font4.setPointSize(10)
        font4.setBold(False)
        font4.setItalic(False)
        self.label_info.setFont(font4)
        self.label_info.setTextFormat(Qt.TextFormat.RichText)
        self.label_info.setWordWrap(True)

        self.verticalLayout_12.addWidget(self.label_info)


        self.verticalLayout_8.addWidget(self.w_SelectImages)

        self.w_SizeImg = QWidget(self.scrollAreaWidgetContents)
        self.w_SizeImg.setObjectName(u"w_SizeImg")
        self.w_SizeImg.setMaximumSize(QSize(16777215, 16777215))
        self.horizontalLayout_7 = QHBoxLayout(self.w_SizeImg)
        self.horizontalLayout_7.setSpacing(5)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.w_x = QWidget(self.w_SizeImg)
        self.w_x.setObjectName(u"w_x")
        self.w_x.setMinimumSize(QSize(100, 44))
        self.w_x.setMaximumSize(QSize(150, 44))
        self.verticalLayout_19 = QVBoxLayout(self.w_x)
        self.verticalLayout_19.setSpacing(0)
        self.verticalLayout_19.setObjectName(u"verticalLayout_19")
        self.verticalLayout_19.setContentsMargins(0, 0, 0, 0)
        self.label_x = QLabel(self.w_x)
        self.label_x.setObjectName(u"label_x")
        sizePolicy1.setHeightForWidth(self.label_x.sizePolicy().hasHeightForWidth())
        self.label_x.setSizePolicy(sizePolicy1)
        self.label_x.setMinimumSize(QSize(90, 20))
        self.label_x.setMaximumSize(QSize(90, 20))
        self.label_x.setFont(font3)
        self.label_x.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout_19.addWidget(self.label_x)

        self.spin_x = MyQSpinXW(self.w_x)
        self.spin_x.setObjectName(u"spin_x")
        self.spin_x.setEnabled(True)
        self.spin_x.setMinimumSize(QSize(90, 24))
        self.spin_x.setMaximumSize(QSize(90, 24))
        self.spin_x.setFont(font)
        self.spin_x.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.spin_x.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        self.spin_x.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
        self.spin_x.setValue(1)

        self.verticalLayout_19.addWidget(self.spin_x)


        self.horizontalLayout_7.addWidget(self.w_x)

        self.w_y = QWidget(self.w_SizeImg)
        self.w_y.setObjectName(u"w_y")
        self.w_y.setMinimumSize(QSize(100, 44))
        self.w_y.setMaximumSize(QSize(150, 44))
        self.verticalLayout_20 = QVBoxLayout(self.w_y)
        self.verticalLayout_20.setSpacing(0)
        self.verticalLayout_20.setObjectName(u"verticalLayout_20")
        self.verticalLayout_20.setContentsMargins(0, 0, 0, 0)
        self.label_y = QLabel(self.w_y)
        self.label_y.setObjectName(u"label_y")
        sizePolicy1.setHeightForWidth(self.label_y.sizePolicy().hasHeightForWidth())
        self.label_y.setSizePolicy(sizePolicy1)
        self.label_y.setMinimumSize(QSize(90, 20))
        self.label_y.setMaximumSize(QSize(90, 20))
        self.label_y.setFont(font3)
        self.label_y.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout_20.addWidget(self.label_y)

        self.spin_y = MyQSpinXW(self.w_y)
        self.spin_y.setObjectName(u"spin_y")
        self.spin_y.setEnabled(True)
        self.spin_y.setMinimumSize(QSize(90, 24))
        self.spin_y.setMaximumSize(QSize(90, 24))
        self.spin_y.setFont(font)
        self.spin_y.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.spin_y.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        self.spin_y.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
        self.spin_y.setValue(1)

        self.verticalLayout_20.addWidget(self.spin_y)


        self.horizontalLayout_7.addWidget(self.w_y)

        self.w_width = QWidget(self.w_SizeImg)
        self.w_width.setObjectName(u"w_width")
        self.w_width.setMinimumSize(QSize(100, 44))
        self.w_width.setMaximumSize(QSize(150, 44))
        self.verticalLayout_21 = QVBoxLayout(self.w_width)
        self.verticalLayout_21.setSpacing(0)
        self.verticalLayout_21.setObjectName(u"verticalLayout_21")
        self.verticalLayout_21.setContentsMargins(0, 0, 0, 0)
        self.label_w = QLabel(self.w_width)
        self.label_w.setObjectName(u"label_w")
        sizePolicy1.setHeightForWidth(self.label_w.sizePolicy().hasHeightForWidth())
        self.label_w.setSizePolicy(sizePolicy1)
        self.label_w.setMinimumSize(QSize(90, 20))
        self.label_w.setMaximumSize(QSize(90, 20))
        self.label_w.setFont(font3)
        self.label_w.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout_21.addWidget(self.label_w)

        self.spin_w = MyQSpin(self.w_width)
        self.spin_w.setObjectName(u"spin_w")
        self.spin_w.setEnabled(True)
        self.spin_w.setMinimumSize(QSize(90, 24))
        self.spin_w.setMaximumSize(QSize(90, 24))
        self.spin_w.setFont(font)
        self.spin_w.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.spin_w.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        self.spin_w.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
        self.spin_w.setValue(1)

        self.verticalLayout_21.addWidget(self.spin_w)


        self.horizontalLayout_7.addWidget(self.w_width)

        self.w_height = QWidget(self.w_SizeImg)
        self.w_height.setObjectName(u"w_height")
        self.w_height.setMinimumSize(QSize(100, 44))
        self.w_height.setMaximumSize(QSize(150, 44))
        self.verticalLayout_22 = QVBoxLayout(self.w_height)
        self.verticalLayout_22.setSpacing(0)
        self.verticalLayout_22.setObjectName(u"verticalLayout_22")
        self.verticalLayout_22.setContentsMargins(0, 0, 0, 0)
        self.label_h = QLabel(self.w_height)
        self.label_h.setObjectName(u"label_h")
        sizePolicy1.setHeightForWidth(self.label_h.sizePolicy().hasHeightForWidth())
        self.label_h.setSizePolicy(sizePolicy1)
        self.label_h.setMinimumSize(QSize(90, 20))
        self.label_h.setMaximumSize(QSize(90, 20))
        self.label_h.setFont(font3)
        self.label_h.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout_22.addWidget(self.label_h)

        self.spin_h = MyQSpin(self.w_height)
        self.spin_h.setObjectName(u"spin_h")
        self.spin_h.setEnabled(True)
        self.spin_h.setMinimumSize(QSize(90, 24))
        self.spin_h.setMaximumSize(QSize(90, 24))
        self.spin_h.setFont(font)
        self.spin_h.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.spin_h.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        self.spin_h.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
        self.spin_h.setValue(1)

        self.verticalLayout_22.addWidget(self.spin_h)


        self.horizontalLayout_7.addWidget(self.w_height)

        self.w_button_resize = QWidget(self.w_SizeImg)
        self.w_button_resize.setObjectName(u"w_button_resize")
        self.w_button_resize.setMinimumSize(QSize(0, 44))
        self.w_button_resize.setMaximumSize(QSize(26, 44))
        self.verticalLayout_6 = QVBoxLayout(self.w_button_resize)
        self.verticalLayout_6.setSpacing(0)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.label_button_resize = QLabel(self.w_button_resize)
        self.label_button_resize.setObjectName(u"label_button_resize")
        sizePolicy1.setHeightForWidth(self.label_button_resize.sizePolicy().hasHeightForWidth())
        self.label_button_resize.setSizePolicy(sizePolicy1)
        self.label_button_resize.setMinimumSize(QSize(0, 18))
        self.label_button_resize.setMaximumSize(QSize(16777215, 18))
        self.label_button_resize.setFont(font3)

        self.verticalLayout_6.addWidget(self.label_button_resize)

        self.button_resize = QToolButton(self.w_button_resize)
        self.button_resize.setObjectName(u"button_resize")
        self.button_resize.setMinimumSize(QSize(26, 26))
        self.button_resize.setMaximumSize(QSize(26, 26))
        icon13 = QIcon()
        icon13.addFile(u""+ icons_path +"resize_icon.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.button_resize.setIcon(icon13)
        self.button_resize.setIconSize(QSize(18, 18))

        self.verticalLayout_6.addWidget(self.button_resize)


        self.horizontalLayout_7.addWidget(self.w_button_resize)


        self.verticalLayout_8.addWidget(self.w_SizeImg)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout_7.addWidget(self.scrollArea)

        self.w_Mode_Output = QWidget(InputTab_CalVi)
        self.w_Mode_Output.setObjectName(u"w_Mode_Output")
        self.w_Mode_Output.setMinimumSize(QSize(0, 50))
        self.w_Mode_Output.setMaximumSize(QSize(16777215, 50))
        self.w_Mode_Output.setFont(font)
        self.horizontalLayout_10 = QHBoxLayout(self.w_Mode_Output)
        self.horizontalLayout_10.setSpacing(3)
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.horizontalLayout_10.setContentsMargins(0, 10, 0, 10)
        self.icon_Output = QLabel(self.w_Mode_Output)
        self.icon_Output.setObjectName(u"icon_Output")
        self.icon_Output.setMinimumSize(QSize(35, 35))
        self.icon_Output.setMaximumSize(QSize(35, 35))
        self.icon_Output.setPixmap(QPixmap(u""+ icons_path +"output_logo.png"))
        self.icon_Output.setScaledContents(True)

        self.horizontalLayout_10.addWidget(self.icon_Output)

        self.name_tab_Output = MyTabLabel(self.w_Mode_Output)
        self.name_tab_Output.setObjectName(u"name_tab_Output")
        self.name_tab_Output.setMinimumSize(QSize(200, 35))
        self.name_tab_Output.setMaximumSize(QSize(16777215, 35))
        self.name_tab_Output.setFont(font1)

        self.horizontalLayout_10.addWidget(self.name_tab_Output)

        self.hs2 = QSpacerItem(70, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_10.addItem(self.hs2)


        self.verticalLayout_7.addWidget(self.w_Mode_Output)

        self.line_2 = QFrame(InputTab_CalVi)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setMinimumSize(QSize(0, 5))
        self.line_2.setFrameShape(QFrame.Shape.HLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_7.addWidget(self.line_2)

        self.w_OutputFold_Button = QWidget(InputTab_CalVi)
        self.w_OutputFold_Button.setObjectName(u"w_OutputFold_Button")
        self.w_OutputFold_Button.setMinimumSize(QSize(0, 44))
        self.w_OutputFold_Button.setMaximumSize(QSize(16777215, 60))
        self.horizontalLayout_6 = QHBoxLayout(self.w_OutputFold_Button)
        self.horizontalLayout_6.setSpacing(10)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.radio_Same_as_input = QRadioButton(self.w_OutputFold_Button)
        self.radio_Same_as_input.setObjectName(u"radio_Same_as_input")
        self.radio_Same_as_input.setMinimumSize(QSize(120, 0))
        self.radio_Same_as_input.setMaximumSize(QSize(16777215, 16777215))
        self.radio_Same_as_input.setFont(font)
        self.radio_Same_as_input.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.radio_Same_as_input.setIconSize(QSize(22, 22))

        self.horizontalLayout_6.addWidget(self.radio_Same_as_input)

        self.w_OutputFolder = QWidget(self.w_OutputFold_Button)
        self.w_OutputFolder.setObjectName(u"w_OutputFolder")
        self.w_OutputFolder.setMinimumSize(QSize(0, 44))
        self.w_OutputFolder.setMaximumSize(QSize(16777215, 44))
        self.w_OutputFolder.setSizeIncrement(QSize(0, 0))
        self.verticalLayout_14 = QVBoxLayout(self.w_OutputFolder)
        self.verticalLayout_14.setSpacing(0)
        self.verticalLayout_14.setObjectName(u"verticalLayout_14")
        self.verticalLayout_14.setContentsMargins(0, 0, 0, 0)
        self.label_path_outfold = QLabel(self.w_OutputFolder)
        self.label_path_outfold.setObjectName(u"label_path_outfold")
        sizePolicy1.setHeightForWidth(self.label_path_outfold.sizePolicy().hasHeightForWidth())
        self.label_path_outfold.setSizePolicy(sizePolicy1)
        self.label_path_outfold.setMinimumSize(QSize(0, 20))
        self.label_path_outfold.setMaximumSize(QSize(16777215, 20))
        self.label_path_outfold.setFont(font3)

        self.verticalLayout_14.addWidget(self.label_path_outfold)

        self.w_edit_path_out = QWidget(self.w_OutputFolder)
        self.w_edit_path_out.setObjectName(u"w_edit_path_out")
        self.w_edit_path_out.setMinimumSize(QSize(0, 0))
        self.w_edit_path_out.setMaximumSize(QSize(16777215, 22))
        palette2 = QPalette()
        self.w_edit_path_out.setPalette(palette2)
        self.horizontalLayout_11 = QHBoxLayout(self.w_edit_path_out)
        self.horizontalLayout_11.setSpacing(0)
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.horizontalLayout_11.setContentsMargins(0, 0, 0, 0)
        self.line_edit_path_out = MyQLineEdit(self.w_edit_path_out)
        self.line_edit_path_out.setObjectName(u"line_edit_path_out")
        self.line_edit_path_out.setMaximumSize(QSize(16777215, 22))
        self.line_edit_path_out.setFont(font)
        self.line_edit_path_out.setStyleSheet(u"border-top: 1px solid gray;\n"
"border-left: 1px solid gray;\n"
"border-bottom: 1px solid gray;\n"
"")

        self.horizontalLayout_11.addWidget(self.line_edit_path_out)

        self.label_check_path_out = ClickableEditLabel(self.w_edit_path_out)
        self.label_check_path_out.setObjectName(u"label_check_path_out")
        self.label_check_path_out.setMinimumSize(QSize(22, 22))
        self.label_check_path_out.setMaximumSize(QSize(22, 22))
        self.label_check_path_out.setStyleSheet(u"border-top: 1px solid gray;\n"
"border-right: 1px solid gray;\n"
"border-bottom: 1px solid gray;\n"
"padding: 2px;")
        self.label_check_path_out.setPixmap(QPixmap(u""+ icons_path +"greenv.png"))
        self.label_check_path_out.setScaledContents(True)
        self.label_check_path_out.setMargin(0)
        self.label_check_path_out.setIndent(-1)

        self.horizontalLayout_11.addWidget(self.label_check_path_out)


        self.verticalLayout_14.addWidget(self.w_edit_path_out)


        self.horizontalLayout_6.addWidget(self.w_OutputFolder)

        self.w_button_path_out = QWidget(self.w_OutputFold_Button)
        self.w_button_path_out.setObjectName(u"w_button_path_out")
        self.w_button_path_out.setMinimumSize(QSize(0, 44))
        self.w_button_path_out.setMaximumSize(QSize(16777215, 44))
        self.verticalLayout_15 = QVBoxLayout(self.w_button_path_out)
        self.verticalLayout_15.setSpacing(0)
        self.verticalLayout_15.setObjectName(u"verticalLayout_15")
        self.verticalLayout_15.setContentsMargins(0, 0, 0, 0)
        self.label_path_out = QLabel(self.w_button_path_out)
        self.label_path_out.setObjectName(u"label_path_out")
        sizePolicy1.setHeightForWidth(self.label_path_out.sizePolicy().hasHeightForWidth())
        self.label_path_out.setSizePolicy(sizePolicy1)
        self.label_path_out.setMinimumSize(QSize(0, 18))
        self.label_path_out.setMaximumSize(QSize(16777215, 18))
        self.label_path_out.setFont(font3)

        self.verticalLayout_15.addWidget(self.label_path_out)

        self.button_path_out = QToolButton(self.w_button_path_out)
        self.button_path_out.setObjectName(u"button_path_out")
        self.button_path_out.setMinimumSize(QSize(26, 26))
        self.button_path_out.setMaximumSize(QSize(26, 26))
        self.button_path_out.setIcon(icon6)
        self.button_path_out.setIconSize(QSize(22, 22))

        self.verticalLayout_15.addWidget(self.button_path_out)


        self.horizontalLayout_6.addWidget(self.w_button_path_out)

        self.w_OutputImg = QWidget(self.w_OutputFold_Button)
        self.w_OutputImg.setObjectName(u"w_OutputImg")
        self.w_OutputImg.setMinimumSize(QSize(100, 0))
        self.w_OutputImg.setMaximumSize(QSize(16777215, 42))
        self.verticalLayout_16 = QVBoxLayout(self.w_OutputImg)
        self.verticalLayout_16.setSpacing(0)
        self.verticalLayout_16.setObjectName(u"verticalLayout_16")
        self.verticalLayout_16.setContentsMargins(0, 0, 0, 0)
        self.label_root_out = QLabel(self.w_OutputImg)
        self.label_root_out.setObjectName(u"label_root_out")
        sizePolicy1.setHeightForWidth(self.label_root_out.sizePolicy().hasHeightForWidth())
        self.label_root_out.setSizePolicy(sizePolicy1)
        self.label_root_out.setMinimumSize(QSize(0, 20))
        self.label_root_out.setMaximumSize(QSize(16777215, 20))
        palette3 = QPalette()
        palette3.setBrush(QPalette.Active, QPalette.Window, brush)
        palette3.setBrush(QPalette.Active, QPalette.ToolTipBase, brush)
        palette3.setBrush(QPalette.Inactive, QPalette.Window, brush1)
        palette3.setBrush(QPalette.Inactive, QPalette.ToolTipBase, brush2)
        palette3.setBrush(QPalette.Disabled, QPalette.Window, brush)
        palette3.setBrush(QPalette.Disabled, QPalette.ToolTipBase, brush2)
        self.label_root_out.setPalette(palette3)
        self.label_root_out.setFont(font3)

        self.verticalLayout_16.addWidget(self.label_root_out)

        self.w_edit_root_out = QWidget(self.w_OutputImg)
        self.w_edit_root_out.setObjectName(u"w_edit_root_out")
        self.w_edit_root_out.setMinimumSize(QSize(0, 0))
        self.w_edit_root_out.setMaximumSize(QSize(16777215, 22))
        self.horizontalLayout_13 = QHBoxLayout(self.w_edit_root_out)
        self.horizontalLayout_13.setSpacing(0)
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.horizontalLayout_13.setContentsMargins(0, 0, 0, 0)
        self.line_edit_root_out = MyQLineEdit(self.w_edit_root_out)
        self.line_edit_root_out.setObjectName(u"line_edit_root_out")
        self.line_edit_root_out.setMaximumSize(QSize(16777215, 22))
        self.line_edit_root_out.setFont(font)
        self.line_edit_root_out.setStyleSheet(u"border-top: 1px solid gray;\n"
"border-left: 1px solid gray;\n"
"border-bottom: 1px solid gray;\n"
"")

        self.horizontalLayout_13.addWidget(self.line_edit_root_out)

        self.label_check_root = ClickableEditLabel(self.w_edit_root_out)
        self.label_check_root.setObjectName(u"label_check_root")
        self.label_check_root.setMinimumSize(QSize(22, 22))
        self.label_check_root.setMaximumSize(QSize(22, 22))
        self.label_check_root.setStyleSheet(u"border-top: 1px solid gray;\n"
"border-right: 1px solid gray;\n"
"border-bottom: 1px solid gray;\n"
"padding: 2px;")
        self.label_check_root.setPixmap(QPixmap(u""+ icons_path +"greenv.png"))
        self.label_check_root.setScaledContents(True)
        self.label_check_root.setMargin(0)

        self.horizontalLayout_13.addWidget(self.label_check_root)


        self.verticalLayout_16.addWidget(self.w_edit_root_out)


        self.horizontalLayout_6.addWidget(self.w_OutputImg)


        self.verticalLayout_7.addWidget(self.w_OutputFold_Button)

        QWidget.setTabOrder(self.button_close_tab, self.scrollArea)
        QWidget.setTabOrder(self.scrollArea, self.line_edit_path)
        QWidget.setTabOrder(self.line_edit_path, self.button_path)
        QWidget.setTabOrder(self.button_path, self.line_edit_cameras)
        QWidget.setTabOrder(self.line_edit_cameras, self.button_import)
        QWidget.setTabOrder(self.button_import, self.list_images)
        QWidget.setTabOrder(self.list_images, self.spin_x)
        QWidget.setTabOrder(self.spin_x, self.spin_y)
        QWidget.setTabOrder(self.spin_y, self.spin_w)
        QWidget.setTabOrder(self.spin_w, self.spin_h)
        QWidget.setTabOrder(self.spin_h, self.button_resize)

        self.retranslateUi(InputTab_CalVi)

        QMetaObject.connectSlotsByName(InputTab_CalVi)
    # setupUi

    def retranslateUi(self, InputTab_CalVi):
        InputTab_CalVi.setWindowTitle(QCoreApplication.translate("InputTab_CalVi", u"Import - CalVi", None))
#if QT_CONFIG(accessibility)
        InputTab_CalVi.setAccessibleName("")
#endif // QT_CONFIG(accessibility)
        self.icon.setText("")
        self.name_tab.setText(QCoreApplication.translate("InputTab_CalVi", u" Input", None))
        self.label_number.setText(QCoreApplication.translate("InputTab_CalVi", u"1", None))
#if QT_CONFIG(tooltip)
        self.button_back.setToolTip(QCoreApplication.translate("InputTab_CalVi", u"Undo", None))
#endif // QT_CONFIG(tooltip)
        self.button_back.setText("")
#if QT_CONFIG(shortcut)
        self.button_back.setShortcut(QCoreApplication.translate("InputTab_CalVi", u"Ctrl+Z", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(tooltip)
        self.button_forward.setToolTip(QCoreApplication.translate("InputTab_CalVi", u"Redo", None))
#endif // QT_CONFIG(tooltip)
        self.button_forward.setText("")
#if QT_CONFIG(shortcut)
        self.button_forward.setShortcut(QCoreApplication.translate("InputTab_CalVi", u"Ctrl+Y", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(tooltip)
        self.button_close_tab.setToolTip(QCoreApplication.translate("InputTab_CalVi", u"Close tab", None))
#endif // QT_CONFIG(tooltip)
        self.button_close_tab.setText("")
#if QT_CONFIG(shortcut)
        self.button_close_tab.setShortcut(QCoreApplication.translate("InputTab_CalVi", u"Alt+I", None))
#endif // QT_CONFIG(shortcut)
        self.label_path.setText(QCoreApplication.translate("InputTab_CalVi", u"Input folder path", None))
#if QT_CONFIG(tooltip)
        self.button_data.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.button_data.setText("")
#if QT_CONFIG(tooltip)
        self.line_edit_path.setToolTip(QCoreApplication.translate("InputTab_CalVi", u"Path of the directory containing the image files", None))
#endif // QT_CONFIG(tooltip)
        self.line_edit_path.setText(QCoreApplication.translate("InputTab_CalVi", u".\\img\\fold3\\", None))
        self.label_check_path.setText("")
        self.label_path_2.setText("")
#if QT_CONFIG(tooltip)
        self.button_path.setToolTip(QCoreApplication.translate("InputTab_CalVi", u"Explore and find the path of the directory containing the image files", None))
#endif // QT_CONFIG(tooltip)
        self.button_path.setText("")
#if QT_CONFIG(shortcut)
        self.button_path.setShortcut(QCoreApplication.translate("InputTab_CalVi", u"Ctrl+Alt+I", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(tooltip)
        self.radio_Cam.setToolTip(QCoreApplication.translate("InputTab_CalVi", u"Image filenames contain the pattern _cam* (with * being the camera identification number)", None))
#endif // QT_CONFIG(tooltip)
        self.radio_Cam.setText(QCoreApplication.translate("InputTab_CalVi", u"_cam* in filename", None))
        self.label_edit_cams.setText(QCoreApplication.translate("InputTab_CalVi", u"Camera id. numbers", None))
#if QT_CONFIG(tooltip)
        self.line_edit_cameras.setToolTip(QCoreApplication.translate("InputTab_CalVi", u"Camera identification numbers (integers)", None))
#endif // QT_CONFIG(tooltip)
        self.line_edit_cameras.setText(QCoreApplication.translate("InputTab_CalVi", u"0, 1", None))
        self.label_root_2.setText("")
#if QT_CONFIG(tooltip)
        self.button_import.setToolTip(QCoreApplication.translate("InputTab_CalVi", u"Browse and import the image files", None))
#endif // QT_CONFIG(tooltip)
        self.button_import.setText("")
#if QT_CONFIG(shortcut)
        self.button_import.setShortcut(QCoreApplication.translate("InputTab_CalVi", u"Ctrl+D", None))
#endif // QT_CONFIG(shortcut)
        self.label_import_plane.setText("")
#if QT_CONFIG(tooltip)
        self.button_import_plane.setToolTip(QCoreApplication.translate("InputTab_CalVi", u"Browse and import the plane parameters", None))
#endif // QT_CONFIG(tooltip)
        self.button_import_plane.setText("")
#if QT_CONFIG(shortcut)
        self.button_import_plane.setShortcut(QCoreApplication.translate("InputTab_CalVi", u"Ctrl+F", None))
#endif // QT_CONFIG(shortcut)
        self.label_down.setText("")
#if QT_CONFIG(tooltip)
        self.button_down.setToolTip(QCoreApplication.translate("InputTab_CalVi", u"Move item down in the list", None))
#endif // QT_CONFIG(tooltip)
        self.button_down.setText("")
#if QT_CONFIG(shortcut)
        self.button_down.setShortcut(QCoreApplication.translate("InputTab_CalVi", u"Ctrl+Down", None))
#endif // QT_CONFIG(shortcut)
        self.label_up.setText("")
#if QT_CONFIG(tooltip)
        self.button_up.setToolTip(QCoreApplication.translate("InputTab_CalVi", u"Move item up in the list", None))
#endif // QT_CONFIG(tooltip)
        self.button_up.setText("")
#if QT_CONFIG(shortcut)
        self.button_up.setShortcut(QCoreApplication.translate("InputTab_CalVi", u"Ctrl+Up", None))
#endif // QT_CONFIG(shortcut)
        self.label_root_3.setText("")
#if QT_CONFIG(tooltip)
        self.button_delete.setToolTip(QCoreApplication.translate("InputTab_CalVi", u"Delete selected image files from the table below", None))
#endif // QT_CONFIG(tooltip)
        self.button_delete.setText("")
#if QT_CONFIG(shortcut)
        self.button_delete.setShortcut(QCoreApplication.translate("InputTab_CalVi", u"Backspace", None))
#endif // QT_CONFIG(shortcut)
        self.label_root_4.setText("")
#if QT_CONFIG(tooltip)
        self.button_clean.setToolTip(QCoreApplication.translate("InputTab_CalVi", u"Delete all the imported image files", None))
#endif // QT_CONFIG(tooltip)
        self.button_clean.setText("")
#if QT_CONFIG(shortcut)
        self.button_clean.setShortcut(QCoreApplication.translate("InputTab_CalVi", u"Ctrl+Shift+T", None))
#endif // QT_CONFIG(shortcut)
        ___qtablewidgetitem = self.list_images.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("InputTab_CalVi", u"Image filename", None));
        ___qtablewidgetitem1 = self.list_images.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("InputTab_CalVi", u"Plane parameters", None));
        ___qtablewidgetitem2 = self.list_images.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("InputTab_CalVi", u"Info", None));
        ___qtablewidgetitem3 = self.list_images.verticalHeaderItem(0)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("InputTab_CalVi", u"0", None));
        ___qtablewidgetitem4 = self.list_images.verticalHeaderItem(1)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("InputTab_CalVi", u"1", None));
#if QT_CONFIG(tooltip)
        self.list_images.setToolTip(QCoreApplication.translate("InputTab_CalVi", u"List of identified calibration images", None))
#endif // QT_CONFIG(tooltip)
        self.label_info.setText(QCoreApplication.translate("InputTab_CalVi", u"Info", None))
        self.label_x.setText(QCoreApplication.translate("InputTab_CalVi", u"X0 (# column)", None))
#if QT_CONFIG(tooltip)
        self.spin_x.setToolTip(QCoreApplication.translate("InputTab_CalVi", u"First column of the image area to process", None))
#endif // QT_CONFIG(tooltip)
        self.label_y.setText(QCoreApplication.translate("InputTab_CalVi", u"Y0 (# row)", None))
#if QT_CONFIG(tooltip)
        self.spin_y.setToolTip(QCoreApplication.translate("InputTab_CalVi", u"First row of the image area to process", None))
#endif // QT_CONFIG(tooltip)
        self.label_w.setText(QCoreApplication.translate("InputTab_CalVi", u"Width (pixels)", None))
#if QT_CONFIG(tooltip)
        self.spin_w.setToolTip(QCoreApplication.translate("InputTab_CalVi", u"Width of the image area to process", None))
#endif // QT_CONFIG(tooltip)
        self.label_h.setText(QCoreApplication.translate("InputTab_CalVi", u"Height (pixels)", None))
#if QT_CONFIG(tooltip)
        self.spin_h.setToolTip(QCoreApplication.translate("InputTab_CalVi", u"Heigth of the image area to process", None))
#endif // QT_CONFIG(tooltip)
        self.label_button_resize.setText("")
#if QT_CONFIG(tooltip)
        self.button_resize.setToolTip(QCoreApplication.translate("InputTab_CalVi", u"Restore full image", None))
#endif // QT_CONFIG(tooltip)
        self.button_resize.setText("")
        self.icon_Output.setText("")
        self.name_tab_Output.setText(QCoreApplication.translate("InputTab_CalVi", u" Output", None))
#if QT_CONFIG(tooltip)
        self.radio_Same_as_input.setToolTip(QCoreApplication.translate("InputTab_CalVi", u"Save the output files in the folder containing the input image files", None))
#endif // QT_CONFIG(tooltip)
        self.radio_Same_as_input.setText(QCoreApplication.translate("InputTab_CalVi", u"Same as input", None))
        self.label_path_outfold.setText(QCoreApplication.translate("InputTab_CalVi", u"Output folder path", None))
#if QT_CONFIG(tooltip)
        self.line_edit_path_out.setToolTip(QCoreApplication.translate("InputTab_CalVi", u"Path of the directory where to the save the output files", None))
#endif // QT_CONFIG(tooltip)
        self.line_edit_path_out.setText(QCoreApplication.translate("InputTab_CalVi", u".\\img\\fold3\\", None))
        self.label_check_path_out.setText("")
        self.label_path_out.setText("")
#if QT_CONFIG(tooltip)
        self.button_path_out.setToolTip(QCoreApplication.translate("InputTab_CalVi", u"Explore and select the path of the directory of the output files", None))
#endif // QT_CONFIG(tooltip)
        self.button_path_out.setText("")
#if QT_CONFIG(shortcut)
        self.button_path_out.setShortcut(QCoreApplication.translate("InputTab_CalVi", u"Ctrl+O, Ctrl+I", None))
#endif // QT_CONFIG(shortcut)
        self.label_root_out.setText(QCoreApplication.translate("InputTab_CalVi", u"Root of output files", None))
#if QT_CONFIG(tooltip)
        self.line_edit_root_out.setToolTip(QCoreApplication.translate("InputTab_CalVi", u"Pattern of the filenames of the output files", None))
#endif // QT_CONFIG(tooltip)
        self.line_edit_root_out.setText(QCoreApplication.translate("InputTab_CalVi", u"out", None))
        self.label_check_root.setText("")
    # retranslateUi


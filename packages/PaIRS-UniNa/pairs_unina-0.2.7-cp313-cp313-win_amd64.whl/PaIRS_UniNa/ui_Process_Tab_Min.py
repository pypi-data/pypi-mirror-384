from .addwidgets_ps import icons_path
# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Process_Tab_Min.ui'
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
    QLabel, QLayout, QRadioButton, QScrollArea,
    QSizePolicy, QSpacerItem, QToolButton, QVBoxLayout,
    QWidget)

from .addwidgets_ps import (MyQCombo, MyQDoubleSpin, MyTabLabel)

class Ui_ProcessTab_Min(object):
    def setupUi(self, ProcessTab_Min):
        if not ProcessTab_Min.objectName():
            ProcessTab_Min.setObjectName(u"ProcessTab_Min")
        ProcessTab_Min.resize(500, 680)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(ProcessTab_Min.sizePolicy().hasHeightForWidth())
        ProcessTab_Min.setSizePolicy(sizePolicy)
        ProcessTab_Min.setMinimumSize(QSize(500, 680))
        ProcessTab_Min.setMaximumSize(QSize(1000, 16777215))
        font = QFont()
        font.setPointSize(11)
        ProcessTab_Min.setFont(font)
        icon1 = QIcon()
        icon1.addFile(u""+ icons_path +"process_logo.png", QSize(), QIcon.Normal, QIcon.Off)
        ProcessTab_Min.setWindowIcon(icon1)
        self.verticalLayout_65 = QVBoxLayout(ProcessTab_Min)
        self.verticalLayout_65.setSpacing(5)
        self.verticalLayout_65.setObjectName(u"verticalLayout_65")
        self.verticalLayout_65.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.verticalLayout_65.setContentsMargins(10, 10, 10, 10)
        self.w_Mode = QWidget(ProcessTab_Min)
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

        self.separator = QFrame(ProcessTab_Min)
        self.separator.setObjectName(u"separator")
        self.separator.setMinimumSize(QSize(0, 5))
        self.separator.setFrameShape(QFrame.Shape.HLine)
        self.separator.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_65.addWidget(self.separator)

        self.scrollArea = QScrollArea(ProcessTab_Min)
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
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 480, 605))
        sizePolicy.setHeightForWidth(self.scrollAreaWidgetContents.sizePolicy().hasHeightForWidth())
        self.scrollAreaWidgetContents.setSizePolicy(sizePolicy)
        self.scrollAreaWidgetContents.setMinimumSize(QSize(0, 0))
        self.scrollAreaWidgetContents.setStyleSheet(u"\u2020")
        self.verticalLayout_10 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_10.setSpacing(20)
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.verticalLayout_10.setContentsMargins(0, 15, 10, 5)
        self.radio_TR = QRadioButton(self.scrollAreaWidgetContents)
        self.radio_TR.setObjectName(u"radio_TR")

        self.verticalLayout_10.addWidget(self.radio_TR)

        self.w_LaserType = QWidget(self.scrollAreaWidgetContents)
        self.w_LaserType.setObjectName(u"w_LaserType")
        self.w_LaserType.setMinimumSize(QSize(0, 44))
        self.w_LaserType.setMaximumSize(QSize(200, 44))
        self.verticalLayout_67 = QVBoxLayout(self.w_LaserType)
        self.verticalLayout_67.setSpacing(0)
        self.verticalLayout_67.setObjectName(u"verticalLayout_67")
        self.verticalLayout_67.setContentsMargins(0, 0, 0, 0)
        self.label_LaserType = QLabel(self.w_LaserType)
        self.label_LaserType.setObjectName(u"label_LaserType")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.label_LaserType.sizePolicy().hasHeightForWidth())
        self.label_LaserType.setSizePolicy(sizePolicy2)
        self.label_LaserType.setMinimumSize(QSize(80, 20))
        self.label_LaserType.setMaximumSize(QSize(16777215, 20))
        font3 = QFont()
        font3.setPointSize(10)
        font3.setBold(False)
        font3.setItalic(True)
        self.label_LaserType.setFont(font3)
        self.label_LaserType.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout_67.addWidget(self.label_LaserType)

        self.combo_LaserType = MyQCombo(self.w_LaserType)
        self.combo_LaserType.addItem("")
        self.combo_LaserType.addItem("")
        self.combo_LaserType.setObjectName(u"combo_LaserType")
        self.combo_LaserType.setMinimumSize(QSize(85, 0))
        self.combo_LaserType.setMaximumSize(QSize(16777215, 24))
        self.combo_LaserType.setFont(font)

        self.verticalLayout_67.addWidget(self.combo_LaserType)


        self.verticalLayout_10.addWidget(self.w_LaserType)

        self.w_example_label = QWidget(self.scrollAreaWidgetContents)
        self.w_example_label.setObjectName(u"w_example_label")
        self.horizontalLayout = QHBoxLayout(self.w_example_label)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.hs_left = QSpacerItem(5, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.hs_left)

        self.example_label = QLabel(self.w_example_label)
        self.example_label.setObjectName(u"example_label")
        sizePolicy.setHeightForWidth(self.example_label.sizePolicy().hasHeightForWidth())
        self.example_label.setSizePolicy(sizePolicy)
        self.example_label.setMinimumSize(QSize(400, 180))
        self.example_label.setMaximumSize(QSize(400, 180))
        self.example_label.setPixmap(QPixmap(u""+ icons_path +"laser_NTR.png"))
        self.example_label.setScaledContents(True)

        self.horizontalLayout.addWidget(self.example_label)

        self.hs_right = QSpacerItem(5, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.hs_right)


        self.verticalLayout_10.addWidget(self.w_example_label)

        self.w_further_val = QWidget(self.scrollAreaWidgetContents)
        self.w_further_val.setObjectName(u"w_further_val")
        self.w_further_val.setMinimumSize(QSize(0, 44))
        self.w_further_val.setMaximumSize(QSize(16777215, 44))
        self.horizontalLayout_5 = QHBoxLayout(self.w_further_val)
        self.horizontalLayout_5.setSpacing(10)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.w_MinVal = QWidget(self.w_further_val)
        self.w_MinVal.setObjectName(u"w_MinVal")
        self.w_MinVal.setMinimumSize(QSize(150, 44))
        self.w_MinVal.setMaximumSize(QSize(16777215, 44))
        self.verticalLayout_31 = QVBoxLayout(self.w_MinVal)
        self.verticalLayout_31.setSpacing(0)
        self.verticalLayout_31.setObjectName(u"verticalLayout_31")
        self.verticalLayout_31.setContentsMargins(0, 0, 0, 0)
        self.label_MinVal = QLabel(self.w_MinVal)
        self.label_MinVal.setObjectName(u"label_MinVal")
        sizePolicy2.setHeightForWidth(self.label_MinVal.sizePolicy().hasHeightForWidth())
        self.label_MinVal.setSizePolicy(sizePolicy2)
        self.label_MinVal.setMinimumSize(QSize(0, 20))
        self.label_MinVal.setMaximumSize(QSize(16777215, 20))
        self.label_MinVal.setFont(font3)
        self.label_MinVal.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout_31.addWidget(self.label_MinVal)

        self.spin_SogliaNoise = MyQDoubleSpin(self.w_MinVal)
        self.spin_SogliaNoise.setObjectName(u"spin_SogliaNoise")
        self.spin_SogliaNoise.setMinimumSize(QSize(0, 0))
        self.spin_SogliaNoise.setMaximumSize(QSize(1000000, 24))
        self.spin_SogliaNoise.setFont(font)
        self.spin_SogliaNoise.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_SogliaNoise.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
        self.spin_SogliaNoise.setMaximum(4294967296.000000000000000)
        self.spin_SogliaNoise.setSingleStep(0.100000000000000)
        self.spin_SogliaNoise.setValue(5.000000000000000)

        self.verticalLayout_31.addWidget(self.spin_SogliaNoise)


        self.horizontalLayout_5.addWidget(self.w_MinVal)

        self.w_MinStD = QWidget(self.w_further_val)
        self.w_MinStD.setObjectName(u"w_MinStD")
        self.w_MinStD.setMinimumSize(QSize(150, 44))
        self.w_MinStD.setMaximumSize(QSize(16777215, 44))
        self.verticalLayout_32 = QVBoxLayout(self.w_MinStD)
        self.verticalLayout_32.setSpacing(0)
        self.verticalLayout_32.setObjectName(u"verticalLayout_32")
        self.verticalLayout_32.setContentsMargins(0, 0, 0, 0)
        self.label_MinStD = QLabel(self.w_MinStD)
        self.label_MinStD.setObjectName(u"label_MinStD")
        sizePolicy2.setHeightForWidth(self.label_MinStD.sizePolicy().hasHeightForWidth())
        self.label_MinStD.setSizePolicy(sizePolicy2)
        self.label_MinStD.setMinimumSize(QSize(0, 20))
        self.label_MinStD.setMaximumSize(QSize(16777215, 20))
        self.label_MinStD.setFont(font3)
        self.label_MinStD.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout_32.addWidget(self.label_MinStD)

        self.spin_SogliaStd = MyQDoubleSpin(self.w_MinStD)
        self.spin_SogliaStd.setObjectName(u"spin_SogliaStd")
        self.spin_SogliaStd.setMinimumSize(QSize(0, 0))
        self.spin_SogliaStd.setMaximumSize(QSize(1000000, 24))
        self.spin_SogliaStd.setFont(font)
        self.spin_SogliaStd.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_SogliaStd.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
        self.spin_SogliaStd.setSingleStep(0.100000000000000)
        self.spin_SogliaStd.setValue(1.500000000000000)

        self.verticalLayout_32.addWidget(self.spin_SogliaStd)


        self.horizontalLayout_5.addWidget(self.w_MinStD)

        self.hs_val = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.hs_val)


        self.verticalLayout_10.addWidget(self.w_further_val)

        self.verticalSpacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_10.addItem(self.verticalSpacer)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout_65.addWidget(self.scrollArea)

        QWidget.setTabOrder(self.button_back, self.button_forward)
        QWidget.setTabOrder(self.button_forward, self.button_close_tab)
        QWidget.setTabOrder(self.button_close_tab, self.scrollArea)

        self.retranslateUi(ProcessTab_Min)

        QMetaObject.connectSlotsByName(ProcessTab_Min)
    # setupUi

    def retranslateUi(self, ProcessTab_Min):
        ProcessTab_Min.setWindowTitle(QCoreApplication.translate("ProcessTab_Min", u"Process", None))
        self.icon.setText("")
        self.name_tab.setText(QCoreApplication.translate("ProcessTab_Min", u" Process", None))
        self.label_number.setText(QCoreApplication.translate("ProcessTab_Min", u"1", None))
#if QT_CONFIG(tooltip)
        self.button_back.setToolTip(QCoreApplication.translate("ProcessTab_Min", u"Undo", None))
#endif // QT_CONFIG(tooltip)
        self.button_back.setText("")
#if QT_CONFIG(tooltip)
        self.button_forward.setToolTip(QCoreApplication.translate("ProcessTab_Min", u"Redo", None))
#endif // QT_CONFIG(tooltip)
        self.button_forward.setText("")
#if QT_CONFIG(tooltip)
        self.button_close_tab.setToolTip(QCoreApplication.translate("ProcessTab_Min", u"Close tab", None))
#endif // QT_CONFIG(tooltip)
        self.button_close_tab.setText("")
#if QT_CONFIG(shortcut)
        self.button_close_tab.setShortcut(QCoreApplication.translate("ProcessTab_Min", u"Alt+P", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(tooltip)
        self.radio_TR.setToolTip(QCoreApplication.translate("ProcessTab_Min", u"If activated, the sequence is assumed to be time-resolved", None))
#endif // QT_CONFIG(tooltip)
        self.radio_TR.setText(QCoreApplication.translate("ProcessTab_Min", u"Time resolved sequence", None))
        self.label_LaserType.setText(QCoreApplication.translate("ProcessTab_Min", u"Laser setup", None))
        self.combo_LaserType.setItemText(0, QCoreApplication.translate("ProcessTab_Min", u"single laser", None))
        self.combo_LaserType.setItemText(1, QCoreApplication.translate("ProcessTab_Min", u"double laser", None))

#if QT_CONFIG(tooltip)
        self.combo_LaserType.setToolTip(QCoreApplication.translate("ProcessTab_Min", u"Type of laser setup", None))
#endif // QT_CONFIG(tooltip)
        self.example_label.setText("")
        self.label_MinVal.setText(QCoreApplication.translate("ProcessTab_Min", u"Min. allowed value", None))
#if QT_CONFIG(tooltip)
        self.spin_SogliaNoise.setToolTip(QCoreApplication.translate("ProcessTab_Min", u"Minimum value of intensity level to consider data in the window reliable", None))
#endif // QT_CONFIG(tooltip)
        self.label_MinStD.setText(QCoreApplication.translate("ProcessTab_Min", u"Min. allowed st.d. value", None))
#if QT_CONFIG(tooltip)
        self.spin_SogliaStd.setToolTip(QCoreApplication.translate("ProcessTab_Min", u"Minimum value of st.d. of intensity levels to consider data in the window reliable", None))
#endif // QT_CONFIG(tooltip)
    # retranslateUi


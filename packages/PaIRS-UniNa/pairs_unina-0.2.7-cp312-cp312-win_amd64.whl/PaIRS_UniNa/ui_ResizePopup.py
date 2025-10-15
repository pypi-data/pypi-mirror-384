from .addwidgets_ps import icons_path
# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ResizePopup.ui'
##
## Created by: Qt User Interface Compiler version 6.4.2
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QSizePolicy, QToolButton,
    QWidget)

class Ui_ResizePopup(object):
    def setupUi(self, ResizePopup):
        if not ResizePopup.objectName():
            ResizePopup.setObjectName(u"ResizePopup")
        ResizePopup.resize(280, 60)
        ResizePopup.setMinimumSize(QSize(280, 60))
        ResizePopup.setMaximumSize(QSize(280, 60))
        self.horizontalLayout_2 = QHBoxLayout(ResizePopup)
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.w_b_size = QWidget(ResizePopup)
        self.w_b_size.setObjectName(u"w_b_size")
        self.horizontalLayout = QHBoxLayout(self.w_b_size)
        self.horizontalLayout.setSpacing(10)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(5, 10, 5, 10)
        self.w_button_close_tab = QWidget(self.w_b_size)
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
        self.button_close_tab.setLayoutDirection(Qt.LeftToRight)
        self.button_close_tab.setStyleSheet(u"QToolButton{\n"
"border-radius: 15px;\n"
"}")
        icon = QIcon()
        icon.addFile(u""+ icons_path +"close.png", QSize(), QIcon.Normal, QIcon.Off)
        self.button_close_tab.setIcon(icon)
        self.button_close_tab.setIconSize(QSize(15, 15))

        self.horizontalLayout_20.addWidget(self.button_close_tab)


        self.horizontalLayout.addWidget(self.w_button_close_tab)

        self.b0 = QToolButton(self.w_b_size)
        self.b0.setObjectName(u"b0")
        self.b0.setMinimumSize(QSize(30, 30))
        self.b0.setMaximumSize(QSize(30, 30))
        self.b0.setStyleSheet(u"")
        icon1 = QIcon()
        icon1.addFile(u""+ icons_path +"w0.png", QSize(), QIcon.Normal, QIcon.Off)
        self.b0.setIcon(icon1)
        self.b0.setIconSize(QSize(30, 30))

        self.horizontalLayout.addWidget(self.b0)

        self.b1 = QToolButton(self.w_b_size)
        self.b1.setObjectName(u"b1")
        self.b1.setMinimumSize(QSize(30, 30))
        self.b1.setMaximumSize(QSize(30, 30))
        self.b1.setStyleSheet(u"")
        icon2 = QIcon()
        icon2.addFile(u""+ icons_path +"w1.png", QSize(), QIcon.Normal, QIcon.Off)
        self.b1.setIcon(icon2)
        self.b1.setIconSize(QSize(30, 30))

        self.horizontalLayout.addWidget(self.b1)

        self.b2 = QToolButton(self.w_b_size)
        self.b2.setObjectName(u"b2")
        self.b2.setMinimumSize(QSize(30, 30))
        self.b2.setMaximumSize(QSize(30, 30))
        self.b2.setStyleSheet(u"")
        icon3 = QIcon()
        icon3.addFile(u""+ icons_path +"w2.png", QSize(), QIcon.Normal, QIcon.Off)
        self.b2.setIcon(icon3)
        self.b2.setIconSize(QSize(30, 30))

        self.horizontalLayout.addWidget(self.b2)

        self.b3 = QToolButton(self.w_b_size)
        self.b3.setObjectName(u"b3")
        self.b3.setMinimumSize(QSize(30, 30))
        self.b3.setMaximumSize(QSize(30, 30))
        self.b3.setStyleSheet(u"")
        icon4 = QIcon()
        icon4.addFile(u""+ icons_path +"w3.png", QSize(), QIcon.Normal, QIcon.Off)
        self.b3.setIcon(icon4)
        self.b3.setIconSize(QSize(30, 30))

        self.horizontalLayout.addWidget(self.b3)

        self.b4 = QToolButton(self.w_b_size)
        self.b4.setObjectName(u"b4")
        self.b4.setMinimumSize(QSize(30, 30))
        self.b4.setMaximumSize(QSize(30, 30))
        self.b4.setStyleSheet(u"")
        icon5 = QIcon()
        icon5.addFile(u""+ icons_path +"w4.png", QSize(), QIcon.Normal, QIcon.Off)
        self.b4.setIcon(icon5)
        self.b4.setIconSize(QSize(30, 30))

        self.horizontalLayout.addWidget(self.b4)

        self.b5 = QToolButton(self.w_b_size)
        self.b5.setObjectName(u"b5")
        self.b5.setMinimumSize(QSize(30, 30))
        self.b5.setMaximumSize(QSize(30, 30))
        self.b5.setStyleSheet(u"")
        icon6 = QIcon()
        icon6.addFile(u""+ icons_path +"w5.png", QSize(), QIcon.Normal, QIcon.Off)
        self.b5.setIcon(icon6)
        self.b5.setIconSize(QSize(30, 30))

        self.horizontalLayout.addWidget(self.b5)


        self.horizontalLayout_2.addWidget(self.w_b_size)

        QWidget.setTabOrder(self.button_close_tab, self.b0)
        QWidget.setTabOrder(self.b0, self.b1)
        QWidget.setTabOrder(self.b1, self.b2)
        QWidget.setTabOrder(self.b2, self.b3)
        QWidget.setTabOrder(self.b3, self.b4)
        QWidget.setTabOrder(self.b4, self.b5)

        self.retranslateUi(ResizePopup)

        QMetaObject.connectSlotsByName(ResizePopup)
    # setupUi

    def retranslateUi(self, ResizePopup):
        ResizePopup.setWindowTitle(QCoreApplication.translate("ResizePopup", u"ResizePopup", None))
#if QT_CONFIG(tooltip)
        self.button_close_tab.setToolTip(QCoreApplication.translate("ResizePopup", u"Close popup", None))
#endif // QT_CONFIG(tooltip)
        self.button_close_tab.setText("")
#if QT_CONFIG(shortcut)
        self.button_close_tab.setShortcut(QCoreApplication.translate("ResizePopup", u"Esc", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(tooltip)
        self.b0.setToolTip(QCoreApplication.translate("ResizePopup", u"Default configuration", None))
#endif // QT_CONFIG(tooltip)
        self.b0.setText("")
#if QT_CONFIG(shortcut)
        self.b0.setShortcut(QCoreApplication.translate("ResizePopup", u"0", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(tooltip)
        self.b1.setToolTip(QCoreApplication.translate("ResizePopup", u"1 tab configuration", None))
#endif // QT_CONFIG(tooltip)
        self.b1.setText(QCoreApplication.translate("ResizePopup", u"...", None))
#if QT_CONFIG(shortcut)
        self.b1.setShortcut(QCoreApplication.translate("ResizePopup", u"1", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(tooltip)
        self.b2.setToolTip(QCoreApplication.translate("ResizePopup", u"2 tabs configuration", None))
#endif // QT_CONFIG(tooltip)
        self.b2.setText(QCoreApplication.translate("ResizePopup", u"...", None))
#if QT_CONFIG(shortcut)
        self.b2.setShortcut(QCoreApplication.translate("ResizePopup", u"2", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(tooltip)
        self.b3.setToolTip(QCoreApplication.translate("ResizePopup", u"3 tabs configuration", None))
#endif // QT_CONFIG(tooltip)
        self.b3.setText(QCoreApplication.translate("ResizePopup", u"...", None))
#if QT_CONFIG(shortcut)
        self.b3.setShortcut(QCoreApplication.translate("ResizePopup", u"3", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(tooltip)
        self.b4.setToolTip(QCoreApplication.translate("ResizePopup", u"Run configuration", None))
#endif // QT_CONFIG(tooltip)
        self.b4.setText("")
#if QT_CONFIG(shortcut)
        self.b4.setShortcut(QCoreApplication.translate("ResizePopup", u"R", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(tooltip)
        self.b5.setToolTip(QCoreApplication.translate("ResizePopup", u"Last configuration", None))
#endif // QT_CONFIG(tooltip)
        self.b5.setText("")
#if QT_CONFIG(shortcut)
        self.b5.setShortcut(QCoreApplication.translate("ResizePopup", u"Backspace", None))
#endif // QT_CONFIG(shortcut)
    # retranslateUi


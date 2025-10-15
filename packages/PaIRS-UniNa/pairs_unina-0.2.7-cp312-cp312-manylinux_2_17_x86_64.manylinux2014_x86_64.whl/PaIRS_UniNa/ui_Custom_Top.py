from .addwidgets_ps import icons_path
# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Custom_Top.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QHBoxLayout, QHeaderView,
    QLabel, QPushButton, QSizePolicy, QSpacerItem,
    QToolButton, QTreeWidgetItem, QVBoxLayout, QWidget)

from .addwidgets_ps import myQTreeWidget

class Ui_Custom_Top(object):
    def setupUi(self, Custom_Top):
        if not Custom_Top.objectName():
            Custom_Top.setObjectName(u"Custom_Top")
        Custom_Top.resize(480, 480)
        Custom_Top.setMinimumSize(QSize(25, 25))
        icon = QIcon()
        icon.addFile(u""+ icons_path +"process_logo.png", QSize(), QIcon.Normal, QIcon.Off)
        Custom_Top.setWindowIcon(icon)
        self.verticalLayout = QVBoxLayout(Custom_Top)
        self.verticalLayout.setSpacing(3)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(10, 10, 10, 10)
        self.w_controls = QWidget(Custom_Top)
        self.w_controls.setObjectName(u"w_controls")
        self.w_controls.setMinimumSize(QSize(0, 25))
        self.w_controls.setMaximumSize(QSize(16777215, 25))
        self.horizontalLayout = QHBoxLayout(self.w_controls)
        self.horizontalLayout.setSpacing(5)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.label_tree = QLabel(self.w_controls)
        self.label_tree.setObjectName(u"label_tree")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_tree.sizePolicy().hasHeightForWidth())
        self.label_tree.setSizePolicy(sizePolicy)
        self.label_tree.setMinimumSize(QSize(0, 20))
        self.label_tree.setMaximumSize(QSize(150, 20))
        font = QFont()
        font.setPointSize(10)
        font.setBold(False)
        font.setItalic(True)
        self.label_tree.setFont(font)
        self.label_tree.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.horizontalLayout.addWidget(self.label_tree)

        self.hs = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.hs)

        self.button_down = QToolButton(self.w_controls)
        self.button_down.setObjectName(u"button_down")
        self.button_down.setMinimumSize(QSize(25, 25))
        self.button_down.setMaximumSize(QSize(25, 25))
        icon1 = QIcon()
        icon1.addFile(u""+ icons_path +"down.png", QSize(), QIcon.Normal, QIcon.Off)
        self.button_down.setIcon(icon1)
        self.button_down.setIconSize(QSize(18, 18))
        self.button_down.setArrowType(Qt.NoArrow)

        self.horizontalLayout.addWidget(self.button_down)

        self.button_up = QToolButton(self.w_controls)
        self.button_up.setObjectName(u"button_up")
        self.button_up.setMinimumSize(QSize(25, 25))
        self.button_up.setMaximumSize(QSize(25, 25))
        icon2 = QIcon()
        icon2.addFile(u""+ icons_path +"up.png", QSize(), QIcon.Normal, QIcon.Off)
        self.button_up.setIcon(icon2)
        self.button_up.setIconSize(QSize(18, 18))
        self.button_up.setArrowType(Qt.NoArrow)

        self.horizontalLayout.addWidget(self.button_up)

        self.button_import = QToolButton(self.w_controls)
        self.button_import.setObjectName(u"button_import")
        self.button_import.setMinimumSize(QSize(25, 25))
        self.button_import.setMaximumSize(QSize(25, 25))
        icon3 = QIcon()
        icon3.addFile(u""+ icons_path +"import.png", QSize(), QIcon.Normal, QIcon.Off)
        self.button_import.setIcon(icon3)
        self.button_import.setIconSize(QSize(18, 18))

        self.horizontalLayout.addWidget(self.button_import)

        self.button_edit = QToolButton(self.w_controls)
        self.button_edit.setObjectName(u"button_edit")
        self.button_edit.setMinimumSize(QSize(25, 25))
        self.button_edit.setMaximumSize(QSize(25, 25))
        icon4 = QIcon()
        icon4.addFile(u""+ icons_path +"pencil_bw.png", QSize(), QIcon.Normal, QIcon.Off)
        self.button_edit.setIcon(icon4)
        self.button_edit.setIconSize(QSize(18, 18))

        self.horizontalLayout.addWidget(self.button_edit)

        self.button_undo = QToolButton(self.w_controls)
        self.button_undo.setObjectName(u"button_undo")
        self.button_undo.setMinimumSize(QSize(25, 25))
        self.button_undo.setMaximumSize(QSize(25, 25))
        icon5 = QIcon()
        icon5.addFile(u""+ icons_path +"undo.png", QSize(), QIcon.Normal, QIcon.Off)
        self.button_undo.setIcon(icon5)
        self.button_undo.setIconSize(QSize(20, 20))
        self.button_undo.setArrowType(Qt.NoArrow)

        self.horizontalLayout.addWidget(self.button_undo)

        self.button_restore = QToolButton(self.w_controls)
        self.button_restore.setObjectName(u"button_restore")
        self.button_restore.setMinimumSize(QSize(25, 25))
        self.button_restore.setMaximumSize(QSize(25, 25))
        icon6 = QIcon()
        icon6.addFile(u""+ icons_path +"restore.png", QSize(), QIcon.Normal, QIcon.Off)
        self.button_restore.setIcon(icon6)
        self.button_restore.setIconSize(QSize(20, 20))

        self.horizontalLayout.addWidget(self.button_restore)

        self.button_delete = QToolButton(self.w_controls)
        self.button_delete.setObjectName(u"button_delete")
        self.button_delete.setMinimumSize(QSize(25, 25))
        self.button_delete.setMaximumSize(QSize(25, 25))
        icon7 = QIcon()
        icon7.addFile(u""+ icons_path +"delete.png", QSize(), QIcon.Normal, QIcon.Off)
        self.button_delete.setIcon(icon7)
        self.button_delete.setIconSize(QSize(20, 20))

        self.horizontalLayout.addWidget(self.button_delete)


        self.verticalLayout.addWidget(self.w_controls)

        self.tree = myQTreeWidget(Custom_Top)
        __qtreewidgetitem = QTreeWidgetItem(self.tree)
        __qtreewidgetitem.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEditable|Qt.ItemIsDragEnabled|Qt.ItemIsDropEnabled|Qt.ItemIsUserCheckable|Qt.ItemIsEnabled);
        __qtreewidgetitem1 = QTreeWidgetItem(self.tree)
        __qtreewidgetitem1.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEditable|Qt.ItemIsDragEnabled|Qt.ItemIsDropEnabled|Qt.ItemIsUserCheckable|Qt.ItemIsEnabled);
        self.tree.setObjectName(u"tree")
        self.tree.setStyleSheet(u"QTreeView::item:selected {\n"
"    border: 1px solid blue;\n"
"    background-color: rgb(214, 226, 255);\n"
"    color: black\n"
"}\n"
"QTreeView::item:!selected:focus{\n"
"    border: none;\n"
"    background-color: rgba(214, 226, 255, 33);\n"
"    color: black\n"
"}\n"
"")
        self.tree.setEditTriggers(QAbstractItemView.DoubleClicked|QAbstractItemView.EditKeyPressed)
        self.tree.setDragEnabled(True)
        self.tree.setDragDropMode(QAbstractItemView.InternalMove)
        self.tree.setDefaultDropAction(Qt.MoveAction)
        self.tree.setAlternatingRowColors(True)
        self.tree.setIndentation(10)
        self.tree.setUniformRowHeights(True)
        self.tree.setItemsExpandable(False)
        self.tree.setSortingEnabled(False)
        self.tree.setHeaderHidden(True)
        self.tree.setColumnCount(1)

        self.verticalLayout.addWidget(self.tree)

        self.w_buttons = QWidget(Custom_Top)
        self.w_buttons.setObjectName(u"w_buttons")
        self.horizontalLayout_2 = QHBoxLayout(self.w_buttons)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.hs_2 = QSpacerItem(172, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.hs_2)

        self.button_cancel = QPushButton(self.w_buttons)
        self.button_cancel.setObjectName(u"button_cancel")

        self.horizontalLayout_2.addWidget(self.button_cancel)

        self.button_done = QPushButton(self.w_buttons)
        self.button_done.setObjectName(u"button_done")

        self.horizontalLayout_2.addWidget(self.button_done)


        self.verticalLayout.addWidget(self.w_buttons)

        QWidget.setTabOrder(self.tree, self.button_down)
        QWidget.setTabOrder(self.button_down, self.button_up)
        QWidget.setTabOrder(self.button_up, self.button_import)
        QWidget.setTabOrder(self.button_import, self.button_edit)
        QWidget.setTabOrder(self.button_edit, self.button_undo)
        QWidget.setTabOrder(self.button_undo, self.button_restore)
        QWidget.setTabOrder(self.button_restore, self.button_delete)
        QWidget.setTabOrder(self.button_delete, self.button_done)
        QWidget.setTabOrder(self.button_done, self.button_cancel)

        self.retranslateUi(Custom_Top)

        QMetaObject.connectSlotsByName(Custom_Top)
    # setupUi

    def retranslateUi(self, Custom_Top):
        Custom_Top.setWindowTitle(QCoreApplication.translate("Custom_Top", u"Custom types of process", None))
#if QT_CONFIG(tooltip)
        self.label_tree.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.label_tree.setText(QCoreApplication.translate("Custom_Top", u"Available processes", None))
#if QT_CONFIG(tooltip)
        self.button_down.setToolTip(QCoreApplication.translate("Custom_Top", u"Move item down in the list", None))
#endif // QT_CONFIG(tooltip)
        self.button_down.setText("")
#if QT_CONFIG(shortcut)
        self.button_down.setShortcut(QCoreApplication.translate("Custom_Top", u"Ctrl+Down", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(tooltip)
        self.button_up.setToolTip(QCoreApplication.translate("Custom_Top", u"Move item up in the list", None))
#endif // QT_CONFIG(tooltip)
        self.button_up.setText("")
#if QT_CONFIG(shortcut)
        self.button_up.setShortcut(QCoreApplication.translate("Custom_Top", u"Ctrl+Up", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(tooltip)
        self.button_import.setToolTip(QCoreApplication.translate("Custom_Top", u"Import process file from disk", None))
#endif // QT_CONFIG(tooltip)
        self.button_import.setText("")
#if QT_CONFIG(shortcut)
        self.button_import.setShortcut(QCoreApplication.translate("Custom_Top", u"Ctrl+D", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(tooltip)
        self.button_edit.setToolTip(QCoreApplication.translate("Custom_Top", u"Edit item", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(shortcut)
        self.button_edit.setShortcut(QCoreApplication.translate("Custom_Top", u"F2", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(tooltip)
        self.button_undo.setToolTip(QCoreApplication.translate("Custom_Top", u"Discard changes for item", None))
#endif // QT_CONFIG(tooltip)
        self.button_undo.setText("")
#if QT_CONFIG(shortcut)
        self.button_undo.setShortcut(QCoreApplication.translate("Custom_Top", u"Ctrl+Z", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(tooltip)
        self.button_restore.setToolTip(QCoreApplication.translate("Custom_Top", u"Restore item", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(shortcut)
        self.button_restore.setShortcut(QCoreApplication.translate("Custom_Top", u"Ctrl+R", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(tooltip)
        self.button_delete.setToolTip(QCoreApplication.translate("Custom_Top", u"Delete item", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(shortcut)
        self.button_delete.setShortcut(QCoreApplication.translate("Custom_Top", u"Backspace", None))
#endif // QT_CONFIG(shortcut)
        ___qtreewidgetitem = self.tree.headerItem()
        ___qtreewidgetitem.setText(0, QCoreApplication.translate("Custom_Top", u"Name", None));

        __sortingEnabled = self.tree.isSortingEnabled()
        self.tree.setSortingEnabled(False)
        ___qtreewidgetitem1 = self.tree.topLevelItem(0)
        ___qtreewidgetitem1.setText(0, QCoreApplication.translate("Custom_Top", u"Item 2", None));
        ___qtreewidgetitem2 = self.tree.topLevelItem(1)
        ___qtreewidgetitem2.setText(0, QCoreApplication.translate("Custom_Top", u"Item 1", None));
        self.tree.setSortingEnabled(__sortingEnabled)

#if QT_CONFIG(tooltip)
        self.button_cancel.setToolTip(QCoreApplication.translate("Custom_Top", u"Discard changes", None))
#endif // QT_CONFIG(tooltip)
        self.button_cancel.setText(QCoreApplication.translate("Custom_Top", u"Cancel", None))
#if QT_CONFIG(shortcut)
        self.button_cancel.setShortcut(QCoreApplication.translate("Custom_Top", u"Esc", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(tooltip)
        self.button_done.setToolTip(QCoreApplication.translate("Custom_Top", u"Save changes", None))
#endif // QT_CONFIG(tooltip)
        self.button_done.setText(QCoreApplication.translate("Custom_Top", u"Save", None))
#if QT_CONFIG(shortcut)
        self.button_done.setShortcut(QCoreApplication.translate("Custom_Top", u"Ctrl+S", None))
#endif // QT_CONFIG(shortcut)
    # retranslateUi


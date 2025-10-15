from .addwidgets_ps import icons_path
# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'infoPaIRSWjIuhO.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
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
    QMainWindow, QMenuBar, QScrollArea, QSizePolicy,
    QTabWidget, QVBoxLayout, QWidget)

class Ui_InfoPaiRS(object):
    def setupUi(self, InfoPaiRS):
        if not InfoPaiRS.objectName():
            InfoPaiRS.setObjectName(u"InfoPaiRS")
        InfoPaiRS.resize(700, 650)
        InfoPaiRS.setMinimumSize(QSize(550, 600))
        font = QFont()
        font.setFamilies([u"Arial"])
        InfoPaiRS.setFont(font)
        icon = QIcon()
        icon.addFile(u""+ icons_path +"icon_PaIRS.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        InfoPaiRS.setWindowIcon(icon)
        self.centralwidget = QWidget(InfoPaiRS)
        self.centralwidget.setObjectName(u"centralwidget")
        font1 = QFont()
        font1.setFamilies([u"Arial"])
        font1.setPointSize(10)
        self.centralwidget.setFont(font1)
        self.horizontalLayout = QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setAutoFillBackground(False)
        self.tabWidget.setTabPosition(QTabWidget.TabPosition.North)
        self.tabWidget.setTabShape(QTabWidget.TabShape.Rounded)
        self.tabWidget.setDocumentMode(True)
        self.tabWidget.setTabBarAutoHide(True)
        self.about = QWidget()
        self.about.setObjectName(u"about")
        self.about.setStyleSheet(u"background-color: rgba(255, 255, 255, 0);")
        self.gridLayout_2 = QGridLayout(self.about)
        self.gridLayout_2.setSpacing(10)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(-1, 15, -1, -1)
        self.logo = QLabel(self.about)
        self.logo.setObjectName(u"logo")
        self.logo.setMinimumSize(QSize(250, 250))
        self.logo.setMaximumSize(QSize(250, 250))
#if QT_CONFIG(accessibility)
        self.logo.setAccessibleDescription(u"")
#endif // QT_CONFIG(accessibility)
        self.logo.setPixmap(QPixmap(u""+ icons_path +"logo_PaIRS_completo.png"))
        self.logo.setScaledContents(True)

        self.gridLayout_2.addWidget(self.logo, 0, 0, 1, 1)

        self.info = QLabel(self.about)
        self.info.setObjectName(u"info")
        font2 = QFont()
        font2.setFamilies([u"Arial"])
        font2.setPointSize(14)
        self.info.setFont(font2)
        self.info.setTextFormat(Qt.TextFormat.RichText)
        self.info.setWordWrap(True)
        self.info.setOpenExternalLinks(True)
        self.info.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByKeyboard|Qt.TextInteractionFlag.LinksAccessibleByMouse|Qt.TextInteractionFlag.TextBrowserInteraction|Qt.TextInteractionFlag.TextSelectableByKeyboard|Qt.TextInteractionFlag.TextSelectableByMouse)

        self.gridLayout_2.addWidget(self.info, 0, 1, 1, 1)

        self.unina_dii = QLabel(self.about)
        self.unina_dii.setObjectName(u"unina_dii")
        self.unina_dii.setMaximumSize(QSize(16777215, 90))
        self.unina_dii.setPixmap(QPixmap(u""+ icons_path +"unina_dii.png"))
        self.unina_dii.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_2.addWidget(self.unina_dii, 1, 0, 1, 1)

        self.info_uni = QLabel(self.about)
        self.info_uni.setObjectName(u"info_uni")
        self.info_uni.setTextFormat(Qt.TextFormat.RichText)
        self.info_uni.setWordWrap(True)

        self.gridLayout_2.addWidget(self.info_uni, 1, 1, 1, 1)

        self.tabWidget.addTab(self.about, "")
        self.authors = QWidget()
        self.authors.setObjectName(u"authors")
        self.authors.setStyleSheet(u"background-color: rgba(255, 255, 255, 0);")
        self.gridLayout = QGridLayout(self.authors)
        self.gridLayout.setSpacing(20)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(-1, 15, -1, -1)
        self.tom = QLabel(self.authors)
        self.tom.setObjectName(u"tom")
        self.tom.setMinimumSize(QSize(150, 150))
        self.tom.setMaximumSize(QSize(150, 150))
        self.tom.setPixmap(QPixmap(u""+ icons_path +"tom.png"))
        self.tom.setScaledContents(True)

        self.gridLayout.addWidget(self.tom, 1, 0, 1, 1)

        self.ger = QLabel(self.authors)
        self.ger.setObjectName(u"ger")
        self.ger.setMinimumSize(QSize(150, 150))
        self.ger.setMaximumSize(QSize(150, 150))
        self.ger.setPixmap(QPixmap(u""+ icons_path +"ger.png"))
        self.ger.setScaledContents(True)

        self.gridLayout.addWidget(self.ger, 0, 0, 1, 1)

        self.scrollArea_ger_cv = QScrollArea(self.authors)
        self.scrollArea_ger_cv.setObjectName(u"scrollArea_ger_cv")
        self.scrollArea_ger_cv.setStyleSheet(u" QScrollArea {\n"
"        border: 1pix solid gray;\n"
"    }\n"
"\n"
"QScrollBar:horizontal\n"
"    {\n"
"        height: 15px;\n"
"        margin: 3px 0px 3px 0px;\n"
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
"        border: none;\n"
"      "
                        "  background: none;\n"
"    }\n"
"\n"
"QScrollBar::sub-line {\n"
"        border: none;\n"
"        background: none;\n"
"    }\n"
"")
        self.scrollArea_ger_cv.setWidgetResizable(True)
        self.scrollAreaWidgetContents_ger_cv = QWidget()
        self.scrollAreaWidgetContents_ger_cv.setObjectName(u"scrollAreaWidgetContents_ger_cv")
        self.scrollAreaWidgetContents_ger_cv.setGeometry(QRect(0, 0, 494, 266))
        self.verticalLayout = QVBoxLayout(self.scrollAreaWidgetContents_ger_cv)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.ger_cv = QLabel(self.scrollAreaWidgetContents_ger_cv)
        self.ger_cv.setObjectName(u"ger_cv")
        font3 = QFont()
        font3.setFamilies([u"Arial"])
        font3.setPointSize(11)
        self.ger_cv.setFont(font3)
        self.ger_cv.setTextFormat(Qt.TextFormat.RichText)
        self.ger_cv.setScaledContents(True)
        self.ger_cv.setWordWrap(True)
        self.ger_cv.setMargin(5)
        self.ger_cv.setIndent(-5)

        self.verticalLayout.addWidget(self.ger_cv)

        self.scrollArea_ger_cv.setWidget(self.scrollAreaWidgetContents_ger_cv)

        self.gridLayout.addWidget(self.scrollArea_ger_cv, 0, 1, 1, 1)

        self.scrollArea_tom_cv = QScrollArea(self.authors)
        self.scrollArea_tom_cv.setObjectName(u"scrollArea_tom_cv")
        self.scrollArea_tom_cv.setStyleSheet(u" QScrollArea {\n"
"        border: 1pix solid gray;\n"
"    }\n"
"\n"
"QScrollBar:horizontal\n"
"    {\n"
"        height: 15px;\n"
"        margin: 3px 0px 3px 0px;\n"
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
"        border: none;\n"
"      "
                        "  background: none;\n"
"    }\n"
"\n"
"QScrollBar::sub-line {\n"
"        border: none;\n"
"        background: none;\n"
"    }\n"
"")
        self.scrollArea_tom_cv.setWidgetResizable(True)
        self.scrollAreaWidgetContents_tom_cv = QWidget()
        self.scrollAreaWidgetContents_tom_cv.setObjectName(u"scrollAreaWidgetContents_tom_cv")
        self.scrollAreaWidgetContents_tom_cv.setGeometry(QRect(0, 0, 494, 266))
        self.verticalLayout_2 = QVBoxLayout(self.scrollAreaWidgetContents_tom_cv)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.tom_cv = QLabel(self.scrollAreaWidgetContents_tom_cv)
        self.tom_cv.setObjectName(u"tom_cv")
        self.tom_cv.setFont(font3)
        self.tom_cv.setTextFormat(Qt.TextFormat.RichText)
        self.tom_cv.setWordWrap(True)
        self.tom_cv.setMargin(5)
        self.tom_cv.setIndent(-5)

        self.verticalLayout_2.addWidget(self.tom_cv)

        self.scrollArea_tom_cv.setWidget(self.scrollAreaWidgetContents_tom_cv)

        self.gridLayout.addWidget(self.scrollArea_tom_cv, 1, 1, 1, 1)

        self.tabWidget.addTab(self.authors, "")
        self.references = QWidget()
        self.references.setObjectName(u"references")
        self.references.setStyleSheet(u"background-color: rgba(255, 255, 255, 0);")
        self.horizontalLayout_2 = QHBoxLayout(self.references)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(-1, 15, -1, -1)
        self.scrollArea_list_ref = QScrollArea(self.references)
        self.scrollArea_list_ref.setObjectName(u"scrollArea_list_ref")
        self.scrollArea_list_ref.setStyleSheet(u" QScrollArea {\n"
"        border: 1pix solid gray;\n"
"    }\n"
"\n"
"QScrollBar:horizontal\n"
"    {\n"
"        height: 15px;\n"
"        margin: 3px 0px 3px 0px;\n"
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
"        border: none;\n"
"      "
                        "  background: none;\n"
"    }\n"
"\n"
"QScrollBar::sub-line {\n"
"        border: none;\n"
"        background: none;\n"
"    }\n"
"")
        self.scrollArea_list_ref.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 649, 582))
        self.scrollAreaWidgetContents.setStyleSheet(u"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
"<ui version=\"4.0\">\n"
" <widget name=\"__qt_fake_top_level\">\n"
"  <widget class=\"QLabel\" name=\"list_ref\">\n"
"   <property name=\"geometry\">\n"
"    <rect>\n"
"     <x>20</x>\n"
"     <y>12</y>\n"
"     <width>636</width>\n"
"     <height>433</height>\n"
"    </rect>\n"
"   </property>\n"
"   <property name=\"text\">\n"
"    <string>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p align=&quot;justify&quot;&gt;&lt;span style=&quot; font-size:11pt;&quot;&gt;Please cite the following works if you intend to use PaIRS-UniNa for your purposes: &lt;/span&gt;&lt;/p&gt;&lt;p align=&quot;justify&quot;&gt;&lt;span style=&quot; font-size:11pt; font-weight:700;&quot;&gt;[1] &lt;/span&gt;&lt;span style=&quot; font-size:11pt;&quot;&gt;Astarita, T., &amp;amp; Cardone, G. (2005). &amp;quot;Analysis of interpolation schemes for image deformation methods in PIV&amp;quot;. &lt;/span&gt;&lt;span style=&quot; font-size:11pt; font-style:italic;&quot;&gt;Experiments in Fluids&lt;/span"
                        "&gt;&lt;span style=&quot; font-size:11pt;&quot;&gt;, 38(2), 233-243.doi: &lt;/span&gt;&lt;a href=&quot;https://doi.org/10.1007/s00348-004-0902-3&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0000ff;&quot;&gt;10.1007/s00348-004-0902-3&lt;/span&gt;&lt;/a&gt;&lt;span style=&quot; font-size:11pt;&quot;&gt;. &lt;/span&gt;&lt;/p&gt;&lt;p align=&quot;justify&quot;&gt;&lt;span style=&quot; font-size:11pt; font-weight:700;&quot;&gt;[2] &lt;/span&gt;&lt;span style=&quot; font-size:11pt;&quot;&gt;Astarita, T. (2006). &amp;quot;Analysis of interpolation schemes for image deformation methods in PIV: effect of noise on the accuracy and spatial resolution&amp;quot;. &lt;/span&gt;&lt;span style=&quot; font-size:11pt; font-style:italic;&quot;&gt;Experiments in Fluids&lt;/span&gt;&lt;span style=&quot; font-size:11pt;&quot;&gt;, vol. 40 (6): 977-987. doi: &lt;/span&gt;&lt;a href=&quot;https://doi.org/10.1007/s00348-006-0139-4&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0000ff;&quot;&gt;1"
                        "0.1007/s00348-006-0139-4&lt;/span&gt;&lt;/a&gt;&lt;span style=&quot; font-size:11pt;&quot;&gt;. &lt;/span&gt;&lt;/p&gt;&lt;p align=&quot;justify&quot;&gt;&lt;span style=&quot; font-size:11pt; font-weight:700;&quot;&gt;[3] &lt;/span&gt;&lt;span style=&quot; font-size:11pt;&quot;&gt;Astarita, T. (2007). &amp;quot;Analysis of weighting windows for image deformation methods in PIV.&amp;quot; &lt;/span&gt;&lt;span style=&quot; font-size:11pt; font-style:italic;&quot;&gt;Experiments in Fluids&lt;/span&gt;&lt;span style=&quot; font-size:11pt;&quot;&gt;, 43(6), 859-872. doi: &lt;/span&gt;&lt;a href=&quot;https://doi.org/10.1007/s00348-007-0314-2&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0000ff;&quot;&gt;10.1007/s00348-007-0314-2&lt;/span&gt;&lt;/a&gt;&lt;span style=&quot; font-size:11pt;&quot;&gt;. &lt;/span&gt;&lt;/p&gt;&lt;p align=&quot;justify&quot;&gt;&lt;span style=&quot; font-size:11pt; font-weight:700;&quot;&gt;[4]&lt;/span&gt;&lt;span style=&quot; font-size:11pt;&quot;&gt; Astarita, T. "
                        "(2008). &amp;quot;Analysis of velocity interpolation schemes for image deformation methods in PIV&amp;quot;. &lt;/span&gt;&lt;span style=&quot; font-size:11pt; font-style:italic;&quot;&gt;Experiments in Fluids&lt;/span&gt;&lt;span style=&quot; font-size:11pt;&quot;&gt;, 45(2), 257-266. doi: &lt;/span&gt;&lt;a href=&quot;https://doi.org/10.1007/s00348-008-0475-7&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0000ff;&quot;&gt;10.1007/s00348-008-0475-7&lt;/span&gt;&lt;/a&gt;&lt;span style=&quot; font-size:11pt;&quot;&gt;. &lt;/span&gt;&lt;/p&gt;&lt;p align=&quot;justify&quot;&gt;&lt;span style=&quot; font-size:11pt; font-weight:700;&quot;&gt;[5] &lt;/span&gt;&lt;span style=&quot; font-size:11pt;&quot;&gt;Astarita, T. (2009). &amp;quot;Adaptive space resolution for PIV&amp;quot;. &lt;/span&gt;&lt;span style=&quot; font-size:11pt; font-style:italic;&quot;&gt;Experiments in Fluids&lt;/span&gt;&lt;span style=&quot; font-size:11pt;&quot;&gt;, 46(6), 1115-1123. doi: &lt;/span&gt;&lt;a href=&quot;http"
                        "s://doi.org/10.1007/s00348-009-0618-5&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0000ff;&quot;&gt;10.1007/s00348-009-0618-5&lt;/span&gt;&lt;/a&gt;&lt;span style=&quot; font-size:11pt;&quot;&gt;. &lt;/span&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</string>\n"
"   </property>\n"
"   <property name=\"textFormat\">\n"
"    <enum>Qt::RichText</enum>\n"
"   </property>\n"
"   <property name=\"alignment\">\n"
"    <set>Qt::AlignLeading|Qt::AlignLeft|Qt::AlignTop</set>\n"
"   </property>\n"
"   <property name=\"wordWrap\">\n"
"    <bool>true</bool>\n"
"   </property>\n"
"   <property name=\"margin\">\n"
"    <number>5</number>\n"
"   </property>\n"
"   <property name=\"openExternalLinks\">\n"
"    <bool>true</bool>\n"
"   </property>\n"
"   <property name=\"textInteractionFlags\">\n"
"    <set>Qt::LinksAccessibleByKeyboard|Qt::LinksAccessibleByMouse|Qt::TextBrowserInteraction|Qt::TextSelectableByKeyboard|Qt::TextSelectableByMouse</set>\n"
"   </property>\n"
"  </widget>\n"
" </widget>\n"
" <resour"
                        "ces/>\n"
"</ui>\n"
"")
        self.verticalLayout_3 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.list_ref = QLabel(self.scrollAreaWidgetContents)
        self.list_ref.setObjectName(u"list_ref")
        self.list_ref.setTextFormat(Qt.TextFormat.RichText)
        self.list_ref.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.list_ref.setWordWrap(True)
        self.list_ref.setMargin(5)
        self.list_ref.setOpenExternalLinks(True)
        self.list_ref.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByKeyboard|Qt.TextInteractionFlag.LinksAccessibleByMouse|Qt.TextInteractionFlag.TextBrowserInteraction|Qt.TextInteractionFlag.TextSelectableByKeyboard|Qt.TextInteractionFlag.TextSelectableByMouse)

        self.verticalLayout_3.addWidget(self.list_ref)

        self.scrollArea_list_ref.setWidget(self.scrollAreaWidgetContents)

        self.horizontalLayout_2.addWidget(self.scrollArea_list_ref)

        self.tabWidget.addTab(self.references, "")
        self.requirements = QWidget()
        self.requirements.setObjectName(u"requirements")
        self.horizontalLayout_3 = QHBoxLayout(self.requirements)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.scrollArea_req = QScrollArea(self.requirements)
        self.scrollArea_req.setObjectName(u"scrollArea_req")
        self.scrollArea_req.setStyleSheet(u" QScrollArea {\n"
"        border: 1pix solid gray;\n"
"    }\n"
"\n"
"QScrollBar:horizontal\n"
"    {\n"
"        height: 15px;\n"
"        margin: 3px 0px 3px 0px;\n"
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
"        border: none;\n"
"      "
                        "  background: none;\n"
"    }\n"
"\n"
"QScrollBar::sub-line {\n"
"        border: none;\n"
"        background: none;\n"
"    }\n"
"")
        self.scrollArea_req.setWidgetResizable(True)
        self.scrollAreaWidgetContents_2 = QWidget()
        self.scrollAreaWidgetContents_2.setObjectName(u"scrollAreaWidgetContents_2")
        self.scrollAreaWidgetContents_2.setGeometry(QRect(0, 0, 664, 558))
        self.scrollAreaWidgetContents_2.setStyleSheet(u"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
"<ui version=\"4.0\">\n"
" <widget name=\"__qt_fake_top_level\">\n"
"  <widget class=\"QLabel\" name=\"list_ref\">\n"
"   <property name=\"geometry\">\n"
"    <rect>\n"
"     <x>20</x>\n"
"     <y>12</y>\n"
"     <width>636</width>\n"
"     <height>433</height>\n"
"    </rect>\n"
"   </property>\n"
"   <property name=\"text\">\n"
"    <string>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p align=&quot;justify&quot;&gt;&lt;span style=&quot; font-size:11pt;&quot;&gt;Please cite the following works if you intend to use PaIRS-UniNa for your purposes: &lt;/span&gt;&lt;/p&gt;&lt;p align=&quot;justify&quot;&gt;&lt;span style=&quot; font-size:11pt; font-weight:700;&quot;&gt;[1] &lt;/span&gt;&lt;span style=&quot; font-size:11pt;&quot;&gt;Astarita, T., &amp;amp; Cardone, G. (2005). &amp;quot;Analysis of interpolation schemes for image deformation methods in PIV&amp;quot;. &lt;/span&gt;&lt;span style=&quot; font-size:11pt; font-style:italic;&quot;&gt;Experiments in Fluids&lt;/span"
                        "&gt;&lt;span style=&quot; font-size:11pt;&quot;&gt;, 38(2), 233-243.doi: &lt;/span&gt;&lt;a href=&quot;https://doi.org/10.1007/s00348-004-0902-3&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0000ff;&quot;&gt;10.1007/s00348-004-0902-3&lt;/span&gt;&lt;/a&gt;&lt;span style=&quot; font-size:11pt;&quot;&gt;. &lt;/span&gt;&lt;/p&gt;&lt;p align=&quot;justify&quot;&gt;&lt;span style=&quot; font-size:11pt; font-weight:700;&quot;&gt;[2] &lt;/span&gt;&lt;span style=&quot; font-size:11pt;&quot;&gt;Astarita, T. (2006). &amp;quot;Analysis of interpolation schemes for image deformation methods in PIV: effect of noise on the accuracy and spatial resolution&amp;quot;. &lt;/span&gt;&lt;span style=&quot; font-size:11pt; font-style:italic;&quot;&gt;Experiments in Fluids&lt;/span&gt;&lt;span style=&quot; font-size:11pt;&quot;&gt;, vol. 40 (6): 977-987. doi: &lt;/span&gt;&lt;a href=&quot;https://doi.org/10.1007/s00348-006-0139-4&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0000ff;&quot;&gt;1"
                        "0.1007/s00348-006-0139-4&lt;/span&gt;&lt;/a&gt;&lt;span style=&quot; font-size:11pt;&quot;&gt;. &lt;/span&gt;&lt;/p&gt;&lt;p align=&quot;justify&quot;&gt;&lt;span style=&quot; font-size:11pt; font-weight:700;&quot;&gt;[3] &lt;/span&gt;&lt;span style=&quot; font-size:11pt;&quot;&gt;Astarita, T. (2007). &amp;quot;Analysis of weighting windows for image deformation methods in PIV.&amp;quot; &lt;/span&gt;&lt;span style=&quot; font-size:11pt; font-style:italic;&quot;&gt;Experiments in Fluids&lt;/span&gt;&lt;span style=&quot; font-size:11pt;&quot;&gt;, 43(6), 859-872. doi: &lt;/span&gt;&lt;a href=&quot;https://doi.org/10.1007/s00348-007-0314-2&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0000ff;&quot;&gt;10.1007/s00348-007-0314-2&lt;/span&gt;&lt;/a&gt;&lt;span style=&quot; font-size:11pt;&quot;&gt;. &lt;/span&gt;&lt;/p&gt;&lt;p align=&quot;justify&quot;&gt;&lt;span style=&quot; font-size:11pt; font-weight:700;&quot;&gt;[4]&lt;/span&gt;&lt;span style=&quot; font-size:11pt;&quot;&gt; Astarita, T. "
                        "(2008). &amp;quot;Analysis of velocity interpolation schemes for image deformation methods in PIV&amp;quot;. &lt;/span&gt;&lt;span style=&quot; font-size:11pt; font-style:italic;&quot;&gt;Experiments in Fluids&lt;/span&gt;&lt;span style=&quot; font-size:11pt;&quot;&gt;, 45(2), 257-266. doi: &lt;/span&gt;&lt;a href=&quot;https://doi.org/10.1007/s00348-008-0475-7&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0000ff;&quot;&gt;10.1007/s00348-008-0475-7&lt;/span&gt;&lt;/a&gt;&lt;span style=&quot; font-size:11pt;&quot;&gt;. &lt;/span&gt;&lt;/p&gt;&lt;p align=&quot;justify&quot;&gt;&lt;span style=&quot; font-size:11pt; font-weight:700;&quot;&gt;[5] &lt;/span&gt;&lt;span style=&quot; font-size:11pt;&quot;&gt;Astarita, T. (2009). &amp;quot;Adaptive space resolution for PIV&amp;quot;. &lt;/span&gt;&lt;span style=&quot; font-size:11pt; font-style:italic;&quot;&gt;Experiments in Fluids&lt;/span&gt;&lt;span style=&quot; font-size:11pt;&quot;&gt;, 46(6), 1115-1123. doi: &lt;/span&gt;&lt;a href=&quot;http"
                        "s://doi.org/10.1007/s00348-009-0618-5&quot;&gt;&lt;span style=&quot; text-decoration: underline; color:#0000ff;&quot;&gt;10.1007/s00348-009-0618-5&lt;/span&gt;&lt;/a&gt;&lt;span style=&quot; font-size:11pt;&quot;&gt;. &lt;/span&gt;&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</string>\n"
"   </property>\n"
"   <property name=\"textFormat\">\n"
"    <enum>Qt::RichText</enum>\n"
"   </property>\n"
"   <property name=\"alignment\">\n"
"    <set>Qt::AlignLeading|Qt::AlignLeft|Qt::AlignTop</set>\n"
"   </property>\n"
"   <property name=\"wordWrap\">\n"
"    <bool>true</bool>\n"
"   </property>\n"
"   <property name=\"margin\">\n"
"    <number>5</number>\n"
"   </property>\n"
"   <property name=\"openExternalLinks\">\n"
"    <bool>true</bool>\n"
"   </property>\n"
"   <property name=\"textInteractionFlags\">\n"
"    <set>Qt::LinksAccessibleByKeyboard|Qt::LinksAccessibleByMouse|Qt::TextBrowserInteraction|Qt::TextSelectableByKeyboard|Qt::TextSelectableByMouse</set>\n"
"   </property>\n"
"  </widget>\n"
" </widget>\n"
" <resour"
                        "ces/>\n"
"</ui>\n"
"")
        self.horizontalLayout_4 = QHBoxLayout(self.scrollAreaWidgetContents_2)
        self.horizontalLayout_4.setSpacing(0)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.req = QLabel(self.scrollAreaWidgetContents_2)
        self.req.setObjectName(u"req")
        self.req.setTextFormat(Qt.TextFormat.RichText)
        self.req.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.req.setWordWrap(True)
        self.req.setMargin(5)
        self.req.setOpenExternalLinks(True)
        self.req.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByKeyboard|Qt.TextInteractionFlag.LinksAccessibleByMouse|Qt.TextInteractionFlag.TextBrowserInteraction|Qt.TextInteractionFlag.TextSelectableByKeyboard|Qt.TextInteractionFlag.TextSelectableByMouse)

        self.horizontalLayout_4.addWidget(self.req)

        self.scrollArea_req.setWidget(self.scrollAreaWidgetContents_2)

        self.horizontalLayout_3.addWidget(self.scrollArea_req)

        self.tabWidget.addTab(self.requirements, "")

        self.horizontalLayout.addWidget(self.tabWidget)

        InfoPaiRS.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(InfoPaiRS)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 700, 33))
        InfoPaiRS.setMenuBar(self.menubar)

        self.retranslateUi(InfoPaiRS)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(InfoPaiRS)
    # setupUi

    def retranslateUi(self, InfoPaiRS):
        InfoPaiRS.setWindowTitle(QCoreApplication.translate("InfoPaiRS", u"About PaIRS", None))
        self.logo.setText("")
        self.info.setText(QCoreApplication.translate("InfoPaiRS", u"<html><head/><body><p><span style=\" font-size:18pt; font-weight:700;\">PaIRS - version: #.#.#</span></p><p><span style=\" font-size:16pt; font-weight:700;\">Pa</span><span style=\" font-size:16pt;\">rticle </span><span style=\" font-size:16pt; font-weight:700;\">I</span><span style=\" font-size:16pt;\">mage </span><span style=\" font-size:16pt; font-weight:700;\">R</span><span style=\" font-size:16pt;\">econstruction </span><span style=\" font-size:16pt; font-weight:700;\">S</span><span style=\" font-size:16pt;\">oftware</span></p><p><span style=\" font-size:16pt;\">\u00a9 yyyy Gerardo Paolillo &amp; Tommaso Astarita. All rights reserved. </span></p><p>date: dddd/dd/dd</p><p><span style=\" font-size:16pt;\">email: </span>mmmm</p><p>website: wwww</p><p><br/></p></body></html>", None))
        self.unina_dii.setText("")
        self.info_uni.setText(QCoreApplication.translate("InfoPaiRS", u"<html><head/><body><p><span style=\" font-size:12pt;\">Experimental Thermo-Fluid Dynamics (ETFD) group, Department of Industrial Engineering (DII)</span></p><p><span style=\" font-size:12pt;\">University of Naples &quot;Federico II&quot;, Naples, Italy</span></p></body></html>", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.about), QCoreApplication.translate("InfoPaiRS", u"About PaIRS", None))
        self.tom.setText("")
        self.ger.setText("")
        self.ger_cv.setText(QCoreApplication.translate("InfoPaiRS", u"<html><head/><body><p align=\"justify\"><span style=\" font-weight:700;\">Gerardo Paolillo</span><span style=\" font-size:10pt;\"> received a Master's degree in Aerospace Engineering and a PhD degree in Industrial Engineering from Universit\u00e0 di Napoli &quot;Federico II&quot; in 2015 and 2018, respectively. </span></p><p align=\"justify\"><span style=\" font-size:10pt;\">He is currently a Research Associate in the Department of Industrial Engineering at Universit\u00e0 di Napoli &quot;Federico II&quot;.</span></p><p align=\"justify\"><span style=\" font-size:10pt;\">His research interests lie in the area of experimental fluid mechanics, with focus on applications of unsteady jets to flow control and electronics cooling, investigation into dynamics of turbulent Rayleigh-B\u00e8nard convection and development of 3D optical velocimetry techniques.</span></p></body></html>", None))
        self.tom_cv.setText(QCoreApplication.translate("InfoPaiRS", u"<html><head/><body><p align=\"justify\"><span style=\" font-weight:700;\">Tommaso Astarita</span><span style=\" font-size:10pt;\"> received a Master's degree in Aeronautical Engineering in 1993 and a PhD degree in Aerospace Engineering in 1997, both from Universit\u00e0 di Napoli &quot;Federico II&quot;. </span></p><p align=\"justify\"><span style=\" font-size:10pt;\">He was Post-doc at the von K\u00e0rm\u00e0n Institute for Fluid Dynamics and he is currently full Professor of Fluid Mechanics at Universit\u00e0 di Napoli &quot;Federico II&quot;. </span></p><p align=\"justify\"><span style=\" font-size:10pt;\">His main research interests are dedicated to the experimental study of problems in the fields of fluid mechanics and convective heat transfer, in particular, the application and development of IR thermography and stereoscopic and tomographic PIV techniques for fluid mechanics problems.</span></p></body></html>", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.authors), QCoreApplication.translate("InfoPaiRS", u"Authors", None))
        self.list_ref.setText(QCoreApplication.translate("InfoPaiRS", u"<html><head/><body><p align=\"justify\"><span style=\" font-size:11pt;\">Please cite the following works if you intend to use PaIRS-UniNa for your purposes: </span></p><p align=\"justify\"><span style=\" font-size:11pt; font-weight:700;\">[1] </span><span style=\" font-size:11pt;\">Astarita, T., &amp; Cardone, G. (2005). &quot;Analysis of interpolation schemes for image deformation methods in PIV&quot;. </span><span style=\" font-size:11pt; font-style:italic;\">Experiments in Fluids</span><span style=\" font-size:11pt;\">, 38(2), 233-243.doi: </span><a href=\"https://doi.org/10.1007/s00348-004-0902-3\"><span style=\" text-decoration: underline; color:#0000ff;\">10.1007/s00348-004-0902-3</span></a><span style=\" font-size:11pt;\">. </span></p><p align=\"justify\"><span style=\" font-size:11pt; font-weight:700;\">[2] </span><span style=\" font-size:11pt;\">Astarita, T. (2006). &quot;Analysis of interpolation schemes for image deformation methods in PIV: effect of noise on the accuracy and spatial resolution&quot"
                        ";. </span><span style=\" font-size:11pt; font-style:italic;\">Experiments in Fluids</span><span style=\" font-size:11pt;\">, vol. 40 (6): 977-987. doi: </span><a href=\"https://doi.org/10.1007/s00348-006-0139-4\"><span style=\" text-decoration: underline; color:#0000ff;\">10.1007/s00348-006-0139-4</span></a><span style=\" font-size:11pt;\">. </span></p><p align=\"justify\"><span style=\" font-size:11pt; font-weight:700;\">[3] </span><span style=\" font-size:11pt;\">Astarita, T. (2007). &quot;Analysis of weighting windows for image deformation methods in PIV.&quot; </span><span style=\" font-size:11pt; font-style:italic;\">Experiments in Fluids</span><span style=\" font-size:11pt;\">, 43(6), 859-872. doi: </span><a href=\"https://doi.org/10.1007/s00348-007-0314-2\"><span style=\" text-decoration: underline; color:#0000ff;\">10.1007/s00348-007-0314-2</span></a><span style=\" font-size:11pt;\">. </span></p><p align=\"justify\"><span style=\" font-size:11pt; font-weight:700;\">[4]</span><span style=\" font-size:11"
                        "pt;\"> Astarita, T. (2008). &quot;Analysis of velocity interpolation schemes for image deformation methods in PIV&quot;. </span><span style=\" font-size:11pt; font-style:italic;\">Experiments in Fluids</span><span style=\" font-size:11pt;\">, 45(2), 257-266. doi: </span><a href=\"https://doi.org/10.1007/s00348-008-0475-7\"><span style=\" text-decoration: underline; color:#0000ff;\">10.1007/s00348-008-0475-7</span></a><span style=\" font-size:11pt;\">. </span></p><p align=\"justify\"><span style=\" font-size:11pt; font-weight:700;\">[5] </span><span style=\" font-size:11pt;\">Astarita, T. (2009). &quot;Adaptive space resolution for PIV&quot;. </span><span style=\" font-size:11pt; font-style:italic;\">Experiments in Fluids</span><span style=\" font-size:11pt;\">, 46(6), 1115-1123. doi: </span><a href=\"https://doi.org/10.1007/s00348-009-0618-5\"><span style=\" text-decoration: underline; color:#0000ff;\">10.1007/s00348-009-0618-5</span></a><span style=\" font-size:11pt;\">. </span></p><p align=\"justify\"><span "
                        "style=\" font-size:11pt; font-weight:700;\">[6] </span><span style=\" font-size:11pt;\">Giordano, R., &amp; Astarita, T. (2009). &quot;Spatial resolution of the Stereo PIV technique&quot;. </span><span style=\" font-size:11pt; font-style:italic;\">Experiments in Fluids</span><span style=\" font-size:11pt;\">, 46(4), 643.658. doi: </span><a href=\"https://doi.org/10.1007/s00348-008-0589-y\"><span style=\" text-decoration: underline; color:#0000ff;\">10.1007/s00348-008-0589-y</span></a><span style=\" font-size:11pt;\">. <br/></span></p><p align=\"justify\"><span style=\" font-size:11pt;\"><br/>Please cite the following works if you intend to use CalVi for your purposes:</span></p><p align=\"justify\"><span style=\" font-size:11pt; font-weight:700;\">[1] </span><span style=\" font-size:11pt;\">Paolillo, G., &amp; Astarita, T. (2020). &quot;Perspective camera model with refraction correction for optical velocimetry measurements in complex geometries&quot;. </span><span style=\" font-size:11pt; font-style:italic;\""
                        ">IEEE Transactions on Pattern Analysis and Machine Intelligence, </span><span style=\" font-size:11pt;\">44(6), 3185-3196</span><span style=\" font-size:11pt; font-weight:700;\">.</span><span style=\" font-size:11pt;\"> doi: </span><a href=\"https://doi.org/10.1109/TPAMI.2020.3046467\"><span style=\" text-decoration: underline; color:#0000ff;\">10.1109/TPAMI.2020.3046467</span></a><span style=\" font-size:11pt;\">. <br/><br/></span><span style=\" font-size:11pt; font-weight:700;\">[2] </span><span style=\" font-size:11pt;\">Paolillo, G., &amp; Astarita, T. (2021). &quot;On the PIV/PTV uncertainty related to calibration of camera systems with refractive surfaces&quot;. </span><span style=\" font-size:11pt; font-style:italic;\">Measurement Science and Technology</span><span style=\" font-size:11pt;\">, 32(9), 094006. doi: </span><a href=\"https://doi.org/10.1088/1361-6501/abf3fc\"><span style=\" text-decoration: underline; color:#0000ff;\">10.1088/1361-6501/abf3fc</span></a><span style=\" font-size:11pt;\">. </s"
                        "pan></p></body></html>", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.references), QCoreApplication.translate("InfoPaiRS", u"References", None))
        self.req.setText(QCoreApplication.translate("InfoPaiRS", u"<html><head/><body><p align=\"justify\"><br/></p></body></html>", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.requirements), QCoreApplication.translate("InfoPaiRS", u"Requirements", None))
    # retranslateUi


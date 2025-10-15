from .PaIRS_pypacks import *
#from ui_Tree_Tab import Ui_TreeTab

QLocale.setDefault(QLocale.Language.English)
curr_locale = QLocale()

InitCheck=True   #False=Collap closed, True=opened
#fonts
font_italic=True
font_weight=QFont.DemiBold
backgroundcolor_none=" background-color: none;"
backgroundcolor_changing=" background-color: rgb(255,230,230);"
color_changing="color: rgb(33,33,255); "+backgroundcolor_changing
color_changing_black="color: rgb(0,0,0); "+backgroundcolor_changing

#********************************************* Operating Widgets
def setSS(b,style):
    ss=f"{b.metaObject().className()}{'{'+style+'}'}\\nQToolTip{'{'+b.initialStyle+'}'}"
    return ss

class MyTabLabel(QLabel):
    def __init__(self,parent):
        super().__init__(parent)
        #self.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.addfuncclick={}

    def mousePressEvent(self, event):
        for f in self.addfuncclick:
             self.addfuncclick[f]()
        return super().mousePressEvent(event)
    
    def setCustomCursor(self):
        if self.addfuncclick:
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        else:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

#MyQLineEdit=QtWidgets.QLineEdit
class MyQLineEdit(QtWidgets.QLineEdit):
    def __init__(self,parent):
        super().__init__(parent)
        self.addlab=QtWidgets.QLabel()
        self.addwid=[]
        self.initFlag=False
        self.initFlag2=False
        self.styleFlag=False
        self.addfuncin={}
        self.addfuncout={}
        self.addfuncreturn={}
        self.FlagCompleter=False
        self.FunSetCompleterList=lambda: None

    def setup(self):
        if not self.initFlag:
            self.initFlag=True
            font_changing = QtGui.QFont(self.font())
            font_changing.setItalic(font_italic)
            font_changing.setWeight(font_weight)
            children=self.parent().children()
            self.bros=children+self.addwid
            for b in self.bros:
                hasStyleFlag=hasattr(b,'styleFlag')
                if hasattr(b,'setStyleSheet'):
                    if hasStyleFlag:
                        if b.styleFlag: continue
                    b.flagS=True
                    b.initialStyle=b.styleSheet()+" "+backgroundcolor_none
                    b.setEnabled(False)
                    b.disabledStyle=b.styleSheet()
                    b.setEnabled(True)
                    b.setStyleSheet(setSS(b,b.initialStyle))
                else:
                    b.flagS=False
                if hasattr(b,'setFont'):
                    b.flagF=True
                    b.initialFont=b.font()
                    b.font_changing=font_changing
                else:
                    b.flagF=False
                if hasStyleFlag: b.styleFlag=True

    def setup2(self):
        if not self.initFlag2:
            self.initFlag2=True
            for b in self.bros:
                if hasattr(b,'bros'):
                    for c in b.bros:
                        if c not in self.bros:
                            self.bros.append(c)

    def setCompleterList(self):
        if not self.FlagCompleter:
            self.FunSetCompleterList()
            self.FlagCompleter=True
        self.showCompleter()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event) #to preserve classical behaviour before adding the below
        self.setCompleterList()

    def enterEvent(self, event):
        super().enterEvent(event)
        if not self.font()==self.font_changing and not self.hasFocus():
            self.setFont(self.font_changing)

    def leaveEvent(self, event):
        super().leaveEvent(event)
        if self.font()==self.font_changing and not self.hasFocus():
            self.setFont(self.initialFont)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        for f in self.addfuncin:
            self.addfuncin[f]()
        self.focusInFun()
            
    def setFocus(self):
        super().setFocus()
        self.focusInFun()

    def focusInFun(self):
        self.setStyleSheet(setSS(self,self.initialStyle+" "+color_changing))
        self.setFont(self.font_changing)
        for b in self.bros:
            if (not b==self) and b.flagS:
                    b.setStyleSheet(b.initialStyle+" "+color_changing_black)
                 
    def focusOutEvent(self, event):
        super().focusOutEvent(event) #to preserve classical behaviour before adding the below
        for f in self.addfuncout:
            self.addfuncout[f]()
        self.focusOutFun()

    def clearFocus(self):
        super().clearFocus()
        self.focusOutFun()

    def focusOutFun(self):
        for b in self.bros:
            if b.flagS:
                if hasattr(b,'default_stylesheet'):
                    b.setStyleSheet(b.default_stylesheet)
                else:
                    b.setStyleSheet(setSS(b,b.initialStyle))
            if b.flagF:
                b.setFont(b.initialFont)
        #self.addlab.clear()
            
    def showCompleter(self):
        if self.completer():
            self.completer().complete()

class MyQLineEditNumber(MyQLineEdit):
    def __init__(self,parent):
        super().__init__(parent)       
        self.addfuncreturn={}

    def keyPressEvent(self, event):
        #infoPrint.white(event.key())
        if event.key() in (Qt.Key.Key_Space, #space
            Qt.Key.Key_Comma, #comma 
            Qt.Key.Key_Delete, Qt.Key.Key_Backspace, #del, backspace
            Qt.Key.Key_Left,Qt.Key.Key_Right, #left, right
            Qt.Key.Key_Return, Qt.Key.Key_Enter #return
            ) \
            or (event.key()>=Qt.Key.Key_0 and event.key()<=Qt.Key.Key_9):
            super().keyPressEvent(event)
        if event.key()==16777220:
            for f in self.addfuncreturn:
                self.addfuncreturn[f]()
        
class MyQCombo(QtWidgets.QComboBox):
    def wheelEvent(self, event):
        event.ignore()

#MyQSpin=QtWidgets.QSpinBox
class MyQSpin(QtWidgets.QSpinBox):
    def __init__(self,parent):
        super().__init__(parent)
        self.addwid=[]
        self.initFlag=False
        self.styleFlag=False
        self.addfuncin={} 
        self.addfuncout={} 
        self.addfuncreturn={}
        
        self.setAccelerated(True)
        self.setGroupSeparatorShown(True)

    def setup(self): 
        if not self.initFlag:
            self.initFlag=True
            font_changing = QtGui.QFont(self.font())
            font_changing.setItalic(font_italic)
            font_changing.setWeight(font_weight)
            self.bros=[self]+self.addwid
            for b in self.bros:
                if b.styleFlag: continue
                b.initialStyle=b.styleSheet()+" "+backgroundcolor_none
                b.initialFont=b.font()
                b.font_changing=font_changing
                b.styleFlag=True
            self.spinFontObj=[]
            for c in self.findChildren(QObject):
                if hasattr(c,'setFont'):
                    self.spinFontObj+=[c]

    def setFocus(self):
        super().setFocus()
        self.focusInFun()

    def focusInEvent(self, event):
        super().focusInEvent(event) #to preserve classical behaviour before adding the below
        for f in self.addfuncin:
            self.addfuncin[f]()
        self.focusInFun()

    def focusInFun(self):
        if not self.font()==self.font_changing:
            for b in self.bros:
                b.setStyleSheet(b.initialStyle+" "+color_changing)
                b.setFont(b.font_changing)
            for b in self.spinFontObj:
                b.setFont(self.font_changing)

    def focusOutEvent(self, event):
        super().focusOutEvent(event) #to preserve classical behaviour before adding the below
        for f in self.addfuncout:
            self.addfuncout[f]()
        if self.font()==self.font_changing:
            for b in self.bros:
                b.setStyleSheet(b.initialStyle)
                b.setFont(b.initialFont)
            for b in self.spinFontObj:
               b.setFont(self.initialFont)

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.key() in (Qt.Key.Key_Return,Qt.Key.Key_Enter) and self.hasFocus():
            for f in self.addfuncreturn:
                self.addfuncreturn[f]()
    
    def wheelEvent(self, event):
        event.ignore()
    
    def textFromValue(self, value):
        return formatNumber(self,value)
    
def formatNumber(self:QWidget,value):
    if Flag_GROUPSEPARATOR:
        text=self.locale().toString(float(value), 'd')
    else:
        text=f"{value:f}"
    return (text).rstrip('0').rstrip(curr_locale.decimalPoint()) 
    #return ('%f' % value).rstrip('0').rstrip('.') 

class MyQSpinXW(MyQSpin):
    def __init__(self,parent):
        super().__init__(parent)
        self.Win=-1

    def focusInEvent(self, event):
        super().focusInEvent(event) #to preserve classical behaviour before adding the below
        if len(self.addwid)>0:
            self.Win=self.addwid[0].value()

class MyToolButton(QtWidgets.QToolButton):
    def __init__(self,parent):
        super().__init__(parent)

class MyQDoubleSpin(QtWidgets.QDoubleSpinBox):
    def __init__(self,parent):
        super().__init__(parent)
        self.addwid=[]
        self.initFlag=False
        self.styleFlag=False
        self.addfuncin={}
        self.addfuncout={}
        self.addfuncreturn={}

        self.setAccelerated(True)
        self.setGroupSeparatorShown(True)

    def setup(self): 
        if not self.initFlag:
            self.initFlag=True
            font_changing = QtGui.QFont(self.font())
            font_changing.setItalic(font_italic)
            font_changing.setWeight(font_weight)
            self.bros=[self]+self.addwid
            for b in self.bros:
                if self.styleFlag: continue
                b.initialStyle=b.styleSheet()+" "+backgroundcolor_none
                b.initialFont=b.font()
                b.font_changing=font_changing
                b.styleFlag=True
            self.spinFontObj=[]
            for c in self.findChildren(QObject):
                if hasattr(c,'setFont'):
                    self.spinFontObj+=[c]

    def focusInEvent(self, event):
        super().focusInEvent(event) #to preserve classical behaviour before adding the below
        for f in self.addfuncin:
            self.addfuncin[f]()
        if not self.font()==self.font_changing:
            for b in self.bros:
                b.setStyleSheet(b.initialStyle+" "+color_changing)
                b.setFont(self.font_changing)
            for b in self.spinFontObj:
                b.setFont(self.font_changing)

    def focusOutEvent(self, event):
        super().focusOutEvent(event) #to preserve classical behaviour before adding the below
        for f in self.addfuncout:
            self.addfuncout[f]()
        if self.font()==self.font_changing:
            for b in self.bros:
                b.setStyleSheet(b.initialStyle)
                b.setFont(b.initialFont)
            for b in self.spinFontObj:
                b.setFont(self.initialFont)
                
    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.key() in (Qt.Key.Key_Return,Qt.Key.Key_Enter) and self.hasFocus():
            for f in self.addfuncreturn:
                self.addfuncreturn[f]()
    
    def wheelEvent(self, event):
        event.ignore()
    
    def textFromValue(self, value):
        if Flag_GROUPSEPARATOR:
            text=self.locale().toString(float(value), 'f', self.decimals())
        else:
            text=f"{value:f}"
        return (text).rstrip('0').rstrip(curr_locale.decimalPoint()) 
        #return ('%f' % value).rstrip('0').rstrip('.') 

class CollapsibleBox(QtWidgets.QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.initFlag=False
        self.FlagPush=False
        self.dpix=5
        self.toolMinimumWidth=400
        self.toolHeight=20
        self.content_area:QGroupBox=None
        self.toggle_button:QPushButton=None
        self.push_button:MyToolButton=None
        
    def setup(self,*args):
        if not self.initFlag:
            if len(args):
                self.ind=args[0]
                self.stretch=args[1]
            else:
                self.ind=-1
                self.stretch=0
            self.initFlag=True

            if self.content_area is None:
                self.content_area=self.findChild(QtWidgets.QGroupBox)
            self.content_area.setStyleSheet("QGroupBox{border: 1px solid gray; border-radius: 6px;}")

            if self.toggle_button is None:
                self.toggle_button=self.findChild(QtWidgets.QToolButton)
                self.toggle_button.setChecked(InitCheck)
                self.toggle_button.clicked.connect(self.on_click)    
            self.toggle_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
            self.toggle_button.setMinimumWidth(self.toolMinimumWidth)

            if self.push_button is None:
                self.push_button=self.findChild(MyToolButton)

            self.OpenStyle=\
            "QToolButton { border: none; }\n"+\
            "QToolButton::hover{color: rgba(0,0,255,200);}"+\
            "QToolButton::focus{color: rgba(0,0,255,200);}"
            #"QToolButton::hover{border: none; border-radius: 6px; background-color: rgba(0, 0,128,32); }"
            self.ClosedStyle=\
            "QToolButton { border: 1px solid lightgray; border-radius: 6px }\n"+\
            "QToolButton::hover{ border: 1px solid rgba(0,0,255,200); border-radius: 6px; color: rgba(0,0,255,200);}"+\
            "QToolButton::focus{ border: 1px solid rgba(0,0,255,200); border-radius: 6px; color: rgba(0,0,255,200);}" #background-color: rgba(0, 0,128,32); }" 

            self.heightToogle=self.toggle_button.minimumHeight()
            self.heightOpened=self.minimumHeight()
            self.heightArea=self.heightOpened-self.toolHeight
            
            self.on_click()

    #@QtCore.pyqtSlot()
    def on_click(self):
        checked = self.toggle_button.isChecked()
        pri.Coding.yellow(f'>>>>> {self.objectName()} {"opening" if checked else "closing"}')
        if self.objectName()=='CollapBox_ImSet' and checked:
            pass
        if self.FlagPush: 
            self.push_button.show()
        else:
            self.push_button.hide()
        if checked:
            self.content_area.show()
            self.toggle_button.setArrowType(QtCore.Qt.ArrowType.DownArrow)
           
            self.toggle_button.setMinimumHeight(self.heightToogle)
            self.toggle_button.setMaximumHeight(self.heightToogle)
            self.setMinimumHeight(self.heightOpened)
            self.setMaximumHeight(int(self.heightOpened*1.5))
            self.content_area.setMinimumHeight(self.heightArea)
            self.content_area.setMaximumHeight(int(self.heightArea*1.5))

            self.toggle_button.setSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Preferred)
            self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Maximum)
            self.content_area.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)

            self.toggle_button.setStyleSheet(self.OpenStyle)
            if self.ind>0:
                self.parent().layout().setStretch(self.ind,self.stretch)
        else:
            self.content_area.hide()
            self.toggle_button.setArrowType(QtCore.Qt.ArrowType.RightArrow)
            
            self.toggle_button.setMinimumHeight(self.heightToogle+self.dpix)
            self.toggle_button.setMaximumHeight(self.heightToogle+self.dpix)
            self.setMinimumHeight(self.heightToogle+self.dpix*2)
            self.setMaximumHeight(self.heightToogle+self.dpix*2)
            self.content_area.setMinimumHeight(0)
            self.content_area.setMaximumHeight(0)

            self.toggle_button.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Preferred)
            self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
            self.content_area.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Minimum)
            
            self.toggle_button.setStyleSheet(self.ClosedStyle)
            
            if self.ind>0:
                self.parent().layout().setStretch(self.ind,0)
        
        # Forza l'aggiornamento dei layout
        self.updateGeometry()
        self.parentWidget().updateGeometry()
        self.parentWidget().adjustSize()

    def openBox(self):
        self.toggle_button.setChecked(True)
        self.on_click()

    def closeBox(self):
        self.toggle_button.setChecked(False)
        self.on_click()

class myQTreeWidget(QTreeWidget):
    def __init__(self,parent):
        super().__init__(parent)
        self.FlagArrowKeysNormal=False
        self.addfuncin={}
        self.addfuncout={}
        self.addfuncreturn={}
        self.addfuncshift_pressed={}
        self.addfuncshift_released={}
        self.addfuncdel_pressed={}
        self.addfuncarrows_pressed={}
        self.addfuncarrows_released={}
        self.addfunckey_pressed={}
        #self.ui:Ui_TreeTab=None
        self.ui=None

    def focusInEvent(self, event):
        super().focusInEvent(event) #to preserve classical behaviour before adding the below
        for f in self.addfuncin:
            self.addfuncin[f]()

    def focusOutEvent(self, event):
        super().focusOutEvent(event) #to preserve classical behaviour before adding the below
        for f in self.addfuncout:
            self.addfuncout[f]()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Shift:
            super().keyPressEvent(event) 
            for f in self.addfuncshift_pressed:
                self.addfuncshift_pressed[f]()
        elif  event.key() == Qt.Key.Key_Delete or event.key() == Qt.Key.Key_Backspace:
            super().keyPressEvent(event) 
            for f in self.addfuncdel_pressed:
                self.addfuncdel_pressed[f]()
        elif event.key() == Qt.Key.Key_Up or event.key() == Qt.Key.Key_Down:
            if self.FlagArrowKeysNormal:
                return super().keyPressEvent(event) 
            else:
                Flag=True
                for f in self.addfuncarrows_pressed:
                    Flag=Flag and self.addfuncarrows_pressed[f](event.key())
                #if Flag: super().keyPressEvent(event) 
        else:
            super().keyPressEvent(event) 
            for f in self.addfunckey_pressed:
                self.addfunckey_pressed[f](event.key())

    def keyReleaseEvent(self, event):
        super().keyReleaseEvent(event) 
        if event.key() == QtCore.Qt.Key_Shift:
            for f in self.addfuncshift_released:
                self.addfuncshift_released[f]()
        elif event.key() == QtCore.Qt.Key_Up or event.key() == QtCore.Qt.Key_Down:
            if self.FlagArrowKeysNormal:
                return super().keyReleaseEvent(event)
            else:
                Flag=True
                for f in self.addfuncarrows_released:
                    Flag=Flag and self.addfuncarrows_released[f](event.key())
                #if Flag: super().keyPressEvent(event)
                
class ToggleSplitterHandle(QtWidgets.QSplitterHandle):
    def mousePressEvent(self, event):
        super().mousePressEvent(event) 
        for f in self.parent().addfuncin:
            self.parent().addfuncin[f]()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event) 
        for f in self.parent().addfuncout:
            self.parent().addfuncout[f]()

class myQSplitter(QSplitter):
    def __init__(self,parent):
        super().__init__(parent)
        self.OpWidth=0
        self.OpMaxWidth=0
        self.addfuncin={}
        self.addfuncout={}
        self.addfuncreturn={}

    def createHandle(self):
        return ToggleSplitterHandle(self.orientation(), self)

class RichTextPushButton(QPushButton):
    margin=0
    spacing=0

    def __init__(self, parent=None, text=None):
        if parent is not None:
            super().__init__(parent)
        else:
            super().__init__()
        
        self.__lyt = QHBoxLayout()
        self.__lyt.setContentsMargins(self.margin, 0, self.margin, 0)
        self.__lyt.setSpacing(self.spacing)
        self.setLayout(self.__lyt)

        self.__icon= QLabel(self)
        self.__icon.setSizePolicy(
            QSizePolicy.Preferred,
            QSizePolicy.Expanding,
        )
        self.__icon.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)

        self.__lbl = QLabel(self)
        if text is not None:
            self.__lbl.setText(text)
        else:
            self.__lbl.hide()
        self.__lbl.setAttribute(Qt.WA_TranslucentBackground)
        self.__lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.__lbl.setSizePolicy(
            QSizePolicy.Preferred,
            QSizePolicy.Expanding,
        )
        self.__lbl.setTextFormat(Qt.RichText)
        self.__lbl.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        self.__lyt.addWidget(self.__icon)     
        self.__lyt.addWidget(self.__lbl)  
        self.__lyt.setStretch(0,1)
        self.__lyt.setStretch(1,2)

        self.lyt=self.__lyt
        self.lbl=self.__lbl
        self.icn=None
        return

    def setText(self, text):
        if text:
            self.__lbl.show()
            self.__lbl.setText(text)
        else: self.__lbl.hide()
        self.updateGeometry()
        return
    
    def setIcon(self, icon):
        h=int(self.size().height()/2)
        pixmap = icon.pixmap(QSize(h,h))
        self.__icon.setPixmap(pixmap) 
        self.icn=icon
        self.updateGeometry()
        return
    
    def setIconSize(self, size:QSize):
        if self.icn: self.__icon.setPixmap(self.icn.pixmap(size)) 
        self.updateGeometry()
        return

    def sizeHint(self):
        s = QPushButton.sizeHint(self)
        w_lbl = self.__lbl.sizeHint()
        w_icon = self.__icon.sizeHint()
        s.setWidth(w_lbl.width()+w_icon.width()
                   +self.margin*2+self.spacing)
        s.setHeight(w_lbl.height())
        return s

class myQTableWidget(QtWidgets.QTableWidget):
    def __init__(self,parent):
        super().__init__(parent)
        self.RowInfo=[]
        self.InfoLabel:QLabel=None
        self.DeleteButton:QPushButton=None
        self.addwid=[]
        self.addfuncreturn={}
        self.addfuncout={}
        #self.itemSelectionChanged.connect(self.resizeInfoLabel)

    def keyPressEvent(self, event):
        #infoPrint.white(event.key())
        super().keyPressEvent(event) 
        if event.key() in (Qt.Key.Key_Return,Qt.Key.Key_Enter):  #return
            for f in self.addfuncreturn:
                self.addfuncreturn[f]()
    
    def focusInEvent(self, event):
        super().focusInEvent(event) 
        #if self.DeleteButton: #and self.currentItem():
        #    self.DeleteButton.setEnabled(True)

    def focusOutEvent(self, event):
        super().focusOutEvent(event) 
        for f in self.addfuncout:
            self.addfuncout[f]()
        #if self.InfoLabel:
        #    self.InfoLabel.hide()
        #    self.InfoLabel.setText('') 
        #if self.DeleteButton:
        #    self.DeleteButton.setEnabled(False)

    def resizeEvent(self, event):
        super().resizeEvent(event) 
        self.resizeInfoLabel()

    def resizeInfoLabel(self):
        if self.InfoLabel and (True if not self.addwid else not self.addwid[0].hasFocus()):
            item=self.currentItem()
            if item:
                self.InfoLabel.show()
                if self.RowInfo: rowInfo=self.RowInfo[self.currentRow()]
                else: rowInfo=''
                tip=item.toolTip()
                if not "<br>" in tip:
                    fw=lambda t: QtGui.QFontMetrics(self.InfoLabel.font()).size(QtCore.Qt.TextSingleLine,t).width()
                    if fw(tip)>self.InfoLabel.width():
                        k=0
                        while fw(tip[:k])<self.InfoLabel.width():
                            k+=1
                        tip="<br>".join([tip[:k-1], tip[k-1:2*k]])
                if rowInfo: tip="<br>".join([tip,rowInfo])
                self.InfoLabel.setText(tip)
            else:
                self.InfoLabel.hide()
                self.InfoLabel.setText('') 

def isfloat(num):
    try:
        float(num)
        return True
    except ValueError:
        return False
    
class ClickableLabel(QLabel):
    pixmap_size=25
    def __init__(self, *args):
        super().__init__(*args)
        
        self.default_stylesheet = self.styleSheet()
        self.highlight_stylesheet = "background-color: #dcdcdc; border-radius: 3px;"
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.resetHighlight)
        self.timer.setSingleShot(True)

        self.moviePixmap=None
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.toolTip():
            self.highlight()
            self.showMessageBox()
            self.resetHighlight()
            
    def showMessageBox(self):
        if self.moviePixmap: pixmap=self.moviePixmap
        else: pixmap=self.pixmap()
        warningDialog(self.window(),Message=self.toolTip(),pixmap=pixmap,title='Info')

    def highlight(self):
        self.setStyleSheet(self.highlight_stylesheet)
        self.repaint()

    def resetHighlight(self):
        self.setStyleSheet(self.default_stylesheet)

    def setToolTip(self,arg__1):
        QLabel.setToolTip(self,arg__1)
        QLabel.setStatusTip(self,arg__1)
        if arg__1:
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        else:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

class ClickableEditLabel(ClickableLabel):
    def setup(self):
        line_edit=QLineEdit(self)
        line_edit.setPalette(self.palette())
        line_edit_bg_color_str = line_edit.palette().color(QPalette.ColorRole.Base).name()
        self.default_stylesheet=self.styleSheet()+f"ClickableEditLabel{{background-color: {line_edit_bg_color_str}}};"
        self.setStyleSheet(self.default_stylesheet)
        line_edit.setParent(None)

class CustomLineEdit(QLineEdit):
    cancelEditing = Signal()

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.originalText = text

    def focusOutEvent(self, event):
        self.cancelEditing.emit()
        super().focusOutEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.cancelEditing.emit()
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.cancelEditing.emit()
        else:
            super().keyReleaseEvent(event)

class ResizingLabel(QLabel):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.complete_text=self.text()
        
    def setText(self,text):
        self.complete_text=text
        self.resizeText(text)
        return 
    
    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.resizeText(self.text())
        return 
    
    def resizeText(self,text):
        text=self.complete_text
        metrics = QFontMetrics(self.font())
        if self.alignment() & Qt.AlignmentFlag.AlignRight:
            FlagRight=True
            textElideMode=Qt.TextElideMode.ElideLeft
        else:
            FlagRight=False
            textElideMode=Qt.TextElideMode.ElideRight
        if "<span" in text:
            match = re.search(r"<span(.*?)</span>", text)
            html_part = "<span"+match.group(1)+"</span>"
            index = match.start(1)-5
            text_without_bullet=text.replace(html_part,'')
            truncated_text=metrics.elidedText(text_without_bullet, textElideMode, self.width()-5)
            if FlagRight:
                index=len(truncated_text)-3*(int('...' in truncated_text))-len(text_without_bullet[index:])
                if index>0:
                    truncated_text=truncated_text[:index]+html_part+truncated_text[index:]
            elif index>len(truncated_text)-3:
                truncated_text=truncated_text[:index]+html_part+truncated_text[index:]
        else:
            truncated_text = metrics.elidedText(text, textElideMode, self.width())
        super().setText(truncated_text)

class EditableLabel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0,0,0,0)
        self.main_layout.setSpacing(0)

        self.label = ResizingLabel(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.label.mouseDoubleClickEvent = self.enable_editing

        self.edit = CustomLineEdit(self)
        self.edit.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.edit.hide()
        self.edit.editingFinished.connect(self.disable_editing)
        self.edit.cancelEditing.connect(self.disable_editing)
        self.updateLabel=lambda: None
        self.bullet=''

        self.installEventFilter(self)  # Installare il filtro eventi

        self.main_layout.addWidget(self.label)
        self.main_layout.addWidget(self.edit)

    def setText(self,text):
        self.label.setText(text)
        self.edit.setText(text)

    def setFont(self,font:QFont):
        self.label.setFont(font)
        self.edit.setFont(font)

    def enable_editing(self, event):
        self.label.hide()
        self.edit.setGeometry(self.label.geometry())  # Assicurati che l'editor prenda la posizione della label
        self.edit.setText(self.label.text().replace(self.bullet,''))  # Assicurati che il testo corrente venga impostato nell'editor
        self.edit.selectAll()
        self.edit.show()
        self.window().setFocus()
        self.edit.setFocus()

    def disable_editing(self):
        self.edit.hide()
        self.label.setText(self.edit.text())
        self.label.show()
        self.updateLabel()


#********************************************* Matplotlib
import io
import matplotlib as mpl
mpl.use('Qt5Agg')
import matplotlib.pyplot as pyplt
import matplotlib.image as mplimage
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure as mplFigure
from mpl_toolkits.axes_grid1 import make_axes_locatable

import matplotlib.style as mplstyle
mplstyle.use('fast')
#mplstyle.use(['dark_background', 'ggplot', 'fast'])
 
class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=8, height=8, dpi=100):
        self.inp_width=width
        self.inp_height=height
        self.inp_dpi=dpi
        self.fig = mplFigure(figsize=(width, height), dpi=dpi)
        self.fig2=[]
        self.axes = self.fig.gca() #self.fig.add_subplot(111)
        self.addfuncrelease={}
        mpl.rcParams["font.family"]=fontName
        #mpl.rcParams["font.size"]=12
        color_tuple=(0.95,0.95,0.95,0)
        #clrgb=[int(i*255) for i in color_tuple]
        self.fig.set_facecolor(color_tuple)

        self.copyIcon=QIcon(icons_path+"copy.png")
        self.openNewWindowIcon=QIcon(icons_path+"open_new_window.png")
        self.scaleDownIcon=QIcon(icons_path+"scale_down.png")
        self.scaleUpIcon=QIcon(icons_path+"scale_up.png")
        self.scaleAllIcon=QIcon(icons_path+"scale_all.png")
        self.showAllIcon=QIcon(icons_path+"show_all.png")
        self.alignAllIcon=QIcon(icons_path+"align_all.png")        
        self.closeAllIcon=QIcon(icons_path+"close_all.png")
        self.loadImageIcon=QIcon(icons_path+"open_image.png")
        self.loadResultIcon=QIcon(icons_path+"open_result.png")

        super(MplCanvas, self).__init__(self.fig)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if event.button() == Qt.LeftButton:
            for f in self.addfuncrelease:
                self.addfuncrelease[f]()

    def copy2clipboard(self):
        with io.BytesIO() as buffer:
            self.fig.savefig(buffer)
            QApplication.clipboard().setImage(QImage.fromData(buffer.getvalue()))
            self.showTip(self,'Image copied to clipboard!')
    
    def copy2newfig(self,text='Vis'):
        fig2=QMainWindow()
        fig2.setPalette(self.palette())
        fig2.setWindowTitle(text)
        fig2.setStyleSheet("background-color: white;")

        wid=QWidget(fig2)
        fig2.setCentralWidget(wid)
        lay=QVBoxLayout(wid)

        lbl=QLabel(fig2)
        lbl.setAlignment(QtCore.Qt.AlignCenter)
        with io.BytesIO() as buffer:
            self.fig.savefig(buffer)
            pixmap = QPixmap(QImage.fromData(buffer.getvalue()))
        lbl.setPixmap(pixmap)
        lbl.setScaledContents(False)
        lbl2=QLabel(text,fig2)
        lbl2.setWordWrap(True)
        lbl2.setStyleSheet("color: black;")

        lay.setSpacing(0)
        lay.addWidget(lbl)
        lay.addWidget(lbl2)

        self.fig2.append(fig2) 

        def closeFig2(event):
            type(fig2).closeEvent(fig2,event)
            self.fig2.pop(self.fig2.index(fig2))
            return 
        fig2.closeEvent=lambda event: closeFig2(event)


        def fCopy2clipboard():
            QApplication.clipboard().setImage(lbl.pixmap().toImage())
            self.showTip(fig2,'Image copied to clipboard!')
            return
        
        fig2.scaleFactor=1
        def resizeFig2(scale):
            fig2.scaleFactor=fig2.scaleFactor*scale
            fig2.scaleFactor=min([fig2.scaleFactor,1.5])
            fig2.scaleFactor=max([fig2.scaleFactor,0.5])
            fig2.setFixedSize(s0*fig2.scaleFactor)
            lbl.setPixmap(pixmap.scaled(pixmap.size()*fig2.scaleFactor,mode=Qt.TransformationMode.SmoothTransformation))
            return
        fig2.resizeFig2=resizeFig2

        sc0=QGuiApplication.primaryScreen().geometry()         
        def shiftFig2(dir):
            dpix=10
            geo=fig2.geometry()
            if dir=='u':
                geo.setY(max([geo.y()-dpix,sc0.y()]))
            elif dir=='d':
                geo.setY(min([geo.y()+dpix,sc0.y()+sc0.height()-fig2.height()]))
            elif dir=='l':
                geo.setX(max([geo.x()-dpix,sc0.x()]))
            elif dir=='r':
                geo.setX(min([geo.x()+dpix,sc0.x()+sc0.width()-fig2.width()]))
            fig2.setGeometry(geo)
            return

        QS_down=QShortcut(QKeySequence('Down'), fig2)
        QS_down.activated.connect(lambda: shiftFig2('d'))
        QS_up=QShortcut(QKeySequence('Up'), fig2)
        QS_up.activated.connect(lambda: shiftFig2('u'))
        QS_right=QShortcut(QKeySequence('Right'), fig2)
        QS_right.activated.connect(lambda: shiftFig2('r'))
        QS_left=QShortcut(QKeySequence('Left'), fig2)
        QS_left.activated.connect(lambda: shiftFig2('l'))

        QS_copy2clipboard=QShortcut(QKeySequence('Ctrl+C'), fig2)
        QS_copy2clipboard.activated.connect(fCopy2clipboard)

        fScaleDown=lambda: resizeFig2(0.9)
        QS_scaleDown=QShortcut(QKeySequence('Ctrl+Down'), fig2)
        QS_scaleDown.activated.connect(fScaleDown)
        fScaleUp=lambda: resizeFig2(1.1)
        QS_scaleUp=QShortcut(QKeySequence('Ctrl+Up'), fig2)
        QS_scaleUp.activated.connect(fScaleUp)
        fScaleAll=lambda: self.scaleAll(fig2.scaleFactor)
        QS_scaleAll=QShortcut(QKeySequence('Ctrl+Return'), fig2)
        QS_scaleAll.activated.connect(fScaleAll)

        QS_showAll=QShortcut(QKeySequence('Ctrl+S'), fig2)
        QS_showAll.activated.connect(self.showAll)
        QS_alignAll=QShortcut(QKeySequence('Ctrl+A'), fig2)
        QS_alignAll.activated.connect(self.alignAll)
        QS_closeAll=QShortcut(QKeySequence('Ctrl+X'), fig2)
        QS_closeAll.activated.connect(self.closeAll)
        
        fig2.lbl:QLabel=lbl
        def contextMenuEventFig2(event):
            contextMenu = QMenu()
            copy2clipboard = contextMenu.addAction("Copy to clipboard ("+QS_copy2clipboard.key().toString(QKeySequence.NativeText)+")")
            contextMenu.addSeparator()
            scaleDown = contextMenu.addAction("Scale down ("+QS_scaleDown.key().toString(QKeySequence.NativeText)+")")
            scaleUp = contextMenu.addAction("Scale up ("+QS_scaleUp.key().toString(QKeySequence.NativeText)+")")
            scaleAll = contextMenu.addAction("Scale all ("+QS_scaleAll.key().toString(QKeySequence.NativeText)+")")
            contextMenu.addSeparator()
            showAll = contextMenu.addAction("Show all ("+QS_showAll.key().toString(QKeySequence.NativeText)+")")
            alignAll = contextMenu.addAction("Align all ("+QS_alignAll.key().toString(QKeySequence.NativeText)+")")
            closeAll = contextMenu.addAction("Close all ("+QS_closeAll.key().toString(QKeySequence.NativeText)+")")
            
            copy2clipboard.setIcon(self.copyIcon)
            scaleDown.setIcon(self.scaleDownIcon)
            scaleUp.setIcon(self.scaleUpIcon)
            scaleAll.setIcon(self.scaleAllIcon)
            showAll.setIcon(self.showAllIcon)
            alignAll.setIcon(self.alignAllIcon)
            closeAll.setIcon(self.closeAllIcon)

            action = contextMenu.exec(fig2.mapToGlobal(event.pos()))

            if action == copy2clipboard:
                fCopy2clipboard()
            elif action == scaleDown:
                fScaleDown()
            elif action == scaleUp:
                fScaleUp()
            elif action == scaleAll:
                self.scaleAll(fig2.scaleFactor)
            elif action == showAll:
                self.showAll()
            elif action == alignAll:
                self.alignAll()
            elif action == closeAll:
                self.closeAll()
            
        
        fig2.contextMenuEvent=lambda event: contextMenuEventFig2(event)

        fig2.show()
        fig2.setFixedSize(fig2.width(), fig2.height())
        s0=fig2.size()

        self.posWindow(len(self.fig2)-1)
        """
        fgeo = fig2.frameGeometry()
        centerPoint = QGuiApplication.primaryScreen().availableGeometry().center()
        fgeo.moveCenter(centerPoint)
        fig2.move(fgeo.topLeft())
        """
    
    def showTip(self,obj,message):
        showTip(obj,message)

    def posWindow(self,ind):
        w=h=0
        for f in self.fig2:
            f:QMainWindow
            w=max([w,f.frameGeometry().width()])
            h=max([h,f.frameGeometry().height()])
        geoS=QGuiApplication.primaryScreen().availableGeometry()
        ncol=int(geoS.width()/w)
        nrow=int(geoS.height()/h)
        ntot=ncol*nrow
        if ind<0: ind=range(len(self.fig2))
        else: ind=[ind]
        for kk in ind:
            k=kk%ntot
            k=kk
            i=int(k/ncol)
            j=k-i*ncol
            f=self.fig2[kk]
            fg=f.frameGeometry()
            fg.moveTopLeft(QPoint(j*w,i*h))
            f.move(fg.topLeft())

    def scaleAll(self,scale):
        for f in self.fig2:
            f:QMainWindow
            f.scaleFactor=scale
            f.resizeFig2(1.0)

    def showAll(self):
        for f in self.fig2:
            f:QMainWindow
            f.hide()
            f.show()
    
    def closeAll(self):
        for f in range(len(self.fig2)):
            f:QMainWindow
            f=self.fig2[0]
            f.close()
        self.fig2=[]
    
    def alignAll(self):
        self.posWindow(-1)
        self.showAll()


def setAppGuiPalette(self:QWidget,palette:QPalette=None):
    applic:QApplication
    if hasattr(self,'app'): 
        applic=self.app
    else: 
        return
    if palette==None: 
        palette=applic.style().standardPalette()
    else:
        applic.setPalette(palette)

    try:
        if self.focusWidget():
            self.focusWidget().clearFocus()
        widgets=[self]
        if hasattr(self,'FloatingTabs'):    widgets+=self.FloatingTabs
        if hasattr(self,'FloatingWindows'): widgets+=self.FloatingWindows
        if hasattr(self,'aboutDialog'):     widgets.append(self.aboutDialog)
        if hasattr(self,'logChanges'):      widgets.append(self.logChanges)
        widgets+=self.findChildren(QDialog)
        for f in  widgets:
            if f and isinstance(f, QWidget):
                f.setPalette(palette)
                for c in f.findChildren(QObject):
                    if hasattr(c,'setPalette') and not isinstance(c, (MplCanvas, mplFigure, QStatusBar)):
                        c.setPalette(palette)
                    if hasattr(c,'initialStyle') and hasattr(c, 'setStyleSheet'):
                        c.setStyleSheet(c.initialStyle)
                for c in f.findChildren(QObject):
                    c:MyQLineEdit
                    if isinstance(c, MyQLineEdit) and hasattr(c, 'setup'):
                        c.initFlag=False
                        c.styleFlag=False
                        c.setup()
                for c in f.findChildren(QObject):
                    if hasattr(c,'setup2'):
                        c.initFlag2=False
                        c.setup2()
        if hasattr(self,'ResizePopup'): 
            if self.ResizePopup is not None:
                self.ResizePopup=type(self.ResizePopup)(self.buttonSizeCallbacks) #non riesco a farlo come gli altri
        if hasattr(self,'w_Vis'): self.w_Vis.addPlotToolBar()
    except:
        pri.Error.red("***** Error while setting the application palette! *****")

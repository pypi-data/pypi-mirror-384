import sys
from .PaIRS_pypacks import *
from .Input_Tab import *
from .Output_Tab import *
from .Process_Tab import *
from .Log_Tab import *
from .Vis_Tab import *

class PaIRS_QSplitter(QSplitter):
    minimumResizeWidth=0
    class PaIRS_ToggleSplitterHandle(QtWidgets.QSplitterHandle):
        minimumHandleDisplacement=200
        def __init__(self, o: Qt.Orientation, parent: QSplitter):
            super().__init__(o, parent)
            self.index=parent.count()-1
            self.limits=[None,None]
            #pri.Coding.yellow(f'Splitter handle #{self.index}')
            self.init_pos=None
            return

        def mousePressEvent(self, event:QMouseEvent):
            super().mousePressEvent(event) 
            
            TABpar.FlagSettingPar=True
            pa:PaIRS_QSplitter=self.parent()
            visibleHandles=[]
            widgets=[]
            visibleWidgets=[]
            for i in range(pa.count()):
                handle = pa.handle(i)
                if handle.isVisible():
                    visibleHandles.append(handle)
                widget=pa.widget(i)
                widgets.append(widget)
                if widget.isVisible():
                    visibleWidgets.append(widget)
            i=visibleHandles.index(self)
            self.index=widgets.index(visibleWidgets[i])
            """
            width=0
            index=-1
            sizes=pa.splitterSizes
            #sizes=pa.sizes()
            while self.pos().x()>width and index<pa.count()-1:
                index+=1
                w=pa.widget(index)
                if w:
                    if w.isVisible():
                        width+=sizes[index]+pa.handleWidth()
            self.index=index
            """
            pri.Coding.magenta(f'pos={self.pos().x()} index={self.index}')
            
            w=pa.widget(self.index)
            w.setMinimumWidth(pa.minimumSizes[self.index])
            w.widget.setMinimumWidth(pa.minimumSizes[self.index])
            w.setMaximumWidth(pa.maximumSizes[self.index])
            w.widget.setMaximumWidth(pa.maximumSizes[self.index])

            pri.Coding.magenta(f'{w.widget.TABname} [{pa.minimumSizes[self.index]},{pa.maximumSizes[self.index]}]')
            dwf=w.maximumWidth()-w.minimumWidth()
            pa.splitterReleased([pa.count()-1],[+dwf],FlagReleased=False)    

            self.init_pos=self.pos().x()
            self.limits=[w.minimumWidth()-w.width(),w.maximumWidth()-w.width()]

        def mouseReleaseEvent(self, event:QMouseEvent):
            super().mouseReleaseEvent(event) 

            TABpar.FlagSettingPar=False
            if self.init_pos:
                pa:PaIRS_QSplitter=self.parent()
                w=pa.widget(self.index)
                dw=self.pos().x()-self.init_pos
                dwf=pa.maximumSizes[self.index]-w.minimumWidth()
                indexes=[self.index,pa.count()-1]
                deltaWidths=[dw,-dwf]
                pa.splitterReleased(indexes,deltaWidths,FlagReleased=True)   

                w.setFixedWidth(pa.splitterSizes[self.index])      
                w.widget.setFixedWidth(pa.splitterSizes[self.index])      
            
        def mouseMoveEvent(self, event: QMouseEvent):
            pa:PaIRS_QSplitter=self.parent()
            #pa.splitterMoving(event.pos().x(),self.index)

            pa.setSizes(pa.sizes())

            pos=event.pos().x()
            if pos and self.limits[0] and self.limits[1]:
                pos=max([self.limits[0],pos])
                pos=min([self.limits[1],pos])
                pos+=self.pos().x()+self.width()
    

                bar=pa.scrollArea.horizontalScrollBar()
                val=bar.value()
                wSA=pa.scrollArea.width()
                #pri.Coding.magenta(f'val={val}\t pos={pos}\t wSA={wSA}')
                if pos-val>wSA:
                    bar.setValue(pos-wSA)
                elif pos<val:
                    bar.setValue(pos)
            return super().mouseMoveEvent(event)
    
    def createHandle(self):
        handle =self.PaIRS_ToggleSplitterHandle(self.orientation(), self)
        handle.setCursor(QCursor(Qt.SplitHCursor if self.orientation() == Qt.Horizontal else Qt.SplitVCursor))
        return handle

    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setOpaqueResize(False)
        self.FlagInit=False
        self.splitterSizes=[]
        self.minimumSizes=[]
        self.maximumSizes=[]
        self.splitterMaximumSize=0
        self.scrollArea:PaIRS_QScrollArea=None

    def addWidget(self, widget):
        if not self.FlagInit: i=self.count()
        else: i=self.count()-1
        return self.insertWidget(i,widget)
    
    def insertWidget(self, i, widget):
        self.splitterSizes.insert(i,widget.minimumWidth())
        self.minimumSizes.insert(i,widget.minimumWidth())
        self.maximumSizes.insert(i,widget.maximumWidth()+int(self.handleWidth()*0.5))
        self.splitterMaximumSize+=self.minimumSizes[-1]+self.handleWidth()
        widget.setMaximumWidth(widget.minimumWidth())
        return super().insertWidget(i,widget)

    def replaceWidget(self, i, widget):
        self.splitterMaximumSize-=self.minimumSizes[i]+self.handleWidth()
        self.splitterSizes[i]=widget.minimumWidth()
        self.minimumSizes[i]=widget.minimumWidth()
        self.maximumSizes[i]=widget.maximumWidth()+int(self.handleWidth()*0.5)
        self.splitterMaximumSize+=self.minimumSizes[i]+self.handleWidth()
        widget.setMaximumWidth(widget.minimumWidth())
        return super().replaceWidget(i,widget)
    
    def setHandleWidth(self, width: int) -> None:
        self.maximumSizes=[m-int(0.5*self.handleWidth())+int(0.5*width) for m in self.maximumSizes]
        return super().setHandleWidth(width)
    
    def splitterReleased(self,indexes,deltaWidths,FlagReleased=True):
        for index,dw in zip(indexes,deltaWidths):
            w=self.widget(index)
            self.splitterSizes[index]=max([min([self.splitterSizes[index]+dw,w.maximumWidth()]),w.minimumWidth()])
        self.splitterResize(FlagReleased=FlagReleased)
        pri.Coding.green(f'i= {indexes}\t dw={deltaWidths}\t Splitter sizes: {self.splitterSizes}')

    def splitterResize(self,FlagVisible=None,FlagReleased=True):
        width=0
        if FlagReleased: self.splitterSizes[-1]=0
        for i in range(self.count()):
            w=self.widget(i)
            if FlagVisible is not None: flag=FlagVisible[i]
            else: flag=w.isVisible()
            if flag:
                width+=self.splitterSizes[i]+self.handleWidth()
        pa=self.parent().parent()
        if pa.width()>width:
            self.splitterSizes[-1]+=pa.width()-width
            width=pa.width()+self.handleWidth()
        self.setFixedWidth(width)
        self.setSizes(self.splitterSizes)  
        if FlagReleased:
            for i in range(self.count()-1):
                w=self.widget(i)
                w.setFixedWidth(self.splitterSizes[i])
                w.widget.setFixedWidth(self.splitterSizes[i]) 
        return self.splitterSizes
        
    def resizeEvent(self,event):
        #self.splitterResize()
        return
        
    def setHandleVisibility(self):
        for i in range(self.count()):
            self.handle(i).setVisible(self.widget(i).isVisible())

class PaIRS_QScrollArea(QScrollArea):
    def __init__(self,widgets=[],handleWidth=20,margin=0):
        super().__init__()    
        self.handleWidth=handleWidth
        self.margin=margin

        self.setWidgetResizable(True)
        self.container_widget = QWidget()
        self.setWidget(self.container_widget)
        self.main_layout = QVBoxLayout(self.container_widget)
        self.main_layout.setContentsMargins(margin,margin,margin,margin)

        self.splitter=None 
        self.setupSplitter(widgets)

    def setupSplitter(self,widgets):
        self.frames=[]
        if not widgets: 
            return
        if self.splitter:
            self.main_layout.removeWidget(self.splitter)
        self.splitter=splitter=PaIRS_QSplitter(Qt.Horizontal)
        self.splitter.setObjectName('tabArea_splitter')
        self.widgets=widgets

        dw=0
        # Aggiungi alcuni widget al QSplitter
        for i,w in enumerate(widgets):
            w:gPaIRS_Tab
            w.blockSignals(True)
            frame = QFrame()
            frame_layout = QVBoxLayout(frame)
            frame_layout.setContentsMargins(0,0,0,0)
            frame.setMinimumWidth(w.minimumWidth())
            frame.setMaximumWidth(w.maximumWidth())
            dw+=max([dw,w.maximumWidth()-w.minimumWidth()])
            
            objName=f'{w.TABname}_frame'
            frame.setObjectName(objName)
            frame.setStyleSheet(f"""
                QFrame#{objName} {{
                    border: 1px solid rgba(128, 128, 128, 0.5); 
                    border-radius: 15px;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(128, 128, 128, 0), stop:1 rgba(224, 224, 224, 0.25));
                    }}
                QWidget#scrollAreaWidgetContents{{
                    background: transparent;
                }}
            """)

            splitter.addWidget(frame)
            splitter.setCollapsible(i,False)
            #if i in (0,3): frame.hide()
            frame_layout.addWidget(w)
            setattr(frame,'widget',w)
            frame.setVisible(False)
            self.frames.append(frame)
            if hasattr(w,'ui') and hasattr(w.ui,'scrollArea'):
                w.ui.scrollArea.setObjectName('scroll_area_'+w.TABname)
            w.blockSignals(False)

        frame = QFrame()
        objName=f'empty_frame'
        frame.setMinimumWidth(50)
        frame.setMaximumWidth(dw)
      
        frame.setObjectName(objName)
        frame.setStyleSheet(f"""
                QFrame#{objName} {{
                    border: none; 
                    background: transparent;
                    }}
        """)
        splitter.addWidget(frame)
        frame.setMaximumWidth(dw)
        setattr(frame,'TABname','Empty frame')
        setattr(frame,'widget',frame)
        self.frames.append(frame)
        
        splitter.setHandleWidth(self.handleWidth)
        splitter.scrollArea=self
        self.main_layout.addWidget(self.splitter)

    def resizeEvent(self, event: QResizeEvent):
        self.update()
        total_height = self.viewport().height()
        scrollbar_height = self.horizontalScrollBar().height() if self.horizontalScrollBar().isVisible() else 0
        available_height = total_height - scrollbar_height
        for f,w in zip(self.frames,self.widgets):
            f:QFrame
            available_height=max([available_height,w.minimumHeight()])
        for f,w in zip(self.frames,self.widgets):
            f:QFrame
            f.setMinimumHeight(available_height)
        self.splitter.setMinimumHeight(available_height)
        self.container_widget.setMinimumHeight(available_height+scrollbar_height)
        
        return super().resizeEvent(event)
    
class SPLpar(TABpar):   
    sizes_default       = []
    FlagVisible_default = []
    horizontalBarValues_default    = {}
    verticalBarValues_default      = {}
    FlagCollapsibleBoxes_default   = {}

    def __init__(self,Process=ProcessTypes.null,Step=StepTypes.null):
        self.setup(Process,Step)
        super().__init__('SPLpar','TabAreaWidget')
        self.unchecked_fields+=[]

    def setup(self,Process,Step):
        self.Process=Process
        self.Step=Step
        self.sizes=[s for s in SPLpar.sizes_default]
        self.FlagVisible=[f for f in SPLpar.FlagVisible_default]
        self.horizontalBarValues=copy.deepcopy(SPLpar.horizontalBarValues_default)
        self.verticalBarValues=copy.deepcopy(SPLpar.verticalBarValues_default)
        self.FlagCollapsibleBoxes=copy.deepcopy(SPLpar.FlagCollapsibleBoxes_default)

class TabAreaWidget(gPaIRS_Tab):
    margin=10

    buttonSpacing=10
    buttonSize=[40,30]
    iconSize=20

    widgetMinimumWidth=550
    widgetMaximumWidth=1100
    widgetMinimumHeight=650
    tabAreaMinimumHeight=750
    widgetMaximumHeight=10000
    widgetHorizontalMargin=10
    widgetVerticalMargin=5
    handleWidth=20

    def __init__(self, parent: QWidget = None, widgets=[],icons=[]):
        super().__init__(parent,UiClass=None,ParClass=SPLpar)
        if __name__ == "__main__":
            iconW = QIcon()
            iconW.addFile(u""+ icons_path +"logo_PaIRS.png", QSize(), QIcon.Normal, QIcon.Off)
            self.setWindowTitle('Tab area widget')
            self.setWindowIcon(iconW)
        self.main_layout=QVBoxLayout()
        
        #------------------------------------- Graphical interface: miscellanea
        self.TABname='TabArea'
        m=self.margin
        self.setMinimumWidth(self.widgetMinimumWidth+m*2+self.handleWidth)
        self.tabAreaHeight=self.buttonSize[1]+self.buttonSpacing+self.tabAreaMinimumHeight+m*4
        #self.setMinimumHeight(self.buttonSize[1]+self.buttonSpacing+self.widgetMinimumHeight+m*4)
        self.main_layout.setContentsMargins(m,m,m,m)
        self.main_layout.setSpacing(self.buttonSpacing)
        self.setLayout(self.main_layout)
        
        self.buttonBar=QWidget()
        self.buttonBar_layout=QHBoxLayout()
        self.buttonBar_layout.setContentsMargins(0,0,0,0)
        self.buttonBar_layout.setSpacing(self.buttonSpacing)
        self.buttonBar.setLayout(self.buttonBar_layout)
        self.buttonSpacer=QSpacerItem(self.buttonSize[0],self.buttonSize[1],QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.buttonBar_layout.addSpacerItem(self.buttonSpacer)

        self.scrollArea = PaIRS_QScrollArea(handleWidth=self.handleWidth)
        self.scrollArea.setObjectName('scroll_area_tabArea')

        self.main_layout.addWidget(self.buttonBar)
        self.main_layout.addWidget(self.scrollArea)

        #------------------------------------- Declaration of parameters 
        self.SPLpar_base=SPLpar()
        self.SPLpar:SPLpar=self.TABpar
        self.SPLpar_old:SPLpar=self.TABpar_old

        #------------------------------------- Callbacks 
        self.buttons=[]
        self.animation = QVariantAnimation(self.scrollArea)
        self.animation.valueChanged.connect(self.moveTo)  
        self.scrollArea.horizontalScrollBar().valueChanged.connect(self.finishAnimation)

        self.setTABlayout=self.setSPLlayout
        self.FlagAddPrev=False
        self.FlagBridge=False
        self.FlagAnimationRunning=False

        self.setupWid()
        if __name__ == "__main__": 
            self.app=app
            setAppGuiPalette(self)

        self.FlagDisplayControls=False
        self.setupTabArea(widgets,icons)      

    def null(self):
        return True
    
    def setupTabArea(self,widgets,icons):
        self.widgets=widgets
        if not widgets: return
        for b in self.buttons:
            b:RichTextPushButton
            self.buttonBar_layout.removeWidget(b)
            b.setParent(None)
        self.buttons=[]
        self.setupButtons(widgets,icons)
        self.scrollArea.setupSplitter(widgets)
        self.scrollArea.splitter.splitterResize=self.splitterResize

        self.SPLpar.sizes=[w.width() for w in widgets]+[self.scrollArea.splitter.minimumResizeWidth]
        self.SPLpar.FlagVisible=[True for w in widgets]+[True]
        self.SPLpar.horizontalBarValues={}
        self.SPLpar.verticalBarValues={}
       
        self.scrollAreas=self.findChildren(QScrollArea)
        self.collapBoxes=[]
        for w in self.widgets:
            w:gPaIRS_Tab
            self.scrollAreas+=w.findChildren(QScrollArea)
            self.scrollAreas+=w.findChildren(QTextEdit)
            self.scrollAreas+=w.findChildren(QTableWidget)
            self.scrollAreas+=w.findChildren(QTreeWidget)
            self.collapBoxes+=w.findChildren(CollapsibleBox)
        for s in  self.scrollAreas:
            s:QScrollArea
            if s.objectName()=='': continue
            self.SPLpar.horizontalBarValues[s.objectName()]=s.horizontalScrollBar().value()
            self.SPLpar.verticalBarValues[s.objectName()]=s.verticalScrollBar().value()
            s.horizontalScrollBar().valueChanged.connect(lambda v, scrllr=s: self.updateScrollBarValue(scrllr,True))
            s.verticalScrollBar().valueChanged.connect(lambda v, scrllr=s: self.updateScrollBarValue(scrllr,False))
        for cB in self.collapBoxes:
            cB:CollapsibleBox
            self.SPLpar.FlagCollapsibleBoxes[cB.objectName()]=cB.toggle_button.isChecked()
            cB.toggle_button.clicked.connect(lambda v, cllpbx=cB: self.updateFlagCollapsibleBox(cllpbx))   

        SPLpar.sizes_default=[w.width() for w in widgets]+[self.scrollArea.splitter.minimumResizeWidth]
        SPLpar.FlagVisible_default=[True for w in widgets]+[True]
        for k in self.SPLpar.horizontalBarValues:
            SPLpar.horizontalBarValues_default[k]=0
        for k in self.SPLpar.verticalBarValues:
            SPLpar.verticalBarValues_default[k]=0
        for k in self.SPLpar.FlagCollapsibleBoxes:
            SPLpar.FlagCollapsibleBoxes_default[k]=True
        #self.nullCallback()
        #self.adjustTABparInd()

    def updateFlagCollapsibleBox(self,collapBox:CollapsibleBox):
        if self.FlagSettingPar: return
        self.SPLpar.FlagCollapsibleBoxes[collapBox.objectName()]=collapBox.toggle_button.isChecked()
        TABpar_ind:SPLpar=self.TABpar_at(self.TABpar.ind)
        if TABpar_ind: TABpar_ind.FlagCollapsibleBoxes[collapBox.objectName()]=collapBox.toggle_button.isChecked()
    
    def setFlagCollapsibleBox(self):
        for cB in self.collapBoxes:
            cB:CollapsibleBox
            if cB.objectName() in self.SPLpar.FlagCollapsibleBoxes:
                if self.SPLpar.FlagCollapsibleBoxes[cB.objectName()]!=cB.toggle_button.isChecked():
                    cB.toggle_button.setChecked(self.SPLpar.FlagCollapsibleBoxes[cB.objectName()])
                    cB.on_click()

    def updateScrollBarValue(self,scrollArea:QScrollArea=None,flagHorizontal:bool=True):
        if self.FlagAnimationRunning or self.FlagSettingPar: return
        TABpar_ind:SPLpar=self.TABpar_at(self.TABpar.ind)
        
        if flagHorizontal:
            pri.Coding.magenta(f'{scrollArea.objectName()} horizontal ScrollBar value: {scrollArea.horizontalScrollBar().value()}')
            self.SPLpar.horizontalBarValues[scrollArea.objectName()]=scrollArea.horizontalScrollBar().value()
            if TABpar_ind: TABpar_ind.horizontalBarValues[scrollArea.objectName()]=scrollArea.horizontalScrollBar().value()
        else:
            pri.Coding.magenta(f'{scrollArea.objectName()} vertical ScrollBar value: {scrollArea.verticalScrollBar().value()}')
            self.SPLpar.verticalBarValues[scrollArea.objectName()]=scrollArea.verticalScrollBar().value()
            if TABpar_ind: TABpar_ind.verticalBarValues[scrollArea.objectName()]=scrollArea.verticalScrollBar().value()

    def setScrollBarValues(self):
        for s in  self.scrollAreas:
            s:QScrollArea
            if s.objectName() in self.SPLpar.horizontalBarValues:
                if self.SPLpar.horizontalBarValues[s.objectName()]!=s.horizontalScrollBar().value():
                    s.horizontalScrollBar().setValue(self.SPLpar.horizontalBarValues[s.objectName()])
            if s.objectName() in self.SPLpar.verticalBarValues:
                if self.SPLpar.verticalBarValues[s.objectName()]!=s.verticalScrollBar().value():
                    s.verticalScrollBar().setValue(self.SPLpar.verticalBarValues[s.objectName()])

    def setupButtons(self,widgets,icons):
        self.buttonBar_layout.removeItem(self.buttonSpacer)
        
        mh=self.widgetHorizontalMargin
        mv=self.widgetVerticalMargin
        for w,icon,index in zip(widgets,icons,range(len(widgets))):
            b=RichTextPushButton(self.buttonBar)
            b.lyt.setStretch(0,1)
            b.lyt.setStretch(1,0)
            b.setFixedSize(self.buttonSize[0],self.buttonSize[1])
            b.setStyleSheet(f"""
                RichTextPushButton {{
                    border: 1px solid rgba(128, 128, 128, 0.5);
                    border-radius: 5px;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(128, 128, 128, 0), stop:1 rgba(224, 224, 224, 0.25));
                    }}
            """)
            b.setCursor(Qt.CursorShape.PointingHandCursor)

            w:Input_Tab
            if hasattr(w,'ui'):
                if hasattr(w.ui,'name_tab'):
                    b.setToolTip(w.ui.name_tab.text().replace(' ',''))
                    b.setStatusTip(w.ui.name_tab.text().replace(' ',''))
                if hasattr(w.ui,'scrollArea') and not self.scrollArea.styleSheet():
                    self.scrollArea.setStyleSheet(w.ui.scrollArea.styleSheet())
            b.setIcon(QIcon(icons_path+icon+'.png'))
            b.setIconSize(QSize(self.iconSize,self.iconSize))

            self.buttonBar_layout.addWidget(b)
            b.setVisible(False)
            self.buttons.append(b)
            w.buttonTab=b
            
            def defineButtonAction():
                butt=b
                wid=w
                i=index
                return lambda: self.buttonAction(butt,wid,i,self.scrollArea)
            b.clicked.connect(defineButtonAction())
            setattr(w,'buttonAction',defineButtonAction())

            def defineCloseTabAction():
                butt=b
                return lambda: self.closeTabAction(butt)
            w.ui.button_close_tab.clicked.connect(defineCloseTabAction())
            
            #pri.Coding.red(f"{w.ui.name_tab.text()}\t\t width: min={w.minimumWidth()}, max={w.maximumWidth()}\t height: min={w.minimumHeight()}, max={w.maximumHeight()}")
            w.setContentsMargins(mh,mv,mh,mv)
            w.setMinimumWidth(max([self.widgetMinimumWidth,w.minimumWidth()]))
            w.setMaximumWidth(max([self.widgetMaximumWidth,w.maximumWidth()]))
            w.setMinimumHeight(self.widgetMinimumHeight)
            w.setMaximumHeight(self.widgetMaximumHeight)

        self.buttonBar_layout.addItem(self.buttonSpacer)

    def buttonAction(self,b:RichTextPushButton,widget:gPaIRS_Tab,index:int,scrollArea:PaIRS_QScrollArea):
        self.openTabAction(b)
        barValue_end=-int(0.5*scrollArea.splitter.handleWidth())
        for i in range(index):
            w=scrollArea.splitter.widget(i)
            if w.isVisible():
                barValue_end+=scrollArea.splitter.splitterSizes[i]+scrollArea.splitter.handleWidth()
        if barValue_end!=self.scrollArea.horizontalScrollBar().value():
            self.startAnimation(barValue_end)
        else:
            self.finishAnimation()
        return
    
    def startAnimation(self,v):
        self.FlagAnimationRunning=True
        self.animation.stop()
        self.animation.setStartValue(self.scrollArea.horizontalScrollBar().value())
        self.animation.setEndValue(v)
        self.animation.setDuration(time_ScrollBar) 
        self.animation.finished.connect(self.finishAnimation)
        self.animation.start()

    def finishAnimation(self):
        self.FlagAnimationRunning=False
        self.updateScrollBarValue(self.scrollArea,flagHorizontal=True)
    
    def moveTo(self, i):
        self.scrollArea.horizontalScrollBar().setValue(i)
    
    def openTabAction(self,b:RichTextPushButton):
        self.SPLpar.FlagVisible[self.buttons.index(b)]=True
        self.nullCallback(f'Open {b.toolTip()} tab')
        #self.adjustTABparInd()

    def closeTabAction(self,b:RichTextPushButton):
        self.SPLpar.FlagVisible[self.buttons.index(b)]=False
        self.nullCallback(f'Close {b.toolTip()} tab')
        #self.adjustTABparInd()

    def setSPLlayout(self):
        #self.setUpdatesEnabled(False)
        #if self.SPLpar.sizes!=self.scrollArea.splitter.splitterSizes:
        self.scrollArea.splitter.splitterSizes=[s for s in self.SPLpar.sizes]
        PaIRS_QSplitter.splitterResize(self.scrollArea.splitter,self.SPLpar.FlagVisible)
        #if self.SPLpar_old.isDifferentFrom(self.SPLpar,fields=['FlagVisible']):
        for w,b,f in zip(self.widgets,self.buttons,self.SPLpar.FlagVisible):
            w:QWidget
            w.parent().setVisible(f)
            b:RichTextPushButton
            b.setText('')
            if not f:
                fPixSize=b.font().pixelSize()
                s=f'<sup><span style=" font-size:{fPixSize-2}px"> 🔒</span></sup>'
                b.setText(s)
        
        #if self.SPLpar_old.barValue!=self.SPLpar.barValue:
        #self.scrollArea.horizontalScrollBar().setValue(self.SPLpar.barValue)
        self.scrollArea.horizontalScrollBar().setMaximum(self.scrollArea.splitter.width()-self.scrollArea.width())
        self.setScrollBarValues()
        self.setFlagCollapsibleBox()

        #self.setUpdatesEnabled(True)
        #self.parent().hide()
        #self.hide()
        self.parent().updateGeometry()
        self.updateGeometry()
        #self.show()
        #self.parent().show()
        return
        
    def splitterResize(self,FlagVisible=None,FlagReleased=True):
        splitterSizes=PaIRS_QSplitter.splitterResize(self.scrollArea.splitter,FlagVisible,FlagReleased)
        if FlagReleased:
            self.SPLpar.sizes=[s for s in splitterSizes]
            self.finishAnimation()

               
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    tabAreaWidget=TabAreaWidget()
    icons=['import_logo','export_logo','process_icon','terminal','vect_field']
    tabs=[Input_Tab,Output_Tab,Process_Tab,Log_Tab,Vis_Tab]
    widgets=[None]*len(tabs)
    for i in range(len(tabs)):
        widgets[i]=tabs[i](tabAreaWidget,False)  
    #tabAreaWidget.resize(1050,0)
    tabAreaWidget.setupTabArea(widgets,icons)
    tabAreaWidget.show()
    sys.exit(app.exec())

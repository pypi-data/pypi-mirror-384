from PySide6.QtGui import QMouseEvent, QResizeEvent
from .PaIRS_pypacks import *
from .TabTools import *
from .procTools import *
from .listLib import *
from datetime import datetime
from .Input_Tab_tools import PaIRSTree
import json
from .FolderLoop import *

FlagStartingPages=True

MONTH_ABBREVIATIONS = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", StepTypes.cal: "Oct", 11: "Nov", 12: "Dec"
}
projectActionButtonSize=[20,24]
processActionButtonSize=[20,24]
actionButtonSpacing=3
processButtonSize=[40,40]  #icon, button
stepButtonSize=[32,32]
headerHeight=24
titleHeight=22
subtitleHeight=14
firstLevelHeight=titleHeight+subtitleHeight
titleNameWidth=150
secondLevelHeight=24
secondLevelIconSize=16
secondLevelIndentation=9
secondLevelSpacing=10
stepNameWidth=230
processTreeIndentation=10
column0Width=30

dFontPixelSize_processTitle=6
dFontPixelSize_stepTitle=3

projectActionButtons = {
    '-':[],
    'info':       ['Info','Information',Qt.Key.Key_F1,'information'],
    'rename':     ['Rename','Rename the current project',Qt.Key.Key_F2,'editing'],
    '|rename':[],
    'new':        ['New','Create a new project',Qt.KeyboardModifier.ControlModifier|Qt.Key.Key_N],
    'open':       ['Open','Open a previous project',Qt.KeyboardModifier.ControlModifier|Qt.Key.Key_B],
    '|open':[],
    'save':       ['Save','Save the current project',Qt.KeyboardModifier.ControlModifier|Qt.Key.Key_S],
    'saveas':     ['Save as...','Save the current project to a specific path',Qt.KeyboardModifier.ControlModifier|Qt.KeyboardModifier.ShiftModifier|Qt.Key.Key_S],
    '|save':[],
    'close':      ['Close','Close the current project',Qt.KeyboardModifier.ControlModifier|Qt.Key.Key_X,'close_project'],
    '|close':[],
    'clean':      ['Clean','Clean the whole project list',Qt.KeyboardModifier.ControlModifier|Qt.KeyboardModifier.ShiftModifier|Qt.Key.Key_X], 
    }
projectGlobalActionButtons=['new','open','clean']
projectPageButtons={}
for n in ('new','open'):
    d={}
    d['name']=projectActionButtons[n][0]
    d['caption']=projectActionButtons[n][1]
    if len(projectActionButtons[n])>3:
        d['icon']=projectActionButtons[n][0][3]
    else:
        d['icon']=n+'.png'
    projectPageButtons[n]=d

processActionButtons = {
    '-':                [],
    'import':           ['Import','Import processes from disk',Qt.KeyboardModifier.ControlModifier|Qt.Key.Key_B,'open',],     
    '|import':[],
    'saveas':           ['Save as...','Save the current project to a specific path',Qt.KeyboardModifier.ControlModifier|Qt.KeyboardModifier.ShiftModifier|Qt.Key.Key_S],
    '|saveas':[],
    'info':             ['Info','Information',Qt.Key.Key_F1,'information'],
    'rename':           ['Rename','Rename the current process',Qt.Key.Key_F2,'editing',],          
    '|rename':          [],  
    'copy':             ['Copy', 'Copy process',Qt.KeyboardModifier.ControlModifier|Qt.Key.Key_C,'copy',],      
    '|paste':           [],  
    'paste_below':      ['Paste below','Paste below the current process', Qt.KeyboardModifier.ControlModifier|Qt.Key.Key_V,'paste_below',],
    'paste_above':      ['Paste above','Paste above the current process',Qt.KeyboardModifier.ControlModifier|Qt.KeyboardModifier.ShiftModifier|Qt.Key.Key_V,'paste_above',],
    '|process_loop':    [],  
    'process_loop':     ['Copy for process loop', 'Copy process to loop over folders',Qt.KeyboardModifier.ControlModifier|Qt.Key.Key_L,], 
    '|restore':         [],  
    'restore':          ['Restore','Restore the current process',Qt.KeyboardModifier.ControlModifier|Qt.Key.Key_R,'restore',],          
    '|delete':          [],  
    'delete':           ['Delete','Delete the current process',[Qt.Key.Key_Delete,Qt.Key.Key_Backspace],'delete',],          
    '|clean':           [], 
    'clean':            ['Clean','Clean the whole list',[Qt.KeyboardModifier.ShiftModifier|Qt.Key.Key_Delete,Qt.KeyboardModifier.ShiftModifier|Qt.Key.Key_Backspace],'clean'],
    }
processGlobalActionButtons=['import','paste_below','paste_above','clean']

class TreeIcons():
    icons={
            None: None,
            'project.png': None,
            'min_proc.png': None,
            'piv_proc.png': None,
            'cal_proc.png': None,
            'spiv_proc.png': None,
            'cal_step.png': None,
            'min_step.png': None,
            'piv_step.png': None,
            'disp_step.png': None,
            'cal_step_off.png': None,
            'min_step_off.png': None,
            'piv_step_off.png': None,
            'disp_step_off.png': None,
            'redx.png': None,
            'greenv.png': None,
            'completed.png': None,
            'issue.png': None,
            'running.png': None,
            'warning_circle.png': None,
            'running_warn.png': None,
            'paused.png': None,
            'queue.png': None,
            'warning.png': None,
            'workspace.png': None,
            'uninitialized.png':None,
            'linked.png':None
        }
    pixmaps={}
    FlagInit=False
    
    def __init__(self):
        if not TreeIcons.FlagInit:
            for t in TreeIcons.icons:
                if t:
                    TreeIcons.icons[t]=QIcon(icons_path+t)
                    TreeIcons.pixmaps[t]=QPixmap(icons_path+t)
                else:
                    TreeIcons.icons[t]=QIcon()
                    TreeIcons.pixmaps[t]=QPixmap()
        TreeIcons.FlagInit=True

def currentTimeString():
    current_time = datetime.now().strftime("%b %d, %Y, %I:%M:%S %p")
    month_number = datetime.now().month  # Get the current month number
    month_abbreviation = MONTH_ABBREVIATIONS.get(month_number, "Mmm")  # Get the month abbreviation based on the number
    current_time = current_time.replace(current_time[:3], month_abbreviation)  # Replace the month abbreviation
    current_time = current_time.replace("am", "AM").replace("pm", "PM")  # Convert AM/PM to uppercase
    return current_time

def scrollAreaStyle():
    style="""
    QScrollArea 
        {
            border: 1pix solid gray;
            background: transparent;
        }

    QScrollBar:horizontal
        {
            height: 15px;
            margin: 3px 10px 3px 10px;
            border: 1px transparent #2A2929;
            border-radius: 4px;
            background-color:  rgba(200,200,200,50);    /* #2A2929; */
        }

    QScrollBar::handle:horizontal
        {
            background-color: rgba(180,180,180,180);      /* #605F5F; */
            min-width: 5px;
            border-radius: 4px;
        }

    QScrollBar:vertical
        {
            background-color: rgba(200,200,200,50);  ;
            width: 15px;
            margin: 10px 3px 10px 3px;
            border: 1px transparent #2A2929;
            border-radius: 4px;
        }

    QScrollBar::handle:vertical
        {
            background-color: rgba(180,180,180,180);         /* #605F5F; */
            min-height: 5px;
            border-radius: 4px;
        }

    QScrollBar::add-line {
            border: none;
            background: none;
        }

    QScrollBar::sub-line {
            border: none;
            background: none;
    }
    """
    return style

class TREpar(TABpar):
    def __init__(self):
        self.setup()
        super().__init__(self.name,'PaIRS_Explorer')
        self.unchecked_fields+=[]

    def setup(self):
        self.name_proj, self.username, self.version = identifierName(typeObject='proj')
        self.outName   = ''
        self.createdDate    = currentTimeString()
        self.modifiedDate   = self.createdDate
        self.savedDate      = ''
        self.FlagSaved      = False
        self.FlagQueue      = True
        self.FlagRunnable   = True

        self.project = None
        self.tree = 0
        self.process = None
        self.step = None
        self.basename = 'Project'
        self.name = 'Project 1'
        self.date = f'Created: {self.createdDate}'
        self.icon = 'project.png'

    def saveBullet(self):
        return '' if self.FlagSaved else '<span style="color: #7A8B8B;"><sup>&#9679;</sup></span>'
    
    def InfoMessage(self):
        InfoMessage=f'{self.name}'
        if self.FlagSaved:
            InfoMessage+=f'\nFile location: {self.outName}'
        else:
            if self.savedDate: 
                InfoMessage+=' (unsaved)'
            else:
                InfoMessage+=' (never saved)'
        InfoMessage+=f'\n\nCreated : {self.createdDate}'
        InfoMessage+=f'\nModified: {self.modifiedDate}'
        if self.savedDate: InfoMessage+=f'\nSaved   : {self.savedDate}'
        InfoMessage+=f'\n\nUser: {self.username}'
        InfoMessage+=f'\nPaIRS version: {self.version}'
        return InfoMessage
    
class ITEpar(TABpar):
    def __init__(self,Process=None,Step=None):
        self.setup(Process,Step)
        super().__init__(self.name,'PaIRS_Explorer')
        self.OptionDone=0
        self.warningMessage='Process step not yet initialized!'
        self.procdata.ind=self.ind
        self.unchecked_fields+=[]

    def setup(self,Process,Step):
        self.Process = Process
        self.Step    = Step

        self.name_proc, self.username, self.version = identifierName(typeObject='proc')
        self.createdDate    = currentTimeString()
        self.modifiedDate   = self.createdDate
        self.savedDate      = ''
        self.FlagSaved      = False
        self.FlagQueue      = True
        self.dependencies   = []

        self.name=''
        self.icon=''
        self.date=f'Created: {self.createdDate}'
        self.children={}
        self.parents=[]
        self.mandatory=[]

        self.tabs=[]
        self.active=False
        self.label='uninitialized'
        self.progress=0
        self.ncam=0
        
        self.data_fields=[f for f,_ in self.__dict__.items()]

        buttons=processData if Step is None else stepData
        type=Process if Step is None else Step
        if type in list(buttons):
            for k,v in buttons[type].items():
                if k in self.data_fields:
                    setattr(self,k,v)
        self.basename=self.name
        self.name=self.basename

        self.procdata=dataTreePar(Process,Step)

    def copyfrom(self, newist, exceptions=None):
        super().copyfrom(newist, exceptions)
        self.procdata.ind=self.ind
        return 

    def InfoMessage(self):
        InfoMessage=f'{self.name}'
        InfoMessage+=f'\n\nCreated : {self.createdDate}'
        InfoMessage+=f'\nModified: {self.modifiedDate}'
        InfoMessage+=f'\n\nUser: {self.username}'
        InfoMessage+=f'\nPaIRS version: {self.version}'
        return InfoMessage

class ModernSwitch(QWidget):
    toggled = Signal(bool)
    handleMargin = 3
    switchHeight=25
    switchWidth=2*(switchHeight+handleMargin)
    timerTime=50 #ms

    def __init__(self, parent=None, name='', par:TREpar=None):
        super().__init__(parent)
        if parent is None:
            self.gui=self.window()
        else:
            from .gPaIRS import gPaIRS
            if hasattr(parent,'gui'):
                self.gui:gPaIRS=parent.gui
            else:
                self.gui:gPaIRS=parent.window()
        self.name=name
        self.par=par
        

        FlagWindowRun=self.gui.FlagRun if hasattr(self.gui,'FlagRun') else False
        self.setFixedSize(self.switchWidth, self.switchHeight)
        if par:
            self._checked = par.FlagQueue #and not FlagWindowRun
        else:
            self._checked = True
        par.FlagQueue=self._checked

        # Load image for the handle and scale it to fit the ellipse
        self.handle_image = QPixmap(icons_path+"gear.png")  # Replace with your image path
        self.handle_image = self.handle_image.scaledToHeight(self.height() - self.handleMargin*2, Qt.SmoothTransformation)

        self.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.FlagAnimation=False
        self.setSwitchLayout()

        self.animation = QPropertyAnimation(self, b"handle_position", self)
        self.animation.setDuration(200)
        self.animation.finished.connect(self.setSwitchLayout)

        self.text_label = QLabel("run ", self)
        #self.text_label.setStyleSheet("color: white;")  # Customize text color if needed
        font=self.text_label.font()
        #font.setItalic(True)
        font.setWeight(QFont.Weight.Light)
        self.text_label.setFont(font)
        self.text_label.adjustSize()

        self.setFixedSize(self.switchWidth, self.switchHeight)
        self.setContentsMargins(self.handleMargin,0,0,0)

        # Timer per aggiornare l'animazione
        self.FlagRunning=False
        self.gearMovie:QMovie=None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        
        self.setEnabled(not FlagWindowRun)
        self.setSwitch(self._checked)
        if par and self.gui.procdata: 
            if self.gui.procdata.ind[:-2]==par.ind[:-2]:
                self.startTimer()
        #self.timer.start(50)  # Aggiorna ogni 50 ms

    def startTimer(self):
        if not self.FlagRunning and hasattr(self.gui,'gearMovie'):
            self.FlagRunning=True
            self.gearMovie=self.gui.gearMovie
            self.timer.start(self.timerTime)
            pri.Coding.yellow('Start switch timer')

    def stopTimer(self):
        if self.FlagRunning:
            self.FlagRunning=False
            self.timer.stop()

    def set_handle_position(self, pos):
        self._handle_position = pos
        self.update()

    def get_handle_position(self):
        return self._handle_position

    handle_position = Property(int, fget=get_handle_position, fset=set_handle_position)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw background ellipse with border
        bg_rect = QRect(0, 0, self.width(), self.height())
    
        # Draw filled background ellipse
        painter.setBrush(self._bg_color)
        painter.drawRoundedRect(bg_rect.adjusted(1, 1, -1, -1), self.height() / 2, self.height() / 2)

        # Calculate position and scale for image
        handle_x = self._handle_position
        handle_y = self.handleMargin
        handle_width = self.handle_image.width()
        handle_height = self.handle_image.height()

        """
        if self._checked:
            # Draw handle image
            handle_rect = QRect(handle_x, handle_y, handle_width, handle_height)
            painter.drawPixmap(handle_rect, self.handle_image)
        else:
            # Draw handle circle
            handle_radius = self.height() - self.handleMargin*2
            handle_rect = QRect(self._handle_position, self.handleMargin, handle_radius, handle_radius)
            painter.setBrush(Qt.white)
            painter.drawEllipse(handle_rect)
        """    
        handle_rect = QRect(handle_x, handle_y, handle_width, handle_height)
        #painter.drawPixmap(handle_rect, self.handle_image)
        if self.FlagRunning:
            painter.drawImage(handle_rect,self.gearMovie.currentImage())
        else:
            painter.drawImage(handle_rect,self.handle_image.toImage())
        
        if self.FlagAnimation:
            self.text_label.setText("")
        else:
            if self._checked:
                self.text_label.setText("run ")
                self.text_label.move(self.handleMargin*2, (self.height() - self.text_label.height()) // 2)
            else:
                self.text_label.setText("skip")
                self.text_label.move(self.width() - self.height() - self.handleMargin*2, (self.height() - self.text_label.height()) // 2)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self.FlagAnimation:
            self.toggle()

    def toggle(self):
        self._checked = not self._checked
        if self.par: self.par.FlagQueue = self._checked
        self.toggled.emit(self._checked)
        self.animation.setEndValue(self.switchHandlePosition())
        self.FlagAnimation=True
        self.animation.start()
    
    def switchHandlePosition(self):
        if self._checked:
            handle_position = self.width() - self.height() + self.handleMargin
        else:
            handle_position = self.handleMargin
        return handle_position

    def setSwitchLayout(self):
        self.FlagAnimation=False
        if self._checked:
            self._bg_color = QColor(46, 204, 113)    #QColor(0, 122, 204) ù
            tip=f'{self.name if self.name else "Item"} added to run queue.'
        else:
            tip=f'{self.name if self.name else "Item"} excluded from run queue.'
            #text_color = self.palette().color(QPalette.WindowText)
            self._bg_color = QColor(175, 175, 175)
            self._bg_color.setAlpha(0.5)
        self.setToolTip(tip)
        self.setStatusTip(tip)
        self.set_handle_position(self.switchHandlePosition())

    def setSwitch(self,FlagChecked):
        if FlagChecked!=self._checked:
            self._checked=FlagChecked
            self.setSwitchLayout()

class ActionButtonBar(QWidget):
    FlagShortCuts = True

    def __init__(self, buttonData:dict={}, additionalButtonBars={}, globalButtons=[], buttonSize:list=projectActionButtonSize, FlagInvisible=True, tree:PaIRSTree=None):
        super().__init__()
        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setContentsMargins(0, 0, 0, 0)
        self.buttonLayout.setSpacing(actionButtonSpacing)
        self.setLayout(self.buttonLayout)

        self.buttonData=buttonData
        self.additionalButtonBars=additionalButtonBars
        self.globalButtons=globalButtons
        self.buttonSize = bs = buttonSize
        self.FlagInvisible=FlagInvisible
        self.tree:QWidget=None
        self.tree=tree
        if self.tree:
            self.tree.actionBar=self

        self.bShortCuts={}
        for icon_name, data in buttonData.items():
            if '-' in icon_name: 
                self.buttonLayout.addItem(QSpacerItem(bs[1], bs[1], QSizePolicy.Expanding, QSizePolicy.Minimum))
            elif '|' in icon_name:
                separator = QFrame()
                separator.setFrameShape(QFrame.VLine)
                separator.setFrameShadow(QFrame.Sunken) 
                setattr(self,'sep_'+icon_name[1:],separator)
                self.buttonLayout.addWidget(separator)
            else:
                b = QToolButton(self)
                b.setObjectName('button_'+icon_name)
                b.setCursor(Qt.CursorShape.PointingHandCursor)
                if FlagInvisible:
                    b.setStyleSheet("QToolButton { border: none; background: none;} QToolButton::menu-indicator { image: none; }")
                    b.pressed.connect(lambda btn=b: btn.setStyleSheet("QToolButton { border: none; background: #dcdcdc;} QToolButton::menu-indicator { image: none; }"))
                    b.released.connect(lambda btn=b: btn.setStyleSheet("QToolButton { border: none; background: none;} QToolButton::menu-indicator { image: none; }"))
                setattr(b,'initialStyle',b.styleSheet())
                b.setToolTip(data[1])
                b.setStatusTip(data[1])
                
                if len(data)>3:
                    icon_file=icons_path+data[3]+'.png'
                else:
                    icon_file=icons_path+icon_name+'.png'
                b.setIcon(QIcon(icon_file))
                b.setIconSize(QSize(bs[0],bs[0]))
                b.setFixedSize(bs[1],bs[1])  # Impostare la dimensione quadrata
                tip=data[1]
                if self.FlagShortCuts:
                    if len(data)>2:
                        if data[2]:
                            data2list=data[2] if isinstance(data[2],list) else [data[2]]
                            addtip=[]
                            for data2 in data2list:
                                addtip.append(QKeySequence(data2).toString(QKeySequence.NativeText) )
                                def buttonClick(b:QToolButton):
                                    if b.isVisible() and b.isEnabled(): b.click()
                                self.bShortCuts[data2]=lambda but=b:buttonClick(but)
                            tip+=' ('+" or ".join(addtip)+')'
                b.setToolTip(tip)
                b.setStatusTip(tip)
                setattr(self,'button_'+icon_name,b)
                self.buttonLayout.addWidget(b)
        if self.tree: self.setButtonActions()
    
    def setButtonActions(self):
        for icon_name, data in self.buttonData.items():
            if '-' not in icon_name and '|' not in icon_name:
                if hasattr(self.tree,'button_'+icon_name+'_action'):
                    b:QPushButton=getattr(self,'button_'+icon_name)
                    b.clicked.connect(getattr(self.tree,'button_'+icon_name+'_action'))
        self.tree.contextMenuEvent=lambda e: ActionButtonBar.treeContextMenuEvent(self,e)

    def treeContextMenuEvent(self, event):
        tree:PaIRSTree=self.tree
        item=tree.itemAt(event.pos())
        if 'globals' in self.additionalButtonBars:
            buttonBars=[bar for bar in self.additionalButtonBars['globals']]
        else:
            buttonBars=[]
        if item is None: 
            buttons=self.globalButtons
        else:
            if item.parent() is None:
                buttons=list(self.buttonData)
            else:   
                buttons=self.globalButtons
            if 'items' in self.additionalButtonBars:
                buttonBars=[bar for bar in self.additionalButtonBars['items']]+buttonBars
        if len(buttons)==0 and len(buttonBars)==0:
            return
        tree.FlagContexMenu=True

        menu=QMenu(tree)
        name=[]
        act=[]
        fun=[]
        
        for bar in buttonBars:
            bar:ProcessButtonBar
            for type, b in bar.buttons.items():
                b:QPushButton
                if b.isVisible() and b.isEnabled():
                    FlagNamedBar='name' in bar.buttonData[type]
                    if FlagNamedBar:
                        nameAction=bar.buttonData[type]['name']
                    else:
                        nameAction=b.toolTip()
                    name.append(nameAction)
                    if FlagNamedBar and 'class' in bar.buttonData[type]:
                        if 'PIV'!=nameAction[:3]: nameAction=nameAction[:1].lower()+nameAction[1:]
                        if b.isCheckable():
                            nameAction=f"{'De-activate' if b.isChecked() else 'Activate'} {nameAction}"
                        else:
                            nameAction='Add '+nameAction
                    act.append(QAction(b.icon(),nameAction,self))
                    menu.addAction(act[-1])
                    if isinstance(b,DraggableButton):
                        callback=lambda butt=b: butt.buttonAction()
                    else:
                        callback=lambda butt=b: butt.click()
                    fun.append(callback)
            if len(act): menu.addSeparator()
        for nb in buttons:
            if '-' not in nb and '|' not in nb:
                b:QPushButton=getattr(self,'button_'+nb)
                if b.isVisible() and b.isEnabled():
                    if hasattr(tree,'button_'+nb+'_action'):
                        name.append(nb)
                        act.append(QAction(b.icon(),toPlainText(b.toolTip().split('.')[0]),self))
                        menu.addAction(act[-1])
                        callback=getattr(tree,'button_'+nb+'_action')
                        fun.append(callback)
            elif '|' in nb:
                if len(act): menu.addSeparator()

        if len(act):
            action = menu.exec(tree.mapToGlobal(event.pos()))
            for nb,a,f in zip(name,act,fun):
                if a==action: 
                    f()
        return
    
    def treeKeyPressEvent(self,event):
        for ksc,f in self.bShortCuts.items():
            if ksc is None: continue
            if type(ksc)!=list: ksc=[ksc]
            for k in ksc:
                if type(k)==QKeyCombination:
                    if event.key()==k.key() and event.modifiers()==k.keyboardModifiers():
                        f()
                        return True  # Impedisce al widget di ricevere l'evento
                else:
                    if event.key()==k and not event.modifiers():
                        f()
                        return True  # Impedisce al widget di ricevere l'evento      

class ProjectTree(PaIRSTree):
    def __init__(self, parent: QWidget=None, listDim=2, listDepth=1, projectActionBar:ActionButtonBar=None, widgets:list=[], Explorer=None):
        super().__init__(parent, listDim, listDepth)
        self.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self.setSelectionBehavior(QTreeWidget.SelectionBehavior.SelectRows)
        self.setIconSize(QSize(firstLevelHeight-4, firstLevelHeight-4))

        columns=["#","Projects"]

        self.setColumnCount(len(columns))
        self.setHeaderLabels(columns)
        header=self.header()
        header.setFixedHeight(headerHeight)
        self.headerItem().setTextAlignment(0,Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter) 
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.setColumnWidth(0,column0Width)
        self.setIndentation(0)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        font=header.font()
        font.setItalic(True)
        font.setPixelSize(fontPixelSize+dFontPixelSize_stepTitle)
        header.setFont(font)      

        self.initialStyleSheet=self.styleSheet()
        self.FlagExternalDrag=False
        
        self.itemDoubleClicked.connect(self.startEditing)
        self.FlagReset=False
        self.editingFinished=lambda: None

        self.actionBar=projectActionBar
        if self.actionBar:
            self.actionBar.tree=self
            self.actionBar.setButtonActions()
        self.setupWidgets(widgets)

        self.TREpar=TREpar()
        self.TREpar_None=TREpar()
        self.adjustSelection=lambda: None
        #self.currentItemChanged.connect(self.tree_item_selection)
        self.itemSelectionChanged.connect(self.tree_item_selection)
        self.tree_item_selection()

        self.Explorer:PaIRS_Explorer=Explorer
        self.adjustSwitches = lambda: None
        self.modifyWorkspace = lambda: None
        self.setVisible(True)        

    def setupWidgets(self,widgets):
        self.widgets=widgets
        expand_level(self.itemList,0,len(widgets)+2)
        for w,itemList in zip(self.widgets,self.itemList[2:]):
            w:gPaIRS_Tab
            w.TABpar_prev=itemList

    def createProject(self,TRE:TREpar):
        Project=[ [TRE], [ [[],[]] ] ]
        if not self.widgets: return Project
        for w in self.widgets:
            w:gPaIRS_Tab
            Project.append([[]])
            Project[-1][-1].append([]) #processTree
            Project[-1][-1].append([]) #binTree
        return Project
    
    def createProjectItem(self,ind=None,FlagNewItem=True):
        self.blockSignals(True)
        if ind==None: ind=self.topLevelItemCount()
        item = QTreeWidgetItem()
        
        if FlagNewItem:
            TRE=TREpar()
            TRE.project=ind
            projectNames=[item.name for item in self.itemList[0]]
            nameInd=1
            TRE.name=f'{TRE.basename} {nameInd}'
            while TRE.name in projectNames:
                nameInd+=1
                TRE.name=f'{TRE.basename} {nameInd}'
            Project=self.createProject(TRE)
            insert_at_depth(self.itemList,self.listDepth,ind,Project)
        else:
            TRE=self.itemList[0][ind]
        
        item.setText(0,str(ind))
        item.setTextAlignment(0,Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter) 
        item.setIcon(1, TreeIcons.icons[TRE.icon])  # Set the icon of the new item
        #item.setFlags(item.flags() | Qt.ItemIsEditable)

        ind=max([0,ind])
        self.insertTopLevelItem(ind,item)
        self.setProjectItemWidget(item,TRE)

        item.setData(0,Qt.ItemDataRole.UserRole,[False])
        self.resetImNumber(ind)
        self.blockSignals(False)
        if FlagNewItem: self.signals.updateLists.emit()
        return item        

    def setProjectItemWidget(self,item:QTreeWidgetItem,TRE:TREpar):
        title_label = ResizingLabel(TRE.name+TRE.saveBullet())
        title_label.setObjectName('title_project')
        title_label.setFixedHeight(titleHeight)
        title_label.setMinimumWidth(titleNameWidth)
        title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # Set the font of the title to bold and the subtitle to double font
        self.titleFont(title_label)

        sub_title=TRE.date
        sub_title_label = ResizingLabel(sub_title)  # Create a QLabel for the subtitle
        sub_title_label.setObjectName('subtitle_project')
        sub_title_label.setFixedHeight(subtitleHeight)
        sub_title_label.setMinimumWidth(titleNameWidth)
        sub_title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.subTitleFont(sub_title_label)
        
        project_title_layout = QVBoxLayout()  # Create a vertical layout to place the subtitle below the title
        project_title_layout.addWidget(title_label)  # Add the title of the element
        project_title_layout.addWidget(sub_title_label)  # Add the subtitle

        project_title_layout.setContentsMargins(10, 2, 0, 2)  # Remove margins
        project_title_layout.setSpacing(2)  # Remove margins

        switch = ModernSwitch(parent=self,name='Project',par=TRE)
        switch.setSwitch(TRE.FlagQueue)
        switch.toggled.connect(lambda: self.toogleProcesses(TRE))
        switch.setVisible(len(self.itemList[1][TRE.project][0])>0)

        #spacer=QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        main_layout=QHBoxLayout()
        main_layout.addLayout(project_title_layout)
        #main_layout.addSpacerItem(spacer)
        main_layout.addWidget(switch)
        main_layout.setContentsMargins(0,0,10,0)
        main_layout.setSpacing(6)
        main_layout.setStretch(0,0)
        main_layout.setStretch(1,1)

        InfoMessage=TRE.InfoMessage()
        title_label.setToolTip(InfoMessage)
        title_label.setStatusTip(TRE.name)
        sub_title_label.setToolTip(sub_title)
        sub_title_label.setStatusTip(sub_title)

        widget = QWidget(self)  # Create a widget container for the layout
        widget.setLayout(main_layout)  # Set the layout for the widget container
        widget.setMinimumWidth(titleNameWidth+switch.switchWidth+main_layout.spacing())
        self.setItemWidget(item, 1 ,widget) 
        return widget

    def toogleProcesses(self,TRE:TREpar):
        ITELists=self.itemList[1][TRE.project][0]
        for k,ITEList in enumerate(ITELists):
            if self.TREpar.project==TRE.project:
                topLevelItem=self.Explorer.processTree.topLevelItem(k)
                itemWidget=self.Explorer.processTree.itemWidget(topLevelItem,1)
                switch:ModernSwitch=itemWidget.findChildren(ModernSwitch)[0]
                if TRE.FlagQueue!=switch._checked: 
                    switch.blockSignals(True)
                    switch.toggle()
                    switch.blockSignals(False)
            else:
                ITEList[0].FlagQueue=TRE.FlagQueue
        if self.Explorer.TREpar.process is not None:
            self.Explorer.ITEpar.FlagQueue=self.Explorer.ITEfromInd(self.Explorer.ITEpar.ind).FlagQueue
        self.Explorer.TREpar.FlagQueue=self.Explorer.projectTree.itemList[0][self.Explorer.TREpar.project].FlagQueue
        self.adjustSwitches()
        #self.itemSelectionChanged.emit()

    def titleFont(self,label:QLabel,fPixelSize=None):
        if fPixelSize is None:
            if hasattr(self.gui,'GPApar'): fPixelSize=self.gui.GPApar.fontPixelSize
            else: fPixelSize=fontPixelSize
        font = label.font()
        font.setFamily(fontName)
        font.setBold(True)  # Bold title
        fPS=min([fPixelSize+dFontPixelSize_processTitle,fontPixelSize+dFontPixelSize_processTitle+3])
        font.setPixelSize(fPS)  # Double font size for subtitle
        label.setFont(font)

    def subTitleFont(self,label:QLabel,fPixelSize=None):
        if fPixelSize is None:
            if hasattr(self.gui,'GPApar'): fPixelSize=self.gui.GPApar.fontPixelSize
            else: fPixelSize=fontPixelSize
        font = label.font()
        font.setFamily(fontName)
        font.setItalic(True)  # Bold title
        fPS=min([fPixelSize,fontPixelSize+3])
        font.setPixelSize(fPS)  # Double font size for subtitle
        label.setFont(font)

    def dropEvent(self,event):
        self.blockSignals(True)
        items=self.selectedItems()
        indexes=[self.indexOfTopLevelItem(i) for i in items]
        drop_indicator_position = self.dropIndicatorPosition()
        if  drop_indicator_position == QTreeWidget.DropIndicatorPosition.OnItem or self.hovered_item is None:
            self.verticalScrollBar().setValue(self.verticalScrollBarVal)
            QCursor.setPos(self.cursor_pos)
            event.ignore()  # Ignore the event if it's not a row move or a drop on an item
            return
        else:
            QTreeWidget.dropEvent(self,event)
            self.dropLists(items,indexes)
            for n,item in enumerate(items):
                k=self.indexOfTopLevelItem(item)
                TRE:TREpar=self.itemList[0][k]
                pri.Coding.blue(f'Dropping {TRE.name} {indexes[n]} --> {k}')
                self.setProjectItemWidget(item,TRE)
            self.dragged_items=self.dragged_indexes=None
            self.repaint()
            self.TREpar.copyfrom(TRE)
            self.setCurrentItem(item)
            self.blockSignals(False)
            self.tree_item_selection()
    
    def resetImNumber(self,kin=None,kfin=None):
        super().resetImNumber(kin,kfin)
        if not kin: kin=0
        if not kfin: kfin=self.topLevelItemCount()-1
        TREList=self.itemList[0]
        for i in range(kin, kfin + 1):
            TRE:TREpar=TREList[i]
            TRE.project=i
        return

    def printProjects(self):
        pri.Coding.red(f'{"*"*50}\nProject list (process tree):')
        for k in range(len(self.itemList[0])):
            pri.Coding.green(f'{k+1}) {self.itemList[0][k].name}')
            for i in self.itemList[1][k][0]:
                for n,j in enumerate(i):
                    if n==0: pri.Coding.yellow(f'     {j.name}')
                    else:    pri.Coding.cyan  (f'         {j.name}')
        pri.Coding.red(f'{"*"*50}\n')

    def startEditing(self, item, column):
        if self.itemWidget(item, column):
            self.editItem(item, column)

    def editItem(self, item, column):
        if column == 0 or item.parent() is not None:  # Se è la prima colonna, non fare nulla
            return
        widget = self.itemWidget(item, column)
        if isinstance(widget, QLineEdit):
            return  # If already editing, do nothing
        k=self.indexOfTopLevelItem(item)
        text = self.itemList[0][k].name
        line_edit = CustomLineEdit(text, self)
        self.titleFont(line_edit)
        line_edit.setText(text)
        self.setItemWidget(item, column, line_edit)
        line_edit.selectAll()
        line_edit.setFocus()
        line_edit.editingFinished.connect(lambda: self.finishEditing(item, column))
        line_edit.cancelEditing.connect(lambda: self.finishEditing(item, column))

    def finishEditing(self, item, column):
        line_edit = self.itemWidget(item, column)
        if not hasattr(line_edit,'text'):
            return
        new_text = line_edit.text()
        k=self.indexOfTopLevelItem(item)
        TRE:TREpar=self.itemList[0][k]
        TRE.name=new_text
        self.TREpar.name=new_text
        self.setProjectItemWidget(item, TRE)
        self.editingFinished()

    def keyPressEvent(self, event):
        self.actionBar.treeKeyPressEvent(event)    
        if event.key() == Qt.Key.Key_Escape:
            self.setCurrentItem(None)
            self.clearSelection()
        else:
            super().keyPressEvent(event)

    def cutItems(self,items,FlagDelete=False):
        cutted_items=[None]*len(items)
        for k,item in enumerate(items):
            cutted_items[k]=self.duplicateItem(item)
        if FlagDelete: type(self).deleted_items=cutted_items
        else: type(self).cutted_items=cutted_items
        return

    def copy_cut_delete_action(self,FlagCut=False,FlagDelete=False):   
        items,indexes=self.selectTopLevel() 
        if not items: return
        if FlagDelete: FlagCut=False
        self.cutItems(items,FlagDelete)

        FlagSignal=True
        if FlagCut or FlagDelete: 
            if len(indexes)<1000:
                for item in items:
                    self.takeTopLevelItem(self.indexOfTopLevelItem(item))
                if not FlagDelete: self.cutLists(indexes)
                else: self.deleteLists(indexes)
            else:
                if not FlagDelete: self.cutLists(indexes)
                else: self.deleteLists(indexes)
                FlagSignal=False
        else: 
            self.copyLists(indexes)

        if FlagCut or FlagDelete: 
            self.setCurrentItem(None)
            self.clearSelection()
        self.setFocus()
        if FlagSignal and not self.signalsBlocked(): self.signals.updateLists.emit()

    def clean_action(self):
        self.setSelectionMode(QTreeWidget.SelectionMode.MultiSelection)
        self.selectAll()
        self.copy_cut_delete_action(FlagDelete=True)
        self.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        return

    def button_rename_action(self):
        selected_items = self.selectedItems()
        if selected_items:
            item = selected_items[0]
            #column = self.currentColumn()
            #self.editItem(item, column)
            self.editItem(item, 1)

    def button_info_action(self):
        warningDialog(self,self.TREpar.InfoMessage(),pixmap=TreeIcons.pixmaps[self.TREpar.icon],title='Project information')

    def button_new_action(self):
        item=self.createProjectItem()
        self.setCurrentItem(item)
        self.modifyWorkspace()
        self.tree_item_selection()
        return
    
    def button_open_action(self):
        return
    
    def button_save_action(self):
        return False
    
    def button_saveas_action(self):
        return False
    
    def button_close_action(self):
        FlagQuestion=True
        if not self.TREpar.FlagSaved:
            if questionDialog(self,'The current project is unsaved. Do you want to save it before closing?'):
                FlagQuestion=not self.button_save_action()
        if FlagQuestion:
            flagYes=questionDialog(self,f"Are you sure you want to remove the selected project{'' if self.TREpar.FlagSaved else ' without saving'}?")
            if not flagYes: return
        self.blockSignals(True)
        self.copy_cut_delete_action(FlagDelete=True)
        self.blockSignals(False)
        item=self.currentItem()
        if item: self.TREpar.project=self.indexOfTopLevelItem(item)
        else: self.TREpar.project=None
        self.modifyWorkspace()
        self.tree_item_selection()
        return
    
    def button_clean_action(self):
        if self.topLevelItemCount()==1:
            self.button_close_action()
            return
        FlagUnsaved=False
        for t in self.itemList[0]:
            t:TREpar
            if not t.FlagSaved: 
                FlagUnsaved=True
                break
        additionalSentence='' if not FlagUnsaved else 'There are some unsaved projects in the current workspace. '
        flagYes=questionDialog(self,f"{additionalSentence}Are you sure you want to remove the selected projects?")
        if not flagYes: return
        self.clean_workspace()

    def clean_workspace(self):
        self.blockSignals(True)
        self.clean_action()
        self.blockSignals(False)
        item=self.currentItem()
        if item: self.TREpar.project=self.indexOfTopLevelItem(item)
        else: self.TREpar.project=None
        self.modifyWorkspace()
        self.tree_item_selection()
        return
    
    def tree_item_selection(self):
        if self.TREpar.project is not None:
            TRE:TREpar=self.itemList[0][self.TREpar.project]
            if TRE.isEqualTo(self.TREpar,fields=['name','project']):
                TRE.copyfrom(self.TREpar)
        item=self.currentItem()
        FlagEnabled=item!=None
        if FlagEnabled:
             self.TREpar.copyfrom(self.itemList[0][self.indexOfTopLevelItem(item)])
        else:
            self.TREpar.copyfrom(self.TREpar_None)
        self.setButtonLayout()

        self.adjustSelection()
        self.printProjects()
        return
    
    def setButtonLayout(self):
        item=self.currentItem()
        FlagEnabled=item!=None
        self.actionBar.button_info.setEnabled(FlagEnabled)
        self.actionBar.button_rename.setEnabled(FlagEnabled)
        self.actionBar.button_save.setEnabled(not self.TREpar.FlagSaved and FlagEnabled)
        self.actionBar.button_saveas.setEnabled(FlagEnabled)
        self.actionBar.button_close.setEnabled(FlagEnabled)
        self.actionBar.button_clean.setEnabled(self.topLevelItemCount()>0)

class DraggableButton(QToolButton):
    def __init__(self, data: dict = {}, buttonSize: list = processButtonSize, FlagInvisible=True, parent=None):
        super().__init__(parent)
        self.buttonData = data
        self.button_text = data['name']
        if len(buttonSize) == 0: buttonSize = processButtonSize
        elif len(buttonSize) < 2: buttonSize.append(buttonSize[0])
        self.buttonSize = buttonSize
        
        self.buttonIcon = TreeIcons.icons[data['icon']]
        self.setIconSize(QSize(self.buttonSize[0], self.buttonSize[0]))
        self.setIcon(self.buttonIcon)
        self.setFixedSize(self.buttonSize[1], self.buttonSize[1])
        if FlagInvisible:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            self.setStyleSheet("QToolButton { border: none; background: none;} QToolButton::menu-indicator { image: none; }")
        self.setToolTip(data['name']+' (drag to process tree or double click to add)')
        self.setStatusTip(data['name']+' (drag to process tree or double click to add)')

        self.buttonAction=lambda: None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.position()  # Memorizza la posizione del click del mouse
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        # Calcola la distanza dal punto di inizio del drag
        distance = (event.position() - self.drag_start_position).manhattanLength()
        # Se la distanza è superiore a una soglia, avvia il drag
        if distance > QApplication.startDragDistance():
            self.dragIcon()
        super().mouseMoveEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        self.buttonAction()
        pass  # Ignora il doppio click del mouse

    def dragIcon(self):
        mime_data = QMimeData()
        mime_data.setText(self.button_text)  # Store the button text as Mime data
        mime_data.setData('application/x-button', json.dumps(self.buttonData['type']).encode())
        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.setPixmap(self.buttonIcon.pixmap(QSize(self.buttonSize[1], self.buttonSize[1])))  # Show only the image during dragging
        sh = int(self.buttonSize[1] * 0.5)
        drag.setHotSpot(QPoint(sh, sh))
        self.setIconSize(QSize(0, 0))
        QApplication.setOverrideCursor(Qt.ClosedHandCursor)
        drag.exec(Qt.MoveAction)
        QApplication.restoreOverrideCursor()
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setIconSize(QSize(self.buttonSize[0], self.buttonSize[0]))

class ProcessButtonBar(QWidget):
    def __init__(self, buttonData=processData, buttonSize=processButtonSize, FlagInvisible=True):
        super().__init__()
        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setContentsMargins(0, 0, 0, 0)
        self.buttonLayout.setSpacing(int(buttonSize[0] / 2))
        self.setLayout(self.buttonLayout)
        self.buttonData=buttonData
        self.buttonSize = buttonSize
        self.FlagInvisible=FlagInvisible

        self.buttons={}
        for type, data in buttonData.items():
            if all([f in list(data) for f in ('icon', 'name', 'type')]):
                if type==ProcessTypes.null: continue
                button = DraggableButton(data, buttonSize, FlagInvisible)
                self.buttonLayout.addWidget(button)
                self.buttons[type]=button
        self.buttonLayout.addSpacerItem(QSpacerItem(0, self.buttonSize[0], QSizePolicy.Expanding, QSizePolicy.Minimum))

class StepButtonBar(QWidget):   
    def __init__(self, buttonData=stepData, buttonSize=processButtonSize, FlagInvisible=True):
        super().__init__()
        self.buttonLayout = QVBoxLayout()
        self.buttonLayout.setContentsMargins(10, headerHeight+5, 0, 10)
        self.buttonLayout.setSpacing(int(buttonSize[0]/2))
        self.setLayout(self.buttonLayout)
        self.buttonData=buttonData
        self.buttonSize = buttonSize

        self.buttons={}
        self.labels={}
        for type in buttonData:
            if type==StepTypes.null: continue
            data=buttonData[type]
            
            if all([f in list(data) for f in ('icon', 'name', 'type')]):
                button = QToolButton(self)
                button.setIconSize(QSize(self.buttonSize[0], self.buttonSize[0]))
                button.setFixedSize(self.buttonSize[1], self.buttonSize[1])
                
                if FlagInvisible:
                    button.setCursor(Qt.CursorShape.PointingHandCursor)
                    button.setStyleSheet("QToolButton { border: none; background: none;} QToolButton::menu-indicator { image: none; }")
                    button.pressed.connect(lambda btn=button: btn.setStyleSheet("QToolButton { border: none; background: #dcdcdc;} QToolButton::menu-indicator { image: none; }"))
                    button.released.connect(lambda btn=button: btn.setStyleSheet("QToolButton { border: none; background: none;} QToolButton::menu-indicator { image: none; }"))
                setattr(button,'initialStyle',button.styleSheet())
                button.setToolTip(data['name'])
                button.setStatusTip(button.toolTip())

                button.setCheckable(True)
                def buttonIcon(b,d):
                    b.iconOn = TreeIcons.icons[d['icon']]
                    b.iconOff = TreeIcons.icons[d['icon'].replace('.png','_off.png')]
                    b.clicked.connect(lambda:self.setButtonIcon(b))
                    setattr(b,'setButtonIcon',lambda:self.setButtonIcon(b))
                    
                    """
                    label=QLabel(self)
                    label.setPixmap( iconOn.pixmap(self.buttonSize[0], self.buttonSize[0]))
                    label.setMargin(int(0.5*(self.buttonSize[1]-self.buttonSize[0])))
                    label.setToolTip(data['name'])
                    label.setStatusTip(data['name'])
                    setattr(b,'label',label)
                    """
                buttonIcon(button,data)
                
                self.buttonLayout.addWidget(button)
                #Dself.buttonLayout.addWidget(button.label)
                button.setButtonIcon()
                setattr(button,'buttonData',data)

                self.buttons[type]=button

                label = QLabel(self)
                label.setPixmap(TreeIcons.pixmaps[data['icon']])
                label.setFixedSize(self.buttonSize[1], self.buttonSize[1])
                label.setScaledContents(True)
                label.setToolTip(data['name']+' (mandatory step)')
                label.setStatusTip(label.toolTip())
                self.buttonLayout.addWidget(label)
                self.labels[type]=label

        self.buttonLayout.addSpacerItem(QSpacerItem(self.buttonSize[0], 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

    def setButtonIcon(self,button:QToolButton):
        if button.isChecked(): #or not button.isVisible():
            button.setIcon(button.iconOn)
        else:
            button.setIcon(button.iconOff)

class ProcessTree(PaIRSTree):
    eventSender=None

    class CustomItemDelegate(QStyledItemDelegate):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.h1 = firstLevelHeight
            self.h2 = secondLevelHeight

        def sizeHint(self, option, index):
            if index.parent().isValid():  # Verifica se l'elemento ha un genitore
                return QSize(option.rect.width(), self.h2)  # Altezza per il secondo livello
            else:
                return QSize(option.rect.width(), self.h1)  # Altezza per il primo livello

    def __init__(self, parent: QWidget=None, listDim=2, listDepth=1, restoreTree=None, processActionBar:ActionButtonBar=None,widgets=[], Explorer=None):
        super().__init__(parent, listDim, listDepth)
        if type(restoreTree)==ProcessTree:
            self.FlagBin=True
            self.restoreTree=restoreTree
            self.name='Bin'
        else:
            self.FlagBin=False
            self.restoreTree=None
            self.name='Process'
        self.setAcceptDrops(True)
        #self.setSelectionMode(QTreeWidget.SingleSelection)
        self.setSelectionBehavior(QTreeWidget.SelectionBehavior.SelectRows)
        self.delegate=self.CustomItemDelegate()
        self.setItemDelegate(self.delegate)  # Set the default height of all rows to 40 pixels
        self.setIconSize(QSize(firstLevelHeight-4, firstLevelHeight-4))
        
        if self.FlagBin:
            columns=["#","Deleted processes"] 
            self.setStyleSheet("""
                QHeaderView::section {
                    color: red;
                }
            """)
        else:
            columns=["#","Processes"]
        self.setColumnCount(len(columns))
        self.setHeaderLabels(columns)
        header=self.header()
        header.setFixedHeight(headerHeight)
        self.headerItem().setTextAlignment(0,Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter) 
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.setColumnWidth(0,column0Width+processTreeIndentation)
        self.setIndentation(processTreeIndentation)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        font=header.font()
        font.setItalic(True)
        font.setPixelSize(fontPixelSize+dFontPixelSize_stepTitle)
        header.setFont(font)      

        self.linkedIcon=QIcon(QPixmap(icons_path+"linked.png").scaled(QSize(secondLevelIconSize,secondLevelIconSize),mode=Qt.TransformationMode.SmoothTransformation))
        self.uneditedIcon=QIcon(QPixmap(icons_path+"unedited.png").scaled(QSize(secondLevelIconSize,secondLevelIconSize),mode=Qt.TransformationMode.SmoothTransformation))
        self.undoneIcon=QIcon(QPixmap(icons_path+"undo.png").scaled(QSize(secondLevelIconSize,secondLevelIconSize),mode=Qt.TransformationMode.SmoothTransformation))

        self.initialStyleSheet=self.styleSheet()
        self.FlagExternalDrag=False
        
        self.itemDoubleClicked.connect(self.startEditing)
        self.FlagReset=False
        self.FlagContexMenu=False

        self.actionBar=processActionBar
        if self.actionBar:
            self.actionBar.tree=self
            self.actionBar.setButtonActions()
        self.setupWidgets(widgets)
        
        self.TREpar=TREpar()
        self.TREpar.tree=int(self.FlagBin)
        self.ITEpar=ITEpar()

        self.editingFinished=lambda: None

        self.Explorer:PaIRS_Explorer=Explorer
        self.adjustSwitches = lambda: None
        self.setVisible(True)

    def setupWidgets(self,widgets):
        self.widgets=widgets
        self.widgetNames=[]
        for w in self.widgets:
            w:gPaIRS_Tab
            self.widgetNames.append(w.TABname)

    def resetImNumber(self,kin=None,kfin=None):
        super().resetImNumber(kin,kfin)
        if not kin: kin=0
        if not kfin: kfin=self.topLevelItemCount()-1
        ITEList=self.itemList[0]
        inds_old={}
        deps_old={}
        links_old={}
        inds_new={}
        for i in range(self.topLevelItemCount()):
            ITEs=ITEList[i]
            inds_old_i =[]
            deps_old_i =[]
            links_old_i=[]
            for k,ITE in enumerate(ITEs):
                if k==0: 
                    inds_new[ITE.ind[2]]=i
                inds_old_i.append(copy.deepcopy(ITE.ind))
                deps_old_i.append(copy.deepcopy(ITE.dependencies))
                links_old_i.append(copy.deepcopy(ITE.link))
                ITE:ITEpar
                ITE.ind[0]=self.TREpar.project
                ITE.ind[1]=int(self.FlagBin)
                ITE.ind[2]=i
                pass
            inds_old[i]=inds_old_i
            deps_old[i]=deps_old_i
            links_old[i]=links_old_i
            if i<kin or i>kfin: continue
            for processPrev in self.itemList[1:]:
                try:
                    for stepPrev in processPrev[i]:
                        for par in stepPrev:
                            if par and not par.FlagNone:
                                par:TABpar
                                pri.Coding.blue(f'{ITEs[0].name} {par.surname} {par.ind} ---> [{self.TREpar.project}, {int(self.FlagBin)}, {i}, {par.ind[3]}, {par.ind[4]}]')
                                par.ind[0]=self.TREpar.project
                                par.ind[1]=int(self.FlagBin)
                                par.ind[2]=i
                except Exception as inst:
                    pri.Error.red(f"{inst}\n{traceback.format_exc()}")
                    pass
        if hasattr(self.gui,'setLinks'):
            inds_new_list=list(inds_new)
            FlagUnlink=True
            for i in range(self.topLevelItemCount()):
                ITEs=ITEList[i]
                inds_old_i=inds_old[i]
                deps_old_i=deps_old[i]
                links_old_i=links_old[i]
                for ITE,ind_old,dep_old,link_old in zip(ITEs,inds_old_i,deps_old_i,links_old_i):
                    for k,ind_slave_old in enumerate(dep_old):
                        if ind_slave_old[2] not in inds_new_list: #stiamo rigenerando l'albero
                            ITE.dependencies[k]=copy.deepcopy(dep_old[k])
                        else:
                            ind_slave_new=copy.deepcopy(ind_slave_old)
                            ind_slave_new[2]=inds_new[ind_slave_new[2]]
                            self.gui.setLinks(ind_slave_old,ind_old,FlagUnlink,ind_slave_new,ITE.ind)     
                            if ind_slave_new[1]==0 and ITE.ind[1]==0:     
                                self.gui.setLinks(ind_slave_new,ITE.ind)
                        pass
                    if link_old in inds_new_list: 
                        link_new=copy.deepcopy(link_old)
                        link_new[2]=inds_new[link_new[2]]
                        self.gui.setLinks(ind_old,link_old,FlagUnlink,ITE.ind,link_new)    
                        if link_new[1]==0 and ITE.ind[1]==0:     
                            self.gui.setLinks(ITE.ind,link_new)   
                        pass 
                    else: #stiamo rigenerando l'albero
                        ITE.link=copy.deepcopy(link_old)

    def dragEnterEvent(self, event):
        if type(self).eventSender is None: type(self).eventSender=self
        if event.mimeData().hasFormat('application/x-qabstractitemmodeldatalist') and type(self).eventSender!=self:
            self.FlagExternalDrag=True
            self.setStyleSheet(self.initialStyleSheet+"QTreeWidget { background-color: rgba(0, 116, 255, 0.2); }")
            event.accept()
        elif event.mimeData().hasFormat('application/x-button') and not self.FlagBin:
            self.FlagExternalDrag=True
            self.dragged_items='externalItem'
            self.setStyleSheet(self.initialStyleSheet+"QTreeWidget { background-color: rgba(0, 116, 255, 0.2); }")
            event.accept()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat('application/x-qabstractitemmodeldatalist') and type(self).eventSender!=self:
            event.setDropAction(Qt.MoveAction)
            event.accept()
        elif event.mimeData().hasFormat('application/x-button') and not self.FlagBin:
            super().dragMoveEvent(event)
            self.repaint()
            event.setDropAction(Qt.MoveAction)
            event.accept()
        else:
            super().dragMoveEvent(event)
    
    def dragLeaveEvent(self,event):
        self.restoreStyleAfterDrag()
        super().dragLeaveEvent(event)

    def restoreStyleAfterDrag(self):
        if self.FlagExternalDrag:
            self.FlagExternalDrag=False
            self.dragged_items=None
            self.setStyleSheet(self.initialStyleSheet)
            if self.parent(): self.setPalette(self.parent().palette())
            self.hovered_item=None

    def dropEvent(self, event):
        if event.mimeData().hasFormat('application/x-qabstractitemmodeldatalist') and type(self).eventSender!=self:
            if self.FlagBin:
                self.restoreTree.copy_cut_delete_action(FlagDelete=True)
            else:
                self.restoreTree.copy_cut_delete_action(FlagRestore=True)
            self.restoreStyleAfterDrag()
            event.setDropAction(Qt.MoveAction)
            event.accept()
        elif event.mimeData().hasFormat('application/x-button') and not self.FlagBin:
            if not self.hovered_item or self.gui.FlagRun:
                ind=self.topLevelItemCount()
            else:
                ind=self.indexOfTopLevelItem(self.hovered_item)+1

            t = json.loads(event.mimeData().data('application/x-button').data().decode())
            item=self.createProcessItem(t,ind)
            self.setCurrentItem(item)
            item.setSelected(True)

            self.restoreStyleAfterDrag()
            event.setDropAction(Qt.MoveAction)
            event.accept()
        else:
            super().dropEvent(event)
            for item in self.selectedItems():
                k=self.indexOfTopLevelItem(item)
                ITEs=self.itemList[0][k]
                self.setProcessItemWidget(item,ITEs[0])
                self.setStepItemWidgets(item,ITEs[0].ind[2])
        type(self).eventSender=None
        return
    
    def createParPrevs(self,ITE:ITEpar):
        if not self.widgets: return
        for  w in self.widgets:
            w:gPaIRS_Tab
            w.gen_TABpar(ITE.ind,FlagEmptyPrev=True,FlagInsert=2,Process=ITE.Process,Step=ITE.Step)
            pass
        return
    
    def createPars(self,ITE:ITEpar):
        if not self.widgets: return
        for t in ITE.tabs+['TabArea']:
            if t in self.widgetNames:
                k=self.widgetNames.index(t)
                w:gPaIRS_Tab=self.widgets[k]
                w.gen_TABpar(ITE.ind,FlagInsert=3,Process=ITE.Process,Step=ITE.Step)
                pass
        for  w, wn in zip(self.widgets,self.widgetNames):
            if wn not in ITE.tabs+['TabArea']:
                w.gen_TABpar(ITE.ind,FlagNone=True,FlagInsert=3,Process=ITE.Process,Step=ITE.Step)
                pass
        return
    
    def createProcessItem(self,type,ind=None,FlagNewItem=True,name=None):
        self.blockSignals(True)
        if ind==None: ind=self.topLevelItemCount()
        item = QTreeWidgetItem()
        
        if FlagNewItem:
            ITE=ITEpar(Process=type,Step=None)
            ITE.FlagQueue=self.TREpar.FlagQueue
            ITE.ind=[self.TREpar.project,int(self.FlagBin),ind,0,0]
            
            if name is None:
                processNames=[item[0].name for item in self.itemList[0]]+[item[0].name for item in self.restoreTree.itemList[0]]
                nameInd=1
                ITE.name=f'{ITE.basename} {nameInd}'
                while ITE.name in processNames:
                    nameInd+=1
                    ITE.name=f'{ITE.basename} {nameInd}'
            else:
                ITE.name=name
            self.createParPrevs(ITE)
            self.itemList[0].insert(ind,[ITE])
        else:
            ITE=self.itemList[0][ind][0]
        
        item.setText(0,str(ind))
        item.setTextAlignment(0,Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter) 
        item.setIcon(1, TreeIcons.icons[ITE.icon])  # Set the icon of the new item
        #item.setFlags(item.flags() | Qt.ItemIsEditable)

        ind=max([0,ind])
        self.insertTopLevelItem(ind,item)
        self.setProcessItemWidget(item,ITE)
        self.createStepItems(item,ITE)
        self.setStepItemWidgets(item,ind)
        item.setExpanded(True)

        item.setData(0,Qt.ItemDataRole.UserRole,[False])
        self.resetImNumber(ind)

        self.restoreStyleAfterDrag()
        self.blockSignals(False)
        if FlagNewItem: self.signals.updateLists.emit()
        return item        

    def setProcessItemWidget(self,item:QTreeWidgetItem,ITE:ITEpar):
        title=ITE.name
        title_label = ResizingLabel(title)
        title_label.setObjectName('title_process')
        title_label.setFixedHeight(titleHeight)
        title_label.setMinimumWidth(titleNameWidth)
        title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # Set the font of the title to bold and the subtitle to double font
        self.titleFont(title_label)
       
        if not ITE.date: 
            ITE.date = f"Created: {currentTimeString()}"
        sub_title=ITE.date
        sub_title_label = ResizingLabel(sub_title)  # Create a QLabel for the subtitle
        sub_title_label.setObjectName('subtitle_process')
        sub_title_label.setFixedHeight(subtitleHeight)
        sub_title_label.setMinimumWidth(titleNameWidth)
        sub_title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.subTitleFont(sub_title_label)
        
        process_title_layout = QVBoxLayout()  # Create a vertical layout to place the subtitle below the title
        process_title_layout.addWidget(title_label)  # Add the title of the element
        process_title_layout.addWidget(sub_title_label)  # Add the subtitle
        process_title_layout.setContentsMargins(10, 2, 0, 2)  # Remove margins
        process_title_layout.setSpacing(2)  # Remove margins

        switch = ModernSwitch(parent=self,name='Process',par=ITE)
        switch.setSwitch(ITE.FlagQueue)
        switch.toggled.connect(lambda: self.toogleProject(ITE))
        switch.setVisible(ITE.flagRun<=0 and ITE.Process!=ProcessTypes.cal and not self.FlagBin)
        
        #spacer=QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        main_layout=QHBoxLayout()
        main_layout.addLayout(process_title_layout)
        #main_layout.addSpacerItem(spacer)
        main_layout.addWidget(switch)
        main_layout.setContentsMargins(0,0,10,0)
        main_layout.setSpacing(6)
        main_layout.setStretch(0,0)
        main_layout.setStretch(1,1)

        InfoMessage=ITE.InfoMessage()
        title_label.setToolTip(InfoMessage)
        title_label.setStatusTip(InfoMessage)
        sub_title_label.setToolTip(InfoMessage)
        sub_title_label.setStatusTip(InfoMessage)

        widget = QWidget(self)  # Create a widget container for the layout
        widget.setLayout(main_layout)  # Set the layout for the widget container
        widget.setMinimumWidth(titleNameWidth+switch.switchWidth+main_layout.spacing())
        self.setItemWidget(item, 1 ,widget) 
        return widget

    def toogleProject(self,ITE:ITEpar):
        #self.projectTree.itemList[0][ITE.ind[0]].FlagQueue = ITE.FlagQueue
        topLevelItem=self.Explorer.projectTree.topLevelItem(ITE.ind[0])
        itemWidget=self.Explorer.projectTree.itemWidget(topLevelItem,1)
        switch:ModernSwitch=itemWidget.findChildren(ModernSwitch)[0]
        FlagToogle=False
        if ITE.FlagQueue==True and switch._checked==False: FlagToogle=True
        elif ITE.FlagQueue==False:
            ITELists=self.Explorer.projectTree.itemList[1][ITE.ind[0]][0]
            if all([i[0].FlagQueue==False for i in ITELists if i[0].flagRun<=0 and i[0].Process!=ProcessTypes.cal]): FlagToogle=True
        if FlagToogle:
            switch.blockSignals(True)
            switch.toggle()
            switch.blockSignals(False)
        if self.Explorer.TREpar.process is not None:
            self.Explorer.ITEpar.FlagQueue=self.Explorer.ITEfromInd(self.Explorer.ITEpar.ind).FlagQueue
        self.Explorer.TREpar.FlagQueue=self.Explorer.projectTree.itemList[0][self.Explorer.TREpar.project].FlagQueue
        self.adjustSwitches()
        # self.itemSelectionChanged.emit()

    def createStepItems(self,parentItem:QTreeWidgetItem,parentITE:ITEpar):
        indItem=parentITE.ind[2]
        #ITEs=self.itemList[0][indItem]
        indChild=-1
        for stepType,v in parentITE.children.items():
            QTreeWidgetItem(parentItem)
            indChild+=1
            if indChild>=len(self.itemList[0][indItem])-1:
                ITE=ITEpar(Process=parentITE.Process,Step=stepType)
                ITE.ind[0]=parentITE.ind[0]
                ITE.ind[1]=parentITE.ind[1]
                ITE.ind[2]=indItem
                ITE.ind[3]=indChild
                ITE.active=v
                self.itemList[0][indItem].append(ITE)
                self.createPars(ITE)
        return

    def setStepItemWidgets(self,parentItem:QTreeWidgetItem,indItem):
        for k,data in enumerate(self.itemList[0][indItem][1:]):
            data:ITEpar
            item:QTreeWidgetItem=parentItem.child(k)
            itemWidget=StepItemWidget(data,parent=self)
            self.setItemWidget(item,1,itemWidget)
            if len(data.link)==0:
                if self.gui and data.flagRun==0 and len(self.gui.ui.tabAreaWidget.TABpar_prev_at(data.ind))<=1:
                    item.setIcon(0,self.uneditedIcon)
                else:
                    item.setIcon(0,QIcon())
            else:
                item.setIcon(0,self.linkedIcon)
            if not data.active:
                item.setHidden(True)
                
    def titleFont(self,label:QLabel,fPixelSize=None):
        if fPixelSize is None:
            if hasattr(self.gui,'GPApar'): fPixelSize=self.gui.GPApar.fontPixelSize
            else: fPixelSize=fontPixelSize
        font = label.font()
        font.setFamily(fontName)
        font.setBold(True)  # Bold title
        fPS=min([fPixelSize+dFontPixelSize_processTitle,fontPixelSize+dFontPixelSize_processTitle+3])
        font.setPixelSize(fPS)  # Double font size for subtitle
        label.setFont(font)

    def subTitleFont(self,label:QLabel,fPixelSize=None):
        if fPixelSize is None:
            if hasattr(self.gui,'GPApar'): fPixelSize=self.gui.GPApar.fontPixelSize
            else: fPixelSize=fontPixelSize
        font = label.font()
        font.setFamily(fontName)
        font.setItalic(True)  # Bold title
        fPS=min([fPixelSize,fontPixelSize+3])
        font.setPixelSize(fPS)  # Double font size for subtitle
        label.setFont(font)

    def startEditing(self, item, column):
        if self.itemWidget(item, column):
            self.editItem(item, column)

    def editItem(self, item, column):
        if column == 0 or item.parent() is not None:  # Se è la prima colonna, non fare nulla
            return
        widget = self.itemWidget(item, column)
        if isinstance(widget, QLineEdit):
            return  # If already editing, do nothing
        k=self.indexOfTopLevelItem(item)
        text = self.itemList[0][k][0].name
        line_edit = CustomLineEdit(text, self)
        self.titleFont(line_edit)
        line_edit.setText(text)
        self.setItemWidget(item, column, line_edit)
        line_edit.selectAll()
        line_edit.setFocus()
        line_edit.editingFinished.connect(lambda: self.finishEditing(item, column))
        line_edit.cancelEditing.connect(lambda: self.finishEditing(item, column))

    def finishEditing(self, item, column):
        line_edit = self.itemWidget(item, column)
        if not hasattr(line_edit,'text'):
            return
        new_text = line_edit.text()
        k=self.indexOfTopLevelItem(item)
        data=self.itemList[0][k]
        data[0].name=new_text
        self.setProcessItemWidget(item, data[0])
        line_edit.editingFinished.disconnect()
        line_edit.cancelEditing.disconnect()
        self.editingFinished()
    
    def keyPressEvent(self, event):
        self.actionBar.treeKeyPressEvent(event) 
        
        if event.key() in (Qt.Key.Key_Return,Qt.Key.Key_Enter) and  event.modifiers()==Qt.KeyboardModifier.ShiftModifier:
            self.currentItem().setExpanded(False)
            return True  # Impedisce al widget di ricevere l'evento
        elif  event.key() in (Qt.Key.Key_Return,Qt.Key.Key_Enter): 
            self.currentItem().setExpanded(True)
            return True  # Impedisce al widget di ricevere l'evento
        elif  event.key()==Qt.Key.Key_Escape:
            self.setCurrentItem(None)
            self.clearSelection()
            self.Explorer.arrangeCurrentProcess(self)
            return True            
        else:
            super().keyPressEvent(event)
    
    def cutItems(self,items,FlagDelete=False):
        cutted_items=[None]*len(items)
        items_expanded=[None]*len(items)
        for k,item in enumerate(items):
            item:QTreeWidgetItem
            cutted_items[k]=self.duplicateItem(item)
            items_expanded[k]=item.isExpanded()
        if FlagDelete: type(self).deleted_items=cutted_items
        else: type(self).cutted_items=cutted_items
        type(self).items_expanded=items_expanded
        return
    
    def button_import_action(self):
        exts=[f'*{e}' for e in [outExt.min,outExt.piv,outExt.cal,outExt.spiv]]
        dirname=os.path.dirname(self.TREpar.outName) if self.TREpar.outName else ''
        filename, _ = QFileDialog.getOpenFileName(self.gui,\
            "Select a PaIRS process file", filter=' '.join(exts),\
                dir=dirname,\
                options=optionNativeDialog)
        if not filename: return
        FlagError=False
        errorString=''
        try:
            from .Saving_tools import loadList
            data, errorMessage=loadList(filename)
            errorString+=errorMessage
        except Exception as inst:
            errorString+=str(inst)
        if errorString:    
            if '_data' in filename:
                try:
                    errorString=''
                    basename,ext=os.path.splitext(filename)
                    filename2=basename[:-5]+ext
                    data, errorMessage=loadList(filename2)
                    #errorString=errorString+errorMessage if errorMessage else ''
                    if errorMessage:
                        WarningMessage="It was not possible to determine which process the selected data file belongs to.\nPlease, try again by loading the process output file directly."
                        warningDialog(self,WarningMessage)
                except Exception as inst2:
                    errorString+=str(inst2)
                    FlagError=True
                else:
                    filename=filename2
            else: FlagError=True
        if FlagError or errorString:
            WarningMessage=f'Error with loading the file: {filename}\n'
            warningDialog(self,WarningMessage)
            pri.Error.red(f'{WarningMessage}\n{errorString}\n')
            return
        try:
            ind=self.topLevelItemCount()
            insert_at_depth(self.itemList,self.listDepth,[ind],data)
            ITEs:TREpar=self.itemList[0][ind]
            for ITE in ITEs:
                ITE:ITEpar 
                ITE.ind[0]=self.TREpar.project
                ITE.ind[1]=int(self.FlagBin)
                ITE.ind[2]=ind
                ITE.link=[]
                ITE.dependencies=[]
            self.createProcessItem(ind,FlagNewItem=False)
            for ITE in ITEs: self.Explorer.setITElayout(ITE)
            item=self.topLevelItem(ind)
            self.setCurrentItem(item)
            item.setSelected(True)  
        except Exception as inst:
            WarningMessage=f'Error while retrieving the process "{data[0][0][0].name}" from the file: {filename}\n'
            warningDialog(self,WarningMessage)
            pri.Error.red(f'{WarningMessage}\n{traceback.format_exc()}\n')
        return

    def save_current_process(self,filename):
        Process=[]
        FlagSaved=False
        for l in self.itemList:
            Process.append([l[self.TREpar.process]])
        try:
            from .Saving_tools import saveList
            saveList(Process,filename)
        except Exception as inst:
            warningDialog(self,f'Error while saving the configuration file {filename}!\nPlease, retry.')
            pri.Error.red(f'Error while saving the configuration file {filename}!\n{inst}')
        return FlagSaved

    def button_saveas_action(self):
        for attr_name, attr_value in vars(ProcessTypes).items():
            if attr_value == self.ITEpar.Process:
                procExt=getattr(outExt,attr_name) 
                break
        Title="Select location and name of the process file to save"
        dirname=os.path.dirname(self.TREpar.outName) if self.TREpar.outName else ''
        filename, _ = QFileDialog.getSaveFileName(self,Title, 
                dir=dirname+self.ITEpar.name.replace(' ','_'), 
                filter=f'*{procExt}',\
                options=optionNativeDialog)
        if not filename: return
        if len(filename)>=len(procExt):
            if filename[-len(procExt):]==procExt: filename=filename[:-len(procExt)]  #per adattarlo al mac
        filename=myStandardRoot('{}'.format(str(filename)))
        if not outExt.cfg in filename:
            filename=filename+procExt
        self.save_current_process(filename)
    
    def button_info_action(self):
        warningDialog(self,self.ITEpar.InfoMessage(),pixmap=TreeIcons.pixmaps[self.ITEpar.icon],title='Process information')

    def button_rename_action(self):
        selected_items = self.selectedItems()
        if selected_items:
            item = selected_items[0]
            #column = self.currentColumn()
            #self.editItem(item, column)
            self.editItem(item, 1)

    def deleteDependencies(self,indexes):
        if hasattr(self.gui,'setLinks'):
            for i in indexes:
                for ITE in self.itemList[0][i]:
                    ITE:ITEpar
                    for dep in ITE.dependencies:
                        self.gui.setLinks(dep,ITE.ind,FlagUnlink=True)
                    if ITE.link: self.gui.setLinks(ITE.ind,ITE.link,FlagUnlink=True)

    def copy_cut_delete_action(self,FlagCut=False,FlagDelete=False,FlagRestore=False):   
        items,indexes=self.selectTopLevel() 
        if FlagRestore: FlagDelete=True
        if FlagDelete and not FlagRestore: 
            FlagCut=False
            if self.FlagBin:
                flagYes=questionDialog(self,f"Are you sure you want to remove the selected process{'es' if len(items)>1 else ''}? This operation is irreversible!")
            else: flagYes=True
            if not flagYes: return
        if FlagDelete and not self.FlagBin: self.deleteDependencies(indexes)
        self.cutItems(items,FlagDelete)

        FlagSignal=True
        if FlagCut or FlagDelete: 
            if len(indexes)<1000:
                for item in items:
                    self.takeTopLevelItem(self.indexOfTopLevelItem(item))
                if not FlagDelete: self.cutLists(indexes)
                else: self.deleteLists(indexes)
            else:
                if not FlagDelete: self.cutLists(indexes)
                else: self.deleteLists(indexes)
                FlagSignal=False
        else: 
            self.copyLists(indexes)

        if FlagCut or FlagDelete: 
            self.setCurrentItem(None)
            self.clearSelection()
        self.setFocus()
        if FlagSignal and not self.signalsBlocked(): self.signals.updateLists.emit()
        if FlagRestore or (not self.FlagBin and FlagDelete): 
            self.restore_action()
    
    def restore_action(self):
        self.restoreTree:ProcessTree
        self.restoreTree.paste_above_below_action(FlagAbove=not self.FlagBin,row=0 if not self.FlagBin else self.restoreTree.topLevelItemCount()-1,FlagPasteDeleted=True,FlagSelectAfterPasting=True)

    def paste_above_below_action(self,FlagAbove=True,row=None,FlagPasteDeleted=False,FlagSelectAfterPasting=False): 
        if len(type(self).cutted_items)==0 and not FlagPasteDeleted: return
        elif len(type(self).deleted_items)==0 and FlagPasteDeleted: return
        self.blockSignals(True)
        selectedItems,indexes=self.selectTopLevel()
        self.blockSignals(False)
        #self.clearSelection()
        if FlagPasteDeleted: new_items=type(self).deleted_items
        else: new_items=type(self).cutted_items
        if FlagAbove:
            if row is None:
                if selectedItems: row=indexes[0]
                else: row=0
            firstItemToScroll=new_items[0]
            lastItemToScroll=new_items[-1]
        else:
            if row is None:
                if selectedItems: row=indexes[-1]+1
                else: row=self.topLevelItemCount()
            else: row=row+1
            firstItemToScroll=new_items[-1]
            lastItemToScroll=new_items[0]
        self.insertItems2List(row,new_items,True,FlagSignal=False)
        for k,item in enumerate(new_items):
            item:QTreeWidgetItem
            item.setExpanded(type(self).items_expanded[k])

        indexes=[row+k for k in range(len(new_items))]
        if not self.FlagCutted and not FlagPasteDeleted:
            self.cutItems(new_items)
        self.pasteLists(row,FlagPasteDeleted)
        name_list=[i[0].name for i in self.itemList[0]]
        for pos,k in enumerate(indexes):
            item=self.topLevelItem(k) 
            ITE=self.itemList[0][k][0]
            tail=set(indexes[pos:]);
            forbidden={name_list[j] for j in range(len(name_list)) if j not in tail}
            if ITE.name in forbidden:
                base=ITE.name 
                n=1
                while f"{base} ({n})" in forbidden: n+=1
                ITE.name=f"{base} ({n})" 
                name_list[k]=ITE.name
            self.setProcessItemWidget(item,ITE)
            self.setStepItemWidgets(item,ITE.ind[2])

        self.scrollToItem(firstItemToScroll)
        self.scrollToItem(lastItemToScroll)
        if FlagPasteDeleted and not FlagSelectAfterPasting: 
            type(self).deleted_items=[]
            self.clearSelection()
        else:
            self.setCurrentItem(new_items[-1])
            new_items[-1].setSelected(True)
            if FlagPasteDeleted: self.Explorer.processTree_item_selection(self)
        self.setFocus()
        self.signals.updateLists.emit()

    def button_copy_action(self):
        self.copy_cut_delete_action()
        self.setProcessActionButtonLayout()

    def button_paste_below_action(self):
        self.blockSignals(True)
        self.paste_above_below_action(FlagAbove=False)
        self.blockSignals(False)
        self.itemSelectionChanged.emit()

    def button_paste_above_action(self):
        self.blockSignals(True)
        self.paste_above_below_action()
        self.blockSignals(False)
        self.itemSelectionChanged.emit()
    
    def button_process_loop_action(self):
        pri.Info.magenta('Process loop over folders')
        paths=choose_directories()
        if paths:
            ITEs=self.Explorer.ITEsfromTRE(self.TREpar)
            ind=copy.deepcopy(ITEs[0].ind)
            processType=ITEs[0].Process
            pixmap_list=[]
            name_list=[]
            flag_list=[]
            for i in range(1,len(ITEs)):
                ITE:ITEpar=ITEs[i]
                pixmap_list.append(icons_path+ITE.icon)
                name_list.append(ITE.name)
                flag_list.append(ITE.Step!=StepTypes.cal)
            func=lambda i, opts: self.process_loop(paths,processType,ind,ITEs[0].name,i,opts)
            dialog = FolderLoopDialog(pixmap_list, name_list, flag_list, parent=self, paths=paths, func=func, process_name=ITEs[0].name)
            dialog.exec()
        return
    
    def process_loop(self,paths,processType,ind,name0,i,opts):
        nProcess=self.topLevelItemCount()
        path=paths[i]
        name=name0+f" (.../{os.path.basename(path)}/)"
        item=self.createProcessItem(processType,nProcess,name=name)        
        ind_master=copy.deepcopy(ind)
        ind_master[-1]=-1
        ind_slave=copy.deepcopy(ind)
        ind_slave[2]=nProcess
        ind_slave[-1]=0
        
        for j in range(len(opts)):
            ind_master[3]=j
            ind_slave[3]=j
            if opts[j] in (0,2):
                ind_new=self.gui.copy_pars(ind_slave,ind_master,FlagNew=True)
                item_child=item.child(j)
                ITE:ITEpar=self.Explorer.ITEfromInd(ind_new)                
                item_child.setHidden(not ITE.active)
                if opts[j]==2:
                    INP: INPpar=self.gui.w_Input.TABpar_at(ind_new)
                    INP.path=myStandardPath(path)
                    self.gui.w_Input.scanImList(ind_new)
                    self.gui.w_Input.checkINPpar(ind_new)
                    self.gui.w_Input.setINPwarn(ind_new)
                    self.Explorer.setITElayout(ITE)

                    TABname=self.gui.w_Input.TABname
                    self.gui.bridge(TABname,ind_new)
                    
                    FlagSettingPar=TABpar.FlagSettingPar
                    TABpar.FlagSettingPar=True
                    for w in self.gui.tabWidgets:
                        w:gPaIRS_Tab
                        if w!=self.gui.w_Input:
                            currpar=w.TABpar.duplicate()
                            TABind_new=w.TABpar_at(ind_new)
                            if TABind_new and not TABind_new.FlagNone:
                                w.TABpar.copyfrom(TABind_new)
                                w.adjustTABpar()
                                w.adjustTABparInd()
                                w.TABpar.copyfrom(currpar)
                                self.gui.bridge(w.TABname,ind_new)
                    TABpar.FlagSettingPar=FlagSettingPar
                    #item_child=item.child(j)
                    #item_child.setSelected(True)
                    #self.setCurrentItem(item_child)
            else:
                self.gui.link_pars(ind_slave,ind_master,FlagSet=False)
        return

    def button_delete_action(self):
        self.blockSignals(True)
        self.copy_cut_delete_action(FlagDelete=True)
        self.blockSignals(False)
        self.itemSelectionChanged.emit()

    def button_restore_action(self):
        self.copy_cut_delete_action(FlagRestore=True)

    def button_clean_action(self):
        self.blockSignals(True)
        self.selectAll()
        self.copy_cut_delete_action(FlagDelete=True)
        self.repaint()
        self.blockSignals(False)
        #self.currentItemChanged.emit(None,None)
        self.itemSelectionChanged.emit()
        
    def setProcessActionButtonLayout(self):
        item=self.currentItem() 
        FlagEnabled=item is not None and item.parent() is None
        FlagPaste=len(ProcessTree.cutted_items)>0
        self.actionBar.setVisible(True)  #self.actionBar.setVisible(FlagEnabled)
        self.actionBar.button_saveas.setEnabled(FlagEnabled)
        self.actionBar.button_info.setEnabled(FlagEnabled)
        self.actionBar.button_rename.setEnabled(FlagEnabled)
        self.actionBar.button_copy.setEnabled(FlagEnabled)
        self.actionBar.button_paste_below.setEnabled(FlagPaste and not self.gui.FlagRun)
        self.actionBar.button_paste_above.setEnabled(FlagPaste and not self.gui.FlagRun)
        self.actionBar.button_process_loop.setEnabled(FlagEnabled and not self.FlagBin)
        self.actionBar.button_restore.setVisible(self.FlagBin)
        self.actionBar.sep_restore.setVisible(self.FlagBin)
        self.actionBar.button_restore.setEnabled(FlagEnabled)
        self.actionBar.button_delete.setEnabled(FlagEnabled)
        self.actionBar.button_clean.setEnabled(self.topLevelItemCount()>0)
        
class StepItemWidget(QWidget):
    pixmaps={'error'        : 'issue.png',
            'done'          : 'completed.png',
            'running'       : 'running.png',
            'warning'       : 'warning_circle.png',
            'running_warn'  : 'running_warn.png',
            'paused'        : 'paused.png',
            'queue'         : 'queue.png',
            'uninitialized' : 'uninitialized.png'
            }

    colors={'error'         :  'rgb(254, 61, 61)',    #'#C9302C', 
            'done'          :  'rgb( 46,204,113)',    #'#4CAE4C',
            'running'       :  'rgb( 48,107,255)',    #'#3A70C7',
            'warning'       :  'rgb(255,212, 42)',    #'#EC971F',
            'running_warn'  :  'rgb( 48,107,255)',    #'#3A70C7',
            'paused'        :  'rgb(255,127, 42)',    #'#3A70C7',
            'queue'         :  'rgb(181,170,255)',    #'#B5AAFF',
            'uninitialized' :  'rgb( 0,0,0)',
            }
    
    label_size=secondLevelHeight-4
    bar_width=label_size*3+4

    def __init__(self, ITE:ITEpar, parent=None):
        super().__init__(parent)
        if parent is None:
            self.gui=self.window()
        else:
            from .gPaIRS import gPaIRS
            if hasattr(parent,'gui'):
                self.gui:gPaIRS=parent.gui
            else:
                self.gui:gPaIRS=parent.window()
        
        # Create the layout
        layout = QHBoxLayout(self)

        # Add an icon
        self.stepIcon = QLabel()
        self.stepIcon.setFixedHeight(secondLevelHeight-2)
        self.stepIcon.setFixedWidth(secondLevelHeight-2)
        self.stepIcon.setScaledContents(True)
        self.stepIcon.setPixmap(TreeIcons.pixmaps[ITE.icon])
        layout.addWidget(self.stepIcon)

        # Add a spacer
        spacer = QSpacerItem(5, secondLevelHeight, QSizePolicy.Minimum, QSizePolicy.Minimum)
        layout.addItem(spacer)

        # Add a label with text
        self.stepName = QLabel()
        self.stepName.setObjectName('title_step')
        self.stepName.setFixedWidth(stepNameWidth)
        self.stepName.setFixedHeight(secondLevelHeight)
        self.stepTitleFont(self.stepName)
        layout.addWidget(self.stepName)

        self.stepName.setText(ITE.name)
        self.stepName.setToolTip(ITE.name)
        self.stepName.setStatusTip(ITE.name)

        # Add another icon
        self.label = ClickableLabel()
        self.label.setFixedWidth(self.label_size)
        self.label.setFixedHeight(self.label_size)
        self.label.setScaledContents(True)
        self.label.setToolTip(ITE.warningMessage)
        self.label.setStatusTip(ITE.warningMessage)
        layout.addWidget(self.label)

        # Add a progress bar
        self.progressBar = QProgressBar()
        self.progressBar.setFixedWidth(self.bar_width)
        self.progressBar.setFixedHeight(self.label_size)
        layout.addWidget(self.progressBar)

        # Add a spacer
        spacer = QSpacerItem(40, secondLevelHeight, QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout.addItem(spacer)

        # Set layout margin and spacing
        layout.setContentsMargins(secondLevelIndentation, 0, 0, 0)
        layout.setSpacing(secondLevelSpacing)

        minimumWidth=self.stepIcon.width()+self.stepName.width()+self.label.width()+self.progressBar.width()+secondLevelSpacing*4+secondLevelIndentation
        self.setMinimumWidth(minimumWidth)
        self.setFromITE(ITE)

    def stepTitleFont(self,label:QLabel,fPixelSize=None):
        if fPixelSize is None:
            if hasattr(self.gui,'GPApar'): fPixelSize=self.gui.GPApar.fontPixelSize
            else: fPixelSize=fontPixelSize
        font = label.font()
        font.setFamily(fontName)
        fPS=min([fPixelSize + dFontPixelSize_stepTitle, fontPixelSize + dFontPixelSize_stepTitle +3])
        font.setPixelSize(fPS)  # Double font size for subtitle
        label.setFont(font)

    def colorProgressBar(self,color='green'):
        style_sheet = f"""
            QProgressBar {{
                background-color: transparent;
                border: 1px solid gray;
                border-radius: 5px;
                text-align: center;
            }}
            
            QProgressBar::chunk {{
                background-color: {color}; 
                width: 1px; /* Larghezza del chunk */
                margin: 0px; /* Spazio tra i chunk */
            }}
        """
        self.progressBar.setStyleSheet(style_sheet)

    def setFromITE(self,ITE:ITEpar):
        pixmap_path=StepItemWidget.pixmaps[ITE.label]
        FlagGif=False
        if ITE.flagRun==-2 and ITE.label=='running' and hasattr(self.gui,'runningMovie'):
            if hasattr(self.gui,'procdata') and self.gui.procdata is ITE.procdata:
                FlagGif=True
        if FlagGif:
            self.label.moviePixmap=TreeIcons.pixmaps[pixmap_path]
            self.label.setMovie(self.gui.runningMovie)
        else:
            self.label.moviePixmap=None
            self.label.setPixmap(TreeIcons.pixmaps[pixmap_path])
        self.label.setToolTip(ITE.warningMessage)
        self.label.setStatusTip(ITE.warningMessage)

        if ITE.Step==StepTypes.cal:
            self.progressBar.setVisible(ITE.ncam>0)
            self.progressBar.setMaximum(ITE.ncam)
            self.progressBar.setValue(ITE.progress)
            self.progressBar.setFormat(f'{ITE.progress}/{ITE.ncam}')
        elif ITE.Step==StepTypes.disp:
            self.progressBar.setVisible(ITE.procdata.Nit>0)
            self.progressBar.setMaximum(ITE.procdata.Nit)
            self.progressBar.setValue(ITE.progress)
            #self.progressBar.setValue(ITE.procdata.numFinalized)
            #self.progressBar.setFormat(f'{ITE.progress}/{ITE.procdata.Nit}')
        else:
            self.progressBar.setVisible(ITE.procdata.nimg>0)
            self.progressBar.setMaximum(ITE.procdata.nimg) 
            self.progressBar.setValue(ITE.progress)
            #self.progressBar.setValue(ITE.procdata.numFinalized)  # Set the initial value of the progress bar
            

        bar_color=StepItemWidget.colors[ITE.label]
        self.colorProgressBar(bar_color)

class PaIRS_Explorer(gPaIRS_Tab):         
    class ProcessTreeWidget_signals(QObject):
        pass
        
    def __init__(self,parent=None,widgets=[]):
        super().__init__(parent,UiClass=None,ParClass=ITEpar)
        if __name__ == "__main__":
            iconW = QIcon()
            iconW.addFile(u""+ icons_path +"checklist.png", QSize(), QIcon.Normal, QIcon.Off)
            self.setWindowTitle('Process tree widget')
            self.setWindowIcon(iconW)
        self.signals=self.ProcessTreeWidget_signals()

        #------------------------------------- Layout
        self.treeIcons=TreeIcons()

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        self.main_layout.setContentsMargins(5, 5, 5, 5)

        self.projectTree_layout= QVBoxLayout()
        self.projectTree_layout.setContentsMargins(0, 0, 0, 0)
        self.projectTree_layout.setSpacing(1)

        self.projectActionBar = ActionButtonBar(buttonData=projectActionButtons,globalButtons=projectGlobalActionButtons,buttonSize=projectActionButtonSize)
        self.projectTree_layout.addWidget(self.projectActionBar)
        self.projectTree = ProjectTree(self,projectActionBar=self.projectActionBar,widgets=widgets,Explorer=self)

        self.scroll_area_projectTree = QScrollArea(self)
        self.scroll_area_projectTree.setObjectName('scroll_area_projectTree')
        self.scroll_area_projectTree.setWidgetResizable(True)
        self.scroll_area_projectTree.setWidget(self.projectTree)
        self.scroll_area_projectTree.setMinimumWidth(0)
        self.scroll_area_projectTree.setStyleSheet(scrollAreaStyle())
        self.projectTree_layout.addWidget(self.scroll_area_projectTree)

        self.processTree_layout= QVBoxLayout()
        spa=int(processButtonSize[0]/4)
        self.processTree_layout.setContentsMargins(0, spa, 0, 0)
        self.processTree_layout.setSpacing(1)
        self.processButtonBar = ProcessButtonBar(processData,buttonSize=processButtonSize)
        self.processTree_layout.addWidget(self.processButtonBar)
        self.processTree_layout.addItem(QSpacerItem(0,spa,QSizePolicy.Minimum, QSizePolicy.Minimum))
        self.processActionBar = ActionButtonBar(buttonData=processActionButtons,globalButtons=processGlobalActionButtons,buttonSize=processActionButtonSize)
        self.processTree_layout.addWidget(self.processActionBar)
        self.binActionBar = ActionButtonBar(buttonData=processActionButtons,globalButtons=processGlobalActionButtons,buttonSize=processActionButtonSize)
        self.processTree_layout.addWidget(self.binActionBar)

        self.stepButton_layout=QHBoxLayout()
        self.stepButton_layout.setContentsMargins(0, 0, 0, 0)
        self.stepButton_layout.setSpacing(int(stepButtonSize[0]/4))

        self.stepButtonBar=StepButtonBar(stepData,buttonSize=stepButtonSize)
        self.stepButton_layout.addWidget(self.stepButtonBar)

        self.processActionBar.additionalButtonBars={'globals': [self.processButtonBar], 'items': [self.stepButtonBar]}
        self.binActionBar.additionalButtonBars={'items': [self.stepButtonBar]}

        self.processTree = ProcessTree(self,processActionBar=self.processActionBar,widgets=widgets,Explorer=self)
        self.binTree = ProcessTree(self,restoreTree=self.processTree,processActionBar=self.binActionBar,widgets=widgets,Explorer=self)
        self.processTree.restoreTree=self.binTree
        itemWidths=[
            titleNameWidth+ModernSwitch.switchWidth+6, #first level
            stepNameWidth+StepItemWidget.label_size+StepItemWidget.bar_width+secondLevelSpacing*3 #second level
        ]
        self.projectTree.setMinimumWidth(max(itemWidths)+self.projectTree.columnWidth(0)-30)
        self.processTree.setMinimumWidth(max(itemWidths)+self.processTree.columnWidth(0)-30)
        self.binTree.setMinimumWidth(max(itemWidths)+self.binTree.columnWidth(0)+40)

        self.Explorer_tree_splitter=QSplitter(self)
        self.Explorer_tree_splitter.setObjectName('Explorer_tree_splitter')
        self.Explorer_tree_splitter.setContentsMargins(0, 0, 0, 0)
        self.Explorer_tree_splitter.setOrientation(Qt.Horizontal)
        self.scroll_area_processTree = QScrollArea(self)
        self.scroll_area_processTree.setObjectName('scroll_area_processTree')
        self.scroll_area_processTree.setWidgetResizable(True)
        self.scroll_area_processTree.setWidget(self.processTree)
        self.scroll_area_processTree.setMinimumWidth(0)
        self.scroll_area_processTree.setStyleSheet(scrollAreaStyle())
        self.scroll_area_binTree = QScrollArea(self)
        self.scroll_area_binTree.setObjectName('scroll_area_binTree')
        self.scroll_area_binTree.setWidgetResizable(True)
        self.scroll_area_binTree.setWidget(self.binTree)
        self.scroll_area_binTree.setMinimumWidth(0)
        self.scroll_area_binTree.setStyleSheet(scrollAreaStyle())
        self.Explorer_tree_splitter.addWidget(self.scroll_area_processTree)
        self.Explorer_tree_splitter.addWidget(self.scroll_area_binTree)
        self.stepButton_layout.addWidget(self.Explorer_tree_splitter)
        self.processTree_layout.addLayout(self.stepButton_layout)
        
        stretches=[0,0,0,0,1] #process bar, spacer, process action bar, bin action bar, trees
        for k,s in enumerate(stretches):
            self.processTree_layout.setStretch(k,s)
        
        self.Explorer_main_splitter=QSplitter(self)
        self.Explorer_main_splitter.setObjectName('Explorer_main_splitter')
        self.Explorer_main_splitter.setContentsMargins(0, 0, 0, 0)
        self.Explorer_main_splitter.setOrientation(Qt.Vertical)

        self.projectWidget=QWidget(self)
        self.projectWidget.setLayout(self.projectTree_layout)
        self.projectWidget.setMinimumHeight(150)

        self.processWidget=QWidget(self)
        self.processWidget.setLayout(self.processTree_layout)
        self.processWidget.setMinimumHeight(300)

        #self.scroll_area_sup = QScrollArea()
        #self.scroll_area_sup.setObjectName('scroll_area_sup')
        #self.scroll_area_sup.setWidgetResizable(True)
        #self.scroll_area_sup.setWidget(self.projectWidget)
        #self.scroll_area_sup.setMinimumHeight(150)
        #self.scroll_area_sup.setStyleSheet(scrollAreaStyle())
        #self.projectWidget.setMinimumHeight(250)

        #self.scroll_area_inf = QScrollArea()
        #self.scroll_area_inf.setObjectName('scroll_area_inf')
        #self.scroll_area_inf.setWidgetResizable(True)
        #self.scroll_area_inf.setWidget(self.processWidget)
        #self.scroll_area_inf.setMinimumHeight(300)
        #self.scroll_area_inf.setStyleSheet(scrollAreaStyle())
        #self.processWidget.setMinimumHeight(400)

        #self.main_splitter.addWidget(self.scroll_area_sup)
        #self.main_splitter.addWidget(self.scroll_area_inf)

        self.Explorer_main_splitter.addWidget(self.projectWidget)
        self.Explorer_main_splitter.addWidget(self.processWidget)

        self.Explorer_main_splitter.setHandleWidth(15)
        self.Explorer_main_splitter.setCollapsible(0, False)
        self.Explorer_main_splitter.setCollapsible(1, False)
        self.main_layout.addWidget(self.Explorer_main_splitter)   
        
        # Creazione del pulsante checkable
        self.binButton = QToolButton(self.processButtonBar)
        self.binButton.setIconSize(QSize(self.processButtonBar.buttonSize[0], self.processButtonBar.buttonSize[0]))
        self.binButton.setFixedSize(self.processButtonBar.buttonSize[1], self.processButtonBar.buttonSize[1])
        if self.processButtonBar.FlagInvisible:
            self.binButton.setCursor(Qt.CursorShape.PointingHandCursor)
            self.binButton.setStyleSheet("QToolButton { border: none; background: none;} QToolButton::menu-indicator { image: none; }")
            self.binButton.pressed.connect(lambda btn=self.binButton: btn.setStyleSheet("QToolButton { border: none; background: #dcdcdc;} QToolButton::menu-indicator { image: none; }"))
            self.binButton.released.connect(lambda btn=self.binButton: btn.setStyleSheet("QToolButton { border: none; background: none;} QToolButton::menu-indicator { image: none; }"))
        self.binButton.setToolTip('Deleted processes')
        self.binButton.setStatusTip('Deleted processes')
        self.processButtonBar.buttonLayout.addWidget(self.binButton)
        self.binIconOff=QIcon(''+ icons_path +'bin_off.png')
        self.binIconOn=QIcon(''+ icons_path +'bin_on.png')
        self.binButton.setCheckable(True)
        self.binButton.setChecked(False)  # Mostra l'albero 2 di default

        #------------------------------------- Declaration of parameters 
        self.ITEpar:ITEpar=self.TABpar
        self.ITEpar.FlagNone=False
        self.processTree.ITEpar=self.ITEpar
        self.TREpar=self.projectTree.TREpar
        self.processTree.TREpar=self.projectTree.TREpar
        self.binTree.TREpar=self.projectTree.TREpar
        self.widgets=widgets

        #------------------------------------- Callbacks
        self.currentTree=None
        self.binButton.clicked.connect(lambda: self.binButton_action(FlagTreeSelection=True))
        binShortCut=QShortcut(QKeySequence('Ctrl+B'),self)
        binShortCut.activated.connect(lambda:self.binButton.click())
        self.Explorer_tree_splitter.splitterMoved.connect(lambda: self.tree_splitter_action(FlagTreeSelection=True))

        self.projectTree.installEventFilter(self)
        self.projectTree.actionBar.installEventFilter(self)
        self.processTree.installEventFilter(self)
        self.binTree.installEventFilter(self)
        
        #self.processTree.currentItemChanged.connect(lambda: self.arrangeCurrentProcess(self.processTree))
        #self.binTree.currentItemChanged.connect(lambda: self.arrangeCurrentProcess(self.binTree))
        self.processTree.itemSelectionChanged.connect(lambda: self.processTree_item_selection(self.processTree))
        self.binTree.itemSelectionChanged.connect(lambda: self.processTree_item_selection(self.binTree))
        self.adjustProcessSelection=lambda: None
        self.binButton_action()
        #self.processTree_item_selection(self.processTree)
        
        self.projectTree.adjustSelection=self.adjustProjectSelection
        self.adjustProjectSelection()

        self.projectPageActions={}
        for k in projectPageButtons.keys():
            b:QPushButton=getattr(self.projectActionBar,'button_'+k)
            self.projectPageActions[k]=lambda butt=b: butt.click()

        self.processPageActions={}
        def processButtonAction(tree:ProcessTree,butt:DraggableButton):
                tree.createProcessItem(butt.buttonData['type'])
                item=tree.topLevelItem(tree.topLevelItemCount()-1)
                tree.setCurrentItem(item)
                self.processTree_item_selection(tree)
        for t,b in self.processButtonBar.buttons.items():
            b:DraggableButton
            b.buttonAction=self.processPageActions[t]=lambda tree=self.processTree, butt=b: processButtonAction(tree,butt)

        self.stepPage:StartingPage=None
        self.stepPageActions={}
        def stepButtonAction(butt:QToolButton, type):
            self.stepButton_action(butt, type)
        def stepPageAction(type):
            tree:ProcessTree=self.processTree if self.TREpar.tree==0 else self.binTree
            ITEs=self.ITEsfromTRE(self.TREpar)
            c=list(ITEs[0].children).index(type)
            ITE_chiild=ITEs[c+1]
            b:QPushButton=self.stepButtonBar.buttons[type]
            if b.isVisible() and b.isEnabled() and not ITE_chiild.active:
                b.click()
            elif ITE_chiild.active:
                item=tree.topLevelItem(self.TREpar.process)
                child=item.child(c)
                tree.setCurrentItem(child)
                self.processTree_item_selection(tree)
            else:
                showTip(self,'Current step is disabled! Please, reset the subsequemt step in the process to access it.')
        for t,b in self.stepButtonBar.buttons.items():
            b:QToolButton
            b.clicked.connect(lambda flag, butt=b, type=t: stepButtonAction(butt, type))
            self.stepPageActions[t]=lambda type=t: stepPageAction(type)
        
        self.processTree.editingFinished=lambda: self.arrangeCurrentProcess(self.processTree)
        self.binTree.editingFinished=lambda: self.arrangeCurrentProcess(self.binTree)
        self.inheritance=lambda: None
        self.undoInd=None
        return
            
    def binButton_action(self,FlagTreeSelection=True):
        w=self.Explorer_tree_splitter.width()
        if self.binButton.isChecked():
            self.Explorer_tree_splitter.setSizes([0, w])  
        else:
            self.Explorer_tree_splitter.setSizes([w, 0]) 
        self.tree_splitter_action(FlagTreeSelection)

    def tree_splitter_action(self,FlagTreeSelection=True):
        FlagProcessEnabled=self.Explorer_tree_splitter.sizes()[0]>0
        self.processTree.setEnabled(FlagProcessEnabled)
        for b in self.processButtonBar.buttons.values():
            b.setEnabled(FlagProcessEnabled)
        if not FlagProcessEnabled and FlagTreeSelection: 
            self.processTree.blockSignals(True)
            self.processTree.setCurrentItem(None)
            self.processTree.clearSelection()
            self.processTree.blockSignals(False)
            self.processTree_item_selection(self.binTree)
        FlagBinEnabled=self.Explorer_tree_splitter.sizes()[1]>0
        self.binTree.setEnabled(FlagBinEnabled)
        self.binButton.setChecked(FlagBinEnabled)
        self.binButton.setIcon(self.binIconOn if FlagBinEnabled else self.binIconOff)
        if not FlagBinEnabled and FlagTreeSelection: 
            self.binTree.blockSignals(True)
            self.binTree.setCurrentItem(None)
            self.binTree.clearSelection()
            self.binTree.blockSignals(False)
            self.processTree_item_selection(self.processTree)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.ShortcutOverride:
            event.accept()
            return True
        return super().eventFilter(obj, event)  

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_Return,Qt.Key.Key_Enter):
            if self.processTree.isEnabled():
                obj=self.processTree
            else:
                obj=self.binTree
            obj.setFocus()
        return super().keyPressEvent(event)
    
    def processTree_item_selection(self, tree:ProcessTree):
        self.currentTree=tree
        for indTree,t in enumerate([self.processTree,self.binTree]):
            if t==tree:
                index,child=self.arrangeCurrentProcess(tree)
                item=tree.currentItem()
                if item: item.setSelected(True)
                self.TREpar.tree=indTree
                self.TREpar.process=index
                self.TREpar.step=child
                if self.TREpar.project is not None:
                    self.projectTree.itemList[0][self.TREpar.project].copyfromfields(self.TREpar,['tree','process','step'])
                tree.setProcessActionButtonLayout()
                self.adjustProcessSelection()
                if self.TREpar.tree==0 and self.Explorer_tree_splitter.sizes()[0]==0:
                    self.binButton.setChecked(False)
                    self.binButton_action(FlagTreeSelection=False)
                if index is not None and index>=0:
                    if child:
                        self.selectStep()
                        #ITE:ITEpar=self.ITEfromTRE(self.TREpar)
                        #pri.Coding.green(f'Process tree selection --->\t {self.TREpar.project} {self.TREpar.tree} {self.TREpar.process} {self.TREpar.step-1 if self.TREpar.step else self.TREpar.step} \t {ITE.ind}')
                    else:
                        self.ITEpar.copyfrom(tree.itemList[0][index][child])
                        #pri.Coding.green(f'Process tree selection --->\t {self.TREpar.tree} {self.TREpar.process} {self.TREpar.step-1 if self.TREpar.step else self.TREpar.step}')
            else:
                t.actionBar.setVisible(False)
                t.blockSignals(True)
                t.clearSelection()
                t.blockSignals(False)

    def arrangeCurrentProcess(self, tree:ProcessTree):
        index=child=None
        item=tree.currentItem()
        if item:  
            self.stepButtonBar.show()
            if item.parent(): 
                child=item.parent().indexOfChild(item)+1
                item=item.parent()
            else:
                child=0
            index=tree.indexOfTopLevelItem(item)
            if index<0 or index>len(tree.itemList[0])-1:
                index=None
                return index, child
            ITEs=tree.itemList[0][index]
            for c in list(stepData):    
                b:QToolButton=self.stepButtonBar.buttons[c]
                lab:QLabel=self.stepButtonBar.labels[c]
                #b.label.setVisible(c in allData[0]['mandatory'])
                nsteps=len(ITEs[0].children)
                self.setProcessFlagRun(ITEs[0].ind)
                if c in ITEs[0].children:
                    ind=list(ITEs[0].children).index(c)
                    if c in ITEs[0].mandatory: ITEs[ind+1].active=True
                    if item.childCount()>ind:
                        item_child=item.child(ind)
                        item_child.setHidden(not ITEs[ind+1].active)
                    b.setVisible(c not in ITEs[0].mandatory) #b.setVisible(True)
                    lab.setVisible(c in ITEs[0].mandatory)
                    flagRunnable=all([ITEs[j].flagRun==0 for j in range(ind+2,nsteps+1)]) if ind<nsteps else True
                    flagRunnable=flagRunnable and ITEs[ind+1].flagRun==0 and ITEs[0].flagRun!=-2 #and len(ITEs[ind+1].link)==0
                    b.setEnabled(flagRunnable)
                    lab.setEnabled(flagRunnable)
                    b.setChecked(ITEs[ind+1].active)
                else:
                    flagRunnable=False
                    b.setVisible(False)
                    lab.setVisible(False)
                    b.setEnabled(False)
                    lab.setEnabled(False)
                    b.setChecked(False)
                b.setButtonIcon()
                if self.stepPage: 
                    self.stepPage.items[c].setVisible(c in ITEs[0].children) #and b.isChecked())
                    pageButton:QPushButton=self.stepPage.items[c].findChildren(QPushButton)[0]  
                    if flagRunnable:    
                        pageButton.setIcon(b.icon())
                    else:
                        pageButton.setIcon(b.iconOn)         
        else: 
            self.ITEpar.FlagNone=True
            self.hideStepButtons()
        return index, child
     
    def hideStepButtons(self):
        for c in list(stepData):
            b:QToolButton=self.stepButtonBar.buttons[c]
            lab:QLabel=self.stepButtonBar.labels[c]
            b.setVisible(False)
            lab.setVisible(False)

    def setProcessFlagRun(self,ind):
        ITEs:ITEpar=self.ITEsfromInd(ind)
        ITEs[0].flagRun=-2 if any([i.flagRun==-2 for i in ITEs[1:] if i.active]) else -1 if any([i.flagRun==-1 for i in ITEs[1:] if i.active]) else 2 if all([i.flagRun==2 for i in ITEs[1:] if i.active]) else 1 if all([i.flagRun>0 for i in ITEs[1:] if i.active]) else 0
        
    def selectStep(self):
        tree=[self.processTree,self.binTree][self.TREpar.tree]
        index=self.TREpar.process
        child=self.TREpar.step

        FlagVisible=[]
        FlagAdjustPar=None
        #tabAreaWidget=self.widgets[-1]
        #tabAreaWidget.scrollArea.splitter.hide()
        #tabAreaWidget.scrollArea.splitter.setFixedWidth(tabAreaWidget.scrollArea.splitter.splitterMaximumSize)
        self.ITEpar.copyfrom(tree.itemList[0][index][child])
        """
        indpar=[j for j in self.ITEpar.ind]
        for j in range(indpar[-2]):
            indpar[-2]=j
            self.inheritance(indpar)
        """
        i=None
        #FlagPrev=CAL.ind[-1]==len(self.w_Calibration.TABpar_prev_at(CAL.ind))-1
        FlagCalVi=False
        for k,w in enumerate(self.widgets):
            w:gPaIRS_Tab
            try:
                par:TABpar=tree.itemList[k+1][index][child-1][-1]
            except Exception as inst:
                pri.Error.red(f'[selectStep] Error while accessing the prev queues:\n{inst}')
                pass
            if w.TABname=='Calibration':
                flagVisible=par is not None
                FlagVisible.append(flagVisible)
                if w.buttonTab: w.buttonTab.setVisible(flagVisible)
                
                FlagCalVi=w.TABpar.FlagCalVi if flagVisible else False
                if hasattr(w,'logo_CalVi'): w.logo_CalVi.setVisible(FlagCalVi) 
                if hasattr(w,'button_Run_CalVi'): w.button_Run_CalVi.setVisible(FlagCalVi) 
            elif w.TABname!='TabArea':
                flagVisible=FlagCalVi if '_CalVi' in w.TABname else par is not None
                FlagVisible.append(flagVisible)
                if w.buttonTab: w.buttonTab.setVisible(flagVisible)
            else:
                for j,f in enumerate(FlagVisible):
                    if not f: par.FlagVisible[j]=f
            if par:
                w.TABpar.copyfrom(par)
                if FlagAdjustPar is None:
                    FlagAdjustPar=not par.FlagInit
                    i=k
            else:
                w.TABpar.FlagNone=True

        FlagAdjustPar=FlagAdjustPar or not self.ITEpar.FlagInit
        FlagBridge=True
        if i is not None: 
            #self.gui.setTABpars_at(self.ITEpar.ind,FlagAdjustPar,FlagBridge,widget=self.widgets[i])
            self.widgets[i].setTABpar(FlagAdjustPar,FlagBridge)
        #self.widgets[-1].setTABpar(FlagAdjustPar,FlagBridge)
        #self.widgets[-1].scrollArea.splitter.show()
        
    def stepButton_action(self,b,t):
        tree:ProcessTree=self.currentTree
        item=tree.currentItem()
        if item.parent(): 
            item=item.parent()
        r=tree.indexOfTopLevelItem(item)
        ITEs=tree.itemList[0][r]
        c=list(ITEs[0].children.keys()).index(b.buttonData['type'])
        child=item.child(c)
        if b.buttonData['type'] in ITEs[0].mandatory:
            tree.setCurrentItem(child)
            self.processTree_item_selection(tree)
            return
        ITE:ITEpar=ITEs[c+1]
        if len(ITE.link)>0:
            global FlagReturn
            FlagReturn=False
            def goToLinkedStep():
                global FlagReturn
                self.TREpar.process=ITE.link[2]
                if ITE.active:
                    self.TREpar.step=ITE.link[3]+1
                else: 
                    self.TREpar.step=0
                self.gui.adjustProjectSelection()
                FlagReturn=True
                return
            def unLink():
                global FlagReturn
                b.setChecked(ITE.active)
                self.gui.unlink_pars(ITE.ind)
                b.click()
                FlagReturn=True
                return
            addButton={
                'Unlink step': unLink,
                'Go to linked step': goToLinkedStep,
                }
            ITE0_master=self.ITEsfromInd(ITE.link)[0]
            linkInfo=f'linked to that of the process:\n\n{ITE0_master.ind[2]+1}: {ITE0_master.name}'
            warningDialog(self,f'The current {ITE.name} step is {linkInfo}.\n\nYou should either modify the step of the above process or unlink the current step from it.',addButton=addButton)
            if not FlagReturn: b.setChecked(ITE.active)
            return
        child.setHidden(not b.isChecked())
        ITE.active=b.isChecked()
        self.inheritance(ITE.ind)
        for dep in ITE.dependencies:
            ITE_dep:ITEpar=self.ITEfromInd(dep)
            ITE_dep.active=b.isChecked()
            item_dep=tree.topLevelItem(dep[2])
            child_dep=item_dep.child(c)
            child_dep.setHidden(not b.isChecked())
            self.gui.inheritance(dep)
        if self.stepPage: self.stepPage.items[t].setVisible(b.isChecked())
        FlagSettingPar=TABpar.FlagSettingPar
        TABpar.FlagSettingPar=True
        tree.clearSelection()
        TABpar.FlagSettingPar=FlagSettingPar
        if ITEs[c+1].active:
            tree.setCurrentItem(child)
            child.setSelected(True)
        else:
            tree.setCurrentItem(item)
            item.setSelected(True)
        return 
    
    def adjustProjectSelection(self):
        project=self.TREpar.project

        FlagHideStepButtons=False
        if project==None:
            self.processWidget.setEnabled(False)
            for k,tree in enumerate([self.processTree,self.binTree]):
                tree.blockSignals(True)
                tree.clearSelection()
                clean_tree(tree)
                tree.blockSignals(False)
            FlagHideStepButtons=True
        else:
            self.processWidget.setEnabled(True)
            
            #for w in self.widgets: w.TABpar_prev=[[],[]]
            item=None
            for k,tree in enumerate([self.processTree,self.binTree]):
                tree.itemList=[]
                for itemList in self.projectTree.itemList[1:]:
                    tree.itemList.append(itemList[project][k])
                """
                for w,prev in zip(self.widgets,tree.itemList[1:]):
                    w:gPaIRS_Tab
                    w.TABpar_prev[k]=prev
                    pass
                """
                tree.blockSignals(True)
                tree.clearSelection()
                clean_tree(tree)
                for i in range(len(tree.itemList[0])):
                    tree.createProcessItem(None,i,FlagNewItem=False)
                
                if self.TREpar.tree==k:
                    item=self.projectTree.topLevelItem(project)
                    self.projectTree.blockSignals(True)
                    self.projectTree.setCurrentItem(item)
                    item.setSelected(True)
                    self.projectTree.blockSignals(False)
                    self.projectTree.setButtonLayout()
                    self.ui.binButton.setChecked(k==1)
                    self.binButton_action(FlagTreeSelection=False)
                    if self.TREpar.process is not None: 
                        item=tree.topLevelItem(self.TREpar.process)
                        if item is None: 
                            self.TREpar.process=None
                            self.TREpar.step=None
                        if self.TREpar.step:
                            item=item.child(self.TREpar.step-1)
                    if item: 
                        tree.setCurrentItem(item)
                        item.setSelected(True)
                tree.blockSignals(False)
            if item:
                item.setSelected(True)
            else: FlagHideStepButtons=True
        if FlagHideStepButtons:
            for c in list(stepData):    
                b:QToolButton=self.stepButtonBar.buttons[c]
                b.setVisible(False)
                b.setChecked(False)
        return

    def ITEsfromTRE(self,TRE:TREpar):
        return self.projectTree.itemList[1][TRE.project][TRE.tree][TRE.process]
    
    def ITEsfromInd(self,ind:list):
        return self.projectTree.itemList[1][ind[0]][ind[1]][ind[2]]
    
    def ITEfromTRE(self,TRE:TREpar):
        return self.projectTree.itemList[1][TRE.project][TRE.tree][TRE.process][TRE.step]
    
    def ITEfromInd(self,ind:list):
        return self.projectTree.itemList[1][ind[0]][ind[1]][ind[2]][ind[3]+1]

    def cancelUndo(self,ind:list=None):
        if ind is None: 
            ind=[self.TREpar.project, self.TREpar.tree, self.TREpar.process, self.TREpar.step-1 if self.TREpar.step else -1, -1]
        if self.undoInd and self.undoInd[:-1]!=ind[:-1]:
            self.undoInd[-1]=-1
            if self.gui.checkProcesses(FlagInit=True,ind=self.undoInd):
                self.setITElayout(self.ITEfromInd(self.undoInd))
            self.undoInd=None

    def setITElayout(self,ITE:ITEpar=None):
        if ITE is None: 
            FlagCurrentITE=True
            ITE=self.ITEpar
        else: 
            FlagCurrentITE=False
        if ITE.FlagNone: return
        self.cancelUndo(ITE.ind)
        FlagDone=True
        warningMessage=''
        ITEs=self.ITEsfromInd(ITE.ind)
        #mandatory=ITEs[0].mandatory
        j=1
        while ITEs[j].Step!=ITE.Step and j<len(ITEs)-1:
            if ITEs[j].active and ITEs[j].OptionDone==0 and ITEs[j].Step in ITE.parents:
                FlagDone=False
                if warningMessage: warningMessage+='\n\n'
                warningMessage+='--- '+ITEs[j].name+' ---\n'+f'The completion of the step "{ITEs[j].name}" is needed for "{ITE.name}"'
            j+=1 
        for w in self.widgets:
            w:gPaIRS_Tab
            if FlagCurrentITE:
                TABpar_ind=w.TABpar
            else: 
                TABpar_ind:TABpar=w.TABpar_at(ITE.ind)
            if not TABpar_ind: continue
            if TABpar_ind.FlagNone: continue
            if w.TABname=='Calibration': 
                ITE.ncam=TABpar_ind.ncam
                ITE.progress=len(TABpar_ind.calList)
            if TABpar_ind.OptionDone==0: pass
            FlagDone=FlagDone and TABpar_ind.OptionDone!=0
            if not TABpar_ind.OptionDone==1 and not TABpar_ind.FlagNone:
                if TABpar_ind.warningMessage=='': continue
                if warningMessage: warningMessage+='\n\n'
                warningMessage+='--- '+w.TABname+' ---\n'+TABpar_ind.warningMessage
        if ITE.flagRun==0:
            if FlagDone: 
                if warningMessage:
                    ITE.warningMessage=warningMessage
                    ITE.label='running_warn'
                    ITE.OptionDone=-1
                else:
                    if ITE.Step!=StepTypes.cal:
                        ITE.warningMessage='Process step ready for running!'
                        ITE.OptionDone=1
                        ITE.label='running'
                    else:
                        ITE.warningMessage='Calibration files correctly identified!'
                        ITE.OptionDone=1
                        ITE.label='done'
            else: 
                if warningMessage: 
                    ITE.warningMessage=warningMessage
                    ITE.label='warning'
                else: 
                    ITE.warningMessage='Process step not yet initialized!'
                    ITE.label='uninitialized'
                ITE.OptionDone=0
        else:
            procdata:dataTreePar=self.ITEfromInd(ITE.ind).procdata
            #if hasattr(self.gui,'reset_step') and not os.path.exists(procdata.procOutName()) and not ITE.FlagInit:
            #    self.gui.reset_step(procdata.ind)
            #    return
            #ITE.progress=procdata.numFinalized
            if ITE.flagRun==-2:
                ITE.warningMessage='Process step currently running.'
                ITE.label='running'
            else:
                if not FlagDone:
                    ITE.warningMessage=f'The following issues are detected with the present step:\n{warningMessage}\n\nPlease, check if it is out-of-date!'
                    ITE.procdata.warnings[0]=ITE.procdata.headerSection('CRITICAL ERROR',ITE.warningMessage,'X') 
                    ITE.procdata.warnings[1]=''
                    ITE.procdata.setCompleteLog()
                    ITE.label='error'
                    ITE.OptionDone=0
                elif procdata.FlagErr:
                    ITE.warningMessage='Some errors occured in this process step! See Log for more information.'
                    ITE.label='error'
                elif ITE.flagRun==-1:
                    ITE.warningMessage='Process step stopped by user.'
                    ITE.label='paused'
                elif ITE.flagRun==-10:
                    ITE.warningMessage='Process step in the queue for execution.'
                    ITE.label='queue'
                else:
                    ITE.warningMessage='Process step correctly completed! 💪🏻'
                    ITE.label='done'

        if FlagCurrentITE:
            ITE:ITEpar=self.ITEfromInd(ITE.ind)
            ITE.copyfrom(self.ITEpar,exceptions=['procdata'])
        self.updateItemWidget(ITE)
        return

    def updateItemWidget(self,ITE:ITEpar):
        if self.TREpar.project==ITE.ind[0]:
            tree=[self.processTree,self.binTree][ITE.ind[1]]
            item:QTreeWidgetItem=tree.topLevelItem(ITE.ind[2])
            item=item.child(ITE.ind[3])
            TREind=[self.TREpar.project, self.TREpar.tree, self.TREpar.process, self.TREpar.step-1 if self.TREpar.step else -1, -1]
            if len(ITE.link)==0:
                if self.gui and ITE.flagRun==0 and len(self.gui.ui.tabAreaWidget.TABpar_prev_at(ITE.ind))<=1:
                    item.setIcon(0,self.processTree.uneditedIcon)
                elif self.gui and TREind[:-1]==ITE.ind[:-1] and self.gui.ui.tabAreaWidget.TABpar.ind[-1]<len(self.gui.w_Input.TABpar_prev_at(ITE.ind))-1:
                    item.setIcon(0,self.processTree.undoneIcon)
                    self.undoInd=self.gui.ui.tabAreaWidget.TABpar.ind
                else:
                    item.setIcon(0,QIcon())
            else:
                item.setIcon(0,self.processTree.linkedIcon)
            
            itemWidget:StepItemWidget=tree.itemWidget(item,1)

            ITE_ind=self.ITEfromInd(ITE.ind)
            itemWidget.setFromITE(ITE_ind)

    def updateSwitchMovies(self,ind,FlagStart=False):
        self.updateProjectSwitchMovie(ind,FlagStart)
        self.updateProcessSwitchMovie(ind,FlagStart)

    def updateProjectSwitchMovie(self,ind,FlagStart=False):
        if ind is None: return
        topLevelItem=self.projectTree.topLevelItem(ind[0])
        itemWidget=self.projectTree.itemWidget(topLevelItem,1)
        if itemWidget:
            switch:ModernSwitch=itemWidget.findChildren(ModernSwitch)[0]
            if switch:
                if FlagStart: switch.startTimer()
                else: switch.stopTimer()

    def updateProcessSwitchMovie(self,ind,FlagStart=False):
        if ind is None: return
        if self.TREpar.project==ind[0]:
            topLevelItem=self.processTree.topLevelItem(ind[2])
            itemWidget=self.processTree.itemWidget(topLevelItem,1)
            if itemWidget:
                switch:ModernSwitch=itemWidget.findChildren(ModernSwitch)[0]
                if switch:
                    if FlagStart: switch.startTimer()
                    else: switch.stopTimer()

class StartingPage(QFrame):
    ICON_SIZE = 65
    LAYOUT_SPACING = 20
    LAYOUT_MARGIN = 20
    ITEM_HEIGHT = 100
    NAME_LABEL_HEIGHT = 32
    TEXT_LAYOUT_SPACING = 1
    CAPTION_WIDTH = 350
    BUTTON_LAYOUT_TOP_MARGIN = 0

    dFontPixelSize_title=11
    TITLE_FONT_SIZE = fontPixelSize+dFontPixelSize_title
    NAME_FONT_SIZE = TITLE_FONT_SIZE-2
    CAPTION_FONT_SIZE = NAME_FONT_SIZE-2

    def __init__(self, title:str='', processes:dict={}, buttonBar:dict={}):
        super().__init__()
        if __name__ == "__main__":
            iconW = QIcon()
            iconW.addFile(u""+ icons_path +"logo_PaIRS.png", QSize(), QIcon.Normal, QIcon.Off)
            self.setWindowTitle(title)
            self.setWindowIcon(iconW)
        
        # ScrollArea
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)

        # Widget per contenere il layout principale
        container_widget = QFrame()
        container_widget.setObjectName('container')
        container_widget.setStyleSheet(f"""
                QFrame#container {{
                    border: 1px solid rgba(128, 128, 128, 0.5); 
                    border-radius: 15px;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(128, 128, 128, 0), stop:1 rgba(224, 224, 224, 0.25));
                    }}
                QWidget{{
                    background: transparent;
                }}
            """)

        # Layout principale verticale
        self.main_layout = QVBoxLayout(container_widget)
        self.main_layout.setSpacing(self.LAYOUT_SPACING)
        self.main_layout.setContentsMargins(self.LAYOUT_MARGIN, self.LAYOUT_MARGIN, self.LAYOUT_MARGIN, self.LAYOUT_MARGIN)

        # Label iniziale con font più grande
        self.title = QLabel(title)
        title_font = self.title.font()
        title_font.setBold(True)
        self.title.setFont(title_font)
        self.title.setAlignment(Qt.AlignLeft)
        self.title.setFixedHeight(self.NAME_LABEL_HEIGHT)
        self.main_layout.addWidget(self.title)

        self.scroll_area.setWidget(container_widget)
        self.scroll_area.setStyleSheet(scrollAreaStyle())
        layout = QVBoxLayout(self)
        layout.addWidget(self.scroll_area)
        self.setLayout(layout)

        self.setupPage(processes,buttonBar)
        
    def setObjectName(self,name:str):
        QFrame.setObjectName(self,name)
        self.scroll_area.setObjectName('scroll_area_'+self.objectName())
        return
    
    def setupPage(self, processes:dict={}, buttonBar:dict={}):
        if not len(processes): return
        button_margin=self.ITEM_HEIGHT-self.ICON_SIZE-self.BUTTON_LAYOUT_TOP_MARGIN
        CAPTION_HEIGHT=self.ITEM_HEIGHT-self.NAME_LABEL_HEIGHT-self.TEXT_LAYOUT_SPACING
        self.items={}
        # Itera sui dizionari nella lista
        for n, process in processes.items():
            # Layout orizzontale per ogni processo
            widget=QWidget()
            process_layout = QHBoxLayout(widget)
            process_layout.setSpacing(self.LAYOUT_SPACING)
            process_layout.setContentsMargins(0, 0, 0, 0)

            # Pulsante con icona
            button_layout = QHBoxLayout()
            button_layout.setSpacing(0)
            button_layout.setContentsMargins(0, self.BUTTON_LAYOUT_TOP_MARGIN, 0, button_margin)

            icon_button = QPushButton()
            pixmap = QPixmap(icons_path+process['icon']).scaled(self.ICON_SIZE, self.ICON_SIZE, mode=Qt.TransformationMode.SmoothTransformation)
            icon_button.setIcon(pixmap)
            icon_button.setIconSize(pixmap.size())
            icon_button.setFixedSize(self.ICON_SIZE, self.ICON_SIZE)
            icon_button.setStyleSheet("border: none; background: none;")
            icon_button.setCursor(Qt.PointingHandCursor)
            
            # Effetto dinamico al clic
            icon_button.pressed.connect(lambda btn=icon_button: btn.setStyleSheet("border: none; background: #dcdcdc;"))
            icon_button.released.connect(lambda btn=icon_button: btn.setStyleSheet("border: none; background: none;"))
            if buttonBar:
                def action(name):
                    return lambda: buttonBar[name]()
                icon_button.clicked.connect(action(n))

            button_layout.addWidget(icon_button)
            process_layout.addLayout(button_layout)

            # Layout verticale per nome e descrizione
            text_layout = QVBoxLayout()
            text_layout.setSpacing(self.TEXT_LAYOUT_SPACING)
            text_layout.setContentsMargins(0, 0, 0, 0)

            name_label = QLabel(process['name'])
            name_label.setObjectName('name_label')
            name_font = name_label.font()
            name_font.setPixelSize(self.NAME_FONT_SIZE)
            name_font.setBold(True)
            name_label.setFont(name_font)
            name_label.setAlignment(Qt.AlignLeft)
            name_label.setFixedHeight(self.NAME_LABEL_HEIGHT)
            text_layout.addWidget(name_label)

            caption_text_edit = QTextEdit(process['caption'])
            caption_text_edit.setObjectName('caption_text_edit')
            caption_font = caption_text_edit.font()
            caption_font.setPixelSize(self.CAPTION_FONT_SIZE)
            caption_text_edit.setFont(caption_font)
            caption_text_edit.setAlignment(Qt.AlignmentFlag.AlignJustify)
            caption_text_edit.setReadOnly(True)
            caption_text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            caption_text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            caption_text_edit.setFrameStyle(QFrame.NoFrame)
            #caption_text_edit.setFixedWidth(self.CAPTION_WIDTH)
            caption_text_edit.setStyleSheet("background: transparent;")
            caption_text_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

            # Adjust height to content
            caption_text_edit.document().setTextWidth(caption_text_edit.viewport().width())
            caption_text_edit.setFixedHeight(CAPTION_HEIGHT)#caption_text_edit.document().size().height())

            text_layout.addWidget(caption_text_edit)

            process_layout.addLayout(text_layout)

            # Spacer orizzontale che si espande
            #spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
            #process_layout.addSpacerItem(spacer)

            # Aggiungi il layout orizzontale al layout principale
            self.main_layout.addWidget(widget)

            self.items[n]=widget

        self.main_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding))

    def setFontPixelSize(self,fPixelSize):
        TITLE_FONT_SIZE = min([fPixelSize+self.dFontPixelSize_title,30])
        title_font = self.title.font()
        title_font.setPixelSize(TITLE_FONT_SIZE)
        title_font.setBold(True)
        self.title.setFont(title_font)

        NAME_FONT_SIZE = TITLE_FONT_SIZE-2
        for c in self.findChildren(QLabel,'name_label'):
            c:QLabel
            name_font = c.font()
            name_font.setPixelSize(NAME_FONT_SIZE)
            name_font.setBold(True)
            c.setFont(name_font)
        CAPTION_FONT_SIZE = NAME_FONT_SIZE-4
        for c in self.findChildren(QTextEdit,'caption_text_edit'):
            c:QLabel
            caption_font = c.font()
            caption_font.setPixelSize(CAPTION_FONT_SIZE)
            c.setFont(caption_font)         

if __name__ == "__main__":
    app = QApplication([])
    app.setStyle('Fusion')
    
    Explorer = PaIRS_Explorer()
    if FlagStartingPages:
        projectStartingPage=StartingPage("Select a project", projectPageButtons,Explorer.projectPageActions)
        processStartingPage=StartingPage("Select a process", processData,Explorer.processPageActions)
        stepStartingPage=StartingPage("Set up each step of the process", stepData,Explorer.stepPageActions)
        Explorer.stepPage=stepStartingPage

    Explorer.resize(500, 750)
    Explorer.move(0 if FlagStartingPages else 150, 150)
    Explorer.show()
    if FlagStartingPages:
        projectStartingPage.resize(500, 800)
        projectStartingPage.move(500, 150)
        projectStartingPage.show()
        projectStartingPage.setFontPixelSize(fontPixelSize)
        processStartingPage.resize(500, 800)
        processStartingPage.move(1000, 150)
        processStartingPage.show()
        processStartingPage.setFontPixelSize(fontPixelSize)
        stepStartingPage.resize(500, 800)
        stepStartingPage.move(1500, 150)
        stepStartingPage.show()
        stepStartingPage.setFontPixelSize(fontPixelSize)

    app.exec()


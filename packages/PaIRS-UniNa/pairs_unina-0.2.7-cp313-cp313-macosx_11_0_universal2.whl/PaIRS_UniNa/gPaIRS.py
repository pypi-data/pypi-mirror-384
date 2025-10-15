
from .ui_gPairs import *
from .ui_infoPaIRS import *
from .parForWorkers import *

from .TabTools import *
from .procTools import *
from .Explorer import *
from .Input_Tab import *
from .Output_Tab import *
from .Process_Tab import *
from .Log_Tab import *
from .Vis_Tab import *
from .Process_Tab_Min import *
from .Process_Tab_Disp import *
from .Calibration_Tab import *
from .Input_Tab_CalVi import *
from .Process_Tab_CalVi import *
from .Vis_Tab_CalVi import *
from .tabSplitter import *

from .ResizePopup import*
from .Whatsnew import*

from .gPalette import *

from .Saving_tools import*

import concurrent.futures

from .__init__ import __version__,__subversion__,__year__,__date__,__mail__,__website__

version=__version__
subversion=__subversion__
year=__year__
mail=__mail__
website=__website__
uicfg_version='0.2.0'
uicfg_version_to_load=uicfg_version
#uicfg_version_to_load='0.1.5'
Flag_fullDEBUG=False
FlagPrevPropagationTabSplitter=True

#********************************************* Additional windows (LEGACY)
class FloatingObject(QMainWindow):
    def closeEvent(self, event):
        self.hide()
        
    def __init__(self,parent,tab):
        super().__init__()
        if parent is None:
            self.gui=self.window()
        else:
            if hasattr(parent,'gui'):
                self.gui:gPaIRS=parent.gui
            else:
                self.gui:gPaIRS=parent.window()

        self.name=''
        self.button=None
        self.tab=tab
        self.setup()
        
    def setup(self):
        tab=self.tab
        if type(tab)==CollapsibleBox:
            self.setWindowTitle(tab.toggle_button.text())
            self.setWindowIcon(self.gui.windowIcon())
        elif isinstance(tab,Calibration_Tab) or any([isinstance(tab,t) for t in self.gui.tabTypes[1:]]):
            self.name=tab.ui.name_tab.text().replace(' ','')
            self.setWindowTitle(tab.ui.name_tab.text())
            self.setWindowIcon(tab.ui.icon.pixmap())
        else:
            self.setWindowTitle(self.gui.windowTitle())
            self.setWindowIcon(self.gui.windowIcon())
        if type(tab.parent()) in (QSplitter,QLayout,myQSplitter):
            self.lay:QLayout=tab.parent()
        else:
            self.lay:QLayout=tab.parent().layout()
        self.pa=tab
        self.index=self.lay.indexOf(tab)
        #self.setCentralWidget(tab)            

        self.setBaseSize(tab.baseSize())
        self.setAutoFillBackground(False) 
        self.setMinimumSize(tab.minimumSize())
        self.setMaximumSize(tab.maximumSize())
        
        #if self.name:
        #    self.button=getattr(self.gui.ui,'button_'+self.name)

    def setFloat(self):
        self.setCentralWidget(self.pa)
        self.centralWidget().setMinimumSize(self.pa.minimumSize())
        self.centralWidget().setMaximumSize(self.pa.maximumSize())

class FloatingWidget(FloatingObject):
    def closeEvent(self, event):
        index=min([self.index,self.lay.count()-1])
        self.lay.insertWidget(index,self.pa)
        self.close()
        i=self.gui.FloatingWindows.index(self)
        self.gui.FloatingWindows.pop(i)
        #self.gui.undockTabs()

    def __init__(self,parent,tab):
        super().__init__(parent,tab)

        geo=self.pa.geometry()
        geoP=self.gui.geometry()
        x=geoP.x()+int(geoP.width()*0.5)-int(geo.width()*0.5)
        y=geoP.y()+int(geoP.height()*0.5)-int(geo.height()*0.5)
        self.setGeometry(x,y,geo.width(),geo.height())
        self.setFloat()
        self.show()
            
class infoPaIRS(QMainWindow):
    def __init__(self,gui):
        super().__init__()
        ui=Ui_InfoPaiRS()
        ui.setupUi(self)
        self.ui=ui
        setupWid(self)
        
        subv=f"(.{subversion})" if int(subversion) else ""
        infotext=self.ui.info.text().replace('#.#.#',version+subv)
        infotext=infotext.replace('yyyy',year)
        infotext=infotext.replace('dddd/dd/dd',__date__)
        mailString=f'<a href="mailto:{mail}"><span style=" text-decoration: underline; color:#0000ff; font-size:11pt">{mail}</a>'
        infotext=infotext.replace('mmmm',mailString)
        websiteString=f'<a href="{website}"><span style=" text-decoration: underline; color:#0000ff; font-size:11pt">{website}</a>'
        infotext=infotext.replace('wwww',websiteString)
        self.ui.info.setText(infotext)
        if Flag_ISEXE:
            #self.ui.tabWidget.removeTab(3)
            self.ui.tabWidget.setTabText(3,'Packages')
            self.ui.req.setText(self.distPackages())
        else:
            self.ui.tabWidget.setTabText(3,'Requirements')
            self.ui.req.setText(self.requirements())
        
        self.fontPixelSize=gui.GPApar.fontPixelSize
        self.setFontSizeText()

        self.gui=gui
        for w in self.findChildren(QObject):
            if hasattr(w,'keyPressEvent'):
                def createKeyPressFun(w):
                    def KeyPressFun(e):
                        if w.hasFocus():
                            #pri.Info.yellow(w)
                            type(w).keyPressEvent(w,e)
                            #if not e.key() in self.gui.blockedKeys:
                            #    self.gui.keyPressEvent(e)
                    return KeyPressFun
                w.keyPressEvent=createKeyPressFun(w)

    def setFontSizeText(self):
        fPixSize=self.fontPixelSize
        setFontPixelSize(self,fPixSize)
        setFontSizeText(self.ui.info,[fPixSize+6,fPixSize*2])
        setFontSizeText(self.ui.info_uni,[fPixSize+4])
        setFontSizeText(self.ui.ger_cv,[fPixSize+1])
        setFontSizeText(self.ui.tom_cv,[fPixSize+1])
        setFontSizeText(self.ui.list_ref,[fPixSize+1])

    def distPackages(self):
        # Read the contents of the file and split by lines
        with open(rqrdpckgs_filename, 'r') as file:
            lines = file.readlines()

        # Introductory sentence
        intro_text = """
                <p style="font-size: 12pt; font-weight: normal; text-align: justify;">
                    Python packages included in the current executable:
                </p>
                <p>

                </p>
            """

        # Start the HTML table with improved styling
        html_table = intro_text + """
        <table border="1" style="width: 100%; align-items: center;">
                <thead>
                <tr>
                    <th style="padding: 10px; font-size: 11pt; font-weight: bold;">Package</th>
                    <th style="padding: 10px; font-size: 11pt; font-weight: bold;">Version</th>
                </tr>
            </thead>
            <tbody>
        """

        # Iterate over each line in the file
        for line in lines:
            # Split each line into package name, min vers11pt max version, and other info
            package_info = line.strip().split()
            
            # Ensure the line has the expected format
            if len(package_info) >= 3:
                package_name = package_info[0]
                if package_name[0]=='#': continue
                max_version = package_info[2]
                
                # Append a row to the HTML table
                html_table += f"""
                <tr>
                    <td style="padding: 10px; font-size: 11pt">{package_name}</td>
                    <td style="padding: 10px; font-size: 11pt">{max_version}</td>
                </tr>
                """

        # Close the table tags
        html_table += """
            </tbody>
        </table>
        """
        return html_table

    def requirements(self):
        # Read the contents of the file and split by lines
        with open(rqrdpckgs_filename, 'r') as file:
            lines = file.readlines()

        # Introductory sentence
        intro_text = """
                <p style="font-size: 12pt; font-weight: normal; text-align: justify;">
                    Required Python packages with their minimum and maximum supported versions:
                </p>
                <p>

                </p>
            """

        # Start the HTML table with improved styling
        html_table = intro_text + """
        <table border="1" style="width: 100%; align-items: center;">
                <thead>
                <tr>
                    <th style="padding: 10px; font-size: 11pt; font-weight: bold;">Package</th>
                    <th style="padding: 10px; font-size: 11pt; font-weight: bold;">Minimum version</th>
                    <th style="padding: 10px; font-size: 11pt; font-weight: bold;">Maximum version</th>
                    <th style="padding: 10px; font-size: 11pt; font-weight: bold;">Installed version</th>
                </tr>
            </thead>
            <tbody>
        """

        # Iterate over each line in the file
        for line in lines:
            # Split each line into package name, min vers11pt max version, and other info
            package_info = line.strip().split()
            
            # Ensure the line has the expected format
            if len(package_info) >= 3:
                package_name = package_info[0]
                if package_name[0]=='#': continue
                min_version = package_info[1]
                max_version = package_info[2]
                curr_version = package_info[3]
                
                # Append a row to the HTML table
                html_table += f"""
                <tr>
                    <td style="padding: 10px; font-size: 11pt">{package_name}</td>
                    <td style="padding: 10px; font-size: 11pt">{min_version}</td>
                    <td style="padding: 10px; font-size: 11pt">{max_version}</td>
                    <td style="padding: 10px; font-size: 11pt">{curr_version}</td>
                </tr>
                """

        # Close the table tags
        html_table += """
            </tbody>
        </table>
        """
        return html_table
    
#********************************************* GPaIRS
class gPaIRS(QMainWindow):

    def eventFilter(self, obj, event:QKeyEvent):
        # Check if the event is a KeyPress event
        if event.type() == QEvent.KeyPress:
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier and event.key() == Qt.Key.Key_F:
                    self.setDefaultSizes()
                    return True
                FlagSetFont=False
                if event.key() == Qt.Key.Key_0:
                    FlagSetFont=self.GPApar.fontPixelSize!=fontPixelSize
                    self.GPApar.fontPixelSize=fontPixelSize
                elif event.key() == Qt.Key.Key_1 or event.key() == Qt.Key.Key_Minus:
                    if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                        FlagSetFont=self.GPApar.fontPixelSize!=fontPixelSize_lim[0]
                        self.GPApar.fontPixelSize=fontPixelSize_lim[0]
                    else:
                        FlagSetFont=self.GPApar.fontPixelSize>fontPixelSize_lim[0]
                        if FlagSetFont: self.GPApar.fontPixelSize-=1
                elif event.key() == Qt.Key.Key_9 or event.key() == Qt.Key.Key_Plus:
                    if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                         FlagSetFont=self.GPApar.fontPixelSize!=fontPixelSize_lim[1]
                         self.GPApar.fontPixelSize=fontPixelSize_lim[1]
                    else:
                        FlagSetFont=self.GPApar.fontPixelSize<fontPixelSize_lim[1]
                        if FlagSetFont: self.GPApar.fontPixelSize+=1
                if FlagSetFont:
                    self.app.processEvents()
                    self.setFontPixelSize()
                    return True

        # Pass the event on to the parent class
        return super().eventFilter(obj, event)

    def resizeEvent(self,event):
        if self.FlagGeometryInit:
            self.FlagGeometryInit=False
        #self.setFontPixelSize()
        super().resizeEvent(event)
        #self.updateGPAparGeom()     

    def showEvent(self, event):
        super().showEvent(event)
        if event.type() == QEvent.Show:
            QTimer.singleShot(0, lambda: self.ui.tabAreaWidget.setSPLlayout())
            pass

    def closeEvent(self,event):
        if self.completingTask!=self.correctClose:
            self.pauseQuestion('quitting',self.correctClose,FlagFirstQuestion=True)
            event.ignore()
        return
    
    def correctClose(self):
        if self.pfPool: self.pfPool.closeParPool()
        print('\nClosing PaIRS...')
        self.save_last_workspace()
        self.closeAll()
        if self.GPApar.FlagOutDated:
            warningLatestVersion(self,self.app,flagExit=1,flagWarning=self.GPApar.FlagOutDated in (-1,1,-1000))
        self.close()
        self.app.processEvents()
        self.app.SecondaryThreads=self.SecondaryThreads
        self.app.quit()

    def closeAll(self):
        if hasattr(self,"FloatingTabs"):
            for w in self.FloatingTabs:
                w.close()
        if hasattr(self,"FloatingWindows"):
            for w in self.FloatingWindows:
                w.close()
    
    class gPaIRS_signals(QObject):
        killOrResetParForWorker=Signal(bool)#used to kill or reset he parForWorker
        progress=Signal(int)
        indProc=Signal(int)
        parPoolInit=Signal()
        guiInit=Signal()
        setMapVar=Signal()
        pause_proc=Signal()
        printOutDated=Signal()

    def __init__(self,flagDebug=False,app=None, standardPalette=None):
        self.app:QApplication=app
        self.name='PaIRS'
        self.flagSimpleFor=False # normally false, True only if you are checking the c library or the parpool therefore I have added a long print at the end of this function
        #todo gerardo spostare la stampa alla fine di tutto anche se ripetuta
        activateFlagDebug(flagDebug)
        self.PIVvers=PaIRS_lib.Version(PaIRS_lib.MOD_PIV).split('\n')[0]
        pri.Time.blue(2,f'gPaIRS init PaIRS-PIV {self.PIVvers}')
        super().__init__()

        #------------------------------------- Launching Parallel Pool
        self.previousPlotTime=time() #previous time for plotting
        self.FlagGeometryInit=True
        self.FlagOpenedWorkspace=False
        
        self.FlagGuiInit=False
        self.signals=self.gPaIRS_signals()
        #self.numUsedThreadsPIV=NUMTHREADS_MAX #now is called numMaxProcs
        
        self.numMaxProcs=NUMTHREADS_MAX #number of cores that the user has selected should be larger than numUsedProcs*numPivOmpCores
        self.numUsedProcs=NUMTHREADS_MAX #number of  really used processor (Threads parfor)
        self.numPivOmpCores=1 # number of PIV internal cores used by omp
        
        self.FlagParPoolInit=False
        self.launchParPool(NUMTHREADS_MAX)
        
        self.procdata:dataTreePar=None
        self.currind:list=None
        #self.numProcOrErrTot=0  # at the end should be equal to the number of images to be processed
        self.numCallBackTotOk=0 # Callbacks that are relative to a normal termination 
        self.SecondaryThreads=[]

        self.FlagPackIssue=False

        #------------------------------------- Graphical interface: widgets
        ui=Ui_gPairs()
        ui.setupUi(self)
        self.ui=ui
        self.ui.button_Run.setVisible(False)
        self.ui.button_Run.setEnabled(False)
        
        self.buttonSizeCallbacks=[]
        def createCallback(k):
            return lambda: self.setPresetSizes(k)
        for k in range(6):
            self.buttonSizeCallbacks.append(createCallback(k))
        #self.ResizePopup=ResizePopup(self.buttonSizeCallbacks)
        self.ResizePopup=None
    
        self.cfgname=lastcfgname
        self.FlagHappyLogo=False
        self.setupLogo()

        self.GPApar_old=GPApar()
        self.GPApar=GPApar()
        self.GPApar.NumCores=self.numMaxProcs
        self.TABpar=self.GPApar

        pri.Time.blue(2,f'gPaIRS inizio generazione tabs')
        self.defineTabs()
        self.defineMenuActions()
        self.ui.title_workspace.updateLabel=self.updateWorkspaceTitle

        setupWid(self) #---------------- IMPORTANT
        self.setFurtherFontPixelSizes(fontPixelSize)
        
        pri.Time.blue(2,f'gPaIRS fine generazione tabs')

        #for the keyboard shortcut
        """
        self.FlagKeyCallbackExec=False
        self.blockedKeys=[Qt.Key.Key_Up,Qt.Key.Key_Down,Qt.Key.Key_Left,Qt.Key.Key_Right]
        for w in self.findChildren(QObject):
            if hasattr(w,'keyPressEvent'):
                def createKeyPressFun(w):
                    def KeyPressFun(e):
                        if w.hasFocus():
                            #pri.Info.yellow(w)
                            if not self.FlagKeyCallbackExec:
                                self.FlagKeyCallbackExec=True
                                type(w).keyPressEvent(w,e)
                            if not e.key() in self.blockedKeys:
                                self.keyPressEvent(e)
                            self.FlagKeyCallbackExec=False
                    return KeyPressFun
                w.keyPressEvent=createKeyPressFun(w)
        """
        self.ui.spin_nworkers.setValue(self.numMaxProcs)
        self.ui.spin_nworkers.setMinimum(1)
        self.ui.spin_nworkers.setMaximum(NUMTHREADS_MAX)
        self.ui.spin_nworkers.valueChanged.connect(self.spin_nworkers_action)

        self.ui.button_pause.hide()
        self.ui.w_progress_Proc.hide()

        #for positioning and resizing
        #window=QWindow()
        #window.showMaximized()
        #self.maximumGeometry=window.geometry()
        #window.close()
        self.maximumGeometry=self.app.primaryScreen().geometry()
        
        self.minW=self.minimumWidth()
        self.maxW=self.maximumGeometry.width()
        self.ui.Explorer.setMinimumWidth(0)
        margins=self.ui.centralLayout.contentsMargins()
        self.minW_ManTabs=self.minimumWidth()-margins.left()-margins.right()

        self.splash=None
        
        #------------------------------------- Graphical interface: miscellanea
        self.flaticon_PaIRS_download=QIcon()
        self.flaticon_PaIRS_download.addFile(icons_path+'flaticon_PaIRS_download.png')
        self.flaticon_PaIRS_download_warning=QIcon()
        self.flaticon_PaIRS_download_warning.addFile(icons_path+'flaticon_PaIRS_download_warning.png')
        self.flaticon_PaIRS_beta=QIcon()
        self.flaticon_PaIRS_beta.addFile(icons_path+'flaticon_PaIRS_beta.png')

        self.icon_play=QIcon()
        self.icon_play.addFile(u""+ icons_path +"play.png", QSize(), QIcon.Normal, QIcon.Off)
        self.icon_pause=QIcon()
        self.icon_pause.addFile(u""+ icons_path +"pause.png", QSize(), QIcon.Normal, QIcon.Off)
        self.icon_save_and_stop=QIcon()
        self.icon_save_and_stop.addFile(u""+ icons_path +"save_and_stop.png", QSize(), QIcon.Normal, QIcon.Off)

        self.ui.tabAreaWidget.icon_link=QIcon()
        self.ui.tabAreaWidget.icon_link.addFile(u""+ icons_path +"link.png", QSize(), QIcon.Normal, QIcon.Off)
        self.ui.tabAreaWidget.icon_unlink=QIcon()
        self.ui.tabAreaWidget.icon_unlink.addFile(u""+ icons_path +"unlink.png", QSize(), QIcon.Normal, QIcon.Off)

        self.updating_import_gif = QMovie(u""+ icons_path +"updating_import.gif")
        self.updating_import_gif.setScaledSize(self.ui.label_updating_import.size())
        #self.ui.label_updating_import.setScaledContents(True)     
        self.updating_import_gif.start()
        self.ui.label_updating_import.setMovie(self.updating_import_gif)
        self.ui.label_updating_import.setVisible(False)

        self.updating_pairs_gif = QMovie(u""+ icons_path +"updating_pairs.gif")
        self.updating_pairs_gif.setScaledSize(self.ui.label_updating_pairs.size())
        #self.ui.label_updating_pairs.setScaledContents(True)     
        self.updating_pairs_gif.start()
        self.ui.label_updating_pairs.setMovie(self.updating_pairs_gif)
        self.ui.label_updating_pairs.setVisible(False)

        self.runningMovie = QMovie(icons_path+'running.gif')
        self.runningMovie.setScaledSize(QSize(StepItemWidget.label_size,StepItemWidget.label_size))
        self.runningMovie.start()

        self.gearMovie = QMovie(icons_path+'gear.gif')
        self.gearMovie.setScaledSize(QSize(StepItemWidget.label_size,StepItemWidget.label_size))
        self.gearMovie.start()
        
        self.palettes=[lightPalette(),darkPalette(),standardPalette]
        self.paletteNames=['Light','Dark','System']
        #self.ui.logo.contextMenuEvent=self.paletteContextMenuEvent
        self.ui.button_colormode.mousePressEvent=self.paletteContextMenuEvent
        self.ui.button_packissue.mousePressEvent=lambda e: checkRequiredPackages(self,FlagDisplay=True)
        self.ui.logo.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.ui.logo.mousePressEvent=lambda e: self.about()
        #self.ui.logo.mousePressEvent=self.paletteContextMenuEvent
        #cursor_lamp_pixmap=QtGui.QPixmap(''+ icons_path +'cursor_lamp.png').scaled(QSize(24,24), Qt.KeepAspectRatio)
        #cursor_lamp = QtGui.QCursor(cursor_lamp_pixmap,-1,-1)
        #self.ui.logo.setCursor(cursor_lamp)

        self.aboutDialog=None
        self.logChanges:Log_Tab=None
        self.whatsNew=lambda: whatsNew(self)
        
        self.ui.button_PaIRS_download.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ui.button_PaIRS_download.setVisible(False)
        self.signals.printOutDated.connect(self.setButtonDownload)

        self.fontPixelSize=fontPixelSize
        self.setDefaultSizes()

        self.ui.title_workspace.bullet=GPApar().saveBullet()

        #------------------------------------- Declaration of parameters 
        self.PaIRS_threadpool=QThreadPool()
        if NUMTHREADS_gPaIRS:
            self.PaIRS_threadpool.setMaxThreadCount(NUMTHREADS_gPaIRS)

        self.FlagRun=0
        self.procWorkers=[]
        self.contProc=self.nProc=0
        self.procdata=None
        self.FlagResetPlot=False
        self.FlagProcInit=False
        self.FlagProcPlot=False
        self.procFields=['numProcOrErrTot','Log','list_print','list_pim','numCallBackTotOk','numFinalized','flagRun','flagParForCompleted']
        self.namesPIV=NamesPIV()
        
        #self.defineFloatings()
        self.FloatingTabs=[]
        self.FloatingWindows=[]
        
        self.menuDebug=None
        self.completingTask=None
        self.waitingDialog=None

        #------------------------------------- Callbacks 
        self.ui.Explorer.adjustProcessSelection=self.adjustProcessSelection
        self.ui.Explorer.projectTree.adjustSelection=self.adjustProjectSelection
        self.projectTree.editingFinished=self.adjustProcessSelection
        self.processTree.editingFinished=lambda: self.editingFinished(self.processTree)
        self.binTree.editingFinished=lambda: self.editingFinished(self.binTree)

        self.ui.button_Run.clicked.connect(self.button_run_pause_action)
        self.ui.button_pause.clicked.connect(self.button_run_pause_action)

        self.ui.workspace_icon.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.ui.workspace_icon.pressed.connect(lambda btn=self.ui.workspace_icon: btn.setStyleSheet("border: none; background: #dcdcdc;"))
        self.ui.workspace_icon.released.connect(lambda btn=self.ui.workspace_icon: btn.setStyleSheet("border: none; background: none;"))
        pixmap_workspace=QPixmap(icons_path+'workspace.png')
        self.ui.workspace_icon.clicked.connect(lambda: self.warningDialog(self.GPApar.InfoMessage(),pixmap=pixmap_workspace,title='Workspace information'))

        self.currITEpar=self.TREpar
        self.ui.title_icon.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.ui.title_icon.pressed.connect(lambda btn=self.ui.title_icon: btn.setStyleSheet("border: none; background: #dcdcdc;"))
        self.ui.title_icon.released.connect(lambda btn=self.ui.title_icon: btn.setStyleSheet("border: none; background: none;"))
        pixmap_workspace=QPixmap(icons_path+'workspace.png')
        self.ui.title_icon.clicked.connect(lambda: self.warningDialog(self.currITEpar.InfoMessage(),pixmap=TreeIcons.pixmaps[self.currITEpar.icon],title=f"{self.currITEpar.basename} information"))

        class RCLbar:
            buttons={0: self.ui.button_reset_step,
                     1: self.ui.button_step_inherit,
                     2: self.ui.button_copy_step,
                     3: self.ui.button_link_step}
            buttonData={0: {'name': 'Reset step'}, 
                        1: {'name': 'Copy input/output data from...'}, 
                        2: {'name': 'Copy step from...'}, 
                        3: {'name': 'Link step to...'}}
        self.RCLbar=RCLbar()
        self.ui.Explorer.processActionBar.additionalButtonBars['items'].append(self.RCLbar)

        self.installEventFilter(self)

        #------------------------------------- Initialization
        from .PaIRS_pypacks import basefold
        basefold=myStandardPath(basefold)
        self.initialize()

        #------------------------------------- Debug
        self.addDebugMenu()
        self.menuDebug.setFont(self.ui.menuFile.font())
        self.menuDebug.menuAction().setVisible(Flag_DEBUG)
        self.userDebugShortcut = QShortcut(QKeySequence('Shift+Alt+D'), self)
        self.userDebugShortcut.activated.connect(self.userDebugMode)
        self.developerDebugShortcut = QShortcut(QKeySequence('Alt+D, Alt+E, Alt+B, Alt+Return'), self)
        self.developerDebugShortcut.activated.connect(lambda:self.setDebugMode(True))
        #self.exitDebugShortcut = QShortcut(QKeySequence('Shift+Alt+D'), self)
        #self.exitDebugShortcut.activated.connect(lambda:self.setDebugMode(False))
        self.setDebugMode(flagDebug)# should be put not upper than here
        pri.Time.blue(0,'dopo setupUi')
        self.FlagClosing=[False]
        #self.setupPathCompleter()

        self.FlagGuiInit=True
        self.load_gif = QMovie(u""+ icons_path +"loading_2.gif")
        self.load_gif.start()
        self.loaded_map=QPixmap(u""+ icons_path + "loaded.png")
        self.parPoolInitSetup()
        #todo gerardo spostare questa  stampa alla fine di tutto anche se ripetuta
        if self.flagSimpleFor:print('\n\n\n\n\n\nflagSimplefor=True \nAre you really working with the c library?\n\n\n\n\n\n\n\n')
        pri.Time.blue(0,'fine di tutto init')

    def initialize(self):
        pri.Info.yellow('||| Initializing gPaIRS |||')
        if os.path.exists(lastcfgname):
            self.open_workspace(filename=lastcfgname,FlagSetGeometry=True)
            self.GPApar_old.copyfrom(self.GPApar)   
        else:
            self.adjustProjectSelection()  
            self.setGPaIRSPalette()          
        return

    def disableDropping(self,FlagDisableed=True):
        self.projectTree.setDragEnabled(not FlagDisableed)
        self.processTree.setDragEnabled(not FlagDisableed)

    def setSwitchEnabled(self,FlagEnabled=True):
        for k in range(len(self.projectTree.itemList[0])):
            topLevelItem=self.projectTree.topLevelItem(k)
            itemWidget=self.projectTree.itemWidget(topLevelItem,1)
            if itemWidget:
                switch:ModernSwitch=itemWidget.findChildren(ModernSwitch)[0]
                if switch:
                    switch.setEnabled(FlagEnabled)
        for k in range(self.processTree.topLevelItemCount()):
            topLevelItem=self.processTree.topLevelItem(k)
            itemWidget=self.processTree.itemWidget(topLevelItem,1)
            if itemWidget:
                switch:ModernSwitch=itemWidget.findChildren(ModernSwitch)[0]
                if switch: 
                    switch.setEnabled(FlagEnabled)
        
    def setButtonRunVisible(self):
        FlagButtonRun=any([tre.FlagRunnable and tre.FlagQueue for tre in self.projectTree.itemList[0]])
        if not FlagButtonRun:
            self.ui.button_Run.setVisible(False)
            self.ui.button_pause.setVisible(False)
            self.ui.w_progress_Proc.setVisible(False)
            self.ui.progress_Proc.setValue(0)
            self.ui.time_stamp.setText('Initializing...')
        else:
            FlagButtonRun=self.ui.progress_Proc.value() in (0,self.ui.progress_Proc.maximum()) and self.FlagRun==0
            self.ui.button_Run.setVisible(FlagButtonRun)
            self.ui.button_pause.setVisible(not FlagButtonRun)
            self.ui.w_progress_Proc.setVisible(not FlagButtonRun)
        self.ui.tabAreaWidget.display_controls()
    
    def editingFinished(self,tree):
        self.ui.Explorer.arrangeCurrentProcess(tree)
        self.adjustProcessSelection()

    def defineFloatings(self):
        self.FloatingTabs=[]
        for wid in self.tabWidgets[:-1]:
            self.FloatingTabs.append(FloatingObject(self,wid))
        self.GPApar.FloatGeometry.append(self.geometry())
        self.GPApar.FloatingsVis.append(self.isVisible())

#********************************************* TAB definitions
    def defineTabs(self):
        self.w_Input    = Input_Tab(self,False)
        pri.Time.magenta('Input')
        self.w_Output   = Output_Tab(self,False)
        pri.Time.magenta('Output')
        self.w_Process  = Process_Tab(self,False)
        pri.Time.magenta('Process')
        self.w_Log      = Log_Tab(self,False)
        pri.Time.magenta('Log')
        self.w_Vis      = Vis_Tab(self,False)
        pri.Time.magenta('Vis')
        self.w_Process_Min    = Process_Tab_Min(self,False)
        pri.Time.magenta('Process_Min')
        self.w_Process_Disp   = Process_Tab_Disp(self,False)
        pri.Time.magenta('Process_Disp')
        self.w_Calibration    = Calibration_Tab(self,False)
        pri.Time.magenta('Calibration')
        self.w_Input_CalVi    = Input_Tab_CalVi(self,False)
        pri.Time.magenta('Input_CalVi')
        self.w_Process_CalVi  = Process_Tab_CalVi(self,False)
        pri.Time.magenta('Process_CalVi')
        self.w_Vis_CalVi      = Vis_Tab_CalVi(self,False)
        pri.Time.magenta('Vis_CalVi')
        self.tabWidgets=[ self.w_Calibration,
                          self.w_Input,self.w_Input_CalVi,
                          self.w_Output,
                          self.w_Process,self.w_Process_Min,self.w_Process_Disp,self.w_Process_CalVi,
                          self.w_Log,
                          self.w_Vis,self.w_Vis_CalVi  ]
        self.tabTypes=[type(w) for w in self.tabWidgets]
        pri.Time.blue(2,f'gPaIRS generazione tabs')

        icons=[w.TABname.split('_')[0].lower()+'_logo' for w in self.tabWidgets]
        self.ui.tabAreaWidget.setupTabArea(self.tabWidgets,icons)
        self.ui.tabAreaWidget.gui=self
        self.tabWidgets=self.tabWidgets+[self.ui.tabAreaWidget]
        self.tabNames=[tab.TABname for tab in self.tabWidgets]

        self.w_Input.ui.imTreeWidget.disableTab=self.disableTab_ImTree

        self.ui.projectPage.ITEM_HEIGHT=80
        self.ui.projectPage.title.setText("Select a project")
        self.ui.projectPage.setupPage(projectPageButtons,self.ui.Explorer.projectPageActions)
        self.ui.processPage.title.setText("Select a process")
        self.ui.processPage.setupPage(processData,self.ui.Explorer.processPageActions)
        self.ui.stepPage.title.setText("Set up each step of the process")
        self.ui.stepPage.setupPage(stepData,self.ui.Explorer.stepPageActions)
        self.ui.Explorer.stepPage=self.ui.stepPage
        
        self.projectTree=self.ui.Explorer.projectTree
        self.processTree=self.ui.Explorer.processTree
        self.binTree=self.ui.Explorer.binTree
        self.TREpar=self.ui.Explorer.TREpar

        self.ui.Explorer.gui=self
        self.projectTree.gui=self
        self.processTree.gui=self
        self.binTree.gui=self

        for w in self.tabWidgets:
            w:gPaIRS_Tab
            w.TABpar_prev=[]
        self.processTree.itemList=[]
        self.binTree.itemList=[]

        self.ui.Explorer.widgets=self.tabWidgets
        self.projectTree.setupWidgets(self.tabWidgets)
        self.processTree.setupWidgets(self.tabWidgets)
        self.binTree.setupWidgets(self.tabWidgets)

        self.projectTree.modifyWorkspace=self.modifyWorkspace
        self.projectTree.adjustSwitches=self.adjustSwitches
        self.processTree.adjustSwitches=self.adjustSwitches
        self.projectTree.signals.updateLists.connect(self.updateWorkspace)
        self.processTree.signals.updateLists.connect(self.updateProjectItemWidget)

        #self.ui.button_back.hide()
        #self.ui.button_forward.hide()

        self.ui.w_header.layout().removeWidget(self.ui.logo_CalVi)
        self.ui.w_header.layout().removeWidget(self.ui.button_Run_CalVi)
        self.ui.w_header.layout().removeWidget(self.ui.button_Abort_CalVi)
        self.ui.tabAreaWidget.buttonBar_layout.addWidget(self.ui.logo_CalVi)
        self.ui.tabAreaWidget.buttonBar_layout.addWidget(self.ui.button_Run_CalVi)
        self.ui.tabAreaWidget.buttonBar_layout.addWidget(self.ui.button_Abort_CalVi)
        self.ui.button_Run_CalVi.setFixedHeight(TabAreaWidget.buttonSize[1])
        self.ui.button_Abort_CalVi.setFixedHeight(TabAreaWidget.buttonSize[1])
        self.ui.tabAreaWidget.buttonBar.setMaximumHeight(TabAreaWidget.buttonSize[1])

        self.ui.logo_CalVi.setVisible(False)
        self.ui.button_Run_CalVi.setVisible(False)
        self.ui.button_Abort_CalVi.setVisible(False)
        self.ui.button_Run_CalVi.clicked.connect(self.runCalVi)
        self.ui.button_Abort_CalVi.clicked.connect(self.abortCalVi)
        self.w_Input_CalVi.setRunCalViButtonText=lambda: self.setRunCalViButtonText(False)
        setattr(self.w_Calibration,'logo_CalVi',self.ui.logo_CalVi)
        setattr(self.w_Calibration,'button_Run_CalVi',self.ui.button_Run_CalVi)

        for w in self.tabWidgets:
            w:gPaIRS_Tab
            w.FlagDisplayControls=False
        self.w_Input.ui.w_Mode.layout().removeWidget(self.w_Input.ui.button_back)
        self.w_Input.ui.w_Mode.layout().removeWidget(self.w_Input.ui.button_forward)
        self.w_Input.ui.button_back.clicked.disconnect()
        self.w_Input.ui.button_forward.clicked.disconnect()
        self.w_Input.display_controls=lambda:None

        self.ui.w_header.layout().removeWidget(self.ui.button_restore_undo)
        self.ui.tabAreaWidget.buttonBar_layout.addWidget(self.ui.button_restore_undo)
        self.ui.button_restore_undo.setFixedWidth(TabAreaWidget.buttonSize[1])
        self.ui.button_restore_undo.setFixedHeight(TabAreaWidget.buttonSize[1])
        self.ui.button_restore_undo.clicked.connect(self.fullCallback)
        self.ui.tabAreaWidget.ui.button_restore_undo=self.ui.button_restore_undo

        self.ui.tabAreaWidget.FlagDisplayControls=True
        self.ui.tabAreaWidget.ui.button_back=self.w_Input.ui.button_back
        self.ui.tabAreaWidget.ui.button_back.clicked.connect(lambda: self.button_back_forward_action(-1))
        self.ui.tabAreaWidget.ui.button_back.contextMenuEvent=lambda e: self.bfContextMenu(-1,e)

        self.ui.tabAreaWidget.ui.button_forward=self.w_Input.ui.button_forward
        self.ui.tabAreaWidget.ui.button_forward.clicked.connect(lambda: self.button_back_forward_action(+1))
        self.ui.tabAreaWidget.ui.button_forward.contextMenuEvent=lambda e: self.bfContextMenu(+1,e)

        self.onlyReadLabel=QLabel('Read-Only')
        font=self.onlyReadLabel.font()
        font.setBold(True)
        font.setItalic(True)
        font.setPixelSize(fontPixelSize)
        self.onlyReadLabel.setFont(font)
        self.onlyReadLabel.setStyleSheet('color: rgb(51, 102, 255)')  #('color: rgb(255,51,51);')
        #self.ui.tabAreaWidget.buttonBar_layout.addWidget(self.onlyReadLabel)
        self.ui.tabAreaWidget.onlyReadLabel=self.onlyReadLabel
        self.ui.tabAreaWidget.button_reset_step=self.ui.button_reset_step
        self.ui.tabAreaWidget.button_step_inherit=self.ui.button_step_inherit
        self.ui.tabAreaWidget.button_copy_step=self.ui.button_copy_step
        self.ui.tabAreaWidget.button_link_step=self.ui.button_link_step

        self.w_RCL = QWidget(self)  #CLR: copy, link, reset
        self.RCL_layout = QHBoxLayout()
        self.RCL_layout.setContentsMargins(0, 0, 0, 0)
        self.RCL_layout.setSpacing(actionButtonSpacing*2)
        self.w_RCL.setLayout(self.RCL_layout)

        self.RCL_layout.addSpacerItem(QSpacerItem(projectActionButtonSize[1], projectActionButtonSize[1], QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.RCL_layout.addWidget(self.onlyReadLabel)
        self.RCL_layout.addSpacerItem(QSpacerItem(5, projectActionButtonSize[1], QSizePolicy.Minimum, QSizePolicy.Minimum))
        for b in [self.ui.button_reset_step,self.ui.button_step_inherit,self.ui.button_copy_step,self.ui.button_link_step]:
            self.ui.w_header.layout().removeWidget(b)
            #self.ui.tabAreaWidget.buttonBar_layout.addWidget(b)
            #b.setFixedSize(TabAreaWidget.buttonSize[1],TabAreaWidget.buttonSize[1])
            #b.setIconSize(QSize(TabAreaWidget.buttonSize[1]-8,TabAreaWidget.buttonSize[1]-8))
            self.RCL_layout.addWidget(b)
            b.setFixedSize(projectActionButtonSize[1],projectActionButtonSize[1])
            b.setIconSize(QSize(projectActionButtonSize[0],projectActionButtonSize[0]))
            if hasattr(self,b.objectName()+'_action'):
                b.clicked.connect(getattr(self,b.objectName()+'_action'))
        self.ui.Explorer.processTree_layout.addWidget(self.w_RCL)

        self.w_Input.ui.button_back.setFixedSize(TabAreaWidget.buttonSize[1],TabAreaWidget.buttonSize[1])
        self.w_Input.ui.button_back.setIconSize(QSize(TabAreaWidget.buttonSize[1]-2,TabAreaWidget.buttonSize[1]-2))
        self.w_Input.ui.button_forward.setFixedSize(TabAreaWidget.buttonSize[1],TabAreaWidget.buttonSize[1])
        self.w_Input.ui.button_forward.setIconSize(QSize(TabAreaWidget.buttonSize[1]-2,TabAreaWidget.buttonSize[1]-2))
        self.ui.tabAreaWidget.buttonBar_layout.addWidget(self.w_Input.ui.button_back)
        self.ui.tabAreaWidget.buttonBar_layout.addWidget(self.w_Input.ui.button_forward)
        
        self.ui.tabAreaWidget.FlagPrevPropagation=FlagPrevPropagationTabSplitter
        self.ui.Explorer.inheritance=self.inheritance

        self.brush_icon=QIcon(icons_path+"brush_cursor.png")
        self.w_Vis.ui.icon.addfuncclick['copy_VIS']=lambda: self.copy_link_action(self.w_Vis.ui.name_tab,lambda isl,ima: self.copy_VIS(isl,ima),menuTitle='Copy graphical settings from...',icon=self.brush_icon)
        self.w_Vis.ui.icon.setCustomCursor()

        self.defineTABbridges()

        for c in self.findChildren(PaIRSTree):
            c:PaIRSTree
            c.gui=self
    
    def fullCallback(self):
        for w in self.tabWidgets:
            w:gPaIRS_Tab
            TABpar_ind=w.TABpar_at(w.TABpar.ind[:-1]+[-1])
            if TABpar_ind:
                if w.TABpar.isDifferentFrom(TABpar_ind,exceptions=w.TABpar.unchecked_fields+['ind']):
                    w.TABpar.ind[-1]=-1
                    w.fullCallback('Restored configuration')
                    break
        ind=[i for i in w.TABpar.ind]
        ind[-1]=-1
        self.setTABpars_at(ind)

    def defineMenuActions(self):
        self.projectTree.button_open_action=self.open_project
        self.projectTree.button_save_action=self.save_project
        self.projectTree.button_saveas_action=self.saveas_project
        self.projectTree.button_close_action=self.close_project
        self.projectTree.button_clean_action=self.clean_projects
        
        self.processTree.button_delete_action=self.delete_process
        self.processTree.button_clean_action=self.clean_processes

        self.ui.actionPaIRS_Run.triggered.connect(lambda: runPaIRS(self,))
        self.ui.actionPaIRS_Clean_run.triggered.connect(lambda: runPaIRS(self,'-c'))
        self.ui.actionPaIRS_Debug_run.triggered.connect(lambda: runPaIRS(self,'-d'))

        actions=self.ui.menuFile.actions()
        for a in actions:
            aName=a.objectName().replace('action','').lower()
            if hasattr(self,'menu_'+aName+'_action'):
                a.triggered.connect(getattr(self,'menu_'+aName+'_action'))
        self.ui.aExit.triggered.connect(lambda: self.close())

        self.showChanges=lambda: changes(self,Log_Tab,fileChanges)
        self.ui.actionChanges.triggered.connect(self.showChanges)
        self.ui.actionGuide.triggered.connect(self.guide)
        self.ui.actionDownload.setVisible(not Flag_ISEXE)
        if not Flag_ISEXE: 
            self.ui.menuHelp.insertSeparator(self.ui.actionDownload)
            self.ui.actionDownload.triggered.connect(self.downloadApp)
        self.ui.actionAbout.triggered.connect(self.about)

        self.ui.button_PaIRS_download.clicked.connect(lambda: button_download_PaIRS_action(self,self.app))

    def disableTab_ImTree(self,Flag=True):
        self.ui.w_Managing_Tabs.setEnabled(not Flag)
        for w in self.tabWidgets:
            w:gPaIRS_Tab
            if w!=self.w_Input and w!=self.ui.tabAreaWidget:
                w.setEnabled(not Flag)
        self.w_Input.ui.CollapBox_ImSet.setEnabled(not Flag)
        self.w_Input.ui.w_InputFold_Button.setEnabled(not Flag)
        self.w_Input.ui.imTreeWidget.setEnabled(True)

        self.w_Input.ui.button_back.setEnabled(not Flag)
        self.w_Input.ui.button_forward.setEnabled(not Flag)

        self.ui.menubar.setEnabled(not Flag)

        #evita TABpar.FlagSettingPar=Flag così che sai dove FlagSettingPar è settato True o False
        ImageTreeWidget.disableTab(self.w_Input.ui.imTreeWidget,Flag)    

    def button_back_forward_action(self,step):
        self.w_Input.FlagSettingPar=True
        self.setFocus()
        self.w_Input.FlagSettingPar=False
        for w in self.tabWidgets:
            w:gPaIRS_Tab
            if not w.TABpar.FlagNone:
                ind=w.TABpar.ind
                ind[-1]+=step
                w.TABpar.copyfrom(w.TABpar_at(ind))
        FlagAdjustPar=w.TABpar.FlagInit==False or w.TABpar.Process==ProcessTypes.cal #w.TABpar.ind[-1]==0
        FlagBridge=w.TABpar.Process==ProcessTypes.cal #False
        if FlagAdjustPar or FlagBridge:
            for w in self.tabWidgets:
                if not w.TABpar.FlagNone:
                    w:gPaIRS_Tab
                    if FlagAdjustPar: 
                        FlagSettingPar=TABpar.FlagSettingPar
                        TABpar.FlagSettingPar=True
                        w.adjustTABpar()
                        TABpar.FlagSettingPar=FlagSettingPar
                    if FlagBridge: self.bridge(w.TABname)
            FlagAdjustPar=False
            FlagBridge=False
        for w in self.tabWidgets:
            w:gPaIRS_Tab
            if not w.TABpar.FlagNone:
                w.setTABpar(FlagAdjustPar,FlagBridge) 
        self.ui.Explorer.setITElayout()
        return 
    
    def bfContextMenu(self,bf,event):
        ind=self.ui.tabAreaWidget.TABpar.ind
        i=ind[-1]
        TABpar_prev=self.ui.tabAreaWidget.TABpar_prev_at(ind)

        if bf==-1:
            b=self.ui.tabAreaWidget.ui.button_back
            kin=max([0,i-Num_Prevs_back_forw])
            krange=[k for k in range(i-1,kin,-1)]+[0]
            icon=self.ui.tabAreaWidget.undo_icon
            d=1
        elif bf==1:
            b=self.ui.tabAreaWidget.ui.button_forward
            kfin=min([len(TABpar_prev)-1,i+Num_Prevs_back_forw])
            krange=[k for k in range(i+1,kfin)]+[len(TABpar_prev)-1]
            icon=self.ui.tabAreaWidget.redo_icon
            d=0

        menu=QMenu(b)
        act=[]
        nur=len(krange)
        flag=nur==Num_Prevs_back_forw
        for j,k in enumerate(krange):
            if j==nur-1: 
                if flag: menu.addSeparator()
                if k==0: s=' (first)'
                else: s=' (current)'
            else:
                if j==nur-2 and flag:
                    s=' (...)'
                else:
                    s=''
            n=f"{k-i:+d}: "
            name=n+TABpar_prev[k+d].tip+s
            act.append(QAction(icon,name,b))
            menu.addAction(act[-1])  

        action = menu.exec_(b.mapToGlobal(event.pos()))
        for k,a in zip(krange,act):
            if a==action: 
                self.button_back_forward_action(-i+k)

    def defineTABbridges(self):
        for w in self.tabWidgets: #[:-1] except tabArea
            w:gPaIRS_Tab
            self.define_add_TABpar_bridge(w)
            self.define_setTABpar_bridge(w)

    def setTABpars_at(self,ind,FlagAdjustPar=False,FlagBridge=True,widget:gPaIRS_Tab=None):
        for w in self.tabWidgets:
            w:gPaIRS_Tab
            TABpar_ind:TABpar=w.TABpar_at(ind)
            if TABpar_ind:
                if not TABpar_ind.FlagNone: 
                    w.TABpar.copyfrom(TABpar_ind)  
        ITE_ind:ITEpar=self.ui.Explorer.ITEfromInd(ind)
        self.ui.Explorer.ITEpar.copyfrom(ITE_ind,exceptions=['procdata'])
        self.ui.Explorer.ITEpar.procdata=dataTreePar(ITE_ind.Process,ITE_ind.Step)
        self.ui.Explorer.ITEpar.procdata.ind=self.ui.Explorer.ITEpar.ind
        self.ui.Explorer.ITEpar.procdata.copyfrom(ITE_ind.procdata)
        if widget is None:
            self.ui.tabAreaWidget.setTABpar(FlagAdjustPar,FlagBridge)
        else:
            widget.setTABpar(FlagAdjustPar,FlagBridge)
        self.ui.tabAreaWidget.display_controls()

    def define_add_TABpar_bridge(self,tab:gPaIRS_Tab):
        def add_TABpar_bridge(tip,ind):
            tab.TABpar.parentTab=tab.TABname
            for w in self.tabWidgets:
                w:gPaIRS_Tab
                if w!=tab:
                    w:gPaIRS_Tab
                    w.TABpar.ind=[i for i in ind] 
                    ind_new=w.add_TABpar_copy(tip,ind)  #setting parameters without bridge
            ITE:ITEpar=self.ui.Explorer.ITEfromInd(ind)
            ITE.ind[-1]=ind_new[-1]
            self.ui.Explorer.ITEpar.ind[-1]=ind_new[-1]
            ITEs:ITEpar=self.ui.Explorer.ITEsfromInd(ind)
            ITEs[0].modifiedDate=currentTimeString()
            ITEs[0].date=f'Modified: {ITE.modifiedDate}'
            
            TRE:TREpar=self.projectTree.itemList[0][ITE.ind[0]]
            TRE.modifiedDate=ITEs[0].modifiedDate
            TRE.date=ITEs[0].date
            TRE.FlagSaved=False

            self.GPApar.modifiedDate=ITEs[0].modifiedDate
            self.GPApar.date=ITEs[0].date
            self.GPApar.FlagSaved=False

            self.ui.Explorer.ITEpar.copyfrom(ITE)
            self.TREpar.copyfrom(TRE)
            self.adjustItemWidgets(ind)

            self.inheritance(ind)
            self.IOVinheritance(ind)
            self.adjustDependencies(ITE)
            #self.checkFutureProc()
        tab.add_TABpar_bridge=add_TABpar_bridge

    def define_setTABpar_bridge(self,tab:gPaIRS_Tab):
        def setTABpar_bridge(FlagAdjustPar,FlagCallback=False):
            focusWidget=self.focusWidget()
            TABname=tab.TABname
            self.bridge(TABname)
            if FlagAdjustPar:
                FlagSettingPar=TABpar.FlagSettingPar
                TABpar.FlagSettingPar=True
                for w in self.tabWidgets:
                    if w.TABpar.FlagNone: continue
                    w:gPaIRS_Tab
                    if w!=tab:
                        w.adjustTABpar()
                        self.bridge(w.TABname)
                TABpar.FlagSettingPar=FlagSettingPar
                FlagAdjustPar=False
            FlagBridge=False
            FlagDisplayControls=False
            for w in self.tabWidgets:
                w:gPaIRS_Tab
                if  not w.TABpar.FlagNone and w!=self.w_Log:
                    if w.TABpar_old.isDifferentFrom(w.TABpar,exceptions=['ind'],FlagStrictDiff=True):
                        w.setTABpar(FlagAdjustPar,FlagBridge,FlagCallback,FlagDisplayControls)  #setting parameters without bridge
                    else:
                        if w==self.w_Vis_CalVi and w.TABpar.plane and w.TABpar.cam: 
                            self.w_Vis_CalVi.calibView.show()
                        w.TABpar_old.copyfrom(w.TABpar,exceptions=['ind'])
                    if not FlagCallback: 
                        w.adjustTABparInd()
            self.ui.Explorer.ITEpar.FlagInit=False
            self.ui.Explorer.setITElayout()
            if not self.w_Log.TABpar.FlagNone:
                if self.w_Log.LOGpar.flagRun!=-2:
                    self.logBridge()
                    if self.w_Log.TABpar_old.isDifferentFrom(self.w_Log.TABpar,FlagStrictDiff=True):
                        self.w_Log.setTABpar(FlagAdjustPar,FlagBridge,FlagCallback)
                    else:
                        self.w_Log.TABpar_old.copyfrom(self.w_Log.TABpar,exceptions=['ind'])
                    if not FlagCallback: self.w_Log.adjustTABparInd()
                else:
                    self.w_Log.setTABpar(FlagAdjustPar=False,FlagBridge=False,FlagCallback=False)
            if not FlagCallback: 
                self.inheritance(tab.TABpar.ind)
                ITE_ind:ITEpar=self.ui.Explorer.ITEfromInd(tab.TABpar.ind)
                self.adjustDependencies(ITE_ind)
            self.ui.tabAreaWidget.display_controls()

            if focusWidget:
                self.app.processEvents()
                focusWidget.setFocus()
        tab.setTABpar_bridge=setTABpar_bridge

    def logBridge(self):
        LOG:LOGpar = self.w_Log.TABpar
        ITE:ITEpar = self.ui.Explorer.ITEpar #self.ui.Explorer.ITEfromTRE(self.TREpar)

        if ITE.flagRun==0:
            warningMessages=[]
            errorMessages=[]
            for w in self.tabWidgets[:-1]:
                w:gPaIRS_Tab
                par:TABpar= w.TABpar
                if w!=self.w_Log and not par.FlagNone:
                    if par.OptionDone==0: errorMessages.append('--- '+w.TABname+' ---\n'+par.warningMessage)
                    elif par.OptionDone!=1: warningMessages.append('--- '+w.TABname+' ---\n'+par.warningMessage)
            
            
            warnigText='\n\n'.join(warningMessages)
            if warnigText: 
                warnigText='\n\n'+ITE.procdata.headerSection('WARNINGS',warnigText,'!')  
            errorText='\n\n'.join(errorMessages)
            if errorText: 
                errorText='\n\n'+ITE.procdata.headerSection('CRITICAL ISSUES',errorText,'X')  
            LOG.text=PaIRS_Header+ITE.procdata.itemname+warnigText+errorText
        else:
            LOG.text=ITE.procdata.Log

    def bridge(self,TABname:str,ind:list=None):
        if ind is None:
            INP:INPpar = self.w_Input.TABpar
            OUT:OUTpar = self.w_Output.TABpar
            PRO:PROpar = self.w_Process.TABpar
            VIS:VISpar = self.w_Vis.TABpar

            PRO_Min:PROpar_Min = self.w_Process_Min.TABpar
            PRO_Disp:PROpar_Disp = self.w_Process_Disp.TABpar

            CAL:CALpar = self.w_Calibration.TABpar
            INP_CalVi:INPpar_CalVi = self.w_Input_CalVi.TABpar
            PRO_CalVi:PROpar_CalVi = self.w_Process_CalVi.TABpar
            VIS_CalVi:VISpar_CalVi = self.w_Vis_CalVi.TABpar

            ITE:ITEpar = self.ui.Explorer.TABpar #self.ui.Explorer.ITEfromTRE(self.TREpar)
            SPL:SPLpar = self.ui.tabAreaWidget.TABpar
        else:
            INP:INPpar = self.w_Input.TABpar_at(ind)
            OUT:OUTpar = self.w_Output.TABpar_at(ind)
            PRO:PROpar = self.w_Process.TABpar_at(ind)
            VIS:VISpar = self.w_Vis.TABpar_at(ind)

            PRO_Min:PROpar_Min = self.w_Process_Min.TABpar_at(ind)
            PRO_Disp:PROpar_Disp = self.w_Process_Disp.TABpar_at(ind)

            CAL:CALpar = self.w_Calibration.TABpar_at(ind)
            INP_CalVi:INPpar_CalVi = self.w_Input_CalVi.TABpar_at(ind)
            PRO_CalVi:PROpar_CalVi = self.w_Process_CalVi.TABpar_at(ind)
            VIS_CalVi:VISpar_CalVi = self.w_Vis_CalVi.TABpar_at(ind)

            ITE:ITEpar = self.ui.Explorer.ITEfromInd(ind) #self.ui.Explorer.ITEfromTRE(self.TREpar)
            SPL:SPLpar = self.ui.tabAreaWidget.TABpar_at(ind)
        
        if ITE.Step in [StepTypes.min,StepTypes.piv,StepTypes.disp,StepTypes.spiv]:
            if TABname=='Input':
                OUT.inputPath=INP.path
                OUT.imageFile=None
                if INP.nimg:
                    for c in range(len(INP.imList)):
                        for f in range(len(INP.imList[c])):
                            for k in range(len(INP.imList[c][f])):
                                if INP.imEx[c][f][k]: 
                                    OUT.imageFile=INP.imList[c][f][k]
                                    break                    

                VIS.img=INP.selection[0]
                VIS.cam=INP.selection[1]
                VIS.frame=INP.selection[2]
                VIS.ncam=INP.ncam
                VIS.path=INP.path
                VIS.imList=copy.deepcopy(INP.imList)
                VIS.nimg=INP.nimg
                VIS.Out.copyfrom(OUT)
            elif TABname=='Output':
                if VIS.Out.isDifferentFrom(OUT):
                    VIS.Out.copyfrom(OUT)
                    self.w_Vis.FlagResetSizes=True
                if ITE.Step in [StepTypes.piv,StepTypes.disp,StepTypes.spiv]:
                    outPathRoot=myStandardRoot(OUT.path+OUT.subfold+OUT.root)
                    ndig=len(str(VIS.nimg))
                    outExt=list(outType_dict)[OUT.outType]
                    VIS.outPathRoot=outPathRoot
                    VIS.name_proc=ITE.procdata.name_proc
                    VIS.fres=[outPathRoot+'_', ndig, outExt]   #lambda i: f"{outPathRoot}_{i:0{ndig:d}d}{outExt}"
                elif ITE.Step == StepTypes.min:
                    imListMin=[]
                    outPathRoot=myStandardRoot(OUT.path+OUT.subfold+OUT.root)
                    for c in range(INP.ncam):
                        imListMin.append([outPathRoot+f'_cam{c+1}_a_min.png',outPathRoot+f'_cam{c+1}_b_min.png'])

                    INP.FlagMIN = True
                    INP.FlagTR = PRO_Min.FlagTR
                    INP.LaserType = PRO_Min.LaserType
                    INP.imListMin = deep_duplicate(imListMin)      

                    VIS.FlagMIN = ITE.procdata.flagRun>0
                    VIS.FlagTR = PRO_Min.FlagTR
                    VIS.LaserType = PRO_Min.LaserType
                    VIS.imListMin = deep_duplicate(imListMin)       
            elif TABname=='Process_Min':
                INP.FlagTR=PRO_Min.FlagTR
                INP.LaserType=PRO_Min.LaserType
                VIS.FlagTR=PRO_Min.FlagTR
                VIS.LaserType=PRO_Min.LaserType
            elif TABname=='Process_Disp':
                if VIS.Pro.isDifferentFrom(PRO_Disp,exceptions=['FlagBordo']):
                    VIS.Pro.copyfrom(PRO_Disp,exceptions=['FlagBordo'])
                VIS.Nit=PRO_Disp.Nit if VIS.flagRun!=-2 else ITE.procdata.numFinalized
            elif TABname=='Process':
                if VIS.Pro.isDifferentFrom(PRO):
                    VIS.Pro.copyfrom(PRO)
            elif TABname=='Vis':
                INP.selection=[VIS.img,VIS.cam,VIS.frame]
                self.w_Input.InputAdjustSelection(INP)
                pass                
        elif ITE.Step in [StepTypes.cal]:
            INP_CalVi.FlagReadCalib=PRO_CalVi.CalibProcType>=2
            INP_CalVi.CalibProcType=PRO_CalVi.CalibProcType
            if TABname=='Calibration':
                #FlagPrev=CAL.ind[-1]==len(self.w_Calibration.TABpar_prev_at(CAL.ind))-1
                self.ui.logo_CalVi.setVisible(CAL.FlagCalVi and CAL.flagRun==0 and not CAL.link) #and FlagPrev)
                self.ui.button_Run_CalVi.setVisible(CAL.FlagCalVi and CAL.flagRun==0 and not CAL.link) #and FlagPrev)
                if CAL.isDifferentFrom(self.w_Calibration.CALpar_old,fields=['FlagCalVi','flagRun']) or not INP_CalVi.FlagInit:
                    for w in [self.w_Input_CalVi,self.w_Process_CalVi,self.w_Vis_CalVi]:
                        k=self.ui.tabAreaWidget.widgets.index(w)
                        SPL.FlagVisible[k]=CAL.FlagCalVi
                        w.buttonTab.setVisible(CAL.FlagCalVi)
                    self.ui.tabAreaWidget.splitterResize(FlagReleased=False)
                    width=sum([s if f else 0 for s,f in zip(SPL.sizes,SPL.FlagVisible)])
                    if width<self.ui.tabAreaWidget.width():
                        SPL.sizes[-1]= self.ui.tabAreaWidget.width()-width
                    else: SPL.sizes[-1]=0
                #ITE.ncam=CAL.ncam
                #ITE.progress=len(CAL.calList)
            elif TABname=='Input_CalVi':
                VIS_CalVi.plane=int(INP_CalVi.row)*(1+PRO_CalVi.TargetType)+1
                VIS_CalVi.FlagResetLevels=INP_CalVi.isDifferentFrom(self.w_Input_CalVi.INPpar_old,fields=['path']) or len(self.w_Input_CalVi.INPpar_old.filenames)==0
                VIS_CalVi.FlagResetZoom=INP_CalVi.isDifferentFrom(self.w_Input_CalVi.INPpar_old,fields=['x','y','w','h','W','H']) or len(self.w_Input_CalVi.INPpar_old.filenames)==0
                pass
            elif TABname=='Process_CalVi':
                INP_CalVi.FlagOptPlane=PRO_CalVi.CalibProcType>0
                if len(INP_CalVi.plapar):
                    if INP_CalVi.FlagOptPlane:
                        for k,p in enumerate(INP_CalVi.plapar):
                            if len(p)==1:
                                INP_CalVi.plapar[k]=[float(0)]*5+[p[0]]
                    else:
                        for k,p in enumerate(INP_CalVi.plapar):
                            if len(p)>1:
                                INP_CalVi.plapar[k]=[p[-1]]
                pass
            elif TABname=='Vis_CalVi':
                if VIS_CalVi.plane-1!=INP_CalVi.row:
                    INP_CalVi.row=int( (VIS_CalVi.plane-1)/(1+PRO_CalVi.TargetType) )
                    INP_CalVi.rows=[INP_CalVi.row]
                    #INP_CalVi.col=0
                    #INP_CalVi.cols=[INP_CalVi.col]
                pass
            else:
                pass
        return

    def getInheritance(self, ind):
        indpar=[j for j in ind]
        for j in range(indpar[-2]):
            indpar[-2]=j
            self.inheritance(indpar)

    def inheritance(self,indpar):
        ITE:ITEpar = self.ui.Explorer.ITEfromInd(indpar) #self.ui.Explorer.ITEfromTRE(self.TREpar)
        if ITE.FlagNone: return
        ind=copy.deepcopy(ITE.ind)
        Process=ITE.Process
        Step=ITE.Step

        if Process in (ProcessTypes.piv,ProcessTypes.spiv) and Step == StepTypes.min:
            if ITE.active:
                FlagMIN=True
                INP:INPpar = self.w_Input.TABpar_at(ind)
                OUT:OUTpar = self.w_Output.TABpar_at(ind)
                PRO_Min:PROpar_Min = self.w_Process_Min.TABpar_at(ind)
                FlagTR=PRO_Min.FlagTR
                LaserType=PRO_Min.LaserType
                imListMin=[]
                outPathRoot=myStandardRoot(OUT.path+OUT.subfold+OUT.root)
                for c in range(INP.ncam):
                    imListMin.append([outPathRoot+f'_cam{c+1}_a_min.png',outPathRoot+f'_cam{c+1}_b_min.png'])
                imageFileMin=INP.path
                FlagImage=False
                for c in range(len(INP.imList)):
                    for f in range(len(INP.imList[c])):
                        if INP.imList[c][f]:
                            imageFileMin+=INP.imList[c][f][0]
                            FlagImage=True
                            break
                    if FlagImage: break
            else:
                FlagMIN=False
                FlagTR=False
                LaserType=0 #0 single, 1 double
                imListMin=[]
                imageFileMin=None
            if Process==ProcessTypes.piv:
                children=[+1] #piv step
            else:
                children=[+1,+2]  #disparity, spiv steps
            for c in children:
                ind_child=copy.deepcopy(ind)
                ind_child[-2]+=c
                TABpar_prev=self.w_Input.TABpar_prev_at(ind_child)

                for d in range(len(TABpar_prev)):
                    ind_child[-1]=d
                    INP_child:INPpar=self.w_Input.TABpar_at(ind_child)
                    INP_child.FlagMIN = FlagMIN
                    INP_child.FlagTR = FlagTR
                    INP_child.LaserType = LaserType
                    INP_child.imListMin = deep_duplicate(imListMin)  
                    #INP_child.FlagInit  = False
                    
                    OUT_child:OUTpar=self.w_Output.TABpar_at(ind_child)
                    OUT_child.imageFileMin = imageFileMin

                    VIS_child:VISpar=self.w_Vis.TABpar_at(ind_child)
                    VIS_child.FlagMIN = ITE.procdata.flagRun>0
                    VIS_child.FlagTR = FlagTR
                    VIS_child.LaserType = LaserType
                    VIS_child.imListMin = deep_duplicate(imListMin)
                    #VIS_child.FlagInit  = False

        elif Process == ProcessTypes.spiv and Step == StepTypes.cal:
            if ITE.active:
                CAL:CALpar = self.w_Calibration.TABpar_at(ind)
                FlagCAL=ITE.procdata.flagRun>0
                
                calList=CAL.calList
                calEx=CAL.calEx
            else:
                FlagCAL=False
                calList=[]
                calEx=[]
            children=[+1,+2,+3]  #disparity, spiv steps
            for c in children:
                ind_child=copy.deepcopy(ind)
                ind_child[-2]+=c

                for d in range(len(self.w_Input.TABpar_prev_at(ind_child))):
                    ind_child[-1]=d

                    INP_child:INPpar=self.w_Input.TABpar_at(ind_child)
                    INP_child.FlagCAL = FlagCAL
                    INP_child.calList = copy.deepcopy(calList)
                    INP_child.calEx   = copy.deepcopy(calEx)
                    #INP_child.FlagInit = False

                    VIS_child:VISpar=self.w_Vis.TABpar_at(ind_child)
                    VIS_child.FlagCAL = FlagCAL
                    VIS_child.calList = copy.deepcopy(calList)
                    VIS_child.calEx   = copy.deepcopy(calEx)
                    #VIS_child.FlagInit = False

        elif Process == ProcessTypes.spiv and Step == StepTypes.disp:
            if ITE.active:
                FlagDISP=True
            else:
                FlagDISP=False
            children=[+1]  #disparity, spiv steps
            for c in children:
                ind_child=copy.deepcopy(ind)
                ind_child[-2]+=c
                TABpar_prev=self.w_Input.TABpar_prev_at(ind_child)

                for d in range(len(TABpar_prev)):
                    ind_child[-1]=d
                    OUT_child:OUTpar=self.w_Output.TABpar_at(ind_child)
                    OUT_child.FlagDISP = FlagDISP
        """
        elif Process == ProcessTypes.spiv and Step == StepTypes.disp:
            if ITE.active:
                FlagDISP=True
                INP:INPpar = self.w_Input.TABpar_at(ind)
                OUT:OUTpar = self.w_Output.TABpar_at(ind)
                zconst=OUT.zconst
                xterm=OUT.xterm 
                yterm=OUT.yterm 
                outPathRoot=myStandardRoot(OUT.path+OUT.subfold+OUT.root)
                dispFile=outPathRoot+'.clz'
            else:
                FlagDISP=False
                zconst=0.0
                xterm=0.0
                yterm=0.0
                dispFile=''
            children=[+1]  #disparity, spiv steps
            FlagInit=True
            for c in children:
                ind_child=copy.deepcopy(ind)
                ind_child[-2]+=c
                TABpar_prev=self.w_Input.TABpar_prev_at(ind_child)

                for d in range(len(TABpar_prev)):
                    ind_child[-1]=d

                    INP_child:INPpar=self.w_Input.TABpar_at(ind_child)
                    INP_child.FlagDISP = FlagDISP
                    INP_child.dispFile = dispFile
                    #INP_child.FlagInit = False

                    OUT_child:OUTpar=self.w_Output.TABpar_at(ind_child)
                    OUT_child.FlagDISP = FlagDISP
                    OUT_child.zconst= zconst
                    OUT_child.xterm = xterm 
                    OUT_child.yterm = yterm 

                    VIS_child:VISpar=self.w_Vis.TABpar_at(ind_child)
                    VIS_child.FlagDISP = FlagDISP
                    VIS_child.dispFile = dispFile
                    #VIS_child.FlagInit = False

            pass
        """

        ITEs=self.ui.Explorer.ITEsfromInd(indpar)
        #currInd=list(ITEs[0].children).index(ITE.Step)+1
        for c in range(len(ITEs)):  #range(currInd+1,len(ITEs))
            ITE_ind:ITEpar=ITEs[c]
            self.checkProcesses(FlagInit=True,ind=ITE_ind.ind)
            #self.checkProcesses(FlagInit=False,ind=ITE_ind.ind)
            self.ui.Explorer.setITElayout(ITE_ind)
        return

    def IOVinheritance(self,indpar):
        ITE:ITEpar = self.ui.Explorer.ITEfromInd(indpar) #self.ui.Explorer.ITEfromTRE(self.TREpar)
        if ITE.FlagNone: return
        ind=copy.deepcopy(ITE.ind)
        Step=ITE.Step
        #inverse inheritance 
        if Step not in (StepTypes.cal,) and ITE.active:
            INP:INPpar = self.w_Input.TABpar_at(ind)
            OUT:OUTpar = self.w_Output.TABpar_at(ind)
            VIS:VISpar = self.w_Vis.TABpar_at(ind)

            #children=[-2, -1] if Step==StepTypes.spiv else [-1]  #disparity, spiv steps #*
            for c in range(len(processData[ITE.Process]['children'])): #in children: #*
                ind_child=copy.deepcopy(ind)
                #ind_child[-2]+=c #*
                ind_child[-2]=c
                TABpar_prev=self.w_Input.TABpar_prev_at(ind_child)
                if TABpar_prev[0] is None: continue

                FlagInit=len(TABpar_prev)==1 and TABpar_prev[0].flagRun==0
                if FlagInit:
                    ind_child[-1]=0
                    INP_child:INPpar=self.w_Input.TABpar_at(ind_child)
                    INP_child.copyfrom(INP,exceptions=['Process','Step']+INP_child.parFields)

                    OUT_child:OUTpar=self.w_Output.TABpar_at(ind_child)
                    OUT_child.copyfrom(OUT,exceptions=['Process','Step']+OUT_child.parFields)
                    
                    VIS_child:VISpar=self.w_Vis.TABpar_at(ind_child)
                    VIS_child.copyfrom(VIS,exceptions=['Process','Step']+VIS_child.parFields)
                    
                    self.checkProcesses(FlagInit=True,ind=ind_child)
                    self.checkProcesses(FlagInit=False,ind=ind_child)
                    ITE_ind:ITEpar = self.ui.Explorer.ITEfromInd(ind_child)
                    self.ui.Explorer.setITElayout(ITE_ind)
                    self.inheritance(ind_child)

    def IOVcopy(self,ind_slave,ind_master):
        ITE:ITEpar = self.ui.Explorer.ITEfromInd(ind_master) #self.ui.Explorer.ITEfromTRE(self.TREpar)
        if ITE.FlagNone: return

        #Input/Output/Vis inheritance 
        INP:INPpar = self.w_Input.TABpar_at(ind_master)
        OUT:OUTpar = self.w_Output.TABpar_at(ind_master)
        VIS:VISpar = self.w_Vis.TABpar_at(ind_master)

        self.w_Input.INPpar.copyfrom(INP,exceptions=['Process','Step']+INP.parFields)
        self.w_Output.OUTpar.copyfrom(OUT,exceptions=['Process','Step']+OUT.parFields)
        self.w_Vis.VISpar.copyfrom(VIS,exceptions=['Process','Step']+VIS.parFields)

        FlagNewPar=self.w_Input.isNewPar() or self.w_Output.isNewPar()
        ind_slave=self.w_Input.add_TABpar('Copy input/output data from step',FlagNewPar)
        self.setTABpars_at(ind_slave,FlagAdjustPar=True,FlagBridge=True,widget=self.w_Input)

        ITE_slave:ITEpar = self.ui.Explorer.ITEfromInd(ind_slave) #self.ui.Explorer.ITEfromTRE(self.TREpar)
        self.ui.Explorer.setITElayout(ITE_slave)
        return

#*************************************************** Update workspace and projects
    def updateWorkspace(self):
        self.GPApar.modifiedDate=currentTimeString()
        self.GPApar.date=f'Modified: {self.GPApar.modifiedDate}'
        self.GPApar.FlagSaved=False
        
        self.adjustWorkspaceHeader()

    def adjustWorkspaceHeader(self):
        if self.GPApar.outName and self.GPApar.outName!=lastcfgname:
            title=self.GPApar.name+self.GPApar.saveBullet()
            subtitle=self.GPApar.date
            icon=self.GPApar.icon
            FlagVisible=True
        else:
            title=''
            subtitle=''
            icon=None
            FlagVisible=False
        self.ui.title_workspace.setVisible(FlagVisible)
        self.ui.subtitle_workspace.setVisible(FlagVisible)
        self.ui.title_workspace.setText(title)
        self.ui.subtitle_workspace.setText(subtitle)
        
        InfoMessage=self.GPApar.InfoMessage()
        self.ui.title_workspace.setToolTip(InfoMessage)
        self.ui.title_workspace.setStatusTip(InfoMessage)
        self.ui.subtitle_workspace.setToolTip(InfoMessage)
        self.ui.subtitle_workspace.setStatusTip(InfoMessage)

        self.ui.workspace_icon.setVisible(icon is not None)
        self.adjustMenuFile()

        self.setGPaIRSTitle()

    def adjustMenuFile(self):
        self.ui.actionSave.setEnabled(not self.GPApar.FlagSaved)
        self.ui.actionClose.setEnabled(self.GPApar.outName not in ('',lastcfgname))

    def updateProjectItemWidget(self):
        TRE:TREpar=self.projectTree.itemList[0][self.TREpar.project]
        TRE.modifiedDate=currentTimeString()
        TRE.date=f'Modified: {TRE.modifiedDate}'
        TRE.FlagSaved=False
        self.TREpar.copyfrom(TRE)

        self.GPApar.modifiedDate=TRE.modifiedDate
        self.GPApar.date=TRE.date
        self.GPApar.FlagSaved=False

        self.adjustItemWidgets()

    def adjustItemWidgets(self,ind=None):
        if ind is None: ind=[self.TREpar.project, self.TREpar.tree, self.TREpar.process, self.TREpar.step, -1]
        TRE:TREpar=self.projectTree.itemList[0][ind[0]]
        topLevelItem=self.projectTree.topLevelItem(ind[0])
        itemWidget=self.projectTree.itemWidget(topLevelItem,1)
        if itemWidget:
            title:QLabel=itemWidget.findChildren(QLabel,'title_project')[0]
            title.setText(TRE.name+TRE.saveBullet())
            subtitle:QLabel=itemWidget.findChildren(QLabel,'subtitle_project')[0]
            subtitle.setText(TRE.date)
            InfoMessage=TRE.InfoMessage()
            title.setToolTip(InfoMessage)
            title.setStatusTip(InfoMessage)
            subtitle.setToolTip(InfoMessage)
            subtitle.setStatusTip(InfoMessage)
        if self.TREpar.project==ind[0] and self.TREpar.tree==ind[1] and self.TREpar.process is not None:
            self.adjustTitleHeader()
            self.projectTree.actionBar.button_save.setEnabled(not self.TREpar.FlagSaved)
            topLevelItem=self.processTree.topLevelItem(ind[2])
            itemWidget=self.processTree.itemWidget(topLevelItem,1)
            if itemWidget:
                title:QLabel=itemWidget.findChildren(QLabel,'title_process')[0]
                subtitle:QLabel=itemWidget.findChildren(QLabel,'subtitle_process')[0]
                subtitle.setText(TRE.date)
                ITE:ITEpar=self.ui.Explorer.ITEfromTRE(TRE)
                InfoMessage=ITE.InfoMessage()
                title.setToolTip(InfoMessage)
                title.setStatusTip(InfoMessage)
                subtitle.setToolTip(InfoMessage)
                subtitle.setStatusTip(InfoMessage)
            self.adjustTitleHeader()
        self.adjustWorkspaceHeader()

    def adjustTitleHeader(self):
        if self.TREpar.project is None:
            title='Welcome to PaIRS'
            subtitle='Particle Image Reconstruction Software'
            icon=None
            self.currITEpar=None
        else:
            title=self.TREpar.name+self.TREpar.saveBullet()
            if self.TREpar.process is None or self.TREpar.step is None:
                subtitle=self.TREpar.date
                icon=self.TREpar.icon
                self.currITEpar=self.TREpar
            else:
                ITEs:ITEpar=self.ui.Explorer.ITEsfromTRE(self.TREpar)
                title+=': '+ITEs[0].name
                subtitle=self.TREpar.date
                icon=ITEs[self.TREpar.step].icon
                self.currITEpar=ITEs[self.TREpar.step]
        self.ui.title.setText(title)
        self.ui.subtitle.setText(subtitle)

        if self.currITEpar:
            InfoMessage=self.currITEpar.InfoMessage()
        else:
            InfoMessage=''
        self.ui.title.setToolTip(InfoMessage)
        self.ui.title.setStatusTip(InfoMessage)
        self.ui.subtitle.setToolTip(InfoMessage)
        self.ui.subtitle.setStatusTip(InfoMessage)

        self.ui.title_icon.setVisible(icon is not None)
        self.ui.title_icon.setIcon(TreeIcons.icons[icon])
    
    def adjustProcessSelection(self):
        FlagVisible=[False,False,False,False]
        if self.TREpar.project is None:
            FlagVisible[0]=True
            self.ui.Explorer.hideStepButtons()
        else:
            if self.TREpar.process is None:
                FlagVisible[1]=True
                self.ui.Explorer.hideStepButtons()
            else:
                if self.TREpar.step is None or self.TREpar.step==0:
                    FlagVisible[2]=True
                else:
                    FlagVisible[3]=True            
        self.ui.projectPage.setVisible(FlagVisible[0])
        self.ui.processPage.setVisible(FlagVisible[1])
        self.ui.stepPage.setVisible(FlagVisible[2])
        self.ui.tabAreaWidget.setVisible(FlagVisible[3])
        self.w_RCL.setVisible(FlagVisible[3])
        #if FlagVisible[3]:
        #    self.ui.tabAreaWidget.scrollArea.splitter.splitterResize()
        
        self.adjustWorkspaceHeader()
        self.adjustTitleHeader()
        self.adjustSwitches()

        self.ui.Explorer.cancelUndo()

    def adjustProjectSelection(self):
        self.adjustProcessSelection()
        self.ui.Explorer.adjustProjectSelection()
        
    def adjustSwitches(self):
        for k in range(len(self.projectTree.itemList[0])):
            topLevelItem=self.projectTree.topLevelItem(k)
            itemWidget=self.projectTree.itemWidget(topLevelItem,1)
            if itemWidget:
                switch:ModernSwitch=itemWidget.findChildren(ModernSwitch)[0]
                if switch:
                    FlagVisible=any([i[0].flagRun<=0 and i[0].Process!=ProcessTypes.cal for i in self.projectTree.itemList[1][k][0]])
                    self.projectTree.itemList[0][k].FlagRunnable=FlagVisible
                    if not self.FlagRun:
                        FlagQueue=len(self.projectTree.itemList[1][k][0])==0 or not FlagVisible or any([i[0].flagRun<=0 and i[0].Process!=ProcessTypes.cal and i[0].FlagQueue for i in self.projectTree.itemList[1][k][0]])
                    else:
                        FlagQueue=switch._checked

                    switch.setVisible(FlagVisible)
                    switch.setSwitch(FlagQueue)
                    self.projectTree.itemList[0][k].FlagQueue=FlagQueue
                    if self.TREpar.project==k:
                        self.TREpar.FlagQueue=FlagQueue
                    #switch.setEnabled(self.FlagRun==0)
        if len(self.processTree.itemList):
            for k,i in enumerate(self.processTree.itemList[0]):
                topLevelItem=self.processTree.topLevelItem(k)
                itemWidget=self.processTree.itemWidget(topLevelItem,1)
                if itemWidget:
                    switch:ModernSwitch=itemWidget.findChildren(ModernSwitch)[0]
                    if switch:
                        ITE:ITEpar=i[0]
                        switch.setVisible(ITE.flagRun<=0 and ITE.Process!=ProcessTypes.cal and any([j.active and len(j.link)==0 for j in i[1:]]))
        #self.swithcEnabled(self.FlagRun==0)
        self.setButtonRunVisible()

#*************************************************** Link and copy
    def adjustDependencies(self,ITE:ITEpar):
        for ind_slave in ITE.dependencies:
            self.copy_pars(ind_slave,ITE.ind)
            #self.inheritance(ind_slave) #useless, already performed in copy_pars
            self.setLinks(ind_slave,ITE.ind)

    def button_reset_step_action(self):
        if self.questionDialog('Are you sure you want to reset the current process step? This operation will affect all the subsequent steps in the process and it is irreversible!'):
            self.reset_step(self.ui.Explorer.ITEpar.ind)
        return

    def reset_step(self,ind):
        FlagSettingPar=TABpar.FlagSettingPar
        TABpar.FlagSettingPar=True
        ITEs_ind:ITEpar=self.ui.Explorer.ITEsfromInd(ind)
        ind_child=copy.deepcopy(ind)
        for j in range(ind[-2],0,-1):
            ind_child[-2]=j-1
            ITE_ind:ITEpar=ITEs_ind[j]
            if not ITE_ind.active and ITE_ind.flagRun<0:
                ITE_ind.procdata=data=dataTreePar(ITE_ind.Process,ITE_ind.Step)
                ITE_ind.procdata.ind=ITE_ind.ind
                ITE_ind.progress=0
                self.setFlagRun(data,0,flagPrev=True)
            else:
                break
        for j in range(len(ITEs_ind)-1,ind[-2],-1):
            ind_child[-2]=j-1
            ITE_ind:ITEpar=ITEs_ind[j]
            ITE_ind.procdata=data=dataTreePar(ITE_ind.Process,ITE_ind.Step)
            ITE_ind.procdata.ind=ITE_ind.ind
            ITE_ind.progress=0
            self.setFlagRun(data,0,flagPrev=True)
            self.adjustDependencies(ITE_ind)
            self.inheritance(ind_child)
            ind_child[-1]=-1
            LOG_ind:LOGpar=self.w_Log.TABpar_at(ind_child)
            if LOG_ind: 
                LOG_ind.progress=0
                if self.w_Log.LOGpar.ind[:-1]==LOG_ind.ind[:-1]:
                    self.w_Log.setLOGlayout()
        self.ui.progress_Proc.setValue(0)
        self.setTABpars_at(ITE_ind.ind,FlagAdjustPar=True,widget=self.w_Calibration if ITE_ind.Step==StepTypes.cal else self.w_Vis)
        if data.ind[:-2]==self.ui.tabAreaWidget.TABpar.ind[:-2]:
            self.ui.Explorer.arrangeCurrentProcess(self.processTree)
        
        self.adjustSwitches()

        TABpar.FlagSettingPar=FlagSettingPar
    
    def IOVheritableSteps(self):
        ITE=self.ui.Explorer.ITEpar
        stepList={}
        if len(self.processTree.itemList) and ITE.ind[2]<len(self.processTree.itemList[0]):
            for step in self.processTree.itemList[0][ITE.ind[2]]:
                step:ITEpar
                if step.active and ITE.ind[:-1]!=step.ind[:-1]:
                    INP:INPpar = self.w_Input.TABpar_at(step.ind)
                    OUT:OUTpar = self.w_Output.TABpar_at(step.ind)
                    VIS:VISpar = self.w_Vis.TABpar_at(step.ind)
                    if INP is not None and OUT is not None and VIS is not None:
                        stepList[step.name]={'ind': step.ind, 'icon': step.icon}
        return stepList
    
    def linkableSteps(self,FlagExcludeLinked=False):
        ITE=self.ui.Explorer.ITEpar
        stepList={}
        if len(self.processTree.itemList):
            for process in self.processTree.itemList[0]:
                ITE0:ITEpar=process[0]
                for step in process[1:]:
                    step:ITEpar
                    FlagNoOverLink=True if not FlagExcludeLinked else len(step.link)==0
                    if step.active and step.Step==ITE.Step and ITE.ind[:-2]!=ITE0.ind[:-2] and FlagNoOverLink:
                        stepList[f'{step.ind[-3]+1}: '+ITE0.name]={'ind': step.ind, 'icon': ITE0.icon}
        return stepList

    def copy_link_action(self,button:QPushButton, fun=lambda ind_slave, ind_master:None, FlagExcludeLinked=False, menuTitle='Copy step from...',icon=None,message='No process step available!', stepListType=0):
        if stepListType==1:
            stepList=self.IOVheritableSteps()
        else:
            stepList=self.linkableSteps(FlagExcludeLinked=FlagExcludeLinked)
        ITE=self.ui.Explorer.ITEpar
        if len(stepList)==0:
            showTip(self,message)
            return None
        menu = QMenu(self)
        title_action = QAction(menuTitle, self)
        if icon: title_action.setIcon(icon)
        title_action.setDisabled(True)  # Disabilita l'azione per evitare l'interazione
        menu.addAction(title_action)
        menu.addSeparator()
        for key, item in stepList.items():
            #for colormap in VIS_ColorMaps[colorMapClass]:
            nameItem=' '+key
            action:QAction = menu.addAction(TreeIcons.icons[item['icon']], nameItem)
            action.triggered.connect(lambda _, name=key: fun(ITE.ind,stepList[name]['ind']))   
        return menu.exec(QCursor.pos()) #menu.exec(button.mapToGlobal(button.rect().bottomLeft()))

    def button_step_inherit_action(self):
        self.copy_link_action(self.ui.button_step_inherit,lambda isl,ima: self.IOVcopy(isl,ima),menuTitle='Copy input/output data from...', message='No process step available!', stepListType=1)

    def button_copy_step_action(self):
        self.copy_link_action(self.ui.button_copy_step,lambda isl,ima: self.copy_pars_proc(isl,ima,FlagNew=True))
    
    def checkCamCompatibility(self,ind_slave,ind_master):
        ITE_slave:ITEpar=self.ui.Explorer.ITEfromInd(ind_slave)
        isCompatible=True
        if ITE_slave.Step==StepTypes.min:
            INP_slave:INPpar=self.w_Input.TABpar_at(ind_slave)
            ncam_slave=INP_slave.ncam
            INP_master:INPpar=self.w_Input.TABpar_at(ind_master)
            ncam_master=INP_master.ncam
            isCompatible=ncam_slave==ncam_master
        elif ITE_slave.Step==StepTypes.cal:
            CAL_slave:CALpar=self.w_Calibration.TABpar_at(ind_slave)
            ncam_slave=CAL_slave.ncam
            CAL_master:CALpar=self.w_Calibration.TABpar_at(ind_master)
            ncam_master=CAL_master.ncam
            isCompatible=ncam_slave==ncam_master
        if not isCompatible:
            warningMessage=f'The number of cameras in the current step (={ncam_slave}) is different from that in the selected step (={ncam_master}). Please, select a different step or modify the number of cameras in the selected step before proceeding!'
            self.warningDialog(warningMessage)
        return isCompatible
    
    def copy_pars(self,ind_slave,ind_master,FlagNew=False):
        ind_new=[i for i in ind_slave]
        if FlagNew: ind_new[-1]+=1
        for w in self.tabWidgets:
            w:gPaIRS_Tab
            TAB_slave_curr:TABpar=w.TABpar_at(ind_slave)
            if TAB_slave_curr: 
                if FlagNew: w.gen_TABpar(ind_new,Process=TAB_slave_curr.Process,Step=TAB_slave_curr.Step)
                TAB_slave:TABpar=w.TABpar_at(ind_new)
                TAB_slave.copyfrom(w.TABpar_at(ind_master),exceptions=['ind','link','Process'])
        ITE_master:ITEpar=self.ui.Explorer.ITEfromInd(ind_master)
        ITE_slave:ITEpar=self.ui.Explorer.ITEfromInd(ind_new)
        ITE_slave.ind=[i for i in ind_new]
        ITE_slave.copyfrom(ITE_master,exceptions=['procdata','ind','link','Process','dependencies'])
        ITE_slave.procdata.copyfrom(ITE_master.procdata,exceptions=['ind','link','Process'])
        self.getInheritance(ind_slave)
        self.ui.Explorer.undoInd=None
        self.inheritance(ind_slave)
        self.ui.Explorer.setITElayout(ITE_slave)
        self.adjustSwitches()   #useless?
        return ind_new
    
    def copy_pars_proc(self,ind_slave,ind_master,FlagNew=False,FlagSet=True):
        if not self.checkCamCompatibility(ind_slave,ind_master): return
        ITEs_slave=self.ui.Explorer.ITEsfromInd(ind_slave)
        ITEs_master=self.ui.Explorer.ITEsfromInd(ind_master)
        for c in range(ind_slave[-2]+1):
            ind_slave=ITEs_slave[c+1].ind
            ind_master=ITEs_master[c+1].ind
            ind_new=self.copy_pars(ind_slave,ind_master,FlagNew=True)

        if FlagSet:
            self.ui.Explorer.arrangeCurrentProcess(self.ui.Explorer.processTree)
            self.ui.Explorer.selectStep()
        self.adjustSwitches()
        return ind_new
    
    def copy_VIS(self,ind_slave,ind_master):
        ind_new=[i for i in ind_slave]
        w=self.w_Vis
        w:gPaIRS_Tab
        TAB_slave_curr:VISpar=w.TABpar_at(ind_slave)
        if TAB_slave_curr: 
            TAB_slave:VISpar=w.TABpar_at(ind_new)
            TAB_slave.copyfromfields(w.TABpar_at(ind_master),fields=TAB_slave.graphics_fields)
        self.w_Vis.setTABpar_at(ind_new,FlagAdjustPar=True,FlagBridge=True)
        return ind_new
        
    def button_link_step_action(self):
        if self.ui.button_link_step.isChecked():
           result=self.copy_link_action(self.ui.button_link_step,self.link_pars,FlagExcludeLinked=True,menuTitle='Link step to...')
           FlagUnlink=result is None
        else:
            FlagUnlink=True
        if FlagUnlink:
            ITE=self.ui.Explorer.ITEpar
            self.unlink_pars(ITE.ind)
            self.ui.button_link_step.setChecked(False)
           
    def link_pars(self,ind_slave,ind_master,FlagSet=True):
        if not self.checkCamCompatibility(ind_slave,ind_master): return
        ITEs_slave=self.ui.Explorer.ITEsfromInd(ind_slave)
        ITEs_master=self.ui.Explorer.ITEsfromInd(ind_master)
        for c in range(ind_slave[-2]+1):
            ind_slave=ITEs_slave[c+1].ind
            ind_master=ITEs_master[c+1].ind
            ind_new=self.copy_pars(ind_slave,ind_master,FlagNew=True)
            self.setLinks(ind_new,ind_master)
        #item=self.processTree.topLevelItem(ind_new[2])
        #child=item.child(ind_new[3])
        #child.setIcon(0,self.processTree.linkedIcon)

        #self.setTABpars_at(ind_new)
        if FlagSet:
            self.ui.Explorer.arrangeCurrentProcess(self.ui.Explorer.processTree)
            self.ui.Explorer.selectStep()
        self.adjustSwitches()
        return ind_new

    def setLinks(self,ind_slave,ind_master,FlagUnlink=False,ind_slave_new=None,ind_master_new=None):
        if ind_slave_new is None: ind_slave_new=copy.deepcopy(ind_slave)
        if ind_master_new is None: ind_master_new=copy.deepcopy(ind_master)
        ITE_master:ITEpar=self.ui.Explorer.ITEfromInd(ind_master_new)
        if FlagUnlink and ind_slave in ITE_master.dependencies:
            ITE_master.dependencies.remove(ind_slave)
        elif not FlagUnlink and ind_slave not in ITE_master.dependencies:
            ITE_master.dependencies.append(copy.deepcopy(ind_slave))
        for w in self.tabWidgets:
            w:gPaIRS_Tab
            TABpar_ind:TABpar=w.TABpar_at(ind_slave_new)
            if TABpar_ind: 
                if FlagUnlink: 
                    TABpar_ind.link=[]
                    TABpar_ind.linkInfo=''
                else: 
                    TABpar_ind.link=copy.deepcopy(ind_master)
        ITE_ind:ITEpar=self.ui.Explorer.ITEfromInd(ind_slave_new)
        if FlagUnlink:
            ITE_ind.link=[]
            ITE_ind.procdata.link=[]
        else: 
            ITE_ind.link=copy.deepcopy(ind_master)
            ITE_ind.procdata.link=copy.deepcopy(ind_master)
    
    def unlink_pars(self,ind_slave):
        ITE_slave:ITEpar=self.ui.Explorer.ITEfromInd(ind_slave)
        ind_master=ITE_slave.link
        if ind_master:
            self.setLinks(ind_slave,ind_master,FlagUnlink=True)
            #item=self.processTree.topLevelItem(ind_slave[2])
            #child=item.child(ind_slave[3])
            #child.setIcon(0,QIcon())
            self.setTABpars_at(ind_slave)
            self.adjustSwitches()

#*************************************************** PROCESS
#********************************** Launching
    def button_run_pause_action(self):
        # FlagRun = 0 no procWorkers (all workers have been closed or never launched)
        # FlagRun = 1 procWorkers working
        # FlagRun = 2 pause pressed, waiting for procWorkers to be completed
        pri.Process.magenta(f'button_RunPause_callback self.FlagRun={self.FlagRun}  ')
        self.ui.button_pause.setEnabled(False) #ta disabilitato sempre lo riabilita il worker prima di iniziare

        if self.FlagRun==0: 
            self.FlagRun=1 
            self.setButtonPause(False)
            self.run()
        elif self.FlagRun==1:
            self.FlagRun=2 
            self.signals.killOrResetParForWorker.emit(True)
            self.setButtonPause(True)
    
    def setButtonPause(self,flagPlay):
        if flagPlay:
            self.ui.label_updating_pairs.setVisible(False)
            self.ui.button_pause.setIcon(self.icon_play)
            stringa='Restart'
        else:
            self.ui.label_updating_pairs.setVisible(True)
            self.ui.button_pause.setIcon(self.icon_pause)
            stringa='Pause'
        tip=f'{stringa} process queue'+' ('+self.ui.button_pause.shortcut().toString(QKeySequence.NativeText)+')'
        self.ui.button_pause.setToolTip(tip)
        self.ui.button_pause.setStatusTip(tip)
        self.setButtonRunVisible()
        self.processTree.setProcessActionButtonLayout()
        """
        FlagButtonRun=self.ui.progress_Proc.value()==0
        self.ui.button_Run.setVisible(FlagButtonRun)
        self.ui.button_pause.setVisible(not FlagButtonRun)
        self.ui.w_progress_Proc.setVisible(not FlagButtonRun)
        """
        
    def run(self):
        self.setSwitchEnabled(False)
        self.disableDropping(True)
        if self.initializeWorkers():
            self.indProc=-1
            self.updateIndProc()
        else:
            self.FlagRun=0
            self.setButtonPause(True)
            #self.button_run_pause_action()
            self.stopProcs()
    
    def updateIndProc(self):
        self.indWorker+=1
        data=self.dataQueue[self.indWorker]
        self.initialize_proc(data)  
        ITE_ind:ITEpar=self.ui.Explorer.ITEfromInd(data.ind)
        self.ui.Explorer.setITElayout(ITE_ind)

        self.indProc+=1
        data:dataTreePar
        self.ui.Explorer.updateSwitchMovies(self.currind,FlagStart=False)
        self.procdata=None
        self.procdata=data=self.dataQueue[self.indProc]
        self.currind=data.ind
        self.checkProcesses(FlagInit=True,ind=self.currind)
        ITE:ITEpar=self.ui.Explorer.ITEfromInd(data.ind)
        self.ui.Explorer.setITElayout(ITE)
        if ITE.OptionDone==0:
            self.stopProcs()
            self.nextProc()
            return

        self.procdata.uncopied_fields+=self.procFields
        self.ui.Explorer.updateSwitchMovies(self.currind,FlagStart=True)

        self.resetProc(data)
        self.setProgressBar(data)
        data.resetLog()
        try:
            with open(data.stepOutName()+'.log', 'w') as file:
                file.write(data.Log)
        except:
            pri.Error.red(f'Error while trying to save the process log file: {data.stepOutName()}.log.\n{traceback.format_exc()}\n') 

        self.FlagResetPlot=True
        self.setFlagRun(data,-2)
        self.ui.Explorer.setITElayout(ITE)
        ITEs_ind:ITEpar=self.ui.Explorer.ITEsfromInd(self.currind)
        ind_child=copy.deepcopy(self.currind)
        for j in range(1,self.currind[-2]+1):
            ind_child[-2]=j-1
            ITE_child:ITEpar=ITEs_ind[j]
            data_child=ITE_child.procdata
            if data_child.flagRun==0:
                self.setFlagRun(data_child,-1)
                self.checkProcesses(FlagInit=True,ind=ind_child)
                self.ui.Explorer.setITElayout(ITE_child)
                if data_child.ind==self.ui.tabAreaWidget.TABpar.ind:
                    self.w_Log.LOGpar.text=data_child.Log
                    self.setTABpars_at(data_child.ind,FlagAdjustPar=True)    

        FlagCurrent=data.ind==self.ui.tabAreaWidget.TABpar.ind
        if FlagCurrent: 
            self.w_Log.LOGpar.text=data.Log
            self.setTABpars_at(data.ind,FlagAdjustPar=True)    
            self.w_Log.buttonAction()
        self.FlagProcInit=True
        self.signals.indProc.emit(self.indProc)
        if  data.flagRun==0:#not launched
          data.resetTimeStat() 
        data.onStartTimeStat()

    def setFlagRun(self,data:dataTreePar,flagRun,flagPrev=False):
        data.flagRun=flagRun  #come ultimo o comunque dopo resetProc    
        for w in self.tabWidgets:
            w:gPaIRS_Tab
            if flagPrev:
                TABpar_prev=w.TABpar_prev_at(data.ind)
                for TABpar_ind in TABpar_prev: 
                    if TABpar_ind: TABpar_ind.flagRun=flagRun
            else:
                TABpar_ind:TABpar=w.TABpar_at(data.ind)
                if TABpar_ind: TABpar_ind.flagRun=flagRun
        ITE_ind:ITEpar=self.ui.Explorer.ITEfromInd(data.ind)
        ITE_ind.flagRun=flagRun
        
        self.ui.Explorer.setProcessFlagRun(data.ind)
        return
    
    def nextProc(self):
        self.UpdatingImage=True

        if self.indProc<self.nProc-1 and self.FlagRun==1:
            try:
                self.updateIndProc()
            except:
                errMessage=f"{traceback.format_exc()}"
                self.procdata.warnings[0]+='\n\n'+self.procdata.headerSection('CRITICAL ERROR',errMessage,'X') 
                self.store_proc(self.procdata)
                self.stopProcs()
                self.nextProc()
        else:
            self.ui.button_pause.setEnabled(False) 

    def resetProc(self,data:dataTreePar):
        data.warnings[0]=data.warnings[1]
        data.warnings[1]=''
        data.flagParForCompleted=False
        data.numCallBackTotOk=data.numFinalized
        self.signals.progress.emit(data.numFinalized)
        data.numProcOrErrTot=0
        self.procWorkers[self.indProc].data=data
        self.ui.time_stamp.hide()
        return

    def setProgressBar(self,data:dataTreePar):
        self.ui.progress_Proc.setMinimum(0)
        self.ui.progress_Proc.setMaximum(data.nsteps)
        self.ui.progress_Proc.setValue(data.numFinalized) 
        self.w_Log.TABpar_at(data.ind).nimg=data.nsteps
        #ITE:ITEpar=self.ui.Explorer.ITEfromInd(data.ind)
        return
        
    def setLogProgressBar(self,data:dataTreePar):
        self.w_Log.ui.progress_Proc.setMinimum(0)
        self.w_Log.ui.progress_Proc.setMaximum(data.nsteps)
        self.w_Log.ui.progress_Proc.setValue(data.numFinalized) 
        return
    
#********************************** Initialization of workers
    def initializeWorkers(self):
        self.indWorker=-1
        self.indProc=-1
        while self.pfPool is None:
          #TBD  serve lo sleep? Se non ci sono errori cancellare
          pri.Error.white('****************\n****************\n****************\nwhile self.pfPool is None\n****************\n****************\n******************\n')
          if Flag_DEBUG: 1/0
          sleep(0.5)
        self.procWorkers=[]
        self.nProc=0
        nError=0
        nValid=0
        nTot=0
        self.dataQueue=[]
        for project in self.projectTree.itemList[1]:
            for process in project[0]:
                for step in process[1:]:
                    step:ITEpar
                    self.ui.Explorer.setITElayout(step)
                    nTot+=int(process[0].FlagQueue and step.active)
                    nError+=int(process[0].FlagQueue and step.active and step.flagRun<=0 and step.Step!=StepTypes.cal and step.OptionDone==0)
                    nValid+=int((process[0].FlagQueue and step.active and step.flagRun>0) or step.Step==StepTypes.cal)
                    if process[0].FlagQueue and step.active and step.flagRun<=0 and step.Step!=StepTypes.cal and step.OptionDone!=0 and len(step.link)==0: 
                        self.nProc+=1
                        data=step.procdata
                        data.ind=step.ind
                        self.dataQueue.append(data)
                    elif step.Process!=ProcessTypes.cal and step.Step==StepTypes.cal and step.OptionDone==1:
                        data=step.procdata
                        data.ind=step.ind
                        self.setFlagRun(data,2)
                        CAL:CALpar=self.w_Calibration.TABpar_at(step.ind)
                        CAL.FlagCalVi=False
        if self.nProc==0 and nValid==0:
            self.warningDialog('No valid process found in the present projects!\nPlease, check for critical issues related to each step of the defined processes.',pixmap=icons_path+'issue.png')
        elif self.nProc==0 and nError>0:
            self.warningDialog(f'{nError} process step{"s" if nError>1 else ""} present{"" if nError>1 else "s"} critical issues!\nNo further valid process found in the present projects.\nPlease, check before running again.',pixmap=icons_path+'issue.png')
        elif self.nProc>0 and nError>0:
            if not self.questionDialog(f'{nError} process step{"s" if nError>1 else ""} present{"" if nError>1 else "s"} critical issues!\n{"They" if nError>1 else "It"} will not be executed. Do you want to proceed with processing?'): 
                self.contProc=self.nProc-1 #necessario per far funzionare stopProc in run quando il risultato di questa funzione è False
                return False
        elif self.nProc==0:
            self.warningDialog(f'All the processes found in the present projects have been already executed!',pixmap=icons_path+'completed.png')
        FlagQueue=len(self.dataQueue)!=0
        self.contProc=-1 if not FlagQueue else 0  
        self.putStepsInQueue()
        """
        for data in self.dataQueue:
            data:dataTreePar
            self.indWorker+=1
            self.initialize_proc(data)  
            ITE_ind:ITEpar=self.ui.Explorer.ITEfromInd(data.ind)
            self.ui.Explorer.setITElayout(ITE_ind)
        """
        return FlagQueue
    
    def initialize_proc(self,data:dataTreePar):
        self.set_proc(data)            
        self.setFlagRun(data,-1)

        if data.ind[:-2]==self.ui.tabAreaWidget.TABpar.ind[:-2]:
            self.ui.Explorer.arrangeCurrentProcess(self.processTree)

        currpath=data.outPath
        if not os.path.exists(currpath): 
            try:
                os.mkdir(currpath)
            except Exception as inst:
                pri.Error.red(f'It was not possible to make the directory {currpath}:\n{traceback.format_exc()}\n\n{inst}')
        pfPool = None if self.flagSimpleFor else self.pfPool
        if data.Step==StepTypes.min:
            self.numUsedProcs=self.numMaxProcs
            data.numPivOmpCores=1
            data.numUsedProcs=self.numMaxProcs
            procWorker=MIN_ParFor_Worker(data,self.indWorker,self.indProc,self.numMaxProcs,pfPool,self.parForMul)
        elif data.Step ==StepTypes.piv or  data.Step ==StepTypes.spiv:
            data.numPivOmpCores,data.numUsedProcs=optimalPivCores(self.numMaxProcs,data.nimg,penCore=0.95)
            #data.numUsedProcs=3 # data.numUsedProcs is used for output should be the number of parfor threads used 
            #data.numPivOmpCores=7#self.numMaxProcs   
            self.numUsedProcs=data.numUsedProcs
            procWorker=PIV_ParFor_Worker(data,self.indWorker,self.indProc,self.numMaxProcs,pfPool,self.parForMul)
        elif data.Step ==StepTypes.disp:
            data.numPivOmpCores=NUMTHREADS_MAX
            data.numUsedProcs=1
            procWorker=StereoDisparity_ParFor_Worker(data,self.indWorker,self.indProc,self.numMaxProcs,pfPool,self.parForMul)
        

        procWorker.signals.progress.connect(self.progress_proc)
        self.signals.progress.connect(procWorker.setNumCallBackTot)
        procWorker.signals.finished.connect(self.pause_proc)
        procWorker.signals.initialized.connect(self.buttonPauseHideShow)
        procWorker.signals.completed.connect(self.stopProcs)
        self.signals.pause_proc.connect(procWorker.storeCompleted) 
        #self.ui.button_pause.clicked.connect(MIN_worker.die)
        self.signals.killOrResetParForWorker.connect(procWorker.killOrReset)
        self.signals.indProc.connect(procWorker.updateIndProc) 
        self.FlagInitialized=True
        self.procWorkers.append(procWorker)
        self.PaIRS_threadpool.start(procWorker)
        
    def set_proc(self,data:dataTreePar,ind=None,FlagLog=True):
        if ind is None: ind=data.ind
        k=self.dataQueue.index(data)
        if self.dataFlagRuns[k]==0:  
            self.getInheritance(ind)
            data.namesPIV=NamesPIV(Process=data.Process,Step=data.Step)
            INP_ind=self.w_Input.TABpar_at(ind)
            OUT_ind=self.w_Output.TABpar_at(ind)
            PRO_ind=self.w_Process.TABpar_at(ind)
            PRO_Min_ind=self.w_Process_Min.TABpar_at(ind)
            PRO_Disp_ind=self.w_Process_Disp.TABpar_at(ind)
            data.setProc(INP_ind,OUT_ind,PRO_ind,PRO_Min_ind,PRO_Disp_ind)
            data.assignDataName()

            if FlagLog:
                ITE_ind:ITEpar=self.ui.Explorer.ITEfromInd(ind)
                data.warnings[1]=ITE_ind.warningMessage
                data.setCompleteLog()

                LOG_ind=self.w_Log.TABpar_at(ind)
                if LOG_ind:
                    LOG_ind.text=data.Log

#********************************** Progress
    @Slot(int,int,int,list,str)
    def progress_proc(self,procId,i,pim,Var,stampa):
        ''' E' la funzione chiamata alla fine di ogni elaborazione dai vari threads in parfor è chiamata wrapUp CallBack'''
        data=self.procdata
        pri.Info.yellow(f'[progress_proc] {data.ind} {self.procdata is self.dataQueue[self.indProc]} {self.currind}')
        #******************** Updating total number of tasks passed to the pool
        data.numProcOrErrTot+=1
        #pri.Time.blue(0,f'progress_proc start i={i} pim={hex(pim)} {"*"*25}   {procId}  FlagRun={self.FlagRun}')
        
        if i<0:  return  #When restarting a process return  immediately if the images have been already processed
        #******************** Updating Log
        data.Log+=stampa+'\n'
        self.w_Log.TABpar_at(data.ind).text=data.Log

        data.list_print[i]=stampa
        data.list_pim[i]=pim

        if not pim&FLAG_CALLBACK_INTERNAL: return   #c'è un errore prima della fine di tutti i processi relativi ad i
        #******************** Updating Progress Bar
        data.numCallBackTotOk+=1 #Always at the end the progress bar will go back to the correct value
        self.signals.progress.emit(data.numCallBackTotOk) #fundamental in multithreading

        ITE_ind:ITEpar=self.ui.Explorer.ITEfromInd(data.ind)
        LOG_ind:LOGpar=self.w_Log.TABpar_at(data.ind)
        if self.FlagRun==1: 
            self.ui.progress_Proc.setValue(data.numProcOrErrTot)
            LOG_ind.progress=data.numProcOrErrTot
            ITE_ind.progress=data.numProcOrErrTot
        else:
            self.ui.progress_Proc.setValue(data.numFinalized)
            LOG_ind.progress=data.numFinalized
            ITE_ind.progress=data.numFinalized
        LOG_ind.nimg=data.nsteps
        self.ui.Explorer.updateItemWidget(ITE_ind)
        self.adjustDependencies(ITE_ind)

        flagSelected=data.hasIndexOf(self.ui.Explorer.ITEpar)
        if flagSelected:
            self.w_Log.LOGpar.progress=LOG_ind.progress
            self.w_Log.LOGpar.nimg=data.nimg
            self.w_Log.setProgressProc()
            
        if data.Step==StepTypes.min:
            flagFinalized=(pim&FLAG_FINALIZED[0]) and (pim&FLAG_FINALIZED[1])
        elif data.Step in (StepTypes.piv,StepTypes.disp,StepTypes.spiv):
            flagFinalized=pim&FLAG_FINALIZED[0]
        
        if not flagFinalized: return   
        #******************** Updating numFinalized
        data.numFinalized+=1
          
        if data.flagParForCompleted: return
        #******************** updating log
        if flagSelected: 
          self.w_Log.LOGpar.text=data.Log
          self.w_Log.setLogText(FlagMoveToBottom=True)
        
        pri.Process.green(f'progress_proc {i} data.numProcOrErrTot={data.numProcOrErrTot} self.numFinalized={data.numFinalized}')
        # prLock ha smesso di funzionare perchè?
        #prLock(f'progress_proc {i} data.numProcOrErrTot={data.numProcOrErrTot}  self.numCallBackTotOk={self.numCallBackTotOk}')

        if self.FlagRun==0 or (procId%self.numUsedProcs and data.Step!=StepTypes.disp): return   #evitare aggiornamento tempo
        #if self.FlagRun==0: return   #evitare aggiornamento tempo
        #******************** Updating time counter and stats
        actualTime=time()
        self.showTimeToEnd(data,time=actualTime)

        if not Flag_GRAPHICS and not self.w_Vis.VISpar.FlagVis: return 
        if actualTime<self.previousPlotTime+deltaTimePlot: return 
        if not flagSelected: return 
        # fra l'altro mi sembra che queata funzione sia abbastanza onerosa
        #updating plot
        pri.Time.green(f'plotting the field {i} over {data.numProcOrErrTot} ')

        self.plotCurrent(data,i,Var)
        self.previousPlotTime=time()
        return 
        #pri.Time.green(0,f'progress_proc end   i={i} pim={hex(pim)} {"-"*25}   {procId}   FlagRun={self.FlagRun}')

    def plotCurrent(self,data=None,i=-1,Var=None,FlagBridge=False):
        if Var==[]: return
        if data is None:
            data=self.procdata
        try:
            FlagCurrent=data.hasIndexOf(self.ui.Explorer.ITEpar)
            VIS_ind:VISpar=self.w_Vis.TABpar_at(data.ind)
            if data.Step==StepTypes.min:
                if i>-1: 
                    VIS_ind.image_file_Current=data.inpPath+data.list_Image_Files[i]
                    self.w_Vis.image_Current_raw=Var
                else:
                    VIS_ind.FlagMIN = True
                    VIS_ind.image_file_Current=''
                    self.w_Vis.image_Current_raw=None
                    #if Var: #todo GP: per i==-1 Var deve essere l'immagine giusta
                    #    self.w_Vis.getImageInfo(Var,data.ind)
                    #    self.w_Vis.resetAllLevels(data.ind)
                    #    self.w_Vis.resetAllXYLims(data.ind)

                if self.FlagResetPlot:
                    VIS_ind.img=0
                    VIS_ind.type=0
                    VIS_ind.variable=self.namesPIV.combo_dict[self.namesPIV.img]
                    VIS_ind.variableKey=self.namesPIV.combo_dict_keys[VIS_ind.variable]
                    VIS_ind.FlagResetLevels=VIS_ind.FlagResetSizes=True
                    self.FlagResetPlot=False                   
                pass
            elif data.Step in (StepTypes.piv,StepTypes.disp,StepTypes.spiv): 
                if i>-1: 
                    if data.Step==StepTypes.disp:
                        VIS_ind.result_file_Current=VIS_ind.resF(f'it{i+1}')
                        VIS_ind.Nit=i+1
                        VIS_ind.it=i+1
                    else:
                        VIS_ind.result_file_Current=VIS_ind.resF(i)
                    fields=data.namesPIV.instVel
                    result={}
                    for f,v in zip(fields,Var):
                        result[f]=v
                    result=self.w_Vis.calcMagnitude(result)
                    result=self.w_Vis.calcZVorticity(result)
                    self.w_Vis.result_Current=result
                else:
                    VIS_ind.result_file_Current=''
                    self.w_Vis.result_Current=None
                    #if Var: #todo GP: per i==-1 Var deve essere result
                    #    self.w_Vis.getResultInfo(result,data.ind)
                    #    self.w_Vis.resetAllLevels(data.ind)
                    #    self.w_Vis.resetAllXYLims(data.ind)

                if self.FlagResetPlot:
                    VIS_ind.img=0
                    VIS_ind.type=1
                    if data.Step==StepTypes.disp:
                        VIS_ind.variable=self.namesPIV.combo_dict[self.namesPIV.z]
                    else:
                        VIS_ind.variable=self.namesPIV.combo_dict[self.namesPIV.Mod]
                    VIS_ind.variableKey=self.namesPIV.combo_dict_keys[VIS_ind.variable]
                    VIS_ind.FlagResetLevels=VIS_ind.FlagResetSizes=True
                    self.FlagResetPlot=False
                pass
            else: 
                pri.Info.red(f'Current process type ({data.Step}) has no plot function available!')
                return
            if FlagCurrent:
                self.w_Vis.FlagReset=i==-1
                self.setTABpars_at(data.ind,FlagAdjustPar=True,widget=self.w_Vis)
                pri.Process.yellow(f'{"*"*50} Result plotted!')
        except Exception as inst:
            pri.Error.red('Error Plotting in progress_proc',color=PrintTA.red)
            traceback.print_exc()
            if Flag_fullDEBUG: pri.Error.red(f'\n{inst}')

    def showTimeToEnd(self,data:dataTreePar,time=0):
        if data.numCallBackTotOk:
            eta=data.deltaTime2String(data.eta) if time==0 else data.calcTimeStat(time,data.numCallBackTotOk)
        else:
            eta='no info'
        self.ui.time_stamp.show()
        self.ui.time_stamp.setText(f'Time to the end: {eta}')

#********************************** Pause
    @Slot(dataTreePar)
    def pause_proc(self,data:dataTreePar,errMessage=''):
        ''' pause_proc also when ends '''
        pri.Time.red(f'pause_proc Begin ')
        if errMessage: 
            self.procdata.warnings[0]+='\n\n'+data.headerSection('CRITICAL ERROR',errMessage,'X') 
        self.store_proc(data)

        if data.FlagFinished or errMessage!='': #save and continue 
            if self.FlagRun==0: # bug noto se uno mette in pausa mentre sta finendo di salvare (al 100%) da errore, basta ripremere play oppure eliminare il check
                pri.Process.red('**************************** pause_proc Error ****************************')
            else:
                self.nextProc()
        else:
            """
            if data.hasIndexOf(self.w_Tree.TABpar):
                self.w_Tree.selectFuture(0)
            if data.flagRun==-1:
                i:QTreeWidgetItem=self.w_Tree.TREpar.future[0]
                data.icon_type=self.Tree_icons.icontype('paused')
                i.setIcon(0,self.Tree_icons.paused)
            self.setButtons(data)
            """
       
        pri.Time.red(f'pause_proc END')
        self.signals.pause_proc.emit()       

    def store_proc(self,data_worker:dataTreePar):
        data=self.procdata #self.w_Tree.TABpar_prev[idata.indTree][idata.indItem][-1]
        for f in self.procFields:
            if f in self.procdata.uncopied_fields:
                i=self.procdata.uncopied_fields.index(f)
                self.procdata.uncopied_fields.pop(i)
        #Aggiusto ciò che deve essere aggiornato
        #if not data.numFinalized:  return
        pri.Time.yellow(f'{"-"*100} store PROC')

        data.onPauseTimeStat()

        #Copio ciò che è stato modificato nel worker
        #siccome data_worker sarà distrutto non faccio una deepcopy con copyfrom
        data.compMin=data_worker.compMin
        data.mediaPIV=data_worker.mediaPIV
        data.FlagFinished=data_worker.FlagFinished

        if data.Step == StepTypes.disp:
            data.res=data_worker.res
            data.laserConst=[const for const in data_worker.laserConst]
            indpar=[i for i in data.ind]
            OUT_ind:OUTpar=self.w_Output.TABpar_at(indpar)
            OUT_ind.res=data.res
            if OUT_ind.unit==0: 
                OUT_ind.xres=data.res
            if 'zconst' in data.OUT_dict and 'xterm' in data.OUT_dict and 'yterm' in data.OUT_dict:
                OUT_ind.zconst=data.OUT_dict['zconst']
                OUT_ind.xterm=data.OUT_dict['xterm']
                OUT_ind.yterm=data.OUT_dict['yterm']
            indpar[-2]+=1
            indpar[-1]=-1
            OUT_ind:OUTpar=self.w_Output.TABpar_at(indpar)
            OUT_ind.res=data.res
            if OUT_ind.unit==0: 
                OUT_ind.xres=data.res
            if 'zconst' in data.OUT_dict and 'xterm' in data.OUT_dict and 'yterm' in data.OUT_dict:
                OUT_ind.zconst=data.OUT_dict['zconst']
                OUT_ind.xterm=data.OUT_dict['xterm']
                OUT_ind.yterm=data.OUT_dict['yterm']
            ITE_ind:ITEpar=self.ui.Explorer.ITEfromInd(indpar)
            ITE_ind.procdata.res=data.res
            ITE_ind.procdata.laserConst=[const for const in data_worker.laserConst]
            if 'zconst' in data.OUT_dict and 'xterm' in data.OUT_dict and 'yterm' in data.OUT_dict:
                ITE_ind.procdata.OUT_dict['zconst']=data.OUT_dict['zconst']
                ITE_ind.procdata.OUT_dict['xterm']=data.OUT_dict['xterm']
                ITE_ind.procdata.OUT_dict['yterm']=data.OUT_dict['yterm']

        #Aggiusto ciò che deve essere aggiornato
        if data.nsteps==data.numCallBackTotOk: #data.FlagFinished:   #todo TA da GP: secondo te è corretto?
            flagRun=int(data.numFinalized==data.nsteps)+1
        else: 
            flagRun=-1  
        self.setFlagRun(data,flagRun)
        data.warnings[1]=''
        data.setCompleteLog()
        self.adjustSwitches()

        Process=[]
        for l in self.projectTree.itemList[1:]:
            Process.append([ l[data.ind[0]][data.ind[1]][data.ind[2]] ])
        filename=data.procOutName()
        try:
            saveList(Process,filename)
        except Exception as inst:
            #warningDialog(self,f'Error while saving the configuration file {filename}!')
            pri.Error.red(f'Error while saving the configuration file {filename}!\n{inst}')

        try:
            with open(data.outPathRoot+'.log', 'a') as file:
                file.write(data.Log)
        except:
            pri.Error.red(f'Error while trying to save the process log file: {data.outPathRoot}.log.\n{traceback.format_exc()}\n')
        try:
            with open(data.stepOutName()+'.log', 'w') as file:
                file.write(data.Log)
        except:
            pri.Error.red(f'Error while trying to save the process log file: {data.stepOutName()}.log.\n{traceback.format_exc()}\n') 
        if data.Step in (StepTypes.piv,StepTypes.spiv):
            data.writeCfgProcPiv()
          
        LOG_ind:LOGpar=self.w_Log.TABpar_at(data.ind)
        LOG_ind.text=data.Log
        self.w_Log.setLogText(FlagMoveToBottom=True)
        self.plotCurrent(data,-1,None,FlagBridge=True)
        
        #if not data.hasIndexOf(self.ui.Explorer.ITEpar):
        ITE:ITEpar=self.ui.Explorer.ITEfromInd(data.ind)
        self.ui.Explorer.setITElayout(ITE)
        self.inheritance(data.ind)
        self.adjustDependencies(ITE)
        self.ui.time_stamp.setText('')
        
        self.adjustSwitches()

        pri.Time.yellow(f'{"-"*100} store PROC  END')

    @Slot()
    def buttonPauseHideShow(self):
        #pr ('buttonPauseHideShow')
        self.ui.button_pause.setEnabled(True) #.show()

    @Slot()
    def stopProcs(self):
        self.contProc+=1
        if self.procdata:
            pri.Time.red(f'stopProcs     self.contProc={self.contProc}/{self.nProc}   self.numCallBackTotOk={self.numCallBackTotOk}  numFinalized={self.procdata.numFinalized}  {self.FlagRun}')
        
        FlagEnd = self.contProc==self.indProc+1 if self.FlagRun==2 else self.contProc==self.nProc
        if FlagEnd: 
            self.ui.Explorer.updateSwitchMovies(self.currind,FlagStart=False)
            self.setSwitchEnabled(True)
            self.disableDropping(False)
            self.procdata=None
            self.currind=None

            self.setEnabled(True)
            self.procWorkers=[]
            self.FlagRun=0
            self.putStepsInQueue()
            self.ui.button_pause.setEnabled(True)
            self.ui.button_Run.setEnabled(True)
            self.setButtonPause(True)
           
            self.closeIfRequested()

    def putStepsInQueue(self):
        if self.FlagRun:
            self.dataFlagRuns=[]
        for k,data in enumerate(self.dataQueue):
            if self.FlagRun:
                self.dataFlagRuns.append(data.flagRun)
                self.setFlagRun(data,-10)
            elif data.flagRun==-10:
                self.setFlagRun(data,self.dataFlagRuns[k])
            else:
                continue
            ITE_ind:ITEpar=self.ui.Explorer.ITEfromInd(data.ind)
            self.ui.Explorer.setITElayout(ITE_ind)
        self.ui.Explorer.arrangeCurrentProcess(self.processTree)
        
    def closeIfRequested(self):
        self.ui.label_updating_pairs.setVisible(False)
        if self.waitingDialog:
            self.waitingDialog.done(0)
            self.waitingDialog=None
        if self.completingTask:
            self.completingTask()
            self.completingTask=None
        """
        if self.FlagClosing[0]:
            self.correctClose()
        """

#********************************************* CalVi
    def runCalVi(self):
        self.w_Vis_CalVi.VISpar.FlagRunning=not self.w_Vis_CalVi.VISpar.FlagRunning
        if self.w_Vis_CalVi.VISpar.FlagRunning:
            """
            prev=self.w_Vis_CalVi.TABpar_prev_at(self.w_Vis_CalVi.TABpar.ind)
            step=len(prev)-1-self.w_Vis_CalVi.TABpar.ind[-1]
            self.button_back_forward_action(step)
            self.w_Vis_CalVi.VISpar.FlagRunning=True
            """
            self.w_Vis_CalVi.VISpar.FlagRunning=False
            self.w_Calibration.fullCallback()
            self.w_Vis_CalVi.VISpar.FlagRunning=True

            self.disableTab_Vis(self.w_Vis_CalVi.VISpar.FlagRunning)

            self.initDataAndSetImgFromGui(self.w_Input_CalVi.INPpar,self.w_Process_CalVi.PROpar)
            FlagResume=self.w_Vis_CalVi.FlagResume
            def removeQuestion():
                if FlagResume!=1: return
                camString=''
                cams=self.w_Input_CalVi.INPpar.cams
                if self.w_Input_CalVi.INPpar.FlagCam:
                    if len(cams)==1: camString=f'_cam{cams[0]}'
                else:
                    cams=[-1]
                data=self.w_Vis_CalVi.calibView.calib.cal.data
                varName=f'{data.percorsoOut}{data.NomeFileOut}{camString}{outExt.calvi}'
                questionMessage=f'The calibration result file:\n{varName}\nalready exists in the current output path. The above error could arise from the attempt of loading such a file.\n\nDo you want to remove the file from the disk?\n\n(Please, consider to choose a different output name root for your process)'
                if questionDialog(self,questionMessage):
                    os.remove(varName)
            if self.w_Input_CalVi.INPpar.errorMessage:
                warningDialog(self,self.w_Input_CalVi.INPpar.errorMessage)
                self.abortCalVi()
                return removeQuestion()
            if self.w_Vis_CalVi.VISpar.errorMessage:
                warningDialog(self,self.w_Vis_CalVi.VISpar.errorMessage)
                self.abortCalVi()
                return removeQuestion()
            if not all([all(imExc) for imExc in self.w_Vis_CalVi.VISpar.imEx]):
                imageFile=''
                for k in range(len(self.w_Vis_CalVi.VISpar.imEx)):
                    for j in range(len(self.w_Vis_CalVi.VISpar.imEx[k])):
                        if not self.w_Vis_CalVi.VISpar.imEx[k][j]:
                            imageFile=self.w_Vis_CalVi.VISpar.imList[k][j]
                            break
                    if imageFile: break
                Message=f'No valid image files found!\n[{imageFile},...]'
                warningDialog(self,Message)
                self.abortCalVi()
                return removeQuestion()
            self.w_Vis_CalVi.buttonAction()
            pri.Info.cyan(f'Running calibration   FlagRestart={self.w_Vis_CalVi.FlagResume}')
            if self.w_Vis_CalVi.FlagResume>-1:
                self.w_Vis_CalVi.runCalVi(flagMod=bool(self.w_Vis_CalVi.FlagResume))
            else:
                flagYes=self.questionDialog('A calibration result file already exists in the current output path. Do you want to overwrite it?')
                if flagYes: 
                    self.w_Vis_CalVi.FlagResume=0
                    self.w_Vis_CalVi.runCalVi(flagMod=False)
                else: 
                    self.runCalVi()
        else:
            self.disableTab_Vis(self.w_Vis_CalVi.VISpar.FlagRunning)
            
            if self.w_Vis_CalVi.FlagResume>-1: 
                self.saveCal()
                if self.w_Vis_CalVi.calibView.calib.FlagCalibration and ( (self.w_Process_CalVi.PROpar.FlagPlane and not self.w_Process_CalVi.PROpar.CalibProcType==0) or self.w_Process_CalVi.PROpar.CamMod==4 ):
                    if self.w_Input_CalVi.INPpar.FlagOptPlane: self.savePlanePar()
                    self.updateINPpar()
                    self.saveCal('_Mod')
                if self.w_Vis_CalVi.calibView.calib.FlagCalibration:
                    self.appendCalibration()
            #indTree,indItem,ind=self.w_Import.INPpar.indexes()
            #self.actualBridge('Import',indTree,indItem,ind)
            self.initDataAndSetImgFromGui(self.w_Input_CalVi.INPpar,self.w_Process_CalVi.PROpar)
            self.w_Vis_CalVi.stopCalVi()

            self.closeIfRequested()
            
    def abortCalVi(self):
        self.w_Vis_CalVi.FlagResume=-1
        self.runCalVi()

    def updateINPpar(self):
        if self.w_Process_CalVi.PROpar.FlagPlane:
            costPlanes=self.w_Vis_CalVi.calibView.calib.cal.vect.costPlanes
            for i in range(len(self.w_Input_CalVi.INPpar.filenames)):
                self.w_Input_CalVi.INPpar.plapar[i]=[round(p,3) for p in costPlanes[i]]
        if self.w_Process_CalVi.PROpar.CamMod==4:
            cost=self.w_Vis_CalVi.calibView.calib.cal.vect.cost[0]
            self.w_Process_CalVi.PROpar.CylRad=cost[21]
            self.w_Process_CalVi.PROpar.CylThick=cost[22]
            self.w_Process_CalVi.PROpar.CylNRatio=cost[23]
        self.w_Input_CalVi.fullCallback()

    def appendCalibration(self):
        INP=self.w_Input_CalVi.INPpar
        data=self.w_Vis_CalVi.calibView.calib.cal.data
        if INP.FlagCam:
            outFiles=[f'{data.percorsoOut}{data.NomeFileOut}{c}.cal' for c in INP.cams]
        else:
            outFiles=[f'{data.percorsoOut}{data.NomeFileOut}{1}.cal']
        appendedFiles=[f for f in outFiles if f not in self.w_Calibration.CALpar.calList]
        self.w_Calibration.buttonAction()
        if len(appendedFiles)==0: return
        if self.w_Calibration.CALpar.ncam==len(self.w_Calibration.CALpar.calList):
            warningDialog(self,f'The calibration file list already contains a number of files equal to the number of cameras specified ({self.w_Calibration.CALpar.ncam}). The results of the current CalVi process will not be appended to the list.')
        else:
            self.w_Calibration.ui.calTree.importLists(appendedFiles)
            self.w_Calibration.copyListsFromTree()
            #self.w_Calibration.nullCallback()
            self.w_Calibration.adjustTABparInd()

    def saveCal(self,add_str=''):
        VIS=self.w_Vis_CalVi.VISpar
        data=self.w_Vis_CalVi.calibView.calib.cal.data
        calVect=self.w_Vis_CalVi.calibView.calib.cal.vect
        VIS.orPosAndShift=[]
        VIS.angAndMask=[]
        VIS.spotDistAndRemoval=[]
        for c in range(data.NCam):
            for p1 in range(data.Numpiani_PerCam):
                p=p1+c*data.Numpiani_PerCam
                VIS.orPosAndShift.append([])
                VIS.angAndMask.append([])
                VIS.spotDistAndRemoval.append([])

                VIS.orPosAndShift[p].append(float(calVect.XOr[p] - data.ColPart))
                VIS.orPosAndShift[p].append(float(calVect.YOr[p] - data.RigaPart))
                VIS.orPosAndShift[p].append(float(calVect.xOrShift[p]))
                VIS.orPosAndShift[p].append(float(calVect.yOrShift[p]))
                
                VIS.angAndMask[p].append(float(calVect.angCol[p]))
                VIS.angAndMask[p].append(float(calVect.angRow[p]))
                for i in self.w_Vis_CalVi.calibView.calib.cal.getPuTrovaCC(p):
                    VIS.angAndMask[p].append(float(i))

                VIS.spotDistAndRemoval[p].append(float(calVect.dColPix[p]))
                VIS.spotDistAndRemoval[p].append(float(calVect.dRigPix[p]))
                VIS.spotDistAndRemoval[p].append(float(calVect.remPointsUp[p]))
                VIS.spotDistAndRemoval[p].append(float(calVect.remPointsDo[p]))
                VIS.spotDistAndRemoval[p].append(float(calVect.remPointsLe[p]))
                VIS.spotDistAndRemoval[p].append(float(calVect.remPointsRi[p]))
        
        INP=self.w_Input_CalVi.INPpar
        camString=''
        if INP.FlagCam: 
            if len(INP.cams)==1: camString=f'_cam{INP.cams[0]}'
        varName=f'{data.percorsoOut}{data.NomeFileOut}{camString}{add_str}{outExt.calvi}'
        var=[INP,self.w_Process_CalVi.PROpar,VIS,myStandardPath(os.path.dirname(varName))]
        try:
            with open(varName,'wb') as file:
                pickle.dump(var,file)
                pri.Info.blue(f'>>> Saving calibration process file {varName}')    
        except:
            pri.Error.red(f'Error while trying to save the calibration process file: {varName}.\n{traceback.format_exc()}\n')   

        self.w_Input_CalVi.adjustTABparInd()
        self.w_Process_CalVi.adjustTABparInd()
        self.w_Vis_CalVi.adjustTABparInd()     
        Process=[]
        for l in self.projectTree.itemList[1:]:
            Process.append([ l[INP.ind[0]][INP.ind[1]][INP.ind[2]] ])
        filename=f'{data.percorsoOut}{data.NomeFileOut}{camString}{add_str}{outExt.cal}'
        try:
            saveList(Process,filename)
        except Exception as inst:
            #warningDialog(self,f'Error while saving the configuration file {filename}!')
            pri.Error.red(f'Error while saving the configuration file {filename}!\n{inst}')
        return
    
    def savePlanePar(self):
        data=self.w_Vis_CalVi.calibView.calib.cal.data
        calVect=self.w_Vis_CalVi.calibView.calib.cal.vect
        INP=self.w_Input_CalVi.INPpar
        if len(INP.cams)==1: camString=f'_cam{INP.cams[0]}'
        else: camString=''
        plaparRad=f'{data.percorsoOut}{data.NomeFileOut}{camString}_plane'
        plapar_names=['beta  (°)','alpha (°)','gamma (°)','x (mm)','y (mm)','z (mm)']
        for i,c in enumerate(calVect.costPlanes):
            dp={}
            for p,v in zip(plapar_names,c):
                dp[p]=v
            plaparName=plaparRad+f"{i+1:d}_z{dp['z (mm)']:.2f}{outExt.pla}"
            try:
                with open(plaparName,'w') as file:
                    file.write(str(dp).replace('{','{\n ').replace(',',',\n').replace('}','\n}'))
            except:
                pri.Error.red(f'Error while trying to save the plane parameter file: {plaparName}.\n{traceback.format_exc()}\n')  
            pri.Info.blue(f'    Saving plane data file {plaparName}')

    def setRunCalViButtonText(self,FlagRunning=True):
        button=self.ui.button_Run_CalVi
        if not FlagRunning:
            flag=bool(self.w_Vis_CalVi.VISpar.errorMessage) or bool(self.w_Input_CalVi.INPpar.errorMessage) 
            if flag:
                fPixSize=button.font().pixelSize()
                s=f'<sup><span style=" font-size:{fPixSize-2}px"> ⚠</span></sup>'
            else:
                s=''
            text='Run'
            button.setIcon(self.icon_play)
            tooltip=f'Run CalVi{" (some issues detected!)" if flag else ""}'
        else:
            s=''
            text='Save'
            button.setIcon(self.icon_save_and_stop)
            tooltip='Quit CalVi and save results'
        button.setText(text+s)
        tooltip+=' ('+button.shortcut().toString(QKeySequence.NativeText)+')'
        button.setToolTip(tooltip)
        button.setStatusTip(tooltip)

    def disableTab_Vis(self,Flag=True):
        self.ui.w_Managing_Tabs.setEnabled(not Flag)
        for w in self.tabWidgets:
            w:gPaIRS_Tab
            if w!=self.w_Vis_CalVi and w!=self.ui.tabAreaWidget:
                w.setEnabled(not Flag)
        self.w_Input.ui.button_back.setEnabled(not Flag)
        self.w_Input.ui.button_forward.setEnabled(not Flag)
        self.ui.button_Run_CalVi.setVisible(not Flag)
        self.ui.button_Abort_CalVi.setVisible(Flag)
        self.setRunCalViButtonText(FlagRunning=Flag)

        self.ui.tabAreaWidget.FlagDisplayControls=not Flag
        self.ui.tabAreaWidget.ui.button_restore_undo.setVisible(not Flag)
        self.ui.tabAreaWidget.ui.button_back.setVisible(not Flag)
        self.ui.tabAreaWidget.ui.button_forward.setVisible(not Flag)
        self.ui.tabAreaWidget.display_controls()

        self.ui.label_updating_pairs.setVisible(Flag) 

    def initDataAndSetImgFromGui(self,INP,PRO):
        self.w_Vis_CalVi.initDataFromGui(INP,PRO)
        inddel=self.w_Vis_CalVi.setImgFromGui()
        if len(inddel): #todo GP: migliorare? (setto due volte le immagini e faccio in calib il check)
            Message=f'The following image files encountered issues while importing (they may have incompatible sizes with the first image file of the list "{self.w_Input_CalVi.INPpar.filenames[0]}" or be not in grayscale format):\n'
            for k in inddel:
                if k==inddel[-1]: colon='.'
                else: colon=';'
                Message+=f'- {self.w_Input_CalVi.INPpar.filenames[k]}{colon}\n'
            Message+='They will not be added to the list.'
            self.warningDialog(Message)
            for i in range(len(inddel)-1,-1,-1):
                k=inddel[i]
                self.w_Input_CalVi.INPpar.filenames.pop(k)
                self.w_Input_CalVi.INPpar.plapar.pop(k)
            self.w_Input_CalVi.adjust_list_images()
            #self.w_Input_CalVi.nullCallback()
            self.w_Input_CalVi.adjustTABparInd()
            self.w_Vis_CalVi.initDataFromGui(INP,PRO)
            self.w_Vis_CalVi.setImgFromGui()

#********************************************* LEGACY
    def setUpdatingState(self,flagUpdating):
        if Flag_DISABLE_onUpdate: 
            for tname in self.TABnames:
                w: gPaIRS_Tab
                wname='w_'+tname
                w=getattr(self,wname)
                if tname=='Vis':
                    w.ui.w_plot.setEnabled(not flagUpdating)
                else:
                    w.ui.scrollArea.setEnabled(not flagUpdating)
            #w.setVisible(not flag)
        self.ui.label_updating_import.setVisible(flagUpdating)
        pass

#*************************************************** Parallel Pool
    def launchParPool(self,nworkers):
        # TA ho deciso di utilizzare concurrent.futures per lanciare il processo in parallelo perchè non ho capito bene come usare 
        # quello di QT
        # Avevo provato anche Thread ma non sono stato capace di capire come lanciare 
        # Ho provato a lanciare le due operazioni all'interno di initParForAsync in parallelo ma mi sembra che sia molto lento
        # Alla fine ho adottato una configurazione mista con initParForAsync scritta in mod asincrono
        # Quando initParForAsync termina chiama initParForComplete che effettua le ultime cose 

        if hasattr(self, 'pfPool'):#this function should be called only once but just in case we check and close the parPool
          self.pfPool.closeParPool()
        else:
          self.pfPool=None
          self.parForMul=None
        self.FlagParPoolInit=False
        self.signals.parPoolInit.connect(self.parPoolInitSetup)
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        f3=executor.submit(asyncio.run,initParForAsync(nworkers))
        def initParForComplete(_f3):
          pri.Time.blue(0,'fine initParFor1')
          (pfPool,parForMul)=f3.result()
          #timesleep(5)
          pri.Time.blue(0,'PIV_ParFor_Worker dopo ParForMul')
          parForMul.sleepTime=ParFor_sleepTime #time between calls of callBack
          self.pfPool=pfPool
          self.parForMul=parForMul
          self.parForMul.numUsedCores=self.numMaxProcs # =NUMTHREADS_MAX#potrebbe essere minore di NUMTHREADS_PIV_MAX con cui è stato impostato
          self.FlagParPoolInit=True
          self.signals.parPoolInit.emit()
        f3.add_done_callback(initParForComplete)

    @Slot(int)
    def parPoolInitSetup(self):
        if self.FlagGuiInit:
            if not self.FlagParPoolInit:
                self.FlagParPoolInit=False
        
                self.ui.label_gif.setPixmap(QPixmap())
                self.ui.label_gif.setMovie(self.load_gif)
                
                self.ui.label_loading.setText('Starting parallel pool with') 
                self.ui.spin_nworkers.setEnabled(False)
                self.ui.label_loading_2.setText('workers...') 
            else:
                self.ui.button_Run.setEnabled(True)

                self.ui.label_gif.setMovie(QMovie())
                self.ui.label_gif.setPixmap(self.loaded_map)
                
                self.ui.label_loading.setText('Parallel pool with')
                self.ui.spin_nworkers.setEnabled(True)
                self.ui.label_loading_2.setText('workers started!')   
                #self.repaint()                

    def spin_nworkers_action(self):
        val=self.ui.spin_nworkers.value() 
        self.GPApar.NumCores=val
        if val <=NUMTHREADS_MAX:
            self.numMaxProcs=val 

#*************************************************** Warnings
    def warningDialog(self,Message,time_milliseconds=0,flagScreenCenter=False,icon=QIcon(),palette=None,pixmap=None,title='Warning!',flagRichText=False,flagNoButtons=False,addButton:dict=None):
        return warningDialog(self,Message,time_milliseconds,flagScreenCenter,icon,palette,pixmap,title,flagRichText,flagNoButtons,addButton)

    def questionDialog(self,Message):
        flagYes=questionDialog(self,Message)
        return flagYes

#*************************************************** Checking
    def checkProcesses(self,FlagInit=False,ind=None):
        FlagCheck=ind is None
        if ind is not None: projects=self.projectTree.itemList[1][ind[0]:ind[0]+1]
        else: projects=self.projectTree.itemList[1]
        for ITEs_project in projects:
            if ind is not None: ITEs_project_ind=ITEs_project[ind[1]:ind[1]+1]
            else: ITEs_project_ind=ITEs_project
            for ITEs_tree in ITEs_project_ind:
                if ind is not None: ITEs_tree_ind=ITEs_tree[ind[2]:ind[2]+1]
                else: ITEs_tree_ind=ITEs_tree
                for ITEs in ITEs_tree_ind:
                    if ind is not None: ITEs_ind=ITEs[ind[3]+1:ind[3]+2]
                    else: ITEs_ind=ITEs
                    for ITE in ITEs_ind:
                        ITE:ITEpar
                        ITE.FlagInit=FlagInit
                        indITE=ITE.ind
                        if  ind is not None: FlagCheck=True
                        for w in self.tabWidgets: 
                            w:gPaIRS_Tab
                            TABpar_ind:TABpar=w.TABpar_at(indITE)
                            if TABpar_ind:
                                if FlagInit:
                                    w.checkTABpar(indITE)
                                    w.setTABwarn(indITE)
                                    TABpar_ind.FlagInit=True
                                else:
                                    TABpar_ind.FlagInit=False
        return FlagCheck
    
#*************************************************** Projects
    def pauseQuestion(self,taskDescription='continuing',task=lambda:None,FlagFirstQuestion=False):
        if FlagFirstQuestion:
            if not self.questionDialog(f'Are you sure you want to proceed with {taskDescription}?'): 
                return
        if self.FlagRun or self.w_Vis_CalVi.VISpar.FlagRunning:
            if self.FlagRun: currentTaskDescription='PaIRS is currently executing the processes in the current workspace. '
            elif self.w_Vis_CalVi.VISpar.FlagRunning: currentTaskDescription='CalVi is currently running. '
            if self.questionDialog(f'{currentTaskDescription}Do you want to pause them before {taskDescription}?'): 
                if self.FlagRun: self.button_run_pause_action()
                self.setEnabled(False)
                self.completingTask=task
                self.waitingDialog=self.warningDialog('Please, wait while stopping the running processes!',pixmap=''+ icons_path +'sandglass.png',flagNoButtons=True)
                if self.w_Vis_CalVi.VISpar.FlagRunning: self.abortCalVi()
        else:
            task()
        return

    def open_project(self):
        filename, _ = QFileDialog.getOpenFileName(self,\
            "Select a PaIRS project file", filter=f'*{outExt.proj}',\
                #dir=self.w_Input.INPpar.path,\
                options=optionNativeDialog)
        if not filename: return
        errorString=''
        try:
            data, errorMessage=loadList(filename)
            errorString+=errorMessage
        except:
            errorString+=traceback.format_exc()
        if errorString:
            WarningMessage=f'Error with loading the file: {filename}\n'
            warningDialog(self,WarningMessage)
            pri.Error.red(f'{WarningMessage}\n{errorString}\n')
        try:
            ind=self.projectTree.topLevelItemCount()
            insert_at_depth(self.projectTree.itemList,self.projectTree.listDepth,ind,data)
            self.modifyWorkspace()
            TRE:TREpar=self.projectTree.itemList[0][ind]
            TRE.project=ind
            self.projectTree.createProjectItem(ind,FlagNewItem=False)
            item=self.projectTree.topLevelItem(ind)
            self.projectTree.setCurrentItem(item)
            item.setSelected(True)  
            self.adjustItemWidgets()
        except Exception as inst:
            WarningMessage=f'Error while retrieving the project "{data[0][0].name}" from the file: {filename}\n'
            warningDialog(self,WarningMessage)
            pri.Error.red(f'{WarningMessage}\n{traceback.format_exc()}\n')
        return

    def saveas_current_structure(self,name:str='',ext='',saveList=lambda f:None,par:TABpar=None,FlagSave=True):
        Title=f"Select location and name of the {name} file to save"
        filename, _ = QFileDialog.getSaveFileName(self,Title, 
                dir=par.name.replace(' ','_'),  #self.w_Input.INPpar.path+par.name.replace(' ','_'), 
                filter=f'*{ext}',\
                options=optionNativeDialog)
        if not filename: return
        if len(filename)>=len(ext):
            if filename[-len(ext):]==ext: filename=filename[:-len(ext)]  #per adattarlo al mac
        filename=myStandardRoot('{}'.format(str(filename)))
        if not outExt.cfg in filename:
            filename=filename+ext
        if FlagSave:saveList(filename)
        return filename

    def updateWorkspaceTitle(self):
        self.GPApar.name=self.ui.title_workspace.label.text().replace(self.GPApar.saveBullet(),'')
        self.GPApar.FlagSaved=False
        self.adjustWorkspaceHeader()
        
    def save_current_project(self,filename):
        Project=[]
        FlagSaved=False
        for l in self.projectTree.itemList:
            Project.append([l[self.TREpar.project]])
        try:
            TRE:TREpar=self.projectTree.itemList[0][self.TREpar.project]
            TRE.outName=filename
            TRE.savedDate=currentTimeString()
            TRE.FlagSaved=True
            saveList(Project,filename)
        except Exception as inst:
            warningDialog(self,f'Error while saving the file {filename}!\nPlease, retry.')
            pri.Error.red(f'Error while saving the file {filename}!\n{inst}')
        else:
            self.TREpar.copyfrom(TRE)
            self.adjustItemWidgets()
            FlagSaved=True
        return FlagSaved
    
    def saveas_current_project(self):
        self.saveas_current_structure(name='project',ext=outExt.proj,saveList=lambda f: self.save_current_project(f),par=self.TREpar)
    
    def save_project(self):
        FlagSaved=False
        if self.TREpar.outName:
            filename=self.TREpar.outName
            if self.TREpar.FlagRunnable and self.TREpar.FlagQueue:
                self.pauseQuestion('saving the selected project',lambda: self.save_current_project(filename),FlagFirstQuestion=self.FlagRun!=0)
            else:
                FlagSaved=self.save_current_project(filename)
        else:
            FlagSaved=self.saveas_project()
        return FlagSaved

    def saveas_project(self):
        FlagSaved=False
        if self.TREpar.FlagRunnable and self.TREpar.FlagQueue:
            self.pauseQuestion('saving the selected project',self.saveas_current_project)
        else:
            FlagSaved=self.saveas_current_project()
        return FlagSaved

    def close_project(self):
        self.pauseQuestion('closing the selected project',lambda: ProjectTree.button_close_action(self.projectTree))

    def clean_projects(self):
        self.pauseQuestion('closing all the projects',lambda: ProjectTree.button_clean_action(self.projectTree))

    def copy_process(self):
        if self.ui.Explorer.ITEpar.FlagQueue and self.ui.Explorer.currentTree==self.processTree:
            self.pauseQuestion('copying the selected process',lambda: ProcessTree.button_copy_action(self.processTree))

    def delete_process(self):
        if self.ui.Explorer.currentTree==self.processTree:
            #if self.ui.Explorer.ITEpar.FlagQueue: self.ui.Explorer.ITEpar.FlagQueue=False
            self.pauseQuestion('deleting the selected process',lambda: ProcessTree.button_delete_action(self.processTree))
    
    def clean_processes(self):
        if self.ui.Explorer.currentTree==self.processTree:
            self.pauseQuestion('cleaning the whole process list',lambda: ProcessTree.button_clean_action(self.processTree))

#*************************************************** Sizes, font & layout
    def updateGPAparGeometry(self):
        self.GPApar.Geometry=self.saveGeometry().toBase64().data().decode()
        self.GPApar.WindowState=self.saveState().toBase64().data().decode()
        #g=self.geometry()
        #self.GPApar.Geometry=[g.x(), g.y(), g.width(), g.height()]
        #self.GPApar.WindowState=[self.windowState().value,self.windowState().name]
        splitterSizes={}
        for s in self.ui.Explorer.findChildren(QSplitter)+[self.ui.main_splitter,self.ui.Operating_Tabs_splitter]:
            s:QSplitter
            pri.Coding.green(f'splitterSizes: {s.objectName()}')
            splitterSizes[s.objectName()]=s.sizes()
        self.GPApar.SplitterSizes=splitterSizes
        scrollAreaValues={}
        for a in self.ui.Explorer.findChildren(QScrollArea):
            a:QScrollArea
            pri.Coding.blue(f'scrollArea: {a.objectName()}')
            scrollAreaValues[a.objectName()]=[a.horizontalScrollBar().value(),a.verticalScrollBar().value()]
        self.GPApar.ScrollAreaValues=scrollAreaValues
        return
        
    def setFontPixelSize(self):
        if self.fontPixelSize==self.GPApar.fontPixelSize: return
        fPixSize=self.GPApar.fontPixelSize
        font=QFont()
        font.setFamily(fontName)
        font.setPixelSize(fPixSize)
        if self.app: self.app.setFont(font)
        setFontPixelSize(self,fPixSize)
        self.setFurtherFontPixelSizes(fPixSize)
        if self.aboutDialog:
            self.aboutDialog.fontPixelSize=self.GPApar.fontPixelSize
            self.aboutDialog.setFontSizeText()
        if self.logChanges: self.logChanges.setFontPixelSize(fPixSize)
        if self.menuDebug: self.menuDebug.setFont(self.ui.menuFile.font())
        self.fontPixelSize=fPixSize
    
    def setFurtherFontPixelSizes(self,fPixSize):
        self.setTabFontPixelSize(fPixSize)

        lab:QLabel=self.ui.title
        fPixSize_TabNames=min([fPixSize*2,30])
        font=lab.font()
        font.setFamily(fontName)
        font.setPixelSize(fPixSize_TabNames)
        lab.setFont(font)
        self.ui.title_workspace.setFont(font)
        
        lab:QLabel=self.ui.subtitle
        font=lab.font()
        font.setFamily(fontName)
        font.setPixelSize(fPixSize+4)
        lab.setFont(font)
        self.ui.subtitle_workspace.setFont(font)

        lab:QLabel=self.onlyReadLabel
        font=lab.font()
        font.setFamily(fontName)
        font.setPixelSize(fPixSize+1)
        lab.setFont(font)

        self.ui.projectPage.setFontPixelSize(fPixSize)
        self.ui.processPage.setFontPixelSize(fPixSize)
        self.ui.stepPage.setFontPixelSize(fPixSize)

        self.w_Log.setLogFont(fontPixelSize-dfontLog)
        self.w_Vis_CalVi.setLogFont(fontPixelSize-dfontLog)

    def setTabFontPixelSize(self,fPixSize):
        fPixSize_TabNames=min([fPixSize*2,30])
        for w in self.ui.tabAreaWidget.widgets:
            setFontPixelSize(w,fPixSize)
            w:gPaIRS_Tab
            for lab in w.findChildren(QLabel):
                lab:QLabel
                if 'name_tab' in lab.objectName():
                    #lab:QLabel=w.ui.name_tab
                    font=lab.font()
                    font.setPixelSize(fPixSize_TabNames)
                    lab.setFont(font)

    def falseShow(self):
        FlagHidden=not self.isVisible()
        total_rect = QGuiApplication.primaryScreen().geometry()
        for screen in QGuiApplication.screens():
            total_rect = total_rect.united(screen.geometry())
        self.move(total_rect.right() + 100, total_rect.bottom() + 100)
        self.updateGeometry()
        self.show()
        self.repaint()
        return FlagHidden
    
    def setDefaultSizes(self):
        margins=self.ui.centralLayout.contentsMargins()
        main_splitter_sizes=[self.ui.w_Managing_Tabs.baseSize().width(),self.ui.tabAreaWidget.widgetMinimumWidth*2+self.ui.tabAreaWidget.margin*2+self.ui.tabAreaWidget.handleWidth*2] #processTree, main_sep, tabAreaWidget
        w=margins.left()+self.ui.main_splitter.handleWidth()*2+sum(main_splitter_sizes)+margins.right()
        h=margins.top()+self.ui.w_header.minimumHeight()+self.ui.tabAreaWidget.tabAreaHeight+self.ui.tabAreaWidget.buttonSize[1]+self.ui.tabAreaWidget.buttonSpacing+self.ui.tabAreaWidget.margin*2+self.ui.w_Operating_Tabs.layout().spacing()+self.ui.statusbar.minimumHeight()+margins.bottom()
        self.resize(w,h)
        self.ui.main_splitter.setSizes(main_splitter_sizes)
        self.updateGeometry()
        x=(self.maximumGeometry.width()-w)*0.5
        y=(self.maximumGeometry.height()-h)*0.5
        if self.falseShow(): self.hide()
        self.move(x,y)
        self.app.processEvents()
        self.updateGPAparGeometry()
        
    def setGPaIRSTitle(self):
        cfgString=f': {self.GPApar.outName}' if self.GPApar.outName and self.GPApar.outName!=lastcfgname else ''
        if not self.GPApar.FlagSaved: cfgString+='*'
        if Flag_DEBUG:#TA per non incasinarmi
            windowTitle=f'PaIRS (v{version}.{__subversion__} - {__date__}) -- cfg v{uicfg_version} -- PIV {self.PIVvers} -- {platform.system()} -- Python {platform.python_version()}'
        else:
            windowTitle=f'PaIRS (v{version})'
        windowTitle+=cfgString
        self.setWindowTitle(windowTitle)

#*************************************************** Menus
#********************* File
    def setGPAlayout(self):
        self.setFontPixelSize()
        self.setGPaIRSPalette()
    
        geometry=QByteArray.fromBase64(self.GPApar.Geometry.encode())
        self.restoreGeometry(geometry)
        #if isinstance(self.GPApar.Geometry,list) and len(self.GPApar.Geometry)==4:
        #    g=self.GPApar.Geometry
        #    try:
        #        self.setGeometry(g[0],g[1],g[2],g[3])
        #    except:
        #        pri.Info.yellow(f'Error while restoring geometry:\n{traceback.format_exc()}\n\nDefault sizes will be set!\n\n')
        #       self.setDefaultSizes()
        #else:
        #    self.setDefaultSizes()
        
        windowState = QByteArray.fromBase64(self.GPApar.WindowState.encode())
        self.restoreState(windowState)
        #try:
        #    s=self.GPApar.WindowState
        #    self.setWindowState(Qt.WindowState(s[0]))
        #except:
        #    pri.Info.yellow(f'Error while restoring window state:\n{traceback.format_exc()}\n\nDefault window state will be set!\n\n')
            
        for s in self.ui.Explorer.findChildren(QSplitter)+[self.ui.main_splitter,self.ui.Operating_Tabs_splitter]:
            s:QSplitter
            if s.objectName() in self.GPApar.SplitterSizes:
                s.setSizes(self.GPApar.SplitterSizes[s.objectName()])
        for a in self.ui.Explorer.findChildren(QScrollArea):
            a:QScrollArea
            if a.objectName() in self.GPApar.ScrollAreaValues:
                scrollAreaValues=self.GPApar.ScrollAreaValues[a.objectName()]
                a.horizontalScrollBar().setValue(scrollAreaValues[0])
                a.verticalScrollBar().setValue(scrollAreaValues[1])
        self.setNumCores()

    def setNumCores(self):
        if self.GPApar.NumCores >NUMTHREADS_MAX:
            self.GPApar.NumCores=NUMTHREADS_MAX
        self.numTotUsedThreads=self.GPApar.NumCores  
        self.ui.spin_nworkers.setValue(self.GPApar.NumCores) 

    def modifyWorkspace(self):
        self.GPApar.modifiedDate=currentTimeString()
        self.GPApar.date=f'Modified : {self.GPApar.modifiedDate}'
        self.GPApar.FlagSaved=False

    def new_workspace(self):
        filename=self.saveas_current_structure(name='workspace',ext=outExt.wksp,saveList=lambda f: self.save_current_workspace(f),par=self.GPApar,FlagSave=False)
        self.GPApar.copyfrom(GPApar(),exceptions=self.GPApar.stateFields)
        self.GPApar.outName=filename
        self.GPApar.createdDate=currentTimeString()
        self.GPApar.modifiedDate=self.GPApar.createdDate
        self.GPApar.date=f'Modified : {self.GPApar.modifiedDate}'
        self.projectTree.clean_workspace()
        self.adjustProjectSelection()

    def new_workspace_debug(self):
        self.GPApar.copyfrom(GPApar(),exceptions=self.GPApar.stateFields)
        self.projectTree.clean_workspace()
        self.adjustProjectSelection()

    def menu_new_action(self):
        taskDescription='creating a new workspace'
        if not self.GPApar.FlagSaved:
            if self.questionDialog(f'The current workspace is unsaved. Do you want to save it before {taskDescription}?'):
                self.menu_save_action()
        self.pauseQuestion(taskDescription,self.new_workspace,FlagFirstQuestion=True)

    def open_workspace(self,filename='',FlagSetGeometry=False):
        pri.Time.cyan('Open workspace: init')
        if filename=='':
            filename, _ = QFileDialog.getOpenFileName(self,\
                "Select a PaIRS workspace file", filter=f'*{outExt.wksp}',\
                    #dir=self.w_Input.INPpar.path,\
                    options=optionNativeDialog)
        if not filename: return
        waitingWindow=warningDialog(self,'Please, wait while retrieving previous workspace!\n(If this action takes too much time, please consider to close the workspace before quitting PaIRS next time.)',pixmap=''+ icons_path +'sandglass.png',flagNoButtons=True,flagScreenCenter=True)
        self.app.processEvents()
        errorString=''
        try:
            data, errorMessage=loadList(filename)
            errorString+=errorMessage
            pri.Time.cyan('Open workspace: load')
        except:
            errorString+=traceback.format_exc()
        if errorString:
            WarningMessage=f'Error with loading the file: {filename}\n'
            warningDialog(self,WarningMessage)
            pri.Error.red(f'{WarningMessage}\n{errorString}\n')
        try:
            self.projectTree.clean_action()
            #all_indexes=[i for i in range(len(data[2]))]
            insert_at_depth(self.projectTree.itemList,self.projectTree.listDepth,0,data[2])
            self.checkProcesses()
            self.ui.Explorer.ITEpar.FlagInit=False
            for _ in range(len(self.projectTree.itemList[0])):
                self.projectTree.createProjectItem(FlagNewItem=False)
            """
            item=self.projectTree.topLevelItem(0)
            self.projectTree.setCurrentItem(item)
            item.setSelected(True)
            """
            self.GPApar.copyfrom(data[0])
            self.TREpar.copyfrom(data[1])

            #FlagHidden=not self.isVisible()
            #if FlagHidden:
            #    self.move(0, -1e6) #todo: capire come aggiornare la geometria senza lo show
            #    self.show()
            pri.Time.cyan('Open workspace: set data')
            #self.TREpar.step=None
            #FlagShown=self.falseShow()
            if FlagSetGeometry: self.setGPAlayout()
            self.adjustProjectSelection()
            #if FlagShown: self.hide()
            pri.Time.cyan('Open workspace: selection')
            pri.Time.cyan('Open workspace: geometry (end)')
        except Exception as inst:
            if filename==lastcfgname:
                WarningMessage='Error with loading the last configuration file.\n'
                os.remove(lastcfgname)
            else:
                WarningMessage=f'Error while retrieving the workspace "{data[0].name}" from the file: {filename}\n'
            warningDialog(self,WarningMessage)
            pri.Error.red(f'{WarningMessage}\n{traceback.format_exc()}\n')
            self.new_workspace_debug()
            self.setGPAlayout()
        return waitingWindow.done(0)

    def menu_open_action(self):
        taskDescription='loading a previous workspace'
        if not self.GPApar.FlagSaved:
            if self.questionDialog(f'The current workspace is unsaved. Do you want to save it before {taskDescription}?'):
                self.menu_save_action()
        self.pauseQuestion(taskDescription,self.open_workspace,FlagFirstQuestion=True)

    def save_current_workspace(self,filename,FlagAdjustHeader=True):
        self.updateGPAparGeometry()
        if filename!=lastcfgname: 
            if not self.GPApar.outName:
                self.GPApar.name=os.path.splitext(os.path.basename(filename))[0]
            self.GPApar.outName=filename
        self.GPApar.savedDate=currentTimeString()
        self.GPApar.FlagSaved=True
        Workspace=[self.GPApar.duplicate(),self.TREpar.duplicate(),self.projectTree.itemList]
        try:
            saveList(Workspace,filename)
        except Exception as inst:
            warningDialog(self,f'Error while saving the file {filename}!\nPlease, retry.')
            pri.Error.red(f'Error while saving the file {filename}!\n{inst}')
        else:
            if FlagAdjustHeader: self.adjustWorkspaceHeader()
            FlagSaved=True
        return FlagSaved
    
    def save_last_workspace(self):
        self.save_current_workspace(lastcfgname,FlagAdjustHeader=False)
        pri.Info.white(f'    >>>>> Saving last ui configuration to file:\t{lastcfgname}')

    def saveas_current_workspace(self):
        self.saveas_current_structure(name='workspace',ext=outExt.wksp,saveList=lambda f: self.save_current_workspace(f),par=self.GPApar)
    
    def menu_save_action(self):
        if self.GPApar.outName:
            filename=self.GPApar.outName
            self.pauseQuestion('saving the current workspace',lambda: self.save_current_workspace(filename),FlagFirstQuestion=False)
        else:
            self.menu_saveas_action()
        return False

    def menu_saveas_action(self):
        self.pauseQuestion('saving the current workspace',self.saveas_current_workspace,FlagFirstQuestion=False)
        return False
    
    def close_workspace(self):
        self.GPApar.copyfrom(GPApar(),exceptions=self.GPApar.stateFields)
        self.projectTree.clean_workspace()
    
    def menu_close_action(self):
        taskDescription='closing the current workspace'
        if not self.GPApar.FlagSaved:
            if self.questionDialog(f'The current workspace is unsaved. Do you want to save it before {taskDescription}?'):
                self.menu_save_action()
        self.pauseQuestion(taskDescription,self.close_workspace,FlagFirstQuestion=True)
       
#********************* Help    
    def guide(self):
        #url = QUrl("http://wpage.unina.it/etfd/PaIRS/PaIRS-UniNa-Guide.pdf")
        url = QUrl("https://www.pairs.unina.it/web/PaIRS-UniNa-v020-Guide.pdf")
        QDesktopServices.openUrl(url)

    def downloadApp(self):
        #url = QUrl("http://wpage.unina.it/etfd/PaIRS/PaIRS-UniNa-Guide.pdf")
        url = QUrl(EXEurl)
        QDesktopServices.openUrl(url)

    def about(self):
        if self.aboutDialog:
            self.aboutDialog.hide()
            self.aboutDialog.show()
        else:
            self.aboutDialog=infoPaIRS(self)
            self.aboutDialog.show()

#********************* Debug
    def addDebugMenu(self):
        global Flag_fullDEBUG, pri
        menubar=self.ui.menubar
        self.menuDebug=menubar.addMenu("Debug")

        #--------------------------- new ui cfg
        self.menuDebug.addSeparator()
        self.ui.aNew = self.menuDebug.addAction("New")
        self.ui.aNew.triggered.connect(self.new_workspace_debug)

        #--------------------------- last ui cfg
        self.menuDebug.addSeparator()
        self.ui.aSaveLastCfg = self.menuDebug.addAction("Save lastWorkspace"+outExt.cfg)
        self.ui.aSaveLastCfg.triggered.connect(self.save_last_workspace)

        self.ui.aDeleteLastCfg = self.menuDebug.addAction("Delete lastWorkspace"+outExt.cfg)
        def delete_lastcfg():
            if os.path.exists(lastcfgname):
                os.remove(lastcfgname)
                pri.Info.white(f'    xxxxx Deleting last ui configuration file:\t{lastcfgname}')
            else:
                 pri.Info.white(f'    xxxxx Last ui configuration file:\t{lastcfgname}\t already deleted!')
        self.delete_lastcfg=delete_lastcfg
        self.ui.aDeleteLastCfg.triggered.connect(delete_lastcfg)

        self.ui.aReloadLastCfg = self.menuDebug.addAction("Reload lastWorkspace"+outExt.cfg)
        def reloadLastCfg():
            if os.path.exists(lastcfgname): self.initialize()
            else: self.new_workspace_debug()
        self.ui.aReloadLastCfg.triggered.connect(reloadLastCfg)

        #--------------------------- printings
        self.menuDebug.addSeparator()
        self.ui.printMenu=self.menuDebug.addMenu('Print')
        printTypes_list=list(self.GPApar.printTypes)
        printActions=[]
        printCallbacks=[]
        def setPrint(name,act,k):
            flag=act.isChecked()
            self.GPApar.printTypes[name]=flag
            flagTime=getattr(getattr(pri,name),'flagTime')
            faceStd=getattr(getattr(pri,name),'faceStd')
            if flag:
                setattr(pri,name,ColorPrint(flagTime=flagTime,prio=PrintTAPriority.medium,faceStd=faceStd))
            else:
                setattr(pri,name,ColorPrint(flagTime=flagTime,prio=PrintTAPriority.never,faceStd=faceStd))
            #print(f'{name}  {flag}')
            #pri.Callback.white(f'pri.Callback.white(): setPrint')
            return
        def genCallback(name,act,k):
            n=name
            a=act
            j=k
            def callback():
                setPrint(n,a,j)
                self.menuDebug.popup(self.menuDebug.pos())
                self.ui.printMenu.exec_()
            return callback
        for k,name in enumerate(printTypes_list):
            if not hasattr(pri,name): continue
            flagFullDebug=getattr(getattr(pri,name),'flagFullDebug')
            if flagFullDebug and not Flag_fullDEBUG: continue
            act=self.ui.printMenu.addAction(name)
            printActions.append(act)
            act.setCheckable(True)
            flag=self.GPApar.printTypes[name]
            act.setChecked(flag)
            setPrint(name,act,k)
            printCallbacks.append(genCallback(name,act,k))
            act.triggered.connect(printCallbacks[-1])
        self.ui.printMenu.addSeparator()
        allPrintsAct=self.ui.printMenu.addAction('All printings')
        allPrintsAct.setCheckable(True)
        def setAllPrints():
            flag=allPrintsAct.isChecked()
            for a in printActions:
                a:QAction
                a.setChecked(flag)
                setPrint(a.text(),a,None)   
            self.menuDebug.popup(self.menuDebug.pos())
            self.ui.printMenu.exec_()
            return  
        allPrintsAct.triggered.connect(setAllPrints)
        
        #--------------------------- operation
        if Flag_fullDEBUG:
            self.menuDebug.addSeparator()
            self.ui.simpleFor = self.menuDebug.addAction("Dummy it will be change after")
            def changeFlagSingleFor():
                self.flagSimpleFor=not self.flagSimpleFor
                if self.flagSimpleFor:
                    self.ui.simpleFor.setText("reactivate multi processor")
                else:
                    self.ui.simpleFor.setText("Simple For (no Multi processor usefull to debug c code)")
            self.flagSimpleFor=not self.flagSimpleFor
            changeFlagSingleFor()
            self.ui.simpleFor.triggered.connect(changeFlagSingleFor)

            self.menuDebug.addSeparator()
            self.ui.aShowDownload = self.menuDebug.addAction("Show/hide download button")
            def aShowDownload():
                self.ui.button_PaIRS_download.setVisible(not self.ui.button_PaIRS_download.isVisible())
            self.ui.aShowDownload.triggered.connect(aShowDownload)

            self.ui.aBetaDownload = self.menuDebug.addAction("Change download button icon")
            def aBetaDownload():
                b=self.ui.button_PaIRS_download
                if  b.icon().pixmap(b.size()).toImage()==self.flaticon_PaIRS_download.pixmap(b.size()).toImage():
                    b.setIcon(self.flaticon_PaIRS_beta)
                else:
                    b.setIcon(self.flaticon_PaIRS_download)
            self.ui.aBetaDownload.triggered.connect(aBetaDownload)

            self.ui.aResetFlagOutDated = self.menuDebug.addAction("Reset FlagOutDated")
            def aResetFlagOutDated():
                self.GPApar.FlagOutDated=0 if self.GPApar.currentVersion==self.GPApar.latestVersion else 1 if self.GPApar.FlagOutDated>0 else -1
                packageName='PaIRS-UniNa'
                currentVersion=self.GPApar.currentVersion
                latestVersion=self.GPApar.latestVersion
                if self.GPApar.FlagOutDated==1:
                    sOut=f'{packageName} the current version ({currentVersion}) of {packageName} is obsolete! Please, install the latest version: {latestVersion} by using:\npython -m pip install --upgrade {packageName}'
                elif self.GPApar.FlagOutDated==1:
                    sOut=f'The version of the current instance of {packageName} ({currentVersion}) is newer than the latest official releas ({latestVersion})!\nYou should contact Tommaso and Gerardo if you are a developer and some relevant change is made by yourself!\nIf you are a user, enjoy this beta version and please report any issue!'
                else:
                    sOut=f'{packageName} The current version ({currentVersion}) of {packageName} is up-to-date! Enjoy it!'
                pri.Info.yellow(f'[{self.GPApar.FlagOutDated}] '+sOut) 
            self.ui.aResetFlagOutDated.triggered.connect(aResetFlagOutDated)

            self.ui.aCheckOutDated = self.menuDebug.addAction("Check for new packages")
            def aCheckOutDated():
                self.GPApar.FlagOutDated=0
                self.ui.button_PaIRS_download.hide()
                checkLatestVersion(self,__version__,self.app,splash=None)
            self.ui.aCheckOutDated.triggered.connect(aCheckOutDated)

            self.menuDebug.addSeparator()
            self.ui.aResetWhatsNew = self.menuDebug.addAction("Reset whatsnew.txt")
            def aResetWhatsNew():
                if os.path.exists(fileWhatsNew[1]):
                    try:
                        os.rename(fileWhatsNew[1],fileWhatsNew[0])
                    except Exception as inst:
                        pri.Error.red(f'There was a problem while renaming the file {fileWhatsNew[1]}:\n{inst}')
            self.ui.aResetWhatsNew.triggered.connect(aResetWhatsNew)

            self.ui.aShowWhatsNew = self.menuDebug.addAction("Show What's new window")
            def aShowWhatsNew():
                self.whatsNew()
            self.ui.aShowWhatsNew.triggered.connect(aShowWhatsNew)

            self.menuDebug.addSeparator()
            self.ui.aKill = self.menuDebug.addAction("Stop processes and close")
            def aKill():
                self.FlagClosing[0]=True
                self.signals.killOrResetParForWorker.emit(True)
            self.aKill=aKill
            self.ui.aKill.triggered.connect(aKill)

            self.ui.aFocusWid = self.menuDebug.addAction("Print widget with focus")
            def aFocusWid():
                pri.Info.yellow(f"The widget with focus is:   {self.focusWidget()}")
            self.aCheckConnections=aFocusWid
            self.ui.aFocusWid.triggered.connect(aFocusWid)

            if not Flag_ISEXE:
                self.menuDebug.addSeparator()
                self.ui.aResetRequiredPackagesFile = self.menuDebug.addAction("Reset rqrdpckgs.txt file")
                def aResetRequiredPackagesFile():
                    resetRequiredPackagesFile()
                self.ui.aResetRequiredPackagesFile.triggered.connect(aResetRequiredPackagesFile)
                
                self.ui.aCheckRequiredPackages = self.menuDebug.addAction("Requirements' version check")
                def aCheckRequiredPackages():
                    checkRequiredPackages(self,FlagDisplay=True)
                self.ui.aCheckRequiredPackages.triggered.connect(aCheckRequiredPackages)

                self.ui.aShowPackIssue = self.menuDebug.addAction("Show/hide version check button")
                def aShowPackIssue():
                    self.FlagPackIssue=not self.FlagPackIssue
                    self.ui.button_packissue.setVisible(self.FlagPackIssue)
                self.ui.aShowPackIssue.triggered.connect(aShowPackIssue)

                self.ui.aTryCheckRequiredPackages = self.menuDebug.addAction("Try requirements' version check")
                def aTryCheckRequiredPackages():
                    checkRequiredPackages(self,FlagDisplay=True,FlagForcePrint=True)
                self.ui.aTryCheckRequiredPackages.triggered.connect(aTryCheckRequiredPackages)
        
        #--------------------------- graphics
        if Flag_fullDEBUG:
            self.menuDebug.addSeparator()

            self.ui.aDefSizes = self.menuDebug.addAction("Set default sizes")
            self.ui.aDefSizes.triggered.connect(self.setDefaultSizes)

            self.ui.aUndock = self.menuDebug.addAction("Undock a widget")
            self.ui.aUndock.triggered.connect(self.extractWidget)

            self.ui.aLogo = self.menuDebug.addAction("Change PaIRS logo")
            self.ui.aLogo.triggered.connect(self.happyLogo)

            self.ui.aGifs = self.menuDebug.addAction("Show/hide gifs")
            def showGifs():
                flag=not self.ui.label_updating_import.isVisible()
                self.ui.label_updating_import.setVisible(flag)
                self.ui.label_updating_pairs.setVisible(flag)
            self.ui.aGifs.triggered.connect(showGifs)

        #--------------------------- exit
        self.menuDebug.addSeparator()

        self.ui.aExitDebug = self.menuDebug.addAction("Exit debug mode")
        self.ui.aExitDebug.triggered.connect(lambda:self.setDebugMode(False))

    def extractWidget(self):
        title="Undock a widget"
        label="Enter the widget name:"
        words = ["self.w_Input", 
        "self.w_Input.ui.CollapBox_ImSet",
        "self.w_Output", 
        "self.w_Process", 
        "self.w_Process.ui.CollapBox_IntWind",
        "self.w_Process.ui.CollapBox_FinIt",
        "self.w_Process.ui.CollapBox_top",
        "self.w_Process.ui.CollapBox_Interp",
        "self.w_Process.ui.CollapBox_Validation",
        "self.w_Process.ui.CollapBox_Windowing",
        "self.w_Vis", "self.w_Vis.ui.CollapBox_PlotTools", 
        "self.w_Process", "self.w_Log",
        "self.w_Process_Min","self.w_Process_Disp",
        "self.w_Calibration",
         "self.w_Input_CalVi", "self.w_Process_CalVi", "self.w_Vis_CalVi",
        "self.ui.w_Managing_Tabs",
        ]
        
        ok,text=inputDialog(self,title,label,completer_list=words,width=500)
        if ok:
            try:                    
                ts=text.split('.')
                parent=".".join(ts[:-1])
                child=ts[-1]
                tab=getattr(eval(parent),child)
                self.FloatingWindows.append(FloatingWidget(self,tab))
                pass
            except Exception as inst:
                pri.Error.red(f'Error while undocking the widget <{tab}>\n{inst}')
                pass
    
    def userDebugMode(self):
        if not Flag_DEBUG:
            self.inputDebugMode()
        else:
            self.setDebugMode(False)

    def inputDebugMode(self):
        _,text=inputDialog(self,'Debug','Insert password for debug mode:',width=300,flagScreenCenter=not self.isVisible())
        if text==pwddbg:
            self.setDebugMode(True)
        else:
            warningDialog(self,'Password for debug mode is wrong!\nPaIRS will stay in normal mode.',time_milliseconds=5000)
            self.setDebugMode(False)
    
    def setDebugMode(self,Flag):
        global Flag_DEBUG
        Flag_DEBUG=Flag
        activateFlagDebug(Flag_DEBUG)
        self.setGPaIRSTitle()
        self.menuDebug.menuAction().setVisible(Flag)

    def setButtonDownload(self,):
        self.ui.button_PaIRS_download.setVisible(self.GPApar.FlagOutDated!=0)
        if self.GPApar.FlagOutDated>0:
            self.ui.button_PaIRS_download.setIcon(self.flaticon_PaIRS_download)
            self.ui.button_PaIRS_download.setToolTip("Download the latest version of PaIRS-UniNa.")
        elif self.GPApar.FlagOutDated==-1000:
            self.ui.button_PaIRS_download.setIcon(self.flaticon_PaIRS_download_warning)
            self.ui.button_PaIRS_download.setToolTip("Issue with verifying the latest release!")
        else:
            self.ui.button_PaIRS_download.setIcon(self.flaticon_PaIRS_beta)
            self.ui.button_PaIRS_download.setToolTip("A beta version is currently used!")
        self.ui.button_PaIRS_download.setStatusTip(self.ui.button_PaIRS_download.toolTip())

#*************************************************** Greetings
    def setupLogo(self):
        today = datetime.date.today()
        d=today.strftime("%d/%m/%Y")
        happy_days=[
            #[d, 'Happy birthday to PaIRS! 🎈🎂🍾'], #to test
            ['20/12/1991', 'Happy birthday to Gerardo! 🎈🎂🍾'],
            ['05/02/1969', 'Happy birthday to Tommaso! 🎈🎂🍾'],
            ['11/07/1987', 'Happy birthday to Carlo! 🎈🎂🍾'],
            ['19/09/1963', 'Happy birthday to Gennaro! 🎈🎂🍾'],
            ['27/11/1940', 'Happy birthday to prof. Carlomagno! 🎈🎂🍾'],
            ['18/10/1985', 'Happy birthday to Stefano! 🎈🎂🍾'],
            ['13/08/1985', 'Happy birthday to Andrea! 🎈🎂🍾'],
            ['22/12/1988', 'Happy birthday to Jack! 🎈🎂🍾'],
            ['03/09/1991', 'Happy birthday to Giusy! 🎈🎂🍾'],
            ['03/11/1989', 'Happy birthday to Massimo! 🎈🎂🍾'],
            ['15/06/1991', 'Happy birthday to Mattia! 🎈🎂🍾'],
            ['14/07/1993', 'Happy birthday to Mirko! 🎈🎂🍾'],
            ['01/01', 'Happy New Year! 🎊🧨'],
            ['25/12', 'Merry Christmas! 🎄✨'],
            ['31/10', 'Happy Halloween! 🎃👻'],
            ['22/06', 'Hello, Summer! 🌞🌊'],
        ]

        i=-1
        for j,l in enumerate(happy_days):
            if l[0][:6]==d[:6]:
                i=j
                break

        if i>-1:
            self.FlagHappyLogo=True
            self.ui.logo.setPixmap(QPixmap(u""+ icons_path +"logo_PaIRS_party_rect.png"))
            self.ui.lab_happy_days.show()
            self.ui.lab_happy_days.setText(happy_days[i][1])
        else:
            self.FlagHappyLogo=False
            self.ui.logo.setPixmap(QPixmap(u""+ icons_path +"logo_PaIRS_rect.png"))
            self.ui.lab_happy_days.hide()

    def happyLogo(self):
        self.FlagHappyLogo=not self.FlagHappyLogo
        if self.FlagHappyLogo:
            self.ui.logo.setPixmap(QPixmap(u""+ icons_path +"logo_PaIRS_party_rect.png"))
            self.ui.lab_happy_days.show()
            self.ui.lab_happy_days.setText('Greetings! Today is a great day! 🎈🎉')
        else:
            self.ui.logo.setPixmap(QPixmap(u""+ icons_path +"logo_PaIRS_rect.png"))
            self.ui.lab_happy_days.hide()
    
#*************************************************** Palette
    def setGPaIRSPalette(self):
        setAppGuiPalette(self,self.palettes[self.GPApar.paletteType])

    def paletteContextMenuEvent(self, event):   
        contextMenu = QMenu(self)
        act=[]
        for n in self.paletteNames:
            act.append(contextMenu.addAction(f"{n} mode"))
        act[self.GPApar.paletteType].setCheckable(True)
        act[self.GPApar.paletteType].setChecked(True)
        #userAct = contextMenu.exec(self.mapToGlobal(event.pos()))
        userAct = contextMenu.exec(self.ui.button_colormode.mapToGlobal(self.ui.button_colormode.rect().center()))
        for k,a in enumerate(act):
            if a==userAct:
                self.GPApar.paletteType=k
                self.setGPaIRSPalette()

def launchPaIRS(flagDebug=False,flagInputDebug=False):
    print('\n'+PaIRS_Header+'Starting the interface...')
    app=PaIRSApp.instance()
    if not app:app = QApplication(sys.argv)
    app.setStyle('Fusion')
    font=QFont()
    font.setFamily(fontName)
    font.setPixelSize(fontPixelSize)
    app.setFont(font)
    app.pyicon=app.windowIcon()
    icon=QIcon()
    icon.addFile(''+ icons_path +'icon_PaIRS.png',QSize(), QIcon.Normal, QIcon.Off)
    app.setWindowIcon(icon)
    try:
        if (platform.system() == "Windows"):
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('PaIRS')
    except:
        pri.Info.red('It was not possible to set the application icon')

    if not flagDebug or Flag_SHOWSPLASH:
        splash=showSplash()
        app.processEvents()
    else:
        splash=None
    
    standardPalette=app.style().standardPalette()
    global Flag_fullDEBUG
    Flag_fullDEBUG=flagDebug
    for n in printTypes:
        p:ColorPrint=getattr(pri,n)
        if p.flagFullDebug and not Flag_fullDEBUG:
            p.prio=PrintTAPriority.never
            p.setPrints()
    
    if FlagAddMotherBoard and Flag_fullDEBUG:
        pri.Info.yellow(f"{'-'*50}\nHi, developer!\nMaybe it could be useful for you to add the current computer identifier:\n{currentID}\nto the 'developerIDs' dictionary in PaIRS_pypacks.py!\n{'-'*50}\n")
        
    if flagInputDebug:
        _,text=inputDialog(None,'Debug','Insert password for debug mode:',icon=icon,palette=standardPalette,width=300)
        flagDebug=text==pwddbg
        if not flagDebug:
            warningDialog(None,'Password for debug mode is wrong!\nPaIRS will be started in normal mode.',icon=icon,time_milliseconds=5000)
    gui=gPaIRS(flagDebug,app, standardPalette)

    currentVersion=__version__ #if __subversion__=='0' else  __version__+'.'+__subversion__
    flagStopAndDownload=checkLatestVersion(gui,currentVersion,app,splash)
    if flagStopAndDownload:
        gui.correctClose()
        runPaIRS(gui,flagQuestion=False)
        return [app,gui,False]
    
    gui.splash=splash
    #warningDlg.setModal(True)
    if splash:
        splash.setWindowFlags(splash.windowFlags()|Qt.WindowStaysOnTopHint)
        splash.show()
        app.processEvents()
        
    if splash:
        gui.ui.logo.hide()
    #gui.adjustGeometry()
    gui.show()
    gui.setFontPixelSize()
    if splash: 
        splashAnimation(splash,gui.ui.logo)
        #QTimer.singleShot(time_showSplashOnTop,splash.hide)
    print('\nWelcome to PaIRS!\nEnjoy it!')
    if not getattr(sys, 'frozen', False): #made by pyInstaller
        checkRequiredPackages(gui)
    else:
        gui.FlagPackIssue=False
    gui.ui.button_packissue.setVisible(gui.FlagPackIssue)
    if os.path.exists(fileWhatsNew[0]): gui.whatsNew()
    app.exec()
    return [app,gui,True]

def splashAnimation(self:QLabel,logo:QLabel):
    margin=23
    ml=logo.width()/self.width()*margin
    wl=logo.width()+2*ml
    hl=wl/self.width()*self.height()
    
    self.anim = QPropertyAnimation(self, b"pos")
    pos=logo.mapToGlobal(logo.geometry().topLeft())
    pos.setX(pos.x()-ml)
    self.anim.setEndValue(pos)
    self.anim.setDuration(time_showSplashOnTop)
    self.anim_2 = QPropertyAnimation(self, b"size")
    
    self.anim_2.setEndValue(QSize(wl, hl))
    self.anim_2.setDuration(time_showSplashOnTop)
    self.anim_group = QParallelAnimationGroup()
    self.anim_group.addAnimation(self.anim)
    self.anim_group.addAnimation(self.anim_2)
    self.anim_group.finished.connect(self.hide)
    self.anim_group.finished.connect(logo.show)
    self.anim_group.start()
    
def quitPaIRS(app:QApplication,flagPrint=True):
    app.setWindowIcon(app.pyicon)
    app.quit()
    if flagPrint: print('\nPaIRS closed.\nSee you soon!')
    if hasattr(app,'SecondaryThreads'):
        if len(app.SecondaryThreads):
            while any([s.isRunning for s in app.SecondaryThreads]):
                timesleep(.1)
                pass
    app=None
    return

if __name__ == "__main__":
    app,gui,flagPrint=launchPaIRS(True)
    quitPaIRS(app,flagPrint)

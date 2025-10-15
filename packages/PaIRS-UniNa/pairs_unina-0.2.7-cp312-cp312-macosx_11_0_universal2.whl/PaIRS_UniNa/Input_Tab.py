from .ui_Input_Tab import*
from .Input_Tab_tools import*
from .TabTools import*

spin_tips={
    'inp_cam':      'Current camera number (import tool)',
    'inp_ncam':     'Number of cameras (import tool)',
    'ind_in':       'First image number',
    'npairs':       'Number of image pairs',
    'step':         'Step of image pairs',
    'img':          'Current image pair number',
    'cam':          'Current camera number',
    'ncam':         'Number of cameras',
    'frame':        'Current frame number',
}
check_tips={
    'TR_Import':   'Time-resolved sequence',
}
radio_tips={}
line_edit_tips={
    'path': 'Input folder path',
}
button_tips={
    'data':         'Input data set',
    'path':         'Input folder path',
    'scan_path':    'Re-scan path',
    'automatic_list':   'Automatic list setting',
    'tool_CollapBox_ImSet': 'Open/Close image import tool',
    'CollapBox_ImSet':      'Image import tool',
    'automatic_frame':  'Automatic frame setting',
    'example_list':     'Example list setting',
    'import':           'Image set import',
    'scan_list':        'Re-scan list',
    'warning':          'Warning',
    'cut_warnings':     'Cut items with warning',
    'edit_list':        'Edit list',
    'read_list':        'Read list image file',
    'write_list':       'Write list image file',
    'read':             'Read images from disk',
    'sort':             'Sort images',
    'sort_reversed':    'Reversly sort images',
    'wrap_items':       'Expand items',
    'unwrap_items':     'Collapse items',
    'copy':             'Copy items',
    'cut':              'Cut items',
    'paste_below':      'Paste items below',
    'paste_above':      'Paste items above',
    'clean':            'Clean list',
    'discard_changes':  'Discard changes',
    'confirm_changes':  'Accept changes',
    'up':               'Move to the top of the list',
    'down':             'Move to the bottom of the list',
}
combo_tips={
    'process':         'Type of process',
    'frame_a':      'Pattern of pattern 1',
    'frame_b':      'Pattern of pattern 2',
}

class INPpar(TABpar):
    class ImportPar(TABpar):
        def __init__(self,ncam=1):
            self.setup(ncam)
            self.OptionDone=0
            super().__init__('INPpar','Input')

        def setup(self,ncam=1):
            self.frame_1        = [-1]*ncam
            self.frame_2        = [-1]*ncam
            self.inp_ncam       = ncam
            self.inp_cam        = 1
            self.ind_in         = 0
            self.npairs         = 0 
            self.step           = 0
            self.FlagTR_Import  = False
            self.FlagImport     = True

    FlagAutoList   = True
    FlagAutoFrame  = True
    FlagExample    = True

    def __init__(self,Process=ProcessTypes.null,Step=StepTypes.null):
        self.setup(Process,Step)
        super().__init__('INPpar','Input')
        self.importPar.copyfrom(self,exceptions=['name','surname'])
        self.unchecked_fields+=['FlagCam','OptionValidPath','FlagAutoList','FlagAutoFrame','FlagExample',
                                'inp_cam','nExImTree','exImTreeExp','FlagImport','importPar',
                                'selection','FlagDone','pathCompleter'] #'FlagCollapBox'

    def setup(self,Process,Step):
        self.Process        = Process
        self.Step           = Step
        self.FlagCam        = False
        
        self.path             = './'
        self.OptionValidPath  = 1
        
        self.imSet          = ImageSet()

        #self.FlagCollapBox  = True
        self.frame_1        = [-1]
        self.frame_2        = [-1]
        self.inp_ncam       = 3 if Process==ProcessTypes.tpiv else 2 if Process==ProcessTypes.spiv else 1
        self.inp_cam        = 1
        self.ind_in         = 0
        self.npairs         = 0 
        self.step           = 0
        self.FlagTR_Import  = False
        
        self.nExImTree      = 3
        self.exImTreeExp    = [False]*self.nExImTree
        self.exImList       = [[[],[]]*self.inp_cam]
        self.exImEx         = [[[],[]]*self.inp_cam]

        self.FlagImport     = False
        self.importPar      = self.ImportPar(self.inp_ncam)

        self.ncam           = self.inp_ncam
        self.imList         = [[[],[]] for _ in range(self.ncam)]
        self.imEx           = [[[],[]] for _ in range(self.ncam)]
        self.nimg           = 0
        self.selection      = [0,0,0]

        self.FlagMIN        = Step==StepTypes.min
        self.FlagTR         = False
        self.LaserType      = 0
        self.imListMin      = [[[],[]] for _ in range(self.ncam)]

        self.FlagCAL        = Process in ProcessTypes.threeCameras
        self.calList        = []
        self.calEx          = []

        #self.FlagDISP       = Step==StepTypes.disp
        #self.dispFile       = ''
        
        self.pathCompleter=basefold_DEBUGOptions
        
class Input_Tab(gPaIRS_Tab):
    class Import_Tab_Signals(gPaIRS_Tab.Tab_Signals):
        pass

    def __init__(self,parent: QWidget =None, flagInit= __name__ == "__main__"):
        pri.Time.yellow('Input: init')
        super().__init__(parent,Ui_InputTab,INPpar)
        self.signals=self.Import_Tab_Signals(self)
        pri.Time.yellow('Input: ui')

        #------------------------------------- Graphical interface: widgets
        self.TABname='Input'
        self.ui: Ui_InputTab
        self.exImTree=self.ui.exImTree=GlobalImageTree(self,FlagNum=True)
        self.ui.g_ImSet_layout.insertWidget(2,self.exImTree)    
        self.exImTree.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.exImTree.setSelectionBehavior(QTreeWidget.SelectionBehavior.SelectRows)
        self.exImTree.setHeaderHidden(True)

        #necessary to change the name and the order of the items
        for g in list(globals()):
            if '_items' in g or '_ord' in g or '_tips' in g:
                #pri.Info.blue(f'Adding {g} to {self.name_tab}')
                setattr(self,g,eval(g))

        if __name__ == "__main__": 
            self.app=app
            setAppGuiPalette(self)
        
        #------------------------------------- Graphical interface: miscellanea
        self.pixmap_x     = QPixmap(''+ icons_path +'redx.png')
        self.pixmap_v     = QPixmap(''+ icons_path +'greenv.png')
        self.pixmap_wait  = QPixmap(''+ icons_path +'sandglass.png')
        self.pixmap_warn  = QPixmap(u""+ icons_path +"warning.png")
        
        #------------------------------------- Declaration of parameters 
        self.INPpar_base=INPpar()
        self.INPpar:INPpar=self.TABpar
        self.INPpar_old:INPpar=self.TABpar_old

        pri.Time.yellow('Input: setupWid and par')

        #------------------------------------- Callbacks 
        self.defineWidgets()
        self.setupWid()  #---------------- IMPORTANT
        
        self.defineCallbacks()
        self.connectCallbacks()
        self.defineFurtherCallbacks()

        self.defineSettings()
        self.TABsettings.append(self.image_list_set)
        #self.TABsettings.append(self.button_box_set)

        self.adjustTABpar=self.adjustINPpar
        self.setTABlayout=self.setINPlayout
        self.checkTABpar=lambda ind: self.checkINPpar(ind,FlagRescan=True)
        self.setTABwarn=self.setINPwarn
        self.disableTab=self.disableInputTab
        
        self.ImTreeInd=[]
        self.ui.imTreeWidget.imTree.signals.stopWorker.connect(self.emptyImTreeInd)
        self.ui.imTreeWidget.FlagInGui=True
        
        self.FlagScanPath=False
        pri.Time.yellow('Input: define callbacks')

        #------------------------------------- Initializing 
        if flagInit:
            self.initialize()
        #else:
        #    self.setTABpar(FlagBridge=False)

    def defineFurtherCallbacks(self):
        self.ui.button_data.clicked.connect(lambda: downloadExampleData(self,'https://www.pairs.unina.it/web/PIV_data.zip'))

        #self.button_box_callback=self.wrappedCallback('Open/close Image import tool box',self.button_box_action)
        #self.ui.CollapBox_ImSet.toggle_button.clicked.connect(self.button_box_callback)
        self.ui.spin_inp_cam.valueChanged.connect(self.spin_inp_cam_callback)
        self.ui.spin_inp_cam.addfuncout={}
        itemExpansion_callback=self.wrappedCallback('Item expanded/collapsed',self.itemExpandedCollapsed)
        self.exImTree.itemExpanded.connect(itemExpansion_callback)
        self.exImTree.itemCollapsed.connect(itemExpansion_callback)
        
        self.image_list_callback=self.wrappedCallback('Image list change',self.image_list_action)
        self.ui.imTreeWidget.imTrees[0].signals.updateLists.connect(self.image_list_callback)
        #self.selection_callback=self.wrappedCallback('Image list change',self.selection_action)
        self.selection_callback=self.selection_action
        self.ui.imTreeWidget.spin_img.valueChanged.connect(self.selection_callback)
        self.ui.imTreeWidget.spin_cam.valueChanged.connect(self.selection_callback)
        self.ui.imTreeWidget.spin_frame.valueChanged.connect(self.selection_callback)
        self.ui.imTreeWidget.signals.selection.connect(self.selection_callback)

    def initialize(self):
        pri.Info.yellow(f'{"*"*20}   INPUT initialization   {"*"*20}')
        from .PaIRS_pypacks import basefold
        #self.ui.imTreeWidget.nullList()
        self.INPpar.Process=ProcessTypes.piv
        self.INPpar.path=basefold_DEBUG if __name__ == "__main__" else basefold
        self.INPpar.imSet.path=self.INPpar.path
        #self.cleanPrevs(self.INPpar.ind,FlagAllPrev=True)
        self.ui.line_edit_path.setText(self.INPpar.path)
        self.line_edit_path_callback()
        
#*************************************************** Adjusting parameters
    def adjustINPpar(self):
        self.INPpar.FlagCam=self.INPpar.Process in ProcessTypes.threeCameras
        if not self.INPpar.FlagCam:
            self.INPpar.inp_ncam=self.INPpar.ncam=self.ncamMinimum()
        else: 
            self.INPpar.inp_ncam=self.INPpar.ncam=max([self.INPpar.inp_ncam,self.ncamMinimum()])
        self.INPpar.inp_cam=min([self.INPpar.inp_cam,self.INPpar.inp_ncam])
        if self.INPpar.inp_ncam<self.INPpar_old.inp_ncam:
            del self.INPpar.frame_1[self.INPpar.inp_ncam:]
            del self.INPpar.frame_2[self.INPpar.inp_ncam:]
        elif self.INPpar.inp_ncam>self.INPpar_old.inp_ncam:
            frame_1,frame_2=self.automaticFrames()
            self.INPpar.frame_1[self.INPpar_old.inp_ncam:self.INPpar.inp_ncam]=frame_1[self.INPpar_old.inp_ncam:self.INPpar.inp_ncam]
            self.INPpar.frame_2[self.INPpar_old.inp_ncam:self.INPpar.inp_ncam]=frame_2[self.INPpar_old.inp_ncam:self.INPpar.inp_ncam]
        if len(self.INPpar.frame_1)<self.INPpar.inp_ncam:
            self.INPpar.frame_1+=[self.INPpar.frame_1[0]]*(self.INPpar.inp_ncam-len(self.INPpar.frame_1))
            self.INPpar.frame_2+=[self.INPpar.frame_2[0]]*(self.INPpar.inp_ncam-len(self.INPpar.frame_2))
        #if self.INPpar.isDifferentFrom(self.INPpar_old,fields=['path']): 

        self.INPpar.path=myStandardPath(self.INPpar.path)
        self.INPpar.nimg=0
        if len(self.INPpar.imList[0]):
            if len(self.INPpar.imList[0][0]):
                self.INPpar.nimg=len(self.INPpar.imList[0][0])
        self.checkINPpar(FlagRescan=True)
        if not self.INPpar.OptionValidPath or not self.INPpar.imSet.count: INPpar.FlagExample=False
        self.adjustExampleImageList()
        self.INPpar.FlagImport=self.INPpar.importPar.FlagImport and self.INPpar.importPar.isEqualTo(self.INPpar,exceptions=['name','surname','FlagImport','ind'])
        
        #self.INPpar.importPar.printDifferences(self.INPpar,exceptions=['name','surname','FlagImport','ind'],FlagStrictDiff=True)
        return
    
    def checkINPpar(self,ind=None,FlagRescan=False): #FlagRescan=False):
        if ind is None: INP:INPpar=self.INPpar
        else: INP:INPpar=self.TABpar_at(ind)
        self.setOptionValidPath(ind)
        FlagWarn=INP.OptionValidPath==0
        if not INP.FlagInit or FlagRescan: 
            self.scanImList(ind)
        if not FlagWarn:
            for imExc in INP.imEx:
                for imExf in imExc:
                    for ex in imExf:
                        if not ex:
                            FlagWarn=True
                            break
        INP.OptionDone=1 if (len(INP.imList[0][0])>0 and not FlagWarn) else 0 #-1 if len(INP.imList[0][0])>0 else 0
    
    def scanImList(self,ind=None):
        if ind: INP:INPpar=self.TABpar_at(ind)
        else: INP:INPpar=self.INPpar
        for c in range(len(INP.imList)):  #INP.ncam
            for f in range(2): 
                for k in range(len(INP.imList[0][0])):  #INP.nimg
                    #ex=INP.imEx[c][f][k]
                    INP.imEx[c][f][k]=os.path.exists(INP.path+INP.imList[c][f][k]) if INP.imList[c][f][k] else False

#*************************************************** Layout
    def setINPlayout(self):
        self.ui.label_process.setVisible(__name__ == "__main__")
        self.ui.combo_process.setVisible(__name__ == "__main__")
        self.setPathLabel()
        self.setPathCompleter()

        self.ui.g_ImSet.setEnabled(self.INPpar.OptionValidPath and self.INPpar.imSet.count)
        #if self.INPpar.imSet.isDifferentFrom(self.INPpar_old.imSet,fields=['pattern']):
        self.ui.combo_frame_a.clear()
        self.ui.combo_frame_a.addItems(self.INPpar.imSet.pattern)
        self.ui.combo_frame_b.clear()
        self.ui.combo_frame_b.addItems(['-']+self.INPpar.imSet.pattern)
        
        self.ui.spin_inp_ncam.setEnabled(self.INPpar.FlagCam)
        self.ui.spin_inp_ncam.setMinimum(self.ncamMinimum())
        self.ui.imTreeWidget.spin_ncam.setEnabled(False)
        self.ui.imTreeWidget.FlagCam=self.INPpar.FlagCam
        self.ui.imTreeWidget.spin_ncam.setMinimum(self.ncamMinimum())
        self.ui.imTreeWidget.spin_ncam.setValue(self.INPpar.importPar.inp_ncam)
        self.ui.spin_inp_cam.setEnabled(self.INPpar.inp_ncam>1)
        self.ui.spin_inp_cam.setMaximum(self.INPpar.inp_ncam)
        self.setImageNumberSpinLimits()
        self.exImTree.setVisible(INPpar.FlagExample)
        self.layoutExampleImageList()        
        self.ui.button_import.setEnabled(not self.INPpar.FlagImport)

        """
        if self.INPpar.ind[-1]<len(self.TABpar_prev_at(self.INPpar.ind))-1:
            self.ui.imTreeWidget.w_button.setVisible(False)
        else:
            self.ui.imTreeWidget.w_button.setVisible(True)
        """
        
        self.checkINPpar(FlagRescan=False)
        self.setINPwarn()
        self.setTABWarnLabel()
        return

    def setINPwarn(self,ind=None):
        if ind is None: INP:INPpar=self.INPpar
        else: INP:INPpar=self.TABpar_at(ind)
        if INP.OptionDone==1:
            INP.warningMessage='Input image files correctly identified!'
        else:
            FlagWarn=False
            for imExc in INP.imEx:
                for imExf in imExc:
                    for ex in imExf:
                        if not ex:
                            FlagWarn=True
                            break
            if INP.OptionValidPath==0:
                INP.warningMessage='Invalid input path!'
            elif len(INP.imList[0][0])==0:
                INP.warningMessage='Image set empty!'
            elif FlagWarn:
                INP.warningMessage='Some image files missing!'
            else:
                INP.warningMessage='Issues with identifying input image files!'

    def ncamMinimum(self):
        return 3 if self.INPpar.Process==ProcessTypes.tpiv else 2 if self.INPpar.Process==ProcessTypes.spiv else 1
    
    def disableInputTab(self,flag):
        self.setEnabled(not flag)

#*************************************************** Mode
#******************** Actions
    def combo_process_action(self):
        current_ind=self.ui.combo_process.currentIndex()
        self.INPpar.Process=list(process)[current_ind]
        if self.INPpar.Process in ProcessTypes.threeCameras:
           self.INPpar.ncam=self.INPpar.inp_ncam=max([self.INPpar.ncam,self.ncamMinimum()])
        else:
           self.INPpar.ncam=self.INPpar.inp_ncam=self.ncamMinimum()
           
        if INPpar.FlagAutoList:
            self.button_scan_path_action()
        else:
            self.ui.imTreeWidget.spin_ncam.setMinimum(self.ncamMinimum())
            self.ui.imTreeWidget.spin_ncam.setValue(self.INPpar.ncam)
            self.INPpar.imList=self.ui.imTreeWidget.imTree.imList
            self.INPpar.imEx=self.ui.imTreeWidget.imTree.imEx
            self.ui.imTreeWidget.spin_ncam_action()
        return
    
#******************** Set
    def combo_process_set(self):
        current_proc=process[self.INPpar.Process]
        self.ui.combo_process.setCurrentIndex(process_items.index(current_proc))

#*************************************************** Path
#******************** Actions
    def line_edit_path_changing(self): 
         self.ui.label_check_path.setPixmap(QPixmap()) 

    def line_edit_path_preaction(self):
        currpath=myStandardPath(self.ui.line_edit_path.text())    
        self.FlagScanPath=os.path.normpath(self.INPpar.path)!=currpath
        directory_path = myStandardPath(os.getcwd())
        if directory_path in currpath:
            currpath=currpath.replace(directory_path,'./')        
        if os.path.exists(currpath):
            if currpath in self.INPpar.pathCompleter: self.INPpar.pathCompleter.remove(currpath)
            self.INPpar.pathCompleter.insert(0,currpath)
            if len(self.INPpar.pathCompleter)>10: self.INPpar.pathCompleter=self.INPpar.pathCompleter[:10]
        self.ui.line_edit_path.setText(currpath)

    def line_edit_path_action_future(self):
        if self.FlagScanPath:
            self.button_scan_path_action()

    def button_path_action(self):
        directory = str(QFileDialog.getExistingDirectory(self,\
            "Choose an input folder", dir=self.INPpar.path,options=optionNativeDialog))
        currpath='{}'.format(directory)
        if not currpath=='':
            currpath=myStandardPath(currpath)
            self.ui.line_edit_path.setText(currpath)
            self.INPpar.path=self.ui.line_edit_path.text()
            self.line_edit_path_preaction()
        else:
            currpath='./'
        
    def button_path_action_future(self):
        self.line_edit_path_action_future()

    def button_scan_path_action(self):
        self.INPpar.imSet.scanPath(self.INPpar.path)
        if self.INPpar.imSet.count:
            self.INPpar.frame_1[0]=0
            self.INPpar.frame_1,self.INPpar.frame_2=self.automaticFrames()
        else:
            self.INPpar.frame_1=[-1]*self.INPpar.inp_ncam
            self.INPpar.frame_2=[-1]*self.INPpar.inp_ncam
        self.INPpar.ind_in, _, self.INPpar.npairs, _= self.getIndNpairs()
        self.INPpar.step=1 if self.INPpar.npairs else 0
        if INPpar.FlagAutoList: 
            self.button_import_action()
        else:
            self.ui.imTreeWidget.imTree.path=self.INPpar.path
            self.ui.imTreeWidget.imTree.scanLists()
            self.INPpar.imEx=self.ui.imTreeWidget.imTree.imEx

    def automaticFrames(self):
        cam=self.INPpar.inp_cam-1
        if not self.INPpar.imSet.nimg:
            return self.INPpar.frame_1,self.INPpar.frame_2
        f1=self.INPpar.frame_1[cam]
        link1=self.INPpar.imSet.link[f1]
        nlink1=len(link1)
        frame_1=[f1]*self.INPpar.inp_ncam
        frame_2=[f1+1]*self.INPpar.inp_ncam
        frame_2[0]=link1[0]+1 if link1[0]!=f1 else 0
        for c in range(1,self.INPpar.inp_ncam):
            flagValid=c<nlink1-1
            frame_1[c]=f1c=link1[c] if flagValid else -1
            frame_2[c]=self.INPpar.imSet.link[f1c][0]+1 if flagValid else -1
        if cam:
            frame_1=frame_1[-cam:]+frame_1[:-cam]
            frame_2=frame_2[-cam:]+frame_2[:-cam]
        return frame_1, frame_2
  
    def button_automatic_list_action(self):
        INPpar.FlagAutoList=self.ui.button_automatic_list.isChecked()
        return True

#******************** Settings
    def setOptionValidPath(self,ind=None):
        if ind is None: INP:INPpar=self.INPpar
        else: INP:INPpar=self.TABpar_at(ind)
        INP.OptionValidPath=int(os.path.exists(INP.path))
        return
    
    def setPathCompleter(self):
        self.edit_path_completer=QCompleter(self.INPpar.pathCompleter)
        self.edit_path_completer.setCompletionMode(QCompleter.CompletionMode(1))
        self.edit_path_completer.setModelSorting(QCompleter.ModelSorting(2))
        self.edit_path_completer.setWidget(self.ui.line_edit_path)
        if self.INPpar.path in self.INPpar.pathCompleter:
            k=self.INPpar.pathCompleter.index(self.INPpar.path)
            self.edit_path_completer.setCurrentRow(k) 
        self.ui.line_edit_path.setCompleter(self.edit_path_completer)
        self.ui.line_edit_path.FlagCompleter=True

    def button_automatic_list_set(self):
        self.ui.button_automatic_list.setChecked(INPpar.FlagAutoList)
    
#******************** Layout
    def setPathLabel(self):
        #Clickable label: no need for setStatusTip
        if self.INPpar.OptionValidPath==1:
            self.ui.label_check_path.setPixmap(self.pixmap_v)
            self.ui.label_check_path.setToolTip("The specified path of the input folder exists!")
        elif self.INPpar.OptionValidPath==0:
            self.ui.label_check_path.setPixmap(self.pixmap_x)
            self.ui.label_check_path.setToolTip("The specified path of the input folder does not exist!")
        elif self.INPpar.OptionValidPath==-10:
            self.ui.label_check_path.setPixmap(self.pixmap_wait)
            self.ui.label_check_path.setToolTip("The specified path of the input folder is currently under inspection!")

#*************************************************** Image import tool
#******************** Actions
    """
    def button_box_action(self):
        self.INPpar.FlagCollapBox=self.ui.CollapBox_ImSet.toggle_button.isChecked()
        return True
    """

    def button_automatic_frame_action(self):
        INPpar.FlagAutoFrame=self.ui.button_automatic_frame.isChecked()
        return True
        
    def combo_frame_a_action(self):
        self.INPpar.frame_1[self.INPpar.inp_cam-1]=self.ui.combo_frame_a.currentIndex()
        if INPpar.FlagAutoFrame:
            self.INPpar.frame_1,self.INPpar.frame_2=self.automaticFrames()
            self.INPpar.ind_in, _, self.INPpar.npairs, _= self.getIndNpairs()
            
    def combo_frame_b_action(self):
       self.INPpar.frame_2[self.INPpar.inp_cam-1]=self.ui.combo_frame_b.currentIndex()

    def button_example_list_action(self):
        INPpar.FlagExample=self.ui.button_example_list.isChecked()
        self.exImTree.setVisible(INPpar.FlagExample)
        return True

    def spin_inp_cam_action(self):
        if INPpar.FlagExample:
            items=[self.exImTree.topLevelItem(0)] if not self.exImTree.selectedItems() else self.exImTree.selectedItems()
            self.exImTree.clearSelection()
            for item in items:
                if item.parent(): item=item.parent()
                if self.INPpar.inp_cam-1:
                    if not item.isExpanded():
                        self.INPpar.exImTreeExp[self.exImTree.indexOfTopLevelItem(item)]=True
                    item=item.child(self.INPpar.inp_cam-2)
                item.setSelected(True)
        
    def button_import_action(self):
        INPpar.FlagExample=False
        self.INPpar.imList,self.INPpar.imEx=self.INPpar.imSet.genListsFromFrame(self.INPpar.frame_1,self.INPpar.frame_2,self.INPpar.ind_in,self.INPpar.npairs,self.INPpar.step,self.INPpar.FlagTR_Import)
        self.INPpar.selection=[1,1,1]
        self.InputAdjustSelection()
        if self.INPpar.isDifferentFrom(self.INPpar_old,fields=['imList','imEx']):
            self.INPpar.FlagImport=True
            self.INPpar.importPar.copyfrom(self.INPpar,exceptions=['name','surname'])
        self.ui.CollapBox_ImSet.toggle_button.click()
        self.ui.imTreeWidget.setFocus()
  
#******************** Settings
    """
    def button_box_set(self):
        if self.INPpar.FlagCollapBox: 
            self.ui.CollapBox_ImSet.openBox()
        else: 
            self.ui.CollapBox_ImSet.closeBox()
    """

    def button_automatic_frame_set(self):
        self.ui.button_automatic_frame.setChecked(INPpar.FlagAutoFrame)

    def combo_frame_a_set(self):
        i=self.INPpar.frame_1[self.INPpar.inp_cam-1]
        self.ui.combo_frame_a.setCurrentIndex(i)
    
    def combo_frame_b_set(self):
        i=self.INPpar.frame_2[self.INPpar.inp_cam-1]
        self.ui.combo_frame_b.setCurrentIndex(i)
    
    def button_example_list_set(self):
        self.ui.button_example_list.setChecked(INPpar.FlagExample)

#******************** Layout & Adjustments
    def setImageNumberSpinLimits(self):
        if self.INPpar.isDifferentFrom(self.INPpar_old,fields=['imSet','frame_1','frame_2','inp_ncam','FlagTR_Import']):
            ind_in, ind_fin, npairs, npairs_max= self.getIndNpairs()
            self.INPpar.ind_in=min([max([ind_in,self.INPpar.ind_in]),ind_fin])
            self.INPpar.npairs=npairs if self.INPpar.isDifferentFrom(self.INPpar_old,fields=['FlagTR_Import']) else min([self.INPpar.npairs,npairs])
            self.INPpar.step=min([self.INPpar.step,npairs])

            self.ui.spin_ind_in.setMinimum(ind_in)
            self.ui.spin_ind_in.setMaximum(ind_fin)
            s_ind_in=formatNumber(self.ui.spin_ind_in,ind_in)
            s_ind_fin=formatNumber(self.ui.spin_ind_in,ind_fin)
            self.ui.spin_ind_in.setToolTip(f'Number of the first image in the sequence to process. Min.: {s_ind_in}, max: {s_ind_fin}')
            self.ui.spin_ind_in.setStatusTip(self.ui.spin_ind_in.toolTip())

            self.ui.spin_npairs.setMinimum(0)
            self.ui.spin_npairs.setMaximum(npairs_max)
            self.ui.spin_npairs.setToolTip(f'Number of image pairs to process. Max: {npairs_max}')
            self.ui.spin_npairs.setStatusTip(self.ui.spin_npairs.toolTip())

            self.ui.spin_step.setMinimum(1)
            self.ui.spin_step.setMaximum(npairs_max)
        #ind_in=self.INPpar.imSet.ind_in[self.INPpar.frame_a]
        pass

    def getIndNpairs(self):
        if self.INPpar.imSet.count:
            l=[self.INPpar.imSet.ind_in[f] for f in self.INPpar.frame_1 if f>-1]
            ind_in_1=min(l) if l else None
            l=[self.INPpar.imSet.ind_in[f-1] for f in self.INPpar.frame_2  if f>0]
            ind_in_2=min(l) if l else ind_in_1 if ind_in_1 is not None else None
            ind_in=min([ind_in_1,ind_in_2]) if ind_in_2 is not None else 0

            l=[self.INPpar.imSet.ind_fin[f] for f in self.INPpar.frame_1 if f>-1]
            ind_fin_1=max(l) if l else None
            l=[self.INPpar.imSet.ind_fin[f-1] for f in self.INPpar.frame_2  if f>0]
            ind_fin_2=max(l) if l else ind_fin_1 if ind_fin_1 is not None else None
            ind_fin=min([ind_fin_1,ind_fin_2]) if ind_fin_2 is not None else -1
        else: 
            ind_in=ind_in_2=0
            ind_fin=-1
        npairs=nimg=ind_fin-ind_in+1 
        if not all(self.INPpar.frame_2): 
            npairs=int(npairs/2)
        if self.INPpar.FlagTR_Import: 
            npairs=2*npairs-1+nimg%2   #(1+int(any(self.INPpar.frame_2)))*npairs-1
        if npairs==0: ind_in=ind_fin=0
        npairs_max=npairs
        return ind_in, ind_fin, npairs, npairs_max
        
    def adjustExampleImageList(self):
        exImListPar=['path','frame_1','frame_2','inp_ncam','ind_in','npairs','step','FlagTR_Import']
        if self.INPpar.isDifferentFrom(self.INPpar_old,fields=exImListPar):
            #self.INPpar_old.printDifferences(self.INPpar,fields=exImListPar)
            self.INPpar.exImList,self.INPpar.exImEx=self.INPpar.imSet.genListsFromFrame(self.INPpar.frame_1,self.INPpar.frame_2,self.INPpar.ind_in,min([self.INPpar.npairs,self.INPpar.nExImTree]),self.INPpar.step,self.INPpar.FlagTR_Import)
        
    def layoutExampleImageList(self):
        if self.exImTree.imEx!=self.INPpar.exImEx or self.exImTree.imList!=self.INPpar.exImList:
            self.exImTree.imList=self.INPpar.exImList
            self.exImTree.imEx=self.INPpar.exImEx
            self.exImTree.ncam=self.INPpar.ncam
            self.exImTree.setImListEx()
            self.exImTree.path=self.INPpar.path
            self.exImTree.ncam=self.INPpar.inp_ncam
            self.exImTree.setLists(FlagAsync=False)
            self.exImTree.resizeColumnToContents(2)
            if self.INPpar.inp_ncam==1: self.INPpar.exImTreeExp=[False]*3
        height=self.exImTree.header().height()+5
        #itemHeight=20
        #height=itemHeight+5
        for i in range(3):
            item = self.exImTree.topLevelItem(i)
            if not item: continue
            item.setExpanded(self.INPpar.exImTreeExp[i])
            height+=self.exImTree.visualItemRect(item).height()
            for c in range(item.childCount()):
                height+=self.exImTree.visualItemRect(item.child(c)).height()
            #if self.INPpar.exImTreeExp[i]:
            #    height+=item.childCount()*itemHeight
            #else: height+=itemHeight
        self.exImTree.setMinimumHeight(height)
        self.exImTree.setMaximumHeight(height)
        self.exImTree.verticalScrollBar().setMinimumHeight(height)
        self.exImTree.verticalScrollBar().setMaximumHeight(height)
        self.ui.CollapBox_ImSet.heightArea=height+110 if INPpar.FlagExample else 110
        self.ui.CollapBox_ImSet.heightOpened=self.ui.CollapBox_ImSet.heightArea+20
        self.ui.CollapBox_ImSet.on_click()

    def itemExpandedCollapsed(self):
        for i in range(self.exImTree.topLevelItemCount()):
            item = self.exImTree.topLevelItem(i)
            self.INPpar.exImTreeExp[i]=item.isExpanded()
        self.layoutExampleImageList()
        return True

#*************************************************** Image import tool
#******************** Actions
    def image_list_action(self):
        self.INPpar.imList=self.ui.imTreeWidget.imTree.imList
        self.INPpar.imEx=self.ui.imTreeWidget.imTree.imEx
        FlagDifferent=self.INPpar.isDifferentFrom(self.INPpar_old,fields=['imList'])
        self.INPpar.FlagImport=False
        return not FlagDifferent
        
    def selection_action(self):
        if QApplication.keyboardModifiers(): return
        w=self.ui.imTreeWidget
        if w.imTree.FlagSetting: return
        self.INPpar.selection=[w.spin_img.value(),w.spin_cam.value(),w.spin_frame.value()]
        self.InputAdjustSelection()
        if not TABpar.FlagSettingPar and not self.FlagSettingPar: 
            FlagAdjustPar=True
            self.setTABpar_bridge(FlagAdjustPar,FlagCallback=True)
        return True

    def InputAdjustSelection(self,INP:INPpar=None):
        if INP is None: INP=self.INPpar
        if len(self.TABpar_prev_at(INP.ind)):
            self.TABpar_at(INP.ind).selection=copy.deepcopy(INP.selection)

#******************** Settings
    def image_list_set(self):
        FlagNewLists=self.INPpar.isDifferentFrom(self.ui.imTreeWidget.imTree,fields=['imList','imEx'])
        if FlagNewLists and (not self.ImTreeInd or self.ImTreeInd!=self.INPpar.ind) and (self.ui.imTreeWidget.imTree.itemWorker is None or self.INPpar.ind!=self.INPpar_old.ind):
            self.ImTreeInd=copy.deepcopy(self.INPpar.ind)
            self.ui.imTreeWidget.imTree.signals.updateLists.disconnect()
            self.ui.imTreeWidget.imTree.signals.updateLists.connect(self.restoreSignal)
            self.ui.imTreeWidget.setLists(self.INPpar.path,self.INPpar.imList,self.INPpar.imEx,selection=self.INPpar.selection,FlagOnlyPrepare=not FlagNewLists)
            if not FlagNewLists: self.restoreSignal()
        self.ui.imTreeWidget.imTree.spinSelection(self.INPpar.selection)

    def emptyImTreeInd(self):
        self.ImTreeInd=[]
                    
    @Slot()
    def restoreSignal(self):
        self.ui.imTreeWidget.imTree.signals.updateLists.disconnect()
        self.ui.imTreeWidget.imTree.signals.updateLists.connect(self.image_list_callback)
                                              
if __name__ == "__main__":
    import sys
    app=QApplication.instance()
    if not app:app = QApplication(sys.argv)
    app.setStyle('Fusion')
    object = Input_Tab(None)
    object.show()
    app.exec()
    app.quit()
    app=None
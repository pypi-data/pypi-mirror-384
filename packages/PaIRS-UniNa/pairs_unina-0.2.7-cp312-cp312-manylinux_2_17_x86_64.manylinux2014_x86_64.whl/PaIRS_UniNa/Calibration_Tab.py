from .ui_Calibration_Tab import*
from .TabTools import*
from .listLib import*

spin_tips={
    'ncam'  : 'Number of cameras',
}
check_tips={}
radio_tips={}
line_edit_tips={}
button_tips={
    'CalVi':            'Open/Close CalVi',
    'import':           'Calibration file import',
    'scan_list':        'Re-scan list',
    'copy':             'Copy items',
    'cut':              'Cut items',
    'paste_below':      'Paste items below',
    'paste_above':      'Paste items above',
    'clean':            'Clean list',
}
combo_tips={}

class CALpar(TABpar):
    def __init__(self,Process=ProcessTypes.null,Step=StepTypes.null):
        self.setup(Process,Step)
        super().__init__('CALpar','Calibration')
        self.OptionDone=0
        self.unchecked_fields+=['row','calEx']

    def setup(self,Process,Step):
        self.Process        = Process
        self.Step           = Step

        self.FlagCalVi = False
        self.ncam     = 2 if Process==ProcessTypes.spiv else 1
        self.FlagCam  = False if Process==ProcessTypes.spiv else True
        self.calList  = []
        self.calEx    = []
        self.row      = -1

class Calibration_Tab(gPaIRS_Tab):
    calibrationTreeButtons=['scan_list','-','import','|','copy','cut','paste_below','paste_above','|','clean']
    class Process_Tab_Signals(gPaIRS_Tab.Tab_Signals):
        pass
    
    def __init__(self,parent: QWidget =None, flagInit= __name__ == "__main__"):
        super().__init__(parent,Ui_CalibrationTab,CALpar)
        self.signals=self.Process_Tab_Signals(self)
    
        #------------------------------------- Graphical interface: widgets
        self.TABname='Calibration'
        self.ui: Ui_CalibrationTab

        #necessary to change the name and the order of the items
        for g in list(globals()):
            if '_items' in g or '_ord' in g or '_tips' in g:
                #pri.Info.blue(f'Adding {g} to {self.name_tab}')
                setattr(self,g,eval(g))
        
        if __name__ == "__main__": 
            self.app=app
            setAppGuiPalette(self)

        #------------------------------------- Declaration of parameters 
        self.CALpar_base=CALpar()
        self.CALpar:CALpar=self.TABpar
        self.CALpar_old:CALpar=self.TABpar_old

        #------------------------------------- Callbacks 
        self.defineWidgets()
        self.setupWid()  #---------------- IMPORTANT

        self.defineCallbacks()
        self.connectCallbacks()
        self.ui.calTree.itemSelectionChanged.connect(self.wrappedCallback('List selection',self.calibration_list_selection))
        self.ui.calTree.signals.updateLists.connect(self.wrappedCallback('Re-ordering items',self.copyListsFromTree))

        self.defineSettings()
        
        self.adjustTABpar=self.adjustCALpar
        self.setTABlayout=self.setCALlayout
        self.checkTABpar=self.checkCALpar
        self.setTABwarn=self.setCALwarn

        #------------------------------------- Initializing    
        if flagInit:     
            self.initialize()


    def initialize(self):
        pri.Info.yellow(f'{"*"*20}   PROCESS Disp initialization   {"*"*20}')
        self.setTABpar(FlagAdjustPar=True,FlagBridge=False)
        self.add_TABpar('initialization')
        self.setFocus()

#*************************************************** Adjusting parameters
    def adjustCALpar(self):
        if self.CALpar.Process==ProcessTypes.spiv:
           self.CALpar.ncam=2
           self.CALpar.FlagCam=False
        self.ui.calTree.ncam=self.CALpar.ncam

        self.checkCALpar()
        return
    
    def checkCALpar(self,ind=None,FlagRescan=False):
        if ind is None: CAL:CALpar=self.CALpar
        else: CAL:CALpar=self.TABpar_at(ind)
        if FlagRescan: self.scanCalList(ind)
        CAL.OptionDone = 1 if all(CAL.calEx) and len(CAL.calList)==CAL.ncam else 0

    def scanCalList(self,ind=None):
        if ind is None: CAL:CALpar=self.CALpar
        else: CAL:CALpar=self.TABpar_at(ind)
        for c in range(len(CAL.calList)):  #CAL.ncam
            CAL.calEx[c]=os.path.exists(CAL.calList[c])
              
#*************************************************** Layout
    def setCALlayout(self):
        self.ui.label_ncam.adjustSize()
        self.ui.spin_ncam.setEnabled(self.CALpar.FlagCam)

        self.calibration_list_set()

        FlagFiles=self.ui.calTree.nimg>0
        FlagSelected=len(self.ui.calTree.selectedItems())>0
        FlagNCal=self.ui.calTree.nimg<self.ui.calTree.ncam
        FlagCuttedItems=len(CalibrationTree.cutted_items)>0
        self.ui.button_scan_list.setEnabled(FlagFiles)
        self.ui.button_import.setEnabled(FlagNCal)
        self.ui.button_cut.setEnabled(FlagSelected)
        self.ui.button_copy.setEnabled(FlagSelected)
        self.ui.button_paste_below.setEnabled(FlagNCal and FlagCuttedItems)
        self.ui.button_paste_above.setEnabled(FlagNCal and FlagCuttedItems)
        self.ui.button_clean.setEnabled(FlagFiles)

        self.ui.button_CalVi.setVisible(self.CALpar.flagRun==0)

        self.checkCALpar()
        self.setCALwarn()
        self.setTABWarnLabel()
        return

    def setCALwarn(self,ind=None):
        if ind is None: CAL:CALpar=self.CALpar
        else: CAL:CALpar=self.TABpar_at(ind)
        if CAL.OptionDone==1:
            CAL.warningMessage='Calibration files correctly identified!'
        else:
            warningMessage=''
            nFiles=len(CAL.calList)
            if nFiles<CAL.ncam:
                warningMessage+=f'Number of calibration files ({nFiles}) lower than number of cameras specified ({CAL.ncam})!'
            if not all(CAL.calEx):
                n=sum([1 if not ex else 0 for ex in CAL.calEx])
                if warningMessage: warningMessage='\n*  '
                warningMessage+=f'{n} out of {CAL.ncam} calibration files missing!'
            if '\n*  ' in warningMessage: warningMessage='*  '+warningMessage
            CAL.warningMessage=warningMessage

#*************************************************** Spin ncam
#******************** Actions
    def spin_ncam_action(self):
        self.copyListsFromTree()

#*************************************************** Buttons
#******************** Actions
    def button_CalVi_action(self):
        self.CALpar.FlagCalVi=self.ui.button_CalVi.isChecked()

    def button_scan_list_action(self):
        self.ui.calTree.setLists()
        self.CALpar.calEx=deep_duplicate(self.ui.calTree.calEx)

    def button_import_action(self):
        filenames, _ = QFileDialog.getOpenFileNames(self,\
            "Select calibration files from the current directory", filter='*.cal',\
                options=optionNativeDialog)
        if filenames:
            self.ui.calTree.hide()
            self.ui.calTree.importLists(filenames)
        self.copyListsFromTree()
        self.ui.calTree.show()

    def copyListsFromTree(self):
        if self.ui.calTree.nimg>self.CALpar.ncam:
            warningDialog(self,f'A number of files exceeding the specified number of cameras has been selected!\nOnly the first {self.CALpar.ncam} files will be retained in the list.')
        self.CALpar.calList=deep_duplicate(self.ui.calTree.calList[:self.CALpar.ncam])
        self.CALpar.calEx=deep_duplicate(self.ui.calTree.calEx[:self.CALpar.ncam])
        self.calibration_list_selection()

    def button_copy_cut_action(self, FlagCut=False):
        self.ui.calTree.setVisible(False)
        selectedItems,indexes=self.ui.calTree.selectTopLevel()
        self.copy_cut_action(selectedItems,indexes,FlagCut)

    def cutItems(self,items):
        cutted_items=[None]*len(items)
        for k,item in zip(range(len(items)),items): cutted_items[k]=self.ui.calTree.duplicateItem(item)
        type(self.ui.calTree).cutted_items=cutted_items
        return

    def copy_cut_action(self,items,indexes,FlagCut):        
        self.cutItems(items)

        if FlagCut: 
            for item in items:
                self.ui.calTree.takeTopLevelItem(self.ui.calTree.indexOfTopLevelItem(item))
            self.ui.calTree.cutLists(indexes)
        else: 
            self.ui.calTree.copyLists(indexes)

        self.ui.calTree.setVisible(True)
        self.ui.calTree.setFocus()

        self.copyListsFromTree()
    
    def button_copy_action(self):
        self.button_copy_cut_action(FlagCut=False)

    def button_cut_action(self):
        self.button_copy_cut_action(FlagCut=True)

    def button_paste_above_below_action(self,FlagAbove=True): 
        if not self.ui.calTree.cutted_items: return
        self.ui.calTree.setVisible(False)
        FlagResizeHeader=self.ui.calTree.topLevelItemCount()==0
        selectedItems,indexes=self.ui.calTree.selectTopLevel()
        #self.ui.calTree.clearSelection()
        if FlagAbove:
            if selectedItems: row=indexes[0]
            else: row=0
            firstItemToScroll=self.ui.calTree.cutted_items[0]
            lastItemToScroll=self.ui.calTree.cutted_items[-1]
        else:
            if selectedItems: row=indexes[-1]+1
            else: row=self.ui.calTree.topLevelItemCount()
            firstItemToScroll=self.ui.calTree.cutted_items[-1]
            lastItemToScroll=self.ui.calTree.cutted_items[0]
        self.ui.calTree.insertItems2List(row,self.ui.calTree.cutted_items,True,FlagSignal=False)
        if not self.ui.calTree.FlagCutted:
            self.cutItems(self.ui.calTree.cutted_items)
        self.ui.calTree.pasteLists(row)

        self.ui.calTree.scrollToItem(firstItemToScroll)
        self.ui.calTree.scrollToItem(lastItemToScroll)
        if FlagResizeHeader: self.ui.calTree.resizeColumnToContents(0)
        self.ui.calTree.setVisible(True)
        self.ui.calTree.setFocus()
        
        self.copyListsFromTree()

    def button_paste_above_action(self): 
        self.button_paste_above_below_action(FlagAbove=True)

    def button_paste_below_action(self): 
        self.button_paste_above_below_action(FlagAbove=False)
        
    def button_clean_action(self):
        self.ui.calTree.setVisible(False)
        self.nullList()
        self.ui.calTree.setVisible(True)

    def nullList(self):
        self.ui.calTree.nimg=0
        self.ui.calTree.calList=[]
        self.ui.calTree.calEx=[]
        self.ui.calTree.itemList[0]=self.ui.calTree.calList
        self.ui.calTree.itemList[1]=self.ui.calTree.calEx
        self.ui.calTree.setLists()
        
        self.copyListsFromTree()

#******************** Actions
    def button_CalVi_set(self):
        self.ui.button_CalVi.setChecked(self.CALpar.FlagCalVi)

#*************************************************** Calibration List
#******************** Actions
    def calibration_list_selection(self):
        selectedItems=self.ui.calTree.selectedItems()
        self.CALpar.row=self.ui.calTree.indexOfTopLevelItem(selectedItems[-1]) if len(selectedItems) else -1
        return 
    
#******************** Settings
    def calibration_list_set(self):
        if self.CALpar.isDifferentFrom(self.ui.calTree,fields=['calList','calEx']):
            self.ui.calTree.itemList[0]=self.ui.calTree.calList=deep_duplicate(self.CALpar.calList)
            self.ui.calTree.itemList[1]=self.ui.calTree.calEx=deep_duplicate(self.CALpar.calEx)
            self.ui.calTree.setLists()
            self.CALpar.calEx=deep_duplicate(self.ui.calTree.calEx)

        if self.CALpar.row>-1 and self.CALpar.row<len(self.CALpar.calList):
            self.ui.calTree.topLevelItem(self.CALpar.row).setSelected(True)

#*************************************************** Context Menu
    def contextMenuEvent(self, event):
        menu=QMenu(self)
        name=[]
        act=[]
        fun=[]
        for nb in self.calibrationTreeButtons:
            if '-' not in nb and '|' not in nb:
                b:QPushButton=getattr(self.ui,'button_'+nb)
                if b.isVisible() and b.isEnabled():
                    if hasattr(self,'button_'+nb+'_callback'):
                        name.append(nb)
                        act.append(QAction(b.icon(),toPlainText(b.toolTip().split('.')[0]),self))
                        menu.addAction(act[-1])
                        callback=getattr(self,'button_'+nb+'_callback')
                        fun.append(callback)
            elif '|' in nb:
                if len(act): menu.addSeparator()

        if len(act):
            action = menu.exec(self.mapToGlobal(event.pos()))
            for nb,a,f in zip(name,act,fun):
                if a==action: 
                    TABpar.FlagSettingPar=False
                    f()

if __name__ == "__main__":
    import sys
    app=QApplication.instance()
    if not app:app = QApplication(sys.argv)
    app.setStyle('Fusion')
    object = Calibration_Tab(None)
    object.show()
    app.exec()
    app.quit()
    app=None

import PySide6.QtGui
from .ui_Input_Tab_CalVi import*
from .TabTools import*

#bufferSizeLimit=2000*1e6  #bytes
spin_tips={
    'x'  :  'First column of image area to process',
    'y'  :  'First row of image',
    'w'  :  'Width of image area to process',
    'h'  :  'Height of image area to process',
}
check_tips={}
radio_tips={
    'Cam' : '_cam* in filename',
    'Same_as_input' :  'Output folder path same as input',
}
line_edit_tips={
    'path'     : 'Input folder path',
    'cameras'  : 'Input camera numbers',
    'path_out' : 'Output folder path',
    'root_out' : 'Root of output files',
}
button_tips={
    'data'          :  'Download example data',    
    'path'          :  'Input folder path',
    'import'        :  'Import of target images',
    'import_plane'  :  'Import of plane parameters',
    'down'          :  'Order of target images',
    'up'            :  'Order of target images',
    'delete'        :  'Deletion of target images',
    'clean'         :  'Cleaning of the image list',
    'resize'        :  'Reset of image sizes',
    'path_out'      :  'Output folder path',
}
combo_tips={}
class INPpar_CalVi(TABpar):
    def __init__(self,Process=ProcessTypes.null,Step=StepTypes.null):
        self.setup(Process,Step)
        super().__init__('INPpar_CalVi','Input_CalVi')
        self.unchecked_fields+=['OptionValidPath','OptionValidPathOut','OptionValidRootOut','row','col','rows','cols','pathCompleter']

    def setup(self,Process,Step):
        self.Process        = Process
        self.Step           = Step

        self.path          = './'
        self.OptionValidPath = 1
        
        self.ext        = ''
        self.FlagCam    = False
        self.cams       = []
        self.filenames  = []
        self.FlagImages = []
        self.plapar     = []

        self.imageFile  = None
        self.x          = 0
        self.y          = 0
        self.w          = 1
        self.h          = 1
        self.W          = 1
        self.H          = 1
        
        self.row        = -1
        self.col        = -1
        self.rows       = []
        self.cols       = []
        self.imList     = [[]]
        self.imEx       = [[]]

        self.FlagOptPlane  = False
        self.CalibProcType = 1

        self.FlagSame_as_input   = True
        self.path_out            = './'
        self.OptionValidPathOut  = 1
        self.root_out            = 'pyCal'
        self.OptionValidRootOut  = 1

        self.errorMessage       = ''
        self.FlagReadCalib      = False

        self.pathCompleter=basefold_DEBUGOptions
        
class Input_Tab_CalVi(gPaIRS_Tab):

    class Import_Tab_Signals(gPaIRS_Tab.Tab_Signals):
        list_selection=Signal()
        pass

    def __init__(self,parent: QWidget =None, flagInit= __name__ == "__main__"):
        super().__init__(parent,Ui_InputTab_CalVi,INPpar_CalVi)
        self.signals=self.Import_Tab_Signals(self)

        #------------------------------------- Graphical interface: widget
        self.TABname='Input_CalVi'
        self.ui: Ui_InputTab_CalVi
        self.ui.spin_x.addwid=[self.ui.spin_w]
        self.ui.spin_y.addwid=[self.ui.spin_h]

        #necessary to change the name and the order of the items
        for g in list(globals()):
            if '_items' in g or '_ord' in g or '_tips' in g:
                #pri.Info.blue(f'Adding {g} to {self.name_tab}')
                setattr(self,g,eval(g))

        if __name__ == "__main__": 
            self.app=app
            setAppGuiPalette(self)
        
        #------------------------------------- Graphical interface: miscellanea
        self.pixmap_x       = QPixmap(''+ icons_path +'redx.png')
        self.pixmap_v       = QPixmap(''+ icons_path +'greenv.png')
        self.pixmap_wait    = QPixmap(''+ icons_path +'sandglass.png')
        self.pixmap_warn    = QPixmap(u""+ icons_path +"warning.png")

        self.edit_path_label=QPixmap()
        self.edit_cams_label=QPixmap()

        self.tableHeaders = [self.ui.list_images.horizontalHeaderItem(i).text() for i in range(self.ui.list_images.columnCount())]
        header = self.ui.list_images.horizontalHeader()     
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        #header.setMinimumSectionSize(int(self.minimumWidth()/2))
        #header.setMaximumSectionSize(int(self.maximumWidth()/2))
        self.ui.list_images.InfoLabel=self.ui.label_info
        self.ui.list_images.DeleteButton=self.ui.button_delete
        #self.ui.list_images.addfuncreturn['plapar']=self.updatePlanePar
        #self.ui.list_images.addfuncout['plapar']=self.updatePlanePar
        self.ui.label_info.hide()
        self.ui.list_images.setupRowBehaviour()

        #------------------------------------- Declaration of parameters 
        self.INPpar_base=INPpar_CalVi()
        self.INPpar:INPpar_CalVi=self.TABpar
        self.INPpar_old:INPpar_CalVi=self.TABpar_old

        self.bufferImg  = {}
        self.bufferSize = 0

        #------------------------------------- Callbacks 
        self.defineWidgets()
        self.setupWid()  #---------------- IMPORTANT

        self.defineCallbacks()
        self.connectCallbacks()
        self.defineFurtherCallbacks()

        self.defineSettings()

        self.adjustTABpar=self.adjustINPpar
        self.setTABlayout=self.setINPlayout

        self.setRunCalViButtonText=lambda: None

        #------------------------------------- Initializing 
        if flagInit:
            self.initialize()

    def initialize(self):
        pri.Info.yellow(f'{"*"*20}   INPUT CalVi initialization   {"*"*20}')
        self.INPpar.path=basefold_DEBUG if __name__ == "__main__" else basefold
        #self.cleanPrevs(self.INPpar.ind,FlagAllPrev=True)
        self.ui.line_edit_path.setText(self.INPpar.path)
        self.line_edit_path_callback()
        return

    def defineFurtherCallbacks(self):
        #Callbacks
        self.ui.button_data.clicked.connect(lambda: downloadExampleData(self,'https://www.pairs.unina.it/web/Calibration_data.zip'))

        self.ui.list_images.contextMenuEvent=lambda e: self.listContextMenuEvent(self.ui.list_images,e)
        #self.ui.list_images.itemSelectionChanged.connect(self.wrappedCallback('Item selection',self.list_selection))
        self.ui.list_images.currentItemChanged.connect(self.wrappedCallback('Item selection',self.list_selection))
        self.ui.list_images.cellChanged.connect(self.wrappedCallback('Plane parameters',self.updatePlanePar))
        self.ui.list_images.signals.updateLists.connect(self.fullCallback)

    def listContextMenuEvent(self, list_images:QTableWidget, event):
        menu=QMenu(list_images)
        buttons=['import', 'import_plane',
                 -1,'down','up',
                 -1,'delete','clean']
        name=[]
        act=[]
        fun=[]
        for _,nb in enumerate(buttons):
            if type(nb)==str:
                b:QPushButton=getattr(self.ui,'button_'+nb)
                if b.isVisible() and b.isEnabled():
                    if hasattr(self,'button_'+nb+'_callback'):
                        name.append(nb)
                        act.append(QAction(b.icon(),toPlainText(b.toolTip().split('.')[0]),list_images))
                        menu.addAction(act[-1])
                        callback=getattr(self,'button_'+nb+'_callback')
                        fun.append(callback)
            else:
                if len(act): menu.addSeparator()

        if len(act):
            pri.Callback.yellow(f'||| Opening image list context menu |||')
            action = menu.exec(list_images.mapToGlobal(event.pos()))
            for nb,a,f in zip(name,act,fun):
                if a==action: 
                    TABpar.FlagSettingPar=False
                    f()
                    break

#*************************************************** Adjusting parameters
    def adjustINPpar(self):
        self.INPpar.path=myStandardPath(self.INPpar.path)
        self.setOptionValidPath()

        self.INPpar.FlagOptPlane=self.INPpar.CalibProcType>0
        self.check_cams()

        if self.INPpar.isDifferentFrom(self.INPpar_old,fields=['FlagCam']):
            self.adjustCam()
        if self.INPpar.isDifferentFrom(self.INPpar_old,fields=['path','FlagCam','cams','filenames']):
            self.adjust_list_images()
        if self.INPpar.isDifferentFrom(self.INPpar_old,fields=['imageFile']):
            self.adjust_image_sizes()
        if len(self.INPpar_old.filenames)==0 and len(self.INPpar.filenames)>0:
            self.button_resize_action()
        l=len(self.INPpar.filenames)
        if l>0: 
            self.INPpar.row=min([max([self.INPpar.row,0]),l-1])
            self.INPpar.col=max([self.INPpar.col,0])

        if self.INPpar.FlagSame_as_input: self.INPpar.path_out=self.INPpar.path
        #if self.INPpar.isDifferentFrom(self.INPpar_old,fields=['path_out','FlagSame_as_input']):
        self.INPpar.path_out=myStandardPath(self.INPpar.path_out)
        self.setOptionValidPathOut()
        #if self.INPpar.isDifferentFrom(self.INPpar_old,fields=['root_out']):
        self.INPpar.root_out=myStandardRoot(self.INPpar.root_out)
        self.setOptionValidRootOut()
        
        if not self.INPpar.FlagInit: 
            self.adjust_list_images()
        return

    def check_cams(self):
        if len(self.INPpar.cams)>1 and self.INPpar.CalibProcType==0:
            warningDialog(self,'Standard calibration can be performed only one camera at once! The first camera identification number will be retained for the current configuration.')
            self.INPpar.cams=[self.INPpar.cams[0]]
    
#*************************************************** Layout
    def setINPlayout(self):
        self.setPathLabel()
        self.setPathCompleter()

        self.ui.w_InputImg.setVisible(self.INPpar.FlagCam)

        flagSelect=self.INPpar.row>-1
        self.ui.button_down.setEnabled(flagSelect)
        self.ui.button_up.setEnabled(flagSelect)
        self.ui.button_delete.setEnabled(flagSelect)
        FlagImages=len(self.INPpar.filenames)>0
        self.ui.button_import_plane.setEnabled(FlagImages)
        self.ui.button_clean.setEnabled(FlagImages)
        
        if self.INPpar.isDifferentFrom(self.INPpar_old,fields=['filenames','imList','imEx','plapar','FlagImages']) or not self.INPpar.FlagInit:
            self.set_list_images_items()
        item=self.ui.list_images.item(self.INPpar.row,self.INPpar.col)
        if item: self.ui.list_images.setCurrentItem(item)
        for r,c in zip(self.INPpar.rows,self.INPpar.cols):
            item=self.ui.list_images.item(r,c)
            if item: item.setSelected(True)
        
        self.errorMessage()
        self.ui.list_images.resizeInfoLabel()

        self.ui.w_SizeImg.setVisible(FlagImages)
        self.setMinMaxSpinxywh()

        self.setPathOutLabel()
        self.setRootOutLabel()
        self.ui.w_OutputFolder.setEnabled(not self.INPpar.FlagSame_as_input)
        self.ui.w_button_path_out.setEnabled(not self.INPpar.FlagSame_as_input)
        
        self.setRunCalViButtonText()
        self.ui.list_images.itemList=[self.INPpar.filenames,self.INPpar.imList,self.INPpar.imEx,self.INPpar.plapar,self.INPpar.FlagImages]


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
    
    def button_path_action(self):
        directory = str(QFileDialog.getExistingDirectory(self,\
            "Choose an input folder", dir=self.INPpar.path,options=optionNativeDialog))
        currpath='{}'.format(directory)
        if not currpath=='':
            currpath=myStandardPath(currpath)
            self.ui.line_edit_path.setText(currpath)
            self.INPpar.path=self.ui.line_edit_path.text()
            self.line_edit_path_preaction()

    def line_edit_cameras_action(self):
        text=self.ui.line_edit_cameras.text()
        split_text=re.findall(r'(\d+)', text)
        self.INPpar.cams=[]
        for s in split_text:
            i=int(s)
            if i not in self.INPpar.cams: 
                self.INPpar.cams.append(i)
        return
    
#******************** Settings
    def setOptionValidPath(self):
        self.INPpar.OptionValidPath=int(os.path.exists(self.INPpar.path))
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

    def line_edit_cameras_set(self):
        text=", ".join([str(c) for c in self.INPpar.cams])
        self.ui.line_edit_cameras.setText(text)

#******************** Layout
    def setPathLabel(self):
        #Clickable label: no need for setStatusTip
        if self.INPpar.OptionValidPath:
            self.ui.label_check_path.setPixmap(self.pixmap_v)
            self.ui.label_check_path.setToolTip("The specified path of the input folder exists!")
        else:
            self.ui.label_check_path.setPixmap(self.pixmap_x)
            self.ui.label_check_path.setToolTip("The specified path of the input folder does not exist!")
        self.edit_path_label=self.ui.label_check_path.pixmap()

#*************************************************** Images
#******************** Actions    
    def button_import_action(self):
        filenames, _ = QFileDialog.getOpenFileNames(self,\
            "Select an image file of the sequence", filter=text_filter, dir=self.INPpar.path,\
                options=optionNativeDialog)
        if len(filenames)==0: return
        currpath=self.INPpar.path
        f_new=[]
        f_warning=[]
        for filename in filenames:
            if not filename: continue
            f=os.path.basename(filename)
            FlagWarn=False
            if self.INPpar.FlagCam: 
                fsplitted=re.split(r'_cam\d+', f)
                if len(fsplitted)>1:
                    fsplitted.insert(-1,'_cam*')
                    f="".join(fsplitted)
                else:
                    f_warning.append(f) #redundant
                    FlagWarn=True
            if f not in self.INPpar.filenames and f not in f_new and not FlagWarn:
                f_new.append(f)
        if len(f_new)>0:
            for t in f_new:
                self.INPpar.filenames.append(t)
                if self.INPpar.FlagOptPlane:
                    self.INPpar.plapar.append([float(0)]*6)
                else:
                    self.INPpar.plapar.append([float(0)])
            self.INPpar.path, _ = os.path.split(filenames[0])
        if len(f_warning):
            list_img_warn=';\n'.join(f_warning)
            Message=f'The following files located in the path {currpath} do not contain the pattern _cam* in their name and will not be included in the list of image files for the calibration process:\n{list_img_warn}.'
            warningDialog(self,Message)
        return
    
    def button_import_plane_action(self):
        if len(self.INPpar.rows)>1:
            self.INPpar.rows=[self.INPpar.row]
            self.INPpar.cols=[1]
            self.INPpar.col=1
            self.ui.list_images.clearSelection()
            item=self.ui.list_images.item(self.INPpar.row,self.INPpar.col)
            item.setSelected(True)
        plaparName, _ = QFileDialog.getOpenFileName(self,\
            "Select a plane parameter file", filter=f'*{outExt.pla}',\
                dir=self.INPpar.path,\
                options=optionNativeDialog)
        if not plaparName: return
        try:
            if os.path.exists(plaparName):
                with open(plaparName, 'r') as file:
                    data=file.read()
                    dp=eval(data)
                    pass
        except:
            WarningMessage=f'Error with loading the file: {plaparName}\n'
            warningDialog(self,WarningMessage)
        else:
            try:
                if len(self.INPpar.plapar[self.INPpar.row])==1:
                    self.INPpar.plapar[self.INPpar.row]=[round(dp['z (mm)'],3)]
                else:
                    self.INPpar.plapar[self.INPpar.row]=[round(p,3) for p in list(dp.values())]
            except:
                WarningMessage=f'Error with setting the plane parameters read from file: {plaparName}\n'
                warningDialog(self,WarningMessage)

    def button_delete_action(self):
        source_rows=[]
        [source_rows.append(i.row()) for i in self.ui.list_images.selectedItems() if i.row() not in source_rows and i.row()>-1]
        source_rows.sort(reverse=True)
        for k in source_rows:
            self.INPpar.filenames.pop(k)
            self.INPpar.plapar.pop(k)
        self.INPpar.rows=[]
        self.INPpar.cols=[]
        self.INPpar.row=-1
        self.INPpar.col=-1

    def button_clean_action(self):
        self.INPpar.filenames=[]
        self.INPpar.plapar=[]
        self.INPpar.x = self.INPpar.y = 0
        self.INPpar.w = self.INPpar.h = 1
        self.INPpar.W = self.INPpar.H = 1
        self.INPpar.row = -1
        self.INPpar.col = -1 
        return
        
    def button_updown_action(self,d):
        source_rows=[]
        [source_rows.append(i.row()) for i in self.ui.list_images.selectedItems() if i.row() not in source_rows and i.row()>-1]
        source_rows.sort(reverse=d>0)
        
        for row in source_rows:
            if d==-1 and row==0: return
            if d==+1 and row==len(self.INPpar.filenames)-1: return
            filename=self.INPpar.filenames.pop(row)
            self.INPpar.filenames.insert(row+d,filename)
            par=self.INPpar.plapar.pop(row)
            self.INPpar.plapar.insert(row+d,par)
        source_rows.sort(reverse=d>0)
        self.INPpar.rows=[]
        self.INPpar.cols=[]
        for row in source_rows:
            for col in range(self.ui.list_images.columnCount()):
                self.INPpar.rows.append(row+d)
                self.INPpar.cols.append(col)
        self.INPpar.row+=d
        self.ui.list_images.setFocus()
        return 
    
    def button_down_action(self):
        self.button_updown_action(+1)

    def button_up_action(self):
        self.button_updown_action(-1)

    def list_selection(self):
        selectedItems=self.ui.list_images.selectedItems()
        if selectedItems:
            self.INPpar.rows=[i.row() for i in selectedItems]
            self.INPpar.cols=[i.column() for i in selectedItems]
            self.INPpar.row=self.INPpar.rows[-1]
            self.INPpar.col=self.INPpar.cols[-1]
        else:
            self.INPpar.rows=[-1]
            self.INPpar.cols=[-1]
            self.INPpar.row=-1
            self.INPpar.col=-1
        return
    
    def updatePlanePar(self):
        if self.ui.list_images.currentColumn()==1:
            r=self.ui.list_images.currentRow()
            item=self.ui.list_images.item(r,1)
            text=item.text()
            oldtext=", ".join([str(s) for s in self.INPpar.plapar[r]])
            if text!=oldtext:
                #fex=re.compile('[+-]?([0-9]+([.][0-9]*)?|[.][0-9]+)')
                if self.INPpar.FlagOptPlane:
                    tsplitted=re.split(',',text)
                    #pri.Callback.white(tsplitted)
                    if len(tsplitted)==6 and all([isfloat(p) for p in tsplitted]):
                        self.INPpar.plapar[r]=[float(p) for p in tsplitted]
                else:
                    if isfloat(text):
                        self.INPpar.plapar[r]=[float(text)]
                pri.Callback.green(f'***** new par {", ".join([str(s) for s in self.INPpar.plapar[r]])}')

 #******************** Adjusting   
    def adjustCam(self):
        if self.INPpar.FlagCam and len(self.INPpar.cams)==0:
            ncam=0
            for f in self.INPpar.filenames:
                pats=re.findall(r'_cam\d+', f)
                if len(pats):
                    ncam=int(pats[-1].replace("_cam",""))
                    break
            self.INPpar.cams=[ncam]
        elif not self.INPpar.FlagCam and len(self.INPpar.cams)>0:
            scam=str(self.INPpar.cams[0])
            self.INPpar.filenames=[f.replace('*',scam) for f in self.INPpar.filenames]
            self.INPpar.cams=[]
    
    def adjust_list_images(self):
        #deleting filenames not compatible with the option _cam* in the filename
        ind_del=[]
        for k,f in enumerate(self.INPpar.filenames):
            if (not '_cam' in f and self.INPpar.FlagCam) or\
                ('_cam*' in f and not self.INPpar.FlagCam):
                ind_del.append(k)
        for kk in range(len(ind_del)-1,-1,-1):
            k=ind_del[kk]
            self.INPpar.filenames.pop(k)
            self.INPpar.plapar.pop(k)
        
        #check that the filename contains * and not an identifier number
        if self.INPpar.FlagCam:
            for k,f in enumerate(self.INPpar.filenames):
                if '_cam*' in f: continue
                fsplitted=re.split(r'_cam\d+', f)
                fsplitted.insert(-1,'_cam*')
                f="".join(fsplitted)
                self.INPpar.filenames[k]=f
        f_unique=[]
        plapar_unique=[]
        for f,p in zip(self.INPpar.filenames,self.INPpar.plapar):
            if not f in f_unique: 
                f_unique.append(f)
                plapar_unique.append(p)
        self.INPpar.filenames=f_unique
        self.INPpar.plapar=plapar_unique

        self.INPpar.row=min([len(self.INPpar.filenames),self.INPpar.row])
        if self.INPpar.FlagCam:
            self.INPpar.imList=[[] for _ in range(len(self.INPpar.cams))]
            self.INPpar.imEx=[[] for _ in range(len(self.INPpar.cams))]
            for k,c in enumerate(self.INPpar.cams):
                self.INPpar.imList[k]=[self.INPpar.path+f.replace("*",str(c)) for f in self.INPpar.filenames]
                self.INPpar.imEx[k]=[os.path.exists(fk) for fk in self.INPpar.imList[k]]
        else:
            self.INPpar.imList=[[self.INPpar.path+f for f in self.INPpar.filenames]]
            self.INPpar.imEx=[[os.path.exists(fk) for fk in self.INPpar.imList[0]]]
            

        self.INPpar.imageFile=''
        if len(self.INPpar.imList):
            if len(self.INPpar.imList[0]):
                self.INPpar.imageFile=self.INPpar.imList[0][0]
        return

    def adjust_image_sizes(self):
        if not self.INPpar.imageFile or not os.path.exists(self.INPpar.imageFile): return
        try:
            im = Image.open(self.INPpar.imageFile)
            self.INPpar.ext=os.path.splitext(self.INPpar.imageFile)[-1]
            pri.Info.blue(f'File extension: {self.INPpar.ext}')
        except:
            pri.Error.blue(f'Error opening image file: {self.INPpar.imageFile}.\n{traceback.format_exc()}\n')
        else:
            self.INPpar.W,self.INPpar.H=im.size
            if self.INPpar.w<1 or self.INPpar.w>self.INPpar.W:
                self.INPpar.w=self.INPpar.W
            if self.INPpar.h<1 or self.INPpar.H>self.INPpar.H:
                self.INPpar.h=self.INPpar.H
            if self.INPpar.x<0: self.INPpar.x=0
            elif self.INPpar.x>self.INPpar.W-self.INPpar.w: self.INPpar.x=self.INPpar.W-self.INPpar.w
            if self.INPpar.y<0: self.INPpar.y=0
            elif self.INPpar.y>self.INPpar.H-self.INPpar.h: self.INPpar.y=self.INPpar.H-self.INPpar.h
        return        
      
 #******************** Layout 
    def set_list_images_items(self):
        self.ui.list_images.setRowCount(0)
        self.INPpar.FlagImages=[0]*len(self.INPpar.filenames)
        for k,f in enumerate(self.INPpar.filenames):
            c=self.ui.list_images.rowCount()
            self.ui.list_images.insertRow(c)
            list_eim_camk=[ex[k] for ex in self.INPpar.imEx]

            item_filename=QTableWidgetItem(f)
            item_filename.setFlags(item_filename.flags() & ~Qt.ItemIsEditable)
            item_filename.setToolTip(f)
            item_filename.setStatusTip(f)
            self.ui.list_images.setItem(c, 0, item_filename)
            if self.INPpar.FlagOptPlane:
                tiptext='Plane parameters: \u03B2 (°), \u03B1 (°), \u03B3 (°), x (mm), y (mm), z (mm)'
            else:
                tiptext='Plane parameters: z (mm)'
            tooltip=QLabel()
            tooltip.setTextFormat(Qt.TextFormat.RichText)
            tooltip.setText(tiptext)

            item_parameters=QTableWidgetItem(", ".join([str(s) for s in self.INPpar.plapar[k]]))
            item_parameters.setToolTip(tooltip.text())
            item_parameters.setStatusTip(tooltip.text())
            self.ui.list_images.setItem(c, 1, item_parameters)

            message='' 
            tiptext=[]
            if len(self.INPpar.plapar[k])==0:
                message+="⚠"
                tiptext+=[f"⚠︎: Corresponding plane parameters are not defined!"]
                self.INPpar.FlagImages[k]|=1
            for q in range(k):
                if self.INPpar.plapar[k]==self.INPpar.plapar[q]:
                    message+="⚠"
                    tiptext+=[f"⚠︎: Plane parameters are coincident with those of plane {'#'} ({q})!"]
                    self.INPpar.FlagImages[k]|=2
                    break
            if not all(list_eim_camk):
                message+="❌"
                if len(self.INPpar.cams):
                    cams=",".join([str(self.INPpar.cams[kk]) for kk,e in enumerate(list_eim_camk) if not e])
                    tiptext+=[f"❌: Image files for cameras {'#'} ({cams}) are missing!"]
                else:
                    tiptext+=[f"❌: Image files is missing!"]
                self.INPpar.FlagImages[k]|=4
            if tiptext:
                tiptext=f"<br>".join(tiptext)
            else:
                message="✅"
                tiptext='✅: Check if the values of the plane parameters are correct!'
            tooltip=QLabel()
            tooltip.setTextFormat(Qt.TextFormat.RichText)
            tooltip.setText(tiptext)

            item_message=QTableWidgetItem(message)
            item_message.setFlags(item_message.flags() & ~Qt.ItemIsEditable)
            item_message.setToolTip(tooltip.text())
            item_message.setStatusTip(tooltip.text())
            self.ui.list_images.setItem(c, 2, item_message)
        return

    def listClear(self):
        self.ui.list_images.clear()
        nRow=self.ui.list_images.rowCount()
        for k in range(nRow):
            self.ui.list_images.removeRow(self.ui.list_images.rowAt(k))
        self.ui.list_images.setHorizontalHeaderLabels(self.tableHeaders)

    def errorMessage(self):
        self.INPpar.errorMessage=''
        if not len(self.INPpar.FlagImages):
            self.INPpar.errorMessage+='Select a valid set of target image files!\n\n'
        if not self.INPpar.OptionValidPathOut:
            self.INPpar.errorMessage+='Choose a valid path for the output folder!\n\n'
        if not self.INPpar.OptionValidRootOut:
            self.INPpar.errorMessage+='Specify a valid root for the name of the output files!\n\n'
        if any(self.INPpar.FlagImages):
            errorFiles=[[],[]]
            for k,f in enumerate(self.INPpar.FlagImages):
                if f&3: errorFiles[0].append(self.INPpar.filenames[k])
                elif f&4: errorFiles[1].append(self.INPpar.filenames[k])
            if len(errorFiles[0]) or len(errorFiles[1]):
                errorMessage=''
                if len(errorFiles[0]):
                    errList=f";\n   ".join(errorFiles[0])
                    errorMessage+=f'Define appropriately the plane parameters for the following images:\n   {errList}.\n\n'         
                if len(errorFiles[1]):
                    errList=f";\n   ".join(errorFiles[1])
                    errorMessage+=f'Check for missing files related to the following images:\n   {errList}.'         
                #pri.Error.blue(errorMessage)
            self.INPpar.errorMessage+=errorMessage
        if self.INPpar.errorMessage:
            self.INPpar.errorMessage='Please check the following issues before starting calibration!\n\n'+self.INPpar.errorMessage
    
#*************************************************** Output path
#******************** Actions
    def radio_Same_as_input_action(self):
        self.INPpar.path_out=self.INPpar.path         
    
    def line_edit_path_out_changing(self): 
         self.ui.label_check_path_out.setPixmap(QPixmap()) 
        
    def line_edit_path_out_preaction(self):
        currpath=myStandardPath(self.ui.line_edit_path_out.text())     
        directory_path = myStandardPath(os.getcwd())
        if directory_path in currpath:
            currpath=currpath.replace(directory_path,'./')         
        self.ui.line_edit_path_out.setText(currpath)      

    def button_path_out_action(self):
        directory = str(QFileDialog.getExistingDirectory(self,\
            "Choose a folder", dir=self.INPpar.path_out,options=optionNativeDialog))
        currpath='{}'.format(directory)
        if not currpath=='':
            self.ui.line_edit_path_out.setText(currpath)
            self.line_edit_path_out_preaction()
            self.INPpar.path_out=self.ui.line_edit_path_out.text()

#******************** Settings
    def setPathOutLabel(self):
        #Clickable label: no need for setStatusTip
        if self.INPpar.OptionValidPathOut:
            self.ui.label_check_path_out.setPixmap(self.pixmap_v)
            self.ui.label_check_path_out.setToolTip("The specified path of the output folder exists!")
        else:
            self.ui.label_check_path_out.setPixmap(self.pixmap_x)
            self.ui.label_check_path_out.setToolTip("The specified path of the output folder does not exist!")

#******************** Layout
    def setOptionValidPathOut(self):
        self.INPpar.OptionValidPathOut=int(os.path.exists(self.INPpar.path_out))
    
#*************************************************** Output root  
#******************** Actions
    def line_edit_root_out_changing(self):
         self.ui.label_check_root.setPixmap(QPixmap()) 

    def line_edit_root_out_preaction(self):
        entry=myStandardRoot(self.ui.line_edit_root_out.text())
        self.ui.line_edit_root_out.setText(entry)

#******************** Settings
    def setRootOutLabel(self):
        #Clickable label: no need for setStatusTip
        if self.INPpar.OptionValidRootOut==-2:
            if not self.INPpar.FlagReadCalib:
                self.ui.label_check_root.setPixmap(self.pixmap_warn)
                self.ui.label_check_root.setToolTip("Files with the same root name already exist in the selected output folder!")
            else:
                self.ui.label_check_root.setPixmap(self.pixmap_v)
                self.ui.label_check_root.setToolTip("The root of the output filenames is admitted!")
        elif self.INPpar.OptionValidRootOut==0:
            self.ui.label_check_root.setPixmap(self.pixmap_x)
            self.ui.label_check_root.setToolTip("The root of the output filenames is not admitted!")
        if self.INPpar.OptionValidRootOut==1:
            self.ui.label_check_root.setPixmap(self.pixmap_v)
            self.ui.label_check_root.setToolTip("The root of the output filenames is admitted!")

#******************** Layout
    def setOptionValidRootOut(self):
        INP=self.INPpar
        ext='.cal'
        FlagExistPath=INP.OptionValidPathOut
        if FlagExistPath:
            currpath=myStandardPath(INP.path_out)
        else:
            currpath='./'
        pattern=myStandardRoot(currpath+INP.root_out)+'*'+ext
        FlagExist=False
        if FlagExistPath:
            files=findFiles_sorted(pattern)
            FlagExist=len(files)>0
        if  FlagExist: 
            INP.OptionValidRootOut=-2
        else:
            try:
                filename=pattern.replace('*','a0')+'.delmeplease'
                open(filename,'w')
            except:
                FlagDeleteFile=False
                INP.OptionValidRootOut=0
            else:
                FlagDeleteFile=True
                INP.OptionValidRootOut=1
            finally:
                if FlagDeleteFile:
                    os.remove(filename)


if __name__ == "__main__":
    import sys
    app=QApplication.instance()
    if not app:app = QApplication(sys.argv)
    app.setStyle('Fusion')
    object = Input_Tab_CalVi(None)
    object.show()
    app.exec()
    app.quit()
    app=None
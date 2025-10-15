from .PaIRS_pypacks import*
from .ui_Custom_Top import *
from .TabTools import *

class Custom_Top(QDialog):
    
    def __init__(self,custom_list=None):
        super().__init__()
        ui=Ui_Custom_Top()
        ui.setupUi(self)
        self.ui=ui
        setupWid(self)
        self.itemSize=QSize(500,20)
        ui.tree.FlagArrowKeysNormal=True

        self.custom_list_file=pro_path+custom_list_file

        self.queue=[]
        ui.tree.clear()
        if custom_list==None:
            self.custom_list=[os.path.basename(f)[:-10] for f in glob.glob(pro_path+outExt.pro)]
        else:
            self.custom_list=custom_list
        self.custom_list=setCustomList(lambda var,name: self.createItemInTree(ui.tree,self.queue,name,name,QIcon()))
        self.deleted=[]
        self.added=[]
        
        self.setupCallbacks()
        self.FlagAdjusting=False
        self.setButtons()

    def setupCallbacks(self): 
        self.ui.tree.itemSelectionChanged.connect(self.setButtons)
        self.ui.tree.itemChanged.connect(self.adjustText)
       
        button_up_callback=lambda: self.moveupdown(-1)
        button_down_callback=lambda: self.moveupdown(+1)
        self.ui.button_up.clicked.connect(button_up_callback)
        self.ui.button_down.clicked.connect(button_down_callback) 
        self.ui.button_edit.clicked.connect(self.editItem)
        self.ui.button_undo.clicked.connect(self.undo)
        self.ui.button_restore.clicked.connect(self.restoreItem)
        self.ui.button_delete.clicked.connect(self.removeItem)
        self.ui.button_import.clicked.connect(self.loadPastProc)
        
        self.ui.button_done.clicked.connect(self.save_and_close)
        self.ui.button_cancel.clicked.connect(lambda: self.done(0))
        
    def moveupdown(self,d):
        tree: QTreeWidget
        tree=self.ui.tree
        queue=self.queue
        item=tree.currentItem()
        indItem=tree.indexOfTopLevelItem(item)
        tree.takeTopLevelItem(indItem)
        tree.insertTopLevelItem(indItem+d,item)
        queue.insert(indItem+d,queue.pop(indItem))
        self.custom_list.insert(indItem+d,self.custom_list.pop(indItem))

        tree.setCurrentItem(item)
        self.setButtons()

    def createItemInTree(self,tree,queue,name,idata,icon):
        currentItem=QTreeWidgetItem(tree)
        tree.addTopLevelItem(currentItem)
        tree.setCurrentItem(currentItem)
        queue.append(currentItem)
        currentItem.setText(0,name)
        currentItem.setSizeHint(0,self.itemSize)
        currentItem.setIcon(0,icon)
        currentItem.setToolTip(0,name)
        currentItem.setStatusTip(0,name)
        currentItem.setFlags(currentItem.flags() | Qt.ItemIsEditable)
        currentItem.setData(0,Qt.UserRole,idata)
        return currentItem
    
    def setButtons(self,*args):
        tree: QTreeWidget
        tree=self.ui.tree
        if len(args):
            item=args[0]
            i=tree.indexFromItem(item)
            c=args[1]
        else:
            i=tree.currentIndex().row()
            item=tree.currentItem()
            c=0
        if item==None: 
            self.ui.button_down.setEnabled(False)
            self.ui.button_up.setEnabled(False)
            self.ui.button_undo.setVisible(False)
            self.ui.button_delete.setVisible(False)
            self.ui.button_edit.setVisible(False)
            self.ui.button_restore.setVisible(False)
            return
        indItem=tree.indexOfTopLevelItem(tree.currentItem())
        isItemFirst=indItem==0
        isItemLast=indItem==tree.topLevelItemCount()-1
        self.ui.button_down.setEnabled(not isItemLast)
        self.ui.button_up.setEnabled(not isItemFirst)
        flagDeleted=item.font(c).strikeOut()
        self.ui.button_undo.setVisible(item.data(0,Qt.UserRole)!=item.text(0) and not flagDeleted)
        self.ui.button_delete.setVisible(not flagDeleted)
        self.ui.button_edit.setVisible(not flagDeleted)
        self.ui.button_restore.setVisible(flagDeleted)
    
    def editItem(self):
        item=self.ui.tree.currentItem()
        self.ui.tree.edit(self.ui.tree.indexFromItem(item))

    def adjustText(self):
        if self.FlagAdjusting: return
        self.FlagAdjusting=True
        item=self.ui.tree.currentItem()
        newName=item.text(0)
        for i in self.queue:
            if i==item: continue
            if i.data(0,Qt.UserRole)==newName:
                WarningMessage=f'The chosen name "{newName}" is already associated with a custom process. Please, indicate a different name!'
                warningDialog(self,WarningMessage)
                item.setText(0,item.data(0,Qt.UserRole))
        if  item.data(0,Qt.UserRole) and item.data(0,Qt.UserRole)!=item.text(0):
            item.setIcon(0,self.ui.button_edit.icon())
        else:
            item.setIcon(0,QIcon())
        self.setButtons()
        self.FlagAdjusting=False

    def undo(self):
        self.FlagAdjusting=True
        item=self.ui.tree.currentItem()
        item.setText(0,item.data(0,Qt.UserRole))
        item.setIcon(0,QIcon())
        self.setButtons()
        self.FlagAdjusting=False

    def restoreItem(self):
        self.FlagAdjusting=True
        item=self.ui.tree.currentItem()
        f = item.font(0)
        f.setStrikeOut(False)
        item.setFont(0,f)
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        self.deleted.pop(self.deleted.index(item))
        item.setData(0,Qt.UserRole,item.text(0))
        item.setIcon(0,QIcon())
        self.setButtons()
        self.FlagAdjusting=False

    def removeItem(self):
        self.FlagAdjusting=True
        item=self.ui.tree.currentItem()
        #item.setFlags(item.flags() | ~Qt.ItemIsEditable)
        f = item.font(0)
        f.setStrikeOut(True)
        item.setFont(0,f)
        item.setText(0,item.data(0,Qt.UserRole))
        item.setData(0,Qt.UserRole,'')
        item.setIcon(0,QIcon())
        item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
        self.deleted.append(item)
        self.setButtons()
        self.FlagAdjusting=False

    def save_and_close(self):
        if len(self.deleted):
            WarningMessage="Some items were deleted from the list. The corresponding files will be removed from the disk. This operation is irreversible.\n"+\
            "Do you want to continue?"
            flag=questionDialog(self,WarningMessage)
        else:
            flag=True
        if flag:
            self.FlagAdjusting=True
            for item in self.deleted:
                self.deleteItem(item)
                i=self.queue.index(item)
                self.custom_list.pop(i)
                self.queue.pop(i)
            for item in self.queue:
                self.renameItem(item)
                self.custom_list[self.queue.index(item)]=item.text(0)
            self.saveCustomList()
            self.FlagAdjusting=False
            self.done(1)

    def deleteItem(self,item):
        filename=pro_path+item.text(0)+outExt.pro
        if os.path.exists(filename):
            os.remove(filename)

    def renameItem(self,item):
        if item.text(0)==item.data(0,Qt.UserRole) and item.data(0,Qt.UserRole)!='': return

        filename=pro_path+item.text(0)+outExt.pro
        if not os.path.exists(filename):
            dummyfilename=pro_path+item.text(0)+outExt.dum
            try:
                open(dummyfilename,'w')
            except:
                OptionValidRoot=False
            else:
                OptionValidRoot=True
            finally:
                if os.path.exists(dummyfilename):
                    os.remove(dummyfilename)    
        else: OptionValidRoot=True

        if not OptionValidRoot: return
        filename_old=pro_path+item.data(0,Qt.UserRole)+outExt.pro
        if os.path.exists(filename_old):
            os.rename(filename_old,filename)
            item.setData(0,Qt.UserRole,item.text(0))

    def saveCustomList(self):
        try:
            with open(self.custom_list_file,'w') as file:
                for c in self.custom_list:
                    file.write(c+'\n')
                file.close()
        except:
            pri.Error.red(f'Error while trying to save the custom process list: {self.custom_list_file}.\n{traceback.format_exc()}\n')


    def loadPastProc(self,*args):
        if len(args): inpath=args[0]
        else: inpath='./'
        ext_pro=f'*{outExt.min} *{outExt.piv}  *.cfg' 
        filename, _ = QFileDialog.getOpenFileName(self,\
                "Select an image file of the sequence", filter=ext_pro,\
                    dir=inpath,\
                    options=optionNativeDialog)
        if not filename: return

        ext='.'+filename.split('.')[-1] 
        if ext in (outExt.min,outExt.piv):
            try:
                with open(filename, 'rb') as file:
                    data=pickle.load(file)
                    PROpar=data.PRO
            except Exception as inst:
                pri.Error.red(f'Error while loading past process:\n{traceback.format_exc()}\n\n{inst}\n')
                WarningMessage=f'Error while importing {filename}. Perhaps, the file is corrupted.'
                warningDialog(self,WarningMessage)
                return
        elif filename[-4:]=='.cfg':
            try:
                p=PaIRS_lib.PIV()
                p.readCfgProc(filename)
            except Exception as inst:
                pri.Error.red(f'Error while loading the cfg file {filename}:\n{traceback.format_exc()}\n\n{inst}\n')
                errPIVlib='\n'.join(str(inst.args[0]).split('\n')[3:]) #str(inst.__cause__).split('\n')[3] #solved
                WarningMessage=f'Error while importing {filename}:\n{errPIVlib}'
                warningDialog(self,WarningMessage)
                return
            try: 
                from .procTools import PIV2Pro
                PROpar=PIV2Pro(p)
                for f in PROpar.fields:
                    a=getattr(PROpar,f)
                    if type(a)==float:
                        setattr(PROpar,f,round(a,4))
            except Exception as inst:
                pri.Error.red(f'Error while loading the cfg file {filename}:\n{traceback.format_exc()}\n\n{inst}\n')
                WarningMessage=f'Error while importing {filename}. Perhaps, the .cfg file does not correspond to a valid PIV process or the file is corrupted.'
                warningDialog(self,WarningMessage)
                return
        else:
            WarningMessage=f'Invalid selected file format ({ext})! Please select one of the following extentions:\n{ext_pro}'
            warningDialog(self,WarningMessage)
            return
        
        
        name=os.path.basename(filename).split('.')[0]
        filename=pro_path+name+outExt.pro
        i=0
        while os.path.exists(filename):
            filename=pro_path+name+f'_{i}{outExt.pro}'
            i+=1
        if i: name+=f'_{i-1}'

        PROpar.top=0
        PROpar.FlagCustom=False
        PROpar.name=name
        try:
            with open(filename,'wb') as file:
                pickle.dump(PROpar,file)
                pri.Info.blue(f'Saving custom process file {filename}')
                self.createItemInTree(self.ui.tree,self.queue,name,name,QIcon())
                self.custom_list.append(name)
        except Exception as inst:
            pri.Error.red(f'Error while saving custom process file {filename}:\n{traceback.format_exc()}\n\n{inst}')




if __name__ == "__main__":
    import sys
    app=QApplication.instance()
    if not app:app = QApplication(sys.argv)
    app.setStyle('Fusion')
    object = Custom_Top()
    object.exec()
    #app.exec()

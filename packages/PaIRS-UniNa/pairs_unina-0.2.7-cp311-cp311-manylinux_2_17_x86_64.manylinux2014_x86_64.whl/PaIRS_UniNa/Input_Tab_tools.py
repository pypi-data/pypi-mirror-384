import os.path

from PySide6.QtWidgets import QWidget
from .PaIRS_pypacks import*
from .addwidgets_ps import*
from .TabTools import TABpar
from .listLib import *
from concurrent.futures import ThreadPoolExecutor

FlagSpinButtons_Debug=True
batch_size_image_creation=200
sleep_time_item_worker=0.05

class ImageSet(TABpar):

    def __init__(self,path='',exts=supported_exts):
        self.setup()
        self.lists=[f for f,v in self.__dict__.items() if type(v)==list]
        self.supported_exts = exts
        super().__init__('ImageSet','Input')
        self.unchecked_fields+=['signals','fname','fnumb','outFiles']
        if path: self.scanPath(path)
        
    def setup(self):
        self.path       = './'
        self.count      = 0
        self.pattern    = []
        self.pa         = []
        self.fname      = []
        self.fnumb      = []
        self.ndig       = []
        self.nimg       = []
        self.ind_in     = []
        self.ind_fin    = []
        self.ext        = []
        self.link       = []
        self.outFiles   = {}

    def nameF(self,fname,i):
        a=fname[0]
        ndigits=fname[1]
        b=fname[2]
        return a+f"{i:0{ndigits}d}"+b if type(i)==int else a+str(i)+b
    
    def numbF(self,fnumb,name):
        n=fnumb[0]
        ndigits=fnumb[1]
        return int(name[n:n+ndigits])

    def scanPath(self,path):
        pri.Time.blue(f'ImageSet: start scanning path {path}')
        self.clearLists()
        path=myStandardPath(path) #maybe useless
        self.path=path
        files=findFiles_sorted(path+"*.*") # needed to use the recompiled reg expressions   
        for k,file in enumerate(files):
            if not any(file.endswith(ex) for ex in self.supported_exts):
                continue
            basename=os.path.basename(file)
            FlagMatch=False
            if self.count:
                FlagMatch=self.checkMatch(basename)
            if not FlagMatch:
                self.addPattern(basename)
                for j in range(k):
                    basename=os.path.basename(files[j])
                    FlagMatch=self.checkMatch(basename,FlagOnlyLast=True)
        self.sortLists()
        self.createLink()
        self.scanOutFile()
        pri.Time.blue(f'ImageSet: end scanning path {path}')
        return self

    def scanOutFile(self):
        self.outFiles={}
        if os.path.exists(self.path):
            _,dirnames,_=next(os.walk(self.path))
            foldernames=[self.path]+[self.path+d+'/' for d in dirnames]
            values=[v for _,v in outExt.__dict__.items() if type(v)==str]
            for ext in values:
                self.outFiles[ext]=[]
                for fold in foldernames:
                    self.outFiles[ext]+=findFiles_sorted(fold+'*'+ext)

    def clearLists(self):
        self.count=0
        for f in self.lists: setattr(self,f,[])
        return
    
    def checkMatch(self,basename,FlagOnlyLast=False):
        FlagMatch=False
        if FlagOnlyLast: kra=[self.count-1]
        else: kra=range(self.count)
        if self.count:
            for k in kra:
                pa:re.Pattern=re.compile(self.pa[k])
                if pa.match(basename):
                    FlagMatch=True
                    self.nimg[k]+=1
                    ind=self.numbF(self.fnumb[k],basename)
                    self.ind_in[k]=min([self.ind_in[k],ind])
                    self.ind_fin[k]=max([self.ind_fin[k],ind])
        return FlagMatch            

    def addPattern(self,basename):
        _, ext = os.path.splitext(basename)
        split_basename=re.split(r'(\d+)', basename)
        c=0
        for k,s in enumerate(split_basename):
            if not len(s): continue
            if s[0].isdigit():
                self.count+=1
                ndig=len(s)
                self.ndig.append(ndig)
                self.nimg.append(1)
                self.ind_in.append(int(s))
                self.ind_fin.append(int(s))

                pattern_list=split_basename.copy()
                pattern_list[k]="*{"+str(ndig)+"}"
                pattern="".join(pattern_list)
                self.pattern.append(pattern)

                pattern_list[k]='\\d{'+str(ndig)+'}'
                pattern="".join(pattern_list)
                #pa=re.compile(pattern)
                self.pa.append(pattern)

                pre ="".join(pattern_list[:k])
                post="".join(pattern_list[k+1:])
                fname=[pre,ndig,post] #lambda i, a=pre, b=post, ndigits=ndig: a+f"{i:0{ndigits}d}"+b if type(i)==int else a+str(i)+b
                self.fname.append(fname)

                fnumb=[c,ndig] #lambda name, n=c, ndigits=ndig: int(name[n:n+ndigits])
                self.fnumb.append(fnumb)
                self.ext.append(ext)
                self.link.append([])

            c+=len(s)
        return

    def sortLists(self):
        if not self.count: return
        lind=range(len(self.nimg))
        self.nimg.reverse()
        _,lind=zip(*sorted(zip(self.nimg, lind),reverse=True))
        for f in self.lists:
            v=getattr(self,f)
            v.reverse() if f!='nimg' else None
            v2=[v[i] for i in lind]
            setattr(self,f,v2)
        return

    def createLink(self):
        for k,p in enumerate(self.pattern):
            alpha=[]
            jalpha=[]
            number=[]
            jnumber=[]
            for j,p2 in enumerate(self.pattern):
                p2:str
                if len(p)!=len(p2): continue
                diff=[i for i in range(len(p)) if p[i]!=p2[i]]
                if len(diff)==1: 
                    if p2[diff[0]].isalpha(): 
                        jl=jalpha
                        l=alpha
                    else: 
                        jl=jnumber
                        l=number
                    i=0
                    while i<len(jl) and p2[diff[0]]<l[i]: i+=1
                    jl.insert(i-1,j)
                    l.insert(i-1,p2[diff[0]])
            self.link[k]=jalpha+sorted(jnumber)+[k]
        return        

    def print(self):
        pri.Coding.white('\n'+f'Image sets found in path "{self.path}"')
        for k in range(self.count):
            pri.Coding.white(f'{k:2d}:   '+f'{self.pattern[k]}'+'\t'+f'n img = {self.nimg[k]} '+'\t'+f'{self.ind_in[k]}-{self.ind_fin[k]}')
            for j in self.link[k]:
                pri.Coding.white('      '+f'{self.pattern[j]}')
            pri.Coding.white(' ')

    def genList(self,k,i,npairs,step):
        if k>=self.count:
            pri.Error.red(f'Trying to access a non-existing index position ({k}) in the image set structure ({self.count} sets identified)')
            return []
        f=i+npairs*step
        if k>-1: return [self.nameF(self.fname[k],j) for j in range(i,f,step)]
        else:    
            return ['' for _ in range(i,f,step)] if step else []
    
    def genListsFromIndex(self,k,i=None,npairs=None,step=None,ncam=None):
        if k>=self.count:
            pri.Error.red(f'Trying to access a non-existing index position ({k}) in the image set structure ({self.count} sets identified)')
            imList=[[[]]]
            imEx=[[[]]]
            return self.path,imList,imEx
        if not i: i=self.ind_in[k]
        if not npairs: npairs=self.nimg[k]
        if not step: step=1
        if not ncam: ncam=max([len(self.link[k])-1,1])
        l_c1_f1=self.genList(k,i,npairs,step)
        imEx1=[os.path.exists(self.path+f) if f else False for f in l_c1_f1 ]
        l_c1_f2=self.genList(self.link[k][0],i,npairs,step)
        imEx2=[os.path.exists(self.path+f) if f else False for f in l_c1_f2]
        imList=[[l_c1_f1,l_c1_f2]]
        imEx=[[imEx1,imEx2]]
        
        for c in range(1,ncam):
            if c<len(self.link[k])-1:
                k_c=self.link[k][c]
                l_c_f1=self.genList(k_c,i,npairs,step)
                imEx1=[os.path.exists(self.path+f) if f else False for f in l_c_f1 ]
                l_c_f2=self.genList(self.link[k_c][0],i,npairs,step)
                imEx2=[os.path.exists(self.path+f) if f else False for f in l_c_f2]
            else:
                l_c_f1=['' for j in range(npairs)]
                l_c_f2=['' for j in range(npairs)]
                imEx1=[False for j in range(npairs)]
                imEx2=[False for j in range(npairs)]
            imList.append([l_c_f1,l_c_f2])
            imEx.append([imEx1,imEx2])
        return self.path,imList,imEx
    
    def genListsFromFrame(self,frame_1,frame_2,i,npairs,step,FlagTR):
        ncam=len(frame_1)
        imList=[[['' for _ in range(npairs)] for _ in range(2)] for _ in range(ncam)]
        imEx=[[[False for _ in range(npairs)] for _ in range(2)] for _ in range(ncam)]
        if i>-1:
            for c in range(ncam):
                stepc=step
                f1=frame_1[c]
                f2=frame_2[c]-1
                if f2==-1: 
                    f2=f1
                    i2=i+stepc
                    stepc*=2
                else: i2=i
                if not FlagTR: 
                    imList[c][0]=self.genList(f1,i,npairs,stepc)
                    imList[c][1]=self.genList(f2,i2,npairs,stepc)
                else:
                    npairs_half=int(npairs/2)+1
                    a=self.genList(f1,i,npairs_half,stepc)
                    b=self.genList(f2,i2,npairs_half,stepc)
                    imListTR=[val for pair in zip(a, b) for val in pair]
                    imList[c][0]=imListTR[:npairs]
                    imList[c][1]=imListTR[1:npairs+1]
                imEx[c][0]=[os.path.exists(self.path+f) if f else False for f in imList[c][0]]
                imEx[c][1]=[os.path.exists(self.path+f) if f else False for f in imList[c][1]]
        return imList,imEx

class PaIRSTree(QTreeWidget):
    cutted_itemList=[]
    cutted_items=[]
    items_expanded=[]
    deleted_itemList=[]
    deleted_items=[]

    default_row_height=20
    default_col_width=12
    default_indentation=10

    class ImageTree_signals(QObject):
        updateTree=Signal()
        updateLists=Signal()
        createdItems=Signal(int,list,bool,list)
        copyCutItems=Signal()
        pastedItems=Signal()
        
        endOfTask = Signal() 
        stopWorker = Signal()
        keep_on = Signal()

    def on_scroll(self):
        return

    def mousePressEvent(self, event: QMouseEvent):
        self.cursor_pos=event.globalPosition().toPoint()
        super().mousePressEvent(event)
        return 

    def selectedTopLevel(self):
        selectedItems=[i for i in self.selectedItems() if i.parent() is None]
        indexes=[self.indexOfTopLevelItem(i) for i in selectedItems]
        return selectedItems,indexes
    
    def selectTopLevel(self):
        selectedItems=[]
        bottomItems=[]
        for item in self.selectedItems():
            if item.parent():
                if item not in bottomItems: bottomItems.append(item)
                if item.parent() not in selectedItems: selectedItems.append(item.parent())
            elif item not in selectedItems: selectedItems.append(item)
        self.setSelectedQuickly(bottomItems,False)
        indexes=self.setSelectedQuickly(selectedItems,True)
        return selectedItems,indexes
    
    def dragEnterEvent(self, event):
        TABpar.FlagSettingPar=True
        self.dragged_items, self.dragged_indexes = self.selectTopLevel()
        self.expandedItems=[i for i in self.dragged_items if i.isExpanded()]
        #self.collapseAll()
        self.verticalScrollBarVal=self.verticalScrollBar().value()
        super().dragEnterEvent(event)
        
    def dragMoveEvent(self, event):
        pos = event.position().toPoint()
        self.hovered_item = item = self.itemAt(pos)
        if item is not None:
            if item.parent(): self.hovered_item = None
        super().dragMoveEvent(event)  # Allow the event to proceed for row moves

    #@log_qpainter_usage
    def paintEvent(self, event):
        super().paintEvent(event)
        self.paintLines()

    def paintLines(self):
        item=self.hovered_item
        if item and self.dragged_items:
            if self.dragged_items!='externalItem':
                self.drop_indicator_pos = self.dropIndicatorPosition()
                if self.drop_indicator_pos == QTreeWidget.DropIndicatorPosition.AboveItem:
                    item_rect = self.visualItemRect(item)
                    self.drawDropIndicatorLine(item_rect.top(),item_rect.x(),item_rect.height(),item_rect.width(),-1)
                elif self.drop_indicator_pos == QTreeWidget.DropIndicatorPosition.BelowItem:
                    item_rect = self.visualItemRect(item)
                    self.drawDropIndicatorLine(item_rect.bottom(),item_rect.x(),item_rect.height(),item_rect.width(),+1)
            else: #below
                item_rect = self.visualItemRect(item)
                self.drawDropIndicatorLine(item_rect.bottom(),item_rect.x(),item_rect.height(),item_rect.width(),+1)

    def drawDropIndicatorLine(self, y_pos,x_pos,dy,dx,sign=1):
        painter = QPainter(self.viewport())
        painter.setPen(self.pen)
        painter.drawLine(0, y_pos, self.viewport().width(), y_pos)

        # Calcola la posizione della freccia
        s=5*sign
        for x_pos_2 in (x_pos+2*abs(s),x_pos+dx-2*abs(s)):
            y_pos_2=y_pos-5*sign
            arrow_top = QPoint(x_pos_2, y_pos_2 - 3*s)
            arrow_bottom = QPoint(x_pos_2, y_pos_2)
            arrow_left = QPoint(x_pos_2 - s, y_pos_2-s)
            arrow_right = QPoint(x_pos_2 + s, y_pos_2-s)

            # Disegna la freccia
            painter.drawLine(arrow_top, arrow_bottom)
            #painter.drawLine(arrow_left, arrow_right)
            painter.drawLine(arrow_bottom, arrow_right)
            painter.drawLine(arrow_bottom, arrow_left)
        painter.end()

    def dropEvent(self, event):
        drop_indicator_position = self.dropIndicatorPosition()
        
        if  drop_indicator_position == QTreeWidget.DropIndicatorPosition.OnItem or self.hovered_item is None:
            self.verticalScrollBar().setValue(self.verticalScrollBarVal)
            QCursor.setPos(self.cursor_pos)
            event.ignore()  # Ignore the event if it's not a row move or a drop on an item
            FlagUpdateList=False
        else:
            #self.setVisible(False)
            super().dropEvent(event)  # Allow the event to proceed for row moves
            """
            ind=self.indexOfTopLevelItem(self.hovered_item)
            if drop_indicator_position == QTreeWidget.DropIndicatorPosition.AboveItem: ind=ind-1
            for index in self.dragged_indexes:
                self.takeTopLevelItem(index)
            self.insertTopLevelItems(ind,self.dragged_items)
            """
            
            for i in self.expandedItems: i.setExpanded(True)
            self.dropLists(self.dragged_items,self.dragged_indexes)     
            FlagUpdateList=True 
        self.setCurrentItem(self.dragged_items[-1])
        self.setSelectedQuickly(self.dragged_items,True)
        self.dragged_items=self.dragged_indexes=None
        self.repaint()
        #self.setVisible(True)
        #evita TABpar.FlagSettingPar=self.FlagSettingPar così che sai dove FlagSettingPar è settato True o False
        if self.FlagSettingPar:
            TABpar.FlagSettingPar=True
        else:
            TABpar.FlagSettingPar=False
        if FlagUpdateList: self.signals.updateLists.emit()

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.key() in (Qt.Key.Key_Return,Qt.Key.Key_Enter) and self.hasFocus():
            for f in self.addfuncreturn:
                self.addfuncreturn[f]()

    def __init__(self, parent: QWidget=None, listDim=1, listDepth=0):
        super().__init__(parent)
        if parent is None:
            self.gui=self.window()
        else:
            from .gPaIRS import gPaIRS
            if hasattr(parent,'gui'):
                self.gui:gPaIRS=parent.gui
            else:
                self.gui:gPaIRS=parent.window()
        self.listDim=listDim
        self.listDepth=listDepth
        self.signals=self.ImageTree_signals()
        
        self.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)  # Enable multi-selection mode
        self.setSelectionBehavior(QTreeWidget.SelectionBehavior.SelectItems)
        #self.setSelectionBehavior(QTreeWidget.SelectionBehavior.SelectRows)
        self.setDragDropMode(QTreeWidget.DragDropMode.InternalMove)  # Abilita il trascinamento delle voci dell'albero
        self.header().setSectionsMovable(False)
        self.setDropIndicatorShown(True)

        self.icon_warning = QIcon()
        self.icon_warning.addFile(u""+ icons_path +"warning.png", QSize(), QIcon.Normal, QIcon.Off)
        self.dragged_items=self.dragged_indexes=None
        self.hovered_item=None
        self.setAutoScroll(True)
        self.verticalScrollBarVal=self.verticalScrollBar().value()
        self.verticalScrollBar().setStyleSheet("""
            QTreeWidget {
                margin-bottom: 0px;
                }
            QTreeWidget::item {
                margin-bottom: 0px;
                }
            QTreeView {
                margin-bottom: 0px;
                }
            QScrollBar:horizontal{
                height: 15px;
                margin: 3px 0px 3px 0px;
                border: 1px transparent #2A2929;
                border-radius: 4px;
                background-color:  transparent;    /* #2A2929; */
                }
            QScrollBar::handle:horizontal{
                background-color: rgba(180,180,180,180);         /* #605F5F; */
                min-width: 30px;
                border-radius: 4px;
                }
            QScrollBar:vertical{
                width: 15px;
                margin: 0px 3px 0px 3px;
                border: 1px transparent #2A2929;
                border-radius: 4px;
                background-color:  transparent;    /* #2A2929; */
                }
            QScrollBar::handle:vertical{
                background-color: rgba(180,180,180,180);         /* #605F5F; */
                min-height: 30px;
                border-radius: 4px;
                }
            QScrollBar::add-line{
                    border: none;
                    background: none;
                }

            QScrollBar::sub-line{
                    border: none;
                    background: none;
                }""")
        #self.verticalScrollBar().valueChanged.connect(self.on_scroll)
        self.cursor_pos=self.cursor().pos()
        
        self.pen = QPen(qRgba(127,227,255,0.9))
        self.pen.setWidth(3)
        #style="background-color: rgba(173,216,230,0.1); color: rgba(128,128,128,0.25);"
        #self.setStyleSheet(f"QTreeWidget::item:selected {{{style}}}")
        #self.setStyleSheet(f"QTreeWidget::item:selected:active {{{style}}}")

        style = """
            QTreeWidget::item:selected:!active {
                background-color: rgba(0, 116, 255, 0.4);
            }
            QTreeWidget::item:selected:active {
                background-color: rgba(0, 116, 255, 0.8);
            }
            """
        self.setStyleSheet(style)

        self.addfuncreturn={}
        #self.addfuncreturn={'expand': self.expandRow}
        self.FlagSetting=False
        self.FlagReset=False
        self.FlagCutted=False

        self.nimg=0        
        self.itemList=create_empty_list_of_dimension(self.listDim)
        self.warns=[]

        self.signals.createdItems.connect(self.insertItems2List)
        self.disableTab=lambda flag: None
        self.FlagSettingPar=False

        self.setAlternatingRowColors(True)

        self.setVisible(False)        

    def duplicateItem(self, item:QTreeWidgetItem, parent=None):
        new_item = QTreeWidgetItem(parent)
        for column in range(item.columnCount()):
            new_item.setText(column, item.text(column))
            new_item.setTextAlignment(column, Qt.AlignmentFlag(item.textAlignment(column)))
            new_item.setIcon(column, item.icon(column))
        new_item.setData(0,Qt.ItemDataRole.UserRole,item.data(0,Qt.ItemDataRole.UserRole))
        for i in range(item.childCount()):
            self.duplicateItem(item.child(i), new_item)
        if parent: new_item.setExpanded(item.isExpanded())
        return new_item
    
    def setSelectedQuickly(self, items, Flag):
        selectionFlag=QItemSelectionModel.SelectionFlag.Select if Flag else QItemSelectionModel.SelectionFlag.Deselect
        selection_model = self.selectionModel()
        selection = QItemSelection()
        indexes=[]
        for i in items:
            i:QTreeWidgetItem
            if i is None: continue
            try:
                if i.parent() is None: index=self.indexOfTopLevelItem(i)
                else: index=i.parent().indexOfChild(i)
            except:
                continue
            selection.merge(QItemSelection(self.model().index(index, 0), self.model().index(index, self.columnCount()-1)), selectionFlag)
            indexes.append(index)
        selection_model.select(selection, QItemSelectionModel.SelectionFlag.ClearAndSelect )
        return indexes

    def resetImNumber(self,kin=None,kfin=None):
        if not kin: kin=0
        if not kfin: kfin=self.topLevelItemCount()-1
        self.setUpdatesEnabled(False)

        root_item = self.invisibleRootItem()
        self.warns=[]
        for i in range(self.topLevelItemCount()):
            child_item = root_item.child(i)
            if i>=kin and i<=kfin:
                current_text = child_item.text(0)
                new_text = str(i + 1)
                if current_text != new_text:
                    child_item.setText(0, new_text)
            if not child_item.data(0,Qt.ItemDataRole.UserRole)[0] and i not in self.warns:
                self.warns.append(i)
        self.warns.sort()

        self.setUpdatesEnabled(True)
        return
    
    @Slot(int,list,bool,list)
    def insertItems2List(self,i=-1,items=[],FlagSelect=False,selection=[],FlagSignal=True):
        if self.FlagReset: 
            self.clear() #clean_tree(self)
            self.FlagReset=False
        if i==-1:
            self.addTopLevelItems(items)
        else:
            self.insertTopLevelItems(i,items)
        if not selection:
            if FlagSelect: self.setSelectedQuickly(items,True)
            else: self.setSelectedQuickly(items[0:1],True)
        else:
            self.spinSelection(selection)
        if items:
            self.scrollToItem(items[-1])
            self.scrollToItem(items[0])
        self.signals.updateTree.emit()
        self.disableTab(False)
        if FlagSignal and not self.signalsBlocked(): 
            self.signals.updateLists.emit()
    
    def spinSelection(self,selection):
        return
    
    def dropLists(self, items, indexes):
        ind_in=self.indexOfTopLevelItem(items[0])
        cutted_items=pop_at_depth(self.itemList,self.listDepth,indexes)
        insert_at_depth(self.itemList,self.listDepth,ind_in,cutted_items)
        #ind_fin=self.indexOfTopLevelItem(items[-1])
        self.resetImNumber(kin=max([ind_in-1,0]))
        return
    
    def cutLists(self, indexes, FlagDeleted=False):
        if FlagDeleted: type(self).deleted_itemList=pop_at_depth(self.itemList,self.listDepth,indexes)
        else: type(self).cutted_itemList=pop_at_depth(self.itemList,self.listDepth,indexes)
        if not FlagDeleted: self.FlagCutted=True
        self.nimg-=len(indexes)  
        self.resetImNumber(kin=min(indexes))
        return
    
    def deleteLists(self, indexes):
        self.cutLists(indexes,FlagDeleted=True)
        return

    def copyLists(self, indexes):
        type(self).cutted_itemList=copy_at_depth(self.itemList,self.listDepth,indexes)
        self.FlagCutted=False
        return

    def pasteLists(self, ind, FlagDeleted=False):
        pri.Time.magenta('pasteLists: start')
        if FlagDeleted: iList=type(self).deleted_itemList
        else: iList=type(self).cutted_itemList
        self.nimg+=measure_depth_length(iList,self.listDepth)

        insert_at_depth(self.itemList,self.listDepth,ind,iList)
    
        if self.FlagCutted:
            if FlagDeleted:
                type(self).deleted_itemList=[]
                type(self).deleted_items=[]
            else:
                type(self).cutted_itemList=[]
                type(self).cutted_items=[]
            type(self).items_expanded=[]
            self.FlagCutted=False
        else:
            if FlagDeleted: type(self).deleted_itemList=deep_duplicate(iList)
            else: type(self).cutted_itemList=deep_duplicate(iList)
        pri.Time.magenta('pasteLists: list end')
        self.resetImNumber(kin=ind)
        pri.Time.magenta('pasteLists: end')
        return

    def cleanLists(self):
        self.itemList=create_empty_list_of_dimension(self.listDim)

class ItemWorker(QRunnable):
    creationType=0
    FlagRunning=False
    class ItemWorkerSignals(QObject):
        batchItems = Signal(int,int,list)  # Signal to send created item to main thread

    def __init__(self, batch_size=batch_size_image_creation, kin=0, nimg=0, selection=[]):
        super().__init__()
        self.batch_size=batch_size
        self.kin=kin
        self.nimg=nimg
        if not selection:
            selection=[kin,None,None]
        self.selection=selection

        self.signals = self.ItemWorkerSignals()
        self.is_running=True
        self.is_working=True
        self.is_busy=True

    def run(self):
        ItemWorker.FlagRunning=True
        kin=self.kin
        j=0
        while kin<self.nimg:
            if not self.is_running: 
                ItemWorker.FlagRunning=False
                return
            j+=1
            kfin=min([kin+self.batch_size-1,self.nimg-1])  
            #print(f'{j}  kin={kin}  kfin={kfin}')
            self.signals.batchItems.emit(kin,kfin,self.selection)  # Send item to the main thread
            kin=kfin+1
            self.is_busy=True
            while self.is_busy:
                timesleep(sleep_time_item_worker)  # Simulate delay in item creation
        while self.is_running:
            timesleep(sleep_time_item_worker)
        ItemWorker.FlagRunning=False

    @Slot()
    def stopWorker(self):
        self.is_running=False
    
    @Slot()
    def endOfTask(self):
        self.is_working=False  

    @Slot()
    def keep_on(self):
        self.is_busy=False  
        
class ImageNumberTree(PaIRSTree):
    minimum_width=20
    margin=30

    def __init__(self, parent: QWidget=None, listDim=4, listDepth=3):
        super().__init__(parent,listDim,listDepth)

        self.setMinimumWidth(self.minimum_width+self.margin)

        columns=['#']
        self.setColumnCount(len(columns))
        self.setHeaderLabels(columns)
        header=self.header()
        self.headerItem().setTextAlignment(0,Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter) 
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setIndentation(0)
        self.setUniformRowHeights(True)
        self.setStyleSheet(f"QTreeView::item {{ height: {self.default_row_height} px; }}")

        #Disabilita la selezione
        self.setSelectionMode(QTreeWidget.NoSelection)
        #Disabilita il drag-and-drop
        self.setDragEnabled(False)
        self.setDropIndicatorShown(False)
        self.setAcceptDrops(False)

        self.resizeTree()
        self.nItem=0
        self.ncam=1

        #self.itemSelectionChanged.connect(self.selectParent)
        self.mainTree:PaIRSTree=None
        
    def resizeTree(self):
        n=self.topLevelItemCount()
        currwidth=self.maximumWidth()
        if not n: 
            self.setMaximumWidth(self.minimumWidth())
        else:
            text=self.topLevelItem(n-1).text(0)
            textSize=QtGui.QFontMetrics(self.font()).size(QtCore.Qt.TextSingleLine, text)
            if abs(currwidth-textSize.width()-self.margin)>self.margin:
                self.setMaximumWidth(textSize.width()+self.margin)  # Aggiungi un margine se necessario
        self.currwidth=self.maximumWidth()
        if abs(currwidth-self.currwidth)>self.margin:
            self.resizeColumnToContents(0)

    def insertNumbers(self,nItem,ncam):
        if ncam!=self.ncam:
            self.clear()
        self.ncam=ncam
        self.nItem=nItem
        n=self.topLevelItemCount()
        items=[]
        if n<nItem:
            for i in range(n,nItem):
                item=QTreeWidgetItem(self,[f'{i+1}'])
                item.setTextAlignment(0,Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
                for c in range(ncam-1):
                    item.addChild(QTreeWidgetItem(item,''))
                #item.setExpanded(False)
                items.append(item)
            self.addTopLevelItems(items)
        elif n>nItem:
            self.blockSignals(True)
            for i in range(n,nItem-1,-1):
                self.takeTopLevelItem(i)
            self.blockSignals(False)
        self.resizeTree()

    def selectParent(self):
        selectedItems=self.selectedItems()
        self.blockSignals(True)
        self.clearSelection()
        for i in selectedItems:
            if i.parent() is not None:
                i.parent().setSelected(True)
            else:
                i.setSelected(True)
        self.blockSignals(False)

class AsynPaIRSTree(PaIRSTree):
    class PaIRSTreeTypes:
        single=0
        glob=1
    
    def on_scroll(self):
        return
    
    def __init__(self, parent: QWidget=None, listDim=2, listDepth=1, FlagNum=False):
        super().__init__(parent,listDim,listDepth)
        
        self.columnLabels=[]
        self.FlagNum = FlagNum
        self.pixmap_edit = QPixmap(icons_path+"edit_list.png")
        self.pixmap_copy = QPixmap(icons_path+"copy.png")
        self.pixmap_cut = QPixmap(icons_path+"cut.png")
        self.pixmap_wrap = QPixmap(icons_path+"wrap_items.png")
        self.pixmap_unwrap = QPixmap(icons_path+"unwrap_items.png")
        self.pixmap_paste_above = QPixmap(icons_path+"paste_above.png")
        self.pixmap_paste_below = QPixmap(icons_path+"paste_below.png")
        self.pixmap_import_items = QPixmap(icons_path+"read.png")

        self.ThreadPool = QThreadPool()
        self.batch_size=batch_size_image_creation
        self.numTree:ImageNumberTree=None
        self.disableButtons=lambda flag:None
        self.progressBar:QProgressBar=None
        self.infoLabel:QLabel=None

        self.initializeWorker()

        self.imList=create_empty_list_of_dimension(self.listDim-1)
        self.imEx=create_empty_list_of_dimension(self.listDim-1)

        self.itemWorker=None

        self.type=self.PaIRSTreeTypes().glob
        self.numTree=None

    def setVisible(self,visible):
        super().setVisible(visible)
        if hasattr(self,'numTree') and self.numTree is not None: 
            self.numTree.setVisible(visible)

    def setNumTree(self,numTree:ImageNumberTree):
        self.numTree=numTree
        self.numTree.mainTree=self

        self.verticalScrollBar().valueChanged.connect(self.scrollNumTree)
        self.numTree.verticalScrollBar().valueChanged.connect(self.scrollMainTree)

        self.itemExpanded.connect(lambda item: self.expandNumTree(item,True))
        self.itemCollapsed.connect(lambda item: self.expandNumTree(item,False))
        self.numTree.itemExpanded.connect(lambda item: self.expandMainTree(item,True))
        self.numTree.itemCollapsed.connect(lambda item: self.expandMainTree(item,False))

        #self.itemSelectionChanged.connect(self.selectNumTree)
        #self.numTree.itemSelectionChanged.connect(self.selectMainTree)

        self.Expanding=False
        
    def scrollNumTree(self):
        self.numTree.verticalScrollBar().setValue(self.verticalScrollBar().value())
    
    def scrollMainTree(self):
        self.verticalScrollBar().setValue(self.numTree.verticalScrollBar().value())
    
    def expandNumTree(self,item,flag):
        if self.Expanding: return
        self.Expanding=True
        i=self.indexOfTopLevelItem(item)
        self.numTree.topLevelItem(i).setExpanded(flag)
        self.Expanding=False

    def expandMainTree(self,item,flag):
        if self.Expanding: return
        self.Expanding=True
        i=self.numTree.indexOfTopLevelItem(item)
        self.topLevelItem(i).setExpanded(flag)
        self.Expanding=False

    def selectNumTree(self):
        selectedItems=self.selectedItems()
        selectedItems=[i.parent() if i.parent() is not None else i for i in selectedItems]
        items=[self.numTree.topLevelItem(self.indexOfTopLevelItem(i)) for i in selectedItems]
        self.numTree.setSelectedQuickly(items,True)

    def selectMainTree(self):
        selectedItems=self.numTree.selectedItems()
        items=[self.topLevelItem(self.numTree.indexOfTopLevelItem(i)) for i in selectedItems]
        self.setSelectedQuickly(items,True)

    def resetImNumber(self,kin=None,kfin=None):
        self.setUpdatesEnabled(False)

        if self.numTree: 
            self.numTree.insertNumbers(self.nimg,self.ncam)
            for k in range(self.nimg):
                item=self.topLevelItem(k)
                numb=self.numTree.topLevelItem(k)
                numb.setExpanded(item.isExpanded())

        warns=np.array(self.imEx)
        if len(warns.shape)==3:
            self.warns:list=np.where(np.any(warns == False, axis=(0, 1)))[0].tolist()
        else:
            self.warns = np.where(warns == False)[0].tolist()
        self.warns.sort()
        self.setColumnHidden(0,(self.ncam==1 or self.type==self.PaIRSTreeTypes.single) and len(self.warns)==0)

        self.setUpdatesEnabled(True)
        return
    
    def setItemWorker(self,nimg,selection,fun,pixmap):
        self.disableButtons(True)
        #self.disableTab(True)
        worker = ItemWorker(self.batch_size,0,nimg,selection)
        worker.signals.batchItems.connect(fun)
        self.signals.endOfTask.connect(worker.endOfTask)
        self.signals.stopWorker.connect(worker.stopWorker)
        self.signals.keep_on.connect(worker.keep_on)
        if self.progressBar:
            self.progressBar.setMinimum(0)
            self.progressBar.setMaximum(nimg-1)
            self.progressBar.setValue(0)
            self.infoLabel.setPixmap(pixmap)
        return worker
    
    def initializeWorker(self):
        self.workerItems=[]
        self.workerIndexes=[]
        self.workerFlagCut=None
        self.workerFlagWrap=None
        self.workerInd=None
        self.workerNimg=0

    def setStepButtonEnabled(self,FlagEnabled):
        self.stepButton.setEnabled(FlagEnabled) 
        return

    def stopWorker(self):
        if self.itemWorker is not None:
            self.signals.stopWorker.emit()
            self.initializeWorker()
            #QApplication.processEvents()
            timesleep(sleep_time_item_worker*2)
            self.stepButton.setEnabled(True)
        #while ItemWorker.FlagRunning==True:
        #    timesleep(sleep_time_item_worker*2)
        
    def startWorker(self):
        self.stopWorker()
        self.stepButton:QToolButton=self.gui.ui.Explorer.stepButtonBar.buttons[self.gui.ui.Explorer.ITEpar.Step]
        self.stepButtonEnabled=self.stepButton.isEnabled()
        self.setStepButtonEnabled(False)
        
    #worker
    def setLists(self,selection=[],FlagAsync=True):
        self.startWorker()
        if self.type==self.PaIRSTreeTypes().glob:
            self.nimg=nimg=len(self.imList[0][0])
            self.ncam=len(self.imList)
        else:
            self.nimg=nimg=len(self.imList)
            self.ncam=1
        self.setColumnHidden(0,self.ncam==1)
        if self.ncam==1 and len(self.columnLabels)>1:
            columns=[""]+self.columnLabels[1:]
        else:
            columns=self.columnLabels
        self.setHeaderLabels(columns)

        self.clear() #clean_tree(self)
        
        if self.nimg:
            if self.FlagNum:
                if not selection:
                    selection=[0,None,None]
                self.createChuncks(0,self.nimg-1,selection)
            else:
                self.itemWorker=self.setItemWorker(nimg,selection,self.createChuncks,self.pixmap_edit)
                self.ThreadPool.start(self.itemWorker)
        else:
            if self.workerFlagCut: self.endOfCut()
            self.endOfCreation()
        return

    def resizeHeader(self):
        for i in range(self.columnCount()-1):
            self.resizeColumnToContents(i)
        
    @Slot(int,int,list)
    def createChuncks(self,kin,kfin,selection):
        FlagSettingPar=TABpar.FlagSettingPar
        TABpar.FlagSettingPar=True
        items=self.createItems(kin,kfin)
        self.addTopLevelItems(items)
        if self.numTree: self.numTree.insertNumbers(kfin,self.ncam)
        self.resizeHeader()
        if self.progressBar: self.progressBar.setValue(kfin)
        if kin<=selection[0]<=kfin:
            if selection[1] is None:
                item_in=self.topLevelItem(selection[0])
                self.setSelectedQuickly([item_in],True)
            else:
                self.spinSelection(selection)
        self.signals.keep_on.emit()
        TABpar.FlagSettingPar=FlagSettingPar
        if kfin==self.nimg-1:
            self.endOfCreation()
        

    def endOfCreation(self):
        if self.workerFlagCut:
            self.endOfCut()
        else:
            self.resetImNumber()
        self.signals.updateTree.emit()
        self.disableTab(False)
        self.signals.stopWorker.emit()  
        self.setStepButtonEnabled(self.stepButtonEnabled)   
        self.disableButtons(False)
        self.itemWorker=None
        if not self.signalsBlocked(): 
            self.signals.updateLists.emit()
        
    #worker
    def copyCutItems(self,items,indexes,FlagCut):
        self.startWorker()
        self.workerItems=items
        self.workerIndexes=indexes
        self.workerFlagCut=FlagCut
        self.workerNimg=self.nimg
        nimg=len(self.workerIndexes)

        type(self).cutted_items=[None]*nimg
        type(self).cutted_itemList=[]

        pixmap=self.pixmap_cut if FlagCut else self.pixmap_copy
        self.itemWorker=self.setItemWorker(nimg,[],self.copyCutChunks,pixmap)
        self.ThreadPool.start(self.itemWorker)

    @Slot(int,int,list)
    def copyCutChunks(self,kin,kfin,selection):
        FlagSettingPar=TABpar.FlagSettingPar
        TABpar.FlagSettingPar=True
        n=len(self.workerIndexes)-1
        for k in range(n-kin,n-kfin-1,-1):
            type(self).cutted_items[k]=self.duplicateItem(self.workerItems[k])
        cutted_list=copy.deepcopy(type(self).cutted_itemList)
        self.blockSignals(True)
        self.setUpdatesEnabled(False)
        if self.workerFlagCut:
            if n<0.5*self.workerNimg:
                for k in range(n-kin,n-kfin-1,-1):
                    self.takeTopLevelItem(self.workerIndexes[k])
            self.cutLists(self.workerIndexes[n-kfin:n-kin+1])
        else:
            self.copyLists(self.workerIndexes[n-kfin:n-kin+1])
        self.setUpdatesEnabled(True)
        self.blockSignals(False)
        insert_at_depth(type(self).cutted_itemList,self.listDepth,-1,cutted_list)
        if self.numTree: self.numTree.insertNumbers(self.nimg,self.ncam)
        self.resizeHeader()
        self.progressBar.setValue(kfin)
        if kin<=selection[0]<=kfin and self.workerFlagCut:
            if selection[1] is None:
                item_in=self.topLevelItem(selection[0])
                self.setSelectedQuickly([item_in],True)
            else:
                self.spinSelection(selection)
        self.signals.keep_on.emit()
        TABpar.FlagSettingPar=FlagSettingPar
        if kfin==len(self.workerIndexes)-1:
            if n>=0.5*self.workerNimg:
                if self.workerFlagCut:
                    self.setLists()
                    return
            self.endOfCut()
            if not self.signalsBlocked(): 
                self.signals.updateLists.emit()
                
    def endOfCut(self):
        self.resetImNumber()
        self.disableButtons(False)
        self.workerItems=[]
        self.workerIndexes=[]
        self.workerFlagCut=None
        self.workerNimg=0
        self.signals.copyCutItems.emit()
        self.itemWorker=None
        self.setStepButtonEnabled(True)
        
        
    #worker
    def wrapUnWrapItems(self,items,indexes,FlagWrap):
        self.startWorker()
        self.workerItems=items
        self.workerIndexes=indexes
        self.workerFlagWrap=FlagWrap
        nimg=len(self.workerIndexes)

        pixmap=self.pixmap_wrap if FlagWrap else self.pixmap_unwrap
        self.itemWorker=self.setItemWorker(nimg,[],self.wrapUnWrapChuncks,pixmap)
        self.ThreadPool.start(self.itemWorker)

    @Slot(int,int,list)
    def wrapUnWrapChuncks(self,kin,kfin,selection):
        FlagSettingPar=TABpar.FlagSettingPar
        TABpar.FlagSettingPar=True
        self.blockSignals(True)
        self.setUpdatesEnabled(False)
        for k in range(kin,kfin+1):
            item:QTreeWidgetItem=self.workerItems[k]
            item.setExpanded(not self.workerFlagWrap)
        self.setUpdatesEnabled(True)
        self.blockSignals(False)
        self.progressBar.setValue(kfin)
        #QApplication.processEvents()
        self.signals.keep_on.emit()
        TABpar.FlagSettingPar=FlagSettingPar
        if kfin==len(self.workerIndexes)-1:
            self.endOfWrap()
        
        
    def endOfWrap(self):
        self.resetImNumber()
        self.disableButtons(False)
        self.workerItems=[]
        self.workerIndexes=[]
        self.workerFlagWrap=None
        self.itemWorker=None
        self.setStepButtonEnabled(True)

    #worker
    def pasteItems(self,items,i,FlagAbove):
        self.startWorker()
        self.workerItems=items
        self.workerInd=i
        self.clearSelection()
        nimg=len(self.workerItems)

        pixmap=self.pixmap_paste_above if FlagAbove else self.pixmap_paste_below
        self.itemWorker=self.setItemWorker(nimg,[],self.pasteChuncks,pixmap)
        self.ThreadPool.start(self.itemWorker)

    @Slot(int,int,list)
    def pasteChuncks(self,kin,kfin,selection):
        FlagSettingPar=TABpar.FlagSettingPar
        TABpar.FlagSettingPar=True
        n=len(self.workerItems)
        items=self.workerItems[kin:kfin+1]
        self.insertTopLevelItems(self.workerInd+kin,items)
        self.blockSignals(True)
        for i in items: 
            i:QTreeWidgetItem
            i.setSelected(True)
        self.blockSignals(False)
        if self.numTree: self.numTree.insertNumbers(self.nimg+kfin,self.ncam)
        self.resizeHeader()
        self.progressBar.setValue(kfin)
        self.signals.keep_on.emit()
        TABpar.FlagSettingPar=FlagSettingPar
        if kfin==n-1:
            self.endOfPaste()
        

    def endOfPaste(self):
        self.FlagCutted=True
        self.pasteLists(self.workerInd)
        self.workerItems=[]
        self.workerInd=None

        self.signals.updateTree.emit()
        self.disableTab(False)
        self.signals.stopWorker.emit()     
        self.setStepButtonEnabled(True)
        self.disableButtons(False)
        self.signals.pastedItems.emit()
        self.itemWorker=None
        if not self.signalsBlocked(): 
            self.signals.updateLists.emit()

    #worker
    def importItems(self,items):
        self.startWorker()
        self.workerItems=items
        self.clearSelection()
        nimg=len(self.workerItems)

        pixmap=self.pixmap_import_items
        self.itemWorker=self.setItemWorker(nimg,[],self.importChuncks,pixmap)
        self.ThreadPool.start(self.itemWorker)

    @Slot(int,int,list)
    def importChuncks(self,kin,kfin,selection):
        FlagSettingPar=TABpar.FlagSettingPar
        TABpar.FlagSettingPar=True
        n=len(self.workerItems)
        items=self.workerItems[kin:kfin+1]
        self.addTopLevelItems(items)
        for i in items: 
            i:QTreeWidgetItem
            i.setSelected(True)
        if self.numTree: self.numTree.insertNumbers(self.nimg+kfin,self.ncam)
        self.resizeHeader()
        self.progressBar.setValue(kfin)
        self.signals.keep_on.emit()
        TABpar.FlagSettingPar=FlagSettingPar
        if kfin==n-1:
            self.endOfImport()

    def endOfImport(self):
        self.resetImNumber() 
        self.workerItems=[]

        self.signals.updateTree.emit()
        self.disableTab(False)
        self.signals.stopWorker.emit()     
        self.setStepButtonEnabled(True)
        self.disableButtons(False)
        self.signals.pastedItems.emit()
        self.itemWorker=None
        if not self.signalsBlocked(): 
            self.signals.updateLists.emit()

class GlobalImageTree(AsynPaIRSTree):

    def __init__(self, parent: QWidget=None, listDim=4, listDepth=3, FlagNum=False):
        super().__init__(parent,listDim,listDepth)

        self.FlagNum=FlagNum
        self.columnLabels=["cam","frame 1","frame 2"]
        self.setHeaderLabels(self.columnLabels)
        self.setColumnCount(len(self.columnLabels))
        header=self.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self.headerItem().setTextAlignment(0,Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter) 
        self.setUniformRowHeights(True)
        self.setStyleSheet(f"QTreeView::item {{ height: {self.default_row_height} px; }}")

        self.path=''
        self.ncam=1
        self.nframe=2
        self.imList=create_empty_list_of_dimension(self.listDim-1)
        self.imEx=create_empty_list_of_dimension(self.listDim-1)
        self.setImListEx()
        self.itemDoubleClicked.connect(self.item_double_clicked)

    def item_double_clicked(self, item, column):
        self.setSelectedQuickly([item]+self.selectedItems(),True)

    def setImListEx(self):
        self.itemList=create_empty_list_of_dimension(self.listDim)
        expand_level(self.itemList,level=0,target_length=2)
        #expand_level(self.itemList,level=1,target_length=self.ncam)
        #expand_level(self.itemList,level=2,target_length=self.nframe)

        self.itemList[0]=self.imList
        self.itemList[1]=self.imEx

    def indexSelection(self):
        item=self.currentItem()
        if item:
            FlagBottomLevel=bool(item.parent())
            parent_item=item.parent() if FlagBottomLevel else item
            img=self.indexOfTopLevelItem(parent_item)+1
            cam=1 if not FlagBottomLevel else parent_item.indexOfChild(item)+2
            frame=1 if self.currentColumn()<=1 else self.currentColumn()
        else:
            img=cam=frame=0
        return img, cam, frame

    def spinSelection(self,selection):
        if not selection:
            self.clearSelection()
            #self.setCurrentItem(None)
            return
        r,c,f=[i-1 for i in selection][:]
        if r<0: 
            self.clearSelection()
            #self.setCurrentItem(None)
            self.signals.updateTree.emit()
            return
        parent_item = self.topLevelItem(r)
        if parent_item:
            if c==0: item=parent_item
            else: item=parent_item.child(c-1)
            self.indexFromItem(item)
            self.setCurrentItem(item, f+1)
 
    def createNullItem(self,k=None):
        if not k: k=self.topLevelItemCount()
        data=[False,[],[]]
        data[1].append(['(!)','(!)'])
        data[2].append([False,False])
        item_data=['1','(!)','(!)']
        item=QTreeWidgetItem(None,item_data)
        item.setTextAlignment(0,Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter) 
        item.setToolTip(1,item_data[1])
        item.setStatusTip(1,item_data[1])
        item.setToolTip(2,item_data[2])
        item.setStatusTip(2,item_data[2])
        for c in range(1,self.ncam):
            data[1].append(['(!)','(!)'])
            data[2].append([False,False])
            item_data=[str(c+1),'(!)','(!)']
            item2=QTreeWidgetItem(item,item_data)
            item2.setTextAlignment(0,Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter) 
            item.setToolTip(2,item_data[2])
            item.setStatusTip(2,item_data[2])
            item.setToolTip(3,item_data[3])
            item.setStatusTip(3,item_data[3])
        item.setIcon(0,self.icon_warning)
        item.setToolTip(0,'Files (!) missing')
        item.setStatusTip(0,'Files (!) missing')
        item.setData(0,Qt.ItemDataRole.UserRole,data)
        self.insertTopLevelItem(k,item)
        self.warns.append(k)

    def scanLists(self,FlagChange=True):
        def scan_items(k):
            topLevelItem=None
            FlagChanged=False
            FlagWarn=False              
            for c in range(self.ncam):
                for f in range(2):
                    item=None
                    self.imEx[c][f][k]=os.path.exists(self.path+self.imList[c][f][k]) if self.imList[c][f][k] else False
                    FlagWarn=FlagWarn or not self.imEx[c][f][k]
                    if FlagChange: #and ex!=self.imEx[c][f][k] 
                        FlagChanged=True
                        if item==None:
                            if topLevelItem==None: topLevelItem=self.topLevelItem(k)
                            if c: item=topLevelItem.child(c-1)
                            else: item=topLevelItem
                            text=self.imList[c][f][k]
                            if not self.imEx[c][f][k]: text=text+' (!)' if text  else '(!)'
                            item.setText(f+1,text)
                            item.setToolTip(f+1,text)
                            item.setStatusTip(f+1,text)
            #if not FlagChanged: return
            if topLevelItem==None: topLevelItem=self.topLevelItem(k)
            #FlagWarn_old=k in self.warns
            #if FlagWarn!=FlagWarn_old:
            if FlagWarn:
                self.warns.append(k)
                topLevelItem.setIcon(0,self.icon_warning)
                topLevelItem.setToolTip(0,'Files (!) missing')
                topLevelItem.setStatusTip(0,'Files (!) missing')
            else:
                self.warns.remove(k)
                topLevelItem.setIcon(0,QIcon())
                topLevelItem.setToolTip(0,'')
                topLevelItem.setStatusTip(0,'Files (!) missing')
            return
        for k in range(self.topLevelItemCount()): scan_items(k)
        self.resetImNumber()
        return

    def printImageList(self):
        for i in range(self.nimg):
            s='*' if not self.eim[i] else ' '
            pri.Coding.white(f'{i:5d}{s}:'+'\t'+f'{self.imList[0][0][i]}, {self.imList[0][1][i]}')
            for c in range(1,self.ncam):
                pri.Coding.white(f'       '+'\t'+f'{self.imList[c][0][i]}, {self.imList[c][1][i]}')

    def createItems(self,kin=None,kfin=None):
        imList=self.imList
        imEx=self.imEx

        if kin is None: kin=0
        if kfin is None: kfin=min([self.batch_size-1,len(imList[0][0])])
        nimg=kfin-kin+1
        ncam=len(imList)
       
        self.warns=[]
        items=[None]*nimg
        j=-1
        for k in range(kin,kfin+1):
            j+=1
            data=[True,[],[]]
            FlagWarn=False
            
            if k>=len(imList[0][0]): 
                for i in range(kfin,k-1,-1):
                    items.pop(-1)
                break
            images=[imList[0][0][k], imList[0][1][k]]
            ex=[imEx[0][0][k], imEx[0][1][k]]
            data[1].append(images)
            data[2].append(ex)
            item_data=['1' if self.ncam>1 else '']+images#[str(k+1),'1']+images
            if not ex[0]: 
                FlagWarn=True
                item_data[1]=item_data[1]+' (!)' if item_data[1] else '(!)'
            if not ex[1]: 
                FlagWarn=True
                item_data[2]=item_data[2]+' (!)' if item_data[2] else '(!)'
        
            item=QTreeWidgetItem(self,item_data)
            item.setTextAlignment(0,Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter) 
            items[j]=item
            item.setToolTip(1,item_data[1])
            item.setStatusTip(1,item_data[1])
            item.setToolTip(2,item_data[2])
            item.setStatusTip(2,item_data[2])
            
            for c in range(1,ncam):
                images=[imList[c][0][k], imList[c][1][k]]
                ex=[imEx[c][0][k], imEx[c][1][k]]
                data[1].append(images)
                data[2].append(ex)
                item_data=[str(c+1)]+images #['',str(c+1)]+images
                if not ex[0]: 
                    FlagWarn=True
                    item_data[1]=item_data[1]+' (!)' if item_data[1] else '(!)'
                if not ex[1]: 
                    FlagWarn=True
                    item_data[2]=item_data[2]+' (!)' if item_data[2] else '(!)'
                if c>item.childCount()-1:
                    item2=QTreeWidgetItem(item,item_data)
                    item2.setTextAlignment(0,Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter) 
                else:
                    item2=item.child(c)
                    [item2.setText(k,t) for k,t in enumerate(item_data)]
                item.setToolTip(1,item_data[1])
                item.setStatusTip(1,item_data[1])
                item.setToolTip(2,item_data[2])
                item.setStatusTip(2,item_data[2])
                [item.takeChild(k) for k in range(item.childCount()-1,ncam-1,-1)]

            if FlagWarn:
                data[0]=False
                item.setIcon(0,self.icon_warning)
                item.setToolTip(0,'Files (!) missing')
                item.setStatusTip(0,'Files (!) missing')
                self.warns.append(k)
            item.setData(0,Qt.ItemDataRole.UserRole,data)
            #self.signals.createdItem.emit()
        return items

class SingleImageTree(AsynPaIRSTree):

    def __init__(self, parent: QWidget=None,listDim=2,listDepth=1):
        super().__init__(parent,listDim,listDepth)

        columns=['',"filename"]
        self.setColumnCount(len(columns))
        self.setHeaderLabels(columns)
        header=self.header()
        self.headerItem().setTextAlignment(0,Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter) 
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.setUniformRowHeights(True)
        self.setStyleSheet(f"QTreeView::item {{ height: {self.default_row_height} px; }}")

        self.c=None #cam
        self.f=None #frame
        self.parentImTree=None
        self.ncam=1

        self.imList=create_empty_list_of_dimension(1)
        self.imEx=create_empty_list_of_dimension(1)

        expand_level(self.itemList,level=0,target_length=2)
        self.itemList[0]=self.imList
        self.itemList[1]=self.imEx

        self.type=self.PaIRSTreeTypes().single

    def indexSelection(self):
        item=self.currentItem()
        if item:
            FlagBottomLevel=bool(item.parent())
            parent_item=item.parent() if FlagBottomLevel else item
            img=self.indexOfTopLevelItem(parent_item)+1
        else:
            img=0
        cam=self.c+1
        frame=self.f+1
        return img, cam, frame
    
    def spinSelection(self,selection):
        if not selection:
            self.clearSelection()
            #self.setCurrentItem(None)
            return
        r,c,f=[i-1 for i in selection][:]
        if r<0: 
            self.clearSelection()
            #self.setCurrentItem(None)
            self.signals.updateTree.emit()
            return
        parent_item = self.topLevelItem(r)
        if parent_item:
            if c==0: item=parent_item
            else: item=parent_item.child(c-1)
            self.indexFromItem(item)
            self.setCurrentItem(item, f+1)

    def createItems(self,kin=None,kfin=None):
        imList=self.imList
        imEx=self.imEx

        if kin is None: kin=0
        if kfin is None: kfin=min([self.batch_size-1,len(imList[0][0])])
        nimg=kfin-kin+1
       
        self.warns=[]
        items=[None]*nimg
        j=-1
        for k in range(kin,kfin+1):
            j+=1
            FlagWarn=False
            
            image=imList[k]
            ex=imEx[k]
            item_data=['',image]
            if not ex: 
                FlagWarn=True
            item=QTreeWidgetItem(None,item_data)
            item.setTextAlignment(0,Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter) 
            items[j]=item
            item.setToolTip(1,item_data[1])
            item.setStatusTip(1,item_data[1])
            
            if FlagWarn:
                item.setIcon(0,self.icon_warning)
                item.setToolTip(0,'File missing')
                item.setStatusTip(0,'File missing')
                self.warns.append(k)
            data=[not FlagWarn,image,ex]
            item.setData(0,Qt.ItemDataRole.UserRole,data)
        return items
    
    def sortLists(self, reverse=False):
        zipped_lists=sorted(zip(self.imList, self.imEx), key=lambda x: x[0], reverse=reverse)
        sorted_imList, sorted_imEx=zip(*zipped_lists)
        for k in range(self.nimg):
            self.imList[k]=sorted_imList[k]
            self.imEx[k]=sorted_imEx[k]
        self.setLists()
    
    def importLists(self,filenames):
        def createItems():
            items=[None]*len(filenames)
            for k,filename in enumerate(filenames):
                FlagWarn=False
                
                image=os.path.basename(filename)
                ex=os.path.exists(self.path+image)
                self.nimg+=1
                item_data=['',image]
                if not ex: 
                    FlagWarn=True
                item=QTreeWidgetItem(None,item_data)
                item.setTextAlignment(0,Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter) 
                
                if FlagWarn:
                    item.setIcon(0,self.icon_warning)
                    item.setToolTip(0,'File missing')
                    item.setStatusTip(0,'File missing')
                data=[FlagWarn,image,ex]
                item.setData(0,Qt.ItemDataRole.UserRole,data)

                self.imList.append(image)
                self.imEx.append(ex)
                items[k]=item
            return items

        items=createItems()
        self.importItems(items) 

class ImageTreeWidget(QWidget):
    class ImageTreeWidget_signals(QObject):
        selection=Signal()
        pass
        
    buttons={
        'discard_changes':  ['Discard changes','Escape','redx'],
        'confirm_changes':  ['Confirm changes','Ctrl+Return','greenv'],
        'up'       :        ['Move to the top of the list','Ctrl+Up'],
        'down'     :        ['Move to the bottom of the list','Ctrl+Down'],
        'scan_list':        ['Re-scan current list to check for missing files','F5'],
        '|scan':[],
        'warning':          ['Check missing files','Ctrl+W'],
        'cut_warnings':     ['Cut all items with missing files','Alt+X'],
        '|warning': [],
        'edit_list':        ['Edit the list','F2'],
        '-1': [],
        'read_list':        ['Read image list file from the current folder','Ctrl+T'],
        'write_list':       ['Write current image list to folder','Ctrl+S'],
        '|read_list': [],
        'read':             ['Read image files from the current folder','Ctrl+R'],
        '|read': [],
        'sort':             ['Sort items in alphabetical order','Ctrl+Q'],
        'sort_reversed':    ['Sort items in alphabetical reversed order','Ctrl+Alt+Q'],
        '|sort': [],
        'wrap_items':       ['Collapse selected items','Shift+Space'],
        'unwrap_items':     ['Expand selected items','Space'],
        '|wrap': [],
        'copy':             ['Copy selected items from the list','Ctrl+C'],
        'cut':              ['Cut selected items from the list','Ctrl+X'],
        'paste_below':      ['Paste below the current item','Ctrl+V'],
        'paste_above':      ['Paste above the current item','Ctrl+Shift+V'],
        '|copy': [],
        'clean':            ['Clean the whole list']
        }
    icons_names=list(buttons)
    excludedFromContextMenu=('scan_list','warning','cut_warnings','edit_list','confirm_changes','discard_changes')

    main_layout_spacing=3
    
    spin_min_width=40
    spin_height=24
    spin_spacer_width=15
    spin_spacing=5

    label_spacing=5
    button_spacing=5
    button_size=20
    
    def __init__(self,parent=None,FlagSpinButtons=True):
        super().__init__(parent)
        if __name__ == "__main__":
            iconW = QIcon()
            iconW.addFile(u""+ icons_path +"input_logo.png", QSize(), QIcon.Normal, QIcon.Off)
            self.setWindowTitle('Image tree widget')
            self.setWindowIcon(iconW)

        self.name='Image set'
        self.signals=self.ImageTreeWidget_signals()
        self.FlagSpinButtons=FlagSpinButtons
        self.FlagCam=True
        self.FlagInGui=False

        font=self.font()
        font.setItalic(True)
        self.pixmap_edit=QPixmap(icons_path+'editing.png')

        self.main_layout=QVBoxLayout(self)
        self.main_layout.setContentsMargins(0,self.main_layout_spacing,0,self.main_layout_spacing)
        self.main_layout.setSpacing(self.main_layout_spacing)

        self.setLayout(self.main_layout)

        self.w_spin=QWidget()
        self.spin_layout = QHBoxLayout()
        self.spin_layout.setContentsMargins(0,0,0,0)
        self.spin_layout.setSpacing(self.spin_spacing)
        self.w_spin.setLayout(self.spin_layout)
        
        self.spin_layout.addItem(QSpacerItem(0, self.spin_height, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        self.label_img = QLabel('#:',font=font)
        self.spin_layout.addWidget(self.label_img)
        self.spin_img = MyQSpin(self)
        self.spin_img.setObjectName('spin_img')
        self.spin_img.setMinimumSize(self.spin_min_width,self.spin_height)
        self.spin_img.setMaximumHeight(self.spin_height)
        self.spin_img.setMinimum(0)
        self.spin_layout.addWidget(self.spin_img)
        self.label_max_img = QLabel('/0',font=font) 
        self.label_max_img.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.spin_layout.addWidget(self.label_max_img)
        self.spin_layout.addItem(QSpacerItem(self.spin_spacer_width, self.spin_height, QSizePolicy.Minimum, QSizePolicy.Minimum))

        self.label_frame = QLabel('frame:',font=font)
        self.spin_layout.addWidget(self.label_frame)
        self.spin_frame = MyQSpin(self)
        self.spin_frame.setObjectName('spin_frame')
        self.spin_frame.setMinimumSize(self.spin_min_width,self.spin_height)
        self.spin_frame.setMaximumHeight(self.spin_height)
        self.spin_frame.setMinimum(1)
        self.spin_frame.setMaximum(2)
        self.spin_layout.addWidget(self.spin_frame)
        self.spin_layout.addItem(QSpacerItem(self.spin_spacer_width, self.spin_height, QSizePolicy.Minimum, QSizePolicy.Minimum))

        self.label_cam = QLabel('cam:',font=font)
        self.spin_layout.addWidget(self.label_cam)
        self.spin_cam = MyQSpin(self)
        self.spin_cam.setObjectName('spin_cam')
        self.spin_cam.setMinimumSize(self.spin_min_width,self.spin_height)
        self.spin_cam.setMaximumHeight(self.spin_height)
        self.spin_cam.setMinimum(1)
        self.spin_layout.addWidget(self.spin_cam)
        self.label_max_cam = QLabel('/',font=font) 
        self.label_max_cam.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.spin_layout.addWidget(self.label_max_cam)
        self.spin_ncam = MyQSpin(self)
        self.spin_ncam.setObjectName('spin_ncam')
        self.spin_ncam.setMinimumSize(self.spin_height,self.spin_height)
        self.spin_ncam.setMaximumHeight(self.spin_height)
        self.spin_ncam.setMinimum(1)
        self.spin_ncam.setMaximum(99)
        self.spin_ncam.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons) 
        self.spin_ncam.setToolTip('Number of cameras')
        self.spin_ncam.setStatusTip('Number of cameras')
        self.spin_layout.addWidget(self.spin_ncam)

        self.spinSetup()

        self.w_button=QWidget(self)
        self.button_layout = QHBoxLayout()
        self.button_layout.setContentsMargins(0,0,0,0)
        self.button_layout.setSpacing(self.button_spacing)
        self.w_button.setLayout(self.button_layout)

        self.label_updating_import=QLabel('')
        self.label_updating_import.setFixedSize(self.button_size,self.button_size)
        self.updating_import_gif = QMovie(u""+ icons_path +"updating_import.gif")
        self.updating_import_gif.setScaledSize(self.label_updating_import.size())
        #self.ui.label_updating_import.setScaledContents(True)     
        self.updating_import_gif.start()
        self.label_updating_import.setMovie(self.updating_import_gif)
        self.label_updating_import.setVisible(False)
        self.button_layout.addWidget(self.label_updating_import)

        self.icon_label=QLabel('')
        self.icon_label.setFixedSize(self.button_size,self.button_size)
        self.icon_label.setScaledContents(True)
        self.icon_label.setPixmap(self.pixmap_edit)

        self.label = QLabel(self.name,font=font)
        self.label.setMinimumHeight(self.button_size)
        self.button_layout.addWidget(self.icon_label,alignment=Qt.AlignmentFlag.AlignLeft)
        self.button_layout.addWidget(self.label, alignment=Qt.AlignmentFlag.AlignLeft)

        self.button_layout.addItem(QSpacerItem(self.label_spacing, self.button_size, QSizePolicy.Minimum, QSizePolicy.Minimum))
        
        bs=self.button_size
        self.bShortCuts={}
        for icon_name in self.icons_names:
            if '-' in icon_name: 
                self.button_layout.addItem(QSpacerItem(bs, bs, QSizePolicy.Expanding, QSizePolicy.Minimum))
            elif '|' in icon_name:
                separator = QFrame()
                separator.setFrameShape(QFrame.VLine)
                separator.setFrameShadow(QFrame.Sunken) 
                setattr(self,'sep_'+icon_name[1:],separator)
                self.button_layout.addWidget(separator)
            else:
                b = QToolButton(self)
                b.setObjectName('button_'+icon_name)
                if len(self.buttons[icon_name])>2:
                    icon_file=icons_path+self.buttons[icon_name][2]+'.png'
                else:
                    icon_file=icons_path+icon_name+'.png'
                b.setIcon(QIcon(icon_file))
                b.setFixedSize(bs, bs)  # Impostare la dimensione quadrata
                b.setIconSize(QSize(bs-4,bs-4))
                tip=self.buttons[icon_name][0]
                if len(self.buttons[icon_name])>1:
                    if self.buttons[icon_name][1]:
                        bshortcut=QShortcut(QCoreApplication.translate("Image Tree",self.buttons[icon_name][1], None),self)
                        def buttonClick(b:QToolButton):
                            if b.isVisible() and b.isEnabled() and self.imTree.hasFocus(): b.click()
                        #bshortcut.activated.connect(lambda but=b:buttonClick(but))
                        tip+=' ('+bshortcut.key().toString(QKeySequence.NativeText)+')'
                        self.bShortCuts[bshortcut.key()[0]]=lambda but=b:buttonClick(but)
                b.setToolTip(tip)
                b.setStatusTip(tip)
                setattr(self,'button_'+icon_name,b)
                if hasattr(self,'button_'+icon_name+'_action'):
                    b.clicked.connect(getattr(self,'button_'+icon_name+'_action'))
                if icon_name=='discard_changes':
                    self.spin_layout.insertWidget(0,b)
                elif icon_name=='confirm_changes':
                    self.spin_layout.insertWidget(1,b)
                elif icon_name=='up':
                    self.spin_layout.insertWidget(3,b)
                elif icon_name=='down': 
                    self.spin_layout.insertWidget(4,b)
                else:
                    self.button_layout.addWidget(b)
        
        self.infoLabel = QLabel('',self)
        self.infoLabel.setFixedWidth(self.spin_height-8)
        self.infoLabel.setFixedHeight(self.spin_height-8)
        self.infoLabel.setScaledContents(True)
        self.progressBar = QProgressBar(self)
        self.progressBar.setFixedWidth(self.spin_height*3)
        self.progressBar.setFixedHeight(self.spin_height-8)
        self.spin_layout.insertWidget(2,self.progressBar)
        self.spin_layout.insertWidget(2,self.infoLabel)

        self.tree_layout=QHBoxLayout()
        self.tree_layout.setContentsMargins(0,0,0,0)
        self.tree_layout.setSpacing(0)
        
        self.imageNumbTree=ImageNumberTree()
        self.imageNumbTree.setVisible(True)
        self.imageNumbTree.setFrameShape(QFrame.NoFrame) 
        
        self.imTrees=[GlobalImageTree()]
        self.setAsynImTree(self.imTrees[0])
        self.imTrees[0].setObjectName('GlobalImageTree')
        self.imTrees[0].setFrameShape(QFrame.NoFrame) 
        self.imTree=self.imTrees[0]
        self.imList_old=[[[]]]
        self.imEx_old=[[[]]]
        self.tree_layout.addWidget(self.imageNumbTree)
        self.tree_layout.addWidget(self.imTree)
        #self.enableParent=lambda:None
        #self.disableParent=lambda:None
        
        self.button_edit_list:QPushButton
        self.button_edit_list.setCheckable(True)
        self.button_edit_list.setChecked(False)
        self.indTree=0
        self.treeSetup()
        
        self.main_layout.addWidget(self.w_spin)
        self.main_layout.addWidget(self.w_button)
        self.main_layout.addLayout(self.tree_layout)
        self.main_layout.addItem(QSpacerItem(0,0,QSizePolicy.Policy.Minimum,QSizePolicy.Policy.Expanding))

        if __name__ == "__main__":
            self.button_setList=QPushButton('Reset list (debug)')
            def resetList():
                imp,iml,ime=imSet.genListsFromIndex(kc,i,npairs,step,ncam)
                self.setLists(imp,iml,ime)
            self.button_setList.clicked.connect(resetList)
            self.button_setList.setMaximumHeight(30)
            self.setList_layout = QHBoxLayout()
            self.setList_layout.addWidget(self.button_setList)
            self.setList_layout.addItem(QSpacerItem(0, self.spin_height, QSizePolicy.Expanding, QSizePolicy.Minimum))
            self.main_layout.insertLayout(0,self.setList_layout)
            stretches=[0,0,0,1,0]
        else:
            stretches=[0,0,1,0]
        for k,s in enumerate(stretches):
            self.main_layout.setStretch(k,s)

        #self.nullList()
        self.w_spin.setVisible(self.FlagSpinButtons)
        self.w_button.setVisible(self.FlagSpinButtons)

        self.FlagAlreadyDisabled=False
        self.FlagEnabled=[]
        self.disabledChildren=[]

        self.setWidgetTabOrder()
        self.imTree.setVisible(True)
        self.imTree.keyPressEvent=lambda e: self.treeKeyPressEvent(e)
        self.imTree.installEventFilter(self)

        self.FlagSettingPar=None

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.ShortcutOverride:
            event.accept()
            return True
        return super().eventFilter(obj, event)  
    
    def treeKeyPressEvent(self,event):
        #pri.Callback.green(f"Pressed key sequence: {QKeySequence(Qt.KeyboardModifier(event.modifiers()) | Qt.Key(event.key())).toString()}")
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
                        return True    # Impedisce al widget di ricevere l'evento      
   
    def setAsynImTree(self,imTree: AsynPaIRSTree):
        imTree.setNumTree(self.imageNumbTree)
        imTree.disableButtons=self.disableButtons
        imTree.progressBar=self.progressBar
        imTree.infoLabel=self.infoLabel
        imTree.signals.copyCutItems.connect(self.copy_cut_action_future)
        imTree.signals.pastedItems.connect(self.button_paste_above_below_action_future)

    def nullList(self):
        nimg=0
        imList0=[[['' for _ in range(nimg)] for _ in range(2)] for _ in range(self.imTree.ncam)]
        imEx0=[[[False for _ in range(nimg)] for _ in range(2)] for _ in range(self.imTree.ncam)]
        self.setLists(self.imTree.path,imList0,imEx0,FlagAsync=False)
        self.imTree.signals.updateLists.emit()

    def disableButtons(self,Flag=True):
        self.progressBar.setVisible(Flag)
        #self.progressBar.setEnabled(Flag) #commenta se self.disableTab(Flag) è commentato
        self.infoLabel.setPixmap(QPixmap())
        self.infoLabel.setVisible(Flag)
        #self.infoLabel.setEnabled(Flag) #commenta se self.disableTab(Flag) è commentato
        #self.disableTab(Flag)
        #return
        self.w_button.setEnabled(not Flag)
        for c in self.w_spin.findChildren(QWidget):
            c:QWidget
            c.setEnabled(not Flag)
        self.updateSpins()
        self.setButtonLayout(True)
        self.progressBar.setEnabled(Flag)  #commenta se self.disableTab(Flag) è decommentato
        self.infoLabel.setEnabled(Flag)    #commenta se self.disableTab(Flag) è decommentato

    def disableTab(self,Flag=True):
        #evita TABpar.FlagSettingPar=Flag così che sai dove FlagSettingPar è settato True o False
        if Flag:
            self.FlagSettingPar=TABpar.FlagSettingPar
            TABpar.FlagSettingPar=True
        else: 
            if self.FlagSettingPar is not None:
                TABpar.FlagSettingPar=self.FlagSettingPar
        for imTree in self.imTrees:
            imTree.FlagSettingPar=Flag
        self.label_updating_import.setVisible(Flag) 
        return
        
    def treeSetup(self):
        self.imTree.itemSelectionChanged.connect(self.setButtonLayout)
        #self.imTree.signals.updateLists.connect(self.setButtonLayout)
        self.imTree.contextMenuEvent=lambda e: self.treeContextMenuEvent(self.imTree,e)
        self.imTree.keyPressEvent=lambda e: self.treeKeyPressEvent(e)
        self.imTree.installEventFilter(self)
        self.imTree.signals.updateTree.connect(self.updateSpins)
        self.imTree.signals.updateTree.connect(self.resizeHeader)
        self.imTree.signals.updateTree.connect(self.setButtonLayout)
        return_action=lambda: self.imTree.setFocus()
        self.spin_img.addfuncreturn['move2Tree']=return_action
        self.spin_cam.addfuncreturn['move2Tree']=return_action
        self.spin_frame.addfuncreturn['move2Tree']=return_action
        
    def spinSetup(self):
        self.spin_img.setup()
        self.spin_cam.setup()
        self.spin_ncam.setup()
        self.spin_frame.setup()
    
        self.spin_img.valueChanged.connect(lambda: self.spins_action(self.spin_img))
        self.spin_cam.valueChanged.connect(lambda: self.spins_action(self.spin_cam))
        self.spin_frame.valueChanged.connect(lambda: self.spins_action(self.spin_frame))
        self.spin_ncam.addfuncreturn['ncam']=self.spin_ncam_action
        self.spin_ncam.addfuncout['ncam']=self.spin_ncam_action

    def setButtonLayout(self,FlagPostponedSignal=False):
        self.setButtonLayout_List()
        self.setButtonLayout_Item(FlagPostponedSignal)

    def setButtonLayout_List(self):
        if not self.FlagSpinButtons: return
        #buttons changes when list changes occur
        FlagWarn=len(self.imTree.warns)>0
        FlagSingleTree=type(self.imTree)==SingleImageTree
        FlagItems=self.imTree.topLevelItemCount()>0
        FlagWrapUnWrap=not FlagSingleTree and self.imTree.ncam>1

        self.button_up.setVisible(FlagItems)
        self.button_down.setVisible(FlagItems)

        self.button_scan_list.setVisible(not FlagSingleTree)
        self.sep_scan.setVisible(not FlagSingleTree)
        self.button_warning.setVisible(FlagWarn)
        self.button_cut_warnings.setVisible(FlagWarn)
        self.sep_warning.setVisible(FlagWarn and not FlagSingleTree)

        self.button_confirm_changes.setVisible(FlagSingleTree)
        self.button_discard_changes.setVisible(FlagSingleTree)

        self.button_edit_list.setVisible(not FlagSingleTree)
        self.button_write_list.setVisible(not FlagSingleTree)
        self.button_write_list.setEnabled(FlagItems)
        self.button_read_list.setVisible(not FlagSingleTree)
        self.sep_read_list.setVisible(not FlagSingleTree)

        self.button_read.setVisible(FlagSingleTree)
        self.sep_read.setVisible(FlagSingleTree)

        self.button_wrap_items.setVisible(FlagWrapUnWrap)
        self.button_unwrap_items.setVisible(FlagWrapUnWrap)
        self.sep_wrap.setVisible(FlagWrapUnWrap)
        self.button_sort.setEnabled(FlagItems)
        self.button_sort_reversed.setEnabled(FlagItems)

        self.button_sort.setVisible(FlagSingleTree)
        self.button_sort_reversed.setVisible(FlagSingleTree)
        self.sep_sort.setVisible(FlagSingleTree)

        self.sep_copy.setVisible(not FlagSingleTree)
        self.button_clean.setVisible(not FlagSingleTree)
        self.button_clean.setEnabled(FlagItems)

    def setButtonLayout_Item(self,FlagPostponedSignal=False):
        if not self.FlagSpinButtons: return
        #buttons changes when item selection changes occur
        FlagSelected=len(self.imTree.selectedItems())>0
        FlagCuttedItems=len(self.imTree.cutted_itemList)>0
        self.button_wrap_items.setEnabled(FlagSelected)
        self.button_unwrap_items.setEnabled(FlagSelected)

        self.button_copy.setEnabled(FlagSelected)
        self.button_cut.setEnabled(FlagSelected)
        self.button_paste_above.setEnabled(FlagCuttedItems)
        self.button_paste_below.setEnabled(FlagCuttedItems)
        
        self.imTree.FlagSetting=True
        img,cam,frame=self.imTree.indexSelection()
        
        if FlagPostponedSignal:
            FlagSettingPar=TABpar.FlagSettingPar
            TABpar.FlagSettingPar=True
        FlagSignal=self.spin_img.value()!=img or self.spin_cam.value()!=cam or self.spin_frame.value()!=frame
        self.spin_img.setValue(img)
        self.spin_cam.setValue(cam)
        self.spin_frame.setValue(frame)
        self.spin_ncam.setValue(self.imTree.ncam)
        if FlagPostponedSignal: TABpar.FlagSettingPar=FlagSettingPar

        self.imTree.FlagSetting=False
        if FlagSignal and not TABpar.FlagSettingPar: self.signals.selection.emit()
        
    def setLists(self,path,imList:list,imEx:list,selection=[],FlagAsync=True,FlagOnlyPrepare=False):
        self.imTree.clearSelection()
        #self.imTree.setVisible(False)
        if self.button_edit_list.isChecked():
            indTree=self.indTree
            self.button_edit_list.setChecked(False)
            self.button_edit_list_action(FlagScan=False)
        else: indTree=0
        self.imTrees[0].path=path
        self.imTrees[0].ncam=ncam=len(imList)
        nimg=len(imList[0][0])
        self.imTrees[0].imList=copy.deepcopy(imList)
        self.imTrees[0].imEx=copy.deepcopy(imEx)
        self.imTrees[0].setImListEx()
        self.imTrees[0].disableTab=lambda flag: self.imTrees[0].setEnabled(not flag)
        countTree=1
        for c in range(ncam):
            for f in range(2):
                countTree+=1
                if len(self.imTrees)<countTree:
                    imTree=SingleImageTree(self)
                    imTree.setFrameShape(QFrame.NoFrame) 
                    self.imTrees.append(imTree)
                    self.tree_layout.addWidget(imTree)
                else:
                    imTree=self.imTrees[countTree-1]
                imTree.c=c
                imTree.f=f
                imTree.path=path
                imTree.ncam=ncam
                imTree.nimg=nimg
                imTree.parentImTree=self.imTrees[0]
                imTree.disableTab=lambda flag: imTree.setEnabled(not flag)
        [self.tree_layout.removeWidget(i) for i in self.imTrees[countTree:]]
                
        if not FlagOnlyPrepare: 
            self.imTrees[0].setLists(selection,FlagAsync)
        if indTree:
            self.button_edit_list.setChecked(True)            
        self.button_edit_list_action(FlagScan=False)
        
    def updateImList(self):
        #for imTree in self.imTrees:
        for k,imTree in enumerate(self.imTrees[1:]):
            imTree:SingleImageTree
            c=int(k/2)
            f=k-c*2
            if c>=self.imTrees[0].ncam: break
            imTree.imList=self.imTrees[0].imList[c][f]
            imTree.imEx=self.imTrees[0].imEx[c][f]
            imTree.itemList[0]=imTree.imList
            imTree.itemList[1]=imTree.imEx
            imTree.ncam=self.imTrees[0].ncam
            if self.initTree[k+1]: imTree.nimg=self.imTrees[0].nimg
        if self.initTree[self.indTree] and self.indTree:
            self.initTree[self.indTree]=False
            imTree=self.imTrees[self.indTree]
            imTree.setLists([self.spin_img.value(),1,1])

    def button_up_action(self):
        self.imTree.clearSelection()
        item=self.imTree.topLevelItem(0)
        self.imTree.setCurrentItem(item)
        self.imTree.setSelectedQuickly([item],True)
        self.imTree.scrollToTop()
            
    def button_down_action(self):
        self.imTree.clearSelection()
        item=self.imTree.topLevelItem(self.imTree.topLevelItemCount()-1)
        self.imTree.setCurrentItem(item)
        self.imTree.setSelectedQuickly([item],True)
        self.imTree.scrollToBottom()
        
    def button_scan_list_action(self):
        #self.imTree.setVisible(False)
        self.imTree.scanLists() 
        self.imTree.resetImNumber()
        #self.imTree.setVisible(True)
        self.imTree.signals.updateLists.emit()

    def button_cut_warnings_action(self):
        items=[self.imTree.topLevelItem(k) for k in self.imTree.warns]
        indexes=[self.imTree.indexOfTopLevelItem(i) for i in items]
        self.copy_cut_action(items,indexes,True)
        
    def button_warning_action(self):
        i=self.spin_img.value()-1
        if i in self.imTree.warns:
            k=self.imTree.warns.index(i)
            k=k+1 if k<len(self.imTree.warns)-1 else 0
        else: k=0
        item=self.imTree.topLevelItem(self.imTree.warns[k])
        self.imTree.setCurrentItem(item)
        self.imTree.setSelectedQuickly([item],True)
        
    def button_edit_list_action(self,FlagScan=True,FlagSignal=False):
        self.setUpdatesEnabled(False)
        indTree_old=self.indTree
        self.initTree=[True for _ in self.imTrees]
        if not self.button_edit_list.isChecked():
            self.indTree=0
            self.disableTab(False)
        else:
            if FlagScan: self.imTrees[0].scanLists(FlagChange=False)
            self.disableTab(True)
            self.imList_old=copy.deepcopy(self.imTree.imList)
            self.imEx_old=copy.deepcopy(self.imTree.imEx)
            c=self.spin_cam.value()-1
            f=self.spin_frame.value()-1
            self.indTree=1+c*2+f
            
        self.imTree=self.imTrees[self.indTree]
        self.setAsynImTree(self.imTree)
        self.updateImList()
        self.treeSetup()
        self.setButtonLayout(FlagPostponedSignal=FlagSignal)

        self.spins_action()
        if FlagSignal and not self.signalsBlocked(): 
            self.imTree.signals.updateLists.emit()
        if indTree_old!=self.indTree:
            self.imTrees[indTree_old].setVisible(False)
            self.imTree.setVisible(True)
        self.setUpdatesEnabled(True)
        
    def resizeHeader(self):
        self.imTree.resizeHeader()
        return

    def button_confirm_changes_action(self):
        nimg=max([imTree.nimg for imTree in self.imTrees[1:]])
        
        for k,imTree in enumerate(self.imTrees[1:]):
            imTree:SingleImageTree
            if imTree.nimg<nimg:
                imTree.imList.extend(['']*(nimg-imTree.nimg))
                imTree.imEx.extend([False]*(nimg-imTree.nimg))
            imTree.nimg=nimg
        self.imTrees[0].nimg=nimg

        self.imTrees[0].scanLists(FlagChange=False)
        self.imTrees[0].setLists()
        self.button_edit_list.setChecked(False)
        self.button_edit_list_action(FlagScan=False,FlagSignal=True)
        return
    
    def button_discard_changes_action(self):
        self.imTrees[0].imList=self.imList_old
        self.imTrees[0].imEx=self.imEx_old
        self.imTrees[0].setImListEx()
        self.imTrees[0].resetImNumber()
        self.imTrees[0].scanLists(FlagChange=True)
        self.button_edit_list.setChecked(False)
        self.button_edit_list_action(FlagScan=False,FlagSignal=True)
        return
    
    def spins_action(self,spin:QSpinBox=None):
        if self.imTree.FlagSetting: return
        self.updateSpins()
        r=self.spin_img.value()-1
        c=self.spin_cam.value()-1
        f=self.spin_frame.value()-1
        if not self.button_edit_list.isChecked(): #global tree
            self.label.setText(self.name)
            self.label.setStyleSheet('')
            self.icon_label.setVisible(False)
            self.imTree.spinSelection([r+1,c+1,f+1])
        else: #single tree
            self.label.setText(self.name + f' (cam: {c+1}, frame: {f+1})')
            self.label.setStyleSheet('QLabel{color:rgba(0, 116, 255, 1)}')
            self.icon_label.setVisible(True)
            indTree=1+c*2+f
            if indTree!=self.indTree:
                self.imTree.setVisible(False)
                self.indTree=indTree
                self.imTree=self.imTrees[self.indTree]
                self.setAsynImTree(self.imTree)
                self.updateImList()
                self.imTree.setVisible(True)
                self.treeSetup()
                self.updateSpins()
                r=self.spin_img.value()-1
            item = self.imTree.topLevelItem(r)
            self.imTree.indexFromItem(item)
            #self.imTree.clearSelection()
            self.imTree.setCurrentItem(item, 1)
        #if spin: spin.setFocus()

    def spin_ncam_action(self):
        ncam=self.spin_ncam.value()
        if self.imTree.ncam>ncam:
            del self.imTree.imList[ncam:]
            del self.imTree.imEx[ncam:]
        elif self.imTree.ncam<ncam:
            for c in range(self.imTree.ncam,ncam):
                self.imTree.imList[c:c]=[[['' for _ in range(self.imTree.nimg)] for _ in range(2)]]
                self.imTree.imEx[c:c]=[[[False for _ in range(self.imTree.nimg)] for _ in range(2)]]            
        else: return
        if self.imTree.ncam!=ncam:
            self.imTree.ncam=ncam
            self.imTree.setImListEx()
        self.imTree.setLists()

    def updateSpins(self):
        FlagSettingPar=TABpar.FlagSettingPar
        TABpar.FlagSettingPar=True
        self.spin_img.setMinimum(min([self.imTree.nimg,0]))
        self.spin_img.setMaximum(max([self.imTree.nimg,0]))
        self.spin_img.setToolTip(f'Current image. Number of images: {formatNumber(self.spin_img,self.spin_img.maximum())}')
        self.spin_img.setStatusTip(self.spin_img.toolTip())
        if self.spin_img.maximum(): self.label_max_img.setText('/'+self.spin_img.textFromValue(self.spin_img.maximum()))
        else: self.label_max_img.setText('')
        self.label_max_img.adjustSize()
        self.spin_img.setMinimumWidth(self.label_max_img.width()+self.spin_height)
        self.spin_img.setEnabled(self.imTree.nimg>1)

        self.spin_cam.setMinimum(min([self.imTree.ncam,1]))
        self.spin_cam.setMaximum(self.imTree.ncam)
        self.spin_cam.setToolTip(f'Current camera. Number of cameras: {formatNumber(self.spin_cam,self.spin_cam.maximum())}')
        self.spin_cam.setStatusTip(self.spin_cam.toolTip())
        FlagSingleTree=type(self.imTree)==SingleImageTree
        self.spin_cam.setEnabled(self.imTree.ncam>1 and (self.imTree.nimg>1 or FlagSingleTree))
        self.spin_ncam.setEnabled(not FlagSingleTree and self.FlagCam and not self.FlagInGui)
        
        self.spin_frame.setToolTip(f'Current frame. Number of frames: {self.spin_frame.maximum()}')
        self.spin_frame.setStatusTip(self.spin_frame.toolTip())
        self.spin_frame.setEnabled(self.imTree.nimg>1 or FlagSingleTree)
        TABpar.FlagSettingPar=FlagSettingPar

    def buttonActionWrapper(self,fun=lambda:None):
        FlagSettingPar=TABpar.FlagSettingPar
        TABpar.FlagSettingPar=True
        fun()
        TABpar.FlagSettingPar=FlagSettingPar
        self.imTree.signals.updateLists.emit()

    def button_wrap_unwrap_action(self,FlagWrap=True):
        #self.imTree.setVisible(False)
        selectedItems,indexes=self.imTree.selectedTopLevel()
        self.imTree.wrapUnWrapItems(selectedItems,indexes,FlagWrap)

    def button_wrap_items_action(self):
        #self.buttonActionWrapper(lambda: 
        self.button_wrap_unwrap_action(FlagWrap=True)
        #)

    def button_unwrap_items_action(self):
        #self.buttonActionWrapper(lambda: 
        self.button_wrap_unwrap_action(FlagWrap=False)
        #)
        
    def button_copy_cut_action(self, FlagCut=False):
        #self.imTree.setVisible(False)
        selectedItems,indexes=self.imTree.selectedTopLevel()
        self.copy_cut_action(selectedItems,indexes,FlagCut)

    def copy_cut_action(self,items,indexes,FlagCut):        
        self.imTree.copyCutItems(items,indexes,FlagCut)
        
    def copy_cut_action_future(self):
        FlagSignal=True
        self.updateSpins()
        self.setButtonLayout(FlagPostponedSignal=FlagSignal)

        #self.imTree.setVisible(True)
        self.imTree.setFocus()
        if not self.signalsBlocked(): self.imTree.signals.updateLists.emit()
    
    def button_copy_action(self):
        self.button_copy_cut_action(FlagCut=False)

    def button_cut_action(self):
        #self.buttonActionWrapper(lambda: 
        self.button_copy_cut_action(FlagCut=True)
        #)

    def button_paste_above_below_action(self,FlagAbove=True): 
        if not self.imTree.cutted_items: return
        #self.imTree.setVisible(False)
        
        self.FlagResizeHeader=self.imTree.topLevelItemCount()==0
        self.FlagAbove=FlagAbove
        selectedItems,indexes=self.imTree.selectedTopLevel()
        #self.imTree.clearSelection()
        if FlagAbove:
            if selectedItems: row=indexes[0]
            else: row=0
        else:
            if selectedItems: row=indexes[-1]+1
            else: row=self.imTree.topLevelItemCount()
        self.imTree.pasteItems(self.imTree.cutted_items,row,FlagAbove)
         
    def button_paste_above_below_action_future(self): 
        self.updateSpins()
        self.setButtonLayout()
        
        selectedItems,_=self.imTree.selectedTopLevel()
        #self.imTree.clearSelection()
        if self.FlagAbove:
            firstItemToScroll=selectedItems[0]
            lastItemToScroll=selectedItems[-1]
        else:
            firstItemToScroll=selectedItems[-1]
            lastItemToScroll=selectedItems[0] 

        self.imTree.scrollToItem(firstItemToScroll)
        self.imTree.scrollToItem(lastItemToScroll)

        kin=self.imTree.indexOfTopLevelItem(firstItemToScroll)
        firstItemToScroll=self.imageNumbTree.topLevelItem(kin)
        kfin=self.imTree.indexOfTopLevelItem(lastItemToScroll)
        lastItemToScroll=self.imageNumbTree.topLevelItem(kfin)
        self.imageNumbTree.scrollToItem(firstItemToScroll)
        self.imageNumbTree.scrollToItem(lastItemToScroll)

        #self.imageNumbTree.verticalScrollBar().setValue(self.imTree.verticalScrollBar().value())
        if self.FlagResizeHeader: self.resizeHeader()
        #self.imTree.setVisible(True)
        self.imTree.setFocus()
        self.imTree.signals.updateLists.emit()

    def button_paste_above_action(self): 
        #self.buttonActionWrapper(lambda: 
        self.button_paste_above_below_action(FlagAbove=True)
        #)

    def button_paste_below_action(self): 
        #self.buttonActionWrapper(lambda: 
        self.button_paste_above_below_action(FlagAbove=False)
        #)
        
    def clean_action(self):
        #self.imTree.setVisible(False)
        self.setUpdatesEnabled(False)
        for imTree in self.imTrees:
            imTree.clear() #clean_tree(imTree)
            imTree.cleanLists()
            imTree.itemList.append(deep_duplicate(imTree.itemList[0]))
        self.nullList()
        self.setUpdatesEnabled(True)
        #self.imTree.setVisible(True)

    def button_clean_action(self):
        #self.buttonActionWrapper(lambda:
        self.clean_action()
        #)

    def button_read_action(self):
        filenames, _ = QFileDialog.getOpenFileNames(self,\
            "Select image files from the current directory", filter=text_filter, dir=self.imTree.path,\
                options=optionNativeDialog)
        self.imTree:SingleImageTree
        if filenames:      
            self.FlagResizeHeader=self.imTree.topLevelItemCount()==0
            self.FlagAbove=False
            self.imTree.importLists(filenames)
    
    def button_sort_action(self):
        self.imTree:SingleImageTree
        self.imTree.sortLists(reverse=False)

    def button_sort_reversed_action(self):
        self.imTree:SingleImageTree
        self.imTree.sortLists(reverse=True)
     
    def button_read_list_action(self):
        filename, _ = QFileDialog.getOpenFileName(self,\
            "Select image list file", dir=self.imTree.path,\
                options=optionNativeDialog)
        if filename:
            imList,imEx=self.read_imFile(filename)
            if imList:
                #self.buttonActionWrapper(lambda:
                TABpar.FlagSettingPar=True
                self.setLists(self.imTree.path,imList,imEx)
                TABpar.FlagSettingPar=False
                #)

    def read_imFile(self,filename):
        path=self.imTree.path
        try:
            with open( filename, 'r') as file:
                lines = file.readlines()
                for i, line in enumerate(lines):
                    pairs = line.strip().split(';')
                    if len(pairs) < self.imTree.ncam:
                        raise ValueError(f"Invalid format in line {i + 1}:\n\n{line.strip()}\n\nEach line should contain at least {self.imTree.ncam} pairs of image filenames separated by a semicolon.")
                    if not i:
                        imList=[[['' for _ in range(len(lines))] for _ in range(2)] for _ in range(self.imTree.ncam)]
                        imEx=[[[False for _ in range(len(lines))] for _ in range(2)] for _ in range(self.imTree.ncam)]
                    for c in range(self.imTree.ncam):
                        pair=pairs[c]
                        items = pair.strip().split(',')
                        if len(items) != 2:
                            raise ValueError(f"Invalid format in line {i + 1}:\n\n{line.strip()}\n\nEach pair should contain exactly two image filenames separated by a comma.")
                        for f in range(2): 
                            imList[c][f][i]=items[f].strip() 
                            imEx[c][f][i]=os.path.exists(path+imList[c][f][i]) if imList[c][f][i] else False
        except FileNotFoundError:
            warningDialog(self,f"File '{filename}' not found at path '{path}'.")
            imList=imEx=[]  
        except ValueError as e:
            warningDialog(self,f"Error: {e}")
            imList=imEx=[]
        return imList, imEx
        
    def button_write_list_action(self):
        filename, _ = QFileDialog.getSaveFileName(self,"Select location and name of the image list file to save", 
                    dir=self.imTree.path, filter='*.txt',\
                    options=optionNativeDialog)
        if filename:
            if filename[-4:]!='.txt': filename+='.txt'  #per adattarlo al mac
            filename=myStandardRoot('{}'.format(str(filename)))
            self.write_imFile(filename,self.imTree.imList)
        
    def write_imFile(self,filename,imList):
        try:
            with open(filename, 'w') as file:
                for i in range(len(imList[0][0])):
                    row = '; '.join([f"{imList[j][0][i]}, {imList[j][1][i]}" for j in range(len(imList))]) + '\n'
                    file.write(row)
        except Exception as e:
            pri.Error.red(f"Error writing to file: {e}\n{traceback.format_exc()}\n")
            warningDialog(self,f"Error writing to file: {e}")
      
    def treeContextMenuEvent(self, tree:PaIRSTree, event):
        item=tree.currentItem()
        if not item: return
        menu=QMenu(tree)
        name=[]
        act=[]
        fun=[]
        for nb in self.icons_names:
            if '-' not in nb and '|' not in nb and nb not in self.excludedFromContextMenu:
                b:QPushButton=getattr(self,'button_'+nb)
                if b.isVisible() and b.isEnabled():
                    if hasattr(self,'button_'+nb+'_action'):
                        name.append(nb)
                        act.append(QAction(b.icon(),toPlainText(b.toolTip().split('.')[0]),tree))
                        menu.addAction(act[-1])
                        callback=getattr(self,'button_'+nb+'_action')
                        fun.append(callback)
            elif '|' in nb:
                if len(act): menu.addSeparator()

        if len(act):
            action = menu.exec(tree.mapToGlobal(event.pos()))
            for nb,a,f in zip(name,act,fun):
                if a==action: 
                    f()

    def setWidgetTabOrder(self):
        buttons=[getattr(self,'button_'+icon_name) if hasattr(self,'button_'+icon_name) else None for icon_name in self.icons_names]
        widgets=[self]+[self.button_setList if hasattr(self,'button_setList') else None]+buttons[:4]+[self.spin_img, self.spin_cam, self.spin_ncam, self.spin_frame]+buttons[4:]
        for i in range(len(widgets)-2):
            self.setTabOrder(widgets[i],widgets[i+1])
        
class CalibrationTree(PaIRSTree):

    def mousePressEvent(self, event: QMouseEvent):
        TABpar.FlagSettingPar=True
        self.cursor_pos=event.globalPosition().toPoint()
        super().mousePressEvent(event)
        return 

    def mouseReleaseEvent(self, event: QMouseEvent):
        TABpar.FlagSettingPar=False
        self.itemSelectionChanged.emit()
        super().mouseReleaseEvent(event)
        return
    
    def __init__(self, parent: QWidget=None,listDim=2,listDepth=1):
        super().__init__(parent,listDim,listDepth)

        columns=["#","filename"]
        self.setColumnCount(len(columns))
        self.setHeaderLabels(columns)
        header=self.header()
        self.headerItem().setTextAlignment(0,Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter) 
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.setStyleSheet(f"QTreeView::item {{ height: {self.default_row_height} px; }}")

        self.ncam=1
        self.calList=create_empty_list_of_dimension(1)
        self.calEx=create_empty_list_of_dimension(1)

        expand_level(self.itemList,level=0,target_length=2)
        self.itemList[0]=self.calList
        self.itemList[1]=self.calEx

        self.setVisible(True)

    def importLists(self,filenames):
        def createItems():
            items=[None]*len(filenames)
            for k,filename in enumerate(filenames):
                FlagWarn=False
                
                ex=os.path.exists(filename)
                self.nimg+=1
                item_data=[str(self.nimg),os.path.basename(filename) + f' ({os.path.dirname(filename)})']
                if not ex: 
                    FlagWarn=True
                item=QTreeWidgetItem(None,item_data)
                item.setTextAlignment(0,Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter) 
                
                if FlagWarn:
                    item.setIcon(0,self.icon_warning)
                    item.setToolTip(0,'File missing')
                    item.setStatusTip(0,'File missing')
                data=[FlagWarn,filename,ex]
                item.setData(0,Qt.ItemDataRole.UserRole,data)

                self.calList.append(filename)
                self.calEx.append(ex)
                items[k]=item
            return (items)

        items=createItems()
        self.insertItems2List(-1,items,False,NotImplementedError)

    def setLists(self,selection=[]):
        calList=self.calList
        calEx=self.calEx
        self.warns=[]

        pri.Time.blue(f'CalibrationTree: start setting list')
        self.nimg=nimg=len(calList)
        if self.nimg:
            while not calList[self.nimg-1]:
                calList.pop(self.nimg-1)
                calEx.pop(self.nimg-1)
                self.nimg-=1
                if self.nimg==0: break
            nimg=self.nimg
        self.FlagReset=True

        def createItems():
            items=[None]*nimg
            for k in range(nimg):
                FlagWarn=False
                
                filename=calList[k]
                ex=calEx[k]=os.path.exists(filename)
                item_data=[str(k+1),os.path.basename(filename) + f' ({os.path.dirname(filename)})']
                if not ex: 
                    FlagWarn=True
                item=QTreeWidgetItem(None,item_data)
                item.setTextAlignment(0,Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter) 
                items[k]=item
                item.setToolTip(1,item_data[1])
                item.setStatusTip(1,item_data[1])
                
                if FlagWarn:
                    item.setIcon(0,self.icon_warning)
                    item.setToolTip(0,'File missing')
                    item.setStatusTip(0,'File missing')
                    self.warns.append(k)
                data=[not FlagWarn,filename,ex]
                item.setData(0,Qt.ItemDataRole.UserRole,data)
            return (items)
        
        items=createItems()
        self.insertItems2List(-1,items,False,selection)
        pri.Time.blue(f'CalibrationTree: end setting list')
        return

class PaIRSTable(QTableWidget):
    cutted_itemList=[]
    cutted_items=[]
    deleted_itemList=[]
    deleted_items=[]
    margin_rect=10

    class ImageTable_signals(QObject):
        updateTree=Signal()
        updateLists=Signal()
        createdItems=Signal(int,list,bool,list)

    def __init__(self,  parent: QWidget=None, listDim=1, listDepth=0):
        super().__init__(parent=parent)
        self.listDim=listDim
        self.listDepth=listDepth
        self.signals=self.ImageTable_signals()

        self.setupRowBehaviour()
        
        self.icon_warning = QIcon()
        self.icon_warning.addFile(u""+ icons_path +"warn.png", QSize(), QIcon.Normal, QIcon.Off)
        self.dragged_items=self.dragged_indexes=None
        self.hovered_item=None
        self.setAutoScroll(True)
        self.verticalScrollBarVal=self.verticalScrollBar().value()
        self.verticalScrollBar().setStyleSheet("""
            QTreeWidget {
                margin-bottom: 0px;
                }
            QTreeWidget::item {
                margin-bottom: 0px;
                }
            QTreeView {
                margin-bottom: 0px;
                }
            QScrollBar:horizontal{
                height: 15px;
                margin: 3px 0px 3px 0px;
                border: 1px transparent #2A2929;
                border-radius: 4px;
                background-color:  transparent;    /* #2A2929; */
                }
            QScrollBar::handle:horizontal{
                background-color: rgba(180,180,180,180);         /* #605F5F; */
                min-width: 30px;
                border-radius: 4px;
                }
            QScrollBar:vertical{
                width: 15px;
                margin: 0px 3px 0px 3px;
                border: 1px transparent #2A2929;
                border-radius: 4px;
                background-color:  transparent;    /* #2A2929; */
                }
            QScrollBar::handle:vertical{
                background-color: rgba(180,180,180,180);         /* #605F5F; */
                min-height: 30px;
                border-radius: 4px;
                }
            QScrollBar::add-line{
                    border: none;
                    background: none;
                }

            QScrollBar::sub-line{
                    border: none;
                    background: none;
                }""")
        self.cursor_pos=self.cursor().pos()
        
        self.pen = QPen(qRgba(127,227,255,0.9))
        self.pen.setWidth(3)
        #style="background-color: rgba(173,216,230,0.1); color: rgba(128,128,128,0.25);"
        #self.setStyleSheet(f"QTreeWidget::item:selected {{{style}}}")
        #self.setStyleSheet(f"QTreeWidget::item:selected:active {{{style}}}")

        style = """
            QTreeWidget::item:selected:!active {
                background-color: rgba(0, 116, 255, 0.4);
            }
            QTreeWidget::item:selected:active {
                background-color: rgba(0, 116, 255, 0.8);
            }
            """
        self.setStyleSheet(style)

        self.addfuncreturn={}
        #self.addfuncreturn={'expand': self.expandRow}
        self.FlagSetting=False
        self.FlagReset=False
        self.FlagCutted=False

        self.nimg=0        
        self.itemList=create_empty_list_of_dimension(self.listDim)
        self.warns=[]

        self.disableTab=lambda flag: None

    def setupRowBehaviour(self):                  
        self.setDragDropMode(QTableWidget.DragDropMode.InternalMove)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectItems)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropOverwriteMode(False)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSortingEnabled(False)
        
    def mousePressEvent(self, event: QMouseEvent):
        TABpar.FlagSettingPar=True
        self.itemUponPressing=self.currentItem()
        self.cursor_pos=event.globalPosition().toPoint()
        super().mousePressEvent(event)
        return 

    def mouseReleaseEvent(self, event: QMouseEvent):
        TABpar.FlagSettingPar=False
        itemUponReleasing=self.currentItem()
        if itemUponReleasing!=self.itemUponPressing:
            self.currentItemChanged.emit(itemUponReleasing,itemUponReleasing)
        super().mouseReleaseEvent(event)
        return
    
    def dragEnterEvent(self, event):
        TABpar.FlagSettingPar=True
        self.dragged_items = self.selectedItems()
        rows=[i.row() for i in self.dragged_items]
        self.setSelectedQuickly(rows,True)
        self.dragged_items = self.selectedItems()
        self.dragged_indexes = self.selectedIndexes()
        self.verticalScrollBarVal=self.verticalScrollBar().value()
        super().dragEnterEvent(event)
        
    def dragMoveEvent(self, event):
        pos = event.position().toPoint()
        self.hovered_item = item = self.itemAt(pos)
        super().dragMoveEvent(event)  # Allow the event to proceed for row moves

    #@log_qpainter_usage
    def paintEvent(self, event):
        super().paintEvent(event)
        self.paintLines()

    def paintLines(self):
        item=self.hovered_item
        if item and self.dragged_items:
            if self.dragged_items!='externalItem':
                self.drop_indicator_pos = self.dropIndicatorPosition()
                if self.drop_indicator_pos == QTableWidget.DropIndicatorPosition.AboveItem:
                    item_rect = self.visualRowRect(item)
                    self.drawDropIndicatorLine(item_rect.top(),item_rect.x(),item_rect.height(),item_rect.width(),-1)
                elif self.drop_indicator_pos == QTableWidget.DropIndicatorPosition.BelowItem:
                    item_rect = self.visualRowRect(item)
                    self.drawDropIndicatorLine(item_rect.bottom(),item_rect.x(),item_rect.height(),item_rect.width(),+1)
            else: #below
                item_rect = self.visualRowRect(item)
                self.drawDropIndicatorLine(item_rect.bottom(),item_rect.x(),item_rect.height(),item_rect.width(),+1)

    def visualRowRect(self, row: int):
        if type(row)==QTableWidgetItem:
            row=row.row()
        rect = QRect()
        for column in range(self.columnCount()):
            item = self.item(row, column)
            if item:
                item_rect = self.visualItemRect(item)
                if column == 0:  # Se è la prima colonna, aggiungi il margine
                    item_rect.adjust(self.margin_rect, 0, 0, 0)
                rect = rect.united(item_rect)
        return rect
    
    def drawDropIndicatorLine(self, y_pos,x_pos,dy,dx,sign=1):
        painter = QPainter(self.viewport())
        painter.setPen(self.pen)
        painter.drawLine(0, y_pos, self.viewport().width(), y_pos)

        # Calcola la posizione della freccia
        s=5*sign
        for x_pos_2 in (x_pos,x_pos+dx-2*abs(s)):
            y_pos_2=y_pos-5*sign
            arrow_top = QPoint(x_pos_2, y_pos_2 - 3*s)
            arrow_bottom = QPoint(x_pos_2, y_pos_2)
            arrow_left = QPoint(x_pos_2 - s, y_pos_2-s)
            arrow_right = QPoint(x_pos_2 + s, y_pos_2-s)

            # Disegna la freccia
            painter.drawLine(arrow_top, arrow_bottom)
            #painter.drawLine(arrow_left, arrow_right)
            painter.drawLine(arrow_bottom, arrow_right)
            painter.drawLine(arrow_bottom, arrow_left)
        painter.end()
   
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return,Qt.Key.Key_Enter):
            for f in self.addfuncreturn:
                self.addfuncreturn[f]()
        super().keyPressEvent(event)
        current_item = self.currentItem()
        if not current_item or not self.isPersistentEditorOpen(current_item):
            self.setFocus()

    '''
    def mimeData(self, items):
        mimeData = QMimeData()
        encodedData = QByteArray()
        stream = QDataStream(encodedData, QIODevice.WriteOnly)

        for item in items:
            row = self.row(item)
            column = self.column(item)
            text = item.text()
            stream.writeInt32(row)
            stream.writeInt32(column)
            stream.writeQString(text)

        mimeData.setData("application/x-qabstractitemmodeldatalist", encodedData)
        return mimeData

    def dropMimeData(self, row, column, data, action):
        if action == Qt.MoveAction:
            encodedData = data.data("application/x-qabstractitemmodeldatalist")
            stream = QDataStream(encodedData, QIODevice.ReadOnly)
            newItems = []

            while not stream.atEnd():
                row = stream.readInt32()
                column = stream.readInt32()
                text = stream.readQString()
                newItems.append((row, column, text))

            for row, column, text in newItems:
                self.setItem(row, column, QTableWidgetItem(text))

            return True
        return False
    '''

    def dropEvent(self, event):
        drop_indicator_position = self.dropIndicatorPosition()

        if  drop_indicator_position == QTableWidget.DropIndicatorPosition.OnItem or self.hovered_item is None:
            target_row_index=None
            self.verticalScrollBar().setValue(self.verticalScrollBarVal)
            QCursor.setPos(self.cursor_pos)
            event.ignore()  # Ignore the event if it's not a row move or a drop on an item
            FlagUpdateList=False
        else:
            target_row = self.hovered_item.row()
            #pri.Coding.yellow(f'Hovered item: {self.item(target_row,0).text()}')
            source_rows=[]
            for i in self.dragged_items:
                if i.row() not in source_rows:
                    source_rows.append(i.row())
            
            if self.drop_indicator_pos == QTableWidget.DropIndicatorPosition.BelowItem:
                target_row+=1
            selectedItems,target_row_new=self.move_rows_to(source_rows,target_row)
            self.dropLists(selectedItems,source_rows)  
            for r in range(len(source_rows)):
                for c in range(self.columnCount()-1,-1,-1):
                    i=self.item(r+target_row_new,c)
                    i:QTableWidgetItem
                    """
                    if not c: 
                        pri.Coding.yellow(f'row={i.row()} {i.text()}')
                        pri.Coding.red(f'{self.itemList[0][r+target_row_new]}')
                    """
                    i.setSelected(True) 

            event.accept()
            #for i in selectedItems: i.setSelected(True)

            
            FlagUpdateList=True 
                 
        self.dragged_items=self.dragged_indexes=None
        self.repaint()  
        TABpar.FlagSettingPar=False  
        self.itemSelectionChanged.emit() 
        if FlagUpdateList: self.signals.updateLists.emit()
    
    def move_rows_to(self, rows, target_row):
        sorted_rows = sorted(rows)
        # Salvataggio dei dati delle righe da spostare
        rows_data = []
        for row in sorted_rows:
            row_data = [self.item(row, column).text() for column in range(self.columnCount())]
            rows_data.append(row_data)

        # Rimozione delle righe dalla loro posizione originale
        diff=0
        for row in reversed(sorted_rows):
            self.removeRow(row)
            if row<target_row: diff+=1
        target_row-=diff

        selectedItems=[]
        # Inserimento delle righe nella posizione target
        for row, data in enumerate(rows_data):
            target_row_index = target_row + row
            self.insertRow(target_row_index)
            for column, text in enumerate(data):
                item=QTableWidgetItem(text)
                self.setItem(target_row_index, column,item)
                selectedItems.append(item)
        return selectedItems, target_row

    def setSelectedQuickly(self, rows, Flag):
        self.clearSelection()
        selectionFlag=QItemSelectionModel.SelectionFlag.Select if Flag else QItemSelectionModel.SelectionFlag.Deselect
        selection_model = self.selectionModel()
        selection = QItemSelection()
        for row in rows:
            selection.merge(QItemSelection(self.model().index(row, 0), self.model().index(row, self.columnCount() - 1)), selectionFlag)
        selection_model.select(selection, QItemSelectionModel.SelectionFlag.ClearAndSelect )
        return

    def dropLists(self, items, indexes):
        if self.itemList:
            cutted_items=pop_at_depth(self.itemList,self.listDepth,indexes)
            insert_at_depth(self.itemList,self.listDepth,items[0].row(),cutted_items)
        #ind_fin=self.indexOfTopLevelItem(items[-1])
        return
    
    def cutLists(self, indexes, FlagDeleted=False):
        if FlagDeleted: type(self).deleted_itemList=pop_at_depth(self.itemList,self.listDepth,indexes)
        else: type(self).cutted_itemList=pop_at_depth(self.itemList,self.listDepth,indexes)
        if not FlagDeleted: self.FlagCutted=True
        self.nimg-=len(indexes)  
        return
    
    def deleteLists(self, indexes):
        self.cutLists(indexes,FlagDeleted=True)
        return

    def copyLists(self, indexes):
        type(self).cutted_itemList=copy_at_depth(self.itemList,self.listDepth,indexes)
        self.FlagCutted=False
        return

    def pasteLists(self, ind, FlagDeleted=False):
        pri.Time.magenta('pasteLists: start')
        if FlagDeleted: iList=type(self).deleted_itemList
        else: iList=type(self).cutted_itemList
        self.nimg+=measure_depth_length(iList,self.listDepth)
        insert_at_depth(self.itemList,self.listDepth,ind,iList)
        if self.FlagCutted:
            type(self).cutted_itemList=[]
            type(self).cutted_items=[]
            self.FlagCutted=False
        else:
            if FlagDeleted: type(self).deleted_itemList=deep_duplicate(iList)
            else: type(self).cutted_itemList=deep_duplicate(iList)
        pri.Time.magenta('pasteLists: end')
        return

    def cleanLists(self):
        self.itemList=create_empty_list_of_dimension(self.listDim)

class ImageTable(PaIRSTable):
    
    def __init__(self, parent: QWidget=None, listDim=2, listDepth=1):
        super().__init__(parent,listDim,listDepth)

        columns=["Image filename","Plane parameters","Info"]
        self.setColumnCount(len(columns))
        header = self.horizontalHeader()     
        self.setHorizontalHeaderLabels(columns)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        self.RowInfo=[]
        self.InfoLabel:QLabel=None
        self.DeleteButton:QPushButton=None
        self.addwid=[]
        self.addfuncreturn={}
        self.addfuncout={}

        self.setVisible(True)

    def keyPressEvent(self, event):
        super().keyPressEvent(event) 
        if event.key() in (Qt.Key.Key_Return,Qt.Key.Key_Enter):  #return
            for f in self.addfuncreturn:
                self.addfuncreturn[f]()

    def focusOutEvent(self, event):
        super().focusOutEvent(event) 
        for f in self.addfuncout:
            self.addfuncout[f]()

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

#*************************************************** TESTING
if __name__ == "__main__":
    if currentID==developerIDs['GP_Win_Office']:
        working_fold='C:/desk/PIV_Img/swirler_png/'
    elif currentID==developerIDs['GP_Mac_Laptop']:
        working_fold='/Users/gerardo/Desktop/PIV_Img/swirler_png/'
    else:
        working_fold=basefold
    
    pri.Coding.white('\n'+'*'*50+'\n')
    imSet=ImageSet()
    imSet.scanPath(working_fold)
    imSet.print()
    pri.Coding.white('\n'+'*'*50+'\n')
    
    kc=0
    i=198
    npairs=6000
    step=1
    ncam=2
    
    app = PaIRSApp(sys.argv)
    w=ImageTreeWidget(FlagSpinButtons=FlagSpinButtons_Debug)
    try:
        imagePath,imageList,imageEx=imSet.genListsFromIndex(kc,i,npairs,step,ncam)
        w.setLists(imagePath,imageList,imageEx,[10,ncam,1])
        w.write_imFile(working_fold+'example.txt',imageList)
        if npairs<100:
            pri.Coding.white(f'List "{imSet.pattern[kc]}", i={i}, npairs={npairs}, step={step}')
            for n in range(len(imageList[0][0])): 
                pri.Coding.white(f'{n:6d}:'+'\t'+imageList[0][0][n]+', '+imageList[0][1][n])
                for c in range(1,len(imageList)):
                    pri.Coding.white(f'{" "*7}'+'\t'+imageList[c][0][n]+', '+imageList[c][1][n])
    except:
        traceback.print_exc()
        w.nullList()
        pass

    w.resize(750,750)
    w.setVisible(True)

    '''
    w2=ImageTable()
    w2.resize(750,750)
    w2.setVisible(True)
    '''
    sys.exit(app.exec())

    quit()
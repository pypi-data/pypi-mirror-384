
from .PaIRS_pypacks import *
from .addwidgets_ps import *

Num_Prevs_Max=100
Num_Prevs_back_forw=10

FlagAsyncCallbacks=True
FlagSimulateError=False
globExecutor = concurrent.futures.ThreadPoolExecutor(max_workers=10)  

indParGlob=0
class TABpar:
    #indParGlob=0
    FlagSettingPar=False
    FlagInit=False

    def __init__(self,name=str(uuid.uuid4())[:8],surname=str(uuid.uuid4())[:8]): 
        self.uiFields=[f for f,_ in self.__dict__.items()]

        self.name=name
        self.surname=surname
        self.ind=[0,0,0,0,0]   #project, tree, item, subitem, do/undo
        self.tip='...'
        self.parentTab=None
        self.FlagNone=False
        self.flagRun=0      #0:not launched yet, 1:completed, -1:interrupted, -2:running
        self.link=[]
        
        self.parFields=[f for f,_ in self.__dict__.items() if f not in self.uiFields ]
        self.uncopied_fields=['tip']
        self.unchecked_fields=['name','surname','parentTab']+self.uncopied_fields
        
        self.OptionDone=1
        self.warningMessage=''

        self.fields=[f for f,_ in self.__dict__.items()]
        pass

    def setNone(self):
        for f in self.fields:
            setattr(self,f,None)

    def printPar(self,before='',after=''):
        before=after=''
        print(before+str(self.__dict__)+after)

    def duplicate(self):
        if hasattr(self,'Process') and hasattr(self,'Step'):
            newist=type(self)(Process=self.Process,Step=self.Step)
        else:
            newist=type(self)()
        for f in self.fields:
            if f in self.uncopied_fields: continue
            a=getattr(self,f)
            if  hasattr(a,'duplicate'): #type(a)==patternInfoList:
                setattr(newist,f,a.duplicate())
            else:
                setattr(newist,f,copy.deepcopy(a))
        return newist
    
    def copyfromdiz(self,diz:dict):
        for f,a in diz.items():
            if hasattr(a,'duplicate'):
                if hasattr(a,'isDifferentFrom') and hasattr(self,f): 
                    b=getattr(self,f)
                    flag=a.isDifferentFrom(b,FlagPrint=False)
                else: flag=True
                if flag: setattr(self,f,a.duplicate())
            else:
                setattr(self,f,copy.deepcopy(a))

    def copyfrom(self,newist,exceptions=None):
        if newist is None:
            self.FlagNone=True
        else:
            self.copyfromfields(newist,self.fields,exceptions)

    def copyfromfields(self,newist,fields=None,exceptions=None):
        """
        exceptions=[] --> no exceptions
        """
        newist:TABpar
        if exceptions is None:
            exceptions=self.uncopied_fields
        for f in fields:
            if f in exceptions: continue
            if not hasattr(self,f):
                pri.Error.red(f'copyfromdiz: field <{f}> is missing in {self.name} par structure!')
                continue
            if not hasattr(newist,f):
                pri.Error.red(f'copyfromdiz: field <{f}> is missing in {newist.name} par structure!')
                continue
            a=getattr(newist,f)
            if hasattr(a,'duplicate'): #type(a)==patternInfoList:
                if hasattr(a,'isDifferentFrom') and hasattr(self,f):
                    b=getattr(self,f)
                    flag=a.isDifferentFrom(b,FlagPrint=False)
                else: flag=True
                if flag: setattr(self,f,a.duplicate())
            else:
                setattr(self,f,copy.deepcopy(a))
    
    def isDifferentFrom(self,v,exceptions:list=[],fields:list=[],FlagStrictDiff=False,FlagPrint=True):
        if not FlagStrictDiff: 
            exceptions+=self.unchecked_fields
            exceptions=list(set(exceptions))
        if not fields:
            fields=self.fields
        else:
            [exceptions.remove(f) for f in fields if f in exceptions]

        Flag=False
        for f in fields:
            if f in exceptions: continue
            else:
                if not hasattr(self,f):
                    pri.Error.red(f'isDifferentFrom: field <{f}> is missing in {self.name} par structure!')
                    continue
                if not hasattr(v,f):
                    pri.Error.red(f'isDifferentFrom: field <{f}> is missing in {v.name} par structure!')
                    continue 
                a=getattr(self,f)
                b=getattr(v,f)
                if f=='Vect':
                    Flag=not all([np.array_equal(a[i],b[i]) for i in range(4)])
                    if Flag: 
                        break
                else:
                    if hasattr(a,'isDifferentFrom'): #in ('Pinfo','pinfo'):
                        Flag=a.isDifferentFrom(b,exceptions,FlagStrictDiff=FlagStrictDiff)
                        if Flag: break
                    else:
                        if a!=b:
                            Flag=True
                            break
        if FlagPrint:
            if Flag:  
                pri.TABparDiff.red(f'{self.name} is different in {f}:\t {b}   -->   {a}')
            else: 
                pri.TABparDiff.green(f'{self.name} is unchanged')
        return Flag
    
    def isEqualTo(self,v,exceptions=[],fields=[],FlagStrictDiff=False,FlagPrint=False):
        Flag=bool(not self.isDifferentFrom(v,exceptions,fields,FlagStrictDiff,FlagPrint))
        return Flag
    
    def printDifferences(self,v,exceptions=[],fields=[],FlagStrictDiff=False):
        if FlagStrictDiff: exceptions+=self.unchecked_fields
        if not fields:
            fields=self.fields
        else:
            [exceptions.remove(f) for f in fields if f in exceptions]
        printing=''
        df=[]
        for f in fields:
            if f in exceptions: continue
            if not hasattr(self,f):
                pri.Error.red(f'printDifferences: field <{f}> is missing in {self.name} par structure!')
                continue
            if not hasattr(v,f):
                pri.Error.red(f'printDifferences: field <{f}> is missing in {v.name} par structure!')
                continue 
            a=getattr(self,f)
            b=getattr(v,f)
            Flag=False
            if f=='Vect':
                Flag=not all([np.array_equal(a[i],b[i]) for i in range(4)])
            else:
                if hasattr(a,'isDifferentFrom'): #in ('Pinfo','pinfo'):
                    if hasattr(a,'fields'):
                        Flag=a.isDifferentFrom(b,[],a.fields,FlagStrictDiff,FlagPrint=False)
                        if Flag:
                            a.printDifferences(b,[],a.fields,FlagStrictDiff)
                    else:
                        Flag=a.isDifferentFrom(b,[],FlagPrint=False)
                else:
                    if a!=b: Flag=True
            if Flag: 
                df.append(f)
                if not printing: printing=f'{self.name} differences in:'
                printing=printing+f'\n*\t{f}:\t {str(a)[:100]}   -->   {str(b)[:100]}'
        if not printing: printing=f'{self.name} no differences!'
        pri.Info.magenta(printing)
        return df
    
    def hasIndexOf(self,d):
      """ check if the indexes are the same """
      return self.ind==d.ind            
                              
class gPaIRS_Tab(QWidget):
    indGlob=(0,0,0,0)
    FlagGlob=False

    class Tab_Signals(QObject):
        callback2_end=Signal(str,bool,bool)

        def __init__(self, parent):
            super().__init__(parent)
            self.callback2_end.connect(parent.callback2_end)

    def __init__(self,parent=None,UiClass=None,ParClass=TABpar):
        super().__init__()
        from .gPaIRS import gPaIRS
        if parent is None:
            self.gui=self.window()
        else:
            if hasattr(parent,'gui'):
                self.gui:gPaIRS=parent.gui
            else:
                self.gui:gPaIRS=parent.window()

        self.TABname='Tab'
        self.signals=self.Tab_Signals(self)
        self.father=parent
        
        self.ParClass=ParClass
        self.TABpar=self.ParClass()            #current configuration 
        self.TABpar_old=self.ParClass()        #last configuration in the current tab
        self.TABpar_prev=[]
        self.gen_TABpar(self.TABpar.ind,FlagEmptyPrev=True) #queue of previous configurations, alias undos/redos (indTree,indItem,ind)
        self.Num_Prevs_Max=Num_Prevs_Max

        self.FlagAddPrev=True     #if False, no further par are added to the queue of undos/redos "prev"
        self.FlagBridge=True      #if False, no bridge is executed during setting of parameters
        self.FlagPrevPropagation=False

        #self.setTABpar_prev=lambda itree,iitem,i,flagBridge: None
        self.TABsettings=[]

        self.FlagSettingPar=False
        self.FlagAsyncCallEvaluation=False
        self.disableTab=lambda flag: None

        self.adjustTABpar=lambda: None
        self.setTABlayout=lambda: None
        self.checkTABpar=lambda ind: None
        self.setTABwarn=lambda ind: None
        self.setTABpar_bridge=lambda fLagAdjustPar, flagCallback: None
        self.add_TABpar_bridge=lambda tip, ind: None

        self.buttonTab=None

        #Controls
        if UiClass!=None:
            self.ui=UiClass()
        if not hasattr(self,'ui'):
            self.ui=self
        if hasattr(self.ui,'setupUi'):
            self.ui.setupUi(self)
        if hasattr(self.ui,'name_tab'):
            self.name_tab=self.ui.name_tab.text().replace(' ','')
        else:
            self.name_tab=''

        
        #------------------------------------- Graphical interface: miscellanea
        self.pixmap_warnc = QPixmap(u""+ icons_path +"warning_circle.png")
        self.pixmap_done  = QPixmap(u""+ icons_path +"completed.png")
        
        self.undo_icon=QIcon()
        self.undo_icon.addFile(u""+ icons_path +"undo.png", QSize(), QIcon.Normal, QIcon.Off)  
        self.redo_icon=QIcon()
        self.redo_icon.addFile(u""+ icons_path +"redo.png", QSize(), QIcon.Normal, QIcon.Off)  
        if not hasattr(self.ui,'button_back'): 
            setattr(self.ui,'button_back',QPushButton(self))
        else:
            self.ui.button_back.contextMenuEvent=lambda e: self.bfContextMenu(-1,e)
        if not hasattr(self.ui,'button_forward'): 
            setattr(self.ui,'button_forward',QPushButton(self))
        else:
            self.ui.button_forward.contextMenuEvent=lambda e: self.bfContextMenu(+1,e)
        if not hasattr(self.ui,'button_restore_undo'): 
            setattr(self.ui,'button_restore_undo',QPushButton(self))
        if not hasattr(self.ui,'label_number'): 
            setattr(self.ui,'label_number',QLabel(self))
        if hasattr(self.ui,'button_close_tab'):
            b:QPushButton=self.ui.button_close_tab
            b.setCursor(Qt.CursorShape.PointingHandCursor)
        self.onlyReadLabel:QLabel=None
        self.button_reset_step:QPushButton=None
        self.button_step_inherit:QPushButton=None
        self.button_copy_step:QPushButton=None
        self.button_link_step:QPushButton=None

        self.FlagDisplayControls=True  #if False, undo and redo buttons are hidden and so not usable
        self.ui.button_forward.hide()
        self.ui.button_back.hide()
        self.ui.button_restore_undo.hide()
        self.ui.button_back.clicked.connect(self.button_back_action)
        self.ui.button_forward.clicked.connect(self.button_forward_action)
        self.ui.label_number.setText('')
        self.ui.label_number.hide()

        if hasattr(self.ui,'spin_x'):
            self.ui.spin_x.valueChanged.connect(self.spin_x_changing)
        if hasattr(self.ui,'spin_y'):
            self.ui.spin_y.valueChanged.connect(self.spin_y_changing)
        
        self.spins_valueChanged=[]

        self.nullCallback=lambda f='Null Callback': self.wrappedCallback(f,lambda: True)()
        self.fullCallback=lambda f='Full Callback': self.wrappedCallback(f,lambda: None)()

#*************************************************** Widgets
    def defineWidgets(self):        
        def wDict(types,signals):
            l=[]
            for t in types: 
                for c in self.findChildren(t): l.append(c) if c not in l else None
            d={'widgets': l, 'signals': signals}
            return d
                       
        widgets={
                'spin':     wDict([MyQSpin,MyQDoubleSpin],['addfuncout','addfuncreturn']),
                'check':    wDict([QCheckBox],['toggled']),
                'radio':    wDict([QRadioButton],['toggled']),
                'line_edit': wDict([QLineEdit,MyQLineEdit,MyQLineEditNumber],['addfuncout','returnPressed']),
                'button' :  wDict([QPushButton,QToolButton,MyToolButton],['clicked']),
                'combo' :   wDict([QComboBox],['activated']),
                }
        self.widgetTypes=list(widgets)
        self.widgets=[]
        self.widgetSignals=[]
        for w in self.widgetTypes:
            self.widgets.append(widgets[w]['widgets'])
            self.widgetSignals.append(widgets[w]['signals'])
        self.widgetsOfType=lambda t: self.widgets[self.widgetTypes.index(t)]

        for c in self.widgetsOfType('combo'):
            c:QComboBox
            nameCombo=c.objectName().split('combo_')[-1]
            if hasattr(self,nameCombo+'_items'):
                itemsCombo=getattr(self,nameCombo+'_items')
            else: continue
            if hasattr(self,nameCombo+'_order'):
                orderCombo=getattr(self,nameCombo+'_order')
            else: orderCombo=[i for i in range(len(itemsCombo))]
            c.clear()
            for i in orderCombo:
                c.addItem(itemsCombo[i])

#*************************************************** Widget callbacks
    def defaultCallback(self,wName,wtype):
        widget=getattr(self.ui,wtype+'_'+wName)
        if wName=='x_min':
            pass
        if wtype=='spin': 
            def callbackSpin(s:MyQSpin):
                setattr(self.TABpar,wName,s.value())
            default_callback=lambda: callbackSpin(widget)
        elif (wtype=='check' or wtype=='radio') and hasattr(self.TABpar,'Flag'+wName): 
            def callbackCheck(c:QCheckBox):
                setattr(self.TABpar,'Flag'+wName,c.isChecked())
            default_callback=lambda: callbackCheck(widget)
        elif wtype=='combo':
            def callbackCombo(c:QComboBox):
                if hasattr(self,wName+'_items'):
                    itemsCombo:list=getattr(self,wName+'_items')
                else:
                    itemsCombo=[c.itemText(i) for i in range(c.count())]
                if len(itemsCombo):
                    setattr(self.TABpar,wName,itemsCombo.index(c.currentText()))
                else: 
                    setattr(self.TABpar,wName,-1)
            default_callback=lambda: callbackCombo(widget)
        elif wtype=='line_edit':
            def callbackLineEdit(l:MyQLineEdit):
                setattr(self.TABpar,wName,l.text())
            default_callback=lambda: callbackLineEdit(widget)
        else:
            default_callback=None
        return default_callback
                    
    def defineCallbacks(self):
        def buildCallback(wName,wtype,tip):
            if not hasattr(self.ui,wtype+'_'+wName): return   
            callback01=callback02=callback03=callback1=callback2=None

            #callback01: _preaction method in the class: particular callback that is fast and can be executed on the main thread instead of as concurrent future before the default callback
            a=wtype+'_'+wName+'_preaction'
            if hasattr(self,a): callback01=getattr(self,a)

            #callback02: callback common to all widgets of the same type (avoid code repetition)
            if hasattr(self.TABpar,wName) or ((wtype=='check' or wtype=='radio') and hasattr(self.TABpar,'Flag'+wName)): 
                callback02=self.defaultCallback(wName,wtype)

            #callback03: _action method in the class: particular callback that is fast and can be executed on the main thread instead of as concurrent future after the default callback
            a=wtype+'_'+wName+'_action'
            if hasattr(self,a): callback03=getattr(self,a)

            if callback01 or callback02 or callback03:
                def callback1():
                    name=wName
                    flag=None
                    if callback01: callback01()
                    if callback02: callback02()
                    if callback03: flag=callback03()
                    return flag
            else: callback1=None

            #callback1: _action_future method in the class: particular callback that is fast and can be executed on the main thread instead of as concurrent future
            a=wtype+'_'+wName+'_action_future'
            if hasattr(self,a): 
                callback2=getattr(self,a)

            if callback1 or callback2:
                callback=self.wrappedCallback(tip,callback1,callback2)
                setattr(self,wtype+'_'+wName+'_callback',callback)
            else:
                callback=None
            return callback
        
        self.widgetCallbacks=[]
        for l,wtype in zip(self.widgets,self.widgetTypes):
            missing_tips=[]
            if hasattr(self,wtype+'_tips'):
                d=getattr(self,wtype+'_tips')
            else:
                d=None
                pri.Coding.red(f'*** [{self.TABname}]  - {wtype}_tips -  missing dictionary!')
            widgetCallbacks=[]
            for c in l:
                c:QObject
                if c.objectName() in ('button_back','button_forward','button_close_tab'): 
                    callback=None
                    widgetCallbacks.append(callback)
                    continue
                if '_' in c.objectName(): wName=c.objectName().split(wtype+'_')[-1]
                else:  wName=c.objectName()
                if d!=None:
                    if wName in list(d): tip=d[wName]
                    else: 
                        tip=f"{wtype} {wName}"
                        if wName and not (wtype=='line_edit' and wName in ('qt_spinbox_lineedit') ) and \
                            not (wtype=='button' and wName in ('back','forward','close_tab') ):
                            missing_tips.append(f"'{wName}'")
                else: tip=f"{wtype} {wName}"
                callback=buildCallback(wName,wtype,tip)
                widgetCallbacks.append(callback)
            if len(missing_tips):
                pri.Coding.blue(f'*** [{self.TABname}]  - {wtype}_tips -  missing tips:\n\t'+"\n\t".join(missing_tips))
            elif d:
                pri.Coding.green(f'✔️ [{self.TABname}]  - {wtype}_tips -  complete dictionary!')
            self.widgetCallbacks.append(widgetCallbacks)

    def wrappedCallback(self,tip='',callback1=None,callback2=None):
         def debugFun(fun,message=''):
            try:
                out=fun()
            except Exception as inst:
                out=None
                pri.Error.red(f"{'!'*100}\n{message}:\n{traceback.format_exc()}\n{'!'*100}")
                printException()
                #if Flag_DEBUG: raise Exception("!!! Debug stop !!!") 
            return out
         async def callback2_async(fun2):
            if Flag_DEBUG: timesleep(time_callback2_async)
            if fun2: debugFun(fun2,f'Asyncronus function error callback2 ({tip}): ')
            return
         def callback():
            FlagSettingPar=self.FlagSettingPar or TABpar.FlagSettingPar
            if FlagSettingPar: 
                return
            else:
                self.FlagSettingPar=True
            try:
                FlagPreventAddPrev=False
                if callback1: FlagPreventAddPrev=debugFun(callback1,f'Error callback1 ({tip}): ')
                if callback2: 
                    self.FlagAsyncCallEvaluation=True
                    self.disableTab(True)
            
                    if FlagAsyncCallbacks:
                        f3=globExecutor.submit(asyncio.run,callback2_async(callback2))
                        def f3callback(_f3):
                            self.signals.callback2_end.emit(tip,FlagSettingPar,FlagPreventAddPrev)
                        f3.add_done_callback(f3callback)
                    else:
                        debugFun(callback2,f'Error callback2 ({tip}): ')
                        self.callback2_end(tip,FlagSettingPar,FlagPreventAddPrev)
                else:
                    self.callback2_end(tip,FlagSettingPar,FlagPreventAddPrev)
            except Exception as inst:
                pri.Error.red(f"Error in wrapped callback ({tip}):\n{traceback.format_exc()}")
                printException()
                self.FlagSettingPar=FlagSettingPar
            return 
         return callback
        
    @Slot(str)
    def callback2_end(self,tip,FlagSettingPar,FlagPreventAddPrev):
        pri.Coding.green(f'{"*"*50}\nCallback <{self.TABname}>: {tip}')
        if tip=='Null Callback':
            pass
        try:
            if self.FlagAsyncCallEvaluation==True:
                self.FlagAsyncCallEvaluation=False
                self.disableTab(False)
            try:
                TABpar_ind=self.TABpar_at(self.TABpar.ind)
                if TABpar_ind and self.TABpar.isEqualTo(TABpar_ind,FlagStrictDiff=True): return
                FlagNewPar=self.isNewPar()
                flagRun=self.TABpar_at(self.TABpar.ind).flagRun
                if FlagNewPar and (flagRun!=0 or len(self.TABpar.link)>0):
                    #FlagNewPar=not self.FlagAddPrev
                    if len(self.TABpar.link)>0:
                        ITE0_master=self.gui.ui.Explorer.ITEsfromInd(self.TABpar.link)[0]
                        linkInfo=f'{ITE0_master.ind[2]+1}: {ITE0_master.name}'
                        Messagge=f'This process step is linked to process {linkInfo}. To modify it, you need to unlink the process step.'
                        if flagRun!=0 or ITE0_master.flagRun!=0:
                            Messagge+=' After unlinking the process will be reset!'
                        def unlink_pars_online():
                            TABpar_ind.copyfrom(self.TABpar)
                            self.gui.unlink_pars(self.TABpar.ind)
                            if self.TABpar.flagRun!=0 or ITE0_master.flagRun!=0:
                                self.gui.reset_step(self.TABpar.ind)
                        warningDialog(self.gui,Messagge,addButton={'Unlink step!': unlink_pars_online})
                    elif flagRun==-10:
                         Messagge='This process step is in the queue for process execution. To modify it, you need to stop processing and then reset it and all the subsequent steps.'
                         warningDialog(self.gui,Messagge)
                    elif flagRun==-2:
                         Messagge='This process step is currently in execution. To modify it, you need to stop processing and then reset it and all the subsequent steps.'
                         warningDialog(self.gui,Messagge)
                    elif flagRun!=0:
                        if self.gui.FlagRun:
                            Messagge='This process step has already been executed. To modify it, you need to stop processing and then reset it and all the subsequent steps.'
                            warningDialog(self.gui,Messagge)               
                        else:    
                            Messagge='This process step has already been executed. To modify it, you need to reset the current step and all the subsequent ones.'
                            def reset_step_online():
                                TABpar_ind.copyfrom(self.TABpar)
                                self.gui.reset_step(self.TABpar.ind)
                                return
                            warningDialog(self.gui,Messagge,addButton={'Reset step!': reset_step_online})
                    

                    if flagRun!=0 or len(self.TABpar.link)>0:
                        self.TABpar.copyfrom(TABpar_ind)
                        originalStyleSheet=self.gui.styleSheet()
                        self.gui.setStyleSheet(f'background: {self.palette().color(QPalette.ColorRole.Text).name()} ;') #dcdcdc
                        self.repaint()
                        try:
                            self.setTABpar(FlagAdjustPar=False,FlagBridge=False,FlagCallback=False)
                        finally:
                            timesleep(.01)
                            self.gui.setStyleSheet(originalStyleSheet)
                    else:
                        return
                else:
                    self.setTABpar(FlagAdjustPar=True,FlagBridge=self.FlagBridge,FlagCallback=True)
            except:
                pri.Error.red(f'Error in callback2_end ({tip}):\n        |-> Error in setting the parameters')
                pri.Error.red(f'{traceback.format_exc()}')
                printException()
            else:
                try:  
                    FlagNewPar=FlagNewPar and not FlagPreventAddPrev and self.TABpar.flagRun==0 and len(self.TABpar.link)==0
                    self.add_TABpar(tip,FlagNewPar)
                except:
                    pri.Error.red(f'Error in callback2_end ({tip}):\n        |-> Error in adding parameters to redos/undos {tip}')    
                    printException()
        except Exception as inst:
                pri.Error.red(f"Error in callback2_end ({tip}):\n{traceback.format_exc()}")
                printException()
        finally:
            self.FlagSettingPar=FlagSettingPar
        pri.Coding.green(f'Callback <{self.TABname}>: {tip}\n{"*"*50}\n')

    def connectCallbacks(self):
        for W,S,CB in zip(self.widgets,self.widgetSignals,self.widgetCallbacks):
            for w,cb in zip(W,CB):
                if cb==None: continue
                for s in S:
                    sig=getattr(w,s)
                    if hasattr(sig,'connect'):
                        sig.connect(cb)
                    elif s in ('addfuncout','addfuncreturn'):
                        if w in self.spins_valueChanged:
                            if s=='addfuncout': w.valueChanged.connect(cb)
                        else:
                            sig['callback']=cb

#*************************************************** Setting parameters to widgets
    def defaultSetting(self,wName,wtype):
        if not hasattr(self.ui,wtype+'_'+wName): return  
        widget=getattr(self.ui,wtype+'_'+wName)
        if wtype=='spin': 
            def settingSpinValue(s:MyQSpin):
                s.setValue(getattr(self.TABpar,wName))
            default_setting=lambda: settingSpinValue(widget)
        elif (wtype=='check' or wtype=='radio') and hasattr(self.TABpar,'Flag'+wName): 
            def settingChecked(c:QCheckBox):
                try:
                    c.setChecked(getattr(self.TABpar,'Flag'+wName))
                except:
                    pass
            default_setting=lambda: settingChecked(widget)
        elif wtype=='combo':
            widget:QComboBox
            def settingComboIndex(c:QComboBox):
                items=[c.itemText(i) for i in range(c.count())]
                if hasattr(self,wName+'_items'):
                    itemsCombo:list=getattr(self,wName+'_items')
                else:
                    itemsCombo=items
                ind=getattr(self.TABpar,wName)
                if ind>-1: c.setCurrentIndex(items.index(itemsCombo[ind]))
            default_setting=lambda: settingComboIndex(widget)
        elif wtype=='line_edit':
            def settingText(l:MyQLineEdit):
                l.setText(getattr(self.TABpar,wName))
            default_setting=lambda: settingText(widget)
        else:
            default_setting=None
        return default_setting

    def defineSettings(self):
        def buildSetting(wName,wtype):
            setting0=default_setting=setting2=None
            #setting0: _preset method in the class: setting to be done before standard setting (0)
            a=wtype+'_'+wName+'_preset'
            if hasattr(self,a): setting0=getattr(self,a) 

            #setting1: setting common to all widgets of the same type (avoid code repetition)
            if hasattr(self.TABpar,wName) or ((wtype=='check' or wtype=='radio') and hasattr(self.TABpar,'Flag'+wName)): 
                default_setting=self.defaultSetting(wName,wtype)
                
            #callback2: _set method in the class: setting to be done before standard setting (1)
            a=wtype+'_'+wName+'_set'
            if hasattr(self,a): setting2=getattr(self,a)

            def setting():
                name=wName
                if setting0: setting0()
                if default_setting: default_setting()
                if setting2: setting2()
                return
            setattr(self,wtype+'_'+wName+'_setting',setting)
            self.TABsettings.append(setting)
            return
        
        self.TABsettings=[]
        for l,wtype in zip(self.widgets,self.widgetTypes):
            for c in l:
                wName=c.objectName().split(wtype+'_')[-1]
                buildSetting(wName,wtype)
                if wtype=='line_edit':
                    if hasattr(c,'addfuncout'):
                        c.addfuncout['setting']=self.TABsettings[-1]
                    else:
                        def focusOutEvent(obj, event):
                            type(obj).focusOutEvent(obj,event) #to preserve classical behaviour before adding the below
                            self.TABsettings[-1]()
                        c.focusOutEvent=focusOutEvent

    def setTABpar(self,FlagAdjustPar=True,FlagBridge=True,FlagCallback=False,FlagDisplayControls=None):
        if self.TABpar.FlagNone and self.TABpar_at(self.TABpar.ind) is None: return
        pri.Coding.magenta(f'    --- setting {self.TABpar.name} {self.TABpar.ind}')

        self.FlagSettingPar=True
        FlagSettingPar=TABpar.FlagSettingPar
        TABpar.FlagSettingPar=True

        if FlagAdjustPar:
            self.adjustTABpar()
            
        self.setTABlayout() 
        for f in self.TABsettings:
            f()
        #self.TABpar_old.copyfrom(self.TABpar)
        self.TABpar.FlagInit=True

        if FlagBridge:
            self.setTABpar_bridge(FlagAdjustPar,FlagCallback)
        
        self.TABpar_old.copyfrom(self.TABpar)
        
        if FlagDisplayControls is None: FlagDisplayControls=not FlagBridge
        if FlagDisplayControls:
            self.display_controls()
        
        TABpar.FlagSettingPar=FlagSettingPar 
        self.FlagSettingPar=False

        if not FlagCallback: 
            self.adjustTABparInd()

    def setTABpar_at(self,ind,FlagAdjustPar=False,FlagBridge=False):
        pri.Coding.green(f'{":"*50}\nSetting previous par <{self.TABname}>: {ind}')
        TABpar_ind:TABpar=self.TABpar_at(ind)
        if not TABpar_ind.FlagNone:
            self.TABpar.copyfrom(TABpar_ind)  
            self.setTABpar(FlagAdjustPar,FlagBridge)
        pri.Coding.green(f'Setting previous par <{self.TABname}>: {ind}\n{":"*50}\n')

    def setupWid(self):
        setupWid(self)  
        fPixSize_TabNames=30
        qlabels=self.findChildren(QLabel)
        labs=[l for l in qlabels if 'name_tab' in l.objectName()]
        for lab in labs:
            lab:QLabel #=self.ui.name_tab
            font=lab.font()
            font.setPixelSize(fPixSize_TabNames)
            lab.setFont(font)    

    def setTABWarnLabel(self):
        self.ui.name_tab.setFixedWidth(self.ui.name_tab.sizeHint().width())
        self.ui.label_done.setPixmap(self.pixmap_done if self.TABpar.OptionDone==1 else self.pixmap_warnc)
        self.ui.label_done.setToolTip(self.TABpar.warningMessage)
        
#*************************************************** Undo/redo
    def adjustTABparInd(self):
        TABpar_ind=self.TABpar_at(self.TABpar.ind)
        if TABpar_ind: 
            TABpar_ind.copyfrom(self.TABpar)

    def gen_TABpar(self,ind,FlagSet=True,FlagEmptyPrev=False,FlagNone=False,FlagInsert=-1,Process=None,Step=None):
        Prev=prev=self.TABpar_prev if FlagSet else []

        for i in range(len(ind)):
            if i<len(ind)-1:
                if i==FlagInsert:
                    prev.insert(ind[i],[])
                else:
                    while ind[i]>len(prev)-1:
                        prev.append([])
                prev=prev[ind[i]]
            else:
                if not FlagEmptyPrev:
                    if i==FlagInsert:
                        if ind[i]<len(prev):
                            if FlagNone:
                                prev[ind[i]]=None
                            else:
                                if Process is not None and Step is not None:
                                    par=self.ParClass(Process=Process,Step=Step)
                                else:
                                    par=self.ParClass()
                                par.ind=ind
                                prev[ind[i]]=par
                                pri.Coding.cyan(f'[gen_TABpar] {par.surname} {par.ind} ---> {self.TABpar_at(ind).ind}')
                        else:
                            if FlagNone:
                                prev.insert(ind[i],None)
                            else:
                                if Process is not None and Step is not None:
                                    par=self.ParClass(Process=Process,Step=Step)
                                else:
                                    par=self.ParClass()
                                par.ind=ind
                                prev.insert(ind[i],par)
                                pri.Coding.cyan(f'[gen_TABpar] {par.surname} {par.ind} ---> {self.TABpar_at(ind).ind}')
                    else:
                        while ind[i]>len(prev)-1:
                            if FlagNone:
                                prev.append(None)
                            else:
                                if Process is not None and Step is not None:
                                    par=self.ParClass(Process=Process,Step=Step)
                                else:
                                    par=self.ParClass()
                                par.ind=ind
                                prev.append(par)
                                pri.Coding.cyan(f'[gen_TABpar] {par.surname} {par.ind} ---> {self.TABpar_at(ind).ind}')
        return Prev
        
    def TABpar_at(self,ind):
        if ind[0]<len(self.TABpar_prev):
            p:TABpar=self.TABpar_prev[ind[0]]
        else: 
            p=None
        if p:
            for i in range(1,len(ind)):
                if ind[i]<len(p):
                    p=p[ind[i]]
                else:
                    p=None
                    break
        return p
    
    def TABpar_prev_at(self,ind):
        if len(self.TABpar_prev)-1<ind[0]:
            return []
        else:
            p:TABpar=self.TABpar_prev[ind[0]]
            for i in range(1,len(ind)-1):
                if len(p)-1<ind[i]:
                    p=[]
                    break
                else:
                    p=p[ind[i]]
            return p

    def isNewPar(self):
        ind=self.TABpar.ind
        TABpar_prev=self.TABpar_prev_at(ind)
        if len(TABpar_prev)>0:
            FlagNewPar=self.FlagAddPrev and self.TABpar.isDifferentFrom(TABpar_prev[-1],exceptions=self.TABpar.unchecked_fields+['ind']) #see below
            self.TABpar.printDifferences(TABpar_prev[-1],exceptions=self.TABpar.unchecked_fields+['ind']) 
        else:
            FlagNewPar=self.FlagAddPrev
        return FlagNewPar

    def add_TABpar(self,tip,FlagNewPar=True):
        ind=self.TABpar.ind
        TABpar_prev=self.TABpar_prev_at(ind)
        if (FlagNewPar or len(TABpar_prev)==0) and self.FlagAddPrev: #something changed
            if len(TABpar_prev): TABpar_prev[-1].printDifferences(self.TABpar,self.TABpar.unchecked_fields+['ind'])
            self.add_TABpar_copy(tip,ind)
            self.add_TABpar_bridge(tip,ind)  #should create a copy of the other tabs' parameters (see gPaIRS)
            ind[-1]=TABpar_prev[-1].ind[-1]
        else:
            self.adjustTABparInd()
        
        if self.FlagPrevPropagation:
            #pri.Time.blue('Propagation par init')
            TABpar_prev=self.TABpar_prev_at(self.TABpar.ind)
            for p in TABpar_prev:
                p:TABpar
                p.copyfrom(TABpar_prev[self.TABpar.ind[-1]],exceptions=['ind','tip'])
            #pri.Time.blue('Propagation par end')
        return ind

    def add_TABpar_copy(self,name,ind):
        TABpar_prev:list=self.TABpar_prev_at(ind)
        if not self.TABpar.FlagNone:
            TABpar_new=self.TABpar.duplicate()
            if len(TABpar_prev)>self.Num_Prevs_Max:
                TABpar_prev.pop(0)
                for k,p in enumerate(TABpar_prev):
                    p.ind[-1]=k
            else:
                TABpar_new.ind[-1]=len(TABpar_prev)
            TABpar_new.tip=name
            self.TABpar.ind=copy.deepcopy(TABpar_new.ind)  #in this way, we move to the last added par in the "prev"
            pri.Coding.yellow(f'   |-> +++ {self.TABpar.name}: new par {TABpar_new.ind} <{name}>')
        else:
            TABpar_new=None
        TABpar_prev.append(TABpar_new)
        self.display_controls()
        ind_new=[i for i in ind]
        ind_new[-1]=len(TABpar_prev)-1
        return ind_new

    def display_controls(self):
        if not self.FlagDisplayControls: return
        FlagVisible=self.TABpar.flagRun==0 and len(self.TABpar.link)==0 
        self.ui.button_restore_undo.setVisible(FlagVisible)
        self.ui.button_back.setVisible(FlagVisible)
        self.ui.button_forward.setVisible(FlagVisible)
        lprev=len(self.TABpar_prev_at(self.TABpar.ind))
        if self.onlyReadLabel:
            if len(self.TABpar.link)==0:
                if lprev:
                    ITE0=self.gui.ui.Explorer.ITEsfromInd(self.TABpar.ind)[0]
                    if ITE0.flagRun==0:
                        self.onlyReadLabel.setText('')
                    else:
                        self.onlyReadLabel.setText('read-only')
                else:
                    self.onlyReadLabel.setText('')
                self.button_link_step.setToolTip('Link current process step to another in the same project')
                self.button_link_step.setIcon(self.icon_link)
                self.gui.RCLbar.buttonData[3]['name']='Link step to...'
            else:
                if hasattr(self.gui,'ui') and hasattr(self.gui.ui,'Explorer'):
                    ITE0_master=self.gui.ui.Explorer.ITEsfromInd(self.TABpar.link)[0]
                    linkInfo=f'linked to {ITE0_master.ind[2]+1}: {ITE0_master.name}'
                    self.onlyReadLabel.setText(linkInfo)
                else:
                    self.onlyReadLabel.setText('')
                self.button_link_step.setToolTip('Unlink current process step')
                self.button_link_step.setIcon(self.icon_unlink)
                self.gui.RCLbar.buttonData[3]['name']='Unlink step'
            self.button_link_step.setStatusTip(self.button_link_step.toolTip())
            self.button_link_step.setChecked(len(self.TABpar.link)!=0)

            if self.gui.ui.Explorer.TREpar.step is None:
                FlagProcessTree=False
            else:
                FlagProcessTree=self.gui.ui.Explorer.currentTree==self.gui.ui.Explorer.processTree and self.gui.ui.Explorer.TREpar.step>0
            FlagLabel=(self.TABpar.flagRun!=0 and len(self.TABpar.link)==0) or len(self.TABpar.link)>0
            FlagReset=self.TABpar.flagRun!=0 and len(self.TABpar.link)==0
            FlagInherit=self.TABpar.flagRun==0 and len(self.TABpar.link)==0 and len(self.gui.IOVheritableSteps())>0
            FlagCopy=self.TABpar.flagRun==0 and len(self.TABpar.link)==0 and len(self.gui.linkableSteps(FlagExcludeLinked=True))>0
            FlagLink=(len(self.TABpar.link)==0 and self.TABpar.flagRun==0 and len(self.gui.linkableSteps(FlagExcludeLinked=True))>0) or len(self.TABpar.link)>0
            if FlagProcessTree and (FlagLabel or FlagReset or FlagInherit or FlagCopy or FlagLink):
                self.gui.w_RCL.setVisible(True)
                self.onlyReadLabel.setVisible(FlagLabel)
                self.button_reset_step.setVisible(FlagReset)
                self.button_step_inherit.setVisible(FlagInherit)
                self.button_copy_step.setVisible(FlagCopy)
                self.button_link_step.setVisible(FlagLink)
            else:
                self.gui.w_RCL.setVisible(False)
            FlagEnabled = not self.gui.FlagRun
            self.button_reset_step.setEnabled(FlagEnabled)
            self.button_step_inherit.setEnabled(FlagEnabled)
            self.button_copy_step.setEnabled(FlagEnabled)
            self.button_link_step.setEnabled(FlagEnabled)

        if self.TABpar.flagRun or len(self.TABpar.link)>0: return

        i=self.TABpar.ind[-1]
        self.ui.button_restore_undo.setVisible(lprev>1)
        self.ui.button_forward.setVisible(lprev>1)
        self.ui.button_back.setVisible(lprev>1)
        self.ui.button_restore_undo.setEnabled(not (i==lprev-1 or i==-1))
        self.ui.button_forward.setEnabled(not (i==lprev-1 or i==-1))
        self.ui.button_back.setEnabled(i!=0)
        if self.ui.label_number.isVisible():
            if i==lprev-1 or i==-1:
                self.ui.label_number.setText('')
            elif i>=0:
                self.ui.label_number.setText("(-"+str(lprev-1-i)+")")
            else:
                self.ui.label_number.setText("(-"+str(i+1)+")")

    def button_back_action(self):
        ind=self.TABpar.ind
        ind[-1]-=1
        self.FlagSettingPar=True
        self.setFocus()
        self.FlagSettingPar=False
        self.setTABpar_at(ind,FlagAdjustPar=ind[-1]==0,FlagBridge=True) #True=with bridge
        return False

    def button_forward_action(self):
        ind=self.TABpar.ind
        ind[-1]+=1
        self.FlagSettingPar=True
        self.setFocus()
        self.FlagSettingPar=False
        self.setTABpar_at(ind,FlagAdjustPar=ind[-1]==0,FlagBridge=True) #True=with bridge
        return False

    def bfContextMenu(self,bf,event):
        i=self.TABpar.ind[-1]
        TABpar_prev=self.TABpar_prev_at(self.TABpar.ind)

        if bf==-1:
            b=self.ui.button_back
            f=self.button_back_action
            kin=max([0,i-Num_Prevs_back_forw])
            krange=[k for k in range(i-1,kin,-1)]+[0]
            icon=self.undo_icon
            d=1
        elif bf==1:
            b=self.ui.button_forward
            f=self.button_forward_action
            kfin=min([len(TABpar_prev)-1,i+Num_Prevs_back_forw])
            krange=[k for k in range(i+1,kfin)]+[len(TABpar_prev)-1]
            icon=self.redo_icon
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
                self.TABpar.ind[-1]=k-bf
                f()

    def cleanPrevs(self,ind,FlagAllPrev=False):
        TABpar_prev=self.TABpar_prev_at(ind)
        for _ in range(len(TABpar_prev)-1*int(not FlagAllPrev)):
            TABpar_prev.pop(0)
        if not FlagAllPrev:
            TABpar_prev[0].ind[-1]=0
            if self.TABpar.ind[:-1]==ind[:-1]:
                self.TABpar.ind[-1]=0


#*************************************************** Special spin boxes (x,y,w,h)
    def setMinMaxSpinxywh(self):
        self.ui.spin_x.setMinimum(0)
        self.ui.spin_x.setMaximum(self.TABpar.W-1)
        self.ui.spin_y.setMinimum(0)
        self.ui.spin_y.setMaximum(self.TABpar.H-1)
        self.ui.spin_w.setMinimum(1)
        self.ui.spin_w.setMaximum(self.TABpar.W)
        self.ui.spin_h.setMinimum(1)
        self.ui.spin_h.setMaximum(self.TABpar.H)
        for field in ('spin_x','spin_y','spin_w','spin_h'):
            s:MyQSpin=getattr(self.ui,field)
            tip=getattr(self,"tip_"+field)
            stringa=". Image size: "+str(self.TABpar.W)+"x"+str(self.TABpar.H)
            newtip=tip+stringa
            s.setToolTip(newtip)
            s.setStatusTip(newtip)
        self.check_resize()

    def check_resize(self):
        if self.TABpar.W!=self.TABpar.w or \
            self.TABpar.H!=self.TABpar.h:
            self.ui.button_resize.show()
        else:
            self.ui.button_resize.hide()     

    def button_resize_action(self):
        self.TABpar.x=self.TABpar.y=0
        self.TABpar.w=self.TABpar.W
        self.TABpar.h=self.TABpar.H
        self.ui.spin_w.setMaximum(self.TABpar.W)
        self.ui.spin_h.setMaximum(self.TABpar.H)
        return

    def spin_x_changing(self):
        wmax=self.TABpar.W-self.ui.spin_x.value()
        self.ui.spin_w.setMaximum(wmax)
        w=min([self.TABpar.w,wmax])
        self.ui.spin_w.setValue(w)

    def spin_x_action(self):
        self.TABpar.w=self.ui.spin_w.value()

    def spin_y_changing(self):
        hmax=self.TABpar.H-self.ui.spin_y.value()
        self.ui.spin_h.setMaximum(hmax)
        h=min([self.TABpar.h,hmax])
        self.ui.spin_h.setValue(h)

    def spin_y_action(self):
       self.TABpar.h=self.ui.spin_h.value()

#*************************************************** Widget setup
    def newTip(self,field):
        s: MyQSpin
        if field=='spin_range_from':  #INPpar
            s=self.ui.spin_range_from
            stringa=". Range: "+str(s.minimum())+'-'+str(s.maximum())
            newtip=self.tip_spin_range_from+stringa
        elif field=='spin_range_to':  #INPpar
            s=self.ui.spin_range_to
            stringa=". Max.: "+str(s.maximum())
            newtip=self.tip_spin_range_to+stringa
        s.setToolTip(newtip)
        s.setStatusTip(newtip)  

#*************************************************** Widget setup
def setupWid(self:gPaIRS_Tab,FlagFontSize=True):
    if FlagFontSize: setFontPixelSize(self,fontPixelSize)
    
    if hasattr(self,'widgets'): widgets=self.widgets
    else: widgets=self.findChildren(QWidget)
    widgets+=self.findChildren(CollapsibleBox)
    for w in widgets:
        w:QToolButton
        if hasattr(w,'toolTip'):
            tooltip=toPlainText(w.toolTip())
            if hasattr(w,'shortcut'):
                scut=w.shortcut().toString(QKeySequence.NativeText)
                if scut:
                    scut=toPlainText('('+scut+')')
                    if scut not in tooltip:
                        tooltip+=' '+scut
                        w.setToolTip(tooltip)
            #if hasattr(w,'statusTip'):
            w.setStatusTip(tooltip)
                    
        if hasattr(w,'setup'):
            w.setup()
        if hasattr(w,'setup2'):
            w.setup2()

        if isinstance(w,QToolButton) or isinstance(w,QPushButton):
            if w.cursor().shape()==Qt.CursorShape.ArrowCursor:
                w.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    for sname in ('range_from','range_to','x','y','w','h'):
        if hasattr(self.ui,"spin_"+sname):
            sp=getattr(self.ui,"spin_"+sname)
            setattr(self,"tip_spin_"+sname,sp.toolTip())

def setFontPixelSize(self,fPixSize):
    font=self.font()
    font.setFamily(fontName)
    font.setPixelSize(fPixSize)
    self.setFont(font)
    c=self.findChildren(QWidget)
    for w in c:
        w:QWidget
        if w.objectName()=='title_project' and hasattr(self,'projectTree'):
            self.projectTree.titleFont(w,fPixSize)
        elif  w.objectName()=='subtitle_project' and hasattr(self,'projectTree'):
            self.projectTree.subTitleFont(w,fPixSize)
        elif w.objectName()=='title_process' and hasattr(self,'processTree'):
            self.processTree.titleFont(w,fPixSize)
        elif  w.objectName()=='subtitle_process' and hasattr(self,'processTree'):
            self.processTree.subTitleFont(w,fPixSize)
        elif  w.objectName()=='title_step':
            w.parent().stepTitleFont(w,fPixSize)
        elif hasattr(w,'setFont'):
            font=w.font()
            font.setFamily(fontName)
            t=type(w)
            if issubclass(t,QLabel):
                setFontSizeText(w,[fPixSize-1])
            elif issubclass(t,QPushButton) or issubclass(t,QToolButton):
                font.setPixelSize(fPixSize+1)
                w.setFont(font)
                adjustFont(w)
            else:
                font.setPixelSize(fPixSize)
                w.setFont(font)
                adjustFont(w)
    c=self.findChildren(RichTextPushButton)
    for w in c:
        font=w.font()
        font.setFamily(fontName)
        font.setPixelSize(fPixSize+3)
        w.lbl.setFont(font)
        
def setFontSizeText(lab:QLabel,fPixSizes):
    text=lab.text()
    text=re.sub(r"font-size:\d+pt",f"font-size:{fPixSizes[0]}px",text)   
    text=re.sub(r"font-size:\d+px",f"font-size:{fPixSizes[0]}px",text)  
    if len(fPixSizes)>1:
        for k in range(len(fPixSizes)-1,0,-1):
            text=re.sub(r"font-size:\d+px",f"font-size:{fPixSizes[k]}px",text,k)
    lab.setText(text)
    font=lab.font()
    font.setPixelSize(fPixSizes[0])
    lab.setFont(font)
    adjustFont(lab)

def adjustFont(self:QLabel):
    if not hasattr(self,'geometry'): return
    if not hasattr(self,'text') and not hasattr(self,'currentText'): return 
    flagParent=self.isVisible() and bool(self.parent())
    font = self.font()
    if hasattr(self,'text'):
        text = self.text()
    elif hasattr(self,'currentText'):
        text = self.currentText()
    else: return
    if 'Parallel' in text:
        pass

    if hasattr(self,'text'):
        if 'Find' in self.text():
            pass
    
    S=self.geometry()
    maxS = QRect(self.pos(),self.maximumSize())
    minS = QRect(self.pos(),self.minimumSize())
    if flagParent:
        r=self.parent().rect()
        S&= r
        maxS&= QRect(QPoint(r.x(),r.y()),self.parent().maximumSize())
        minS&= QRect(QPoint(r.x(),r.y()),self.parent().minimumSize()) 
    
    textSize=QtGui.QFontMetrics(font).size(QtCore.Qt.TextSingleLine, text)
    if (textSize.height()<=S.height()) and (textSize.width()<=S.width()):
        return
    while True:
        if font.pixelSize()<=fontPixelSize_lim[0]:
            font.setPixelSize(fontPixelSize_lim[0])
            break
        if (textSize.height()<=S.height()):
            break
        font.setPixelSize(font.pixelSize()-1)
        textSize=QtGui.QFontMetrics(font).size(QtCore.Qt.TextSingleLine, text)

    textWidth=min([textSize.width(),maxS.width()])
    textWidth=max([textWidth,minS.width()])
    if S.width()<textWidth:
        s=self.geometry()
        s.setWidth(textWidth)
        self.setGeometry(s)
        if flagParent:
            S=s&self.parent().rect()
        else:
            S=s
    while True:
        if font.pixelSize()<=fontPixelSize_lim[0]:
            font.setPixelSize(fontPixelSize_lim[0])
            break
        if (textSize.width()<=S.width()):
            break
        font.setPixelSize(font.pixelSize()-1)
        textSize=QtGui.QFontMetrics(font).size(QtCore.Qt.TextSingleLine, text)
    
    self.setFont(font)

#*************************************************** Other
def iterateList(l,value):
        if type(l)==list:
            if len(l):
                if type(l[0])==list:
                    for m in l:
                        iterateList(m,value)
                else:
                    for k in range(len(l)):
                        l[k]=value

def funexample():
    def fun2(i):
        if FlagSimulateError:
            raise Exception("funexample: the requested exception!") 
        pri.Info.cyan('funexample: Hello, sir!')
    return [1,fun2]

if __name__ == "__main__":
    a=TABpar()
    b=TABpar()

    a.printPar('a: ')
    c=a.duplicate()
    b.printPar('b: ')

    a.copyfrom(b)
    a.printPar('a: ','   copied from b')
    c.printPar('c: ')
    c.copyfromfields(b,['surname'])
    c.printPar('c: ', '   surname copied from b')

    print(f'Is a different from b? {a.isDifferentFrom(b)}')
    print(f'Is a equal to b? {a.isEqualTo(b)}')
    print(f'Is c different from b? {c.isDifferentFrom(b)}')
    print(f'Is c equal to b? {c.isEqualTo(b)}')
    print(f'Is c different from b except surname? {c.isDifferentFrom(b,["surname"])}')
    print(f'Is c equal to b except name? {c.isEqualTo(b,["name"])}')

    """
    app=QApplication.instance()
    if not app:app = QApplication(sys.argv)
    app.setStyle('Fusion')
    TAB = gPaIRS_Tab(None,QWidget)
    callbackfun=TAB.addParWrapper(funexample,'example')
    callbackfun()
    app.exec()
    app.quit()
    app=None
    """
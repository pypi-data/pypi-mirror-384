from .ui_Vis_Tab_CalVi import*
from .TabTools import*
from .calib import Calib, CalibTasks, calibTasksText, CalibFunctions, calibFunctionsText
from .calibView import CalibView
from .Input_Tab_CalVi import INPpar_CalVi
from .Process_Tab_CalVi import PROpar_CalVi


bufferSizeLimit=2000*1e6  #bytes
if __name__ == "__main__":
    cfgName='../../img/calib/NewCam0.cfg'
    cfgName='../../img/calib/NewCam0_Mod.cfg'
    FlagRunning=True
else:
    cfgName=''
    FlagRunning=False

spin_tips={
    'plane'     :  'Plane number',
    'cam'       :  'Camera number',
    'LMin'      :  'Minimum intensity level',
    'LMax'      :  'Maximum intensity level',
    'yOriOff'   :  'Origin y shift',
    'xOriOff'   :  'Origin x shift',
    'yp'        :  'Maximum y limit',
    'ym'        :  'Minimum y limit',
    'xp'        :  'Maximum x limit',
    'xm'        :  'Minimum x limit',
}
check_tips={}
radio_tips={
    'ShowMask' : 'Show mask', 
}
line_edit_tips={}
button_tips={
    'findAll'   :  'Find points in all planes',
    'find'      :  'Find points in current plane',
    'copyGrid'  :  'Copy grid limits to all planes',
    'saveCoord' :  'Save point coordinates',
    'calibrate' :  'Calibration',
    'focusErr'  :  'Focus on max. error point',
    'deleteErr' :  'Deletion of max. error point',
    'zoom_minus':  'Zoom out',
    'zoom_equal':  'Reset zoom',
    'zoom_plus' :  'Zoom in',
    'restore'   :  'Restore intensity levels',
    'PlotMask'  :  'Plot mask',
}
combo_tips={}

class VISpar_CalVi(TABpar):
    FlagVis=True

    def __init__(self,Process=ProcessTypes.null,Step=StepTypes.null):
        self.setup(Process,Step)
        super().__init__('VISpar_CalVi','Vis_CalVi')
        self.unchecked_fields+=[]

    def setup(self,Process,Step):
        self.Process = Process
        self.Step = Step

        self.cfgName = cfgName
        self.FlagRunning = FlagRunning

        self.nPlane         = 0
        self.plane          = 1
        self.nCam           = 0
        self.cam            = 1
        self.defaultScaleFactor = 1.0
        self.scaleFactor    = 1.0
        self.scrollBarValues = [0,0]
        self.LLim           = 0
        self.LMin           = 0
        self.LMax           = 1

        self.MaskType       = 0
        self.DotDiam        = 0
        self.FlagShowMask   = True
        self.FlagPlotMask   = False

        #self.xOriOff        = 0
        #self.yOriOff        = 0
        #self.xm             = 0
        #self.xp             = 0
        #self.ym             = 0
        #self.yp             = 0

        self.orPosAndShift  = []
        self.angAndMask     = []
        self.spotDistAndRemoval = []
        
        self.imList = []
        self.imEx   = []
        self.splitterSizes   = [ ]

        self.FlagResetLevels = True
        self.FlagResetZoom   = True

        self.errorMessage=''

class Vis_Tab_CalVi(gPaIRS_Tab):
    class VIS_Tab_Signals(gPaIRS_Tab.Tab_Signals):
        run=Signal(bool)
        pass
    
    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        if not self.FlagInitVIS:
            self.FlagInitVIS=True
            S=self.scrollArea.size()
            s=self.calibView.pixmap().size()
            self.VISpar.scaleFactor = self.calibView.scaleFactor =min([S.width()/s.width() if s.width() else S.width(), S.height()/s.height() if s.height() else S.height()])
            self.calibView.resize(self.VISpar.scaleFactor * self.calibView.pixmap().size())
        return 
    
    def closeEvent(self,event):
        ''' called when closing 
        I had to add this to be sure that calib was destroyed'''
        
        #self.calibView.imageViewerThreadpool.clear()
        pri.Info.white("Vis_Tab_CalVi closeEvent")
        del self.calibView
    
    def resizeEvent(self,event):
        super().resizeEvent(event)
        self.setZoom()

    def __init__(self,parent: QWidget =None, flagInit= __name__ == "__main__"):
        super().__init__(parent,Ui_VisTab_CalVi,VISpar_CalVi)
        self.signals=self.VIS_Tab_Signals(self)

        #------------------------------------- Graphical interface: widgets
        self.TABname='Vis_CalVi'
        self.ui: Ui_VisTab_CalVi

        #necessary to change the name and the order of the items
        for g in list(globals()):
            if '_items' in g or '_ord' in g or '_tips' in g:
                #pri.Info.blue(f'Adding {g} to {self.name_tab}')
                setattr(self,g,eval(g))

        
        #introducing CalibView
        self.scrollArea = QtWidgets.QScrollArea(self)
        self.scrollArea.setObjectName('scroll_area_Vis_CalVi')
        self.scrollArea.setBackgroundRole(QtGui.QPalette.Dark)
        self.calibView=CalibView(self.scrollArea,self.outFromCalibView,self.outToStatusBarFromCalibView,self.textFromCalib,self.workerCompleted)
        self.scrollArea.setWidget(self.calibView)
        self.ui.Vis_CalVi_splitter.insertWidget(0,self.scrollArea)
        if __name__ == "__main__": 
            self.app=app
            setAppGuiPalette(self)

        #------------------------------------- Graphical interface: miscellanea
        self.ui.status_L.setText('')
        self.ui.status_R.setText('')
        self.FlagFirstShow=False
        self.setLogFont(fontPixelSize-dfontLog)

        #------------------------------------- Declaration of parameters 
        self.VISpar_base=VISpar_CalVi()
        self.VISpar:VISpar_CalVi=self.TABpar
        self.VISpar_old:VISpar_CalVi=self.TABpar_old        
        
        #------------------------------------- Callbacks 
        self.FlagInitVIS=False
        self.defineWidgets()
        self.setupWid()  #---------------- IMPORTANT

        self.defineCallbacks()
        self.spins_valueChanged=[self.ui.spin_plane,self.ui.spin_cam,
                                 self.ui.spin_xOriOff,self.ui.spin_yOriOff,
                                 self.ui.spin_ym,self.ui.spin_yp,
                                 self.ui.spin_xm,self.ui.spin_xp]
        self.connectCallbacks()
        self.defineFurtherCallbacks()
    
        self.defineSettings()

        self.adjustTABpar=self.adjustVISpar
        self.setTABlayout=self.setVISlayout
        
        self.FlagAddPrev=False
        
        self.calibView.flagCurrentTask=CalibTasks.stop #todo GP per me si deve cancellare è stato già fatto nell'init di CalibView
        
        self.bufferImg={}
        self.bufferSize=[]
        self.setRunButtonText=lambda: None

        self.FlagResume=0
        self.FlagInitData=False

        #------------------------------------- Initializing       
        if flagInit:
            self.initialize()

    def initialize(self):
        pri.Info.yellow(f'{"*"*20}   VIS initialization   {"*"*20}')

        if self.VISpar.cfgName:
            self.calibView.calib.cfgName=self.VISpar.cfgName
            flagOp=self.calibView.calib.readCfg()
            self.calibView.calib.readImgs() #todo verificare eventuali errori e dimensioni delle immagini in questo momento non da errore e l'img viene tagliata
            
            self.nullCallback('CalVi process')
            #self.adjustTABparInd()        
            self.runCalVi('_Mod' in self.VISpar.cfgName)
    
    @Slot(bool)
    def runCalVi(self,flagMod=False):
        self.FlagBridge=False
        self.calibView.flagFirstTask=CalibTasks.findPlanesFromOrigin if flagMod else CalibTasks.findAllPlanes
        self.VISpar.plane=self.VISpar.cam=1
        self.VISpar.FlagPlotMask=False
        if flagMod: self.ui.log.setText('')
        self.setTABlayout()
        if self.calibView.executeCalibTask(self.calibView.flagFirstTask):
            self.setTaskButtonsText()
            #self.resetScaleFactor()

    def stopCalVi(self):
        self.calibView.executeCalibTask(CalibTasks.stop)
        self.setTaskButtonsText()
        self.gui.ui.button_Run_CalVi.setVisible(True)
        self.setTABlayout()
        self.FlagBridge=True  
        self.adjustTABparInd()      

    def show(self):
        super().show()
        if not self.FlagFirstShow:
            self.FlagFirstShow=True
            self.resetScaleFactor()
            self.setVISlayout()

    def defineFurtherCallbacks(self):
        self.ui.Vis_CalVi_splitter.addfuncout['setScrollAreaWidth']=self.wrappedCallback('Splitter sizes',self.splitterMoved)

        self.taskButtons=[self.ui.button_findAll,
                          self.ui.button_find,
                          self.ui.button_calibrate,
                          self.ui.button_saveCoord,
                          ]
        self.taskButtons_actions=[]
        def create_taskButton_action(ind,k):
            def taskButton_action(ind,k):
                FlagSettingPar=TABpar.FlagSettingPar
                TABpar.FlagSettingPar=True
                self.taskButtonPressed(CalibTasks(ind),k!=3)
                TABpar.FlagSettingPar=FlagSettingPar
            return self.wrappedCallback('CalVi task',lambda: taskButton_action(ind,k))
        for k,ind in enumerate([f.value for f in CalibTasks if f.value>0]):
            self.taskButtons_actions.append(create_taskButton_action(ind,k))
            self.taskButtons[k].clicked.connect(self.taskButtons_actions[k])

        self.buttonsToDisableNotCalibrated=[] #used to gray buttons if not calibrated
        self.functionButtons=[
                              self.ui.button_deleteErr,
                              self.ui.button_focusErr,
                              self.ui.button_copyGrid,
                              ]
        self.functionButtons_actions=[]
        def create_functionButton_action(ind):
            def functionButton_action(ind):
                FlagSettingPar=TABpar.FlagSettingPar
                TABpar.FlagSettingPar=True
                self.functionButtonPressed(CalibFunctions(ind),True)
                TABpar.FlagSettingPar=FlagSettingPar
            return self.wrappedCallback('CalVi function',lambda: functionButton_action(ind))
        for k,ind in  enumerate([f.value for f in CalibFunctions if f.value>0]):
            self.functionButtons_actions.append(create_functionButton_action(ind))
            self.functionButtons[k].clicked.connect(self.functionButtons_actions[k])
            self.buttonsToDisableNotCalibrated.append(self.functionButtons[k])

        functionButtons_insert=[0,0,0]
        for k,ind in  enumerate([f.value for f in CalibFunctions]):
            action=QAction(self.functionButtons[k].icn,calibFunctionsText[abs(ind)],self)
            self.calibView.contextMenuActions.insert(functionButtons_insert[k],action)
            action.triggered.connect(create_functionButton_action(ind))
            if ind>0:
                self.buttonsToDisableNotCalibrated.append(action)

        self.originOffbox=self.ui.g_OriOff
        self.remPoinsBox=self.ui.g_GriLim
        self.buttonsToDisable=[
                              self.ui.spin_plane,
                              self.originOffbox,
                              self.remPoinsBox,
                             ] #used to gray buttons when calibrating
    
    def setLogFont(self,fPixSize):
        logfont=self.ui.log.font()
        logfont.setFamily('Courier New')
        logfont.setPixelSize(fPixSize)
        self.ui.log.setFont(logfont)

#********************************************* Adjusting parameters
    def adjustVISpar(self):
        self.calibView.hide()
        
        FlagNewRun=self.VISpar.isDifferentFrom(self.VISpar_old,fields=['FlagRunning'])
        if FlagNewRun: 
            self.defaultSplitterSize()

        FlagNewSet=False
        INP_CalVi:INPpar_CalVi = self.gui.w_Input_CalVi.TABpar
        PRO_CalVi:PROpar_CalVi = self.gui.w_Process_CalVi.TABpar
        if PRO_CalVi.isDifferentFrom(self.gui.w_Process_CalVi.PROpar_old,exceptions=['ind']) or INP_CalVi.isDifferentFrom(self.gui.w_Input_CalVi.INPpar_old,exceptions=['ind']) or not self.FlagInitData: 
            FlagNewSet=True
            self.gui.initDataAndSetImgFromGui(INP_CalVi,PRO_CalVi)

        #***Data
        c=self.calibView.calib
        self.VISpar.nPlane=c.nPlanesPerCam
        self.VISpar.nCam=c.nCams
        if self.VISpar.plane and not self.VISpar.nPlane: self.VISpar.plane=0
        elif not self.VISpar.plane and self.VISpar.nPlane: self.VISpar.plane=self.VISpar.nPlane
        if self.VISpar.cam and not self.VISpar.nCam: self.VISpar.cam=0
        elif not self.VISpar.cam and self.VISpar.nCam: self.VISpar.cam=self.VISpar.nCam

        self.VISpar.MaskType=abs(self.calibView.calib.cal.data.FlagPos)
        if self.VISpar.MaskType in (2,3):
            #self.VISpar.FlagShowMask=False
            self.VISpar.FlagPlotMask=False
        #if not self.VISpar.FlagShowMask: self.VISpar.FlagPlotMask=False
        self.VISpar.DotDiam=abs(self.calibView.calib.cal.data.raggioInizialeRicerca)
        self.calibView.calib.flagShowMask=self.VISpar.FlagShowMask
        self.calibView.calib.flagPlotMask=self.VISpar.FlagPlotMask

        #***Levels
        FlagPlot=False
        FlagPlotMask=self.VISpar.isDifferentFrom(self.VISpar_old,fields=['FlagPlotMask'])
        if FlagPlotMask: 
            FlagPlot=True
            self.plotPlane()
        if self.VISpar.FlagResetLevels or FlagNewRun or FlagNewSet: #or FlagPlotMask:
            if not FlagPlot: 
                FlagPlot=True
                self.plotPlane()
            self.restoreLevels()
            #self.VISpar.FlagResetLevels=False            
        self.VISpar.LLim=c.LLim
        if self.VISpar.FlagResetLevels: 
            self.VISpar.LMin=c.LMin
            self.VISpar.LMax=c.LMax
        else:
            self.VISpar.LMax=c.LMax if self.VISpar.LMax>c.LLim else self.VISpar.LMax
            self.VISpar.LMin=self.VISpar.LMax-1 if self.VISpar.LMin >self.VISpar.LMax-1 else self.VISpar.LMin
        self.calibView.calib.LMin=self.VISpar.LMin
        self.calibView.calib.LMax=self.VISpar.LMax
        self.VISpar.FlagResetLevels=False
        
        #***Zoom
        if self.VISpar.FlagResetZoom or FlagNewRun or FlagPlotMask or FlagNewSet:
            if not FlagPlot: 
                FlagPlot=True
                self.plotPlane()
            self.resetScaleFactor()
        self.calibView.scaleFactor=self.VISpar.scaleFactor
        self.VISpar.FlagResetZoom=False
        
    def defaultSplitterSize(self):
        self.VISpar.splitterSizes=[self.width()-self.ui.w_Commands.minimumWidth(),self.ui.w_Commands.minimumWidth()]
        
#********************************************* Layout
    def setVISlayout(self):
        self.calibView.hide()

        FlagImg=len(self.calibView.calib.imgs)>0
        self.ui.g_Image.setEnabled(FlagImg)
        self.ui.spin_plane.setEnabled(FlagImg and self.VISpar.nPlane>1)
        self.ui.spin_cam.setEnabled(FlagImg and self.VISpar.nCam>1)

        FlagMask=self.VISpar.MaskType not in (2,3) and len(self.calibView.calib.ccMask)>0
        self.ui.g_Mask.setVisible(FlagMask)

        FlagZoomLevels=FlagImg or FlagMask
        self.ui.g_Zoom.setEnabled(FlagZoomLevels)
        self.ui.g_Levels.setEnabled(FlagZoomLevels)
        
        self.ui.button_PlotMask.setEnabled(self.VISpar.MaskType not in (2,3))
        
        self.ui.w_Commands.setVisible(self.VISpar.FlagRunning)
        if self.VISpar.FlagRunning:
            self.calibView.contextMenu = QtWidgets.QMenu(self)
            for a in self.calibView.contextMenuActions:
                self.calibView.contextMenu.addAction(a)
            self.calibView.contextMenu.insertSeparator(self.calibView.contextMenuActions[1])
        else:
            self.calibView.contextMenu =None
            
        self.setSpinMaxMin()
        self.ui.Vis_CalVi_splitter.setSizes(self.VISpar.splitterSizes)
        
        self.calibView.scaleFactor=self.VISpar.scaleFactor
        self.calibView.calib.LMin=self.VISpar.LMin
        self.calibView.calib.LMax=self.VISpar.LMax
        self.calibView.calib.flagShowMask=self.VISpar.FlagShowMask
        self.calibView.calib.flagPlotMask=self.VISpar.FlagPlotMask
        
        FlagNoImage=True
        if self.VISpar.cam>0 and self.VISpar.plane>0:
            if self.VISpar.nCam==len(self.VISpar.imEx):
                TargetType=self.gui.w_Process_CalVi.PROpar.TargetType
                nPlane=self.VISpar.nPlane/(1+TargetType)
                if nPlane==len(self.VISpar.imEx[0]):
                    plane=int( (self.VISpar.plane+TargetType)/(1+TargetType) )
                    if self.VISpar.imEx[self.VISpar.cam-1][plane-1]:
                        FlagNoImage=False
        if FlagNoImage:
            self.ui.status_R.setText('')
            self.ui.status_L.setText('')
            self.calibView.hide()
        else:   
            if self.VISpar_old.FlagRunning!=self.VISpar.FlagRunning or (self.VISpar.nPlane>0 and self.VISpar_old.nPlane==0):
                self.plotPlane()
                self.button_zoom_equal_action()
            self.setZoom()
            self.plotPlane()
            self.calibView.show()
            if not self.VISpar.FlagInit:
                self.button_zoom_equal_action()
        self.setRunButtonText()
        return

    def setSpinMaxMin(self):
        self.ui.spin_plane.setMinimum(1*bool(self.VISpar.nPlane))
        self.ui.spin_plane.setMaximum(self.VISpar.nPlane)
        self.ui.spin_cam.setMinimum(1*bool(self.VISpar.nCam))
        self.ui.spin_cam.setMaximum(self.VISpar.nCam)

        self.ui.spin_LMin.setMinimum(-self.VISpar.LLim)
        self.ui.spin_LMin.setMaximum(self.VISpar.LMax-1)
        self.ui.spin_LMax.setMinimum(self.VISpar.LMin+1)
        self.ui.spin_LMax.setMaximum(self.VISpar.LLim)

#********************************************* Zoom
#******************** Actions
    def button_zoom_minus_action(self):
        self.zoom(0.8)
        return
    
    def button_zoom_equal_action(self):
        self.resetScaleFactor()
        self.zoom(1.0)
        return
    
    def button_zoom_plus_action(self):
        self.zoom(1.25)
        return

    def zoom(self,zoom):
        ''' zooms f a factor zoom if negative reset to no zoom '''
        if zoom<=0:
            zoom = self.calibView.scaleFactor = 1.0
        self.zoomImage(zoom)
  
    def zoomImage(self, zoom):
        ''' zooms the image of self.CalibView.scaleFactor times a factor zoom
        adjust also the scrollBars'''
        self.calibView.scaleFactor *= zoom
        self.VISpar.scaleFactor=self.calibView.scaleFactor
        self.VISpar.scrollBarValues[0]=self.adjustedScrollBarValue(self.scrollArea.horizontalScrollBar(), zoom)
        self.VISpar.scrollBarValues[1]=self.adjustedScrollBarValue(self.scrollArea.verticalScrollBar(), zoom)
    
    def adjustedScrollBarValue(self, scrollBar:QScrollBar, factor):
        ''' adjust the position when zooming in or out ''' 
        return int(factor * scrollBar.value() + ((factor - 1) * scrollBar.pageStep()/2))
    
    def splitterMoved(self):
        self.calibView.resetScaleFactor(self.scrollArea.size())
        self.VISpar.defaultScaleFactor=self.calibView.scaleFactor
        self.VISpar.splitterSizes=self.ui.Vis_CalVi_splitter.sizes()

#******************** Settings
    def setZoom(self):
        #self.calibView.show()
        self.calibView.resize(self.VISpar.scaleFactor * self.calibView.pixmap().size())
        self.scrollArea.horizontalScrollBar().setValue(self.VISpar.scrollBarValues[0])
        self.scrollArea.verticalScrollBar().setValue(self.VISpar.scrollBarValues[1])

#******************** Adjusting
    def resetScaleFactor(self):
        ''' reset the scale factor so that the image perfectly feet the window'''
        self.calibView.resetScaleFactor(self.scrollArea.size())
        self.VISpar.defaultScaleFactor=self.VISpar.scaleFactor=self.calibView.scaleFactor
        self.VISpar.scrollBarValues=[0,0]

#********************************************* Levels
#******************** Actions
    def button_restore_action(self):
        self.VISpar.FlagResetLevels=True
        
#******************** Adjusting
    def restoreLevels(self):
        pc=self.VISpar.plane-1
        c=self.VISpar.cam-1
        p=pc+c*self.calibView.calib.nPlanesPerCam
        c=self.calibView.calib
        c.setLMinMax(p)

#********************************************* Mask
#******************** Actions
    def button_PlotMask_action(self):
        self.VISpar.FlagPlotMask=self.ui.button_PlotMask.isChecked()
        
#******************** Settings
    def button_PlotMask_set(self):
        self.ui.button_PlotMask.setChecked(self.VISpar.FlagPlotMask)
        
#********************************************* Plot
#******************** Layout
    def plotPlane(self):
        pc=self.VISpar.plane-1
        c=self.VISpar.cam-1
        p=pc+c*self.calibView.calib.nPlanesPerCam
        self.calibView.plotPlane(p)

#********************************************* Parameters
#******************** Actions
    def spin_OriOff_action(self,spin:QSpinBox,flagX):
        self.focusOnTarget()
        Off=spin.value()
        if spin.hasFocus():
            self.calibView.spinOriginChanged(Off,spin,flagX,flagPlot=False)

    def spin_xOriOff_action(self):
        self.spin_OriOff_action(self.ui.spin_xOriOff,True)

    def spin_yOriOff_action(self):
        self.spin_OriOff_action(self.ui.spin_yOriOff,False)

    def spin_remPoi_action(self,spin:QSpinBox,flagX,flagPos):
        self.focusOnTarget()
        Off=spin.value()
        if spin.hasFocus():
            self.calibView.spinRemPoints(Off,spin,flagX,flagPos)
    
    def spin_ym_action(self):
        self.spin_remPoi_action(self.ui.spin_ym,flagX=False,flagPos=False)
    
    def spin_yp_action(self):
        self.spin_remPoi_action(self.ui.spin_yp,flagX=False,flagPos=True)

    def spin_xm_action(self):
        self.spin_remPoi_action(self.ui.spin_xm,flagX=True,flagPos=False)

    def spin_xp_action(self):
        self.spin_remPoi_action(self.ui.spin_xp,flagX=True,flagPos=True)

    def button_copyGrid_action(self):
        self.focusOnTarget()
        self.calibView.copyRemPoints()
    
    def focusOnTarget(self):
        self.VISpar.FlagPlotMask=False

#********************************************* CalibView function
    def outFromCalibView(self,out:str):
        ''' output From CalibView called from plotImg'''
        calib=self.calibView.calib
        da=calib.cal.vect
        p=calib.plane
        c=int(p/calib.nPlanesPerCam)
        pc=p-c*calib.nPlanesPerCam
        
        FlagSettingPar=TABpar.FlagSettingPar
        TABpar.FlagSettingPar=True
        self.VISpar.plane=pc+1
        self.VISpar.cam=c+1
        self.ui.spin_cam.setValue(c+1)
        self.ui.spin_plane.setValue(pc+1)
        
        self.ui.spin_xOriOff.setValue(da.xOrShift[p])
        self.ui.spin_yOriOff.setValue(da.yOrShift[p])

        self.ui.spin_xm.setValue(da.remPointsLe[p])
        self.ui.spin_xp.setValue(da.remPointsRi[p])
        self.ui.spin_ym.setValue(da.remPointsDo[p])
        self.ui.spin_yp.setValue(da.remPointsUp[p])
        TABpar.FlagSettingPar=FlagSettingPar

        if self.VISpar.FlagPlotMask:
            out2=' [CC mask]'
        else:
            out2=' [target image]'
        self.ui.status_R.setText(out+out2)
        self.calibView.setStatusTip(out+out2)

    def outToStatusBarFromCalibView(self,out:str):
        ''' output to status bar From CalibView '''
        self.ui.status_L.setText(out)
        #self.calibView.setToolTip(out)

    Slot(str)
    def textFromCalib(self,out:str):
        ''' set single line text from calib'''
        
        #print(f'textFromCalib  {out}')
        self.ui.log.setText(out)

    def workerCompleted(self,flagError):
        ''' called when worker has completed '''
        if flagError:
            warningDialog(self,'An error occurred during calibration!\n\nPlease, restart the procedure manually.')
        if  not self.calibView.flagCurrentTask is CalibTasks.stop:# pylint: disable=unneeded-not
            if self.calibView.executeCalibTask(CalibTasks.stop):
                self.setTaskButtonsText()

    def setTaskButtonsText(self):
        ''' set all the button texts and enable/disable them '''
        flagEnab=True if (self.calibView.flagCurrentTask==CalibTasks.stop) else False
        for f in  [f for f in CalibTasks if f.value>0]:
            if flagEnab:  # stop the process -> enable all buttons and restore text
                self.taskButtons [f.value-1].setText(calibTasksText[f.value])
                self.taskButtons [f.value-1].setEnabled(True)
            else:
                if self.calibView.flagCurrentTask is f: 
                    self.taskButtons [f.value-1].setText(calibTasksText[0])
                else:
                    self.taskButtons [f.value-1].setEnabled(False)
        for b in self.buttonsToDisable:
            b.setEnabled(flagEnab)
        for b  in  self.buttonsToDisableNotCalibrated:      
            b.setEnabled(self.calibView.calib.cal.flagCalibrated)    
        self.setRunCalViButtonLayout()
        #for b in self.functionButtons:      b.setEnabled(flagEnab)
        #pri.Callback.green('-----abcde----- TaskButtonsText -----abcde-----')
   
    def taskButtonPressed(self,flag:CalibTasks,flagFocus):
        ''' one of the button has been  pressed '''
        if flagFocus: self.focusOnTarget()
        if self.calibView.executeCalibTask(flag):
            self.setTaskButtonsText()
        #pri.Callback.green('-----xxxxx----- taskButtonPressed -----xxxxx-----')
   
    def functionButtonPressed(self,flag:CalibTasks,flagFocus):
        ''' one of the button has been  pressed '''
        if flagFocus: self.focusOnTarget()
        self.calibView.executeCalibFunction(flag)  
        #pri.Callback.green('-----|||||----- functionButtonPressed -----|||||-----')

#********************************************* Spin callbacks
    def setImgFromGui(self):
        inddel=[]
        calib=self.calibView.calib    
        calib.imgs=[]
        calib.ccMask=[]
        flagFirstImage=True
        npType=np.uint16

        data=calib.cal.data
        Him=data.ImgH
        Wim=data.ImgW
        if self.VISpar.imList: #only used to read the first image and fix the img dimensions
            for imListc,imExc in zip(self.VISpar.imList,self.VISpar.imEx):
                for k,f in enumerate(imListc):
                    ex=imExc[k]=os.path.exists(f)
                    if ex:
                        if f not in self.bufferImg:
                            try:
                                im=Image.open(f)
                                da=np.array(im,dtype=npType)
                                if len(da.shape)!=2:
                                    self.bufferImg[f]=da=None
                                    raise(f'Error: the image file: {f} seems not to be grayscale!')
                                else:
                                    self.bufferImg[f]=da
                            except:
                                pri.Error.red(f'Error while opening the image file: {f}.\n{traceback.format_exc()}\n')
                                self.bufferImg[f]=da=None
                        else:
                            da=self.bufferImg[f]
                        if flagFirstImage and da is not None:
                            Him,Wim=da.shape
                            flagFirstImage=False
                            break
                if not flagFirstImage: break        
        if self.VISpar.imList: #reading the images 
             for imListc,imExc in zip(self.VISpar.imList,self.VISpar.imEx):
                k=-1
                for f,ex in zip(imListc,imExc):
                    k+=1
                    if f not in self.bufferImg:
                        if ex:
                            try:
                                im=Image.open(f)
                                da=np.array(im,dtype=npType)
                                if len(da.shape)!=2:
                                    da=None
                                    raise(f'Error: the image file: {f} seems not to be grayscale!')
                            except:
                                pri.Error.red(f'Error while opening the image file: {f}.\n{traceback.format_exc()}\n')
                                da=None
                        else:
                            da=np.zeros((Him,Wim),dtype=npType)
                        self.bufferImg[f]=da
                    else:
                        da=self.bufferImg[f]
                    if da is None:
                        inddel.append(k)
                        continue
                    h,w=da.shape
                    if (Wim,Him)!=(w,h):
                        inddel.append(k)
                    calib.imgs.append(np.ascontiguousarray(da[data.RigaPart:data.RigaPart+data.ImgH,data.ColPart:data.ColPart+data.ImgW],dtype=npType))
                    if data.TipoTarget:
                        calib.imgs.append(np.ascontiguousarray(da[data.RigaPart:data.RigaPart+data.ImgH,data.ColPart:data.ColPart+data.ImgW],dtype=npType))

                
        self.bufferSize=0
        for f in self.bufferImg:#deleting buffer if to big
            a:np.ndarray=self.bufferImg[f]
            if a is not None:
                self.bufferSize+=a.size*a.itemsize
        if self.bufferSize>bufferSizeLimit:
            imgList=list(self.bufferImg)
            k=0
            while self.bufferSize>bufferSizeLimit and len(imgList) and imgList[k] not in self.VISpar.imList: 
                f=imgList[k]
                a=self.bufferImg[f]
                self.bufferSize-=a.size*a.itemsize
                self.bufferImg.pop(f)
                imgList.pop(k)

        if calib.imgs:        
            calib.cal.setImgs(calib.imgs)
            calib.ccMask=calib.cal.getMask()
            pass
        return inddel

    def initDataFromGui(self,INP:INPpar_CalVi,PRO:PROpar_CalVi):
        #FlagNewImages=self.VISpar.imList!=INP.imList or self.VISpar.imEx!=INP.imEx
        #if not FlagNewImages: return FlagNewImages
        self.VISpar.imList=copy.deepcopy(INP.imList)
        self.VISpar.imEx=copy.deepcopy(INP.imEx)
        calib=self.calibView.calib
        calib.cal.DefaultValues()
        calib.FlagCalibration=False
        
        self.FlagResume=0
        #-------------------------------------- %
        #            Not in cfg             %
        # --------------------------------------%

        data=calib.cal.data
        calVect=calib.cal.vect
        data.PercErrMax = 0.1                # 0.10 Percentuale massima per errore in posizioneTom da modificare 
        # InitParOptCalVi(&dati->POC); #todo

        #-------------------------------------- %
        #            Input and Output parameters             %
        # --------------------------------------%
        data.percorso = INP.path     #percorso file di input
        data.EstensioneIn = INP.ext #estensione in (b16 o tif)
        data.FlagCam=0 if INP.FlagCam else 1    
        data.percorsoOut = INP.path_out # percorso file di output
        data.NomeFileOut = INP.root_out # nome file di output

        camString=''
        cams=INP.cams
        if INP.FlagCam:
            if len(cams)==1: camString=f'_cam{cams[0]}'
        else:
            cams=[-1]
        calib.cfgName=f'{data.percorsoOut}{data.NomeFileOut}{camString}.cfg'
        data.NCam = len(cams) if INP.FlagCam else 1 # Numero di elementi nel vettore cam (numero di camere da calibrare)

        if self.VISpar.FlagRunning:
            varName=f'{data.percorsoOut}{data.NomeFileOut}{camString}{outExt.calvi}'
            if os.path.exists(varName):
                try:
                    with open(varName, 'rb') as file:
                        try:
                            var=pickle.load(file)
                        except:
                            self.FlagResume=-1
                        else:
                            self.FlagResume=1 if INP.isEqualTo(var[0],exceptions=TABpar().fields,fields=['cams','filenames','x','y','w','h','W','H']) else -1
                            INP.printDifferences(var[0])
                            #PRO.printDifferences(var[1])
                            if self.FlagResume>0:
                                self.VISpar.copyfrom(var[2],TABpar().fields+['FlagRunning'])
                except:
                    self.FlagResume=-1
                    pri.Error.red(f'Error while restoring the previous calibration process file: {varName}.\n{traceback.format_exc()}\n')

        #-------------------------------------- %
        #            Distance between spots                     %
        # --------------------------------------%
        data.pasX = PRO.DotDx            # passo della griglia lungo X
        data.pasY = PRO.DotDy            # passo della griglia lungo Y

        #-------------------------------------- %
        #            Calibration parameters                     %
        # --------------------------------------%
        data.Threshold = PRO.DotThresh    # valore percentuale della soglia
        data.FlagPos = (2*bool(PRO.DotColor)-1)*([0,3,4,5,1,2][PRO.DotTypeSearch]+1)            # Tipo ricerca pallino 1 CC 2 Interp 3 geom Positivi pallini bianchi negativi pallini neri 4 e 5 TopHat piu gaussiana 6 gaussiana
        #Cal = (TipoCal >> CalFlags.SHIFT) & CalFlags.MASK;
        #Cyl = (TipoCal >> CalFlags.SHIFT_CYL) & CalFlags.MASK;
        data.raggioInizialeRicerca=int(PRO.DotDiam*2.5)
        calType=PRO.CalibProcType
        F_Ph=int(PRO.FlagPinhole)
        F_Pl=int(PRO.FlagPlane)
        F_Sa=int(PRO.FlagSaveLOS)
        P_Cyl=PRO.CorrMod_Cyl
        P_Ph=0
        data.TipoCal=calib.toTipoCal(calType,F_Ph,F_Pl,F_Sa,P_Cyl,P_Ph) # Calibration type [Type F_Ph F_Pl F_Sa P_Cyl P_Ph] 	

        #-------------------------------------- %
        #                        Image Parameters                     %
        # --------------------------------------%
        data.ImgW=INP.w
        data.ImgH=INP.h
        data.ColPart=INP.x
        data.RigaPart=INP.y

        #-------------------------------------- %
        #                     Target parameters                     %
        # --------------------------------------%
        data.TipoTarget = PRO.TargetType # Tipo di target 0 normale singolo piano 1 doppio piano con dx dy sfalsato al 50%)
        data.dx = PRO.OriginXShift                 # TipoTarget==1 sfasamento fra i piani target altirmenti non utlizzato
        data.dy = PRO.OriginYShift                 # TipoTarget==1 sfasamento fra i piani target altirmenti non utlizzato
        data.dz = PRO.OriginZShift                # TipoTarget==1 distanza fra i piani target altirmenti non utlizzato
        if data.TipoTarget==0:            data.dx = data.dy = data.dz = 0
        data.Numpiani_PerCam=len(INP.filenames)*(data.TipoTarget+1) # numero di piani da calibrare per camera in caso di target doppio piano inserire 2 * numero di spostamenti target
        data.Numpiani = data.NCam * data.Numpiani_PerCam

        if len(INP.filenames) <1 : #when initializing the filenames are not known
            calib.nCams=0
            calib.cams=[]
            calib.nPlanes=0
            calib.nPlanesPerCam=0
            self.VISpar.nPlane=calib.nPlanesPerCam
            self.VISpar.nCam=calib.nCams
            return

        CamModType=[1,2,3,10,30][PRO.CamMod]
        if CamModType in (1,2,3):
            modPar=[PRO.XDeg,PRO.YDeg,PRO.ZDeg]
        elif CamModType==10:
            CamModType+=[0,2,4][PRO.CorrMod]
            modPar=[PRO.PixAR,PRO.PixPitch]
        elif CamModType==30:
            CamModType+=[0,2,4,5,6,7,8][PRO.CorrMod]
            modPar=[PRO.PixAR,PRO.PixPitch,PRO.CylRad,PRO.CylThick,PRO.CylNRatio]
        additionalPar=[CamModType]+modPar     # Calibration type and parameters 	(12)    

        calib.cal.allocAndinit(additionalPar,0)
        for i,c in enumerate (cams):
            calVect.cam[i]=c

        # -------------------------------------- %
        #             Plane img name and coordinates     %
        # -------------------------------------- %
        imgRoot=[]
        for f in INP.filenames:
            if data.FlagCam==0:
                imgRoot.append(os.path.splitext(f)[0].replace('_cam*',''))
            else:
                imgRoot.append(os.path.splitext(f)[0])

        
        if calType:
            z=[0.0]*len(INP.plapar)
            costPlanes=INP.plapar
        else:
            z=[p[-1] for p in INP.plapar]
            costPlanes=[[0.0]*5+[zk] for zk in z]
        if data.TipoTarget==1:
            for k in range(len(INP.filenames)):
                k2=k*2+1
                imgRootk=imgRoot[2*k]
                imgRoot.insert(k2,imgRootk)
                zk=z[2*k]
                z.insert(k2,zk+data.dz)
                cP=costPlanes[2*k]
                cP2=[c for c in cP]
                cP2[-1]+=data.dz
                costPlanes.insert(k2,cP2)
            pass

        
        for p1 in range(data.Numpiani_PerCam):
            for c in range(data.NCam):
                p=p1+c*data.Numpiani_PerCam
                calib.cal.setImgRoot(p,imgRoot[p1])
                calVect.z[p]    = z[p1]

                if self.FlagResume<=0:
                    calVect.XOr[p] = calVect.YOr[p]  = calVect.angCol[p]  = calVect.angRow[p]  = calVect.xOrShift[p] = calVect.yOrShift[p] = 0
                    calib.cal.setPuTrovaCC([0,0,0,0],p)
                    calVect.dColPix[p] =calVect.dRigPix[p] = 10000 #not really important but has to be big
                    calVect.remPointsUp[p] = calVect.remPointsDo[p] = calVect.remPointsLe[p] = calVect.remPointsRi[p] = 0
                else:
                    calVect.XOr[p]  = self.VISpar.orPosAndShift[p][0] + data.ColPart
                    calVect.YOr[p]  = self.VISpar.orPosAndShift[p][1] + data.RigaPart
                    calVect.angCol[p]  = self.VISpar.angAndMask[p][0]
                    calVect.angRow[p]  = self.VISpar.angAndMask[p][1]

                    calVect.xOrShift[p] = round(self.VISpar.orPosAndShift[p][2])
                    calVect.yOrShift[p] = round(self.VISpar.orPosAndShift[p][3])

                    self.calibView.calib.cal.setPuTrovaCC(self.VISpar.angAndMask[p][2:],p)
                    #calVect.flagPlane[p]|= PaIRS_lib.CalFlags.PLANE_NOT_INIT_TROVA_PUNTO|PaIRS_lib.CalFlags.PLANE_NOT_FOUND
                    #self.cal.getPuTrovaCC(p)
                    calVect.dColPix[p] = round(self.VISpar.spotDistAndRemoval[p][0])
                    calVect.dRigPix[p] = round(self.VISpar.spotDistAndRemoval[p][1])
                    #self.cal.calcBounds(p)
                    calVect.remPointsUp[p] = round(self.VISpar.spotDistAndRemoval[p][2])
                    calVect.remPointsDo[p] = round(self.VISpar.spotDistAndRemoval[p][3])
                    calVect.remPointsLe[p] = round(self.VISpar.spotDistAndRemoval[p][4])
                    calVect.remPointsRi[p] = round(self.VISpar.spotDistAndRemoval[p][5])
            
                
            if calType!=0: #no standard calibration    planes involved
                calVect.costPlanes[p1]=costPlanes[p1]
        calib.cal.allocAndinit(additionalPar,1)
        errorFiles=[[],[]]
        if calType >= 2:# Calibrazione piano per controllo     Legge le costanti di calibrazione
            # si devono leggere o passare le costanti di calibrazione
            for cam in range(data.NCam):
                buffer=f'{data.percorso}{data.NomeFileOut}{abs(calVect.cam[cam])}.cal'
                if os.path.exists(buffer):
                    try:
                        calib.readCalFile(buffer,calVect.cost[cam],data.NumCostCalib,CamModType)
                    except Exception as inst:
                        errorFiles[1].append(f'{os.path.basename(buffer)} ({inst})')
                else:
                    errorFiles[0].append(f'{os.path.basename(buffer)}')
        errorMessage=''
        if len(errorFiles[0]) or len(errorFiles[1]):
            errorMessage='Error while initialising the calibration process.\n\n'
            if len(errorFiles[0]):
                errList=f";\n   ".join(errorFiles[0])
                errorMessage+=f'The following files do not exist in the specified path ({data.percorso}):\n   {errList}.\n\n'         
            if len(errorFiles[1]):
                errList=f";\n   ".join(errorFiles[1])
                errorMessage+=f'There were errors with opening the following files in the specified path ({data.percorso}):\n   {errList}.'         
            #pri.Error.blue(errorMessage)
        self.VISpar.errorMessage=errorMessage

        calib.cal.allocAndinit(additionalPar,2)

        pri.Process.yellow(f'TipoCal = [{calType} {F_Ph} {F_Pl} {F_Sa} {P_Cyl} {P_Ph}]')
        pri.Process.yellow(f'initDataFromGui:     additionalPar={additionalPar}')
        pri.Process.yellow(f'initDataFromGui:     plapar={INP.plapar},     z={z}')
        pri.Process.yellow(f'initDataFromGui:     calVect.z={calVect.z}')


        calib.nCams=calib.cal.data.NCam
        calib.cams=calib.cal.getCams()
        calib.nPlanes=calib.cal.data.Numpiani

        calib.nPlanesPerCam=calib.cal.data.Numpiani_PerCam
        self.VISpar.nPlane=calib.nPlanesPerCam
        self.VISpar.nCam=calib.nCams
        self.FlagInitData=True
        return
    
    def setRunCalViButtonLayout(self):
        if self.gui:
            FlagVisible=True
            calib=self.calibView.calib
            calVect=calib.cal.vect
            FlagVisible=all([not bool(p) for p in calVect.flagPlane[:-1]])
            self.gui.ui.button_Run_CalVi.setVisible(FlagVisible)

        
    

if __name__ == "__main__":
    import sys
    app=QApplication.instance()
    if not app:app = QApplication(sys.argv)
    app.setStyle('Fusion')
    object = Vis_Tab_CalVi(None)
    object.show()
    app.exec()
    app.quit()
    app=None
''' CalibView '''
# pylint: disable=pointless-string-statement, too-many-instance-attributes, no-name-in-module, multiple-imports
# pylint: disable= import-error 
# pylint: disable=multiple-statements,c-extension-no-member
import sys, traceback
from typing import Callable
from enum import Enum
#import faulthandler # per capire da dove vengono gli errori c
import platform

from PySide6 import QtCore, QtGui, QtWidgets

from PySide6.QtCore import  Slot, QThreadPool, QObject, Signal, QRunnable
from PySide6.QtWidgets import  QLabel  #,QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtWidgets import  QSpinBox  #,QApplication, QPushButton

from PIL import Image, ImageQt
import numpy as np


from .calib import Calib, CalibTasks, TYPE_ERR_STOP, CalibFunctions


try: 
  from .PaIRS_pypacks import pri, Flag_DEBUG_PARPOOL # type: ignore per ignorare il warning dy pylance
  flagImageViewer=0
except ModuleNotFoundError as exc:  
  from .tAVarie import pri
  flagImageViewer=1
  Flag_DEBUG_PARPOOL=0 # pylint: disable=invalid-name
if Flag_DEBUG_PARPOOL:
  import debugpy # pylint: disable=unused-import #nel caso mettere nel thread debugpy.debug_this_thread()
  
#faulthandler.enable() # per capire da dove vengono gli errori c
if __package__ or "." in __name__:
  import PaIRS_UniNa.PaIRS_PIV as PaIRS_lib # pylint: disable=unused-import
  from PaIRS_UniNa.PaIRS_PIV import Punto
  from PaIRS_UniNa.PaIRS_PIV import CalFlags
else:
  if platform.system() == "Darwin":
    sys.path.append('../lib/mac')
  else:
    #sys.path.append('PaIRS_PIV')
    sys.path.append('../lib')
  import PaIRS_PIV as PaIRS_lib # pylint: disable=unused-import # type: ignore
  from PaIRS_PIV import Punto # type: ignore
  from PaIRS_PIV import CalFlags # type: ignore


class CircleType(Enum):
  circle = 1 # pylint: disable=invalid-name
  square= 2  # pylint: disable=invalid-name
  filledCircle=3 # pylint: disable=invalid-name

mainInCircleColors=['#ff0000', '#ff00ff','#0000ff']
foundCircleColor='#ff0000'
maxErrorCircleColor='#ffff00'
OriginCircleColor='#00ff00'
mainInCircleType=[CircleType.circle, CircleType.square,CircleType.circle]
rFoundCircle=5
rInpCircle=15
penWidth=2
percLunFreccia=0.25#lunghezza testa      
lunFreccia=100#scalatura freccia
angFreccia=30*np.pi/180 
tanFreccia=percLunFreccia*np.tan(angFreccia)
    
class    Circle():
  def __init__(self,x,y,r:int=rInpCircle,col:str=foundCircleColor,ty:CircleType=CircleType.filledCircle):#'#EB5160'
    self.r=r
    self.col=col
    self.type=ty
    self.xe=x
    self.ye=y
    self.x=x
    self.y=y
  @classmethod
  def fromPunto(cls, pu:Punto,r:int=5,col:str=foundCircleColor,ty:CircleType=CircleType.circle)->Punto:
      ''' retrun a circle from a Punto'''
      return cls(pu.x,pu.y,r,col,ty)

class SignalsImageViewer(QObject):
  ''' signals used to comunicate form calib to view'''
  pointFromView=Signal(object)
  replyFromView=Signal(int)
  
class CalibView(QLabel):  
  ''' View class for the wrapper (calib)'''
  def aa__del__(self):# should not be used because some times it is not called when deleting the object therefore I have changed the name
    ''' destructor '''
    pri.Time.red(0,'Destructor calibView')
    pri.Info.white('Destructor CalibView.')
  def __init__(self,parent:QObject=None, outFromCalibView:Callable=None,outToStatusBarFromCalibView:Callable=None,textFromCalib:Callable=None,workerCompleted:Callable=None,):
      ''' 
        outFromCalibView called by plotImg -- output function called to give some single line info und to update the interface
        outToStatusBarFromCalibView output function with position and gray level 
        two other slot are passed and set when the worker is created
        self.worker.signals.textFromCalib.connect(textFromCalib) instruction for the user
        self.worker.signals.finished.connect(workerCompleted)
            '''
      super().__init__(parent)
      self.textFromCalib=textFromCalib  #Output function to status bar
      self.outToCaller=outFromCalibView  #output function to caller called by plot
      self.workerCompleted=workerCompleted
      self.outToStatusBarCaller=outToStatusBarFromCalibView #output function to caller called by mouseMoveEvent
      self.setBackgroundRole(QtGui.QPalette.Base)
      self.setSizePolicy(QtWidgets.QSizePolicy.Ignored,  QtWidgets.QSizePolicy.Ignored)
      self.setScaledContents(True)

      # Threadpool
      self.imageViewerThreadpool=QThreadPool()
      self.imageViewerThreadpool.setMaxThreadCount(10)

      self.rectMask=None
      self.flagGetPoint=0# if true acquire points and pass them to calib
      
      self.worker:CalibWorker=None
      self.signals=SignalsImageViewer()
      self.signals.pointFromView.connect(self.pointFromView) 
      self.signals.replyFromView.connect(self.replyFromView) 
      
      self.oldPos=QtCore.QPointF(0, 0)
      self.contextMenu:QtWidgets.Qmenu=None
      self.contextMenuActions:list[QAction]=[]
      '''
      # for now unused should be used to change the level and position
      self.timer = QtCore.QTimer(self)
      self.timer.timeout.connect( self.onTimer)        
      self.timer.start(100)
      self.oldPos=QtGui.QCursor.pos()
      '''
      #  Calib and the like
      self.calib=Calib()
      #flagOp=self.calib.readCfg()
      #self.calib.readImgs()#todo verificare eventuali errori e dimensioni delle immagini in questo momento non da errore e l'img viene tagliata
      self.flagFirstTask=CalibTasks.stop
      self.flagCurrentTask=CalibTasks.stop
      
      self.setMouseTracking(True)
      self.flagButCalib=CalibTasks.findAllPlanes
      self.puMiddleButton=Punto(-1,-1)# point found when pressing with the middle button
      self.flagSearchMaskZone=False
      self.scaleFactor=1.0
      self.imgPlot=np.zeros((1,1),dtype=np.uint8)
      pri.Time.cyan(0,'End Init calibView')

      #pri.Callback.white (PaIRS_lib.Version(PaIRS_lib.MOD_Calib))
  
  def resetScaleFactor(self,scrollAreaSize):
    ''' reset the scale factor so that the image perfectly feet the window'''
    if self.calib.flagPlotMask:
      if len(self.calib.ccMask):
        (h,w)=self.calib.ccMask[0].shape
      else:
        return
    else:
       if len(self.calib.imgs):
          (h,w)=self.calib.imgs[0].shape
       else:
         return
    delta=4# by tom maybe delta pixel are added ??
    self.scaleFactor=min(    scrollAreaSize.height()/(h+delta),    scrollAreaSize.width()/(w+delta))
    
  @Slot(int)
  def drawCirclesFromCalib(self,plane:int):
    ''' draw all the circles '''
    self.drawCircles(plane)
  @Slot(object)
  def drawSingleCircleFromCalib(self,pu:Punto,flag:int,ind:int):
    ''' draws a single Circle from a point received by calib '''
    ci=Circle.fromPunto(pu) if flag else Circle.fromPunto(pu,r=rInpCircle,col=mainInCircleColors[ind],ty=mainInCircleType[ind])
    self.drawSingleCircle(ci)

  @Slot(object)
  def flagGetPointFromCalib(self,flag:int):
    ''' setter of flagGetPoint from calib'''
    self.flagGetPoint=flag
  @Slot(str)
  def askFromCalib(self,text:str):
    '''    ask if ok from Calib'''
    msgBox=QtWidgets.QMessageBox(self)
    okButton=QtWidgets.QMessageBox.Yes
    msgBox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No )
    msgBox.setDefaultButton(QtWidgets.QMessageBox.Yes)
    msgBox.setText(text)
    msgBox.setWindowTitle('CalVi')
    msgBox.setIcon(QtWidgets.QMessageBox.Question)
    okButton=msgBox.button(QtWidgets.QMessageBox.Yes)
    msgBox.show()

    #screenGeometry = QtGui.QGuiApplication.primaryScreen().availableGeometry()# screen
    screenGeometry =self.window().geometry() #main window
    screenGeo = screenGeometry.bottomRight()
    #msgGeo = QtCore.QRect(QtCore.QPoint(0,0), msgBox.sizeHint())
    msgGeo = QtCore.QRect(QtCore.QPoint(0,0), msgBox.size())
    msgGeo.moveBottomRight(screenGeo)
    #msgBox.move(msgGeo.bottomRight())
    #msgBox.move(100,0)
    a=msgBox.mapToGlobal(QtCore.QPoint(0, 0))
    a=QtCore.QPoint(*(msgBox.size()).toTuple())
    
    msgBox.move(msgGeo.bottomRight()-a-QtCore.QPoint(0,30))
    oldPos=QtGui.QCursor.pos()
    QtGui.QCursor.setPos(okButton.mapToGlobal(QtCore.QPoint(0, 0)+QtCore.QPoint(*(okButton.size()/2).toTuple())))
    #self.window().mapToGlobal(QtCore.QPoint(0, 0)) #main window
    #self.parentWidget().mapToGlobal(QtCore.QPoint(0, 0)) #parent widget
    res=msgBox.exec()
    QtGui.QCursor.setPos(oldPos)
  
    #res=QtWidgets.QMessageBox.question(self, "Calib",text )
    flag=1 if res == QtWidgets.QMessageBox.Yes  else  0
    self.signals.replyFromView.emit(flag)

  def createWorker(self,flag:CalibTasks,textFromCalib:Callable,workerCompleted:Callable):
    ''' create the worker, connects the signals and start'''
    self.worker=CalibWorker()
    self.worker.signals.drawSingleCircleFromCalib.connect(self.drawSingleCircleFromCalib)
    self.worker.signals.drawCirclesFromCalib.connect(self.drawCirclesFromCalib)
    self.worker.signals.flagGetPointFromCalib.connect(self.flagGetPointFromCalib)
    self.worker.signals.askFromCalib.connect(self.askFromCalib)
    self.worker.signals.plotImgFromCalib.connect(self.plotImg)
    self.worker.setTask(self.calib,flag)
    
    self.worker.signals.textFromCalib.connect(textFromCalib)
    self.worker.signals.finished.connect(workerCompleted)
    self.imageViewerThreadpool.start(self.worker)  

  def executeCalibTask(self,flag:CalibTasks):
    ''' button  pressed '''
    #pri.Info.red(f'executeCalibTask  {self.calib.flagExitFromView is True}   {self.calib.cal.flagWorking } {self.calib.cal.flagWorking is True}')
    if self.calib.flagExitFromView is True and self.calib.cal.flagWorking ==1:
      pri.Info.red('still working let us wait')# never used? Maybe flagWorking is useless???
      return False
    if flag is self.flagCurrentTask or flag  is CalibTasks.stop:# in this case always stop
      self.calib.flagExitFromView=True
      self.flagCurrentTask=flag=CalibTasks.stop
      self.flagGetPoint=0# if true acquire points and pass them to calib
      pri.Info.green('pressed stop')
      return True
    elif not self.flagCurrentTask is CalibTasks.stop: # already running a task simply exit function # pylint: disable=unneeded-not,superfluous-parens
      return False
    


    self.flagCurrentTask=flag
    self.calib.flagExitFromView=False
    self.createWorker(flag,self.textFromCalib,self.workerCompleted)
    return True

  def executeCalibFunction(self,flag:CalibFunctions):
    ''' button  pressed '''
    if flag is CalibFunctions.removeMaxErrPoint and self.calib.cal.flagCalibrated:
      self.calib.cal.vect.flag[self.calib.cal.data.kMax,self.calib.cal.data.jMax]=CalFlags.P_REMOVED
      self.calib.cal.removeMaxErrPoint()
          
      strPriErrCalib=self.calib.prettyPrintErrCalib()
      pri.Process.blue (strPriErrCalib)
      self.textFromCalib(strPriErrCalib)
      self.plotPlane(self.calib.cal.data.kMax)
    elif flag is CalibFunctions.findMaxErrPoint:
      self.plotPlane(self.calib.cal.data.kMax)
    elif flag is CalibFunctions.RemovePoint:
      pu=Punto(*self.scaleToImg(self.contextMenuPos).toTuple())
      if not self.insideImg(pu):
        return
      else:
        self.calib.cal.removePoint(pu)
        self.plotPlane(self.calib.plane)
    #self.scaleToImg(mouseEv.position())
    
  def plotPlane(self,plane):
    ''' plot image of plane=plane'''
    pri.Info.green('plotPlane call')
    flagPlot=False
    try:
      if 0<=plane <self.calib.nPlanes:
        self.calib.cal.data.piano=self.calib.plane=plane
        self.calib.cal.initFindPoint(plane)
        flagPlot=self.plotImg(plane)   
        if flagPlot and not self.calib.flagPlotMask: 
          self.drawCircles(plane)   
    except Exception as inst:
      pri.Error.red(f'plotePlane call: error while plotting image\n{traceback.format_exc()}')
    #XY=self.calib.cal.pointFromCalib([0,0,0],0)
    #pri.Info.green(f"Punto (x,y,z)=(0,0,0) -> (X,Y)=({XY.x},{XY.y})")
    #self.outToStatusBarCaller(f'Cam#:{self.calib.plane//self.calib.nPlanesPerCam} Plane:{self.calib.plane%self.calib.nPlanesPerCam}')
    return flagPlot
    
  @Slot(int)
  def plotImg(self,plane,flagDrawRect=False):
    ''' plot the image whenever the plane is changed '''  
    pri.Callback.white('+++ Plotting image in Vis +++')
    img,flagPlot=self.preparePlot(plane)
    if not flagPlot: 
      self.setPixmap(QtGui.QPixmap())
      return flagPlot
    dumStr='' if self.calib.cal.data.FlagCam else f'_cam{self.calib.cams[self.calib.plane//self.calib.nPlanesPerCam]}'
    nomeImg=self.calib.cal.getImgRoot(self.calib.plane%self.calib.nPlanesPerCam)+dumStr+self.calib.cal.data.EstensioneIn
    self.outToCaller(nomeImg)
    img=ImageQt.ImageQt(Image.fromarray(img))
    self.setPixmap(QtGui.QPixmap.fromImage(img))
    if flagDrawRect:
      self.drawRectangleCC(plane)
    return flagPlot
    
  #def onTimer(self):
    ''' used to pri.Callback.white the position and the gray level'''
    '''
    newPos=QtGui.QCursor.pos()
    if newPos!=self.oldPos:
      self.oldPos=newPos
      try:
        pu = self.mapFrom(self, newPos)/self.scaleFactor
        f= 0<=pu.x() <self.pixmap().width()
        if not (f and (0<= pu.y() <self.pixmap().height())):
         return
        pri.Callback.white(f'    {pu.x()}')
        j=int(pu.x())
        i=int(pu.y())
        self.outToStatusBarCaller(f'({i},{j}) {self.calib.imgs[self.calib.plane][i,j]}')
      except:
        pri.Callback.white ('Exception in onTimer')
    '''  
  def preparePlot(self,plane=0):
    ''' build the background 8 bit image for plotting'''
    self.imgPlot=np.zeros((1,1),dtype=np.uint8)#penso sia inutile e forse dannoso
    calib=self.calib
    FlagPlot=False
    if len(calib.ccMask):
      if calib.flagPlotMask: 
        mask=self.normalizeArray(calib.ccMask[plane],calib.LMax,calib.LMin)
      elif calib.flagShowMask:
        _,LMax,LMin=calib.calcLMinMax(plane,flagPlotMask=True)
        mask=self.normalizeArray(calib.ccMask[plane],LMax,LMin)
          
    if not calib.flagPlotMask:
        if len(calib.imgs):
          self.imgPlot=self.normalizeArray(calib.imgs[plane],calib.LMax,calib.LMin)
          FlagPlot=bool(self.imgPlot.max()!=self.imgPlot.min())

        if calib.flagShowMask and len(calib.ccMask):#todo TA ma se l'img è più piccola
          self.imgPlot[0:mask.shape[0],0:mask.shape[1]]=mask # pylint: disable=unsupported-assignment-operation
    else:
        if len(calib.ccMask):
          self.imgPlot=mask
          FlagPlot=bool(self.imgPlot.max()!=self.imgPlot.min())
      
    return self.imgPlot,FlagPlot
  
  def normalizeArray(self,da,LMax=None,LMin=None):
    #todo GP non è mai chiamata con None è necessario complicarla? Fra l'altro se decidiamo di valutare 
    # min e max in fase di assegnazione è inutile
    a=da.copy()# todo GP perchè la copii?
    if 'int' in a.dtype.name:
      LLim=2**16-1
      if not LMax: 
        LMax=max([min([a.max(),LLim]),-LLim+1])
      if not LMin: 
        LMin=max([min([a.min(),LMax-1]),-LLim])
      LMin=max([0,LMin])
      LMax=max([LMin+1,LMax])
      a[a>LMax]=LMax
      a[a<LMin]=LMin
    else:
      LMax=a.max()
      LMin=a.min()
      if LMax==LMin: LMax=LMax+1
  
    a=np.uint8(255.0*(a-LMin)/(LMax-LMin)) 
    return a
  def insideImg(self,pu:Punto)->bool:
    ''' checks if a point is inside the image'''  
    f= 0<=pu.x <self.pixmap().width()
    return f and (0<= pu.y <self.pixmap().height())
  
  def contextMenuEvent(self, event):
    # Show the context menu
    if self.contextMenu:
      self.contextMenuPos=event.position()
      self.contextMenu.exec(event.globalPosition().toPoint())  

  def mouseMoveEvent(self, mouseEv):
    ''' mouse move'''
    if self.imgPlot.size==1: 
      return
    try:
      newPos=self.scaleToImg(mouseEv.position())
      if newPos!=self.oldPos:
        self.oldPos=newPos
        pu=Punto(*newPos.toTuple())
        j=int(pu.x)
        i=int(pu.y)
        try:
          #self.outToStatusBarCaller(f'Cam #{self.calib.plane//self.calib.nPlanesPerCam} Plane #{self.calib.plane%self.calib.nPlanesPerCam}: ({i},{j}) {self.calib.imgs[self.calib.plane][i,j]}')
          sAppo=f'{self.calib.ccMask[self.calib.plane][i,j]:.2f}' if self.calib.flagPlotMask else f'{self.calib.imgs[self.calib.plane][i,j]:d}'
          self.outToStatusBarCaller(f'(x,y)=({i},{j}), Lev={sAppo}')
        except IndexError as exc:
          return  #out of bounds I am not checking but  exit from the function
        if mouseEv.buttons()==QtCore.Qt.MiddleButton and not self.calib.flagPlotMask: # in this case use buttons instead of button !!!!
          self.rectMask= QtCore.QRectF(min (self.puMiddleButton.x(),newPos.x()), min (self.puMiddleButton.y(),newPos.y()),abs(self.puMiddleButton.x()-newPos.x()),abs(self.puMiddleButton.y()-newPos.y()))
          self.update()
          
    except Exception as exc:# pylint: disable=broad-exception-caught
      pri.Error.red(f'Exception in mouseMoveEvent {str(exc)}')# tin qt some exception are non propagated

  def mousePressEvent(self, mouseEv):  
    ''' when mouse pressed'''
    try:
      if mouseEv.button()==QtCore.Qt.RightButton:
        self.contextMenuEvent(mouseEv)  
      elif mouseEv.button()==QtCore.Qt.MiddleButton and not self.calib.flagPlotMask:
        #self.puMiddleButton=self.scaleToImg(mouseEv.position())
        self.puMiddleButton=self.scaleToImg(mouseEv.position())
        self.flagSearchMaskZone=True
        pri.Callback.white('Mouse pressed')
    except Exception as exc:# pylint: disable=broad-exception-caught
      pri.Error.red(f'Exception in mousePressEvent {str(exc)}')# tin qt some exception are non propagated
  
  def paintEvent(self, event):
    ''' called  any time a repaint should be done used here in only to plot moving things on particular the rectangle defining the cc mask'''
    super().paintEvent(event)
    try:
      
      if self.rectMask is None or self.calib.flagPlotMask:
        return
      painter = QtGui.QPainter(self)
      pen = QtGui.QPen()
      pen.setWidth(penWidth)
      pen.setColor(QtGui.QColor(mainInCircleColors[2]))
      painter.setPen(pen)
    
      painter.drawRect(QtCore.QRectF(*self.scaleFromImgIterable(self.rectMask.getRect())))
    except Exception as exc:# pylint: disable=broad-exception-caught
      pri.Error.red(f'Exception in paintEvent {str(exc)}')# tin qt some exception are non propagated
      
  def mouseReleaseEvent(self, mouseEv):
    ''' exception raised in qt functions (slot?) are not propagated:
    # https://stackoverflow.com/questions/45787237/exception-handled-surprisingly-in-pyside-slots
    '''
    try:
      if mouseEv.button()==QtCore.Qt.LeftButton:
        if self.flagGetPoint:
          try:
            pu=Punto(*self.scaleToImg(mouseEv.position()).toTuple())
            if not self.insideImg(pu):
                return
            self.signals.pointFromView.emit(pu)
          except Exception as exc:
            pri.Error.red(str(exc))# the try should be useless but you never know since in qt some exception are non propagated
      elif mouseEv.button()==QtCore.Qt.MiddleButton and not self.calib.flagPlotMask:
        if (self.flagSearchMaskZone):
          self.setMaskZone()
          #todo add the code to revaluate the cc mask
          pri.Callback.white('Middle use Released')
    except Exception as exc:# pylint: disable=broad-exception-caught
      pri.Error.red(f'Exception in mouseReleaseEvent {str(exc)}')# tin qt some exception are non propagated

  #def drawRectangle(self, p,painter,pen):
  def setMaskZone(self):
    data=self.calib.cal.data
    p=self.calib.plane
    
    if (self.rectMask.height()< data.DimWinCC or self.rectMask.width()< data.DimWinCC ):
      raise ValueError('Error the selected window is to small') #from exc 
      
    else:
      
      self.calib.cal.setPuTrovaCC(self.rectMask.getRect(),p)
      if self.calib.flagFindAllPlanes and p==0: #when starting select a mask for all the planes
        for p1 in range(1,self.calib.nPlanes):
          self.calib.cal.setPuTrovaCC(self.rectMask.getRect(),p1)
          self.calib.cal.vect.flagPlane[p1]|= CalFlags.PLANE_NOT_INIT_TROVA_PUNTO|CalFlags.PLANE_NOT_FOUND
      self.calib.changeMask(p)
      self.plotPlane(p)
      
    self.flagSearchMaskZone=False
    self.rectMask=None# maybe is reduntant but we are using his to avoid plotting the rectangle 

  def setCirclePainter(self,canvas,cir): 
    ''' used to speed up drawCircles'''  
    painter = QtGui.QPainter(canvas)
    pen = QtGui.QPen()
    pen.setWidth(penWidth/self.scaleFactor)
    pen.setColor(QtGui.QColor(cir.col))
    painter.setPen(pen)
    if cir.type==CircleType.circle:
      def pCir(X:float, Y:float,r:float):
        painter.drawRoundedRect(X-r, Y-r,2*r,2*r,r,r)
    elif cir.type==CircleType.square:
      def pCir(X:float, Y:float,r:float):
        painter.drawRect(X-r, Y-r,2*r,2*r)
    elif cir.type==CircleType.filledCircle:
      def pCir(X:float, Y:float,r:float):
        painter.drawRoundedRect(X-r, Y-r,2*r,2*r,r,r)
      painter.setBrush(QtGui.QBrush(QtGui.QColor(cir.col)))
    return (painter,pen,pCir)  
  
  def drawArrow(self,painter,l,x1,y1,x,y):
    ''' draw arrow from x1 to x scaled with l''' 
    dx=(x-x1)*l
    dy=(y-y1)*l
    if abs(dx)>10**6 or abs(dy)>10**6:
      dx=10**3
      dy=10**3
    x2=x1+dx
    y2=y1+dy
    painter.drawLine(x1,y1,x2,y2)
    painter.drawLine(x2,y2,x2-dx*percLunFreccia+dy*tanFreccia ,y2-dy*percLunFreccia-dx*tanFreccia)
    painter.drawLine(x2,y2,x2-dx*percLunFreccia-dy*tanFreccia ,y2-dy*percLunFreccia+dx*tanFreccia)
  
  def drawAxis(self, p,painter,pen): 
    ''' draws the axis'''                                   
    calVect=self.calib.cal.vect
    flagDrawCircles=True
    percLine=0.25
    def c1(x1,x2,percLine):
       
       return x1 + (x2 - x1)*percLine
    offSetText=4
    def cLeftText( x1,x2,y1,y2 ): 
      return (c1(x1,x2,percLine if x2>x1 else (1-percLine))+offSetText,c1(y1,y2,percLine if y1>y2 else (1-percLine))-offSetText)
    def c2( x1,x2,y1,y2 ): 
        return (c1(x1,x2,percLine),c1(y1,y2,percLine),c1(x1,x2,1-percLine),c1(y1,y2,1-percLine))
  
    font = QtGui.QFont()
    font.setFamily('Arial')
    font.setPointSize(40)#todo dimesione testo e font
    painter.setFont(font)
    calVect=self.calib.cal.vect

    
    #origin
    ii=self.calib.cal.indFromCoord(0,0,p)
    if calVect.flag[p,ii]==1:
      puOr=Punto(calVect.XOr[p],calVect.YOr[p])
      ind=0
      #puOr=Punto(out.X[p,ii], out.Y[p,ii])
      #for pp in range (0,self.calib.cal.data.Numpiani):        pri.Info.green(out.X[pp,ii], out.Y[pp,ii])
      #pri.Info.green(f'Or=({out.X[p,iOr]}, {out.Y[p,iOr]})   x=({out.X[p,ii]}, {out.Y[p,ii]})  y=({out.X[p,iOr+1]}, {out.Y[p,iOr+1]})')


      if flagDrawCircles:
        r=rInpCircle
        def pCir(X:float, Y:float,r:float):
          painter.drawRoundedRect(X-r, Y-r,2*r,2*r,r,r)
          #pri.Info.green(X,Y)
        pen.setColor(QtGui.QColor(mainInCircleColors[ind]))
        painter.setPen(pen)
        pCir(puOr.x,puOr.y,r)
    # y axis 
    ind=2
    ii=self.calib.cal.indFromCoord(1,0,p)
    if calVect.flag[p,ii]==1:
      pu=Punto(calVect.X[p,ii], calVect.Y[p,ii])
      pen.setColor(QtGui.QColor(mainInCircleColors[ind]))
      painter.setPen(pen)
      self.drawArrow(painter,1,*c2( puOr.x ,pu.x ,puOr.y ,pu.y ))
      painter.drawText(*cLeftText( puOr.x ,pu.x ,puOr.y ,pu.y ),'Y')
      
      if flagDrawCircles:
        pCir(pu.x,pu.y,r)
    #asse x
    ind=1
    ii=self.calib.cal.indFromCoord(0,1,p)
    if calVect.flag[p,ii]==1:
      pu=Punto(calVect.X[p,ii], calVect.Y[p,ii])
      pen.setColor(QtGui.QColor(mainInCircleColors[ind]))
      painter.setPen(pen)
      
      painter.drawText(*cLeftText( puOr.x ,pu.x ,puOr.y ,pu.y ),'X')
      self.drawArrow(painter,1,*c2( puOr.x ,pu.x ,puOr.y ,pu.y ))
      if flagDrawCircles:
        pCir(pu.x,pu.y,r)
    # origin shift
    if (calVect.xOrShift[p] != 0 or  calVect.yOrShift[p] != 0):#plot origin
      ii=self.calib.cal.indFromCoord( int(calVect.yOrShift[p]), int(calVect.xOrShift[p]),p)
      if calVect.flag[p,ii]==1:
        
        pu=Punto(calVect.X[p,ii], calVect.Y[p,ii])
        pen.setColor(QtGui.QColor(OriginCircleColor))
        painter.setPen(pen)
        r=2*rInpCircle
        pCir(pu.x,pu.y,r)
        r=rInpCircle
        pCir(pu.x,pu.y,r)
  def drawRectangleCC(self, p):
    rect=QtCore.QRectF(*self.calib.cal.getPuTrovaCC(p))
    if rect.height()!=0:
      cir=Circle.fromPunto(Punto(0,0))
      canvas = self.pixmap()
      (painter,pen,pCir)=self.setCirclePainter(canvas,cir)
      pen.setColor(QtGui.QColor(mainInCircleColors[2]))
      painter.setPen(pen)
      painter.drawRect(rect)
      painter.end()
      self.setPixmap(canvas)
    
  ''' draw circles of the same type and color'''           
  def drawCircles(self, p,):
    ''' draw circles of the same type and color and the axis with the main points'''    
    rect=QtCore.QRectF(*self.calib.cal.getPuTrovaCC(p))
    if self.flagGetPoint:
      for i in range(self.calib.flagRicerca):
        #i=self.calib.flagRicerca-1
        if self.calib.flagFoundPoints[i]:
          pu=self.calib.foundPoints[i]
          self.drawSingleCircleFromCalib(pu,0,i) # draws a circle on the detected points
          self.drawSingleCircleFromCalib(pu,1,0) # draws a circle on the detected points
     
    err=self.calib.tryFindPlane(p)# no exception only err in output
    if err and rect.height()==0:
      return # Cosa si deve fare? Forse va bene così in fondo non è stato possibile trovare il piano

    calVect=self.calib.cal.vect
    cir=Circle.fromPunto(Punto(0,0))
    canvas = self.pixmap()
    (painter,pen,pCir)=self.setCirclePainter(canvas,cir)

    if not err:
      r=cir.r#/self.scaleFactor
      #try:
      indOk=np.nonzero(calVect.flag[p]==1)[0]
      for i in indOk:
        pCir(calVect.X[p,i], calVect.Y[p,i],r)
      if self.calib.cal.flagCalibrated:    
        data=self.calib.cal.data
        for i in indOk:
          x=float(calVect.Xc[p,i]-data.ColPart)
          y=float(calVect.Yc[p,i]-data.RigaPart)
          self.drawArrow(painter,lunFreccia,calVect.X[p,i], calVect.Y[p,i],x,y)
        if p==data.kMax:
          pen.setColor(QtGui.QColor(maxErrorCircleColor))
          painter.setPen(pen)
          r=rInpCircle
          painter.drawRect(calVect.X[p,self.calib.cal.data.jMax]-r,calVect.Y[p,self.calib.cal.data.jMax]-r,2*r,2*r)
          r*=2
          painter.drawRoundedRect(calVect.X[p,self.calib.cal.data.jMax]-r,calVect.Y[p,self.calib.cal.data.jMax]-r,2*r,2*r,r,r)
      self.drawAxis(p,painter,pen)      

    if rect.height()!=0:
      pen.setColor(QtGui.QColor(mainInCircleColors[2]))
      painter.setPen(pen)
      painter.drawRect(rect) 
    #except:        pri.Callback.white('u')
    painter.end()
    self.setPixmap(canvas)
  
  def drawSingleCircle(self, cir):
    ''' draws a single circle '''
    #pri.Callback.white(cir)
    canvas = self.pixmap()
    (painter,_,pCir)=self.setCirclePainter(canvas,cir)
    r=cir.r#/self.scaleFactor
    pCir(cir.x, cir.y,r)
    painter.end()
    self.setPixmap(canvas)      
        
  def scaleToImg(self,point):
    ''' from mouse position to image '''    
    #widgetPos = self.mapFrom(self, pos)# not needed any more since we are now plotting directly in the QLabel
    #return Punto(widgetPos.x()/self.scaleFactor,widgetPos.y()/self.scaleFactor)
    return point/self.scaleFactor
  def scaleFromImg(self,point):
    ''' from image to view  '''    
    return point*self.scaleFactor
  def scaleFromImgIterable(self,li):
    ''' from image to view  '''    
    return [d*self.scaleFactor for d in li]
  if flagImageViewer:  
    def wheelEvent(self,event):
      if event.angleDelta().y()/120>0:
        self.plotPlane(self.calib.plane+1)
      else:
        self.plotPlane(self.calib.plane-1)
    
    

  
  def spinImgChanged(self,plane):
    ''' plot image of plane=plane'''
    self.plotPlane(plane)

  def spinOriginChanged(self,Off:int,spin:QSpinBox,flagX:bool,flagPlot=True):
    ''' offset Origin '''
    p=self.calib.plane
    calVect=self.calib.cal.vect
    ma=calVect.W[p] / 2 if flagX else calVect.H[p] / 2
    if not  -ma<Off<ma:  # if inside
      Off=int(-ma if Off < -ma else ma if Off > ma else Off)
      spin.setValue(Off)
    if flagX:
      calVect.xOrShift[p]=Off
    else:
      calVect.yOrShift[p]=Off
    if flagPlot: self.plotPlane(self.calib.plane)
  
  def copyRemPoints(self):
    p=self.calib.plane
    calVect=self.calib.cal.vect
    
    for pp in range(self.calib.nPlanes):
      if pp is p : 
        continue
      self.calib.cal.data.piano=pp
      
      calVect.remPointsRi[pp]=calVect.remPointsRi[p]
      calVect.remPointsLe[pp]=calVect.remPointsLe[p]
      calVect.remPointsUp[pp]=calVect.remPointsUp[p]
      calVect.remPointsDo[pp]=calVect.remPointsDo[p]
      self.calib.cal.removeBulk()
    self.calib.cal.data.piano=p
  def spinRemPoints(self,Off:int,spin:QSpinBox,flagX:bool,flagPos:bool):
    ''' Remove points '''
    p=self.calib.plane
    p=self.calib.cal.data.piano=p
    calVect=self.calib.cal.vect
    ma=calVect.W[p] / 2 if flagX else calVect.H[p] / 2
    if not  -ma<Off<ma:  # if inside
      Off=int(-ma if Off < -ma else ma if Off > ma else Off)
      spin.setValue(Off)
    if flagX:
      if flagPos:
        calVect.remPointsRi[p]=Off
      else:
        calVect.remPointsLe[p]=Off
    else:
      if flagPos:
        calVect.remPointsUp[p]=Off
      else:
        calVect.remPointsDo[p]=Off
    self.calib.cal.removeBulk()
    if self.calib.cal.flagCalibrated:
      self.calib.cal.checkCalibration() #needed because use the main thread and may exit with an exception
      strPriCalib=self.calib.prettyPrintCalib()
      strPriErrCalib=self.calib.prettyPrintErrCalib()
      pri.Process.blue (strPriErrCalib)
          
      self.calib.signals.textFromCalib.emit(strPriErrCalib+'\n'+strPriCalib)
    self.plotPlane(self.calib.plane)
  
  @Slot(int)
  def replyFromView(self,ans:int):
    ''' slot function called by the View when the answer is ready  '''
    #pri.Info.white(f'replyFromView {ans}')
    self.calib.ans=ans
    self.calib.flagAnsReady=True
  @Slot(object)
  def pointFromView(self,pu:Punto):
    ''' slot function called by the View when the point  is ready  '''
    #pri.Info.white(f'pointFromView {pu.x}')  
    self.calib.pu=pu
    self.calib.flagPointReady=True
  
class SignalsCalibWorker(QObject):
  drawSingleCircleFromCalib=Signal(object,int,int)
  drawCirclesFromCalib=Signal(int)
  flagGetPointFromCalib=Signal(int)
  askFromCalib=Signal(str)
  plotImgFromCalib=Signal(int,bool)
  textFromCalib=Signal(str)
  finished=Signal(bool)

class CalibWorker(QRunnable):
  def __init__(self,):
  #def __init__(self,mainFun:Callable,cal:Calib):
    
    #def __init__(self,data:dataTreePar,indWorker:int,indProc:int,numUsedThreadsPIV:int,pfPool:ParForPool,parForMul:ParForMul,nameWorker:str,mainFun:Callable):
    #super(MIN_ParFor_Worker,self).__init__(data,indWorker,indProc,pfPool=ParForPool,parForMul=ParForMul)
    super(CalibWorker,self).__init__()
    self.signals=SignalsCalibWorker()
    self.isKilled = False
    self.isStoreCompleted = False
    self.calib:Calib=None
    self.mainFun:Callable=None
    
  def setTask(self,calib:Calib,flag:CalibTasks):
    ''' set calib and chooses the task'''
    self.calib=calib
    self.calib.signals=self.signals
    if flag is CalibTasks.findAllPlanes:
      self.mainFun=self.calib.taskFindAllPlanes
    elif flag is CalibTasks.findCurrentPlane:
      self.mainFun=self.calib.taskFindCurrentPlane
    elif flag is CalibTasks.calibrate:
      self.mainFun=self.calib.taskCalibrate
    elif flag is CalibTasks.findPlanesFromOrigin:
      self.mainFun=self.calib.taskFindAllPlanesFromOrigin
    elif flag is CalibTasks.savePoints:
      self.mainFun=self.calib.taskSavePoints
    pri.Callback.blue(f'setCal-> {self.mainFun.__func__.__name__}  flag={flag}')  
    self.signals.textFromCalib.emit(f'')

  @Slot()
  def run(self):
    ''' main running function'''
    if Flag_DEBUG_PARPOOL: 
      try:
        debugpy.debug_this_thread() 
      except Exception as inst:
        pri.Error.red(f'Error with debugpy (CalibWorker):\n{inst}')
    try:
        #pr(f'ParForWorker.run self.isKilled={self.isKilled}  self.indWorker={self.indWorker}  self.indProc={self.indProc}  ')
        #self.parForMul.numUsedCores=self.numUsedThreadsPIV
        '''
        while self.indWorker!=self.indProc:# and not self.isKilled:
            timesleep(SleepTime_Workers) 
            if self.isKilled: 
                self.signals.completed.emit()
                return # in this case we are killing all the threads
        pri.Process.blue(f'ParForWorker.run starting {self.nameWorker} self.isKilled={self.isKilled}  self.indWorker={self.indWorker}  self.indProc={self.indProc}  ')
        '''
        flagErr=False
        self.mainFun()
        

    except ValueError as exc:
      if exc.args[1]!=TYPE_ERR_STOP:
        #traceback.print_exc()  
        pri.Info.white(f"run ->Unexpected {exc=}, {type(exc)=}")
        self.signals.textFromCalib.emit(f'Calibration error:\n{exc}')
        flagErr=True
    except Exception as exc:
      #traceback.print_exc()
      pri.Info.white(f"run ->Unexpected {exc=}, {type(exc)=}")
      self.signals.textFromCalib.emit(f'Calibration error:\n{exc}')
      flagErr=True
    #else:      pass
    #pri.Info.white("Normal termination of  Worker")
    finally:
      self.signals.finished.emit(flagErr)  
      pri.Process.blue(f'End of Worker->{self.mainFun.__func__.__name__}() ')  
      
    

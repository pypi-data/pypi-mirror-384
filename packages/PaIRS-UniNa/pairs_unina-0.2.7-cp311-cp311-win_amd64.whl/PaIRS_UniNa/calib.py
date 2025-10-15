''' helper class for calib'''
# pylint: disable=pointless-string-statement, too-many-instance-attributes, no-name-in-module, multiple-imports
# pylint: disable= import-error 
# pylint: disable=multiple-statements


import sys #, traceback
from time import sleep as timesleep
from typing import Tuple#,Callable
from enum import Enum
from time import sleep 
#import faulthandler # per capire da dove vengono gli errori c
import platform

from PIL import Image
import numpy as np

from .tAVarie import pri, PrintTA ,PrintTAPriority
from .readcfg import readNumCfg, readCfgTag,readNumVecCfg


if __package__ or "." in __name__:
  import PaIRS_UniNa.PaIRS_PIV as PaIRS_lib
  from PaIRS_UniNa.PaIRS_PIV import Punto
  from PaIRS_UniNa.PaIRS_PIV import CalFlags
else:
  if platform.system() == "Darwin":
    sys.path.append('../lib/mac')
    #sys.path.append('../lib')
  else:
    #sys.path.append('PaIRS_PIV')
    sys.path.append('../lib')
    sys.path.append('TpivPython/lib')
  import PaIRS_PIV as PaIRS_lib # type: ignore
  from PaIRS_PIV import Punto # type: ignore
  from PaIRS_PIV import CalFlags # type: ignore

# to be deleted
#import debugpy #nel caso mettere nel thread debugpy.debug_this_thread()
from .PaIRS_pypacks import Flag_DEBUG_PARPOOL
#Flag_DEBUG_PARPOOL=1 # pylint: disable=invalid-name
if Flag_DEBUG_PARPOOL: import debugpy #nel casso mettere nel thread debugpy.debug_this_thread()


sleepTimeWorkers=0.2 #for multithreading and other stuff
FlagReadCfg=True
PrintTA.flagPriority=PrintTAPriority.veryLow 
# errror codes 
TYPE_ERR_REPEAT=-101 # pylint: disable=invalid-name
TYPE_ERR_STOP=0 # pylint: disable=invalid-name

#for multithreading and other stuff 
SleepTime_Workers=0.1 # pylint: disable=invalid-name

class CalibTasks(Enum):
  ''' when <=0 no button is created'''
  #stop should be zero so that is is possible to check immediately is no task are running
  stop = 0            # pylint: disable=invalid-name
  findAllPlanes= 1    # pylint: disable=invalid-name
  findCurrentPlane= 2 # pylint: disable=invalid-name
  calibrate=3         # pylint: disable=invalid-name
  savePoints=4         # pylint: disable=invalid-name
  findPlanesFromOrigin=-1         # pylint: disable=invalid-name
calibTasksText=[
  # the index is relative to the value of CalibTask
   'Stop',           
   'Find all' ,  
   'Find curr.',
   'Calibrate' ,   
   'Save coord.' ,   
   '...' 

]
''' when not calibrated all the voices are disabled'''
class CalibFunctions(Enum):
  ''' when <=0 only the context menu is added but the button isn't created (negative voices are not disabled)'''
  removeMaxErrPoint= 1    # pylint: disable=invalid-name
  findMaxErrPoint=2    # pylint: disable=invalid-name
  RemovePoint=-3    # pylint: disable=invalid-name
  #findMaxErrPoint1=[3, 4]    # pylint: disable=invalid-name
  
calibFunctionsText=[
  # hte index is relative to the value of CalibTask
   'Stop',           #not used but needed
   'Delete max.',           
   'Focus max.',           
   'Apply to all',
]

def loopFun(fun):
  ''' loop a function 
    if the fun raises exception:
      ValueError as err: if err.args[1]==TYPE_ERR_REPEAT'''
  def wrapper(*args,**kwargs):
    ''' wrapper'''
    while True:  
      try:
        res=fun(*args,**kwargs)
      except ValueError as err:
        if err.args[1]!=TYPE_ERR_REPEAT:
          raise err
        continue
      break
    return res
  return wrapper  


class Calib(PaIRS_lib.PyFunOutCalib):
  def __init__(self):
    #super().__init__(mainFun=self.findAllPlanes)
    PaIRS_lib.PyFunOutCalib.__init__(self)
    self.funCalib =PaIRS_lib.getPyFunCalib(self) 
    self.pointDesc=['origin ', 'right (along x)','upper (along y)']
    self.inputPoints=[Punto(0,0)]*3  #input points when looking for origin
    self.foundPoints=[Punto(0,0)]*3  #found point near the input points when looking for origin
    self.flagFoundPoints=[False]*3  #flag to be sure that point have been found
    self.cal=PaIRS_lib.Cal()
    self.imgs =[]                     # Images
    self.ccMask =[]                   # correlation mask 
    self.flagRicerca=0  # 0 stand by 1-3 searching first, second or third point 4 the three point have been found

    self.plane=self.cal.data.piano=0  # Plane in use
    self.nCams=0                  # number of cameras
    self.cams=[]                  # list of the camera identifiers
    self.nPlanesPerCam=0          # Total number of planes per camera
    self.nPlanes=0                # Total number of planes =nCams*nPlanesPerCam
    self.tipoCal=0                # Calibration type see calibra.h
    # comunication with the view
    self.signals:SignalsCalibWorker=None
    self.ans=0                    # Answer from view
    self.pu=Punto(0,0)            # Point From view
    self.flagAnsReady=False       #True  if answer is ready to be read
    self.flagPointReady=False     #True  if point  is ready to be read
    self.flagExitFromView=False   #True  if exit from View signal
    self.flagFindAllPlanes=False  #True  if point  searching all the planes
    self.cal.flagCalibrated=False      # True if the calibration has ended successfully
    # various
    self.cfgName=''               # Name of the cfg file comprehensive of path but without extension
    pri.Time.cyan(0,'Init Calib')
    # flags
    self.flagShowMask=True       # True to plot the mask #todo maybe in a different window
    self.flagPlotMask=False
    self.strOut=''
  
    self.LLim=1
    self.LMax=1
    self.LMin=0
    self.FlagCalibration=False


  def reinitCal(self):
    ''' non utilizzata penso di averla messa quando si bloccava in uscita'''
    try: 
      del self.cal
    except AttributeError: 
      pass
    cal=PaIRS_lib.Cal()
    cal.flagCalibrated=False      # True if the calibration has ended successfully
    cal.data.piano=0  # Plane in use
    return cal,cal.data.piano
  
  def waitAnsFromView(self)-> int:
    ''' used to wait an answer from the view return an int  '''
    while not self.flagAnsReady:
      sleep(SleepTime_Workers) 
    self.flagAnsReady=False

    return self.ans

  def checkExitFromView(self):
    ''' control if an exit signal has been emitted by the view and in case raises an error signal'''
    if self.flagExitFromView:
      self.flagExitFromView=False
      self.signals.textFromCalib.emit( 'stopped by user')
      raise ValueError('Exit from view ',TYPE_ERR_STOP) 
      
  def waitPointFromView(self)-> int:
    ''' used to wait a point from the view return an int  '''
    while not self.flagPointReady and not self.flagExitFromView:
      sleep(SleepTime_Workers) 
    self.flagPointReady=False
    self.checkExitFromView()
    return self.pu

  
  
  def askToRetry(self, funName:str):
    ''' used to avoid repeating code'''
    self.signals.askFromCalib.emit('Press Yes to continue No to repeat' )
    if not self.waitAnsFromView():
      raise ValueError(f'Repeat in {funName}',TYPE_ERR_REPEAT) 
  
  def exceptAskRetry(self, exc:Exception, question: str,funName:str):
    ''' used to avoid repeating code'''
    if len(exc.args) >1:# if not most probably from c Lib
      if exc.args[1]==TYPE_ERR_STOP:# just exit
        raise exc
    self.signals.askFromCalib.emit(question)
    if self.waitAnsFromView():
      raise ValueError(f'Repeat in {funName}',TYPE_ERR_REPEAT) from exc 
    raise ValueError(f'Search stopped in {funName}',TYPE_ERR_STOP) from exc
  @loopFun
  def findPoint(self)->Punto:  
    ''' look for a single point '''
    self.signals.flagGetPointFromCalib.emit(1) #enables the search for points in the view
    pu=self.waitPointFromView()
    self.signals.flagGetPointFromCalib.emit(0) #disables the search for points in the view
    sleep(0)
    try:
      pu=self.cal.findPoint(pu)
    except ValueError as exc:
      self.exceptAskRetry( exc, 'Point not found Yes to repeat No to stop','findPoint')
    #pri.Info.white(f'findPoint ({pu.x}, {pu.y})')
    self.signals.drawSingleCircleFromCalib.emit(pu,0,self.flagRicerca-1) # draws a circle on the detected points
    return pu
  
  @loopFun
  def findPlaneFrom3Points(self,plane=0,op=0):  
    ''' ask the user to input the 3 points and then finds the spots in the plane'''
    try:
      #pri.Info.magenta(plane)
      self.resetFindPlane(plane) 
      for i in range (3):
        self.signals.textFromCalib.emit(f'Select the {self.pointDesc[i]} point')
        self.flagRicerca=i+1
        self.foundPoints[i]=pu=  self.findPoint()
        self.flagFoundPoints[i]=True
        self.signals.drawSingleCircleFromCalib.emit(pu,1,0) # draws a circle on the detected points
      self.evalAnglesFindPlanes(op=op)
    except ValueError as exc:
      self.exceptAskRetry( exc, 'Plane not found Yes to repeat No to stop','findPlane')
    self.askToRetry('findPlane')
  
  @loopFun  
  def findPlaneFromOrigin(self,plane=1,op=1):  
    ''' ask the user to input the origin then finds the spots in the plane
        op is passed to the lib function evalAngles and should be equal to_
        * 0:// evaluate angles from 3 points in input
        * 1:// only the origin. Should be the second plane and the first should be already have been processed
        * 2:// Nothing  Should be the at least the third  plane and the first two should be already have been processed 
        * 3:// multiplane target  
    '''
    try:
      self.resetFindPlane(plane)
      self.signals.textFromCalib.emit(f'Select the {self.pointDesc[0]} point')
      self.flagRicerca=1
      self.foundPoints[0]=pu=self.findPoint()
      self.flagFoundPoints[0]=True
      self.signals.drawSingleCircleFromCalib.emit(pu,1,0)
      self.evalAnglesFindPlanes(op=op)
    except ValueError as exc:
      self.exceptAskRetry( exc, 'Plane not found Yes to repeat No to stop','findPlaneFromOrigin')
    self.askToRetry('findPlaneFromOrigin')
  
  def findPlaneAutomatic(self,plane:int,op:int):  
    ''' Automatic selection of the origin then finds the spots in the plane'''
    self.signals.textFromCalib.emit('Automatic selection of the origin')
    try:
      self.resetFindPlane(plane)
      self.evalAnglesFindPlanes(op=op)
    except ValueError as exc:
      try:
        self.signals.textFromCalib.emit(exc.args[0])# todo mettere anche dove si vuole sapere l'errore preciso della libreria
        self.exceptAskRetry( exc, 'Plane not found Yes for manual search No to exit','findPlaneAutomatic')
      except ValueError as err:# looking for a plane from the origin
        if err.args[1]==TYPE_ERR_REPEAT:
          self.findPlaneFrom3Points(plane=plane) 
          #self.findPlaneFromOrigin(plane=plane,op=2) # this is not possibile unless on changes the behavior of the library
        else :
          #print('Si dovrebbe uscire senza errore')
          pass
        return

    #self.askToRetry('findPlaneAutomatic')
    self.signals.askFromCalib.emit('Press Yes to continue No for manual search' )
    if not self.waitAnsFromView():
      self.findPlaneFrom3Points(plane=plane) 
      #raise ValueError('Repeat in findPlaneAutomatic',TYPE_ERR_STOP) 

  def tryFindPlane(self,p:int)->int:
    ''' call find plane only if needed '''
    err=0
    flagPlane=self.cal.vect.flagPlane[p]
    #flagPlane=self.cal.getFlagPlane(p)
    if flagPlane:# the points have not been found
      
      if flagPlane &   CalFlags.PLANE_ORIGIN_NOT_FOUND: # no origin error code
        #pri.Info.red('getFlagPlane-> searching????')
        err=-1
        return err
      try:
        self.findPlane(p)
      except ValueError:
        return -1
      
    return err

  def findPlane(self,p:int):
    ''' find all the points in a plane'''
    try:
      self.cal.findPlane(p)
    except RuntimeError as exc:
      raise ValueError('Plane not found in findPlane',TYPE_ERR_REPEAT) from exc 
    self.cal.vect.flagPlane[p]=0
    #self.cal.setPlaneFound(p,True)
    
  def taskFindAllPlanes(self):  
    ''' finds all the planes '''
    self.cal.flagCalibrated=False      # True if the calibration has ended successfully
    self.cal.flagWorking=1
    self.flagFindAllPlanes=True
    tipoCal = (self.cal.data.TipoCal >> CalFlags.SHIFT) &CalFlags.MASK#calibration type
    try:
      for c in range(self.nCams):
        p0=c*self.nPlanesPerCam
        self.findPlaneFrom3Points(plane=p0) 
        if self.cal.data.TipoTarget==1: #
          for p in range(1,self.nPlanesPerCam):
             self.findPlaneAutomatic(p0+p,3)   #double plane target op=3
        elif tipoCal==0:#calibrazione normale only origin op=1
          self.findPlaneFromOrigin(plane=p0+1) # only origin op=1
          for p in range(2,self.nPlanesPerCam):
            self.findPlaneAutomatic(p0+p,2)  # normal plane automatic op=2
        else:#CpP, cyl or other things  per plane calibration op=0
          for p in range(1,self.nPlanesPerCam):
            self.findPlaneFrom3Points(plane=p0+p,op=0) 
        #Nel caso avvisare cambio camera
      #for p in range(self.nPlanes):
    except ValueError as exc:
      raise exc #può succedere in findPlaneAutomatic o se si preme stop
    finally:
      self.flagFindAllPlanes=False
      self.cal.flagWorking=0

  def taskFindAllPlanesFromOrigin(self):  
    ''' finds all the spots in the planes when the origins and angles are known'''
    self.cal.flagWorking=1
    try:
      for c in range(self.nCams):
        p0=c*self.nPlanesPerCam
        for p in range(0,self.nPlanesPerCam):
          self.findPlane(p0+p)
      self.signals.drawCirclesFromCalib.emit(self.plane)
    except ValueError as exc:
      raise exc #può succedere in findPlaneAutomatic o se si preme stop
    finally:
      self.cal.flagWorking=0



  def evalAnglesFindPlanes(self,op=0)->int:
    '''  op is passed to the lib function evalAngles and should be equal to_
    * 0:// evaluate angles from 3 points in input
    * 1:// only the origin. Should be the second plane and the first should be already have been processed
    * 2:// Nothing  Should be the at least the third  plane and the first two should be already have been processed 
    * 3:// multiplane target  

    '''
    self.cal.evalAngles(self.plane,op,self.foundPoints)
    self.cal.cleanPlanes()
    self.findPlane(self.plane)
    self.signals.drawCirclesFromCalib.emit(self.plane)
  

  def changeMask(self,plane:int):
    ''' used after changing the mask origin may or may have not been found
    * stores plane in self.plane 
    * plot the image
    * initFindPoint and allocate memory if needed'''
    
    self.cal.data.piano=self.plane=plane
    self.cal.vect.flagPlane[plane]|= CalFlags.PLANE_NOT_INIT_TROVA_PUNTO|CalFlags.PLANE_NOT_FOUND
    
    if (self.cal.originFound (self.plane)):
      self.findPlane(self.plane)
    else:
      self.cal.initFindPoint(self.plane)
    self.cal.removeBulk()
    self.ccMask=self.cal.getMask()
    

  def resetFindPlane(self,plane:int):
    ''' reset the plane  
    * stores plane in self.plane 
    * plot the image
    * initFindPoint and allocate memory if needed'''
    self.flagRicerca=1
    self.cal.data.piano=self.plane=plane
    self.cal.setOriginFound (self.plane,False)
    #self.cal.vect.flagPlane[plane]|= CalFlags.PLANE_ORIGIN_NOT_FOUND|CalFlags.PLANE_NOT_FOUND
    self.flagFoundPoints=[False]*len(self.flagFoundPoints)
    self.cal.initFindPoint(self.plane)
    self.signals.plotImgFromCalib.emit(self.plane,True) 
  
  def taskFindCurrentPlane(self):  
    ''' finds a single plane '''
    '''self.signals.textFromCalib.emit(f'FindCurrentPlane work in progress')
    self.cal.flagCalibrated=False      # True if the calibration has ended successfully
    for i in range (5):
      sleep(1)
      self.checkExitFromView()
      pri.Info.white (f'findCurrentPlane {i}')
    self.signals.textFromCalib.emit(f'')
    
    '''    
    self.cal.flagWorking=1
    self.cal.flagCalibrated=False      # True if the calibration has ended successfully
    try:
      self.findPlaneFrom3Points(plane=self.plane) 
    except ValueError as exc:
      raise exc #può succedere in findPlaneAutomatic o se si preme stop
    finally:
      self.cal.flagWorking=0
    
  def funOutCalib(self, flag,s) :  
    ''' called by the library when calibrating '''
    #print(f'  funOutCalib {flag} {s}',end='')
    if self.flagExitFromView is True:
      return -1
    
    if flag==0:
      self.signals.textFromCalib.emit(self.strOut)
      self.strOut=s
    elif flag==1:
      self.strOut+=s  
    #self.app.processEvents()
    return  0
  
  def taskSavePoints(self):
    ''' saves calibration points'''
    self.cal.flagWorking=1
    try:
      self.cal.savePoints() 
    except RuntimeError as exc:
      raise  exc #todo a single error otherwise we should use more try blocks
    finally:
      self.signals.textFromCalib.emit(f'')    
      self.cal.flagWorking=0
  
  def taskCalibrate(self):  
    ''' calibrates '''
    self.cal.flagWorking=1
    data=self.cal.data
    tipoCal = (data.TipoCal >> CalFlags.SHIFT) &CalFlags.MASK
    try:
      pri.Process.blue ('calibrating ')
      self.signals.textFromCalib.emit('calibrating ')
      pri.Info.white(f'init calibration {self.cal.flagCalibrated}')
      self.cal.calibrate(self.funCalib) 
      
      while self.cal.flagWorking==2:# and not self.isKilled:        
        timesleep(sleepTimeWorkers) 
      pri.Info.white(f'end calibration {self.cal.flagCalibrated}')
      self.cal.checkCalibration() #needed because use the main thread and may exit with an exception
      self.FlagCalibration=True
      self.cal.saveCfg (0,self.cfgName) 
      
      self.cal.saveConst () 
         
      if (tipoCal>0 and  tipoCal!=2):
        self.cal.saveCfg (1,self.cfgName) 
      #self.flagCalibrated=True
    except RuntimeError as exc:
      raise  exc #todo a single error otherwise we should use more try blocks
    finally:
      self.signals.textFromCalib.emit(f'')
      self.cal.flagWorking=0
    
    #self.cal.out.XcPun[0]=8

    
    strPriCalib=self.prettyPrintCalib()
    strPriErrCalib=self.prettyPrintErrCalib()
    pri.Process.blue (strPriErrCalib)
        
    self.signals.textFromCalib.emit(strPriErrCalib+'\n'+strPriCalib)
    self.cal.data.piano=self.plane=0
    self.signals.plotImgFromCalib.emit(self.plane,False )   
    self.signals.drawCirclesFromCalib.emit(self.plane)   
  def prettyPrintErrCalib(self)-> str:
    ''' generate a string with a "pretty" version of the calibration error '''
    data=self.cal.data
    strAppo=f'#Points = { data.Npti}\n'
    strAppo+=f'ErrRms={data.Errrms:.3f} ErrMax={data.ErrMax:.3f} \nImg ({data.XMax:.2f}, {data.YMax:.2f}) Space({data.xMax:.2f}, {data.yMax:.2f}, {data.zMax:.2f})'
    return strAppo
  def prettyPrintCalib(self)-> str:
    ''' generate a string with a "pretty" version of the calibration parameters '''
    data=self.cal.data
    cost=self.cal.vect.cost
    convGradi=180/np.pi
    tipoCal = (data.TipoCal >> CalFlags.SHIFT) &CalFlags.MASK
    flagPinHole =not (not( data.TipoCal & CalFlags.Flag_PIANI))  # pylint: disable=unneeded-not,superfluous-parens
    #F_Sa = not (not(data.TipoCal & CalFlags.Flag_LIN_VI))
    s=''
    if (data.FlagCal == 1 or data.FlagCal == 2 or data.FlagCal == 3):
      c = 0
      for i in range (4, data.NumCostCalib):
         s+=f'{cost[c][i]:+.4g}  '
    else:         # TSAI di qualche forma!!!!!!!!
      if (tipoCal> 0 or ( (data.FlagCal >= 10 and  data.FlagCal <= 43)and  flagPinHole)):#la seconda dovrebbe comprendere la prima 
        cPlanes=self.cal.vect.costPlanes
        s+='Planes ******************\r\n'
        for i in range ( data.Numpiani_PerCam):
          s+=f'Plane {i}: Ang(°)=[{cPlanes[i,0]:+.2f},{cPlanes[i,1]:+.2f},{cPlanes[i,2]:+.2f}] T=[{cPlanes[i,3]:+.2f},{cPlanes[i,4]:+.2f},{cPlanes[i,5]:+.2f}]\r\n'
      if data.FlagCal >= 30:#cal cilindrica
        c = 0
        s+='Cylinder ****************\r\n'
        s+=f'Distortion s1={cost[c][24]:.2e} s2={cost[c][25]:.2e}\r\n' 
        s+=f'T(Cyl)=[{cost[c][17]:+.2f},{cost[c][18]:+.2f}] Ang(°)=[{cost[c][19]:+.2f},{cost[c][20]:+.2f}]\r\n' 
        s+=f'r(Cyl)=[{cost[c][21]:+.2f},{cost[c][21]+cost[c][22]:+.2f}] rho={cost[c][23]:+.2f}  \r\n'
      s+='Cameras  ***************\r\n'
      for c in range(data.NCam):
        if cost[c][1] < 0:
          s+='\r\n \r\n *******  The coordinate system is not right-handed ******* \r\n \r\n'
        #Flag Rot Rot Rot Tx Ty Tz   f   u0  v0    b1    b2    k1    k2    p1    p2   sx   S   

        s+=f'** c={c} Ang(°)=[{cost[c][2] * convGradi:+.2f},{cost[c][3] * convGradi:+.2f},{cost[c][4] * convGradi:+.2f}] '
        s+=f'T=[{cost[c][5]:+.2f},{cost[c][6]:+.2f},{cost[c][7]:+.2f}] \r\n'
        s+=f'   f={cost[c][8]:+.2f} T(Img) [{cost[c][9]:+6.4g},{cost[c][10]:+6.4g}] b=[{ cost[c][11]:.2e},{ cost[c][12]:.2e}]  \r\n'
        s+=f'   k=[{cost[c][13]:.2e},{cost[c][14]:.2e}]  p=[{cost[c][15]:.2e},{cost[c][16]:.2e}]\r\n'
        if data.FlagCal >= 30:
          s+=f'   Pixel Ratio={cost[c][26]:+.4g} xdim pixel={cost[c][27]:+.4g}  \r\n'
        else:
          s+=f'   Pixel Ratio={cost[c][17]:+.4g} xdim pixel={cost[c][18]:+.4g}  \r\n'
    return s
  
  def waitForEver(self):
    ''' simply waits for ever'''
    self.signals.flagGetPointFromCalib.emit(1)
    #sleep(SleepTime_Workers) 
    self.taskFindAllPlanes()
    i=0
    while True:# and not self.isKilled:
      sleep(SleepTime_Workers*5) 
      i+=1
      #pri.Info.white(f'dummy called->{i}')    
      
  def readCfg(self):
    '''if (platform.system() == "Linux"):
      nomeImg='/mnt/c/Dati/Dropbox/DATI/Piv/calvi/CalVi/img/-2mm_cam0.tif'
      nomeCfg='/mnt/c/Dati/Dropbox/DATI/Piv/calvi/CalVi/NewCam0.cfg'
    else:
      nomeImg='C:/Dati/Dropbox/DATI/Piv/calvi/CalVi/img/-2mm_cam0.tif'
      nomeCfg='C:/Dati/Dropbox/DATI/Piv/calvi/CalVi/NewCam0.cfg'''
    try:
      if FlagReadCfg:
        flagOp=self.cal.readCfg(self.cfgName)
      else:
        #flagOp=self.initDataDoppio_Ger()
        #flagOp=self.initDataDoppio()
        flagOp=self.initData_P()
        #flagOp=self.initData_P_Piano()
      pass
    #except RuntimeError as exc:
    except Exception as exc:
      #traceback.print_exc()
      #pri.Info.white(str(exc.__cause__).split('\n')[3])
      pri.Info.white(str(exc.args[0]).split('\n')[3])
      #'''
    #for i in range(100):              print(f'{outDa.z[0]} {outDa.XOr[0]} {outDa.YOr[0]} {outDa.angCol[0]} {outDa.angRow[0]}')
    
    self.nCams=self.cal.data.NCam
    self.cams=self.cal.getCams()
    self.nPlanes=self.cal.data.Numpiani
    self.nPlanesPerCam=self.cal.data.Numpiani_PerCam

    
    return flagOp
  
  def setLMinMax(self,p=0):
    self.LLim,self.LMax,self.LMin=self.calcLMinMax(p,self.flagPlotMask)
    return
  # TODO GP forse è meglio fissare un LLim positivo ed uno negativo come:
  # perc= 0.2 ad esempio
  # LLMin=LMin-abs((LMax-LMin)*perc) 
  # LLMax=LMax+abs((LMax-LMin)*perc) 
  # questo potrebbe essere fatto direttamente in fase di plot
  # fra l'altro potremmo calcolare queste cose solo in fase di lettura (o calcolo nel caso della maschera) e non modificarle più
  def calcLMinMax(self,p,flagPlotMask):
    LLim=2**16-1
    if flagPlotMask and len(self.ccMask):
        a=self.ccMask[p]
        flagArray=True
    elif len(self.imgs):
        a=self.imgs[p]
        LLim=np.iinfo(a.dtype).max
        flagArray=True
    else:
        flagArray=False
    if flagArray:
      try:
        LMax=int(a.max())
      except:
        LMax=LLim
      try:
        LMin=int(a.min())
      except:
        LMin=-LLim
    else:
      LMax=LLim
      LMin=-LLim
    return LLim,LMax,LMin
        

  def readImgs(self ):
    ''' reads the images'''
    for cam in range(self.nCams):
      numero='' if self.cal.data.FlagCam else f'_cam{self.cams[cam]}'
      for p in range(self.nPlanesPerCam):
        nomeImg=self.cal.data.percorso+self.cal.getImgRoot(p)+numero+self.cal.data.EstensioneIn
        da=np.array(Image.open(nomeImg),dtype=float)
        #pri.Info.white (f'{nomeImg}')
        data=self.cal.data
        self.imgs.append(np.ascontiguousarray(da[data.RigaPart:data.RigaPart+data.ImgH,data.ColPart:data.ColPart+data.ImgW],dtype= np.uint16))

    self.setLMinMax()
    #self.cal.FlagPos=-5

    '''aaaa=np.array([[[1, 2, 3, 4],[11, 12, 13, 14],[21, 22, 23,24]]             ,[[10, 2, 3, 4],[1, 12, 13, 14],[1, 22, 23,24]]             ])
    aaaa=np.array([[[[1, 2, 3, 4],[11, 12, 13, 14],[21, 22, 23,24]]             ,[[10, 2, 3, 4],[1, 12, 13, 14],[1, 22, 23,24]]             ],[[[100, 2, 3, 4],[11, 12, 13, 14],[21, 22, 23,24]]             ,[[1000, 2, 3, 4],[1, 12, 13, 14],[1, 22, 23,24]]             ]])
    bb=np.ascontiguousarray(aaaa,dtype= np.uint16)
    self.cal.SetImg( [ bb])
    bb
    da[284,202]
    '''
    self.cal.setImgs(self.imgs)
    self.ccMask=self.cal.getMask()

  
  
  def initDataDoppio(self)->int:
                    
    #-------------------------------------- %
    #      Not in cfg       %
    # --------------------------------------%
    data=self.cal.data
    calVect=self.cal.vect
    FlagCfgAutoGen=1 # auto start as when already processed in this case some additional vectors are needed
    
    data.PercErrMax = 0.1        # 0.10 Percentuale massima per errore in posizioneTom da modificare 
    
    #data.PercRaggioRicerca = 0.4 # 0.40 Not used any more
    # InitParOptCalVi(&dati->POC); #todo
  
    #-------------------------------------- %
    #      Input and Output parameters       %
    # --------------------------------------%
    
    data.percorso = '../../../../../New/ProvaCAlvi/in/targetDoppioPiano/'   #percorso file di input
    data.EstensioneIn = '.png' #estensione in (b16 o tif)
    data.FlagCam=1   #se =-1 non fa nulla se positivo aggiunge _cam# alla fine del nome img  e non mette il numero
    data.percorsoOut = '../../img/calib/' # percorso file di output
    data.NomeFileOut = 'cal' # nome file di output
    cams=[-1]
    data.NCam = len(cams) # Numero di elementi nel vettore cam (numero di camere da calibrare)
    
    #-------------------------------------- %
    #      Distance between spots           %
    # --------------------------------------%
    data.pasX = 10.0      # passo della griglia lungo X
    data.pasY = 10.0      # passo della griglia lungo Y
    #-------------------------------------- %
    #      Calibration parameters           %
    # --------------------------------------%

    data.Threshold = 0.6  # valore percentuale della soglia
    data.FlagPos = 1      # Tipo ricerca pallino 1 CC 2 Interp 3 geom Positivi pallini bianchi negativi pallini neri 4 e 5 TopHat piu gaussiana 6 gaussiana

    
    #Cal = (TipoCal >> CalFlags.SHIFT) & CalFlags.MASK;
    #Cyl = (TipoCal >> CalFlags.SHIFT_CYL) & CalFlags.MASK;
    
    data.raggioInizialeRicerca=37
    calType=0
    data.TipoCal=self.toTipoCal(calType,0,1,0,0,0)#Type,F_Ph,F_Pl,F_Sa,P_Cyl,P_Ph=0,0,1,0,0,0 # Calibration type [Type F_Ph F_Pl F_Sa P_Cyl P_Ph] 	


    
    #-------------------------------------- %
    #            Image Parameters           %
    # --------------------------------------%

    data.ImgW=1104
    data.ImgH=1996
    data.ColPart=0
    data.RigaPart=0
    #-------------------------------------- %
    #           Target parameters           %
    # --------------------------------------%

    data.TipoTarget = 0 # Tipo di target 0 normale singolo piano 1 doppio piano con dx dy sfalsato al 50%)
    data.dx = 5         # TipoTarget==1 sfasamento fra i piani target altirmenti non utlizzato
    data.dy = 5         # TipoTarget==1 sfasamento fra i piani target altirmenti non utlizzato
    data.dz = 1.0       # TipoTarget==1 distanza fra i piani target altirmenti non utlizzato
    if data.TipoTarget==0:      data.dx = data.dy = data.dz = 0
    data.Numpiani_PerCam=2 # numero di piani da calibrare per camera in caso di target doppio piano inserire 2 * numero di spastamenti target
    
    
    data.Numpiani = data.NCam * data.Numpiani_PerCam
    additionalPar=[34,1,0.011,10,10,1  ]   # Calibration type and parameters 	(12)  
    #aa=[self.cal.getImgRoot(p) for p in range(data.Numpiani)]
    self.cal.allocAndinit(additionalPar,0)
    for i,c in enumerate (cams):
      calVect.cam[i]=c
    # -------------------------------------- %
    #       Plane img name and coordinates   %
    # -------------------------------------- %
    calVect=self.cal.vect
    imgRoot=['JetCal_cam0_20_0', 'JetCal_cam0_20_0']# the number of items should be equal to data.Numpiani_PerCam
    z=[20 ,21]#should be set also when per plane calibration is active
    costPlanes=[[0, 0, 1, 1, 2, 2],
                [0, 0, 1, 1, 2, 2],
                [0, 0, 1, 1, 2, 2],
                [0, 0, 1, 1, 2, 2],
                ]
    orPosAndShift=[# Origin Position and Shift repeated for each plane of each  camera
                    [406.921,1085.14,0,0],
                    [456.143,994.494,0,0],]
    angAndMask=[#  Angles and e Mask coordinates repeated for each plane of each  camera
                [0.00639783,-1.56869,0,0,0,0],
                [0.00639783,-1.56869,0,0,0,0],
                ]
    
    spotDistAndRemoval=[#  Spot distances and coordinate for the removal of points repeated for each plane of each  camera
                        [121,180,0,0,0,0],
                        [121,180,0,0,0,0],
                        ]
    for p1 in range(data.Numpiani_PerCam):
      for c in range(data.NCam):
        p=p1+c*data.Numpiani_PerCam
        self.cal.setImgRoot(p,imgRoot[p1])
        
        
        if FlagCfgAutoGen:
          calVect.z[p]   = z[p]
          calVect.XOr[p]  = orPosAndShift[p][0] + data.ColPart
          calVect.YOr[p]  = orPosAndShift[p][1] + data.RigaPart
          calVect.angCol[p]  = angAndMask[p][0]
          calVect.angRow[p]  = angAndMask[p][1]

          calVect.xOrShift[p] = round(orPosAndShift[p][2])
          calVect.yOrShift[p] = round(orPosAndShift[p][3])

          self.cal.setPuTrovaCC(angAndMask[p][2:],p)
          #self.cal.getPuTrovaCC(p)
          calVect.dColPix[p] = round(spotDistAndRemoval[p][0])
          calVect.dRigPix[p] = round(spotDistAndRemoval[p][1])
          #self.cal.calcBounds(p)
          calVect.remPointsUp[p] = round(spotDistAndRemoval[p][2])
          calVect.remPointsDo[p] = round(spotDistAndRemoval[p][3])
          calVect.remPointsLe[p] = round(spotDistAndRemoval[p][4])
          calVect.remPointsRi[p] = round(spotDistAndRemoval[p][5])

          
        else:
          calVect.z[p]  =z[p1]
          calVect.xOrShift[p] = calVect.yOrShift[p] = 0
          calVect.remPointsUp[p] = calVect.remPointsDo[p] = calVect.remPointsLe[p] = calVect.remPointsRi[p] = 0
          self.cal.setPuTrovaCC([0,0,0,0],p)
          calVect.dColPix[p] =calVect.dRigPix[p] = 10000 #not really important but has to be big
        
        
      if calType!=0: #no standard calibration  planes involved
        calVect.costPlanes[p1]=costPlanes[p1]
    self.cal.allocAndinit(additionalPar,1)
    if calType >= 2:# Calibrazione piano per controllo   Legge le costanti di calibrazione
      # si devono leggere o passare le costanti di calibrazione
      for cam in range(data.NCam):
        buffer=f'{data.percorso}{data.NomeFileOut}{abs(calVect.cam[cam])}.cal'
        self.readCalFile(buffer,calVect.cost[cam],data.NumCostCalib)
    self.cal.allocAndinit(additionalPar,2)
    return FlagCfgAutoGen
  
  def initDataDoppio_Ger(self)->int:
                    
    #-------------------------------------- %
    #      Not in cfg       %
    # --------------------------------------%
    data=self.cal.data
    calVect=self.cal.vect
    FlagCfgAutoGen=0 # auto start as when already processed in this case some additional vectors are needed
    
    data.PercErrMax = 0.1        # 0.10 Percentuale massima per errore in posizioneTom da modificare 
    
    #data.PercRaggioRicerca = 0.4 # 0.40 Not used any more
    # InitParOptCalVi(&dati->POC); #todo
  
    #-------------------------------------- %
    #      Input and Output parameters       %
    # --------------------------------------%
    
    data.percorso = '../CALVI_GUI/testCase/'   #percorso file di input
    data.EstensioneIn = '.tif' #estensione in (b16 o tif)
    data.FlagCam=0   #se =-1 non fa nulla se positivo aggiunge _cam# alla fine del nome img  e non mette il numero
    data.percorsoOut = '../CALVI_GUI/testCase/' # percorso file di output
    data.NomeFileOut = 'cal' # nome file di output
    cams=[0]
    data.NCam = len(cams) # Numero di elementi nel vettore cam (numero di camere da calibrare)
    
    #-------------------------------------- %
    #      Distance between spots           %
    # --------------------------------------%
    data.pasX = 5.0      # passo della griglia lungo X
    data.pasY = 5.0      # passo della griglia lungo Y
    #-------------------------------------- %
    #      Calibration parameters           %
    # --------------------------------------%

    data.Threshold = 0.5  # valore percentuale della soglia
    data.FlagPos = 1      # Tipo ricerca pallino 1 CC 2 Interp 3 geom Positivi pallini bianchi negativi pallini neri 4 e 5 TopHat piu gaussiana 6 gaussiana

    
    #Cal = (TipoCal >> CalFlags.SHIFT) & CalFlags.MASK;
    #Cyl = (TipoCal >> CalFlags.SHIFT_CYL) & CalFlags.MASK;
    
    data.raggioInizialeRicerca=35
    calType=0
    data.TipoCal=self.toTipoCal(calType,1,1,0,0,0)#Type,F_Ph,F_Pl,F_Sa,P_Cyl,P_Ph=0,0,1,0,0,0 # Calibration type [Type F_Ph F_Pl F_Sa P_Cyl P_Ph] 	


    
    #-------------------------------------- %
    #            Image Parameters           %
    # --------------------------------------%

    data.ImgW=2050
    data.ImgH=1050
    data.ColPart=0
    data.RigaPart=0
    #-------------------------------------- %
    #           Target parameters           %
    # --------------------------------------%

    data.TipoTarget = 0 # Tipo di target 0 normale singolo piano 1 doppio piano con dx dy sfalsato al 50%)
    data.dx = 5         # TipoTarget==1 sfasamento fra i piani target altirmenti non utlizzato
    data.dy = 5         # TipoTarget==1 sfasamento fra i piani target altirmenti non utlizzato
    data.dz = 10.0       # TipoTarget==1 distanza fra i piani target altirmenti non utlizzato
    if data.TipoTarget==0:      data.dx = data.dy = data.dz = 0
    data.Numpiani_PerCam=3 # numero di piani da calibrare per camera in caso di target doppio piano inserire 2 * numero di spastamenti target
    
    
    data.Numpiani = data.NCam * data.Numpiani_PerCam
    additionalPar=[14,1,0.0065 ]   # Calibration type and parameters 	(12)  
    #aa=[self.cal.getImgRoot(p) for p in range(data.Numpiani)]
    self.cal.allocAndinit(additionalPar,0)
    for i,c in enumerate (cams):
      calVect.cam[i]=c
    # -------------------------------------- %
    #       Plane img name and coordinates   %
    # -------------------------------------- %
    calVect=self.cal.vect
    imgRoot=['-10mm','0mm', '10mm']# the number of items should be equal to data.Numpiani_PerCam
    z=[-10,0 ,10]#should be set also when per plane calibration is active
    costPlanes=[[0.0, 0.0, 0.0, 0.0, 0.0, -10.0 ],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0 ],
                [0.0, 0.0, 0.0, 0.0, 0.0, 10.0 ]]
    orPosAndShift=[[0.0]*4]*data.Numpiani
    angAndMask=[[0.0]*6]*data.Numpiani
    spotDistAndRemoval=[[0.0]*6]*data.Numpiani
    """
    costPlanes=[[0, 0, 1, 1, 2, 2],
                [0, 0, 1, 1, 2, 2],
                [0, 0, 1, 1, 2, 2],
                [0, 0, 1, 1, 2, 2],
                ]
    orPosAndShift=[# Origin Position and Shift repeated for each plane of each  camera
                    [406.921,1085.14,0,0],
                    [456.143,994.494,0,0],]
    angAndMask=[#  Angles and e Mask coordinates repeated for each plane of each  camera
                [0.00639783,-1.56869,0,0,0,0],
                [0.00639783,-1.56869,0,0,0,0],
                ]
    
    spotDistAndRemoval=[#  Spot distances and coordinate for the removal of points repeated for each plane of each  camera
                        [121,180,0,0,0,0],
                        [121,180,0,0,0,0],
                        ]
    """
    for p1 in range(data.Numpiani_PerCam):
      for c in range(data.NCam):
        p=p1+c*data.Numpiani_PerCam
        self.cal.setImgRoot(p,imgRoot[p1])
        
        
        if FlagCfgAutoGen:
          calVect.z[p]   = z[p]
          calVect.XOr[p]  = orPosAndShift[p][0] + data.ColPart
          calVect.YOr[p]  = orPosAndShift[p][1] + data.RigaPart
          calVect.angCol[p]  = angAndMask[p][0]
          calVect.angRow[p]  = angAndMask[p][1]

          calVect.xOrShift[p] = round(orPosAndShift[p][2])
          calVect.yOrShift[p] = round(orPosAndShift[p][3])

          self.cal.setPuTrovaCC(angAndMask[p][2:],p)
          #self.cal.getPuTrovaCC(p)
          calVect.dColPix[p] = round(spotDistAndRemoval[p][0])
          calVect.dRigPix[p] = round(spotDistAndRemoval[p][1])
          #self.cal.calcBounds(p)
          calVect.remPointsUp[p] = round(spotDistAndRemoval[p][2])
          calVect.remPointsDo[p] = round(spotDistAndRemoval[p][3])
          calVect.remPointsLe[p] = round(spotDistAndRemoval[p][4])
          calVect.remPointsRi[p] = round(spotDistAndRemoval[p][5])

          
        else:
          calVect.z[p]  =z[p1]
          calVect.xOrShift[p] = calVect.yOrShift[p] = 0
          calVect.remPointsUp[p] = calVect.remPointsDo[p] = calVect.remPointsLe[p] = calVect.remPointsRi[p] = 0
          self.cal.setPuTrovaCC([0,0,0,0],p)
        
        
      if calType!=0: #no standard calibration  planes involved
        calVect.costPlanes[p1]=costPlanes[p1]
    self.cal.allocAndinit(additionalPar,1)
    if calType >= 2:# Calibrazione piano per controllo   Legge le costanti di calibrazione
      # si devono leggere o passare le costanti di calibrazione
      for cam in range(data.NCam):
        buffer=f'{data.percorso}{data.NomeFileOut}{abs(calVect.cam[cam])}.cal'
        self.readCalFile(buffer,calVect.cost[cam],data.NumCostCalib)
    self.cal.allocAndinit(additionalPar,2)
    
    return FlagCfgAutoGen

  def initData_P_Ger(self)->int:
                    
    #-------------------------------------- %
    #      Not in cfg       %
    # --------------------------------------%
    data=self.cal.data
    calVect=self.cal.vect
    FlagCfgAutoGen=1 # auto start as when already processed in this case some additional vectors are needed
    
    data.PercErrMax = 0.1        # 0.10 Percentuale massima per errore in posizioneTom da modificare 
    
    #data.PercRaggioRicerca = 0.4 # 0.40 Not used any more
    # InitParOptCalVi(&dati->POC); #todo
  
    #-------------------------------------- %
    #      Input and Output parameters       %
    # --------------------------------------%
    
    data.percorso = '../CALVI_GUI/testCase/'   #percorso file di input
    data.EstensioneIn = '.tif' #estensione in (b16 o tif)
    data.FlagCam=0   #se =-1 non fa nulla se positivo aggiunge _cam# alla fine del nome img  e non mette il numero
    data.percorsoOut = '../CALVI_GUI/testCase/' # percorso file di output
    data.NomeFileOut = 'cal' # nome file di output
    cams=[0]
    data.NCam = len(cams) # Numero di elementi nel vettore cam (numero di camere da calibrare)
    #-------------------------------------- %
    #      Distance between spots           %
    # --------------------------------------%
    data.pasX = 5.0      # passo della griglia lungo X
    data.pasY = 5.0      # passo della griglia lungo Y
    #-------------------------------------- %
    #      Calibration parameters           %
    # --------------------------------------%

    data.Threshold = 0.5  # valore percentuale della soglia
    data.FlagPos = 1      # Tipo ricerca pallino 1 CC 2 Interp 3 geom Positivi pallini bianchi negativi pallini neri 4 e 5 TopHat piu gaussiana 6 gaussiana

    
    #Cal = (TipoCal >> CalFlags.SHIFT) & CalFlags.MASK;
    #Cyl = (TipoCal >> CalFlags.SHIFT_CYL) & CalFlags.MASK;
    
    data.raggioInizialeRicerca=10
    calType=1
    data.TipoCal=self.toTipoCal(calType,1,1,0,0,0)#Type,F_Ph,F_Pl,F_Sa,P_Cyl,P_Ph=0,0,1,0,0,0 # Calibration type [Type F_Ph F_Pl F_Sa P_Cyl P_Ph] 	

    #-------------------------------------- %
    #            Image Parameters           %
    # --------------------------------------%

    data.ImgW=2050
    data.ImgH=1050
    data.ColPart=0
    data.RigaPart=0
    #-------------------------------------- %
    #           Target parameters           %
    # --------------------------------------%

    data.TipoTarget = 0 # Tipo di target 0 normale singolo piano 1 doppio piano con dx dy sfalsato al 50%)
    data.dx = 0         # TipoTarget==1 sfasamento fra i piani target altirmenti non utlizzato
    data.dy = 0         # TipoTarget==1 sfasamento fra i piani target altirmenti non utlizzato
    data.dz = 0       # TipoTarget==1 distanza fra i piani target altirmenti non utlizzato
    if data.TipoTarget==0:      data.dx = data.dy = data.dz = 0
    data.Numpiani_PerCam=3 # numero di piani da calibrare per camera in caso di target doppio piano inserire 2 * numero di spastamenti target
    
    
    data.Numpiani = data.NCam * data.Numpiani_PerCam
    additionalPar=[14,1,0.0065  ]   # Calibration type and parameters 	(12)  
    #aa=[self.cal.getImgRoot(p) for p in range(data.Numpiani)]
    
    self.cal.allocAndinit(additionalPar,0)
    for i,c in enumerate (cams):
      calVect.cam[i]=c
    # -------------------------------------- %
    #       Plane img name and coordinates   %
    # -------------------------------------- %
    imgRoot=['0mm', '10mm','-10mm']# the number of items should be equal to data.Numpiani_PerCam
    z=[0 ,0, 0 ,0]#should be set also when per plane calibration is active
    costPlanes=[[ 2.5e-03, -2.250e-02,  0.0e+00, 2.0e-02, -1.5e-02,  1.8775e+00],
       [ 1.34894426e-01,  2.91175150e+00,  1.98674975e+00,-8.72858866e-01, -1.99508511e+00,  4.63332625e+00],
                ]
    orPosAndShift=[# Origin Position and Shift repeated for each plane of each  camera
                    [782.439, 497.443, 0, 0], 
                    [759.74, 570.252, 0, 0], 
                    [540.461, 288.694, 0, 0], 
                    [562.007, 287.582, 0, 0]]
    

    angAndMask=[#  Angles and e Mask coordinates repeated for each plane of each  camera
                [0.00205666, -1.57294, 0, 0, 0, 0], 
                [0.0523335, -1.55305, 0, 0, 0, 0], 
                [3.13826, 1.56465, 0, 0, 0, 0], 
                [3.13769, 1.61467, 0, 0, 0, 0]
                ]
    
    spotDistAndRemoval=[#  Spot distances and coordinate for the removal of points repeated for each plane of each  camera
                        [113, 101, 0, 0, 0, 0],
                        [110, 103, 0, 0, 0, 0],
                        [105, 94, 0, 0, 0, 0] ,
                        [104, 93, 0, 0, 0, 0],
                        ]
                        
    for p1 in range(data.Numpiani_PerCam):
      for c in range(data.NCam):
        p=p1+c*data.Numpiani_PerCam
        self.cal.setImgRoot(p,imgRoot[p1])
        
        
        if FlagCfgAutoGen:
          calVect.z[p]   = z[p]
          calVect.XOr[p]  = orPosAndShift[p][0] + data.ColPart
          calVect.YOr[p]  = orPosAndShift[p][1] + data.RigaPart
          calVect.angCol[p]  = angAndMask[p][0]
          calVect.angRow[p]  = angAndMask[p][1]

          calVect.xOrShift[p] = round(orPosAndShift[p][2])
          calVect.yOrShift[p] = round(orPosAndShift[p][3])

          self.cal.setPuTrovaCC(angAndMask[p][2:],p)
          #self.cal.getPuTrovaCC(p)
          calVect.dColPix[p] = round(spotDistAndRemoval[p][0])
          calVect.dRigPix[p] = round(spotDistAndRemoval[p][1])
          #self.cal.calcBounds(p)
          calVect.remPointsUp[p] = round(spotDistAndRemoval[p][2])
          calVect.remPointsDo[p] = round(spotDistAndRemoval[p][3])
          calVect.remPointsLe[p] = round(spotDistAndRemoval[p][4])
          calVect.remPointsRi[p] = round(spotDistAndRemoval[p][5])

          
        else:
          calVect.z[p]  =z[p1]
          calVect.xOrShift[p] = calVect.yOrShift[p] = 0
          calVect.remPointsUp[p] = calVect.remPointsDo[p] = calVect.remPointsLe[p] = calVect.remPointsRi[p] = 0
          self.cal.setPuTrovaCC([0,0,0,0],p)
        
        
      if calType!=0: #no standard calibration  planes involved
        calVect.costPlanes[p1]=costPlanes[p1]
    self.cal.allocAndinit(additionalPar,1)
    if calType >= 2:# Calibrazione piano per controllo   Legge le costanti di calibrazione
      # si devono leggere o passare le costanti di calibrazione
      for cam in range(data.NCam):
        buffer=f'{data.percorso}{data.NomeFileOut}{abs(calVect.cam[cam])}.cal'
        self.readCalFile(buffer,calVect.cost[cam],data.NumCostCalib)
    self.cal.allocAndinit(additionalPar,2)
    return FlagCfgAutoGen
  
  def initData_P(self)->int:
                    
    #-------------------------------------- %
    #      Not in cfg       %
    # --------------------------------------%
    data=self.cal.data
    calVect=self.cal.vect
    FlagCfgAutoGen=1 # auto start as when already processed in this case some additional vectors are needed
    
    data.PercErrMax = 0.1        # 0.10 Percentuale massima per errore in posizioneTom da modificare 
    
    #data.PercRaggioRicerca = 0.4 # 0.40 Not used any more
    # InitParOptCalVi(&dati->POC); #todo
  
    #-------------------------------------- %
    #      Input and Output parameters       %
    # --------------------------------------%
    
    data.percorso = '../../../../../New/ProvaCAlvi/in/Pia/'   #percorso file di input
    data.EstensioneIn = '.tif' #estensione in (b16 o tif)
    data.FlagCam=0   #se =-1 non fa nulla se positivo aggiunge _cam# alla fine del nome img  e non mette il numero
    data.percorsoOut = '../../img/calib/' # percorso file di output
    data.NomeFileOut = 'cal' # nome file di output
    cams=[0 ,1]
    data.NCam = len(cams) # Numero di elementi nel vettore cam (numero di camere da calibrare)
    #-------------------------------------- %
    #      Distance between spots           %
    # --------------------------------------%
    data.pasX = 5.0      # passo della griglia lungo X
    data.pasY = 5.0      # passo della griglia lungo Y
    #-------------------------------------- %
    #      Calibration parameters           %
    # --------------------------------------%

    data.Threshold = 0.6  # valore percentuale della soglia
    data.FlagPos = -1      # Tipo ricerca pallino 1 CC 2 Interp 3 geom Positivi pallini bianchi negativi pallini neri 4 e 5 TopHat piu gaussiana 6 gaussiana

    
    #Cal = (TipoCal >> CalFlags.SHIFT) & CalFlags.MASK;
    #Cyl = (TipoCal >> CalFlags.SHIFT_CYL) & CalFlags.MASK;
    
    data.raggioInizialeRicerca=37
    calType=1
    data.TipoCal=self.toTipoCal(calType,1,1,0,0,0)#Type,F_Ph,F_Pl,F_Sa,P_Cyl,P_Ph=0,0,1,0,0,0 # Calibration type [Type F_Ph F_Pl F_Sa P_Cyl P_Ph] 	

    #-------------------------------------- %
    #            Image Parameters           %
    # --------------------------------------%
    data.ImgW=1280
    data.ImgH=800
    data.ColPart=0
    data.RigaPart=0

    #-------------------------------------- %
    #           Target parameters           %
    # --------------------------------------%

    data.TipoTarget = 0 # Tipo di target 0 normale singolo piano 1 doppio piano con dx dy sfalsato al 50%)
    data.dx = 0         # TipoTarget==1 sfasamento fra i piani target altirmenti non utlizzato
    data.dy = 0         # TipoTarget==1 sfasamento fra i piani target altirmenti non utlizzato
    data.dz = 0       # TipoTarget==1 distanza fra i piani target altirmenti non utlizzato
    if data.TipoTarget==0:      data.dx = data.dy = data.dz = 0
    data.Numpiani_PerCam=2 # numero di piani da calibrare per camera in caso di target doppio piano inserire 2 * numero di spastamenti target
    
    
    data.Numpiani = data.NCam * data.Numpiani_PerCam
    additionalPar=[14,1,0.02  ]   # Calibration type and parameters 	(12)  
    #aa=[self.cal.getImgRoot(p) for p in range(data.Numpiani)]
    
    self.cal.allocAndinit(additionalPar,0)
    for i,c in enumerate (cams):
      calVect.cam[i]=c
    # -------------------------------------- %
    #       Plane img name and coordinates   %
    # -------------------------------------- %
    imgRoot=['2mm', '1991mm']# the number of items should be equal to data.Numpiani_PerCam
    z=[0 ,0, 0 ,0]#should be set also when per plane calibration is active
    costPlanes=[[ 2.5e-03, -2.250e-02,  0.0e+00, 2.0e-02, -1.5e-02,  1.8775e+00],
       [ 1.34894426e-01,  2.91175150e+00,  1.98674975e+00,-8.72858866e-01, -1.99508511e+00,  4.63332625e+00],
                ]
    orPosAndShift=[# Origin Position and Shift repeated for each plane of each  camera
                    [782.439, 497.443, 0, 0], 
                    [759.74, 570.252, 0, 0], 
                    [540.461, 288.694, 0, 0], 
                    [562.007, 287.582, 0, 0]]
    

    angAndMask=[#  Angles and e Mask coordinates repeated for each plane of each  camera
                [0.00205666, -1.57294, 0, 0, 0, 0], 
                [0.0523335, -1.55305, 0, 0, 0, 0], 
                [3.13826, 1.56465, 0, 0, 0, 0], 
                [3.13769, 1.61467, 0, 0, 0, 0]
                ]
    
    spotDistAndRemoval=[#  Spot distances and coordinate for the removal of points repeated for each plane of each  camera
                        [113, 101, 0, 0, 0, 0],
                        [110, 103, 0, 0, 0, 0],
                        [105, 94, 0, 0, 0, 0] ,
                        [104, 93, 0, 0, 0, 0],
                        ]
                        
    for p1 in range(data.Numpiani_PerCam):
      for c in range(data.NCam):
        p=p1+c*data.Numpiani_PerCam
        self.cal.setImgRoot(p,imgRoot[p1])
        
        
        if FlagCfgAutoGen:
          calVect.z[p]   = z[p]
          calVect.XOr[p]  = orPosAndShift[p][0] + data.ColPart
          calVect.YOr[p]  = orPosAndShift[p][1] + data.RigaPart
          calVect.angCol[p]  = angAndMask[p][0]
          calVect.angRow[p]  = angAndMask[p][1]

          calVect.xOrShift[p] = round(orPosAndShift[p][2])
          calVect.yOrShift[p] = round(orPosAndShift[p][3])

          self.cal.setPuTrovaCC(angAndMask[p][2:],p)
          #self.cal.getPuTrovaCC(p)
          calVect.dColPix[p] = round(spotDistAndRemoval[p][0])
          calVect.dRigPix[p] = round(spotDistAndRemoval[p][1])
          #self.cal.calcBounds(p)
          calVect.remPointsUp[p] = round(spotDistAndRemoval[p][2])
          calVect.remPointsDo[p] = round(spotDistAndRemoval[p][3])
          calVect.remPointsLe[p] = round(spotDistAndRemoval[p][4])
          calVect.remPointsRi[p] = round(spotDistAndRemoval[p][5])

          
        else:
          calVect.z[p]  =z[p1]
          calVect.xOrShift[p] = calVect.yOrShift[p] = 0
          calVect.remPointsUp[p] = calVect.remPointsDo[p] = calVect.remPointsLe[p] = calVect.remPointsRi[p] = 0
          self.cal.setPuTrovaCC([0,0,0,0],p)
          calVect.dColPix[p] =calVect.dRigPix[p] = 10000 #not really important but has to be big
        
        
      if calType!=0: #no standard calibration  planes involved
        calVect.costPlanes[p1]=costPlanes[p1]
    self.cal.allocAndinit(additionalPar,1)
    if calType >= 2:# Calibrazione piano per controllo   Legge le costanti di calibrazione
      # si devono leggere o passare le costanti di calibrazione
      for cam in range(data.NCam):
        buffer=f'{data.percorso}{data.NomeFileOut}{abs(calVect.cam[cam])}.cal'
        self.readCalFile(buffer,calVect.cost[cam],data.NumCostCalib)
    self.cal.allocAndinit(additionalPar,2)
    return FlagCfgAutoGen
  
  
  def initData_P_Piano(self)->int:
                    
    #-------------------------------------- %
    #      Not in cfg       %
    # --------------------------------------%
    data=self.cal.data
    calVect=self.cal.vect
    FlagCfgAutoGen=1 # auto start as when already processed in this case some additional vectors are needed
    
    data.PercErrMax = 0.1        # 0.10 Percentuale massima per errore in posizioneTom da modificare 
    
    #data.PercRaggioRicerca = 0.4 # 0.40 Not used any more
    # InitParOptCalVi(&dati->POC); #todo
  
    #-------------------------------------- %
    #      Input and Output parameters       %
    # --------------------------------------%
    data.percorso = '../../../../../New/ProvaCAlvi/in/Pia/'   #percorso file di input
    data.EstensioneIn = '.tif' #estensione in (b16 o tif)
    data.FlagCam=0   #se =-1 non fa nulla se positivo aggiunge _cam# alla fine del nome img  e non mette il numero
    data.percorsoOut = '../../img/calib/' # percorso file di output
    data.NomeFileOut = 'cal' # nome file di output
    cams=[0 ,1]
    data.NCam = len(cams) # Numero di elementi nel vettore cam (numero di camere da calibrare)

    #-------------------------------------- %
    #      Distance between spots           %
    # --------------------------------------%
    data.pasX = 5.0      # passo della griglia lungo X
    data.pasY = 5.0      # passo della griglia lungo Y
    #-------------------------------------- %
    #      Calibration parameters           %
    # --------------------------------------%

    data.Threshold = 0.6  # valore percentuale della soglia
    data.FlagPos = -1      # Tipo ricerca pallino 1 CC 2 Interp 3 geom Positivi pallini bianchi negativi pallini neri 4 e 5 TopHat piu gaussiana 6 gaussiana

    
    #Cal = (TipoCal >> CalFlags.SHIFT) & CalFlags.MASK;
    #Cyl = (TipoCal >> CalFlags.SHIFT_CYL) & CalFlags.MASK;
    
    data.raggioInizialeRicerca=37
    calType=2
    data.TipoCal=self.toTipoCal(calType,1,1,0,0,0)#Type,F_Ph,F_Pl,F_Sa,P_Cyl,P_Ph=0,0,1,0,0,0 # Calibration type [Type F_Ph F_Pl F_Sa P_Cyl P_Ph] 	

    #-------------------------------------- %
    #            Image Parameters           %
    # --------------------------------------%

    data.ImgW=1280
    data.ImgH=800
    data.ColPart=0
    data.RigaPart=0
    #-------------------------------------- %
    #           Target parameters           %
    # --------------------------------------%

    data.TipoTarget = 0 # Tipo di target 0 normale singolo piano 1 doppio piano con dx dy sfalsato al 50%)
    data.dx = 0         # TipoTarget==1 sfasamento fra i piani target altirmenti non utlizzato
    data.dy = 0         # TipoTarget==1 sfasamento fra i piani target altirmenti non utlizzato
    data.dz = 0       # TipoTarget==1 distanza fra i piani target altirmenti non utlizzato
    if data.TipoTarget==0:      data.dx = data.dy = data.dz = 0
    data.Numpiani_PerCam=1 # numero di piani da calibrare per camera in caso di target doppio piano inserire 2 * numero di spastamenti target
    
    
    data.Numpiani = data.NCam * data.Numpiani_PerCam
    additionalPar=[14,1,0.02  ]   # Calibration type and parameters 	(12)  
    #aa=[self.cal.getImgRoot(p) for p in range(data.Numpiani)]
    
    self.cal.allocAndinit(additionalPar,0)
    for i,c in enumerate (cams):
      calVect.cam[i]=c
    # -------------------------------------- %
    #       Plane img name and coordinates   %
    # -------------------------------------- %
    imgRoot=['2mm', '1991mm']# the number of items should be equal to data.Numpiani_PerCam
    z=[0 ,0, 0 ,0]#should be set also when per plane calibration is active
    costPlanes=[[ -3.60015048016046e+02, -2.07316568271620e-02 ,-1.79997723561649e+02, 5.02013720544883e+00, 4.98453013490223e+00, 1.87393988788882e+00 ],
      
                ]
    orPosAndShift=[# Origin Position and Shift repeated for each plane of each  camera
                    [782.439, 497.443, 0, 0], 
                    [540.461, 288.694, 0, 0], 
                  ]
    

    angAndMask=[#  Angles and e Mask coordinates repeated for each plane of each  camera
                [-3.14044 ,-1.57307, 0, 0, 0, 0], 
                [-0.00289468 ,1.57463 , 0, 0, 0, 0], 
                
                ]
    
    spotDistAndRemoval=[#  Spot distances and coordinate for the removal of points repeated for each plane of each  camera
                        [110, 101, 0, 0, 0, 0],
                        [107, 94, 0, 0, 0, 0] ,
                        ]
                        
    for p1 in range(data.Numpiani_PerCam):
      for c in range(data.NCam):
        p=p1+c*data.Numpiani_PerCam
        self.cal.setImgRoot(p,imgRoot[p1])
        
        
        if FlagCfgAutoGen:
          calVect.z[p]   = z[p]
          calVect.XOr[p]  = orPosAndShift[p][0] + data.ColPart
          calVect.YOr[p]  = orPosAndShift[p][1] + data.RigaPart
          calVect.angCol[p]  = angAndMask[p][0]
          calVect.angRow[p]  = angAndMask[p][1]

          calVect.xOrShift[p] = round(orPosAndShift[p][2])
          calVect.yOrShift[p] = round(orPosAndShift[p][3])

          self.cal.setPuTrovaCC(angAndMask[p][2:],p)
          #self.cal.getPuTrovaCC(p)
          calVect.dColPix[p] = round(spotDistAndRemoval[p][0])
          calVect.dRigPix[p] = round(spotDistAndRemoval[p][1])
          #self.cal.calcBounds(p)
          calVect.remPointsUp[p] = round(spotDistAndRemoval[p][2])
          calVect.remPointsDo[p] = round(spotDistAndRemoval[p][3])
          calVect.remPointsLe[p] = round(spotDistAndRemoval[p][4])
          calVect.remPointsRi[p] = round(spotDistAndRemoval[p][5])

          
        else:
          calVect.z[p]  =z[p1]
          calVect.xOrShift[p] = calVect.yOrShift[p] = 0
          calVect.remPointsUp[p] = calVect.remPointsDo[p] = calVect.remPointsLe[p] = calVect.remPointsRi[p] = 0
          self.cal.setPuTrovaCC([0,0,0,0],p)
          calVect.dColPix[p] =calVect.dRigPix[p] = 10000 #not really important but has to be big
        
        
      if calType!=0: #no standard calibration  planes involved
        calVect.costPlanes[p1]=costPlanes[p1]
    self.cal.allocAndinit(additionalPar,1)
    if calType >= 2:# Calibrazione piano per controllo   Legge le costanti di calibrazione
      # si devono leggere o passare le costanti di calibrazione
      for cam in range(data.NCam):
        buffer=f'{data.percorso}{data.NomeFileOut}{abs(calVect.cam[cam])}.cal'
        self.readCalFile(buffer,calVect.cost[cam],data.NumCostCalib)
    self.cal.allocAndinit(additionalPar,2)
    return FlagCfgAutoGen

      

        
  def readCalFile(self,buffer:str,cost:list[float],numCostCalib:int,calType:int=None):
    ''' reads the calibration constants from a file 
      buffer is the name of the file
      if cost and numCostCalib are normally None in this case they are initialized internally
      if cost is different from none should be large enough to contain the constants
      if numCostCalib is different from none it is used regardless of the value in  the file
      In output returns flagCal,N,cost 
    '''
    try:
      with open(buffer,'r') as f:
        tag=readCfgTag(f)
        
        if tag != "%SP00015":
          raise RuntimeError(f'Wrong tag in file: {buffer}') 
        ind=1
        #ind,flagCal=readNumVecCfg(f,ind,int)
        ind,flagCal=readNumCfg(f,ind,int)
        ind,parNumber=readNumCfg(f,ind,int)
        N=parNumber if numCostCalib is None else numCostCalib 

        def fCalType(c):
          if c in (1,2,3): t=c
          elif c>=10 and c<15: t=10
          elif c>=30 and c<39: t=30
          return t
        
        if calType:
          FlagCylFromPinhole=fCalType(flagCal)==10 and fCalType(calType)==30
          if fCalType(flagCal)!=fCalType(calType) and not FlagCylFromPinhole:
            CamMod_items=['polynomial', #0
                'rational',             #1
                'tri-polynomial',       #2
                'pinhole',              #3
                'pinhole + cylinder',   #4
                ]
            CamMod_id=[1,2,3,10,30]
            file_CamMod=CamMod_items[CamMod_id.index(fCalType(flagCal))]
            excepted_CamMod=CamMod_items[CamMod_id.index(fCalType(calType))]
            raise RuntimeError(f'Wrong type of camera calibration model in file: {buffer}. Found {file_CamMod}, expected {excepted_CamMod} camera model.') 
        else:
          FlagCylFromPinhole=False
        
        if FlagCylFromPinhole: 
          flagCal+=-10+30
          N=28
        if cost is None:
          cost=[0]*N
        if not FlagCylFromPinhole:
          for i in range(N):# dati->NumCostCalib; i++):
            ind,cost[i]=readNumCfg(f,ind,float)
        else:
          for i in range(17):# dati->NumCostCalib; i++):
            ind,cost[i]=readNumCfg(f,ind,float)
          ind,cost[26]=readNumCfg(f,ind,float)
          ind,cost[27]=readNumCfg(f,ind,float)


        #if "%SP00015"
        #for index, line in enumerate(f):              pri.Info.white("Line {}: {}".format(index, line.strip()))
    #except Exception as exc: 
    except IOError as exc: 
      raise RuntimeError(f'Error opening the calibration constants file: {buffer}') from exc
    except ValueError as exc: 
      raise RuntimeError(f'Error reading line:{ind+1} of file: {buffer}') from exc
    except IndexError as exc: 
      raise RuntimeError(f'Error reading array in line:{ind+1} of file: {buffer}') from exc  
    
 
  def toTipoCal(self,type ,F_Ph,F_Pl,F_Sa,P_Cyl,P_Ph):
    ''' from parameters to tipoCal
    type is the type of calibration 
    F_Ph, F_Pl, F_Sa are boolean to activate the relative function (PinHole, Plane, or save Line of sights)
    P_Cyl are additional parameters for cylindrical calibration
    P_Ph are additional parameters for PinHole not used
    
    Vecchi tipi di calibrazione
                                                                     type | F_Ph   |  F_Pia  |  F_SA_LinVista
    0 Normale                                                         0   |        |         |
    (-1) Calibrazione per piani                                       1   |  x     |Implicito|
    (-2) Calibrazione singolo(multi) piano                            2   |        |Implicito|
    (-3) Calibrazione Cyl No Pinhole Si Piani	                        3   |        |  x      |
    (-4) Calibrazione Cyl Si  Pinhole NO Piani                        3   |  x     |         |
    (-5) Calibrazione Cyl Si  Pinhole Si  Piani                       3   |  x     |  x      |
    (-6) Calibrazione Cyl Si  Pinhole No Piani                        3   |  x     |         |
    (-7) Calibrazione Cyl SI Pinhole Si Piani anche linee vista	      3   |  x     |  x      |  x
    (-8) Calibrazione Cyl SI Pinhole No Piani anche linee vista	      3   |  x     |         |  x
    (-10) SelfCal                                                     10
    In questo momento type è un numero (0:15)
    F_Ph, F_Pia e F_SA_LinVista sono booleani
    In aggiunta sono previsti due parametri aggiuntivi P_CYL (vedi IntiCostMin) e P_PH (per ora non utilizzato)
    Di seguito i dettagli
    
    // long flagCal
    // Per ora usati solo i primi 2 byte in particolare ogni cifra esadecimale � usata per uno scopo 
    // per inserire i dati supponendo che type sia il primo blocco, Cyl il secondo, PH il terzo e si voglia attivare solo il flag PIANI
    //   int flagCal =type + (Cyl << CalFlags.SHIFT_CYL) + (PH<<CalFlags.SHIFT_PH)+CalFlags.FLAG_PIANI;
    
    int type = 3, PH = 4, Cyl = 10;
    int tipoCal = type + (P_Cyl << CalFlags.SHIFT_CYL)+(P_Ph << CalFlags.SHIFT_PH) + (F_Ph *CalFlags.Flag_PINHOLE)
                      + (F_Pl*CalFlags.Flag_PIANI)+F_Sa*CalFlags.Flag_LIN_VI
    cal = (tipoCal >> CalFlags.SHIFT) & CalFlags.MASK
    P_Cyl = (tipoCal >> CalFlags.SHIFT_CYL) & CalFlags.MASK
    P_Ph = (tipoCal >> CalFlags.SHIFT_PH) & CalFlags.MASK
    F_Ph = tipoCal  & CalFlags.Flag_PINHOLE
    F_Pl = tipoCal  & CalFlags.Flag_PIANI
    F_Sa = tipoCal  & CalFlags.Flag_LIN_VI
    
    '''
    return type + (P_Cyl << CalFlags.SHIFT_CYL)+(P_Ph << CalFlags.SHIFT_PH) + (F_Ph *CalFlags.Flag_PINHOLE)+ (F_Pl*CalFlags.Flag_PIANI)+F_Sa*CalFlags.Flag_LIN_VI
  def fromTipoCal(self,tipoCal):
    ''' from parameters to tipoCal 
    call with 
    type,F_Ph,F_Pl,F_Sa,P_Cyl,P_Ph=self.fromTipoCal(tipoCal)
    type is the type of calibration 
    F_Ph, F_Pl, F_Sa are bolean to activate the relative function (PinHole, Plane, or save Line of sights)
    P_Cyl are additional parameters for cylindrical calibration
    P_Ph are additional parameters for PinHole not used'''
    type = (tipoCal >> CalFlags.SHIFT) & CalFlags.MASK
    P_Cyl = (tipoCal >> CalFlags.SHIFT_CYL) & CalFlags.MASK
    P_Ph = (tipoCal >> CalFlags.SHIFT_PH) & CalFlags.MASK
    F_Ph = tipoCal  & CalFlags.Flag_PINHOLE
    F_Pl = tipoCal  & CalFlags.Flag_PIANI
    F_Sa = tipoCal  & CalFlags.Flag_LIN_VI
    return type,F_Ph,F_Pl,F_Sa,P_Cyl,P_Ph

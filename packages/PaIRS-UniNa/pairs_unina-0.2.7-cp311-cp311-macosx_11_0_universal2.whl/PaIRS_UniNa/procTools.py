''' 2d PIV helper function for parfor   '''
from  datetime import timedelta
import os.path

# In hex is easy 0606 both read and processed 01234156789abcdef 
FLAG_READ_ERR = [1, 1<<8] #2, 256=                    0001    1   0001 0000 0000
FLAG_READ = [2 ,1<<9] #1<<9=2**9=512                  0010    2
FLAG_PROC = [1<<2 ,1<<10] #8 ,1024                    0100    4
FLAG_FINALIZED = [1<<3  ,1<<11] #completely processed 1000    8
# In hex is easy 0E0E both read, processed and finalized
FLAG_CALLBACK_INTERNAL = 1<<16 #on if the callback has been called in its internal parts   
FLAG_GENERIC_ERROR = 1<<17 #on if the callback has been called in its internal parts   
FLAG_PROC_AB =FLAG_PROC[0]|FLAG_PROC[1]  #4+1024=1028=x404 se si somma anche FLAG_READ  6+1536=1542=x606
FLAG_FINALIZED_AB =FLAG_FINALIZED[0]|FLAG_FINALIZED[1]  
FLAG_PROC_OR_ERR=[ p|e for (p,e) in zip(FLAG_PROC,FLAG_READ_ERR)]
FLAG_FINALIZED_OR_ERR = [ p|e for (p,e) in zip(FLAG_FINALIZED,FLAG_READ_ERR)]
# usare con 
# supponendo che k sia 0 (img a) o 1 (img b) 
# if pim(i)&FLAG_PROC[k]: allora img i, k processata
# per annullare un bit f=f& (~FLAG_CALLBACK)

from .PaIRS_pypacks import*
from .Input_Tab import INPpar as INPpar
from .Output_Tab import OUTpar as OUTpar
from .Output_Tab import outType_dict
from .Process_Tab import PROpar as PROpar
from .Process_Tab_Min import PROpar_Min as PROpar_Min
from .Process_Tab_Disp import PROpar_Disp as PROpar_Disp
from .Vis_Tab import VISpar as VISpar
from .Vis_Tab import NamesPIV
from .TabTools import TABpar
from .readcfg import readCalFile
from .__init__ import __version__,__subversion__,__year__

processData = {
        ProcessTypes.min:  {'name': 'Pre-process', 'caption': 'Pre-process analysis of a set of images aimed at computing historical minimum background',
         'class': 0, 'icon': 'min_proc.png', 
         'children': {StepTypes.min:True}, 'mandatory': [StepTypes.min]},
        ProcessTypes.piv:  {'name': 'PIV process', 'caption': 'Particle Image Velocimetry analysis for computation of the two-dimensional two-component velocity field',
         'class': 0, 'icon': 'piv_proc.png', 
         'children': {StepTypes.min:False,StepTypes.piv:True}, 'mandatory': [StepTypes.piv]},
        ProcessTypes.cal: {'name': 'Calibration', 'caption': 'Accurate optical calibration of single and multiple camera bundles',
         'class': 0, 'icon': 'cal_proc.png', 
         'children': {StepTypes.cal:True}, 'mandatory': [StepTypes.cal]},   
        ProcessTypes.spiv:  {'name': 'Stereo-PIV process', 'caption': 'Stereoscopic Particle Image Velocimetry analysis for computation of the two-dimensional three-component velocity field',
         'class': 0, 'icon': 'spiv_proc.png', 
         'children': {StepTypes.cal:True,StepTypes.min:False,StepTypes.disp:True,StepTypes.spiv:True},'mandatory': [StepTypes.cal]},
        }
for p in processData:
    processData[p]['type']=p
    
stepData= {
        StepTypes.cal: {'name': 'Camera calibration', 'caption': 'Select an appropriate camera model and estimate the parameters of the mapping functions based on calibration target images',
         'class': 1, 'icon': 'cal_step.png', 'parents': [],
         'tabs': ['Calibration','Input_CalVi','Process_CalVi','Vis_CalVi'], },    
        StepTypes.min: {'name': 'Image pre-processing', 'caption': 'Select a set of particle images and compute the historical minimum background for subsets corresponding to the same laser light source',
         'class': 1, 'icon': 'min_step.png', 'parents': [],
         'tabs': ['Input','Output','Process_Min','Log','Vis'], },        
        StepTypes.piv: {'name': 'PIV analysis', 'caption': 'Select a set of particle images, craft a custom iterative multi-grid method and compute the two-dimensional two-component displacement field',
         'class': 1, 'icon': 'piv_step.png', 'parents': [],
         'tabs': ['Input','Output','Process','Log','Vis'], },   
        StepTypes.disp: {'name': 'Disparity correction', 'caption': 'Select a a set of particle images and compute the laser sheet position and orientation to adjust the camera disparities in the stereo-setup',
         'class': 1, 'icon': 'disp_step.png', 'parents': [StepTypes.cal],
         'tabs': ['Input','Output','Process_Disp','Log','Vis'], },   
        StepTypes.spiv: {'name': 'Stereoscopic PIV analysis', 'caption': 'Select a set of particle images, craft a custom iterative multi-grid method and compute the two-dimensional three-component displacement field',
         'class': 1, 'icon': 'piv_step.png', 'parents': [StepTypes.cal,StepTypes.disp],
         'tabs': ['Input','Output','Process','Log','Vis'], },   
         }
for p in stepData:
    stepData[p]['type']=p

class dataTreePar(TABpar):
    def __init__(self,Process=ProcessTypes.null,Step=StepTypes.null):
        self.setup(Process,Step)
        super().__init__('dataTreePar','ITEpar')

        self.setCompleteLog()
        
        self.surname='itemTreePar.gPaIRS'
        self.unchecked_fields+=['name_fields']
        self.uncopied_fields+=['ind']

    def setup(self,Process,Step):
        #typeProc, names, icon, log: item fields
        self.Process=Process
        self.Step=Step
        self.namesPIV=NamesPIV(Step)

        if Step:
          self.itemname=stepData[Step]['name']
        else: 
          self.itemname=''
        self.filename_proc = ''
        self.name_proc = ''

        self.Log=''
        self.procLog=['','','']  #LogProc, LogStat, LogErr
        self.FlagErr=False
        self.warnings=['',''] #warnings once completed the process, warnings related to current state

        self.item_fields=[f for f,_ in self.__dict__.items()]+['ind']

        #common data
        self.inpPath=''
        self.outPath=''
        self.outPathRoot=''
        self.ndig=-1
        self.outExt=''
        self.compMin:CompMin=CompMin()
        self.mediaPIV:MediaPIV=MediaPIV(stepType=Step)
        #if Step==StepTypes.min:
        self.FlagTR = False
        self.LaserType = False
        self.SogliaNoise_Min = 0.0
        self.SogliaStd_Min   = 100.0
        
        #elif Step in (StepTypes.piv, StepTypes.disp, StepTypes.spiv):
          #common
        self.FlagMIN=False
        self.Imin=[]
        
        self.dispFrames=0

        self.numUsedProcs=1
        self.numPivOmpCores=-1 # used by PIV_ParFor_Workerfor setting the correct number of threads

        self.OUT_dict={}
        self.PRO_dict={}
        self.PRO_Disp_dict={}

        self.Nit=0
        self.nimg=0
        self.ncam=0
        self.nframe=2
        self.nsteps=0
        self.list_Image_Files=[]
        self.list_eim=[]
        self.list_pim=[]        
        self.list_print=[]

        #if Step in (StepTypes.disp, StepTypes.spiv):
        self.calList=[]
        self.calEx=[]
        self.res=0
        self.laserConst=[0.0 for _ in range(3)]
        
        #if Step==StepTypes.spiv:
        self.FlagDISP=False
        #self.dispFile=''

        fields=[f for f,_ in self.__dict__.items()]
        self.numCallBackTotOk=0  #numero di callback ricevute= quelle con problema + finalized
        self.numFinalized=0   #numero di processi andati a buon fine
        self.numProcOrErrTot=0
        self.FlagFinished=False
        self.flagParForCompleted=False  # par for completed                

        # processing time
        self.initProcTime=time()  #initial time qhen starting the process
        self.eta=0  # expexted time to finish the process
        self.procTime=0 # processing time 
        self.timePerImage=0
        
        #interface
        self.freset_par=''
        self.procfields=[f for f,_ in self.__dict__.items() if f not in fields]+ ['compMin','mediaPIV']

        self.assignDataName()
        return

    def resF(self,i,string=''):
        if self.ndig<-1: return ''
        if string=='dispMap':
          fold=os.path.dirname(self.outPathRoot)
          rad=os.path.splitext(os.path.basename(self.outPathRoot))[0]
          if rad[-1]!='_': rad+='_'
          return myStandardRoot(os.path.join(fold, f'dispMap_rot_{rad}{i}.png'))
        else:
          if type(i)==str:
              return f"{self.outPathRoot}_{i}{self.outExt}"
          elif type(i)==int:
                return f"{self.outPathRoot}_{i:0{self.ndig:d}d}{self.outExt}"
          else:
              return ''

    def setProc(self,INP:INPpar=INPpar(),OUT:OUTpar=OUTpar(),PRO:PROpar=PROpar(),PRO_Min:PROpar_Min=PROpar_Min(),PRO_Disp:PROpar_Disp=PROpar_Disp()):
        if INP is None: return
        self.inpPath=INP.path
        self.outPath=myStandardRoot(OUT.path+OUT.subfold)
        self.outPathRoot=myStandardRoot(OUT.path+OUT.subfold+OUT.root)
        
        if self.Step==StepTypes.disp:
           self.list_Image_Files=INP.imList
           self.list_eim=INP.imEx
        else:
          self.list_Image_Files=[]
          self.list_eim=[]
          for c in range(INP.ncam):
            for k in range(INP.nimg):
              for f in range(2):
                  self.list_Image_Files.append(INP.imList[c][f][k])
                  self.list_eim.append(INP.imEx[c][f][k])
        self.ncam=len(INP.imList)
        self.FlagTR=INP.FlagTR
        self.LaserType=INP.LaserType
        self.FlagMIN=INP.FlagMIN
        self.Imin=INP.imListMin
        
        if self.Step==StepTypes.min:
            self.compMin.outName   = self.outPathRoot+'_data'+outExt.min
            self.compMin.name_proc = self.name_proc
            self.compMin.flag_TR=self.FlagTR
            self.compMin.LaserType=self.LaserType
            self.compMin.setup(self.ncam,self.nframe)
            self.nimg=(len(self.list_Image_Files)//(2*self.ncam)+1)//2 if self.FlagTR else len(self.list_Image_Files)//(2*self.ncam)
        elif self.Step in (StepTypes.piv,StepTypes.disp,StepTypes.spiv):
            if self.Step==StepTypes.piv:
               self.mediaPIV.outName   = self.outPathRoot+'_data'+outExt.piv
               self.mediaPIV.name_proc = self.name_proc
            elif self.Step==StepTypes.spiv:
               self.mediaPIV.outName   = self.outPathRoot+'_data'+outExt.spiv
               self.mediaPIV.name_proc = self.name_proc
            self.nimg=INP.nimg
            self.ndig=len(str(self.nimg))
            self.outExt=list(outType_dict)[OUT.outType]
            self.numUsedProcs=self.numUsedProcs  #TODEL 
        if self.Step in (StepTypes.disp,StepTypes.spiv):
           self.calList=INP.calList
           self.calEx  =INP.calEx
        if self.Step==StepTypes.disp:
           self.Nit = PRO_Disp.Nit
           self.dispFrames = PRO_Disp.frames
        #if self.Step==StepTypes.spiv:
           #self.FlagDISP=INP.FlagDISP
           #self.dispFile=INP.dispFile

        self.nsteps=self.Nit if self.Step==StepTypes.disp else self.nimg
        self.list_pim=[0]*self.nsteps
        self.list_print=['']*self.nsteps

        if PRO_Min:
          self.SogliaNoise_Min=PRO_Min.SogliaNoise
          self.SogliaStd_Min=PRO_Min.SogliaStd
        
        for f,v in OUT.duplicate().__dict__.items():
          self.OUT_dict[f]=v
        if self.Step in (StepTypes.piv,StepTypes.spiv):
          for f,v in PRO.duplicate().__dict__.items():
            self.PRO_dict[f]=v
        if self.Step == StepTypes.disp:
           for f,v in PRO_Disp.duplicate().__dict__.items():
              self.PRO_Disp_dict[f]=v
        #self.setPIV(OUT,PRO,flagSpiv)
    
    def assignDataName(self):
        self.name_proc,_,_=identifierName(typeObject='proc')
        
        if self.Step!=StepTypes.null:
          self.itemname=stepData[self.Step]['name']
          for f,v in StepTypes.__dict__.items():
            if v==self.Step: 
              break
          ext=getattr(outExt,f)
          self.filename_proc=f"{self.outPathRoot}{ext}"
        
    def procOutName(self):
      return procOutName(self)
    
    def stepOutName(self):
      return stepOutName(self)

    def resetTimeStat(self):        
        ''' reset all the TimeStat parameters should be called before starting a new process maybe it is useless ask GP'''
        self.procTime=0
        self.eta=0
        self.timePerImage=0

    def onStartTimeStat(self):
        ''' Should be called whenever play is pressed '''
        pri.Time.blue(f'onStartTimeStat self.procTime={self.procTime}')
        self.initProcTime=time()

    def onPauseTimeStat(self):        
        ''' Should be called whenever pause is pressed '''
        actualTime=time()
        self.calcTimeStat(actualTime,self.numFinalized) #if paused should evaluate the correct eta when restarting
        self.procTime+=actualTime-self.initProcTime
        pri.Time.blue(f'onPauseTimeStat self.procTime={self.procTime}  self.eta={self.eta} self.numFinalized={self.numFinalized}')

    def deltaTime2String(self,dt,FlagMilliseconds=False):
       if FlagMilliseconds:
          s=str(timedelta(seconds=int(dt)))
          s+="."+f"{dt:#.3f}".split('.')[-1] #
       else:
          s=str(timedelta(seconds=round(dt)))
       return s
       
    def calcTimeStat(self,actualTime,numDone):
        '''  Should be called when when the eta should be updated '''
        procTime=self.procTime+actualTime-self.initProcTime
        numStilToProc=self.nsteps-numDone
        
        if numDone==0:
           self.eta=0
           self.timePerImage=0
        else:
          self.timePerImage=(procTime)/numDone
          self.eta=self.timePerImage*numStilToProc
        
        #pr(f'dt={procTime} ETA={self.eta} {self.deltaTime2String(self.eta)} dt+ETA={round(procTime+ self.eta)} timePerImage={self.timePerImage} numStilToProc={numStilToProc} numDone={numDone} ')
        return self.deltaTime2String(self.eta)

    def setPIV(self,flagSpiv=False):
        self.PIV=data2PIV(self,flagSpiv) 

    def createLogHeader(self):
        header=PaIRS_Header
        if self.Step==StepTypes.null: #minimum
          name='Welcome to PaIRS!\nEnjoy it!\n\n'
          header=header+name
        else:
          name=f'{self.itemname} ({self.filename_proc})\n'
          name+=self.name_proc
          date_time=QDate.currentDate().toString('yyyy/MM/dd')+' at '+\
              QTime().currentTime().toString()
          header+=f'{name}\n'+'Last modified date: '+date_time+'\n\n\n'
        return header
      
    def setCompleteLog(self):
        warn1=self.headerSection('WARNINGS',self.warnings[1],'!')  
        if self.flagRun not in (0,-10):
            warn0=''
            self.createLogProc()
            LogProc = self.headerSection('OUTPUT',self.procLog[0])
            LogStat = self.headerSection('PROGRESS status',self.procLog[1]) 
            LogErr = self.headerSection('ERROR report',self.procLog[2])
            procLog=LogProc+LogStat+LogErr 
            if self.warnings[0]: warn0='*Further information:\n'+self.warnings[0]+'\n'        
            self.Log=self.createLogHeader()+procLog+warn0+warn1
        else:
            if self.flagRun:
              self.Log=self.createLogHeader() 
            else:
              self.Log=self.createLogHeader()+warn1

    def createWarningLog(self,warning):
        warn1=self.headerSection('WARNINGS',warning,'!')  
        return self.createLogHeader()+warn1

    def headerSection(self,nameSection,Log,*args):
        if len(Log):
            c='-'
            n=36
            if len(args): c=args[0]
            if len(args)>1: n=args[1]
            ln=len(nameSection)
            ns=int((n-ln)/2)
            Log=f'{f"{c}"*n}\n{" "*ns}{nameSection}{" "*ns}\n{f"{c}"*n}\n'+Log+'\n'
        return Log
    
    def createLogProc(self):
        splitAs='\n   '#used to join the strings together tab or spaces may be use to indent the error
        numImgTot=len(self.list_pim) if self.Step!=StepTypes.min else (2*len(self.list_pim))
        LogProc=''
        LogErr=''
        cont=0
        contErr=0
        for i,p in enumerate(self.list_pim):
            if not p or self.list_print[i]=='': 
              continue
            if self.Step==StepTypes.min: #minimum
                cont+=2
                #flag=(p&FLAG_FINALIZED[0]) and (p&FLAG_FINALIZED[1]) 
                if (p&FLAG_FINALIZED[0]):
                    if (p&FLAG_FINALIZED[1]):
                      LogProc+=(self.list_print[i])
                    else:
                      sAppo=self.list_print[i].split('\n')
                      LogProc+=sAppo[0]+'\n'
                      if (not p&FLAG_READ[1]) and p&FLAG_READ_ERR[1]:
                        LogErr+=splitAs.join(sAppo[1:-1])+'\n'
                        contErr+=1
                        #pri.Process.magenta(f'LogProc {i} {p}   {splitAs.join(sAppo[1:-1])} {hex(p)}   ')  
                      else:# la b nonè stata proprio letta
                          cont-=1
                          #pri.Process.magenta(f'LogProc wrong {i} {p}   {splitAs.join(sAppo[1:-1])} {hex(p)}  ')
                    LogProc+='\n'
                else:
                    sAppo=self.list_print[i].split('\n')
                    if (p&FLAG_FINALIZED[1]):
                      LogProc+=(sAppo[-2])+'\n'
                      LogErr+=splitAs.join(sAppo[0:-2])+'\n'
                      contErr+=1
                    else:
                      iDum=len(sAppo)//2
                      LogErr+=splitAs.join(sAppo[0:iDum])+'\n'+splitAs.join(sAppo[iDum:-1])+'\n'
                      contErr+=2
            elif self.Step in (StepTypes.piv,StepTypes.disp,StepTypes.spiv): #PIV process
                cont+=1
                if p&FLAG_FINALIZED[0]:
                  LogProc+=self.list_print[i]+"\n"
                  #pr(f'LogProc {i} {p}   {self.list_print[i]} {hex(p)}   =    {hex(FLAG_FINALIZED_AB)}\n')
                else:
                  contErr+=1
                  errString=splitAs.join(self.list_print[i].split('\n')[0:-1])
                  if errString: LogErr+=errString+'\n'

        if not LogProc: LogProc=self.nullLogProc()
        
        self.FlagErr=bool(LogErr) or 'CRITICAL ERROR' in self.warnings[0]
        if self.Step in (StepTypes.piv,StepTypes.spiv):
          errStr=f' ({contErr}/{numImgTot} images)'
        else:
          errStr=''
        if 'CRITICAL ERROR' in self.warnings[0]:
           errStr2='!!! Critical errors occured! Please, see further information reported below.\n\n'
        else:
           errStr2=''
        if self.FlagErr:
          LogErr=f'There were errors in the current process{errStr}:\n\n{errStr2}'+LogErr
        else:
          LogErr=f'There were no errors in the current process!\n\n'
        if numImgTot:
          pProc=cont*100/numImgTot
        else:
           pProc=100
        pLeft=100-pProc
        if cont:
          pErr=contErr*100/cont
        else:
          pErr=0
        pCorr=100-pErr
        item='pair' if self.Step!=StepTypes.disp else 'iteration'
        sp=' '*6 if self.Step!=StepTypes.disp else ' ' 
        Log_PIVCores='' if self.Step==StepTypes.min else f'          PIV cores:   {self.numPivOmpCores}\n'
        LogStat=\
              f'Percentage of {item}s\n'+\
              f'          processed:   {pProc:.2f}%\n'+\
              f'          remaining:   {pLeft:.2f}%\n'+\
              f'     without errors:   {pCorr:.2f}%\n'+\
              f'        with errors:   {pErr:.2f}%\n\n'+\
              f'Time\n'+\
              f'     of the process:   {self.deltaTime2String(self.procTime,True)}\n'+\
              f'    {sp} per {item}:   {self.deltaTime2String(self.timePerImage,True)}\n'+\
              f'         to the end:   {self.deltaTime2String(self.eta,True)}\n\n'+\
              f'Multi processing\n'+\
              Log_PIVCores+\
              f'   processing units:   {floor(self.numUsedProcs)}\n'
              #5f'   processing units:   {floor(self.numUsedProcs/self.numPivOmpCores)}\n'
        self.procLog=[LogProc,LogStat,LogErr]
        return 

    def nullLogProc(self):
       return 'No output produced!\n\n'
    
    def resetLog(self):
      if self.procLog[0]!=self.nullLogProc():
        self.Log=self.createLogHeader()+self.procLog[0]
      else:
        self.Log=self.createLogHeader()
      return

    def writeCfgProcPiv(self,filename='',FlagWarningDialog=False):
        flagSpiv=self.Step==StepTypes.spiv
        if filename=='':
          outPathRoot=self.outPathRoot
          foldOut=os.path.dirname(outPathRoot)
          if not os.path.exists(foldOut):
            try:
              os.mkdir(foldOut)
            except Exception as inst:
              pri.Error.red(f'It was not possible to make the directory {foldOut}:\n{traceback.format_exc()}\n\n{inst}')
          filename=f"{outPathRoot}.cfg"
        try:
          writeCfgProcPiv(self,filename,flagSpiv)
        except Exception as inst:
           warningMessage=f'Error while writing PIV configuration file to location "{filename}":\n{inst}'
           if FlagWarningDialog: warningDialog(None,warningMessage)
           pri.Error.red(f'{warningMessage}\n{traceback.format_exc()}\n')

class MediaPIV():
  ''' helper class to perform the avearages '''
  def __init__(self,stepType=StepTypes.piv):
    self.outName=''
    self.name_proc=''

    self.stepType=stepType
    self.namesPIV=NamesPIV(Step=self.stepType)
        
    #self.avgVel=[self.x,self.y,self.u,self.v,self.up,self.vp,self.uvp,self.FCl,self.Info,self.sn]
    self.x=np.zeros(1)
    self.y=np.zeros(1)
    self.u=np.zeros(1)
    self.v=np.zeros(1)
    self.up=np.zeros(1)
    self.vp=np.zeros(1)
    self.uvp=np.zeros(1)
    self.sn=np.zeros(1)
    self.FCl=np.zeros(1)
    self.Info=np.zeros(1)
    if self.stepType==StepTypes.disp:
      self.z=np.zeros(1)
      self.dPar=np.zeros(1)
      self.dOrt=np.zeros(1)
    if self.stepType==StepTypes.spiv:
      self.z=np.zeros(1)
      self.w=np.zeros(1)
      self.wp=np.zeros(1)
      self.uwp=np.zeros(1)
      self.vwp=np.zeros(1)
    self.indu=3 if self.stepType==StepTypes.spiv else 2
    
    # just for checking that the variables are the same 
    # I cannot do it automatically since variables are not recognized by vscode
    for n in self.namesPIV.avgVelFields:       
       v=getattr(self,n)
    
    self.cont=0
    self.nimg=0

    self.fields=[f for f,_ in self.__dict__.items()]

  def sum(self,var):
    # should start with x, y ,u ,v
    infoSi=1
    self.cont=self.cont+1
    for v, n in zip(var[2:], self.namesPIV.instVelFields[2:]) :
      f=getattr(self,n)
      #piv.Info #verificare se sia il caso di sommare solo se =Infosi
      setattr(self,n,f+1*(v==infoSi) if n=='Info' else f+v )
      
    '''
    self.u=self.u+var[2] #piv.u
    self.v=self.v+var[3] #piv.v
    self.FCl=self.FCl+var[4] #piv.FCl
    self.Info=self.Info+1*(var[5]==infoSi)  #piv.Info #verificare se sia il caso di sommare solo se =Infosi
    self.sn=self.sn+var[6] #piv.sn
    '''
    self.up=self.up+var[self.indu]*var[self.indu] #piv.up
    self.vp=self.vp+var[self.indu+1]*var[self.indu+1] #piv.vp
    self.uvp=self.uvp+var[self.indu]*var[self.indu+1] #piv.uvp
    if self.stepType==StepTypes.spiv:
      self.wp=self.wp+var[self.indu+2]*var[self.indu+2] #piv.wp
      self.uwp=self.uwp+var[self.indu]*var[self.indu+2] #piv.uwp
      self.vwp=self.vwp+var[self.indu+1]*var[self.indu+2] #piv.vwp
    
    
    if self.x.size<=1:
      self.x=var[0]  #piv.x dovrebbero essere tutti uguali
      self.y=var[1]  #piv.y dovrebbero essere tutti uguali
      if self.stepType==StepTypes.spiv:
        self.z=var[2]  #piv.y dovrebbero essere tutti uguali

  def sumMedia(self,medToSum):
    self.cont=self.cont+medToSum.cont
    self.u=self.u+medToSum.u
    self.v=self.v+medToSum.v
    self.sn=self.sn+medToSum.sn
    self.FCl=self.FCl+medToSum.FCl
    self.up=self.up+medToSum.up
    self.vp=self.vp+medToSum.vp
    self.uvp=self.uvp+medToSum.uvp
    self.Info=self.Info+medToSum.Info
    if self.stepType==StepTypes.spiv:
      self.w=self.w+medToSum.w
      self.wp=self.wp+medToSum.wp
      self.uwp=self.uwp+medToSum.uwp
      self.vwp=self.vwp+medToSum.vwp
    if self.x.size<=1:
      self.x=medToSum.x  #piv.x dovrebbero essere tutti uguali
      self.y=medToSum.y  #piv.y dovrebbero essere tutti uguali
      if self.stepType==StepTypes.spiv:
        self.z=medToSum.z  #piv.y dovrebbero essere tutti uguali

  def calcMedia(self):
    if self.cont>0:

      self.u/=self.cont
      self.v/=self.cont
      
      self.sn/=self.cont
      self.FCl/=self.cont
      self.Info/=self.cont#percentuale di vettori buoni 1=100% 0 nememno un vettore buono
      self.up=(self.up/self.cont-self.u*self.u)#nan or inf is no good vector
      self.vp=(self.vp/self.cont-self.v*self.v)#nan or inf is no good vector
      self.uvp=(self.uvp/self.cont-self.u*self.v)#nan or inf is no good vector
      if self.stepType==StepTypes.spiv:
        self.w/=self.cont
        self.wp=(self.wp/self.cont-self.w*self.w)#nan or inf is no good vector
        self.uwp=(self.uwp/self.cont-self.u*self.w)#nan or inf is no good vector
        self.vwp=(self.vwp/self.cont-self.w*self.v)#nan or inf is no good vector
  def restoreSum(self):
        
    #OPTIMIZE TA GP gestione delle statistiche ora si usano tutti i vettori anche quelli corretti forse si dovrebbe dare la possibiltà all'utente di scegliere?
    self.up=(self.up+self.u*self.u)*self.cont # inf is no good vector
    self.vp=(self.vp+self.v*self.v)*self.cont # inf is no good vector
    self.uvp=(self.uvp+self.u*self.v)*self.cont # inf is no good vector
    if self.stepType==StepTypes.spiv:
      self.wp=(self.wp+self.w*self.w)*self.cont # inf is no good vector
      self.uwp=(self.uwp+self.u*self.w)*self.cont # inf is no good vector
      self.vwp=(self.vwp+self.w*self.v)*self.cont # inf is no good vector
      self.w=self.w*self.cont

    self.u=self.u*self.cont
    self.v=self.v*self.cont
    self.sn=self.sn*self.cont
    self.Info=self.Info*self.cont#percentuale di vettori buoni 1=100% 0 nememno un vettore buono

class CompMin():
  ''' helper class to compute minimum '''
  def __init__(self,ncam=1,nframe=2):
    self.outName=''
    self.name_proc=''
    
    self.setup(ncam,nframe)
    #self.cont=0
    #self.cont0=0
    
    self.flag_TR=None
    self.LaserType=-1  #0 single, 1 double

    self.fields=[f for f,_  in self.__dict__.items()]
  
  def setup(self,ncam,nframe):
    self.ncam=ncam
    self.nframe=nframe
    self.Imin=[np.zeros(0) for _ in range(self.ncam*self.nframe)]
    self.med=[np.zeros(1) for _ in range(self.ncam*self.nframe)]
    self.contab=[0 for _ in range(ncam*2)]
  
  def minSum(self,I,k):
    ''' min '''   
    #sleep(0.15) 
    # min or max
    if len(I):# why 
      if self.contab[k]==0:
        self.Imin[k]=I
      else:
        self.Imin[k]=np.minimum(I,self.Imin[k])
      # verage std and the like
      self.med[k]=self.med[k]+I#+= non funziona all'inizio
      self.contab[k]+=1
    #prLock(f"minSum   contab={self.contab[k]}")
  def checkImg(self,I,sogliaMedia,sogliaStd)->bool:
    ''' checkImg '''   
    #dum=1/I.size
    media=I.mean()   #I.ravel().sum()*dum     #faster than mean, but affected by overflow
    dev=I.std()      #np.square(I-media).ravel().sum()*dum
    return media>sogliaMedia and dev >sogliaStd*sogliaStd 
    
  def calcMin(self,minMed):
    ''' calcMin and sum media  '''
    #pri.Time.magenta(0,f"self.cont0={self.cont0}")
    #self.cont+=self.cont0
    #nImg=1 if self.flag_TR else 2
    #nImg=2
    for k in range(len(self.Imin)):
      if minMed.contab[k]>0:
        if self.contab[k]==0:
          self.Imin[k]=minMed.Imin[k]
        else:
          self.Imin[k]=np.minimum(minMed.Imin[k],self.Imin[k])
        self.med[k]=self.med[k]+minMed.med[k]
        self.contab[k]+=minMed.contab[k]# uno viene comunque sommato in min
    
  def calcMed(self):
    ''' calcMed and sum media  '''
    pri.Time.magenta(f"calcMed   contab={self.contab}  ")
    #nImg=1 if self.flag_TR else 2
    if self.LaserType==0: # single laser
      for cam in range(self.ncam):
        k=self.nframe*cam
        for j in range(1,self.nframe):
          self.Imin[k]=np.minimum(self.Imin[k],self.Imin[k+j])
          self.med[k]+=self.med[k+j]
          self.contab[k]+=self.contab[k+j]
        self.med[k]/=self.contab[k]
        for j in range(1,self.nframe):
          self.Imin[k+j]=self.Imin[k].copy()   
          self.med[k+j]=self.med[k].copy()   
          self.contab[k+j]=self.contab[k]   #useless? I don't think so, important for restoreMin
    else: 
      for k in range(len(self.Imin)):
        if self.contab[k]>0:
          self.med[k]/=self.contab[k]
    pri.Time.magenta(f"calcMed   fine contab={self.contab}  ")
        
    

  def restoreMin(self):
    #pr(f"restoreMin   contab={self.contab}    self.cont={self.cont} self.cont0={self.cont0}")
    #nImg=1 if self.flag_TR else 2
    for k in range(len(self.Imin)):
      self.med[k]*=self.contab[k]

def foList(li,formato):
  ''' format a list call with 
    where:
    li is a list 
    format is the format that would have been used fo a single element of the list
    e.g. print(f'{a:<4d}') -> print(f'{foList([a a],"<4d")}') 
  '''
  return f"{''.join(f' {x:{formato}}' for x in li)}"
# todo delete old function
def writeCfgProcPivOld(data,nomeFile,flagSpiv=False):
    PIV=data2PIV(data,flagSpiv)
    PIV.SetVect([v.astype(np.intc) for v in data.PRO.Vect])
    inp=PIV.Inp
    vect=data.PRO.Vect
    
    with open(nomeFile,'w', encoding="utf8") as f:
        f.write('%TA000N3 Do not modify the previous string - It indicates the file version\n')
        f.write('% PIV process configuration file - A % symbol on the first column indicates a comment\n')
        f.write('% Windows dimensions ***************************************\n')
        #    % Windows dimensions ***************************************
        f.write(f'[{foList(vect[0],"<3d")}], 			Height of the windows (rows) - insert the sequence of numbers separated by a blank character (1)\n')
        f.write(f'[{foList(vect[2],"<3d")}], 			Width of the windows (columns) (2)\n')
        f.write(f'[{foList(vect[1],"<3d")}], 			Grid distance along the height direction (y) (3)\n')
        f.write(f'[{foList(vect[3],"<3d")}], 			Grid distance along the width direction (x) (4)\n')
        f.write(f'{inp.FlagBordo}, 			Flag boundary: if =1 the first vector is placed at a distance to the boundary equal to the grid distance (5)\n')
        #     % Process parameters - Interpolation ***********************************
        f.write(f'% Process parameters - Interpolation ***********************************\n')
        f.write(f'{inp.IntIniz}, 			Type of interpolation in the initial part of the process (6)\n')
        f.write(f'{inp.IntFin}, 			Type of interpolation in the final part of the process (7)\n')
        f.write(f'{inp.FlagInt}, 			Flag Interpolation: if >0 the final interpolation is used in the final #par iterations (8)\n')
        f.write(f'{inp.IntCorr}, 			Type of interpolation of the correlation map (0=gauss classic; 1=gauss reviewed; 2=Simplex) (9)\n')
        f.write(f'{inp.IntVel}, 			Type of interpolation of the velocity field (1=bilinear; 2= Simplex,...) (10)\n')
        #     % Process parameters **************************************\n')
        f.write(f'% Process parameters **************************************\n')
        f.write(f'{inp.FlagDirectCorr}, 			Flag direct correlation on the final iterations (0=no 1=yes ) (11)\n')
        f.write(f'{inp.NIterazioni}, 			Number of final iterations (12)\n')
        f.write(f'% Activation flags   **************************************\n')
        #     % Activation flags - Validation **************************************
        f.write(f'1, 			Flag Validation (0=default parameters (see manual); otherwise the validation parameters in the final part of the cfg file are activated) (13)\n')
        f.write(f'1, 			Flag Windowing (0=default parameters (see manual); otherwise the windowing parameters in the final part of the cfg file are activated) (14)\n')
        f.write(f'1, 			Flag Filter    (0=default parameters (see manual); otherwise the additional filter parameters in the final part of the cfg file are activated) (29)\n')
        f.write(f'%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n')
        f.write(f'%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n')
        #     % Process parameters - Validation **************************************
        
        f.write(f'% Process parameters - Validation **************************************\n')
        f.write(f'{inp.FlagValid}, 			Flag median test: 0=no; 1=classic; 2=universal (Scarano, 			Westerweel 2005) (15)\n')
        f.write(f'{inp.SemiDimValid}, 			Half-dimension of the kernel (it uses 2*(#par)+1 vectors for each direction) (16)\n')
        f.write(f'{inp.SogliaMed:.2f},			Threshold for the median test - Advised value 2 (1.0 - 3.0) (17)\n')
        f.write(f'{inp.ErroreMed:.2f},			Allowed Error in pixel for the median test - Advised value 0.1 (0.0 -> no limits) (18)\n')
        f.write(f'{inp.FlagAttivaValSN}, 			Flag test sn/CC: 0=no; 1=sn; 2=CC; 3=both  +4 for limiting the maximum displacement (19)\n')
        f.write(f'{inp.SogliaSN:.2f},			Threshold for the signal/noise test (Advised value 1.5) - it doesn\'t work on the direct correlation (20)\n')
        f.write(f'{inp.SogliaFcl:.2f},			Threshold correlation coefficient (Advised value 0.25) (21)\n')
        f.write(f'{inp.FlagSecMax}, 			Flag correction with the second maximum; 0=not active; otherwise it is active (22)\n')
        f.write(f'{inp.FlagCorrezioneVel}, 			Flag correction vectors: 0=average on correct vectors; 1=weighted average with the distance; 2=iterative average (23)\n')
        f.write(f'{inp.SogliaNoise:.2f},			Minimum allowed average value in the interrogation window (24)\n')
        f.write(f'{inp.SogliaStd:.2f},			Minimum allowed std deviation value in the interrogation window(25)\n')
        f.write(f'{inp.FlagValidNog}, 			Flag Nogueira Test (discontinued) : 0 --> no; !=0 -->yes  (if activated disables the other validation criteria )\n')
        f.write(f'0.2, 			First parameter Nogueira Test(0.20-0.35)  \n')
        f.write(f'0.1, 			Second parameter Nogueira Test(0.01-0.1)  \n')
        f.write(f'{0}, 			Hart Correction uses 4 interrogation windows  W=W-W/Par e H=H-/Par 0 disables\n')
        f.write(f'{0}, 			Value of info for a good vector   \n')
        f.write(f'{1}, 			Value of info for an outlier\n')
        #   % Windowing parameters (Astarita, 			Exp Flu, 			2007) *************************
        f.write(f'% Windowing parameters (Astarita EiF 2007) *************************\n')
        f.write(f'{inp.FlagCalcVel}, 			Weighting window for absolute velocity (0=TopHat, 1=Nogueira,	2=Blackman,...) (26)\n')
        f.write(f'{inp.FlagWindowing}, 			Weighting window for the correlation map (0=TopHat 1= Nogueira 2=Blackman 3=top hat at 50%) (27)\n')  
        f.write(f'{inp.SemiDimCalcVel}, 			Half-width of the filtering window (0=window dimension) (28)\n')
        #   % Adaptive PIV parameters (Astarita, 			Exp Flu, 			2009) *************************
        f.write(f'% Adaptive PIV parameters (Astarita EiF 2009) *************************\n')
        f.write(f'{inp.MaxC:.3f},  		Maximum value of zita (30)\n')  
        f.write(f'{inp.MinC:.3f},  		Minimum value of zita (30) \n')
        f.write(f'{inp.LarMin}, 			Minimum Half-width of the weighting window (31)\n')
        f.write(f'{inp.LarMax}, 			Maximum Half-width of the weighting window (31)\n')
        #   % Further processing parameters *************************
        f.write(f'% Further processing parameters *************************\n')
        f.write(f'{inp.FlagSommaProd}, 			Flag product or sum of correlation 0 prod 1 sum (only used if par 27 or 11 are !=0) (32)\n')
        f.write(f'{inp.ItAtt if not -1000 else 0 }, 			Flag for restarting from a previous process (0 no otherwise the previous iteration) (33)\n')
        #   % Filter parameters *************************
        FlagFilt=0
        CutOff=18
        VelCut=-1
        f.write(f'% Additional  filter parameters 2009) *************************\n')
        f.write(f'{FlagFilt:}, 			Flag for alternate direction filtering 0 disable 1 dense predictor 2 displacement (34)\n')  
        f.write(f'{CutOff:.2f},  		Vertical Cutoff wavelength (35) \n')
        f.write(f'{VelCut:.2f},  		Vertical filter rate (36)\n')
        f.write(f'{CutOff:.2f},  		Horizontal Cutoff wavelength (35) \n')
        f.write(f'{VelCut}, 			Horizontal filter rate (36)\n')
        f.write(f'{inp.FlagRemNoise}, 			Flag to activate noise removal on the images (37)\n')
        PercCap=-.001
        PercFc=-3
        f.write(f'{PercFc}, 			Parameter for noise removal  (38)\n')
        f.write(f'{PercCap}, 		Number of std to cap the particles (negative disables) (39)\n')

    
    ''' 
    try:
      p=PaIRS_lib.PIV()
      p.readCfgProc(nomeFile)
    except Exception as inst:
      pri.Error.white(inst.__cause__)

    import inspect
    notUsedKey=['FlagLog','HCellaVec','HOverlapVec','ImgH','ImgW','RisX','RisY','WCellaVec','WOverlapVec','dt','this'    ]
    diPro= dict(inspect.getmembers(PIV.Inp))
    flagEqual=1
    for k,v in inspect.getmembers(p.Inp):
      if not k[0].startswith('_'):
        if not k in notUsedKey:
          if v!=diPro[k]:
            flagEqual=0
            print(f'{k}={v}->{diPro[k]}')
    if flagEqual:
      pr('The cfg is identical to the master')
    #verifica uguaglianza PROpar, mancano i vettori
    flagEqual=1
    try:
      pro=PIV2Pro(p)
      pDum=data2PIV(data)
      pDum.SetVect([v.astype(np.intc) for v in data.PRO.Vect])
      pro=PIV2Pro(pDum)
      
      notUsedKey=['change_top','copyfrom','copyfromdiz','duplicate','indexes','isDifferentFrom','isEqualTo','printDifferences','printPar','setup','tip','uncopied_fields','indTree','indItem']
      listOfList=['Vect'    ]
      diPro= dict(inspect.getmembers(data.PRO))
      #pro.printDifferences(data.PRO,[],[],True) #questo è automatico
      for k,v in inspect.getmembers(pro):
        if not k[0].startswith('_') and not k in notUsedKey:

          if  k in listOfList:
            
              for i,(a,b) in enumerate(zip (v,diPro[k])):
                if (a!=b).any():
                  flagEqual=0
                  print(f'{k}[{i}]={a}->{b}')
          else:
              if v!=diPro[k]:
                flagEqual=0
                print(f'{k}={v}->{diPro[k]}')
      if flagEqual:
        pr('The PROpar is identical to the master')
    except Exception as inst:
        pri.Error.red(f'{inst}')
                    
    
    #'''         
def writeCfgProcPiv(data,nomeFile,flagSpiv=False):
    PIV=data2PIV(data,flagSpiv)
    inp=PIV.Inp
    vect=PIV.GetVect()
    vectWindowing=PIV.GetWindowingVect()
    
    with open(nomeFile,'w', encoding="utf8") as f:
        f.write('%TA000N5 Do not modify the previous string - It indicates the file version\n')
        f.write('% PIV process configuration file - A % symbol on the first column indicates a comment\n')
        f.write('% Windows dimensions position and iterations *******************************\n')
        #    % Windows dimensions position and iterations *******************************
        f.write(f'[{foList(vect[0],"<3d")}],      Height of the windows - sequence separated by a space            (1)\n')
        f.write(f'[{foList(vect[2],"<3d")}],      Width of the IW if equal to -1 then square IW are used           (1)\n')
        f.write(f'[{foList(vect[1],"<3d")}],      Grid distance along the height direction (y)                     (2)\n')
        f.write(f'[{foList(vect[3],"<3d")}],      Grid distance along x if equal to -1 then a square grid is used  (2)\n')
        f.write(f'{inp.FlagBordo},                   Pos flag: 0 normal 1 1st vector is placed par#2 from the border  (3)\n')
        f.write(f'{inp.NIterazioni},                   Number of final iterations                                       (4)\n')
        
        #     % Process parameters - Interpolation ***********************************
        f.write(f'% Process parameters - Interpolation ***********************************\n')
        f.write(f'[{foList([inp.IntIniz,inp.FlagInt,inp.IntFin],"<3d")}],      Image Interpolation: [intial; #iter; final]                      (5)\n')
        f.write(f'{inp.IntCorr},                   Correlation peak IS (3=gauss; 4=gauss reviewed; 5=Simplex)       (6)\n')
        f.write(f'{inp.IntVel},                  Dense predictor IS (1=bilinear; 2=Simplex...)                    (7)\n')
        #     % Process parameters - Validation ******************************************\n')
        f.write(f'% Process parameters - Validation ******************************************\n')
        f.write(f'[{foList([inp.FlagValid,inp.SemiDimValid,inp.SogliaMed,inp.ErroreMed],".6g")}],       Median test: [0=no; 1=med; 2=univ; kernel dim=1; thr=2; eps=0.1]  (8)\n')
        f.write(f'[{foList([inp.FlagAttivaValSN,inp.SogliaSN,inp.SogliaFcl],".6g")}],       sn/CC test: [0=no; 1=sn; 2=CC; 3=both;sn thr=1.5; cc thr=0.3]     (9)\n')
        f.write(f'[{foList([inp.FlagValidNog,inp.SogliaMedia,inp.SogliaNumVet],".6g")}],      Nog test:[0 no; 1 active; par1; par2]                             (10)\n')
        f.write(f'[{foList([inp.SogliaNoise,inp.SogliaStd],".6g")}],             Minimum threshold: [mean=2; std=3]                                (11)\n')
        f.write(f'{inp.FlagCorrHart},                  Hart correction 4 IW of  W=W-W/Par are used o correct outliers    (12)\n')
        f.write(f'{inp.FlagSecMax},                  Flag second maximum correction; 0 no 1 active                     (13)\n')
        f.write(f'{inp.FlagCorrezioneVel},                  Flag vectors correction: 0=average on correct vectors; 1=weighted average with the distance; 2=iterative average  (14)\n')
        f.write(f'[{foList([inp.InfoSi,inp.InfoNo],".6g")}],             Output values (info): [value for good=1; value for corrected=0]   (15)\n')
        # % Windowing parameters (Astarita, Exp Flu, 2007) ***************************
        
        f.write(f'% Windowing parameters (Astarita, Exp Flu, 2007) ***************************\n')
        f.write(f'[{foList(vectWindowing[1],"<3d")}],             WW for predictor  (0=TopHat; 2=Blackman;...)                     (16)\n')
        f.write(f'[{foList(vectWindowing[2],"<3d")}],             WW for the correlation map (0=TopHat;2=Blackman 3=top hat at 50%)(17)\n')
        f.write(f'[{foList(vectWindowing[3],"<3d")}],             Half-width of the filtering window (0=window dimension)           (18)\n')
        f.write(f'[{foList(vectWindowing[4],"<3d")}],     Flag direct correlation (0=no 1=yes )                             (19)\n')
        f.write(f'[{foList(vectWindowing[0],"<3d")}],         Max displacement if <0  fraction of wa i.e. -4-> Wa/4             (20)\n')
        f.write(f'{inp.FlagSommaProd},                  Double CC operation (0 Product 1 sum)                             (21)\n')
        f.write(f'[{foList([inp.flagAdaptive,inp.MaxC,inp.MinC,inp.LarMin,inp.LarMax],".6g")}], Adaptive process [0=no;#of it; par1; par2; par3; par4]            (22)\n')
        f.write(f'{inp.ItAtt if not -1000 else 0 },                  Flag for restarting from a previous process (0 no; prev iter)     (23)\n')
        # % Filter parameters  *******************************************************
        f.write(f'% Filter parameters  *******************************************************\n')
        f.write(f'[{foList([inp.FlagFilt,inp.CutOffH,inp.VelCutH,inp.CutOffW,inp.VelCutW ],".6g")}],   Additional AD filter [0 no; 1 Pred; 2 disp; cutoff H;Rate H;W;W]  (24)\n')
        f.write(f'[{foList([inp.FlagRemNoise,inp.PercFc,],".6g")}],          Noise reduction removal of particles [0 no; it=2; perc=0.01]      (25)\n')
        
        f.write(f'[{0 if inp.PercCap<0 else 1:d} {abs(inp.PercCap):.6g}],           Noise reduction capping [0 no; val=1.05]    (26)\n')
        f.write('\n')
        
        
    
    '''
        # Mettere alla fine di updateGuiFromTree
        tree,_=self.w_Tree.pickTree(self.w_Tree.TREpar.indTree)
        d=tree.currentItem().data(0,Qt.UserRole)
        data:dataTreePar=self.w_Tree.TABpar_prev[d.indTree][d.indItem][d.ind]
        data.writeCfgProcPiv()
        #''' 
    ''' 
    try:
      p=PaIRS_lib.PIV()
      p.readCfgProc(nomeFile)
    except Exception as inst:
      pri.Error.white(inst)

    import inspect
    notUsedKey=['FlagLog','HCellaVec','HOverlapVec','ImgH','ImgW','RisX','RisY','WCellaVec','WOverlapVec','dt','this' ,'FlagCalcVelVec',  'FlagDirectCorrVec','FlagWindowingVec','MaxDispInCCVec','SemiDimCalcVelVec' ]
    diPro= dict(inspect.getmembers(PIV.Inp))
    app=1e-6# to avoid false detections in case of float
    flagEqual=1
    for k,v in inspect.getmembers(p.Inp):
      if not k[0].startswith('_'):
        if not k in notUsedKey:
          if v!=diPro[k]:
            flagEqual=0
            print(f'{k}={v}->{diPro[k]}')
    if flagEqual:
      pr('The cfg is identical to the master')
    #verifica uguaglianza PROpar, mancano i vettori
    flagEqual=1
    
    try:
      #pro=PIV2Pro(p)
      pDum=data2PIV(data)
      pDum.SetVect([v.astype(np.intc) for v in data.PRO.Vect])
      pro=PIV2Pro(pDum)
      
      notUsedKey=['change_top','copyfrom','copyfromdiz','duplicate','indexes','isDifferentFrom','isEqualTo','printDifferences','printPar','setup','tip','uncopied_fields','indTree','indItem']
      listOfList=['Vect' ]##  to add ,'windowingVect'   
      diPro= dict(inspect.getmembers(data.PRO))
      #pro.printDifferences(data.PRO,[],[],True) #questo è automatico
      for k,v in inspect.getmembers(pro):
        if not k[0].startswith('_') and not k in notUsedKey:

          if  k in listOfList:
            
              for i,(a,b) in enumerate(zip (v,diPro[k])):
                if (a!=b).any():
                  flagEqual=0
                  print(f'{k}[{i}]={a}->{b}')
          else:
              if v!=diPro[k]:
                if isinstance(v, float) and v !=0 : 
                  if abs((v-diPro[k])/v) >app:
                    flagEqual=0
                    print(f'{k}={v}->{diPro[k]}')
      if flagEqual:
        pr('The PROpar is identical to the master')
    except Exception as inst:
        pri.Error.red(f'{inst}')
                    
    
    #'''           
# TODO rivedere quando Gerardo aggiunge i vettori
def PIV2Pro(piv:PaIRS_lib.PIV)-> PROpar:  
  pro=PROpar()
  
  #PIV.SetVect([v.astype(np.intc) for v in data.PRO.Vect])
  pro.Vect=[v.astype(np.intc) for v in piv.GetVect()]
  #pro.windowingVect=[v.astype(np.intc) for v in piv.GetVect()]
  
  pro.SogliaNoise=piv.Inp.SogliaNoise
  pro.SogliaStd=piv.Inp.SogliaStd
  pro.SogliaMed=piv.Inp.SogliaMed
  pro.ErroreMed=piv.Inp.ErroreMed
  # Parameters not used in PaIrs but read by readcfg.
  # int FlagFilt;			
  # Tom_Real CutOffH;		// Lunghezza d'onda massima per il filtro					
  # Tom_Real CutOffW;		// Lunghezza d'onda massima per il filtro					
  # Tom_Real VelCutH;		// Rateo di filtraggio											
  # Tom_Real VelCutW;		//																		
  # Tom_Real PercCap;		// PPercentuale massimo livello di grigio non trattato
  # Tom_Real PercFc;		//	Percentuale per considerare cattivo un punto	
  # int FlagCorrHart;		// Flag Per Correzione Hart					
  # These parameters are not exposed in Inp if needed modify PIV_input.i
  #Valid Nog 
  pro.SogliaMedia=0.25#piv.Inp.SogliaMedia
  pro.SogliaNumVet=0.10#piv.Inp.SogliaNumVet
  pro.FlagCorrHart=0#piv.Inp.SogliaNumVet
  
  if piv.Inp.FlagValidNog==1:
    pro.FlagNogTest=1
    pro.FlagMedTest=0
    pro.FlagCPTest=0
    pro.FlagSNTest =0
  else:
    if piv.Inp.FlagValid>0 :
      pro.FlagMedTest=1
      pro.TypeMed=piv.Inp.FlagValid-1
      pro.KernMed=piv.Inp.SemiDimValid
      pro.FlagSecMax=piv.Inp.FlagSecMax 
    pro.FlagSNTest =1 if piv.Inp.FlagAttivaValSN&1  else 0
    pro.FlagCPTest =1 if piv.Inp.FlagAttivaValSN&2  else 0

  pro.SogliaSN=piv.Inp.SogliaSN
  pro.SogliaCP=piv.Inp.SogliaFcl

  pro.IntIniz=piv.Inp.IntIniz
  pro.IntFin=piv.Inp.IntFin
  pro.FlagInt=piv.Inp.FlagInt
  pro.IntVel=piv.Inp.IntVel 
  pro.FlagCorrezioneVel=piv.Inp.FlagCorrezioneVel
  #pro.FlagCorrHart=PIV.Inp.FlagCorrHart
  pro.IntCorr=piv.Inp.IntCorr 
  pro.FlagWindowing=piv.Inp.FlagWindowing

  pro.MaxC=piv.Inp.MaxC
  pro.MinC=piv.Inp.MinC
  pro.LarMin=piv.Inp.LarMin
  pro.LarMax=piv.Inp.LarMax

  pro.FlagCalcVel=piv.Inp.FlagCalcVel
  pro.FlagSommaProd=piv.Inp.FlagSommaProd
  pro.FlagDirectCorr=piv.Inp.FlagDirectCorr
  pro.FlagBordo=piv.Inp.FlagBordo

  if piv.Inp.SemiDimCalcVel<0:
     pro.NItAdaptative=-piv.Inp.SemiDimCalcVel
     pro.NIterazioni=piv.Inp.NIterazioni-pro.NItAdaptative
     pro.FlagAdaptative=1
  else:   
      pro.SemiDimCalcVel=piv.Inp.SemiDimCalcVel
      pro.NIterazioni=piv.Inp.NIterazioni
      pro.FlagAdaptative=0

  return pro
   
def data2PIV(data:dataTreePar,flagSpiv=False):
    OUT=OUTpar()
    OUT.copyfromdiz(data.OUT_dict)
    PRO=PROpar()
    PRO.copyfromdiz(data.PRO_dict)

    if flagSpiv:
      PIV=PaIRS_lib.Stereo()
    else:
      PIV=PaIRS_lib.PIV()
    
    PIV.DefaultValues()
    PIV.Inp.FlagNumThreads=data.numPivOmpCores
    #OUT=data.OUT
    #PRO=data.PRO

    # % Windows dimensions position and iterations *******************************
    PIV.SetVect([np.array(v).astype(np.intc) for v in PRO.Vect])
    PIV.Inp.FlagBordo=PRO.FlagBordo
    PIV.Inp.NIterazioni=PRO.NIterazioni+PRO.NItAdaptative if PRO.FlagAdaptative else PRO.NIterazioni
    # % Process parameters - Interpolation ***********************************
    PIV.Inp.IntIniz=PRO.IntIniz
    PIV.Inp.FlagInt=PRO.FlagInt
    PIV.Inp.IntFin=PRO.IntFin
    PIV.Inp.IntCorr=PRO.IntCorr+3     
    PIV.Inp.IntVel=PRO.IntVel 

    # % Process parameters - Validation ******************************************
    #  Median test : [0 = no; 1 = med; 2 = univ, kernel dim = 1, thr = 2, eps = 0.1] (8)
    PIV.Inp.FlagValid=1 if PRO.TypeMed==0 else 2
    PIV.Inp.SemiDimValid=PRO.KernMed
    PIV.Inp.SogliaMed=PRO.SogliaMed
    PIV.Inp.ErroreMed=PRO.ErroreMed
    PIV.Inp.jumpDimValid=1
    # sn/CC test: [0=no; 1=sn; 2=CC; 3=both,sn thr=1.5, cc thr=0.3]     (9)
    PIV.Inp.FlagAttivaValSN=1 if PRO.FlagSNTest else 0
    PIV.Inp.FlagAttivaValSN|=2 if PRO.FlagCPTest else 0
    PIV.Inp.SogliaSN=PRO.SogliaSN
    PIV.Inp.SogliaFcl=PRO.SogliaCP

    # Nog test : [0 no; 1 active, par1, par2] (10)
    PIV.Inp.FlagValidNog=1 if PRO.FlagNogTest else 0
    PIV.Inp.SogliaMedia=PRO.SogliaMedia
    PIV.Inp.SogliaNumVet=PRO.SogliaNumVet
    
    PIV.Inp.SogliaNoise=PRO.SogliaNoise
    PIV.Inp.SogliaStd=PRO.SogliaStd
    
    PIV.Inp.FlagCorrHart=0 # to be seen 
    PIV.Inp.FlagSecMax=1 if PRO.FlagSecMax else 0
    PIV.Inp.FlagCorrezioneVel=PRO.FlagCorrezioneVel
    # Output values(info) : [value for good = 1, value for corrected = 0] (16)
    PIV.Inp.InfoSi=1
    PIV.Inp.InfoNo=0
    
    # % Windowing parameters (Astarita, Exp Flu, 2007) ***************************
    PIV.Inp.numInitIt=max(len(v) for v in PRO.Vect)
    PIV.Inp.FlagWindowing=PRO.FlagWindowing
    """
    if (PIV.Inp.FlagWindowing >= 0) :
      FlagWindowingVec=np.array([PIV.Inp.FlagWindowing],dtype=np.intc)
    else :
      numInitIt = PIV.Inp.numInitIt +1# if negative onlhy in the final iterations
      FlagWindowingVec=np.array([0 if ii<numInitIt -1 else -PIV.Inp.FlagWindowing for ii in range(numInitIt) ],dtype=np.intc)
    """
    FlagWindowingVec=np.array(PRO.vFlagWindowing,dtype=np.intc)

    flagCalcVelVec=np.array(PRO.vFlagCalcVel,dtype=np.intc)
    semiDimCalcVelVec=np.array(PRO.vSemiDimCalcVel,dtype=np.intc)
    
    PIV.Inp.FlagDirectCorr=PRO.FlagDirectCorr
    """
    if (PIV.Inp.FlagDirectCorr == 0) :
      FlagDirectCorrVec=np.array([PIV.Inp.FlagDirectCorr],dtype=np.intc)
    else :
      numInitIt = PIV.Inp.numInitIt +(PIV.Inp.FlagDirectCorr - 1)# if equal to 2 then should be one element longer
      FlagDirectCorrVec=np.array([0 if ii<numInitIt -1 else 1 for ii in range(numInitIt) ],dtype=np.intc)
    """
    FlagDirectCorrVec=np.array(PRO.vDC,dtype=np.intc)

    maxDispInCCVec=np.array(PRO.vMaxDisp,dtype=np.intc) 
    vect1=[maxDispInCCVec,flagCalcVelVec,FlagWindowingVec,semiDimCalcVelVec,FlagDirectCorrVec]
    
    PIV.Inp.numInitIt=max(*[len(v) for v in vect1],PIV.Inp.numInitIt)
 
    PIV.SetWindowingVect(vect1)
    PIV.Inp.FlagSommaProd=PRO.FlagSommaProd

    # Adaptive process[0 = no; #of it, par1, par2, par3, par4](22)
    # questo  è l'equivalente del c
    #PIV.Inp.flagAdaptive =-PIV.Inp.SemiDimCalcVel if  PIV.Inp.SemiDimCalcVel <= -1 else  0
    #PIV.Inp.SemiDimCalcVel = abs(PIV.Inp.SemiDimCalcVel)
    #flagCalcVelVec=np.array(abs(PIV.Inp.SemiDimCalcVel),dtype=np.intc)
    PIV.Inp.flagAdaptive =PRO.NItAdaptative if PRO.FlagAdaptative else 0
    PIV.Inp.MaxC=PRO.MaxC
    PIV.Inp.MinC=PRO.MinC
    PIV.Inp.LarMin=PRO.LarMin
    PIV.Inp.LarMax=PRO.LarMax    

    PIV.Inp.ItAtt=-1000
    
    
    PIV.Inp.RisX=OUT.xres#*float(10.0)
    PIV.Inp.RisY=OUT.xres*OUT.pixAR#*float(10.0)
    PIV.Inp.dt=OUT.dt*float(10)
    PIV.Inp.ImgH=OUT.h
    PIV.Inp.ImgW=OUT.W
    ''' already done in DefaultValues

    PIV.Inp.FlagFilt = 0; # Flag filtro: 0 nessuno, 1 AD,   
    PIV.Inp.CutOffH=18; # Lunghezza d'onda massima per il filtro    
    PIV.Inp.VelCutH=-1; # Rateo di filtraggio	    
    PIV.Inp.CutOffW=18; # Lunghezza d'onda massima per il filtro
    PIV.Inp.VelCutW=-1; #   
    PIV.Inp.FlagRemNoise = 0;     # Flag per eliminare rumore 0 no,1 si   
    PIV.Inp.PercFc=0.01;		#	Percentuale per considerare cattivo un punto
    PIV.Inp.PercCap=-1.05;		# PPercentuale massimo livello di grigio non trattato
    '''
    

    return PIV

def data2StereoPIV(data:dataTreePar):
  StereoPIV=data2PIV(data,flagSpiv=True)
  
  OUT=OUTpar()
  OUT.copyfromdiz(data.OUT_dict)
  PRO=PROpar()
  PRO.copyfromdiz(data.PRO_dict)

  spiv=StereoPIV.SPIVIn
  dP=StereoPIV.dataProc
  inPiv=StereoPIV.Inp

  # STEREO CFG file
  # A €£ indicate that the feature is not enabled in the python wrapper
  spiv.nomecal=''    # 		Root of calibration constants
  #spiv.NomeCostPiano=data.dispFile[:-4]    # Root of disparity plane constants
                      
  spiv.percorsocal=''     # Path of calibration constants
  spiv.FlagParallel=0          # Type of parallel process 0 horizontal 1 vertical (faster but with less information and mor RAM occupied)
  dP.FlagInt=StereoPIV.Inp.IntFin    #			IS for image reconstruction (only used  when FlagRad==0)
  inPiv.FlagRad=1     #			1 internal (in piv) or 0 external de-warping of the images (the latter €£)
  dP.FlagCoordRad=0     #			when equal to 0 the de-warping is carried on with the larger resolution (pix/mm)
                        #     when equal to 1 (2) the x (y) axis resolution is used 
  spiv.salvarad=0			#    if true and FlagRad is equal to 0 then the dewarped images are saved (€£)


  #                               %  ********************* Input/Output
  spiv.FirstImg=0 # # of first img to be processed (€£)
  spiv.LastImg=0   # # of first last to be processed (€£)
  spiv.Digit=0     # number  of figures i.e. zeros (MAX 10)		 (€£)
  spiv.ImgRoot=''   #		Root of the input Images (€£)
  spiv.InDir=''     # Path of the images (€£)
  spiv.InExt=''   #			Extension of the images (€£)
  spiv.OutRoot =''      #	        Root of the output Files (€£)
  spiv.OutDir =''      #                 Output path (€£)
  spiv.OutExt =''      #                 Output extension (€£)
  spiv.OutFlag = 0        # type of output file : 0 binary Tecplot 1 ascii tecplot (€£)
  spiv.WrtFlag = 1        # 0 only mean values are saved 1 all the instantaneous images are written  (€£)

  spiv.RigaPart=OUT.x 		# Starting row (€£)
  spiv.ColPart=OUT.y			# Starting Col (€£)
  dP.ImgH=OUT.H   # Ending row 
  dP.ImgW=OUT.W	  # Starting Col
  #                     % *********************** Process parameters
  dP.FlagZonaCom=0   # 			Flag for common zone should be equal to 0
  #           Volume ********************************
  dP.xinfZC = OUT.x_min     #		  minimum x world coordinates
  dP.yinfZC = OUT.y_min     #		  minimum y world coordinates
  dP.xsupZC = OUT.x_max      #		  maximum x world coordinates
  dP.ysupZC = OUT.y_max       #		  maximum y world coordinates
  spiv.FlagRis=OUT.unit      #	    0 displacements in m/s 1 in pixels 
  spiv.dt=OUT.dt        #	    time separation. If the displacements in mm are needed use 1000 (and 0 for the previous parameter)
  spiv.Sfas=3         #	    in case of images in a single file the distance between images. Normally define the name (€£)
                      #			1=a,b (after number); 2=_1,_2 (after number); 3=a,b (before number)
  #                    % Output
  spiv.FlagRotImg=0         #	    Rotation of the  img 0=no rot 1=90°, 2=180° 3= 270° clockwise	 (£€)
  inPiv.FlagLog=9            #	    0=no 1=video 2=log 3=video e log 4=Log short  5=video e log short (£€)
  spiv.StatFlag =0          #	    stat on: 1 all the vectors 0 only the good ones
  spiv.nomecfgPiv =''          #	    name of the cfg file for PIV

  # ******************************
  flagReadCalConst=0# if true internal reading
  if flagReadCalConst:
    StereoPIV.readCalConst()
  else:
    c=0
    cost=[]
    for c in range(2):
      fileName=data.calList[c]
      flagCal,numCostCalib,costDum=readCalFile(fileName)
      if c==0:
        dP.FlagCal=flagCal
        dP.NumCostCalib=numCostCalib
      else:
        if (dP.FlagCal!=flagCal):
          raise('error the two calibration file are not compatible')
      cost.append(costDum)
    StereoPIV.setCalConst( flagCal, numCostCalib,cost)
    
  StereoPIV.vect.PianoLaser[0]=np.float32(data.OUT_dict['zconst'])
  StereoPIV.vect.PianoLaser[1]=np.float32(data.OUT_dict['xterm'])
  StereoPIV.vect.PianoLaser[2]=np.float32(data.OUT_dict['yterm'])
  """
  flagReadPlaneConst=0# if true internal reading
  if flagReadPlaneConst:
    if StereoPIV.readPlaneConst()==0:
      pri.Callback.green('Laser plane constants correclty read!')
    else:
      pri.Error.red('Error while reading the file containing the laser plane constants!')
      data.laserConst=[const for const in StereoPIV.vect.PianoLaser]
  else:
    StereoPIV.vect.PianoLaser[0]=data.laserConst[0]
    StereoPIV.vect.PianoLaser[1]=data.laserConst[1]
    StereoPIV.vect.PianoLaser[2]=data.laserConst[2]
  #piv *******************************************************************************
  """
  #StereoPIV.readCfgProc(spiv.nomecfgPiv)
  return  StereoPIV

def data2Disp(data:dataTreePar):
    OUT=OUTpar()
    OUT.copyfromdiz(data.OUT_dict)
    PRO_Disp=PROpar_Disp()
    PRO_Disp.copyfromdiz(data.PRO_Disp_dict)

    Disp=PaIRS_lib.StereoDisp()
    spiv=Disp.SPIVIn
    dP=Disp.dataProc
    dAC=Disp.dispAvCo
    
    spiv.nomecal='' #os.path.splitext(os.path.basename(INP.calList[0]))    # 		Root of calibration constants				
    spiv.percorsocal='' #os.path.dirname(INP.calList[0])     #Path of calibration constants
    spiv.ImgRoot=''   #		Root input	Images
    spiv.InExt=''   #			Extension of the images
    spiv.InDir=''     #Path of the images
    spiv.FirstImg=0 # # of first img to be processed
    spiv.LastImg=0   # # of first last to be processed
    spiv.Digit=0     # number  of figures i.e. zeros (MAX 10)		

    spiv.RigaPart=OUT.y 		# Starting row 
    spiv.ColPart=OUT.x			# Starting column
    dP.ImgH=OUT.h   # Ending row
    dP.ImgW=OUT.w	  # Starting row
    spiv.Sfas=1    #	Sfasamento sub-immagini (righe a partire dall'origine):			0 per singola img: 1=a,b (finali); 2=_1,_2 (finali); 3=a,b (prima del numero sequenziale			
    spiv.FlagImgTau=data.dispFrames   #	Img da processare: 0-entrambe; 1-solo la prima; 2-solo la seconda;PARAMETRO IGNORATO SE SFAS=0					

    #Output
    spiv.OutRoot = OUT.root      #	        Root of output Files
    spiv.OutDir = OUT.path+OUT.subfold      #                 Output path 
    # Process parameters **********************
    dP.FlagInt=PRO_Disp.IntIniz    #			Metodo di raddrizzamento: 0=veloce (simp.), 1=quad…….				
    dP.FlagZonaCom=0   # 			Flag per la zona comune: 0=coordinate nel piano oggetto; 1=coord. nel piano img
    spiv.Niter=PRO_Disp.Nit   #		Numero di iterazioni
    """
    if (spiv.Niter < 0) :
      spiv.WrtFlag = 1
      spiv.Niter = -spiv.Niter
    else:
      spiv.WrtFlag = 0
    """

    dAC.HCella=PRO_Disp.Vect[0]      #     Correlation window Height 
    dAC.WCella=PRO_Disp.Vect[2]      #     Correlation window Width
    dAC.HGrid=PRO_Disp.Vect[1]      #     Grid distance vertical
    dAC.WGrid=PRO_Disp.Vect[3]      #     Grid distance horizontal
    dAC.N_NormEpi=PRO_Disp.SemiWidth_Epipolar      #      Semiwidth in the direction normal to the epipolar line
    dAC.RaggioFiltro=PRO_Disp.Filter_SemiWidth      #       Semiwidth of the filter for the detection of the maximum in the displacement map
    dAC.SogliaCor = PRO_Disp.Threshold   #     Threshold for the determination of point used in the baricentric search of the maximum in the disp map
    dAC.nIterMaxValid = PRO_Disp.Nit_OutDet
    dAC.numStd = PRO_Disp.Std_Threshold

    #%% Volume ********************************
    dP.xinfZC = OUT.x_min    #		Coordinata x inferiore
    dP.yinfZC = OUT.y_min    #		Coordinata y inferiore
    dP.xsupZC = OUT.x_max    #28    #		Coordinata x superiore	
    dP.ysupZC = OUT.y_max    #15    #		Coordinata y superiore
    # ******************************
    flagReadCalConst=0# if true internal reading
    if flagReadCalConst:
      Disp.readCalConst()
    else:
      c=0
      cost=[]
      for c in range(2):
        fileName=data.calList[c]
        flagCal,numCostCalib,costDum=readCalFile(fileName)
        if c==0:
          dP.FlagCal=flagCal
          dP.NumCostCalib=numCostCalib
        else:
          if (dP.FlagCal!=flagCal):
            raise('error the two calibration file are not compatible')
        cost.append(costDum)
      Disp.setCalConst( flagCal, numCostCalib,cost)
      
    flagReadPlaneConst=0# if true internal reading
    if flagReadPlaneConst:
      if Disp.readPlaneConst()==0:
        pri.Callback.green('readPlaneConst ok')
    else:
      Disp.vect.PianoLaser[0]=0
      Disp.vect.PianoLaser[1]=0
      Disp.vect.PianoLaser[2]=0
    return Disp
    
def printPIVLog(PD):
    stampa="It    IW      #IW        #Vect/#Tot      %       CC       CC(avg)   DC%\n"#  NR% Cap%\n"
    for j in range(len(PD.It)):
        riga="%3d %3dx%-3d %4dx%-4d %7d/%-7d %5.1f  %8.7f  %8.7f  %4.1f\n" %\
            (PD.It[j], PD.WCella[j], PD.HCella[j], PD.W[j], PD.H[j], PD.NVect[j],\
            PD.W[j]*PD.H[j], 100.0*PD.NVect[j]/(PD.W[j]*PD.H[j]), PD.Fc[j],\
                PD.FcMedia[j], 100.0*PD.ContErorreDc[j]/(PD.W[j]*PD.H[j]))#,\
                    #100.0*PIV.PD.ContRemNoise[j]/(PIV.Inp.ImgW*PIV.Inp.ImgH),\
                    #100.0*PIV.PD.ContCap[j]/(PIV.Inp.ImgW*PIV.Inp.ImgH))
        stampa=stampa+riga
    return stampa


def saveMin(data:dataTreePar,Imin=list):
  pri.Time.magenta('saveMin Init ')
  frames='ab'
  #nImg=1 if self.flag_TR else 2
  #nImg=2
  for j in range(len(Imin)):
    k=j%data.nframe
    cam=j//data.nframe%data.ncam
    name_min=f"{data.outPathRoot}_cam{cam+1}_{frames[k]}_min.png"
    im = Image.fromarray(Imin[j])
    im.save(name_min)
  pri.Time.magenta('saveMin End')
  
def saveResults(data:dataTreePar,i,Var,nameVar):
    #pri.Time.magenta('saveResults Init')
    if type(i)==int:
      if i<0:
          nameFileOut=data.resF('*').replace('_*','')
      else:
          nameFileOut=data.resF(i)
    elif type(i)==str:
      nameFileOut=data.resF(i)
    #infoPrint.white(f'---> Saving field #{i}: {nameFileOut}')
    
    if '.plt' in data.outExt:
        writePlt(nameFileOut,Var,f'PaIRS - 2D PIV',nameVar,nameFileOut)
    elif  '.mat' in data.outExt:
        dict_out={}
        for j in range(len(nameVar)):
            dict_out[nameVar[j]]=Var[j]
        scipy.io.savemat(nameFileOut,dict_out)
        #import timeit
        #timeit.timeit (lambda :'writePlt(nameFileOut,Var,"b16",nameVar,nameFileOut)')
        #timeit.timeit (lambda :'scipy.io.savemat(nameFileOut,dict_out)')
    #pri.Time.magenta('saveResults End')
    return

def memoryUsagePsutil():
    ''' return the memory usage in MB '''
    process = psutil.Process(os.getpid())
    mem = process.memory_info().rss 
    #print(f"Memory={mem/ float(2 ** 20)}MByte")
    return mem

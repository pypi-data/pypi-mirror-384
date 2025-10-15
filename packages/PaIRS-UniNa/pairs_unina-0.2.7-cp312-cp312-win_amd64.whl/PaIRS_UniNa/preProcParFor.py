''' preProcParFor helper function for parfor '''

from .PaIRS_pypacks import * #OPTIMIZE TAGP rimuovere tutti gli import e mettere solo quelli necessari
from .procTools import *

prTime = PrintTA(PrintTA.cyan, PrintTA.faceStd,  PrintTAPriority.medium).prTime

def initMIN(eventFerma,iImg,procId,data:dataTreePar,*args,**kwargs):   
  ''' this  function is called once per processor before the main function 
  eventferma is passed to the function called by PIV in order to stop the processing ''' 
  #prLock(0,f"  initMIN procId={procId}")
  compMin=CompMin(data.ncam)
  
  compMin.eventExit=eventFerma
  # initially I thought that it was easier to initialize the minimum without calling procMIN but this is not possible because
  # if an error occurs (e.g. reading) while processing the first image it is not possible to overcome this error
  #if  procId==2:    prTimeLock(f"initMIN  rima compmin   procId={procId} ")
  (flagOut,VarOut)=procMIN(iImg,procId,compMin,data,*args,**kwargs)
  #if  procId==2:    prTimeLock(f"fine initMIN    procId={procId} ")
  return  (flagOut,VarOut,compMin)

def procMIN(i,procId,compMin:CompMin,data:dataTreePar,numMaxProcs,*args,**kwargs):
  ''' main proc function called for all the images one time per processor 
    k=0 or 1 for the first and second image
    In output flagOut and varOut[0] can be:
      Already processed:  varOut[0]=-1 flagOut=FLAG_PROC[k]|FLAG_READ[k]|FLAG_FINALIZED[k]
      Error reading:      varOut[0]=i  flagOut=FLAG_READ_ERR[k]
      Read and processed: varOut[0]=i  flagOut=FLAG_PROC[k]|FLAG_READ[k]|FLAG_FINALIZED[k]|FLAG_CALLBACK_INTERNAL
    Use:
    numCallBackTotOk+=sum(1 if x&FLAG_CALLBACK_INTERNAL else 0 for x in flagOut) 
        to evaluate the number of total internal callbacks
    numProcOrErrTot=sum(1 if (f&FLAG_FINALIZED_OR_ERR[0])and (f&FLAG_FINALIZED_OR_ERR[1]) else 0 for f  in flagOut)   
    numProcOrErrTot=sum(1 if f else 0 for f  in flagOut)   
        to evaluate the number of total images processed (after a possible pause)
    numFinalized=sum(1 if (f&FLAG_FINALIZED[0]) and (f&FLAG_FINALIZED[1])  else 0 for f  in flagOut)   
        to evaluate the number of total images correctly  processed 
    where FLAG_FINALIZED_OR_ERR = [ p|e for (p,e) in zip(FLAG_FINALIZED,FLAG_READ_ERR)]
  '''
  flagOut=0 

  varOut=[-1,'',[]]
  
  ncam=data.ncam
  nframe=data.nframe
  nImgMin=nframe*ncam
  nImgMolt=2 if data.FlagTR else 1
  
  try:
    for j in range(nImgMin):  
      # tbd
      k=j%nframe
      cam=j//nframe%ncam
      ind=nImgMolt*nframe*i + k + data.nimg*nframe*cam
      #if i==2:1/0
      
      #i=0 ind=0 (0)-> a ind=1 (1)->b
      #i=1 ind=4 (2)-> a ind=5 (3)->b
      varOut[1]+=data.list_Image_Files[ind]+"\n"
      if data.list_eim[ind]:
        if data.list_pim[i]&FLAG_PROC[k]:
          flagOut|=FLAG_PROC[k]|FLAG_READ[k]|FLAG_FINALIZED[k] # It has been already processed. Exit without calling the callback  core part
          if k: return (flagOut,varOut) #second img
          #flagOut=flagOut& ~FLAG_CALLBACK# nel caso sia stata chiamata in precedenza ed ora non venga chiamata
        else:  
          if compMin.eventExit.is_set(): return (flagOut,varOut)
          nameImg=data.inpPath+data.list_Image_Files[ind]
          #if k==0:          prLock(f'{i}    {data.list_Image_Files[ind]} --- {data.list_Image_Files[ind+1]}  ')
          try:
            if compMin.eventExit.is_set():             return (flagOut,varOut)
            I=np.array(Image.open(nameImg))
          except Exception as inst:
            flagOut|=FLAG_READ_ERR[k]
            #if data.list_pim[i]&FLAG_READ_ERR[k]: varOut[0]=-1# no log already written
            varOut[1]+=f"!!!!!!!!!! Error reading {data.list_Image_Files[ind]}:\n{inst}\n"# no internal callback  {str(inst.__cause__)}
            prLock(f'{varOut[1]}',end='')
            varOut[0]=i# In any case the log will be written. If FLAG_CALLBACK_INTERNAL will be set then also the internal part will be called. 
          else:# no exception
            
            flagOut|=FLAG_READ[k]
            if compMin.checkImg(I,data.SogliaNoise_Min,data.SogliaStd_Min ):
              #flagOut=1 if k==0 else (2 if flagOut==-1 else 3)
              compMin.minSum(I,j)
              #prLock(f"procMIN  {i}--{procId} {nameIm}  flagOut={flagOut}  list_pim[i]={data.list_pim[i]}  ")
              flagOut|=FLAG_PROC[k]|FLAG_FINALIZED[k]# in this case both processed and finalized
            else:
              varOut[1]+=f"The gray levels in {data.list_Image_Files[ind]} are too small! Please, check the image or change the minimum allowed value and standard deviation thresholds in the Validation box!\n" 
              flagOut|=FLAG_PROC[k] # in this case both processed and finalized
            varOut[0]=i# In any case the log will be written. If FLAG_CALLBACK_INTERNAL will be set then also the internal part will be called. 
            flagOut|=FLAG_CALLBACK_INTERNAL# Verrà chiamata la callback
      else:
        #if data.list_pim[i]&FLAG_READ_ERR[k]: varOut[0]=-1# no log already written
        varOut[0]=i# In any case the log will be written. If FLAG_CALLBACK_INTERNAL will be set then also the internal part will be called. 
        flagOut|=FLAG_READ_ERR[k]
        varOut[1]+=f"!!!!!!!!!! The file {data.list_Image_Files[ind]} is missing!\n"
  except :
    flagOut|=FLAG_GENERIC_ERROR
    varOut[0]=i# In any case the log will be written. If FLAG_CALLBACK_INTERNAL will be set then also the internal part will be called. 
    varOut[1]+=printException(flagMessage=True)


  if not procId%numMaxProcs and flagOut&FLAG_PROC_AB: # copying in the queue is time consuming. This is done only when needed
    varOut[2]=compMin.Imin#VarOut=[i,stampa,Var]
  return (flagOut,varOut)
            
def finalMIN( procId,compMin:CompMin,data:dataTreePar,numMaxProcs,*args,**kwargs):
  #prLock(f'finalMIN  procId={procId}  {data.compMin.contab}')
  return compMin

def saveAndMin(procId,flagHasWorked,compMin:CompMin,data:dataTreePar,numMaxProcs,*args,**kwargs):
  ''' saveAndMean is the wrapUp function called once per processor  '''
  #prTimeLock(f'saveAndMin  procId={procId}  {data.compMin.contab}')
  if flagHasWorked:
    data.compMin.calcMin(compMin)
  #prTimeLock(f'saveAndMin  fine procId={procId}  {data.compMin.contab}')
  return data.compMin


def callBackMin(flag,perc,procId,flagOut,name,VarOut,signal_res):
  ''' 
    flag=true new data False just check exit
    perc= precentage done
    flagOutFromTasks,varOutFromTask Out varibles from task  e.g.:
      flagOut=1 #0 to be processed, -1 error, 1 correctly processed
      varOutFromTask whatever for now a string
      name current element in names
    to stop the process the return value should be True otherwise sleep  
  '''
  global FlagStopWorkers
  if flag:
    i=VarOut[0]
    stampa=VarOut[1]
    Var=VarOut[2]
    #prLock(f'Callback {i}  {perc}       getpid {os.getpid()}      {len(Var)}')
    signal_res.emit(procId,i,flagOut,Var,stampa)
    VarOut[2]=[]#altrimenti salvo le img 
    '''
    if i==0:
      callBackMin.flagStop=True
    if(callBackMin.flagStop):
      if i>=2:
        callBackMin.flagStop=False
        FlagStopWorkers[0]=True
        return True
    #'''    
  if FlagStopWorkers[0]:
    return True
  else:
    return False     
callBackMin.flagStop=True
  



  


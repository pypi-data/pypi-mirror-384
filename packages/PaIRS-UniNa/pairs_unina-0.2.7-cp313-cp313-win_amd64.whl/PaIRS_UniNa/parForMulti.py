'''  Parallel for for PIV '''
#import os
import traceback
import queue
import asyncio
#import random
import multiprocessing as mp
from time import sleep, time
from .tAVarie import PrintTA, PrintTAPriority
from .__init__ import __version__,__year__,__mail__
#import numpy as np
#import scipy as sc

prTime=PrintTA(PrintTA.blue, PrintTA.faceStd,  PrintTAPriority.medium).prTime
pr=PrintTA(PrintTA.blue, PrintTA.faceStd,  PrintTAPriority.medium).prTime
# pylint: disable=unused-argument
lock=None
def prLock( *args,**kwargs):
  ''' print in parallel pool without overlap (slower)'''
  try:
    with lock:
      PrintTA(PrintTA.blue, PrintTA.faceStd,  PrintTAPriority.medium).pr( *args,**kwargs)
  except :
    print(ParForMul.printExceptionPFM(flagMessage=True))

def prTimeLock( *args,**kwargs):
  ''' print in parallel pool without overlap (slower)'''
  try:
    with lock:
      PrintTA(PrintTA.blue, PrintTA.faceStd,  PrintTAPriority.medium).prTime( *args,**kwargs)
  except:
    print(ParForMul.printExceptionPFM(flagMessage=True))

def printExceptionMasterParFor(stringa='',flagMessage=False):  #timemilliseconds=-1 ***
    ''' used to print when an exception is raised TA has decided that the printing function is a simple
    print in this way we cannot have any problems when printing in non-compatible terminals
    use with something like

    try:
        a=1/0
    except :#non need to put a variable al the info are in traceback
        printException()
    * stringa is an additional string (to specify the point where the error comes from) 
    * flagMessage is a flag, if true the error message is generated; default value is Flag_DEBUG
    * flagDispDialog is a flag, if true a critical dialog appears after the exception
    '''
    #print(f'***** ParForMul Exception *****  Deltat={time()-PrintTA.startTime}\n{traceback.format_exc()}',*args,**kwargs)
    #print(sys.exc_info()[2])
    Message=""
    if flagMessage:
        Message+=f'Please, mail to: {__mail__}\n\n'
        Message+=f'***** PaIRS Exception *****  time={time()-PrintTA.startTime}\n'+stringa
        Message+=f'***** traceback.print_exc() *****  \n'
        Message+=traceback.format_exc()
        Message+=f'***** traceback.extract_stack() *****  \n'
        # to print all the queue comment if not needed
        for st in traceback.format_list(   traceback.extract_stack()):
            if 'PAIRS_GUI' in st and 'printException'not in st:# limits to files that have  PAIRS_GUI in the path
                Message+=st
        Message+=f'***** PaIRS Exception -> End *****'
    return Message

  

def fakePIV(iImg,procId, p, procTime, flagOutput=False, mes="fakePIV"):
  ''' fakePIV'''
  startTime = time()
  #print(f'reading Img {iImg} pid={os.getpid()} pid={mp.current_process().pid}')
  #print(f'reading Img {iImg}  pid={mp.current_process().pid} procId={procId}')
  #sleep(0.5)
  #print(f'Finished reading Img {iImg}')
  
  a=0
  count=1*1000*1000#on my pc 10*1000*1000=1sec
  nIt=1
  while nIt<2000000: 
    for _ in range(count):
      a+=5#random.random()   
    if time()-startTime>procTime: 
      break
    nIt+=1
  if flagOutput:
    print(f'fine proc Img {iImg} Nit={nIt} t={time()-startTime}   mes={mes}')
  return (0,f'fine proc Img {iImg} Nit={nIt} t={time()-startTime}   mes={mes}')
  
  #return iImg

class ParForCom():
  ''' Comunication varibles used by ParFor'''
  def __init__(self):
    #prTime(0,'Dentro ParForCom Com')
    manager=mp.Manager()#si potrebbe creare un lock al posto della variabile globale qui cercare su internet 
    #prTime(0,'Dentro ParForCom dopo manager')
    self.q = manager.Queue()
    self.qOut= manager.Queue()
    self.qProcessed= manager.Queue()
    self.eventExit = manager.Event()
  
  def clearAll(self):
    ''' Clears all the queues'''
    self.clear(self.q)
    self.clear(self.qOut)
    self.clear(self.qProcessed)

    
    
  def clear(self,q:queue):
    '''clears a Queue'''
    try:
      while True:
        q.get_nowait()
    except queue.Empty:
        pass



class ParForMul():
  ''' class Parallel for for PIV '''
  printExceptionPFM=printExceptionMasterParFor #class variable
  def __init__(self):
    #prTime(0,'Dentro ParForMul inizio')
    self.parForCom:ParForCom=ParForCom()
    # valori impostabili dall'esterno
    self.sleepTime=1. # waiting to do things
    self.nonProcessed=0 # waiting to do things
    #self.numUsedCores =psutil.cpu_count(logical=False)
    ## numUsedCores is the number of cores used fo processing and can be different from numCoresParPool that is the number of cores used in the parPool
    self.numCoresParPool=self.numUsedCores = mp.cpu_count()//2#da decidere per intel  /2 sono i processori reali 
    #prTime(0,'Dentro ParForMul fine')
    self.numCalledCallbacks=0 # identify the times that the callbacks have been called
    self.p=None
    self.flagError=False
    self.exception=None


  def initTask(self,eventExit,name,procId,*args,**kwargs):
    ''' dummy InitTask sample 
    id is the id of the task should be a numeber between 1 and numUsedCores
    if needed initTask should call the main task with name
    '''
    
    (flag,var)=fakePIV(name, procId,('initTask',2), *args,**kwargs)
    return (flag,var,('initTask',2))

  def wrapUp(self,procId,flagHasWorked,P,*args,**kwargs):
    ''' Dummy wrapUp function '''
    if flagHasWorked:#do something
      pass
    return P

  def callBack(self,flag,perc,procId,flagOutFromTask, name,varOutFromTask):
    ''' Dummy callBack function
    perc=percentage of processed images
    flag=true new data False just check exit
    perc= precentage done
    flagOutFromTasks,varOutFromTask Out variables from task  e.g.:
      flagOutFromTasks= 0 success, 1 skipped, -1 error, -2 blocked from caller
      varOutFromTask whatever for now string
      name current element in names
    to stop the process the return value should be True otherwise sleep  '''
    if not flag:
      return False  
    return False

  def finalTask(self,procId,*args,**kwargs):
    ''' dummy final finalTask function 
    id is the id of the task should be a numeber between 1 and numUsedCores'''
    return ('finalTask',2)

  def launchTask(self,procId,task,initTask,finalTask,  *args,**kwargs):
    ''' the main parallel function first calls initTask (eventExit is an event that enables the safe exit)
        then for all the element in the queue q calls task with the variable returned by initTask 
        finally calls finalTask puts in the queue qOut the final result '''
    # aggiunto try così almeno ci rendiamo conto se c'è un errore
    '''
    try: 
      procId=mp.current_process()._identity[0]
    except:
      procId=0 # '''
    #pid=mp.current_process().pid
    flagHasWorked=False#if true the task has processed at least one element
    #if  procId==2: prTimeLock(f"launchTask ||||||||||||  Inizio    procId={procId} flagHasWorked={flagHasWorked} ")
    media=None
    try:
      i,n=self.parForCom.q.get()#  the first time task must be called by initTask
      if i!=-1:
        flagHasWorked=True
        (flag,var,P)=initTask(self.parForCom.eventExit,n,procId,*args,**kwargs)
        self.parForCom.qProcessed.put((procId,flag,i,var))
        while True:
          i,n=self.parForCom.q.get()
          if i==-1:
            break
          (flag,var)=task(n,procId,P,*args,**kwargs)
          self.parForCom.qProcessed.put((procId,flag,i,var))
        media=finalTask(procId,P,*args,**kwargs)# media should be different from None
    except Exception as e:
      raise(e) # I do not really care to have a full report if in debug it may be important
      #ParForMul.printExceptionPFM()
    flagHasWorked=False if media is None else flagHasWorked #if true the task has processed at least one element and media should be different from None
    return (procId,flagHasWorked,media)

  def readQOutProcess(self,strOutput,flagProcessed,callBack,names,nElements):
    ''' reads the qOut queue save the data and calls callback'''
    com=self.parForCom 
    while not com.qProcessed.empty():
      (procId,flag,i,var)=com.qProcessed.get_nowait()
      perc=1-(com.q.qsize()-self.numUsedCores)/nElements#
      strOutput[i]=var
      flagProcessed[i]=flag
      
      #prLock(f'callBack {i}  {perc} {com.q.qsize()}')
      if callBack(True,perc,procId,flag,names[i],var):
        com.eventExit.set()# in this case the process will stop
      self.numCalledCallbacks+=1

  def errorHandler(self,error):
    ''' error function '''
    #self.errorMessage=ParForMul.printExceptionPFM(flagMessage=True)
    self.exception=error
    self.flagError=True
    self.parForCom.eventExit.set()# in this case the process will stop
    #raise(error)
  def parForExtPool(self,parPool,task,names,*args,initTask=None,finalTask=None,wrapUp=None,callBack=None,**kwargs):
    ''' parallel for main function with external mp pool 
    task is the main function that is called for each value in names. 
    optionally initTask and finalTask are called only one time per worker
    args and kwargs are passed to all the functions.add()
    callBack is called frequently and can be used to stop the parFor
    Finally the WrapUp function is called one time per worker to wrap things up
     '''
    #prTime(0,'Dentro parForExtPool')
  
    com=self.parForCom 
    com.eventExit.clear()
    initTask=self.initTask if initTask is None else initTask
    finalTask=self.finalTask if finalTask is None else finalTask
    wrapUp=self.wrapUp if wrapUp is None else wrapUp
    callBack=self.callBack if callBack is None else callBack
    self.flagError=False
    self.numCalledCallbacks=0  # reset the number of called callbacks
    nElements=len(names)
    flagProcessed=[self.nonProcessed]*nElements #lista delle immagini processate inizialmente tutti -1 ma possiamo modificarla
    strOutput = [None]*nElements #lista dei messaggi in output in realtà potrebbe essere di qualunque tipo
    def callWrapUp(var): 
      self.p=wrapUp(*var,*args,**kwargs)
      self.parForCom.qOut.put((var[0:2])) #procid , flagHasWorked
      #prTime(f"callWrapUp fine procid={var[0]} ")

    # per ora -1 non processato, -2 errore ,numero positivo processato
    for i,n  in enumerate(names):
      com.q.put((i,n))
    for _  in range(self.numUsedCores):
      com.q.put((-1,-1))

    for i  in range(self.numUsedCores):
      _=parPool.apply_async(self.launchTask,(i,task, initTask,finalTask)+args,kwargs,callback=callWrapUp, error_callback=self.errorHandler)      
      #_=parPool.apply_async(self.launchTask,(task, initTask,finalTask)+args,kwargs, error_callback=self.errorHandler)      
    #prTime(0,'Dopo apply async in  parForExtPool ++++++++++++++++++++++++++++++++++')
    nThreadEnd=0
    while True:
      try:
        #(procId,flagHasWorked)=com.qOut.get_nowait()
        (_,_)=com.qOut.get_nowait()
        #p=wrapUp(procId,flagHasWorked,p,*args,**kwargs)
        nThreadEnd+=1
        #if nThreadEnd==1: prTime(f"fine nThreadEnd={nThreadEnd}  procId={procId}")
        if nThreadEnd==self.numUsedCores: 
          break
      except queue.Empty :
        #prTime('  except queue.Empty Prima  ')
        if self.flagError  : break # in this case  a critical exception has been raised we should exit
        if com.qProcessed.empty():
          if callBack(False,None,None,None,None,None): 
            com.eventExit.set()# in this case the process will be stopped
            #print("com.eventExit.set()# in this case the process will be stopped")
        else:
          self.readQOutProcess(strOutput,flagProcessed,callBack,names,nElements)
        #prTime('********************************\n******************************dopo  ')
        sleep(self.sleepTime)

    #prTime(f"fine parForExtPool")
    # some of the processes may have  finished without saving the data
    self.readQOutProcess(strOutput,flagProcessed,callBack,names,nElements)
    com.clearAll()# just to be sure ideally only needed when self.flagError is True
  
    return self.p,flagProcessed,strOutput,self.flagError  

  def simpleFor(self,parPool,task,names,*args,initTask=None,finalTask=None,wrapUp=None,callBack=None,**kwargs):
    ''' parallel for main function 
    task is the main function that is called for each value in names. 
    optionally initTask and finalTask are called only one time per worker
    args and kwargs are passed to all the functions.add()
    Finally the WrapUp function is called one time per worker to wrap things up
     '''
    com=self.parForCom 
    com.eventExit.clear()
    initTask=self.initTask if initTask is None else initTask
    finalTask=self.finalTask if finalTask is None else finalTask
    wrapUp=self.wrapUp if wrapUp is None else wrapUp
    callBack=self.callBack if callBack is None else callBack
    self.flagError=False
    self.numCalledCallbacks=0  # reset the number of called callbacks
    nElements=len(names)
    flagProcessed=[self.nonProcessed]*nElements #lista delle immagini processate inizialmente tutti -1 ma possiamo modificarla
    strOutput = [None]*nElements #lista dei messaggi in output in realtà potrebbe essere di qualunque tipo
    
    def callWrapUp(var): 
      self.p=wrapUp(*var,*args,**kwargs)
      self.parForCom.qOut.put((var[0:2]))

    # per ora -1 non processato, -2 errore ,numero positivo processato
    for i,n  in enumerate(names):
      com.q.put((i,n))
    for _  in range(1):
      com.q.put((-1,-1))
    #with mp.Pool(self.numUsedCores) as pp:
    procId=0
    var=self.launchTask(procId,task, initTask,finalTask,*args,**kwargs)
    callWrapUp(var)
    nThreadEnd=0
    while True:
      try:
        #(procId,flagHasWorked)=com.qOut.get_nowait()
        (_,_)=com.qOut.get_nowait()
        #p=wrapUp(procId,flagHasWorked,p,*args,**kwargs)
        nThreadEnd+=1
        #prTime(f"fine nThreadEnd={nThreadEnd}  procId={procId}  flagHasWorked={flagHasWorked}")
        if nThreadEnd==1: 
          break
      except queue.Empty :
        #prTime('********************************\n******************************Prima  ')
        if self.flagError  : break # in this case  a critical exception has been raised we should exit
        if com.qProcessed.empty():
          if callBack(False,None,None,None,None,None): 
            com.eventExit.set()# in this case the process will be stopped
            #print("com.eventExit.set()# in this case the process will be stopped")
        else:
          self.readQOutProcess(strOutput,flagProcessed,callBack,names,nElements)
        #prTime('********************************\n******************************dopo  ')
        sleep(self.sleepTime)
    # some of the processes may have  finished without saving the data
    self.readQOutProcess(strOutput,flagProcessed,callBack,names,nElements)
    return self.p,flagProcessed,strOutput  ,self.flagError    

      
  def parFor(self,task,names,*args,initTask=None,finalTask=None,wrapUp=None,callBack=None,**kwargs):
    ''' parallel for main function 
    task is the main function that is called for each value in names. 
    optionally initTask and finalTask are called only one time per worker
    args and kwargs are passed to all the functions.add()
    callBack is called frequently and can be used to stop the parFor
    Finally the WrapUp function is called one time per worker to wrap things up
     '''
    prTime(0,'Dentro parFor')
    pfPool=ParForPool()
    pfPool.startParPool(self.numUsedCores)
    (p,flagProcessed,strOutput)=self.parForExtPool(pfPool.parPool,task,names,*args,initTask=initTask,finalTask=finalTask,wrapUp=wrapUp,callBack=callBack,**kwargs)
    pfPool.closeParPool()
    return p,flagProcessed,strOutput
  

    
def initPoolProcesses(the_lock):
    '''Initialize each process with a global variable lock.
    '''
    global lock
    lock = the_lock  

class ParForPool():
  ''' Saves the pool '''
  def __init__(self):
    self.parPool=None
    self.numCoresParPool = mp.cpu_count()//2#da decidere per intel sono /2 son i processori reali 
  async def startParPoolAsync(self,numCoresParPool):
    ''' dummy function to call startParPool in async'''
    self.startParPool(numCoresParPool)
  def startParPool(self,numCoresParPool):
    ''' Starts the pool'''
    the_lock = mp.Lock() # neded for prLock and the like
    if self.parPool is None:
      self.parPool=mp.Pool(numCoresParPool,initializer=initPoolProcesses, initargs=(the_lock,))  
    elif self.numCoresParPool!=numCoresParPool:
      self.parPool.close()# Si potrebbe usare terminate che ammazza tutti i processi in essere
      self.parPool=mp.Pool(numCoresParPool)  
    self.numCoresParPool=numCoresParPool
  def closeParPool(self):
    ''' Closes the pool'''
    if self.parPool is not None:
      self.parPool.close()# Si potrebbe usare terminate che ammazza tutti i processi in essere  

async def initParForAsync(numCoresParPool):
  ''' initialise the parPool'''
  #prTime(0,'PIV_ParFor_Worker init')
  pfPool=ParForPool()
  t1=asyncio.create_task(pfPool.startParPoolAsync(numCoresParPool))
  parForMul=ParForMul()
  parForMul.numUsedCores=parForMul.numCoresParPool=numCoresParPool
  await t1
  #prTime(0,'PIV_ParFor_Worker Dopo ParForPool')
  return (pfPool,parForMul)    


def main():
  ''' main '''
  prTime(6,'start')
  
  pp=ParForMul()
  #prTime(0,'Dopo ParForMul   ****************')
  
  pp.sleepTime=.1 # time between calls of callBack not used in this example
  procTime=.02
  nImg=  [x for x in range(20)]
  #startTime = time()
  args=(procTime,)
  kwargs={"flagOutput":False, "mes":"fakePIV"}
  #pp.initParPool()
  #pp.parForCache(fakePIV,nImg,*args,**kwargs)
  
  pfPool=ParForPool()
  pfPool.startParPool(pfPool.numCoresParPool)
  #pp.simpleFor(fakePIV,nImg,*args,**kwargs)
  pp.numUsedCores  =4
  
  #pp.parForExtPool(pfPool.parPool,fakePIV,nImg,*args,**kwargs)
  pp.parForExtPool(pfPool.parPool,fakePIV,nImg,*args,**kwargs)
  pfPool.closeParPool()
  pp.parFor(fakePIV,nImg,*args,**kwargs)
  #pp.parFor(fakePIV,nImg,*args,**kwargs)
  prTime(0,'Fine')
  
    

if __name__ == "__main__":
  main()

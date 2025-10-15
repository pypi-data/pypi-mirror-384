''' helper functions for reading cfg files'''
from typing import Tuple,Callable,TextIO,Union
def readNumCfg(f,ind:int,convFun:Callable,separator=',',comment='%')->Tuple[int,Union [int,float]]:
  ''' reads a number from a cfg file'''
  
  while (line:=f.readline())[0]==comment:
    ind+=1
  
  return  ind+1,convFun(line.strip().split(separator)[0])

def readCfgTag(f:TextIO)->str:
  ''' returns the cfg tag'''
  return f.readline()[0:8]

def readNumVecCfg(f,ind:int,convFun,separator=',',comment='%')->Tuple[int,list[Union [int,float]]]:
  ''' reads a vector of numbers from a cfg file'''
  
  while (line:=f.readline())[0]==comment:
    ind+=1
  nums=line.strip().split(separator)[0].split('[')[1].split(']')[0].strip()

  return  ind+1,[convFun(num) for num in nums.split(' ')]
def readCalFile(buffer:str)->Tuple[int,int ,list[float]]:
    ''' reads the calibration constants from a file
      buffer is the name of the file
      if numCostCalib is different from none it is used regardless of the value in  the file
      In output returns flagCal,numCostCalib,cost 
    '''
    try:
      with open(buffer,'r') as f:
        tag=readCfgTag(f)
        
        if tag != "%SP00015":
          raise RuntimeError(f'Wrong tag in file: {buffer}') 
        ind=1
        ind,flagCal=readNumCfg(f,ind,int)
        ind,numCostCalib=readNumCfg(f,ind,int)
        
        cost=[0]*numCostCalib
        for i in range(numCostCalib):# dati->NumCostCalib; i++):
          ind,cost[i]=readNumCfg(f,ind,float)
      return flagCal,numCostCalib,cost
        #if "%SP00015"
        #for index, line in enumerate(f):              pri.Info.white("Line {}: {}".format(index, line.strip()))
    #except Exception as exc: 
    except IOError as exc: 
      raise RuntimeError(f'Error opening the calibration constants file: {buffer}') from exc
    except ValueError as exc: 
      raise RuntimeError(f'Error reading line:{ind+1} of file: {buffer}') from exc
    except IndexError as exc: 
      raise RuntimeError(f'Error reading array in line:{ind+1} of file: {buffer}') from exc  
  
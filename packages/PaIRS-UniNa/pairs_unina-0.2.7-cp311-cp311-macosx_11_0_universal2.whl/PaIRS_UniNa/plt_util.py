''' plt utilities '''
from typing import List#, Set, Dict, Tuple, Optional
from  struct import unpack
import numpy as np



def writePlt(outFileName:str,mat,title:str,varNames:List[str],zoneTitle:str)->None :
  ''' write tecplot binary files'''
  nVar=len(mat)
  h,w=mat[0].shape
  tecIntest=b'#!TDV71 '

  def writeLong(l):
    f.write(np.int32(l))
  def writeFloat32(fl):
    f.write(np.float32(fl))
  def writeString(s):
    for c in str.encode(s):
      f.write(np.int32(c))
    f.write(np.int32(0))
    return
  #apertura file binario di output .plt
  f=open(outFileName,"wb")

  #scrittura nel file di output del TEST
  f.write(tecIntest)
    #scrittura nel file di output di 1 (ordine dei bytes BO???)
  writeLong(1)
  #scrittura del titolo
  writeString(title)

  #scrittura numero e nome delle variabili
  writeLong(nVar)
  for s in varNames:
    writeString(s)
  writeFloat32(299.0)
  #ZONE NAME
  writeString(zoneTitle)
  #scrittura del BLOCK POINT
  writeLong(1)
  #scrittura del COLORE
  writeLong(-1)
  #scrittura nel file di output della larghezza e altezza img W e H
  writeLong(w)
  writeLong(h)
  #scrittura nel file di output della dimensione Z
  writeLong(1)
  #scrittura nel file di output di 357.0 (bo????)
  writeFloat32(357.0)
  #scrittura nel file di output di 299.0 (bo????)
  writeFloat32(299.0)
  #scrittura nel file di output di 0 (bo????)
  writeLong(0)
  #sizeof variabili
  for _ in range (0,nVar):
    writeLong(1)

  #scrittura nel file di output delle matrici x,y,u,v,up,vp (variabili)
  writeFloat32(np.ascontiguousarray(np.transpose(mat,(1,2,0))))

  f.flush()
  f.close()

  return
def readPlt(inFileName):
  ''' read tecplot binary files 
  returns a 3d array [w,h,nVar]
  '''
  #nVar=len(Mat)
  #h,w=Mat[0].shape
  tecIntest=b'#!TDV71 '


  def readFloat32():
    return unpack('f',f.read(4))[0]

  def readLong():
    return unpack('i',f.read(4))[0]
  def readString():
    s=''
    while True:
      ic=unpack('i',f.read(4))[0]
      if ic==0: 
        break
      s+=chr(ic)
    return s
   

  #apertura file binario di output .plt
  f=open(inFileName,"rb")

  #scrittura nel file di output del TEST
  tecIntest=f.read(8)
  if tecIntest!=b'#!TDV71 ':
    print("ERrore")
  if readLong()!=1:
    print("ERrore")
  #Lettura del titolo
  _=readString()

  #lettura numero e nome delle variabili
  nVar=readLong()
  varNames=[]
  for _ in range(nVar):
    varNames.append(readString())
  if readFloat32()!=299:
    print("ERrore")
  #ZONE NAME
  _=readString()
  #scrittura del BLOCK POINT
  readLong()
  #scrittura del COLORE
  readLong()
  #scrittura nel file di output della larghezza e altezza img W e H
  w=readLong()
  h=readLong()
  #scrittura nel file di output della dimensione Z
  if readLong()!=1:
    print("ERrore")#3d nonprevisto
  if readFloat32()!=357:
    print("ERrore")
  if readFloat32()!=299:
    print("ERrore")  
  readLong()
  for _ in range(nVar):
    dimVar=readLong()   
  ty=np.float32 if dimVar==1 else np.float64
  aa=np.reshape(np.fromfile(f, ty,count=w*h*nVar),[h,w,nVar])

  f.close()
  return  aa,varNames





if __name__ == "__main__":
   i=0
   nomeFileOut= f"{'test'}{i:0{4:d}d}.plt"
   readPlt(nomeFileOut)

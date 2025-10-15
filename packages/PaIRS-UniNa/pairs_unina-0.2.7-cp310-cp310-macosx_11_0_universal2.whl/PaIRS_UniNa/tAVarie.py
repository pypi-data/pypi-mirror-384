''' printing routines'''
from enum import Enum
from time import time



def  commenti():
  '''
  ## Descrizione di alcuni commenti (Doppio ## per titolo Anche singolo #)
  ### Sotto titolo (###)
  #### Sotto titolo (####)

  Questo è un link interno [commenti] o esterno [https://dartdoc.takyam.com/articles/doc-comment-guidelines/#markup].

  L'editor fa un wrap automatico Per andare a capo mettere una linea vuota altrimenti il testo della linea successiva si attacca a quella precedente.
  
  Lista formattata * o numero seguito da punto
  1. item continues until next list item or blank line
  2. next item

  Non funzionano per python:
  * Per il corsivo utilizzare _single underscore_ or *single asterisk*. Per Boldface **double asterisk** or __double underscore__
  * Inserire 5 spazi ed una linea vuota per mettere del codice che poi verrà formattato

    $ def  commenti():
      void commenti(){}

  in alternativa usare (alt96) anche se non mi sembra che funzioni `def  commenti()` (note the backquotes)
  '''
  return



PrintTAPriority=Enum('PrintTAPriority' ,['never', 'veryLow', 'low', 'medium', 'mediumHigh', 'high', 'always' ])
'''
* never non stampa nulla
* always stampa sempre
* Altro stampa solo se la priorità impostata durante la fase di stampa è maggiore uguale di quella impostata nella classe (eccezione per PrintTAPriority.always)
* quindi impostando  PrintTA.flagPriority=PrintTAPriority.always non stampa nulla
* quindi impostando  PrintTA.flagPriority=PrintTAPriority.never  stampa tutto 
''' 

class PrintTA ():
  '''
  ## Usare al posto di Print con qualcosa del tipo

  * printTA = PrintTA(PrintTA.blue, PrintTA.faceStd,  PrintTAPriority.medium)
  * printTA.pr('blue',color=printTA.blue)
  * printTA.pr('green',color=printTA.green)
  * printTA.pr('yellow',color=printTA.yellow)
  * printTA.pr('magenta',color=printTA.magenta)
  * printTA.pr('cyan',color=printTA.cyan)
  * printTA.pr('white faceUnderline plus faceItalic',color=printTA.white,face=printTA.faceUnderline+printTA.faceItalic)
  * printTA.err('Error always bold and','red')
  * printTA.pri.Time('cyan with time',color=printTA.cyan) 

  Per disattivare la stampa:
  * PrintTA.flagPriority=PrintTAPriority.always

'''

  faceBold = ';1'
  faceItalic = ';3'
  faceUnderline = ';4'
  faceStd = ''

  stdCol = '0'
  red = '31'
  green = '32'
  yellow = '33'
  blue = '34'
  magenta = '35'
  cyan = '36'
  white = '37'
  _tAPrintESC = '\x1B['
  _tAPrintLAST = 'm'
  _tAPrintRESET = '\x1B[0m'
  flagPriority=PrintTAPriority.medium
  startTime=time()
  def __init__(self,color='37',face='',flagPriority=PrintTAPriority.medium, prefix='',suffix=''):
    self.face =face 
    self.color=color
    self.prefix=prefix
    self.flagPriority=flagPriority
    self.suffix=suffix
    
  def internalPrint(self, *args,**kwargs): 
    ''' change for a different print function'''
    print(*args,**kwargs,flush=True)

  
  # [https://en.wikipedia.org/wiki/ANSI_escape_code#SGR_parameters]
  # print in color with priority
  # msg text to print
  # color one of PrintTA.color (e.g. PrintTA.red)
  # face  one of   PrintTA.bold, PrintTA.italic, PrintTA.underline or PrintTA.stdFace
  # pri one of PrintTAPriority
  
  def pr(self,   *args,color=None, face=None, pri=None,**kwargs):
    ''' the printing function '''
    #if self.flagPriority is  PrintTAPriority.never: 
    if PrintTA.flagPriority is  PrintTAPriority.always: 
      return
    if color is None: 
      color=self.color
    if face is None: 
      face=self.face
    if pri is None :
      pri=self.flagPriority
    if pri.value < PrintTA.flagPriority.value: 
      return
    self.internalPrint(f'{self._tAPrintESC}{color}{face}{self._tAPrintLAST}{self.prefix}',end='')
    self.internalPrint(*args,f'{self.suffix}{self._tAPrintRESET}',**kwargs)
    
    #self.internalPrint(f'{self._tAPrintESC}{color}{face}{self._tAPrintLAST}{self.prefix}',*args,f'{self.suffix}{self._tAPrintRESET}',**kwargs)

  def err(self, *args,**kwargs):
    ''' print error always bold and red''' 
    self.pr( color= PrintTA.red, face= PrintTA.faceBold, pri= PrintTAPriority.medium,*args,**kwargs)

  def  prTime(self, *args,flagReset=0,color=None, face=None, pri=None,**kwargs):
    ''' 
    flagreset==0 stampa senza reset (tempo incremetale )
    flagreset==1 stampa e reset origin (tempo incremetale riazzera l'origine dei tempi)
    flagreset==2 stampa senza tempo  e reset origin
    flagreset==3 fa solo il reset dei tempi origin
     '''
    if PrintTA.flagPriority is  PrintTAPriority.always: 
      return


    if 0<=flagReset<=1: 
      self.pr(f'Deltat={time()-PrintTA.startTime}  -- ',*args, color=color, face=face, pri=pri,**kwargs)
    elif flagReset==2:
      self.pr(*args, color=color, face=face, pri=pri,**kwargs)
    if flagReset>0: 
      PrintTA.startTime=time()
  def printEvidenced(self,*args,sep='*', numLinee=4,numSep=20,color=None, face=None, pri=None,**kwargs):
    if PrintTA.flagPriority is  PrintTAPriority.always: 
      return
    dum=sep*numSep
    separator=f'{dum}\n'*(numLinee-1)+dum
    self.pr(separator,color=color, face=face, pri=pri)
    self.pr(*args, color=color, face=face, pri=pri,**kwargs)
    self.pr(separator,color=color, face=face, pri=pri)



def testPr():
    ''' can be used to test the priorities'''
    PrintTA(PrintTA.white, PrintTA.faceStd,  PrintTAPriority.never).pr ('never')
    PrintTA(PrintTA.white, PrintTA.faceStd,  PrintTAPriority.medium).pr ('medium')
    PrintTA(PrintTA.white, PrintTA.faceStd,  PrintTAPriority.high).pr ('high')
    PrintTA(PrintTA.white, PrintTA.faceStd,  PrintTAPriority.always).pr ('always')



class ColorPrint:
    def __init__(self,flagTime=False,prio=PrintTAPriority.medium,faceStd=PrintTA.faceStd,flagFullDebug=False):
        self.flagTime=flagTime
        self.prio=prio
        self.faceStd=faceStd
        self.flagFullDebug=flagFullDebug
        self.setPrints()

    def setPrints(self):
        if self.flagTime:
            self.white = lambda flagReset=0, *args, **kwargs: PrintTA(PrintTA.white, self.faceStd,  self.prio).prTime(flagReset,*args,**kwargs)
            self.red = lambda flagReset=0, *args, **kwargs: PrintTA(PrintTA.red, self.faceStd,  self.prio).prTime(flagReset,*args,**kwargs)
            self.green = lambda flagReset=0, *args, **kwargs: PrintTA(PrintTA.green, self.faceStd,  self.prio).prTime(flagReset,*args,**kwargs)
            self.blue = lambda flagReset=0, *args, **kwargs: PrintTA(PrintTA.blue, self.faceStd,  self.prio).prTime(flagReset,*args,**kwargs)
            self.cyan = lambda flagReset=0, *args, **kwargs: PrintTA(PrintTA.cyan, self.faceStd,  self.prio).prTime(flagReset,*args,**kwargs)
            self.magenta = lambda flagReset=0, *args, **kwargs: PrintTA(PrintTA.magenta, self.faceStd,  self.prio).prTime(flagReset,*args,**kwargs)
            self.yellow = lambda flagReset=0, *args, **kwargs: PrintTA(PrintTA.yellow, self.faceStd,  self.prio).prTime(flagReset,*args,**kwargs)
        else:
            self.white = PrintTA(PrintTA.white, self.faceStd,  self.prio).pr 
            self.red = PrintTA(PrintTA.red, self.faceStd,  self.prio).pr
            self.green = PrintTA(PrintTA.green, self.faceStd,  self.prio).pr
            self.blue = PrintTA(PrintTA.blue, self.faceStd,  self.prio).pr
            self.cyan = PrintTA(PrintTA.cyan, self.faceStd,  self.prio).pr
            self.magenta = PrintTA(PrintTA.magenta, self.faceStd,  self.prio).pr
            self.yellow = PrintTA(PrintTA.yellow, self.faceStd,  self.prio).pr

#if prio is assigned to never, in the gPaIRS initializiation the printing is deactivated, otherwise activated
#if prio is > veryLow, then by default the printing is activated after gPaIRS initialization
#flagFullDebug=True means that the printing is available only if fullDebug mode is active
class GPaIRSPrint:
    def __init__(self):
        self.General=ColorPrint(prio=PrintTAPriority.medium)
        self.Info=ColorPrint(prio=PrintTAPriority.medium)
        self.Time=ColorPrint(prio=PrintTAPriority.veryLow,flagTime=True,faceStd=PrintTA.faceUnderline)
        self.Error=ColorPrint(prio=PrintTAPriority.medium,faceStd=PrintTA.faceBold)
        self.Process=ColorPrint(prio=PrintTAPriority.veryLow)
        self.Callback=ColorPrint(prio=PrintTAPriority.veryLow)
        self.Geometry=ColorPrint(prio=PrintTAPriority.veryLow,flagFullDebug=True)

pri=GPaIRSPrint()

if __name__ == '__main__':
  printTA = PrintTA(PrintTA.blue, PrintTA.faceStd,  PrintTAPriority.medium)
  printTA.pr('blue',color=printTA.blue)
  printTA.pr('green',color=printTA.green)
  printTA.pr('yellow',color=printTA.yellow)
  printTA.pr('magenta',color=printTA.magenta)
  printTA.pr('cyan',color=printTA.cyan)
  printTA.pr('white faceUnderline plus faceItalic',color=printTA.white,face=printTA.faceUnderline+printTA.faceItalic)
  
  printTA.err('Error always bold and','red')
  printTA.pri.Time('cyan with time',color=printTA.cyan)
  pri.Time.blue(0,'taPrintTime')
  printTA.flagPriority=PrintTAPriority.always    
  printTA.pri.Time('Non è stampato',color=printTA.cyan)
  #/// Stampa in rosso bold ed a PrintTAPriority.Always
  #void err(msg) => pr(msg, color: red, face: faceBold, pri: PrintTAPriority.always);


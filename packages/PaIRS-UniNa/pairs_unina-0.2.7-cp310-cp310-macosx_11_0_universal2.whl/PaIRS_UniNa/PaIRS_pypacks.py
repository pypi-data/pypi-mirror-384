from math import ceil, floor
#PrintTA.flagPriority=PrintTAPriority.always
Flag_DEBUG=False
Flag_DEBUG_PARPOOL=False
FlagPrintTime=False
FlagPrintCoding=False

pwddbg='Buss4Co1Pied1'
time_warnings_debug=-1 #10000 #milliseconds  #5000

import uuid
basefold='./'
basefold_DEBUGOptions=[]
basefold_DEBUG='./'
basefold_DEBUG_VIS=''
#basefold='B:/dl/apairs/jetcross'


developerIDs={
    'GP_Win_Office': '231128824800632', #'0x7824af430781',
    'GP_Win_Office_New': '140626882900161', #'0x7824af430781',
    'GP_Mac_Laptop': 'V94LRP93FV', #'0xa275dd445ab0',
    'GP_WSL'       : 'b44ec1c0e5a74ffd97bb050c39ef6cb1',
    'TA_Win_Office': '160983906000941',           #'0xccb0da8c896e'
    'TA_Win_Office_New': '231128824801036',           #??
     }

import psutil,subprocess
def getCurrentID():
    #return hex(uuid.getnode())
    serial_number=None
    try:
        if psutil.LINUX:
            def get_linux_serial():
                from pathlib import Path
                candidates = [
                    Path("/sys/class/dmi/id/board_serial"),
                    Path("/sys/class/dmi/id/product_uuid"),
                    Path("/etc/machine-id"), Path("/var/lib/dbus/machine-id") #WSL
                ]
                for p in candidates:
                    try:
                        if p.is_file():
                            val = p.read_text(errors="ignore").strip()
                            if val and val.lower() not in {
                                "none", "unknown", "not specified", "to be filled by o.e.m."
                            }:
                                return val
                    except Exception as e:
                        if Flag_DEBUG:
                            print(f"Error while retrieving motherboard serial number: {e}")
                        continue
                return None
            serial_number = get_linux_serial()
            """"
            # On Linux, the motherboard serial number can be obtained from the /sys/class/dmi/id/board_serial file
            with open('/sys/class/dmi/id/board_serial', 'r') as f:
                serial_number = f.read().strip()
            """
        elif psutil.WINDOWS:
            # On Windows, the motherboard serial number can be obtained using WMI
            output = subprocess.check_output(["wmic", "baseboard", "get", "SerialNumber"]).decode('utf-8')
            serial_number = output.strip().split('\n')[1].strip()
        elif psutil.MACOS:
            # On macOS, the motherboard serial number can be obtained using the system_profiler command
            output = subprocess.check_output(["system_profiler", "SPHardwareDataType"])
            for line in output.splitlines():
                if b'Serial Number (system)' in line:
                    serial_number = line.split(b':')[1].strip().decode('utf-8')
    except Exception as e:
        if Flag_DEBUG:
            print(f"Error while retrieving motherboard serial number: {e}")
    return serial_number

currentID=getCurrentID()
FlagAddMotherBoard=False
if currentID in (developerIDs['GP_Win_Office'],developerIDs['GP_Win_Office_New']): #gerardo windows
    basefold_DEBUG='C:/desk/PIV_Img/_data/PIV_data/virtual_case/'
    basefold_DEBUGOptions=[
                            'C:/desk/PIV_Img/img1/',
                            'C:/desk/PIV_Img/_data/PIV_data/virtual_case/', 
                            'C:/desk/PIV_Img/_data/PIV_data/real_case/',
                            'C:/desk/PIV_Img/_data/Calibration_data/pinhole/',
                            'C:/desk/PIV_Img/_data/Calibration_data/cylinder/',
                            ]
    basefold_DEBUG_VIS='C:/desk/PIV_Img/_data/PIV_data/real_case/'
elif  currentID==developerIDs['GP_WSL']:
    basefold_DEBUG='/mnt/c/desk/PIV_Img/_data/PIV_data/virtual_case/'
    basefold_DEBUGOptions=[
                            '/mnt/c/desk/PIV_Img/img1/',
                            '/mnt/c/desk/PIV_Img/_data/PIV_data/virtual_case/', 
                            '/mnt/c/desk/PIV_Img/_data/PIV_data/real_case/',
                            '/mnt/c/desk/PIV_Img/_data/Calibration_data/pinhole/',
                            '/mnt/c/desk/PIV_Img/_data/Calibration_data/cylinder/',
                            ]
    basefold_DEBUG_VIS='/mnt/c/desk/PIV_Img/_data/PIV_data/real_case/'
elif currentID==developerIDs['GP_Mac_Laptop']: #gerardo mac
    basefold_DEBUG='/Users/gerardo/Desktop/PIV_Img/swirler_png/' #'/Users/gerardo/Desktop/PIV_Img/img1/'
    basefold_DEBUGOptions=[
                            '/Users/gerardo/Desktop/PIV_Img/img1/',
                            '/Users/gerardo/Desktop/PaIRS_examples/PIV_data/virtual_case/',     
                            #'/Users/gerardo/Desktop/PaIRS_examples/PIV_data/virtual_case_2/',     
                            '/Users/gerardo/Desktop/PaIRS_examples/PIV_data/real_case/',
                            '/Users/gerardo/Desktop/PaIRS_examples/SPIV_data/real_case/img/',
                            '/Users/gerardo/Desktop/PaIRS_examples/Calibration_data/pinhole/',
                            '/Users/gerardo/Desktop/PaIRS_examples/Calibration_data/cylinder/'
                            ]
    basefold_DEBUG_VIS='/Users/gerardo/Desktop/PaIRS_examples/PIV_data/real_case/'
    basefold_DEBUG_VIS='/Users/gerardo/Desktop/PIV_Img/img1/'
elif currentID in (developerIDs['TA_Win_Office'],developerIDs['TA_Win_Office_New']): #TA windows
    basefold_DEBUG=r'C:\desk\Attuali\PythonLibC\PIV\img'
    basefold_DEBUGOptions=[
                            'C:/desk/PIV_Img/img1/',
                            'C:/desk/PIV_Img/swirler_png/',                            
                            '../../img/calib/',
                            r'C:\desk\Attuali\PythonLibC\PIV\img',
                            ]
    basefold_DEBUG_VIS=''
else:
    FlagAddMotherBoard=True
    
#fontName='Inter'
#fontName='Cambria'
fontName='Arial'
fontPixelSize=14
dfontLog=2
fontPixelSize_lim=[8,20]
import platform
if (platform.system() == "Linux"):
  fontName='sans-serif'

Flag_SHOWSPLASH=False
Flag_GRAPHICS=True  #if True PaIRS plots while processing
Flag_NATIVEDIALOGS=True
Flag_DISABLE_onUpdate=False
Flag_RESIZEONRUN=False
Flag_GROUPSEPARATOR=True

imin_im_pair=1 #minimum index value for image pair

f_empty_width=250  #blank space in scrollable area within the main window
time_ScrollBar=250 #time of animation of scroll area
time_callback2_async=0  #time to test async callbacks
time_showSplashOnTop=250

fileChanges='Changes.txt'
fileWhatsNew=['whatsnew.txt','whatwasnew.txt']
icons_path="icons/"

from psutil import cpu_count
NUMTHREADS_MAX=cpu_count(logical=True)#-1
if NUMTHREADS_MAX<1: NUMTHREADS_MAX=1
ParFor_sleepTime=0.1
#multithreading
FlagStopWorkers=[0]#messo qui ma utilizzato solo da min e PIV
NUMTHREADS_gPaIRS=0
SleepTime_Workers=0.5 #for multithreading and other stuff
timeOutWorker=0  # used in parfor when the proces is stuck

from .__init__ import __version__,__subversion__,__year__,__mail__
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import*
from PySide6.QtGui import *
from PySide6.QtWidgets import*
from typing import cast
if Flag_DEBUG_PARPOOL: import debugpy

import numpy as np
import scipy.io, pickle
from PIL import Image
from PIL.ImageQt import ImageQt
import sys, os, glob, copy, re, traceback, datetime
from time import sleep as timesleep
from collections import namedtuple
from .plt_util import writePlt, readPlt
#from multiprocessing import cpu_count

from .tAVarie import *
deltaTimePlot=0.75
import concurrent.futures
import gc#garbage collection si può eliminare
from .mtfPIV import *

import sys
import concurrent.futures
import asyncio

_old_init_QAction = QAction.__init__
def _new_init_QAction(self, *args, **kwargs):
    _old_init_QAction(self, *args, **kwargs)
    try:
        self.setIconVisibleInMenu(True)
    except Exception:
        pass
QAction.__init__ = _new_init_QAction
_old_init_QMenu = QMenu.__init__
def _new_init_QMenu(self, *args, **kwargs):
    _old_init_QMenu(self, *args, **kwargs)
    try:
        self.menuAction().setIconVisibleInMenu(True)
    except Exception:
        pass
QMenu.__init__ = _new_init_QMenu

# --- Patch dei metodi QMenu che CREANO/AGGIUNGONO azioni (copre gli overload C++) ---
_old_addAction = QMenu.addAction
def _new_addAction(self, *args, **kwargs):
    act:QAction = _old_addAction(self, *args, **kwargs)   # può essere creato lato C++
    try:
        if isinstance(act, QAction):
            act.setIconVisibleInMenu(True)
    except Exception:
        pass
    return act
QMenu.addAction = _new_addAction

Flag_ISEXE=getattr(sys, 'frozen', False) #made by pyInstaller
EXEurl='https://www.pairs.unina.it/#download'

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
        self.Info=ColorPrint(prio=PrintTAPriority.medium)
        self.Time=ColorPrint(prio=PrintTAPriority.medium if FlagPrintTime else PrintTAPriority.veryLow,flagTime=True,faceStd=PrintTA.faceUnderline)        
        self.Error=ColorPrint(prio=PrintTAPriority.medium,faceStd=PrintTA.faceBold)
        self.IOError=ColorPrint(prio=PrintTAPriority.veryLow,faceStd=PrintTA.faceBold)
        self.Process=ColorPrint(prio=PrintTAPriority.veryLow)
        self.Callback=ColorPrint(prio=PrintTAPriority.veryLow)
        self.TABparDiff=ColorPrint(prio=PrintTAPriority.veryLow)
        self.PlotTime=ColorPrint(prio=PrintTAPriority.veryLow,flagTime=True,faceStd=PrintTA.faceUnderline,flagFullDebug=True)
        self.Coding=ColorPrint(prio=PrintTAPriority.medium if FlagPrintCoding else PrintTAPriority.never,flagFullDebug=True)

pri=GPaIRSPrint()
printTypes={}
for npt,pt in pri.__dict__.items():
    printTypes[npt]=pt.prio in (PrintTAPriority.medium,PrintTAPriority.mediumHigh,PrintTAPriority.high,PrintTAPriority.always)

def activateFlagDebug(Flag=True):
    ''' used to activate the debug mode;  when called with false disables'''
    Flag_DEBUG=Flag
    PrintTA.flagPriority=PrintTAPriority.veryLow   if  Flag_DEBUG else PrintTAPriority.always
    global basefold
    from .gPaIRS import Flag_fullDEBUG
    if not Flag_fullDEBUG:
        basefold='./'
    else:
        basefold=basefold_DEBUG

PaIRS_Header=f'PaIRS - version {__version__}\n'+\
    'Particle Image Reconstruction Software\n'+\
    f'(C) {__year__} Gerardo Paolillo & Tommaso Astarita.\nAll rights reserved.\n'+\
    f'email: {__mail__}\n'+\
    '****************************************\n'
	
from .parForMulti import *
#from pkg_resources import resource_filename
from .parForMulti import ParForMul

import faulthandler # per capire da dove vengono gli errori c
faulthandler.enable()

if __package__ or "." in __name__:
  import PaIRS_UniNa.PaIRS_PIV as PaIRS_lib
else:
  import sys
  if (platform.system() == "Darwin"):
    sys.path.append('../lib/mac')
  else:
    #sys.path.append('PaIRS_PIV')
    sys.path.append('../lib')
  import PaIRS_PIV as PaIRS_lib

if __package__ or "." in __name__:
    import importlib.resources as resources
    resources_path = resources.files(__package__)
    foldPaIRS = str(resources_path)+"\\"
    foldPaIRS = foldPaIRS.replace('\\', '/')
else:
    foldPaIRS='./'
class ProcessTypes:
    null=None
    min=0
    piv=1
    spiv=2
    tpiv=3
    cal=10

    singleCamera=[piv]
    threeCameras=[min,tpiv]

class StepTypes:
    null=None
    min=0
    piv=1
    spiv=2
    cal=10
    disp=11

process={
    ProcessTypes.null: '-',
    ProcessTypes.min: 'minimum',
    ProcessTypes.piv: 'PIV',
    ProcessTypes.spiv: 'SPIV',
    ProcessTypes.tpiv: 'TPIV',
    ProcessTypes.cal: 'calibration',
}
process_items=[v for v in process.values()]
process_ord=range(len(process_items))
class outExt:
    #legacy
    cfg='.pairs_cfg'
    dum='.pairs_dum'
   
    #Workspaces and projects
    wksp='.pairs_wksp'
    proj='.pairs_proj'

    #StepTypes
    min='.pairs_min'
    piv='.pairs_piv'
    spiv='.pairs_spiv'
    cal='.pairs_cal'
    calvi='.calvi'
    disp='.pairs_disp'
    
    #Further types of variable
    #PIV process
    pro='.pairs_pro'
    #CalVi
    cfg_calvi='.calvi_cfg'
    pla='.pairs_pla'


lastcfgname='lastWorkSpace'+outExt.wksp
fileChanges=foldPaIRS+'Changes.txt'
icons_path=foldPaIRS+icons_path

if not Flag_ISEXE:
    fileWhatsNew=[foldPaIRS+f for f in fileWhatsNew]
    
    lastcfgname=foldPaIRS+lastcfgname
    pro_path=foldPaIRS+"pro/"
else:
    from pathlib import Path
    exe_dir = str(Path(sys.argv[0]).resolve().parent)+'/'
    fileWhatsNew=[foldPaIRS+fileWhatsNew[0],exe_dir+fileWhatsNew[1]]
    lastcfgname = exe_dir + lastcfgname
    pro_path = exe_dir + "pro/"
     

if not os.path.exists(pro_path):
    try:
        os.mkdir(pro_path)
    except Exception as inst:
        pri.Error.red(f'It was not possible to make the directory {pro_path}:\n{traceback.format_exc()}\n\n{inst}')
custom_list_file="pro_list.txt"

exts = Image.registered_extensions()
supported_exts = sorted({ex for ex, f in exts.items() if f in Image.OPEN})
text_filter = "Common image files (*.bmp *.gif *.ico *.jpeg *.jpg *.png *.tif *.tiff *.webp"\
   + ");;"+" ;;".join(["{} ".format(fo[1:]) +"(*{})".format(fo) for fo in supported_exts])
#text_filter = "All files (*"\
#   + ");;"+" ;;".join(["{} ".format(fo[1:]) +"(*{})".format(fo) for fo in supported_exts])
#text_filter = "All files ("+ " ".join(["*{}".format(fo) for fo in supported_exts])\
#   + ");;"+" ;;".join(["{} ".format(fo[1:]) +"(*{})".format(fo) for fo in supported_exts])

if Flag_NATIVEDIALOGS: 
    optionNativeDialog=QFileDialog.Options()
else:
    optionNativeDialog=QFileDialog.Option.DontUseNativeDialog 
  
def warningDialog(self:QWidget,Message,time_milliseconds=0,flagScreenCenter=False,icon:QIcon=QIcon(),palette=None,pixmap=None,title='Warning!',flagRichText=False,flagNoButtons=False,addButton:dict=None,FlagStayOnTop=False,pixmapSize=64):  #addButton=['Print Message',lambda: print(Message)]
    dlg=None
    if Message:
        if isinstance(self,QMainWindow) and hasattr(self,'w_Input'):
            dlg = QMessageBox(self.w_Input)
        else:
            dlg = QMessageBox(self)
        dlg.setWindowTitle(title)
        dlg.setText(str(Message))
        
        if flagRichText: dlg.setTextFormat(Qt.TextFormat.RichText)
        if flagNoButtons: 
            dlg.setStandardButtons(QMessageBox.StandardButton.NoButton)
        else:
            dlg.setStandardButtons(QMessageBox.StandardButton.Ok)
            if addButton: 
                for addB, addAction in addButton.items():
                    abutt = dlg.addButton(addB, QtWidgets.QMessageBox.YesRole)
                    abutt.clicked.disconnect()
                    def aFun(fun):
                        fun()
                        dlg.done(0)
                    abutt.clicked.connect(lambda flag=None,fun=addAction: aFun(fun))
        dlg.setIcon(QMessageBox.Warning)
        if icon:
            if type(icon)==QIcon: dlg.setWindowIcon(icon)
            else:
                try:
                    iconW=QIcon()
                    iconW.addFile(icon)
                    dlg.setWindowIcon(iconW)
                except Exception as e:
                    pri.Error.red(f'Error while reading the window icon from the file {icon}:\n{e}')
        else:
            if not hasattr(self,'windowIcon') or not self.windowIcon():
                iconW=QIcon()
                iconW.addFile(icons_path+'icon_PaIRS.png')
                dlg.setWindowIcon(iconW)
            else:
                dlg.setWindowIcon(self.windowIcon())
        if palette:
            dlg.setPalette(palette)
        if pixmap:
            dlg.setIconPixmap(QPixmap(pixmap).scaled(pixmapSize, pixmapSize, Qt.AspectRatioMode.KeepAspectRatio,Qt.SmoothTransformation))
        if self:
            dlg.setFont(self.font())
            c=dlg.findChildren(QObject)
            for w in c:
                if hasattr(w,'setFont'):
                    font=w.font()
                    font.setFamily(fontName)
                    w.setFont(font)
        #dlg.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint) 
        dlg.show()
        if flagScreenCenter and hasattr(self,'maximumGeometry'):
            geom=dlg.geometry()
            geom.moveCenter(self.maximumGeometry.center())
            dlg.setGeometry(geom)
        if time_milliseconds:
            QTimer.singleShot(time_milliseconds, lambda : dlg.done(0))
        else:
            if Flag_DEBUG and time_warnings_debug>=0:
                QTimer.singleShot(time_warnings_debug, lambda : dlg.done(0))  
        if FlagStayOnTop: dlg.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        if not flagNoButtons: dlg.exec()
    return dlg

def questionDialog(self,Message,icon=QMessageBox.Warning):
    if isinstance(self,QMainWindow) and hasattr(self,'w_Input'):
        dlg = QMessageBox(self.w_Input)
    else:
        dlg = QMessageBox(self)
    dlg.setWindowTitle("Warning!")
    dlg.setText(str(Message))
    if not self.windowIcon():
        icons_path+'icon_PaIRS.png'
        iconW=QIcon()
        iconW.addFile(icon)
        dlg.setWindowIcon(iconW)
    else:
        dlg.setWindowIcon(self.windowIcon())

    dlg.setStandardButtons(QMessageBox.Yes|QMessageBox.No)
    dlg.setDefaultButton(QMessageBox.Yes)
    dlg.setIcon(icon)
    if self:
        dlg.setFont(self.font())
        c=dlg.findChildren(QObject)
        for w in c:
            if hasattr(w,'setFont'):
                font=w.font()
                font.setFamily(fontName)
                w.setFont(font)
    button = dlg.exec()
    return button==QMessageBox.Yes    

def inputDialog(self,title,label,icon=None,palette=None,completer_list=[],width=0,flagMouseCenter=False,flagScreenCenter=False):
    dlg = QtWidgets.QInputDialog(self)
    dlg.setWindowTitle(title)
    dlg.setLabelText(label)
    dlg.setTextValue("")
    if icon:
        dlg.setWindowIcon(icon)
    if palette:
        dlg.setPalette(palette)
    le = dlg.findChild(QtWidgets.QLineEdit)
    if self:
        dlg.setFont(self.font())
        c=dlg.findChildren(QObject)
        for w in c:
            if hasattr(w,'setFont'):
                font=w.font()
                font.setFamily(fontName)
                w.setFont(font)
    
    if len(completer_list):
        completer = QtWidgets.QCompleter(completer_list, le)
        completer.setCompletionMode(QCompleter.CompletionMode(1))
        le.setCompleter(completer)

    if not width: width=int(0.5*self.width())
    dlg.resize(width,dlg.height())
    dlg.updateGeometry()

    if flagMouseCenter:
        dlg.show()
        geom = dlg.geometry()
        geom.moveCenter(QtGui.QCursor.pos())
        dlg.setGeometry(geom)

    if flagScreenCenter and hasattr(self,'maximumGeometry'):
        dlg.show()
        geom=dlg.geometry()
        geom.moveCenter(self.maximumGeometry.center())
        dlg.setGeometry(geom)
    
    c=dlg.findChildren(QObject)
    for w in c:
        if hasattr(w,'setFont'):
            font=w.font()
            font.setFamily(fontName)
            w.setFont(font)

    ok, text = (
        dlg.exec() == QtWidgets.QDialog.Accepted,
        dlg.textValue(),
    )
    return ok, text
  
def errorDialog(self,Message,*args):
    if len(args): time_milliseconds = args[0]
    else:  time_milliseconds=0
    if Message:
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Warning!")
        dlg.setText(str(Message))
        copy_butt = dlg.addButton('Copy error to clipboard', QtWidgets.QMessageBox.YesRole)
        copy_butt.clicked.disconnect()
        def copy_fun():
           QApplication.clipboard().setText(Message)
           dlg.done(0)
        copy_butt.clicked.connect(copy_fun)
        ok_butt = dlg.addButton('Ok', QtWidgets.QMessageBox.YesRole)
        dlg.setIcon(QMessageBox.Critical)
        if self:
            dlg.setFont(self.font())
            c=dlg.findChildren(QObject)
            for w in c:
                if hasattr(w,'setFont'):
                    font=w.font()
                    font.setFamily(fontName)
                    w.setFont(font)
        #dlg.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint) 
        if time_milliseconds>=0:
            QTimer.singleShot(time_milliseconds, lambda : dlg.done(0))
        else:
            if Flag_DEBUG and time_warnings_debug>=0:
                QTimer.singleShot(time_warnings_debug, lambda : dlg.done(0))                
        dlg.exec()

def printException(stringa='',flagMessage=Flag_DEBUG,flagDispDialog=False,exception=None):  #timemilliseconds=-1 ***
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
    * exception is the exception, normally you don't need it but for parForMul is required
    '''
    #print(f'***** ParForMul Exception *****  Deltat={time()-PrintTA.startTime}\n{traceback.format_exc()}',*args,**kwargs)
    #print(sys.exc_info()[2])
    Message=""
    if flagMessage or flagDispDialog:
        Message+=f'Please, mail to: {__mail__}\n\n'
        Message+=f'***** PaIRS Exception *****  time={time()-PrintTA.startTime}\n'+stringa
        Message+=f'***** traceback.print_exc() *****  \n'
        if exception is None:
          Message+=traceback.format_exc()
        else:
          Message+=''.join(traceback.format_exception(exception))
        Message+=f'***** traceback.extract_stack() *****  \n'
        # to print all the queue comment if not needed
        for st in traceback.format_list(   traceback.extract_stack()):
            if 'PAIRS_GUI' in st and 'printException'not in st:# limits to files that have  PAIRS_GUI in the path
                Message+=st
        Message+=f'***** PaIRS Exception -> End *****\n'
        if Flag_DEBUG: print(Message)
        #errorDialog(None,Message,timemilliseconds) ***
        if flagDispDialog:
            WarningMessage=f'PaIRS Exception!\n\n'+f'Do you want to copy the error message to the clipboard so that you can send it to: {__mail__}?'
            flagYes=questionDialog(None,WarningMessage,QMessageBox.Critical)
            if flagYes:
                QApplication.clipboard().setText(Message)
    return Message
   
def noPrint(*args,**kwargs):
    pass

#import unidecode
def myStandardPath(path):
    currpath = path.rstrip() # Remove trailing white spaces from the path
    currpath = currpath.replace('\\', '/')  # Replace all backslashes with forward slashes
    currpath = currpath.rstrip('/') + '/' if currpath else './' # Add a trailing slash to the path if not present
    currpath = re.sub('/+', '/', currpath) # Reduce consecutive slashes to a single slash
    return currpath

def myStandardRoot(root):
    currroot = root.rstrip()  # Remove trailing white spaces from the root
    currroot = currroot.replace('\\', '/')  # Replace all backslashes with forward slashes
    currroot = re.sub('/+', '/', currroot)  # Reduce consecutive slashes to a single slash
    return currroot

def findFiles_sorted(pattern):
    list_files=glob.glob(pattern)
    files=sorted([re.sub(r'\\+',r'/',f) for f in list_files],key=str.lower)
    return files

def transfIm(OUT,flagTransf:int=2,Images:list=[],flagRot=1):
    ''' the output is a copy (not deep) of  the input list)
    flagTransf==0 solo img
    flagTransf==1 solo piv
    flagTransf==2 solo entrambi (default)
    '''
    if  len(Images)==0: return
    if OUT.FlagNone: return Images

    if flagTransf==1:  #solo PIV
        ops=OUT.aimop
    else:
        if OUT.h>0 and OUT.w>0:
          for i,_ in enumerate(Images):
              Images[i]=Images[i][OUT.y:OUT.y+OUT.h,OUT.x:OUT.x+OUT.w]#limita l'img
        ops=OUT.bimop if flagTransf==0 else OUT.vecop
    
    
    if len(ops):
        for i,_ in enumerate(Images):# non funziona se si fa il normale ciclo for img in Images
            for op in ops:
                if op==1:  #rot 90 counter
                    Images[i]=np.rot90(Images[i],-1*flagRot)
                elif op==-1: #rot 90 clock
                    Images[i]=np.rot90(Images[i],1*flagRot)
                elif op==3: #flip
                    Images[i]=np.flipud(Images[i])
                elif op==2:
                    Images[i]=np.fliplr(Images[i])
            Images[i]=np.ascontiguousarray(Images[i])
    return Images # the input list is also changed accordingly but it may come in handy in some situation in order to avoid explicitly make a copy 

def transfVect(OUT,PIV):
    x,y,u,v=transfIm(OUT,flagTransf=1,Images=[PIV.x,PIV.y,PIV.u,PIV.v],flagRot=1)# l'output non sarebbe necessario ma così mi fa anche la copia (per ora virtuale)
    for op in OUT.aimop: 
        if op==-1:  #rot 90 counter
            # PIV.u,PIV.v=PIV.v,-PIV.u #questa da errore penso perchè non riesce a fare la copia
            u,v=v,-u
            x,y=y,OUT.w-x
        elif op==1: #rot 90 clock
            u,v=-v,u
            x,y=OUT.h-y,x
        elif op==2:#flip
            u=-u
            x=OUT.w-x
        elif op==3: #flip
            v=-v
            y=OUT.h-y
    return x,y,u,v

def readCustomListFile():
    custom_list=[]
    filename=pro_path+custom_list_file
    if os.path.exists(filename):
        try:
            with open(filename,'r') as file:
                while True:
                    line = file.readline()
                    if not line:
                        break   
                    else:
                        l=line.strip()
                        if l: custom_list.append(l)
                file.close()
        except:
            pri.Error.red(f'Error while opening the custom process list file: {filename}.\n{traceback.format_exc()}\n')
    return custom_list

def setCustomList(task):
    custom_list=readCustomListFile()
    for k,name in enumerate(custom_list):
        filename=pro_path+name+outExt.pro
        try:
            with open(filename,'rb') as file:
                var=pickle.load(file)
                task(var,name)
        except Exception as inst:
            pri.Error.red(f'Error while loading custom process file {filename}\t[from list]:\n{traceback.format_exc()}\n\n{inst}')
            custom_list.pop(k)
            if os.path.exists(filename):
                os.remove(filename)
    profiles=glob.glob(pro_path+f"*{outExt.pro}")
    for f in profiles:
        name=os.path.basename(f)[:-10]
        if not name in custom_list:
            filename=myStandardRoot(f)
            try:
                with open(filename,'rb') as file:
                    var=pickle.load(file)
                    task(var,name)
                    custom_list.append(name)
            except Exception as inst:
                pri.Error.red(f'Error while loading the custom process file {filename}\t[from disk]:\n{traceback.format_exc()}\n\n{inst}')
                if os.path.exists(filename):
                    os.remove(filename)
    rewriteCustomList(custom_list)
    return custom_list

def rewriteCustomList(custom_list):
    filename=pro_path+custom_list_file
    try:
        with open(filename,'w') as file:
            for c in custom_list:
                file.write(c+'\n')
            file.close()
    except:
        pri.Error.red(f'Error while rewriting the custom process file {filename}\t[from disk]:\n{traceback.format_exc()}\n')

def identifierName(typeObject:str='proc'):
    username=platform.system()+'-'+os.environ.get('USER', os.environ.get('USERNAME'))
    date_time=QDate.currentDate().toString('yyyy/MM/dd')+'-'+\
            QTime().currentTime().toString()
    ppid=str(os.getppid())+'-'+str(os.getpid())
    version='PaIRS-v'+__version__
    version_user_info=version+'_'+username+'_'+date_time
    id=ppid+'_'+str(uuid.uuid4())
    name=version_user_info+'_'+typeObject+'_'+id
    return name, username, __version__

PlainTextConverter=QtGui.QTextDocument()
def toPlainText(text):
    PlainTextConverter.setHtml(text) #for safety
    return PlainTextConverter.toPlainText()

def showTip(obj,message):
    toolTipDuration=obj.toolTipDuration()
    obj.setToolTipDuration(3000)
    QToolTip.showText(QCursor.pos(),message)
    obj.setToolTipDuration(toolTipDuration)

def clean_tree(tree:QTreeWidget):
    def remove_children(item:QTreeWidgetItem):
        while item.childCount() > 0:
            child = item.takeChild(0)
            remove_children(child)
        del item

    while tree.topLevelItemCount() > 0:
        item = tree.takeTopLevelItem(0)
        # Elimina ricorsivamente tutti i figli dell'elemento
        remove_children(item)

def html_image(icon_path,size=16):
    text=f"""
        <img src="{icon_path}" width="{size}" height="{size}" style="margin-right: 0px;">
    """
    return text

def procOutName(self):
    for attr_name, attr_value in vars(ProcessTypes).items():
        if attr_value == self.Process:
          procExt=getattr(outExt,attr_name) 
          break
    return f'{self.outPathRoot}{procExt}'

def stepOutName(self):
    for attr_name, attr_value in vars(StepTypes).items():
        if attr_value == self.Step:
          procExt=getattr(outExt,attr_name) 
          break
    return f'{self.outPathRoot}{procExt}'

def findIDFromLog(file_path):
    nMaximumLines=50
    try:
        with open(file_path, 'r') as file:
            # Legge fino a 50 righe (o meno, se il file ha meno righe)
            for _ in range(nMaximumLines):
                line = file.readline()
                if not line:  # Fine del file
                    break
                if line.startswith("PaIRS-v"):
                    return line.strip()  # Ritorna la riga trovata senza spazi extra
        return None  # Nessuna riga trovata
    except FileNotFoundError:
        pri.Error.red(f"File not found: {file_path}")
        return None

def resultCheck(tab,par,ind=None):
    if ind is None: ind=par.ind
    ITE=tab.gui.ui.Explorer.ITEfromInd(ind)
    filename=stepOutName(ITE.procdata)+'.log'
    if os.path.exists(filename):
        id=findIDFromLog(filename)
        FlagResult=id==ITE.procdata.name_proc
    else:
        FlagResult=False
    return FlagResult

def runPaIRS(self,command='',flagQuestion=True):
    Flag=__package__ or "." in __name__
    pyCommands={
                ''  : 'import PaIRS; PaIRS.run()',
                '-c': 'import PaIRS; PaIRS.cleanRun()',
                '-d': 'import PaIRS; PaIRS.debugRun()',
                '-calvi'   : 'import CalVi; CalVi.run()',
                '-calvi -c': 'import CalVi; CalVi.cleanRun()',
                '-calvi -d': 'import CalVi; CalVi.debugRun()',
                }
    nameIstance={
                '' : 'PaIRS',
                '-c': 'PaIRS (clean mode)',
                '-d': 'PaIRS (debug mode)',
                '-calvi'   : 'CalVi',
                '-calvi -c': 'CalVi (clean mode)',
                '-calvi -d': 'CalVi (debug mode)',
                }
    
    class SignalsinstPaIRS(QObject):
        errorSignal=Signal()
    class instPaIRS(QRunnable):
        def __init__(self):
            super(instPaIRS,self).__init__()
            self.isRunning=True
            self.signals=SignalsinstPaIRS()

        def run(self):
            try:
                import subprocess
                if Flag_ISEXE:
                    pri.Info.white(sys.executable+' '+command)
                    subprocess.call(sys.executable+' '+command,shell=True)
                else:
                    if Flag: #launched from package
                        pri.Info.white(sys.executable+' -m PaIRS_UniNa '+command)
                        subprocess.call(sys.executable+' -m PaIRS_UniNa '+command,shell=True)
                    else:
                        pri.Info.white(sys.executable+' -c '+'"'+f"import os; os.chdir('{os.getcwd()}'); {pyCommands[command]}"+'"')
                        subprocess.call(sys.executable+' -c '+'"'+f"import os; os.chdir('{os.getcwd()}'); {pyCommands[command]}"+'"',shell=True)
                self.isRunning=False
            except Exception as inst:
                pri.Error.red(inst)
                self.signals.errorSignal.emit()

    if flagQuestion:
        Message='Are you sure to launch a new istance of '+nameIstance[command]+'?'
        yes=questionDialog(self,Message)
        if not yes: return
    runnable = instPaIRS()
    runnable.signals.errorSignal.connect(lambda: self.warningDialog('It was not possible to launch the module from the present application!\nPlease, retry in another Python environment.'))
    QThreadPool.globalInstance().start(runnable)
    if not hasattr(self,'SecondaryThreads'):
        self.SecondaryThreads=[]
    self.SecondaryThreads.append(runnable)

def showSplash(filename=''+ icons_path +'logo_PaIRS_completo.png'):
    splash=QLabel()
    splash_pix = QPixmap(filename)
    splash.setPixmap(splash_pix)
    splash.setScaledContents(True)
    splash.setMaximumSize(360,360)
    splash.setWindowFlags(Qt.Window|Qt.FramelessWindowHint)
    splash.setAttribute(Qt.WA_NoSystemBackground)
    splash.setAttribute(Qt.WA_TranslucentBackground)
    splash.show()
    return splash

def checkLatestVersion(self,version,app:QApplication=None,splash:QLabel=None,flagWarning=1):
    flagStopAndDownload=False
    var=self.TABpar
    #var.FlagOutDated=0 if currentVersion==var.latestVersion else var.FlagOutDated
    if abs(var.FlagOutDated)==1:
        warningLatestVersion(self,app,flagExit=0,flagWarning=flagWarning,FlagStayOnTop=True)
        var.FlagOutDated=2 if var.FlagOutDated==1 else -2
        """
        flagStopAndDownload=questionDialog(self,f'A new version of the PaIRS_UniNa package is available. Do you want to download it before starting the current istance of {self.name}?')
        if flagStopAndDownload:
            if splash: splash.hide()
            downloadLatestVersion(self,app)
            return flagStopAndDownload
        else:
            var.FlagOutDated=2
        """
        
    packageName='PaIRS_UniNa'
    def printOutDated(flagOutDated,currentVersion,latestVersion):
        """"
        if not flagOutDated:
            flagOutDated2=any([c<l for (c,l) in zip(version.split('.'),latestVersion.split('.'))])
            if flagOutDated2: 
                currentVersion=version
                flagOutDated=1
        """
        var.currentVersion=currentVersion
        var.latestVersion=latestVersion
        if flagOutDated==1:
            sOut=f'{packageName} the current version ({currentVersion}) of {packageName} is obsolete! Please, install the latest version: {latestVersion} by using:\npython -m pip install --upgrade {packageName}'
            var.FlagOutDated=2 if var.FlagOutDated==2 else 1
        elif flagOutDated==-1:
            sOut=f'The version of the current instance of {packageName} ({currentVersion}) is newer than the latest official releas ({latestVersion})!\nYou should contact Tommaso and Gerardo if you are a developer and some relevant change is made by yourself!\nIf you are a user, enjoy this beta version and please report any issue!'
            var.FlagOutDated=-2 if var.FlagOutDated==-2 else -1
        elif flagOutDated==-1000:
            sOut=f'Error from pip: it was not possible to check for a new version of the {packageName} package!'
            var.FlagOutDated=-1000
        else:
            sOut=f'{packageName} The current version ({currentVersion}) of {packageName} is up-to-date! Enjoy it!'
            var.FlagOutDated=0
        pri.Info.cyan(f'[{var.FlagOutDated}] '+sOut)
        self.signals.printOutDated.emit()
        #self.ui.button_PaIRS_download.setVisible(flagOutDated>0)
        pass

    checkOutDated(packageName,printOutDated)
    return flagStopAndDownload

def warningLatestVersion(self,app,flagExit=0,flagWarning=0,time_milliseconds=0,FlagStayOnTop=False):
    if not flagExit: 
        exitSuggestion=f'exit the current instance of {self.name} and '
    else: 
        exitSuggestion='' 
    py=myStandardRoot(sys.executable).split('/')[-1].split('.')[0]
    command=f'{py} -m pip install --upgrade PaIRS_UniNa'
    if self.TABpar.FlagOutDated>0:
        if Flag_ISEXE:
            Message=f'A new version of the PaIRS_UniNa package is available (current: {self.TABpar.currentVersion}, latest: {self.TABpar.latestVersion}).\nPlease, download it from the following link:\n{EXEurl}'
        else:
            Message=f'A new version of the PaIRS_UniNa package is available (current: {self.TABpar.currentVersion}, latest: {self.TABpar.latestVersion}).\nPlease, {exitSuggestion}install it with the following command:\n{command}'
    elif self.TABpar.FlagOutDated==-1000:
        Message = ("Unable to check for the latest official release of PaIRS_UniNa. Please check the PyPI page manually for updates:\n""https://pypi.org/project/PaIRS-UniNa/")
    else:
        Message=f'The version of the current instance of PaIRS_UniNa ({self.TABpar.currentVersion}) is newer than the latest official releas ({self.TABpar.latestVersion})!\nYou should contact Tommaso and Gerardo if you are a developer and some relevant change is made by yourself!\nIf you are a user, enjoy this beta version and please report any issue!'
    if flagExit:
        print(f"\n{'*'*100}\n"+Message+f"\n{'*'*100}\n")
    if flagWarning:
        warningDialog(self,Message,time_milliseconds=time_milliseconds,flagScreenCenter=True,pixmap=''+ icons_path +'flaticon_PaIRS_download.png' if self.TABpar.FlagOutDated>0 else ''+ icons_path +'flaticon_PaIRS_download_warning.png' if self.TABpar.FlagOutDated==-1000 else ''+ icons_path +'flaticon_PaIRS_beta.png',FlagStayOnTop=FlagStayOnTop,addButton={"Go to the download page!": lambda: QDesktopServices.openUrl(QUrl(EXEurl))} if Flag_ISEXE else {"See what's new!": lambda: QDesktopServices.openUrl(QUrl("https://pypi.org/project/PaIRS-UniNa/"))} if self.TABpar.FlagOutDated>0 else {})    

def downloadLatestVersion(self,app):
    try:
        print(f'{"*"*20}   Upgrading PaIRS_UniNa   {"*"*20}')
        splash=showSplash(filename=''+ icons_path +'logo_PaIRS_download.png')
        app.processEvents()
        reqs=subprocess.run([sys.executable, '-m', 'pip', 'install','--upgrade','PaIRS_UniNa'],capture_output=True)
        print(reqs.stderr.decode("utf-8"))
        print(reqs.stdout.decode("utf-8"))
        print(f'{"*"*20}   PaIRS_UniNa upgraded   {"*"*20}')
        #reqs=subprocess.run([sys.executable, '-m', 'pip', 'install','PaIRS_UniNa'],capture_output=True)
        #print(reqs.stderr.decode("utf-8"))
        #print(reqs.stdout.decode("utf-8"))
        splash.hide()    
    except Exception as inst:
        print(inst)
        try:
            warningDialog(self,f'The following error occured while downloading the latest version of the PaIRS_UniNa package from https://pypi.org:\n{inst}.\n\nPlease, try by yourself with the following command:\nnpython -m pip install --upgrade PaIRS_UniNa')
        except Exception as inst:
            print(inst)

def button_download_PaIRS_action(self,app):
    warningLatestVersion(self,app,flagExit=0,flagWarning=1)
    checkLatestVersion(self,__version__,self.app,splash=None,flagWarning=0)
    return
    flagStopAndDownload=questionDialog(self,f'A new version of the PaIRS_UniNa package is available. Do you want to close the current instance of {self.name} and download it?')
    if not flagStopAndDownload: return
    self.TABpar.FlagOutDated=0
    self.close()
    downloadLatestVersion(self,app)
    print(f'{"*"*20}   Relaunching PaIRS   {"*"*20}')
    if self.name=='CalVi': command='-calvi'
    else: command=''
    subprocess.call(sys.executable+' -m PaIRS_UniNa '+command,shell=True)
    #runPaIRS(self,flagQuestion=False)
    
import urllib.request, json, ssl

def get_package_version_urllib(package_name):
    """Get package version using only standard library"""
    try:
        import certifi
        url = f"https://pypi.org/pypi/{package_name}/json"
        context = ssl.create_default_context(cafile=certifi.where())
        with urllib.request.urlopen(url, context=context, timeout=10) as response:
            data = json.loads(response.read().decode())
            return True, data['info']['version']
    except Exception as e:
        return False, f"Error: {e}"

def checkOutDated(packageName:str,printOutDated):
  ''' 
  Check if a package is out dated works asynchronously.
  call with 
  checkOutDated('PaIRS_UniNa',printOutDated)
  Input 
  packageName   the name of the package 
  fun a function that is called when ready and in input will receive a bool (True if outdated and a string that explain to the user what to do)
  def printOutDated(flagOutDated,sOut):
    if flagOutDated==1:
      print (sOut)
    elseif flagOutDated=-1:
      print ('Error from pip ')
    else:
      pass #in this case the last version of the package is installed
  '''
  async def checkOutDatedInternal(packageName):
    #reqs = subprocess.check_output([sys.executable, '-m', 'pip', 'list','--outdated'])
    #reqs = subprocess.run([sys.executable, '-m', 'pip', 'list','--outdated'],capture_output=True)
    #reqs = subprocess.check_output([sys.executable, '-m', 'pip', 'index','versions','PaIRS_UniNa'])
    #reqs = subprocess.check_output([sys.executable, '-m', 'pip', 'install','PaIRS_UniNa=='])

    """"
    reqs = subprocess.run([sys.executable, '-m', 'pip', 'list','--outdated'],capture_output=True)
    outDated = [r.decode().split('==')[0] for r in reqs.stdout.split()]
    """
    flagOutDated=-1000
    currentVersion='none'
    latestVersion=''
    try:
        if Flag_ISEXE:
            currentVersion=__version__+'.'+__subversion__ if int(__subversion__) else __version__
        else:
            if Flag_DEBUG:
                currentVersion=__version__+'.'+__subversion__ if int(__subversion__) else __version__
            else:
                command=[sys.executable, '-m', 'pip', 'show', packageName]
                reqs = subprocess.run(command,capture_output=True)
                if reqs.returncode:
                    pri.Error.red('Error in command:\n'+' '.join(command)+'\n'+reqs.stderr.decode("utf-8") )
                    return flagOutDated,currentVersion,latestVersion  
                printing=reqs.stdout.decode("utf-8") 
                pri.Info.cyan( printing )
                r=reqs.stdout.decode("utf-8").replace('\r','').split('\n')
                currentVersion='none'
                for s in r:
                    if 'Version: ' in s:
                        currentVersion=s.replace('Version: ','')
                        break
        if currentVersion!=__version__:
            message=f'Greetings, developer!\nThe version of the current instance of PaIRS_UniNa ({__version__}) is different from that installed in the present Python environment ({currentVersion})!\nYou should contact Tommaso and Gerardo if some relevant change is made by yourself!'
            pri.Info.yellow(f'{"-"*50}\n{message}\n{"-"*50}\n')
        if Flag_ISEXE:
             _, latestVersion = get_package_version_urllib("PaIRS_UniNa")
        else:
            command=[sys.executable, '-m', 'pip', 'index', 'versions', packageName]
            reqs = subprocess.run(command,capture_output=True)
            if not reqs.returncode:
                printing=reqs.stdout.decode("utf-8") 
                pri.Info.cyan( printing )
                r=reqs.stdout.decode("utf-8").replace('\r','').split('\n')
                #currentVersion=r[0].replace(packageName,'').replace('(','').replace(')','').replace(' ','')
                latestVersion=r[1].replace('Available versions: ','').split(',')[0]
            else:
                flagOk,latestVersion=get_package_version_urllib(packageName)
                if not flagOk:
                    pri.Error.red('Error in command:\n'+' '.join(command)+'\n'+reqs.stderr.decode("utf-8") )
                    pri.Error.red(latestVersion)
                    latestVersion='none'
                
                """
                command=[sys.executable, '-m', 'pip', 'list','--outdated']
                reqs = subprocess.run(command,capture_output=True)
                if reqs.returncode:
                    pri.Error.red('Error in command:\n'+' '.join(command)+'\n'+reqs.stderr.decode("utf-8") )
                    return flagOutDated,currentVersion,latestVersion  
                outDated = [r.decode().split('==')[0] for r in reqs.stdout.split()]
                if packageName in outDated:
                    i=outDated.index(packageName)
                    latestVersion=outDated[i+2]
                else:
                    latestVersion=currentVersion
                pri.Info.cyan(f'{packageName} ({currentVersion}). Latest version available: {latestVersion}')
                """
        #flagOutDated=1 if currentVersion!=latestVersion else 0
        cV_parts=[int(c) for c in currentVersion.split('.')]
        lV_parts=[int(c) for c in latestVersion.split('.')]
        flagOutDated=1 if (cV_parts[0] < lV_parts[0] or 
            cV_parts[1] < lV_parts[1] or 
            cV_parts[2] < lV_parts[2]) \
            else -1 if (cV_parts[0] > lV_parts[0] or
            cV_parts[1] > lV_parts[1] or 
            cV_parts[2] > lV_parts[2] ) \
            or (cV_parts[0] == lV_parts[0] and
            cV_parts[1] == lV_parts[1] and
            cV_parts[2] == lV_parts[2] and len(cV_parts)>len(lV_parts)) \
            else 0
    except Exception as inst:
        pri.Error.red(inst)
    return flagOutDated,currentVersion,latestVersion
  def checkOutDatedComplete(_f3):
    flagOutDated,currentVersion,latestVersion=_f3.result()
    printOutDated (flagOutDated,currentVersion,latestVersion)
  executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
  f3=executor.submit(asyncio.run,checkOutDatedInternal(packageName))
  f3.add_done_callback(checkOutDatedComplete)

def changes(self,TabType,filename,title=" Changes"):
    FlagShow=False
    if self.logChanges:
        if self.logChanges.isVisible():
            FlagShow=True
    if FlagShow:
        self.logChanges.hide()
        self.logChanges.show()
    else:
        self.logChanges=TabType(self,True)
        self.logChanges.resize(720,720)
        self.logChanges.show()
        self.logChanges.ui.progress_Proc.hide()
        self.logChanges.ui.button_close_tab.hide()
        icon=QPixmap(''+ icons_path +'news.png')
        self.logChanges.ui.icon.setPixmap(icon)
        self.logChanges.setWindowIcon(self.windowIcon())
        self.logChanges.setWindowTitle(title)
        self.logChanges.ui.name_tab.setText(title)
    
        self.logChanges.ui.log.setLineWrapColumnOrWidth(self.logChanges.ui.log.width()-20)
        self.logChanges.ui.log.setStyleSheet("")

        def setFontPixelSize(logChanges:type(self.logChanges),fPixSize):
            logfont=self.font()
            logfont.setFamily(fontName)
            logfont.setPixelSize(fPixSize+2)
            logChanges.ui.log.setFont(logfont)
            fPixSize_TabNames=min([fPixSize*2,30])
            lab=logChanges.ui.name_tab
            font=lab.font()
            font.setPixelSize(fPixSize_TabNames)
            lab.setFont(font)
        self.logChanges.setFontPixelSize=lambda fS: setFontPixelSize(self.logChanges,fS)
        self.logChanges.setFontPixelSize(self.TABpar.fontPixelSize)
        def logResizeEvent(logChanges:type(self.logChanges),e):
            super(type(logChanges),logChanges).resizeEvent(e) 
            logChanges.ui.log.setLineWrapColumnOrWidth(logChanges.ui.log.width()-20)
        self.logChanges.ui.log.resizeEvent=lambda e: logResizeEvent(self.logChanges,e)

        self.logChanges.ui.icon.addfuncclick['whatsnew']=self.whatsNew
        self.logChanges.ui.icon.setCustomCursor()

        try:
            file = open(filename, "rb")
            content = file.read().decode("utf-8")
            self.logChanges.ui.log.setText(content)
            file.close()
        except Exception as inst:
            pri.Error.red(f'There was a problem while reading the file {filename}:\n{inst}')
            self.logChanges.ui.log.setText(f'No information about PaIRS-UniNa updates available!\n\nSorry for this, try to reinstall PaIRS-UniNa or alternatively contact the authors at {__mail__}.')
    return

import webbrowser
def downloadExampleData(self,url):
    Message=f'Test data are available at the following link:\n{url}'
    warningDialog(self,Message,pixmap=''+ icons_path +'flaticon_PaIRS_download.png',title='Download test data',addButton={'Download data!':lambda:webbrowser.open(url)})

def optimalPivCores(totCore,nImgs,penCore=1):
    ''' Used to determine the optimal number of pivCores as a function of the total number of cores and the number of imag to be processed
    totCore is the total number of cores that can be used
    nImgs is the number of images
    penCore is a penalization for the internal parallelization of the PIV process if = to 1 the parallelization it is assumed to be perfect
        Most probably a value of 0.95-1 should work correctly 
        with 0.95 adding the xth pivCore is counted as: x=10->0.63 20->0.38 40->0.14 80->0.017
        with 0.98 adding the xth pivCore is counted as: x=10->0.83 20->0.68 40->0.45 80->0.20
    Output
    nPivMax the number of pivCores to be used 
    nCoreMax  the number of multiProces to be used 
    '''
    pen=1     #initially the penalization is zero
    procPower=1  # the processing power of piv is not directly proportional to the numbers of cores
    nCorePerImgMax=0
    nPivMax=0
    for nPiv in range(1,totCore+1):
        nProc=floor(totCore/nPiv)
        nCicli=ceil(nImgs/nProc)
        nCorePerImg=procPower/nCicli
        #♥print(nPiv,nProc,pen,procPower,nCorePerImg,nCicli)
        if nCorePerImg>nCorePerImgMax:
            nCorePerImgMax=nCorePerImg
            nPivMax=nPiv
        pen*=penCore
        procPower+=pen
    nCoreMax=floor(totCore/nPivMax)
    #nPivMax=floor(totCore/nCoreMax)
    return nPivMax,nCoreMax

from PySide6.QtCore import qInstallMessageHandler, QtMsgType
def custom_qt_message_handler(mode, context, message):
    if ("QPainter" in message or "paintEngine" in message):
        return  #Silenzia questi messaggi
    print(message)  #Altrimenti stampali normalmente (oppure loggali)
qInstallMessageHandler(custom_qt_message_handler)

"""
def custom_qt_message_handler(mode, context, message):
    if "QPainter" in message or "paintEngine" in message:
        print("\n!!! Intercepted Qt message:")
        print(message)
        print("\n*** Current Python stacktrace:")
        traceback.print_stack()  # Questo stampa lo stack in cui è stato generato il messaggio
    else:
        print(message)
qInstallMessageHandler(custom_qt_message_handler)
import functools
import traceback
def log_qpainter_usage(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"\n°°° Execution of {func.__name__} in {func.__module__}")
        traceback.print_stack(limit=4)  # Mostra solo lo stack alto
        return func(*args, **kwargs)
    return wrapper
"""

class PaIRSApp(QApplication):
    def __init__(self,*args):
        super().__init__(*args)
        self.installMessageHandler()
        self.setStyle('Fusion')

    def applicationSupportsSecureRestorableState(self):
        return True
    
    def message_handler(self, mode, context, message):
        if "QBasicTimer::start" not in message and "QObject::startTimer" not in message:
            print(message)

    def installMessageHandler(self):
        qInstallMessageHandler(self.message_handler)
    
rqrdpckgs_filename=foldPaIRS+"rqrdpckgs.txt"
from packaging.version import Version
import importlib.metadata

def resetRequiredPackagesFile(filename=rqrdpckgs_filename):
    # Leggi il contenuto esistente
    try:
        with open(filename, "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        pri.Error.red(f"resetRequiredPackagesFile: File {filename} not found.")
        return

    with open(filename, "w") as f:
        for line in lines:
            parts = line.strip().split()
            if len(parts) >= 3:
                pkg = parts[0]
                vmin = parts[1]
                vmax = parts[2]
                f.write(f"{pkg}\t{vmin}\t{vmax}\t0\n")
            else:
                pri.Error.red(f"resetRequiredPackagesFile: Skipping malformed line: {line}")

def to_triplet(v: Version) -> tuple[int,int,int]:
    r = v.release or (0,)
    return (r[0], r[1] if len(r) > 1 else 0, r[2] if len(r) > 2 else 0)

def le_ver(a: Version, b: Version) -> bool:
    a1,a2,a3 = to_triplet(a)
    b1,b2,b3 = to_triplet(b)
    if a1 > b1: return False
    if a1 < b1: return True
    if a2 > b2: return False
    if a2 < b2: return True
    return a3 <= b3

def checkRequiredPackages(self, filename=rqrdpckgs_filename, FlagDisplay=False, FlagForcePrint=False):
    required_packages = []
    vmin_list = []
    vmax_list = []
    vcurr_list = []

    # Read file
    with open(filename, "r") as f:
        for line in f:
            #pri.Info.white(line)
            parts = line.strip().split()
            if len(parts) >= 4:
                required_packages.append(parts[0])
                vmin_list.append(Version(parts[1]))
                vmax_list.append(Version(parts[2]))
                vcurr_list.append(Version(parts[3]) if parts[3] != "0" else None)
            else:
                pri.Error.red(f"Malformed line: {line}")

    Flag = False
    warnings = []

    for i, pkg in enumerate(required_packages):
        try:
            installed_version = Version(importlib.metadata.version(pkg))
        except importlib.metadata.PackageNotFoundError:
            installed_version = None

        # Update current installed version
        if installed_version is not None and (installed_version != vcurr_list[i] or FlagDisplay):
            vcurr_list[i] = installed_version
            Flag = True

            # Check if within [vmin, vmax]
            if not (le_ver(vmin_list[i],installed_version) and le_ver(installed_version,vmax_list[i])):
                """
                warnings.append(
                    f"- {pkg}: installed = {installed_version}, target range = [{vmin_list[i]}, {vmax_list[i]}]"
                )
                """
                warnings.append(
                    f"- {pkg}  {installed_version}  not in [{vmin_list[i]}, {vmax_list[i]}]"
                )

    # Show warning
    if len(warnings)>0: self.FlagPackIssue=True
    if len(warnings)>0 or FlagForcePrint:
        message = (
            "Some installed packages have a version outside the target range used to develop "
            "the current release of the PaIRS_UniNa package.\n\n"
            "This may lead to compatibility issues. If you experience unexpected behavior, "
            "it is recommended to either reinstall the last tested compatible versions or "
            f"download the executable at {EXEurl}."
            f" If any issue occurs, please contact the authors at {__mail__}.\n\n"
            #"or use the standalone executable available at:\n"
            #"https://pairs.unina.it/#download\n\n"
            "Incompatible packages:\n"
            + "\n".join(warnings) +
            "\n\nYou may reinstall the last compatible versions using the following commands:\n\n"
        )
        for i, pkg in enumerate(required_packages):
            if vcurr_list[i] is not None and (not (vmin_list[i] <= vcurr_list[i] <= vmax_list[i]) or FlagForcePrint):
                message += (
                    f"python -m pip uninstall {pkg}\n"
                    f"python -m pip install {pkg}=={vmax_list[i]}\n"
                )

        warningDialog(
            self,
            Message=message,
            flagScreenCenter=True,
            pixmap=icons_path + 'python_warning.png',
            pixmapSize=96
        )
    elif FlagDisplay:
        warningDialog(self, Message="All installed packages are within the expected version range.", flagScreenCenter=True,pixmap=icons_path+'greenv.png')

    # Update file if needed
    if Flag:
        with open(filename, "w") as f:
            for pkg, vmin, vmax, vcurr in zip(required_packages, vmin_list, vmax_list, vcurr_list):
                f.write(f"{pkg}\t{vmin}\t{vmax}\t{vcurr if vcurr else 0}\n")

    return required_packages, vmin_list, vmax_list, vcurr_list
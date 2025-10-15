from .gPaIRS import *

def run():
    gui:gPaIRS
    app,gui,flagPrint=launchPaIRS()
    quitPaIRS(app,flagPrint)

def cleanRun():
    if os.path.exists(lastcfgname):
        os.remove(lastcfgname)
    run()
   
def debugRun():
    gui:gPaIRS
    app,gui,flagPrint=launchPaIRS(flagInputDebug=True)
    quitPaIRS(app,flagPrint)



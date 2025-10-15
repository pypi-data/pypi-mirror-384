from .ui_Log_Tab import*
from .TabTools import*
from .__init__ import __version__,__year__

class LOGpar(TABpar):
    def __init__(self,Process=ProcessTypes.null,Step=StepTypes.null):
        self.setup(Process,Step)
        super().__init__('LOGpar','Log')

    def setup(self,Process,Step):
        self.Process = Process
        self.Step = Step
        self.text=logHeader('Welcome to PaIRS!\nEnjoy it!\n\n')
        self.progress=0
        self.nimg=0
        return
    
class Log_Tab(gPaIRS_Tab):
    class Log_Tab_Signals(gPaIRS_Tab.Tab_Signals):
        pass

    def __init__(self,parent: QWidget =None, flagInit= __name__ == "__main__"):
        super().__init__(parent,Ui_LogTab,LOGpar)
        self.signals=self.Log_Tab_Signals(self)

        #------------------------------------- Graphical interface: widgets
        self.TABname='Log'
        self.setLogFont(fontPixelSize-dfontLog)
             
        #necessary to change the name and the order of the items
        for g in list(globals()):
            if '_items' in g or '_ord' in g or '_tips' in g:
                #pri.Info.blue(f'Adding {g} to {self.name_tab}')
                setattr(self,g,eval(g))

        #------------------------------------- Declaration of parameters 
        self.LOGpar_base=LOGpar()
        self.LOGpar:LOGpar=self.TABpar
        self.LOGpar_old:LOGpar=self.TABpar_old

        #------------------------------------- Callbacks
        self.adjustTABpar=lambda: None
        self.setTABlayout=self.setLOGlayout

        self.setupWid()  #---------------- IMPORTANT
        self.FlagDisplayControls=False

        #------------------------------------- Initializing  
        if flagInit:   
            self.initialize()

    def initialize(self):
        self.setTABpar(FlagBridge=False)

    def setLOGlayout(self):
        self.setLogText()
        self.setProgressProc()

    def setLogText(self,FlagMoveToBottom=False):
        text=self.ui.log.toPlainText()
        new_text=self.LOGpar.text
        if new_text[:len(text)]==text:
            new_text=new_text[len(text):]
        else:
            self.logClear()
        self.logWrite(new_text)
        if FlagMoveToBottom: self.moveToBottom()

    def setProgressProc(self):
        self.ui.progress_Proc.setVisible(self.LOGpar.progress>0)
        self.ui.progress_Proc.setMaximum(self.LOGpar.nimg)
        self.ui.progress_Proc.setValue(self.LOGpar.progress)          

    def setLogFont(self,fPixSize):
        self.ui: Ui_LogTab   
        logfont=self.font()
        logfont.setFamily('Courier New')
        logfont.setPixelSize(fPixSize)
        self.ui.log.setFont(logfont)
    
    def logWrite(self, text):
        cursor = self.ui.log.textCursor() 
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.ui.log.setTextCursor(cursor)
        self.ui.log.ensureCursorVisible()

    def logClear(self):
        self.ui.log.setText('')

    def moveToTop(self):
        self.ui.log.verticalScrollBar().setValue(self.ui.log.verticalScrollBar().minimum())

    def moveToBottom(self):
        self.ui.log.verticalScrollBar().setValue(self.ui.log.verticalScrollBar().maximum())

def logHeader(message):
    header=PaIRS_Header+message
    return header

if __name__ == "__main__":
    import sys
    app=QApplication.instance()
    if not app:app = QApplication(sys.argv)
    app.setStyle('Fusion')
    object = Log_Tab(None)
    object.show()
    app.exec()
    app.quit()
    app=None

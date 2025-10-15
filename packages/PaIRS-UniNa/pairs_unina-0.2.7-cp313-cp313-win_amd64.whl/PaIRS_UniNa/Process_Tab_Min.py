from .ui_Process_Tab_Min import*
from .TabTools import*

LaserTypeSearch_items=[ 'single laser', #0
                        'double laser', #1
                        ]
LaserTypeSearch_order=[i for i in range(len(LaserTypeSearch_items))] #************ change here, please!

spin_tips={
    'SogliaNoise'       :   'Minimum allowed value for validation',
    'SogliaStd'         :   'Minimum allowed st.d. value for validation',
}
check_tips={}
radio_tips={
    'TR': 'Time-resolved sequence',    
}
line_edit_tips={}
button_tips={}
combo_tips={
    'LaserType': 'Laser setup',
}

class PROpar_Min(TABpar):
    def __init__(self,Process=ProcessTypes.null,Step=StepTypes.null):
        self.setup(Process,Step)
        super().__init__('PROpar_Min','Process_Min')
        self.unchecked_fields+=[]

    def setup(self,Process,Step):
        self.Process        = Process
        self.Step           = Step

        self.FlagTR      = False
        self.LaserType   = 0   #0 single, 1 double
        self.SogliaNoise = 5.0
        self.SogliaStd   = 1.5

class Process_Tab_Min(gPaIRS_Tab):
    class Process_Tab_Signals(gPaIRS_Tab.Tab_Signals):
        pass

    def __init__(self,parent: QWidget =None, flagInit= __name__ == "__main__"):
        super().__init__(parent,Ui_ProcessTab_Min,PROpar_Min)
        self.signals=self.Process_Tab_Signals(self)
    
        #------------------------------------- Graphical interface: widgets
        self.TABname='Process_Min'
        self.ui: Ui_ProcessTab_Min

        #necessary to change the name and the order of the items
        for g in list(globals()):
            if '_items' in g or '_ord' in g or '_tips' in g:
                #pri.Info.blue(f'Adding {g} to {self.name_tab}')
                setattr(self,g,eval(g))
        
        if __name__ == "__main__": 
            self.app=app
            setAppGuiPalette(self)

        self.pixmap_laser_NTR=QPixmap(icons_path+'laser_NTR.png')
        self.pixmap_laser_TR_single=QPixmap(icons_path+'laser_TR_single.png')
        self.pixmap_laser_TR_double=QPixmap(icons_path+'laser_TR_double.png')    

        #------------------------------------- Declaration of parameters 
        self.PROpar_base=PROpar_Min()
        self.PROpar:PROpar_Min=self.TABpar
        self.PROpar_old:PROpar_Min=self.TABpar_old

        #------------------------------------- Callbacks 
        self.defineWidgets()
        self.setupWid()  #---------------- IMPORTANT

        self.defineCallbacks()
        self.connectCallbacks()

        self.defineSettings()
        
        self.adjustTABpar=self.adjustPROpar
        self.setTABlayout=self.setPROlayout

        #------------------------------------- Initializing    
        if flagInit:     
            self.initialize()


    def initialize(self):
        pri.Info.yellow(f'{"*"*20}   PROCESS Min initialization   {"*"*20}')
        self.setTABpar(FlagAdjustPar=True,FlagBridge=False)
        self.add_TABpar('initialization')
        self.setFocus()

#*************************************************** Adjusting parameters
    def adjustPROpar(self):
        if not self.PROpar.FlagTR: self.PROpar.LaserType=1
        
        
#*************************************************** Layout
    def setPROlayout(self):
        #pri.Time.blue(1,'setPROpar: Beginning')
        self.ui.w_LaserType.setEnabled(self.PROpar.FlagTR)

        if not self.PROpar.FlagTR:
            self.ui.example_label.setPixmap(self.pixmap_laser_NTR)
        else:
            if self.PROpar.LaserType==0:
                self.ui.example_label.setPixmap(self.pixmap_laser_TR_single)
            elif self.PROpar.LaserType==1:
                self.ui.example_label.setPixmap(self.pixmap_laser_TR_double)


if __name__ == "__main__":
    import sys
    app=QApplication.instance()
    if not app:app = QApplication(sys.argv)
    app.setStyle('Fusion')
    object = Process_Tab_Min(None)
    object.show()
    app.exec()
    app.quit()
    app=None

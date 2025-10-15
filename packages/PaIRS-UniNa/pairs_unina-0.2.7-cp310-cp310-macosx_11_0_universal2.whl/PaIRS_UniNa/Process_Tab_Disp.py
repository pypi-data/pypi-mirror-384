from .ui_Process_Tab_Disp import*
from .TabTools import*
from .Process_Tab import Process_Tab

spin_tips={
    'Nit'                : 'Number of iterations',
    'order'              : 'Kernel width for image interpolation',
    'SemiWidth_Epipolar' : 'Semi-width normal to epipolar line',
    'Filter_SemiWidth'   : 'Semi-width of filter',
    'Threshold'          : 'Threshold for disparity computation',
    'Nit_OutDet'         : 'Number of iterations for outlier detection',
    'Std_Threshold'      : 'S.t.d. threshold for disparity validation',
}
check_tips={}
radio_tips={}
line_edit_tips={
    'IW'    :   'IW sizes and/or spacings',
}
button_tips={
    'tool_CollapBox_FinIt'      :  'Graphics',
    'CollapBox_FinIt'           :  'Graphics',
    'tool_CollapBox_Interp'     :  'Graphics',
    'CollapBox_Interp'          :  'Graphics',
    'tool_CollapBox_Interp_2'   :  'Graphics',
    'CollapBox_Interp_2'        :  'Graphics', 
}
combo_tips={
    'ImInt'             :   'Image interpolation',
    'par_pol'           :   'Polynomial interpolation',      
    'par_imshift'       :   'Moving window',       
    'frames'            :   'Use frame 1/2',         
}

class PROpar_Disp(TABpar):
    def __init__(self,Process=ProcessTypes.null,Step=StepTypes.null):
        self.setup(Process,Step)
        super().__init__('PROpar_Disp','PROCESS_Tab_Disp')
        self.unchecked_fields+=[]

    def setup(self,Process,Step):
        self.Process        = Process
        self.Step           = Step

        self.Nit     = 5
        self.frames  = 1
        self.IntIniz = 57
        self.IntIniz_ind_list = [3,1,2]
        self.Vect =[256,128,256,128]

        self.SemiWidth_Epipolar = 40
        self.Filter_SemiWidth   = 10
        self.Threshold          = 0.5

        self.Nit_OutDet    = 5
        self.Std_Threshold = 3.0

class Process_Tab_Disp(gPaIRS_Tab):
    class Process_Tab_Signals(gPaIRS_Tab.Tab_Signals):
        pass

    def __init__(self,parent: QWidget =None, flagInit= __name__ == "__main__"):
        pri.Time.yellow('Process Disp: init')
        super().__init__(parent,Ui_ProcessTab_Disp,PROpar_Disp)
        self.signals=self.Process_Tab_Signals(self)
        pri.Time.yellow('Process Disp: ui')

        #------------------------------------- Graphical interface: widgets
        self.TABname='Process_Disp'
        self.ui: Ui_ProcessTab_Disp

        #necessary to change the name and the order of the items
        for g in list(globals()):
            if '_items' in g or '_ord' in g or '_tips' in g:
                #pri.Info.blue(f'Adding {g} to {self.name_tab}')
                setattr(self,g,eval(g))

        pri.Time.yellow('Process Disp: globals')
        
        if __name__ == "__main__": 
            self.app=app
            setAppGuiPalette(self)

        pri.Time.yellow('Process Disp: setupWid')

        #------------------------------------- Declaration of parameters 
        self.PROpar_base=PROpar_Disp()
        self.PROpar:PROpar_Disp=self.TABpar
        self.PROpar_old:PROpar_Disp=self.TABpar_old

        pri.Time.yellow('Process Disp: par')

        #------------------------------------- Callbacks 
        self.defineWidgets()
        self.setupWid()  #---------------- IMPORTANT

        Process_Tab.defineInterpActions(self)
        self.defineCallbacks()
        self.connectCallbacks()
        
        Process_Tab.defineInterpSet(self)
        self.defineSettings()
        
        self.adjustTABpar=self.adjustPROpar
        self.setTABlayout=self.setPROlayout

        pri.Time.yellow('Process Disp: define callbacks')

        #------------------------------------- Initializing    
        if flagInit:     
            self.initialize()

    def initialize(self):
        pri.Info.yellow(f'{"*"*20}   PROCESS Disp initialization   {"*"*20}')
        self.setTABpar(FlagAdjustPar=True,FlagBridge=False)
        self.add_TABpar('initialization')
        self.setFocus()

#*************************************************** Adjusting parameters
    def adjustPROpar(self):
       minIWSize=min([self.PROpar.Vect[0],self.PROpar.Vect[2]])
       self.PROpar.SemiWidth_Epipolar=min([self.PROpar.SemiWidth_Epipolar, int(minIWSize/4)])
       self.PROpar.Filter_SemiWidth=min([self.PROpar.Filter_SemiWidth, int(minIWSize/4)])
       self.ui.spin_SemiWidth_Epipolar.setMaximum(int(minIWSize/4))
       self.ui.spin_Filter_SemiWidth.setMaximum(int(minIWSize/4))
       return
              
#*************************************************** Layout
    def setPROlayout(self):
        self.ui.w_Std_Threshold.setVisible(self.PROpar.Nit_OutDet>0)
        return
       
#*************************************************** Windowing and Correlation
#******************** Actions
    def line_edit_IW_action(self):
        text=self.ui.line_edit_IW.text()
        split_text=re.split(r'(\d+)', text)[1:-1:2]
        split_num=[int(t) for t in split_text]
        if len(split_num)<4: split_num+=[split_num[-1]]*(4-len(split_num))
        vect=[int(split_num[i]) for i in (0,2,1,3)]
        FlagValid=len(vect)==4 and all([v>0 for v in vect])
        if FlagValid:
            self.PROpar.Vect=vect
        else:
            message='IW sizes or spacings were assigned inconsistently! Please, retry!'
            showTip(self,message)
        return

#******************** Settings
    def line_edit_IW_set(self):
        vect=[f'{self.PROpar.Vect[i]}' for i in (0,2,1,3)]
        vectStr=', '.join(vect)
        self.ui.line_edit_IW.setText(vectStr)

if __name__ == "__main__":
    import sys
    app=QApplication.instance()
    if not app:app = QApplication(sys.argv)
    app.setStyle('Fusion')
    object = Process_Tab_Disp(None)
    object.show()
    app.exec()
    app.quit()
    app=None

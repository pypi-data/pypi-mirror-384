from .ui_Process_Tab_CalVi import*
from .TabTools import*

DotColor_labels=['Black dot', #0
                'White dot',  #1
                ]

DotTypeSearch_items=['cross-correlation mask',        #0
                     'top hat mask with tight tails', #1
                     'top hat mask with broad tails', #2
                     'Gaussian mask',                 #3
                     'interpolation',                 #4
                     'centroid',                      #5
                        ]
DotTypeSearch_order=[i for i in range(len(DotTypeSearch_items))] #************ change here, please!

TargetType_items=['single plane', #0
                  'double plane', #1
                    ]
TargetType_order=[i for i in range(len(TargetType_items))] #************ change here, please!

CamMod_items=['polynomial',         #0
              'rational',           #1
              'tri-polynomial',     #2
              'pinhole',            #3
              'pinhole + cylinder', #4
                ]
CamMod_order=[i for i in range(len(CamMod_items))] #************ change here, please!

CorrMod_items=['a: no correction',              #0
               'b: radial distortions',         #1
               'c: b + tangential distortions', #2
               'd: c + cylinder origin',        #3
               'e: d + cylinder rotation',      #4
               'f: e + cylinder radius and thickness', #5
               'g: f + refractive index ratio', #6
                ]
CorrMod_order=[i for i in range(len(CorrMod_items))] #************ change here, please!

CalibProcType_items=['standard',                #0
                     'unknown planes',          #1
                     'equation of the plane',   #2
                     'cylinder',                #3
                     ]
CalibProcType_order=[i for i in range(len(CalibProcType_items))] #************ change here, please!

CorrMod_Cyl_items=[ 'a: cylinder origin and rotation',      #0
                    'b: a + cylinder thickness',            #1
                    'c: b + refractive index (n) ratio',    #2
                    'd: b + internal radius',               #3
                    'e: a + internal radius and n ratio',   #4
                    'f: all cylinder parameters',           #5
                    ]
CorrMod_Cyl_order=[i for i in range(len(CorrMod_Cyl_items))] #************ change here, please!



spin_tips={
        'DotThresh'     :  'Threshold on maximum/minimum value for search of control points',
        'DotDiam'       :  'Dot diameter in pixels (search radius is 2.5 times this value)',
        'DotDx'         :  'Spacing of dots along x on each level of the target',
        'DotDy'         :  'Spacing of dots along y on each level of the target',
        'OriginXShift'  :  'Shift of the origin along x on the second level of the target',
        'OriginYShift'  :  'Shift of the origin along y on the second level of the target',
        'OriginZShift'  :  'Shift of the origin along z on the second level of the target',
        'XDeg'          :  'Degree of polynomial along x',
        'YDeg'          :  'Degree of polynomial along y',
        'ZDeg'          :  'Degree of polynomial along z',
        'PixAR'         :  'Pixel aspect ratio (y/x)',
        'PixPitch'      :  'Pixel pitch in millimeter units',
        'CylRad'        :  'Initial value for cylinder internal radius in mm',
        'CylThick'      :  'Initial value for cylinder wall thickness in mm',
        'CylNRatio'     :  'Refractive index ratio (fluid/solid wall)',
}
check_tips={
        'Plane'     :   'Optimize the plane constants',
        'Pinhole'   :   'Optimize the pinhole parameters',
        'SaveLOS'   :   'Save physical coordinates of the intersections of the lines of sight with the cylinder',
}
radio_tips={}
line_edit_tips={}
button_tips={
        'DotColor'              :  'White/black dot in the image',
        'tool_CollapBox_Target' :  'Graphics',
        'CollapBox_Target'      :  'Graphics',
        'tool_CollapBox_CalPar' :  'Graphics',
        'CollapBox_CalPar'      :  'Graphics',
}
combo_tips={
        'DotTypeSearch' :  'Type of search for control points',
        'TargetType'    :  'Type of target (single or double plane)',
        'CalibProcType' :  'Type of calibration procedure',
        'CamMod'        :  'Type of mapping function',
        'CorrMod'       :  'Parameters of the correction to be optimized',
        'CorrMod_Cyl'   :  'Cylinder parameters of the correction to be optimized',
}

class PROpar_CalVi(TABpar):
    def __init__(self,Process=ProcessTypes.null,Step=StepTypes.null):
        self.setup(Process,Step)
        super().__init__('PROpar_CalVi','Process_CalVi')
        self.unchecked_fields+=['FlagTarget_reset','FlagCalib_reset']

    def setup(self,Process,Step):
        self.Process        = Process
        self.Step           = Step

        #***Dot
        self.DotColor=0
        self.DotTypeSearch=0
        self.DotThresh=0.5
        self.DotDiam=10

        #***Type of target
        self.TargetType=0
        self.DotDx=5
        self.DotDy=5
        #double plane target
        self.OriginXShift=2.5
        self.OriginYShift=2.5
        self.OriginZShift=2.5

        #***Calibration procedure
        self.CalibProcType=0  #standard
        self.FlagPlane=0
        self.FlagPinhole=1  

        #***Camera calibration model
        self.CamMod=3
        #polynomials/rational functions
        self.XDeg=2
        self.YDeg=2
        self.ZDeg=2
        #pinhole
        self.PixAR=1
        self.PixPitch=0.0065
        #correction model
        self.CorrMod=2  #radial+tangential distortions
        #cylinder parameters
        self.CylRad=30
        self.CylThick=2
        self.CylNRatio=1
        #correction model cylinder
        self.CorrMod_Cyl=0  #cylinder origin and rotation
        self.FlagSaveLOS=0


class Process_Tab_CalVi(gPaIRS_Tab):
    class Process_Tab_Signals(gPaIRS_Tab.Tab_Signals):
        pass

    def __init__(self,parent: QWidget =None, flagInit= __name__ == "__main__"):
        super().__init__(parent,Ui_ProcessTab_CalVi,PROpar_CalVi)
        self.signals=self.Process_Tab_Signals(self)
    
        #------------------------------------- Graphical interface: widgets
        self.TABname='Process_CalVi'
        self.ui: Ui_ProcessTab_CalVi

        #necessary to change the name and the order of the items
        for g in list(globals()):
            if '_items' in g or '_ord' in g or '_tips' in g:
                #pri.Info.blue(f'Adding {g} to {self.name_tab}')
                setattr(self,g,eval(g))
        
        if __name__ == "__main__": 
            self.app=app
            setAppGuiPalette(self)

        #------------------------------------- Graphical interface: miscellanea
        self.Flag_CYLINDERCAL_option=None
        self.Flag_CYLINDERCAL=True

        #------------------------------------- Declaration of parameters 
        self.PROpar_base=PROpar_CalVi()
        self.PROpar:PROpar_CalVi=self.TABpar
        self.PROpar_old:PROpar_CalVi=self.TABpar_old

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
        pri.Info.yellow(f'{"*"*20}   PROCESS CalVi initialization   {"*"*20}')
        self.setTABpar(FlagAdjustPar=True,FlagBridge=False)
        self.add_TABpar('initialization')
        self.setFocus()

#*************************************************** Adjusting parameters
    def adjustPROpar(self):
        if self.PROpar.CalibProcType!=self.PROpar_old.CalibProcType:
            if self.PROpar.CalibProcType==0:
                self.PROpar.FlagPlane=True
            elif self.PROpar.CalibProcType==3:
                self.PROpar.FlagPlane=False
                self.PROpar.FlagPinhole=False
        self.adjustCalibProcType()
        self.adjustCorrMod()
        
        
#*************************************************** Layout
    def setPROlayout(self):
        #pri.Time.blue(1,'setPROpar: Beginning')
        self.ui.w_DoublePlane.setVisible(self.PROpar.TargetType!=0)

        if bool(self.Flag_CYLINDERCAL_option):
            self.Flag_CYLINDERCAL_option.setEnabled(self.PROpar.CalibProcType!=3)

        #check_Plane
        self.ui.check_Plane.setText(f'{"Show" if self.PROpar.CalibProcType==0 else "Opt."} plane const.')    
        self.ui.check_Plane.setEnabled(self.PROpar.CalibProcType not in (1,2))

        #check_Pinhole
        self.ui.check_Pinhole.setEnabled(self.PROpar.CalibProcType==3)

        #combo_CamMod
        self.ui.combo_CamMod.clear()
        flagEnabled=True
        if self.PROpar.CalibProcType==0:
            for it in CamMod_items:
                self.ui.combo_CamMod.addItem(it)
        elif self.PROpar.CalibProcType in (1,2): #unknwon planes (2) compatible with cylinder ?
            self.ui.combo_CamMod.addItem(CamMod_items[3])
            flagEnabled=False
        elif self.PROpar.CalibProcType==3:
            self.ui.combo_CamMod.addItem(CamMod_items[-1])
            flagEnabled=False
        self.ui.combo_CamMod.setEnabled(flagEnabled)
            
        #stacked_Widget
        FlagCamMod=self.PROpar.CamMod>=3
        self.ui.w_CamMod_par.setCurrentIndex(int(FlagCamMod))
        self.ui.check_Plane.setVisible(FlagCamMod)
        self.ui.check_Pinhole.setVisible(FlagCamMod)
        self.ui.w_CamMod_par.setEnabled(self.PROpar.CamMod < 3 or self.PROpar.FlagPinhole)

        #combo_corrMod
        self.ui.w_CylPar.setVisible(self.PROpar.CamMod==4)
        FlagCorrMod=self.PROpar.CamMod >= 3 and self.PROpar.FlagPinhole
        self.ui.combo_CorrMod.setVisible(FlagCorrMod)
        self.ui.label_CorrMod.setVisible(FlagCorrMod)
        if FlagCorrMod:
            self.ui.combo_CorrMod.clear()
            if self.PROpar.CalibProcType==0 and self.PROpar.CamMod==4: l=len(CorrMod_items)
            else: l=3
            for it in CorrMod_items[:l]:
                self.ui.combo_CorrMod.addItem(it)      
        self.ui.w_CalibProc_Cyl.setVisible(self.PROpar.CalibProcType==3)      

#*************************************************** Target parameters
#******************** Actions 
    def button_DotColor_action(self):
        if self.ui.button_DotColor.text()==DotColor_labels[0]: self.PROpar.DotColor=1
        else: self.PROpar.DotColor=0

#******************** Settings   
    def button_DotColor_set(self):
        self.ui.button_DotColor.setText(DotColor_labels[self.PROpar.DotColor])
        
#*************************************************** Calibration parameters
#******************** Actions  
    def check_SaveLOS_action(self):
        if self.ui.check_SaveLOS.isChecked():
            warningDialog(self,'Please notice that the feature to save the lines-of-sight (LOS) data to the disk is not currently available!\n\nContact the authors via email if interested.')

#******************** Adjusting 
    def adjustCalibProcType(self):
        if self.PROpar.CalibProcType in (1,2):
            self.PROpar.FlagPlane=True

        if self.PROpar.CalibProcType!=3:
            self.PROpar.FlagPinhole=self.PROpar.CalibProcType<2

        if self.PROpar.CalibProcType in (1,2) and self.PROpar.CamMod!=3:
            self.PROpar.CamMod=3
        elif self.PROpar.CalibProcType==3:
            self.PROpar.CamMod=4

    def adjustCorrMod(self):
        if not(self.PROpar.CalibProcType==0 and self.PROpar.CamMod==4) and self.PROpar.CorrMod>2:
            self.PROpar.CorrMod=2

#*************************************************** From Parameters to UI
    def setCYLPARDebug(self):
        self.ui.combo_CalibProcType.clear()
        if self.Flag_CYLINDERCAL: l=len(CalibProcType_items)
        else: l=len(CalibProcType_items)-1
        for it in CalibProcType_items[:l]:
            self.ui.combo_CalibProcType.addItem(it)

if __name__ == "__main__":
    import sys
    app=QApplication.instance()
    if not app:app = QApplication(sys.argv)
    app.setStyle('Fusion')
    object = Process_Tab_CalVi(None)
    object.show()
    app.exec()
    app.quit()
    app=None

from .ui_Process_Tab import*
from .TabTools import*
from .Custom_Top import Custom_Top
#from procTools import *

Flag_type_of_DCs=False
Flag_Hart_corr=False
Flag_Nogueira=False
minNIterAdaptative=5

mode_items= ['simple', #0
             'advanced', #1
             'expert'] #2

top_items=[ 'custom',  #0
            'preview', #1
            'fast',    #2
            'standard',#3
            'advanced',#4
            'high resolution', #5
            'adaptative resolution'] #6

mode_init=0
top_init=3
WSize_init=[128, 64, 32]
WSpac_init=[ 64, 16, 8]

ImInt_items=( #************ do not change the order of items here!
            'none',                             # none
            'moving window',                    # moving window
            'linear revitalized',               # linear revitalized
            'bilinear/biquadratic/bicubic',     # bilinear/biquadratic/bicubic
            'simplex',                          # simplex
            'shift theorem',                    # shift theorem
            'sinc (Whittaker-Shannon)',         # sinc (Whittaker-Shannon)
            'B-spline'                          # B-spline
            )
ImInt_order=[i for i in range(len(ImInt_items))] #************ change here, please!

VelInt_items=( #************ do not change the order of items here!
            'bilinear',                         # bilinear
            'linear revitalized',               # linear revitalized
            'simplex',                          # simplex
            'shift theorem',                    # shift theorem
            'shift theorem (extrapolation)',    # shift theorem (extrapolation)
            'B-spline'                          # B-spline
            )
VelInt_order=[i for i in range(len(VelInt_items))] #************ change here, please!


Wind_items=( #************ do not change the order of items here!
            'top-hat',                          # top-hat
            'Nogueira',                         # Nogueira
            'Blackman',                        # Blackman
            'Blackman-Harris',                 # Blackman-Harris
            'triangular',                       # Triangular
            'Hann',                             # Hann
            'Gaussian',                         # Gaussian
            )
Wind_abbrev=('TH','NG','BL','BH','TR','HN','GS')
#Wind_order=[i for i in range(8)] #************ change here, please!
Wind_order=[0,2,6,3,5,1,4]

spin_tips={ 
            'final_iter'        :   'Number of final iterations',
            'final_it'          :   'Number of final iterations for different image interpolation',
            'KernMed'           :   'Semi-kernel for median test',
            'SogliaMed'         :   'Alpha threshold for median test',
            'ErroreMed'         :   'Epsilon threshold for median test',
            'JumpMed'           :   'Spacing of vectors for validation',
            'SogliaSN'          :   'Threshold for S/N test',
            'SogliaCP'          :   'Threshold for correlation peak test',
            'SogliaMedia'       :   'Tolerance for Nogueira test',
            'SogliaNumVet'      :   'Number of vectors for Nogueira test',
            'SogliaNoise'       :   'Minimum allowed value for validation',
            'SogliaStd'         :   'Minimum allowed st.d. value for validation',
            'Wind_halfwidth'    :   'Weighting window half-width',
            'NItAdaptative'     :   'Number of iterations for adaptative process',
            'MinC'              :   'Minimum correlation value for adapatative process',
            'MaxC'              :   'Maximum correlation value for adapatative process',
            'LarMax'            :   'Maximum half-width for adapatative process',
            'LarMin'            :   'Minimum half-width for adapatative process',
            'order'             :   'Kernel width for image interpolation',
            'order_2'           :   'Kernel width for image interpolation (final it.)',
            'VelInt_order'      :   'Kernel width for velocity interpolation',
            'par_Gauss'         :   'Alpha threshold for Gaussian window',
            'par_Gauss_2'       :   'Half-width for Gaussian window',
            'MaxDisp_absolute'  :   'Maximum displacement',
            }
button_tips={
            'more_size'  :   'Rectangular IW',
            'more_iter'  :   'Image interpolation (final it.)',
            'edit_custom':   'Custom type of process',
            'add'        :   'PIV process iterations',
            'delete'     :   'PIV process iterations',
            'FinIt'      :   'Final iteration  box',
            'Interp'     :   'Interpolation box',
            'Validation' :   'Validation box',
            'Windowing'  :   'Windowing box',
            'top'        :   'Type of process box',
            'save_custom':   'Save custom process',
            'mtf'        :   'Plot MTF',
            'save_cfg'   :   'Save of .cfg file',
            'tool_CollapBox_IntWind'   : 'Graphics',
            'CollapBox_IntWind'        : 'Graphics',
            'tool_CollapBox_FinIt'     : 'Graphics',
            'CollapBox_FinIt'          : 'Graphics',
            'tool_CollapBox_top'       : 'Graphics',
            'CollapBox_top'            : 'Graphics',
            'tool_CollapBox_Interp'    : 'Graphics',
            'CollapBox_Interp'         : 'Graphics',
            'tool_Validation'          : 'Graphics',
            'CollapBox_Validation'     : 'Graphics',
            'tool_Windowing'           : 'Graphics',
            'CollapBox_Windowing'      : 'Graphics',
            }
check_tips={
            'Bordo'         :  'First vector at IW spacing',
            'DC'            :   'Direct correlation',
            'SecMax'        :   'Second correlation peak correction',
            'CorrHart'      :   'Hart''s correction',
            'DC_it'         :   'DC for current iteration',
            }
line_edit_tips={
                'size'      :  'IW size'   ,
                'spacing'   :  'IW spacing',
                'size_2'    :  'IW size'   ,
                'spacing_2' :  'IW spacing',
                'IW'        :  'IW sizes and/or spacings',
                }
combo_tips ={
            'mode'              :   'Process mode',                  
            'top'               :   'Type of process',               
            'custom_top'        :   'Custom type of process',        
            'correlation'       :   'Correlation map interpolation', 
            'TypeMed'           :   'Median test type',              
            'FlagCorrezioneVel' :   'Correction type',               
            'FlagSommaProd'     :   'Type of DCs',                   
            'ImInt'             :   'Image interpolation',
            'par_pol'           :   'Polynomial interpolation',      
            'par_imshift'       :   'Moving window',                 
            'ImInt_2'           :   'Image interpolation (final it.)', 
            'par_pol_2'         :   'Polynomial interpolation (final it.)',
            'par_imshift_2'     :   'Moving window (final it.)',
            'int_vel'           :   'Velocity field interpolation',  
            'Wind_Vel_type'     :   'Velocity weighting window',
            'par_tophat'        :   'Top-hat window type (vel.)',
            'par_Nog'           :   'Nogueira window type (vel.)',
            'par_Bla'           :   'Blackman window type (vel.)',
            'par_Har'           :   'Blackman-Harris window type (vel.)',
            'Wind_Corr_type'    :   'Correlation map weighting window',
            'par_tophat_2'      :   'Top-hat window type (corr.)',
            'par_Nog_2'         :   'Nogueira window type (corr.)',
            'par_Bla_2'         :   'Blackman window type (corr.)',
            'par_Har_2'         :   'Blackman-Harris window type (corr.)',
            'MaxDisp_type'      :   'Maximum displacement type',
            'MaxDisp_relative'  :   'Maximum displacement',
            }
radio_tips={
            'MedTest'   :  'Median test',
            'SNTest'    :  'S/N test',
            'CPTest'    :  'Correlation peak test',
            'Nogueira'  :  'Nogueira test',
            'Adaptative':  'Adaptative process',
            }

def cont_fields(diz):
    cont=0
    for f,v in diz:
        if not 'fields' in f and f[0]!='_':
            cont+=1
    return cont
    
class PROpar(TABpar):
    mode=mode_init

    def __init__(self,top=top_init,WSize=WSize_init,WSpac=WSpac_init,Process=ProcessTypes.null,Step=StepTypes.null):    
        #attributes in fields
        self.setup(top,WSize,WSpac,Process,Step)
        super().__init__('PROpar','Process')
        self.unchecked_fields+=['prev_top','mode',\
            'FlagFinIt_reset','FlagInterp_reset','FlagValidation_reset','FlagWindowing_reset','FlagCustom',\
            'IntIniz_ind_list','IntFin_ind_list',\
            'VectFlag','flag_rect_wind','row','col',\
            'FlagCalcVel','FlagWindowing','SemiDimCalcVel','MaxDisp','FlagDC_it']

    def setup(self,top=top_init,WSize=WSize_init,WSpac=WSpac_init,Process=ProcessTypes.null,Step=StepTypes.null):
        self.Process = Process
        self.Step = Step
        cont=[0]
        name_fields=['']
        #************* DEFAULT VALUES
        #******************************* base_fields
        self.FlagCustom=False
        self.FlagFinIt_reset=False
        self.FlagInterp_reset=False
        self.FlagValidation_reset=False
        self.FlagWindowing_reset=False

        if not self.mode in mode_items:
            self.mode=0
        self.top=top
        self.prev_top=top
        self.custom_top_name=''

        cont.append(cont_fields(self.__dict__.items()))
        name_fields.append('base')

        #******************************* IW_fields
        self.Nit=len(WSize)
        Vect=[copy.deepcopy(WSize),copy.deepcopy(WSpac),copy.deepcopy(WSize),copy.deepcopy(WSpac)]
        self.Vect=Vect
        self.VectFlag=[True]*4
        self.flag_rect_wind=False
        self.FlagBordo=1

        cont.append(cont_fields(self.__dict__.items()))
        name_fields.append('IW')

        #******************************* FinalIt_fields
        self.FlagDirectCorr=1
        self.NIterazioni=0

        cont.append(cont_fields(self.__dict__.items()))
        name_fields.append('FinalIt')
        
        #******************************* Int_fields
        self.IntIniz=1
        self.IntIniz_ind_list=[3,1,2]
        self.IntFin=1
        self.IntFin_ind_list=[3,1,2]
        self.FlagInt=0
        self.IntCorr=0
        self.IntVel=1

        cont.append(cont_fields(self.__dict__.items()))
        name_fields.append('Int')

        #******************************* Validation_fields
        self.FlagMedTest=1
        self.TypeMed=1
        self.KernMed=1
        self.SogliaMed=2.0
        self.ErroreMed=0.5
        self.JumpMed=1

        self.FlagSNTest=0
        self.SogliaSN=1.5

        self.FlagCPTest=0
        self.SogliaCP=0.2

        self.FlagNogTest=0
        self.SogliaMedia=0.25
        self.SogliaNumVet=0.10

        self.SogliaNoise=2.00
        self.SogliaStd=3.00
        self.FlagCorrezioneVel=1
        self.FlagSecMax=1
        self.FlagCorrHart=0

        cont.append(cont_fields(self.__dict__.items())) 
        name_fields.append('Validation')

        #******************************* Windowing_fields
        self.vFlagCalcVel=[0]*self.Nit
        self.vFlagWindowing=[0]*self.Nit
        self.vSemiDimCalcVel=[0]*self.Nit
        self.vMaxDisp=[-4]*self.Nit
        if self.Nit>1:
            self.vDC=[0]*(self.Nit-1)+[self.FlagDirectCorr]
        else:
            self.vDC=[0]
            

        self.FlagAdaptative=0
        self.NItAdaptative=2
        self.MinC=0.4
        self.MaxC=0.75
        self.LarMin=1
        self.LarMax=16
        self.FlagSommaProd=0
        
        cont.append(cont_fields(self.__dict__.items()))
        name_fields.append('Wind')

        self.row=0
        self.col=0

        if self.top==1: #preview/custom
            self.IntIniz=3
            self.IntFin=3
            self.IntVel=1
            self.NIterazioni=0
        elif self.top==2: #fast
            self.IntIniz=1
            self.IntFin=1
            self.IntVel=1
            self.NIterazioni=1
        elif self.top==0 or self.top==3: #standard
            self.IntIniz=53
            self.IntFin=53
            self.IntVel=52
            self.NIterazioni=2
        elif self.top==4: #advanced
            self.IntIniz=57
            self.IntFin=57
            self.IntVel=53
            self.NIterazioni=2

            self.vFlagCalcVel=[2]*self.Nit
            self.vFlagWindowing=[2]*self.Nit
        elif self.top==5: #high resolution
            self.IntIniz=57
            self.IntFin=57
            self.IntVel=53
            self.NIterazioni=10

            self.vFlagCalcVel=[2]*self.Nit
            self.vFlagWindowing=[2]*self.Nit
            self.vSemiDimCalcVel=[3]*self.Nit
        elif self.top==6: #adaptative
            self.IntIniz=57
            self.IntFin=57
            self.IntVel=53
            self.NIterazioni=20

            self.FlagAdaptative=1
            self.vFlagCalcVel=[2]*(self.Nit+1)
            self.vFlagWindowing=[2]*(self.Nit+1)
            self.vSemiDimCalcVel=[3]*self.Nit+[self.LarMax]
            self.vMaxDisp+=[self.vMaxDisp[-1]]
            self.vDC+=[self.vDC[-1]]
        
        self.FlagCalcVel   =self.vFlagCalcVel   [self.row]
        self.FlagWindowing =self.vFlagWindowing [self.row]
        self.SemiDimCalcVel=self.vSemiDimCalcVel[self.row]
        self.MaxDisp       =self.vMaxDisp       [self.row]
        self.FlagDC_it            =self.vDC [self.row]
        
        for j in range(1,len(cont)):
            setattr(self,name_fields[j]+"_fields",[])
            d=getattr(self,name_fields[j]+"_fields")
            k=-1
            for f,_ in self.__dict__.items():
                k+=1
                if k in range(cont[j-1],cont[j]):
                    d.append(f)

    def change_top(self,top_new):
        WSize=[w for w in self.Vect[0]]
        WSpac=[w for w in self.Vect[1]]
        newist=PROpar(top_new,WSize,WSpac,self.Process,self.Step)
        newist.copyfromfields(self,newist.parFields)
        for f in self.fields:
            if f not in self.IW_fields:
                setattr(self,f,getattr(newist,f))       

class Process_Tab(gPaIRS_Tab):
    class Process_Tab_Signals(gPaIRS_Tab.Tab_Signals):
        pass

    def __init__(self,parent: QWidget =None, flagInit= __name__ == "__main__"):
        super().__init__(parent,Ui_ProcessTab,PROpar)
        self.signals=self.Process_Tab_Signals(self)

        #------------------------------------- Graphical interface: widgets
        self.TABname='Process'
        self.ui: Ui_ProcessTab
        ui=self.ui

        self.Vect_widgets=[ui.line_edit_size,\
            ui.line_edit_spacing,\
                ui.line_edit_size_2,\
                    ui.line_edit_spacing_2]
        self.Vect_Lab_widgets=[ui.check_edit_size,\
            ui.check_edit_spacing,\
                ui.check_edit_size_2,\
                    ui.check_edit_spacing_2]
        ui.line_edit_size.addlab=ui.check_edit_size
        ui.line_edit_size.addwid=[w for w in self.Vect_widgets]
        ui.line_edit_size.addwid.append(ui.spin_final_iter)
        ui.line_edit_spacing.addlab=ui.check_edit_spacing
        ui.line_edit_spacing.addwid=ui.line_edit_size.addwid
        ui.line_edit_size_2.addlab=ui.check_edit_size_2
        ui.line_edit_size_2.addwid=ui.line_edit_size.addwid
        ui.line_edit_spacing_2.addlab=ui.check_edit_spacing_2
        ui.line_edit_spacing_2.addwid=ui.line_edit_size.addwid
        ui.table_iter.addwid.append(ui.line_edit_IW)

        #necessary to change the name and the order of the items
        for g in list(globals()):
            if '_items' in g or '_ord' in g or '_tips' in g:
                #pri.Info.blue(f'Adding {g} to {self.name_tab}')
                setattr(self,g,eval(g))
        self.Wind_Vel_type_items=Wind_items
        self.Wind_Vel_type_order=Wind_order
        self.Wind_Corr_type_items=Wind_items
        self.Wind_Corr_type_order=Wind_order

        
        if __name__ == "__main__": 
            self.app=app
            setAppGuiPalette(self)
            
        #------------------------------------- Graphical interface: miscellanea
        self.icon_plus = QIcon()
        self.icon_plus.addFile(u""+ icons_path +"plus.png", QSize(), QIcon.Normal, QIcon.Off)
        self.icon_minus = QIcon()
        self.icon_minus.addFile(u""+ icons_path +"minus.png", QSize(), QIcon.Normal, QIcon.Off)

        self.Lab_greenv=QPixmap(u""+ icons_path +"greenv.png")
        self.Lab_redx=QPixmap(u""+ icons_path +"redx.png")
        self.Lab_warning=QPixmap(u""+ icons_path +"warning.png")

        self.ui.button_more_size.setIconSize(self.ui.button_more_size.size()-QSize(6,6))
        self.ui.button_more_iter.setIconSize(self.ui.button_more_iter.size()-QSize(6,6))

        self.custom_list_file=pro_path+custom_list_file
        self.setCustomTops()

        self.tableHeaders =[self.ui.table_iter.horizontalHeaderItem(i).text() for i in range(self.ui.table_iter.columnCount())]
        header = self.ui.table_iter.horizontalHeader()    
        #it, velocity, correlation, DC, Max. disp.
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) #it
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive) #velocity
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive) #correlation
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive) #Max. disp.
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents) #DC
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch) #Info
        self.ui.table_iter.setHorizontalHeaderLabels(self.tableHeaders)
        #header.setMinimumSectionSize(int(self.minimumWidth()/2))
        #header.setMaximumSectionSize(int(self.maximumWidth()/2))
        self.ui.table_iter.InfoLabel=self.ui.label_info
        self.ui.table_iter.DeleteButton=self.ui.button_delete
        self.ui.label_info.hide()

        #------------------------------------- obsolescences    
        if not Flag_type_of_DCs: 
            #self.ui.w_type_of_DCs.hide()
            self.ui.label_type_of_DCs.hide()
            self.ui.combo_FlagSommaProd.hide()
        if not Flag_Hart_corr: self.ui.check_CorrHart.hide()
        if not Flag_Nogueira: self.ui.w_Nogueira.hide()

        #------------------------------------- Declaration of parameters 
        self.PROpar_base=PROpar()
        self.PROpar:PROpar=self.TABpar
        self.PROpar_old:PROpar=self.TABpar_old
        self.PROpar_custom=PROpar(0)

        #------------------------------------- Callbacks
        self.defineWidgets()
        self.setupWid()  #---------------- IMPORTANT
        
        self.defineActions()
        self.defineCallbacks()
        self.connectCallbacks()
        self.defineAdditionalCallbacks()
        self.defineSet()
        self.defineSettings()
        self.TABsettings.append(self.table_iter_set)
        self.adjustTABpar=self.adjustPROpar
        self.setTABlayout=self.setPROlayout

        #------------------------------------- Initializing    
        if flagInit:     
            self.initialize()
        #else:
        #    self.setTABpar(FlagBridge=False)

    def initialize(self):
        pri.Info.yellow(f'{"*"*20}   PROCESS initialization   {"*"*20}')
        self.setTABpar(FlagBridge=False)
        self.add_TABpar('initialization')
        self.setFocus()
        
    def defineActions(self):
        self.defineIWActions() 
        self.defineInterpActions() 
        self.defineWindowingActions()
        self.defineCollapBoxActions()

    def defineAdditionalCallbacks(self):
        #additional callbacks
        self.ui.spin_final_it.addfuncout['check_more_iter']=self.spin_final_it_action
        self.ui.spin_final_it.addfuncreturn['check_more_iter']=self.spin_final_it_action 

        #graphical callbacks
        names=['size','spacing','size_2','spacing_2']
        f='line_edit'
        for n in names:
            wid=getattr(self.ui,f+"_"+n)
            fcallback=getattr(self,f+"_"+n+"_changing")
            wid.textChanged.connect(fcallback)
        
        #other functions
        self.ui.line_edit_IW.addfuncin["InfoLabelIn"]=self.line_edit_IW_addfuncin
        self.ui.line_edit_IW.addfuncout["InfoLabelOut"]=self.ui.table_iter.resizeInfoLabel
        self.ui.table_iter.itemSelectionChanged.connect(self.wrappedCallback('Iteration table selection',self.table_iter_action))
        self.ui.table_iter.contextMenuEvent=lambda e: self.tableContextMenuEvent(self.ui.table_iter,e)
        self.ui.spin_LarMin.valueChanged.connect(self.spin_LarMin_changing)

    def defineIWActions(self):
        wtype='line_edit'
        def defineIWAction(i,n):
            widname=wtype+"_"+n
            a1=getattr(self.ui,'line_edit'+'_'+n)
            a2=getattr(self.ui,'check_edit'+'_'+n)
            edit_changing=widname+'_changing'
            setattr(self,edit_changing,lambda: self.edit_Wind_vectors(a1,a2))
            edit_action=widname+'_action'
            setattr(self,edit_action,lambda: self.set_Wind_vectors(a1,a2,i))
        names=['size','spacing','size_2','spacing_2']
        for i,n in enumerate(names):
            defineIWAction(i,n)
        return
    
    def defineInterpActions(self):
        if hasattr(self.ui,'combo_ImInt'):
            self.combo_ImInt_action=lambda: Process_Tab.combo_ImInt_action_gen(self,'IntIniz',self.ui.combo_ImInt,self.ui.w_ImInt_par,self.PROpar.IntIniz_ind_list)
            names=['combo_par_pol','combo_par_imshift','spin_order']
            for n in names:
                setattr(self,n+'_action',self.combo_ImInt_action)

        if hasattr(self.ui,'combo_ImInt_2'):
            self.combo_ImInt_2_action=lambda: Process_Tab.combo_ImInt_action_gen(self,'IntFin',self.ui.combo_ImInt_2,self.ui.w_ImInt_par_2,self.PROpar.IntFin_ind_list)
            names=['combo_par_pol_2','combo_par_imshift_2','spin_order_2']
            for n in names:
                setattr(self,n+'_action',self.combo_ImInt_2_action)

        if hasattr(self.ui,'combo_int_vel'):
            self.combo_int_vel_action=lambda: Process_Tab.combo_int_vel_action_gen(self,'IntVel',self.ui.combo_int_vel,self.ui.w_VelInt_par)
            self.spin_VelInt_order_action=self.combo_int_vel_action
        return     

    def defineWindowingActions(self):
        self.combo_Wind_Vel_type_action=lambda: self.combo_Wind_Vel_action_gen('FlagCalcVel',self.ui.combo_Wind_Vel_type,self.ui.w_Wind_par)
        names=['combo_par_tophat','combo_par_Nog','combo_par_Bla','combo_par_Har','spin_par_Gauss']
        for n in names:
            setattr(self,n+'_action',self.combo_Wind_Vel_type_action)

        self.combo_Wind_Corr_type_action=lambda: self.combo_Wind_Vel_action_gen('FlagWindowing',self.ui.combo_Wind_Corr_type,self.ui.w_Wind_par_2)
        names=['combo_par_tophat_2','combo_par_Nog_2','combo_par_Bla_2','combo_par_Har_2','spin_par_Gauss_2']
        for n in names:
            setattr(self,n+'_action',self.combo_Wind_Corr_type_action)

        self.combo_MaxDisp_relative_action=self.combo_MaxDisp_action
        self.spin_MaxDisp_absolute_action=self.combo_MaxDisp_action
        return

    def defineCollapBoxActions(self):
        self.button_CollapBox_FinIt_action=lambda: self.reset_field('FinalIt_fields')
        self.button_CollapBox_Interp_action=lambda: self.reset_field('Int_fields')
        self.button_CollapBox_Validation_action=lambda: self.reset_field('Validation_fields')
        self.button_CollapBox_Windowing_action=lambda: self.reset_field('Wind_fields')
        self.button_CollapBox_top_action=self.combo_top_action
        return
   
    def defineSet(self):
        self.defineInterpSet()
        self.defineWindowingSet()

    def defineInterpSet(self):
        if hasattr(self.ui,'combo_ImInt'):
            self.combo_ImInt_set=lambda: Process_Tab.combo_ImInt_set_gen(self,'IntIniz',self.ui.combo_ImInt,self.ui.w_ImInt_par,self.PROpar.IntIniz_ind_list)
        if hasattr(self.ui,'combo_ImInt_2'):
            self.combo_ImInt_2_set=lambda: Process_Tab.combo_ImInt_set_gen(self,'IntFin',self.ui.combo_ImInt_2,self.ui.w_ImInt_par_2,self.PROpar.IntFin_ind_list)
        if hasattr(self.ui,'combo_int_vel'):
            self.combo_int_vel_set=lambda: Process_Tab.combo_int_vel_set_gen(self,'IntVel',self.ui.combo_int_vel,self.ui.w_VelInt_par)
        return

    def defineWindowingSet(self):
        self.combo_Wind_Vel_type_set=lambda: self.combo_Wind_Vel_set_gen('FlagCalcVel',self.ui.combo_Wind_Vel_type,self.ui.w_Wind_par)
        self.combo_Wind_Corr_type_set=lambda: self.combo_Wind_Vel_set_gen('FlagWindowing',self.ui.combo_Wind_Corr_type,self.ui.w_Wind_par_2)
        self.MTF=None

 #*************************************************** adjusting PROpars and controls
    def reset_field(self,dizName):
        diz=getattr(self.PROpar,dizName)
        top=self.PROpar.prev_top
        WSize=[w for w in self.PROpar.Vect[0]]
        WSpac=[w for w in self.PROpar.Vect[1]]
        PROpar_old=PROpar(top,WSize,WSpac,self.PROpar.Process,self.PROpar.Step)
        self.PROpar.copyfromfields(PROpar_old,diz)
        if self.PROpar.top==0:
            self.setPROpar_custom()

    def adjustPROpar(self):
        self.check_reset()
        self.check_more_iter()
        self.adjustWindowingPar()

    def check_reset(self):
        WSize=[w for w in self.PROpar.Vect[0]]
        WSpac=[w for w in self.PROpar.Vect[1]]
        PROpar_old=PROpar(self.PROpar.top,WSize,WSpac,self.PROpar.Process,self.PROpar.Step)
        if PROpar_old.top==0:
            i=self.ui.combo_custom_top.currentIndex()
            if i!=-1:
                PROpar_old.copyfrom(self.PROpar_customs[i])
        exc=self.PROpar.unchecked_fields+['ind']
        self.PROpar.FlagFinIt_reset=not self.PROpar.isEqualTo(PROpar_old,exc,self.PROpar.FinalIt_fields)
        self.PROpar.FlagInterp_reset=not self.PROpar.isEqualTo(PROpar_old,exc,self.PROpar.Int_fields)
        self.PROpar.FlagValidation_reset=not self.PROpar.isEqualTo(PROpar_old,exc,self.PROpar.Validation_fields)
        self.PROpar.FlagWindowing_reset=not self.PROpar.isEqualTo(PROpar_old,exc,self.PROpar.Wind_fields)
        #self.PROpar.printDifferences(PROpar_old,exc)
        self.PROpar.FlagCustom=self.PROpar.FlagFinIt_reset|self.PROpar.FlagInterp_reset|\
            self.PROpar.FlagValidation_reset|self.PROpar.FlagWindowing_reset

    def check_more_iter(self):
        max_it=len(self.PROpar.Vect[0])+self.PROpar.NIterazioni
        if max_it==1:
            self.PROpar.FlagInt=0
        else:
            self.ui.spin_final_it.setMaximum(max_it-1)
    
    def adjustWindowingPar(self):
        Nit=self.PROpar.Nit
        fields=['vFlagCalcVel','vFlagWindowing','vSemiDimCalcVel','vDC','vMaxDisp']
        for f in fields:
            v=getattr(self.PROpar,f)
            nWind=len(v)
            if nWind>Nit:
                for k in range(nWind-1,Nit-1,-1):
                    v.pop(k)
            elif nWind<Nit:
                for k in range(nWind,Nit):
                    v.append(v[-1])
        if self.PROpar.FlagAdaptative:
            self.PROpar.vSemiDimCalcVel[-1]=self.PROpar.LarMin
            self.PROpar.vFlagCalcVel+=[self.PROpar.vFlagCalcVel[-1]]      #+=[2] per BL
            self.PROpar.vFlagWindowing+=[self.PROpar.vFlagWindowing[-1]]  #+=[2] per BL
            self.PROpar.vSemiDimCalcVel+=[self.PROpar.LarMax]
            self.PROpar.vMaxDisp+=[self.PROpar.vMaxDisp[-1]]
            self.PROpar.vDC+=[self.PROpar.vDC[-1]]
        if not self.PROpar.FlagDirectCorr:
            self.PROpar.vDC=[0]*len(self.PROpar.vDC)
        self.PROpar.row=len(self.PROpar.vFlagCalcVel)-1 if self.PROpar.row>=len(self.PROpar.vFlagCalcVel)-1 else self.PROpar.row if self.PROpar.row>-1 else 0
        self.adjustTablePar()
        if self.PROpar.FlagAdaptative and self.PROpar.row==self.PROpar.Nit-1:
            self.PROpar.SemiDimCalcVel=self.PROpar.LarMin
        return

    def adjustTablePar(self):
        self.PROpar.FlagCalcVel   =self.PROpar.vFlagCalcVel   [self.PROpar.row]
        self.PROpar.FlagWindowing =self.PROpar.vFlagWindowing [self.PROpar.row]
        self.PROpar.SemiDimCalcVel=self.PROpar.vSemiDimCalcVel[self.PROpar.row]
        self.PROpar.MaxDisp=self.PROpar.vMaxDisp[self.PROpar.row]
        self.PROpar.FlagDC_it=self.PROpar.vDC[self.PROpar.row]
        pri.Callback.green(f'{" "*10}   FlagCalcVel={self.PROpar.FlagCalcVel}, FlagWindowing={self.PROpar.FlagWindowing}, SemiDimCalcVel={self.PROpar.SemiDimCalcVel}, MaxDisp={self.PROpar.MaxDisp}, DC={self.PROpar.FlagDC_it}')

    def setPushCollapBoxes(self,*args):
        if len(args): 
            cb=args #tuple
        else: 
            cb=('FinIt','Interp','Validation','Windowing','ToP')
        for n in cb:
            if n!='ToP':
                flag=getattr(self.PROpar,'Flag'+n+'_reset')
                push=getattr(self.ui,'button_CollapBox_'+n)
                CollapBox=getattr(self.ui,'CollapBox_'+n)
                if flag:
                    push.show() 
                else:
                    push.hide()
                    w=getattr(self.ui,'CollapBox_'+n)
                    #w.setFocus()
                CollapBox.FlagPush=flag
        if self.PROpar.FlagCustom:
            self.ui.button_save_custom.show()
            self.ui.label_top.setText("Modified from ")
            self.ui.button_CollapBox_top.show() 
            self.ui.CollapBox_top.FlagPush=True
        else:
            self.ui.button_save_custom.hide()
            self.ui.label_top.setText("Current")
            self.ui.button_CollapBox_top.hide() 
            self.ui.CollapBox_top.FlagPush=False

#*************************************************** From Parameters to UI
    def setPROlayout(self):
        self.setPROlayout_mode()
        self.setPROlayout_IW()
        self.setPROlayout_ToP()
        self.setPushCollapBoxes()
        self.setPROlayout_Int()
        self.setPROlayout_Valid()
        self.setPROlayout_Wind()
  
#*************************************************** MODE   
#******************** Actions     
    def combo_mode_action(self):
        self.PROpar.mode=PROpar.mode=self.ui.combo_mode.currentIndex()
        return 

    def button_save_cfg_action(self):
        Title='Select location and name of the configuration file to save'
        filename, _ = QFileDialog.getSaveFileName(self,Title, 
                    filter=f'*.cfg',\
                    options=optionNativeDialog)
        filename=myStandardRoot('{}'.format(str(filename)))
        if not filename: return
        if 'dataTreePar' not in list(globals()):
            from .procTools import dataTreePar
        data=dataTreePar(self.PROpar.Process,self.PROpar.Step)
        data.setProc(PRO=self.PROpar.duplicate())
        data.writeCfgProcPiv(filename,FlagWarningDialog=True)
        
#******************** Settings   
    def combo_mode_set(self):
        self.ui.combo_mode.setCurrentIndex(PROpar.mode)
        return 

#******************** Layout  
    def setPROlayout_mode(self):
        index=PROpar.mode
        self.ui.CollapBox_Interp.setVisible(index>0)
        self.ui.CollapBox_Validation.setVisible(index>1)
        self.ui.CollapBox_Windowing.setVisible(index>1)

#*************************************************** INTERROGATION WINDOWS
#******************** Actions     
    def edit_Wind_vectors(self,wedit:QLineEdit,wlab:QLabel):
        text=wedit.text()
        split_text=re.split(r'(\d+)', text)[1:-1:2]
        vect=[int(i) for i in split_text]
        FlagEmpty=len(vect)==0
        if FlagEmpty: FlagError=True
        else: FlagError=not all([v>=w for v,w in zip(vect[:-1],vect[1:])])
        if FlagError:
            wlab.setPixmap(self.Lab_warning)
            if FlagEmpty:
                message="Please, insert at least one element!"
            else:
                message="Items must be inserted in decreasing order!"
            wlab.setToolTip(message)
            wlab.setStatusTip(message)
            """
            QToolTip.showText(QCursor.pos(),wlab.toolTip(),wedit,QRect(),3000)       
            """
        else: 
            wlab.setPixmap(QPixmap())
        self.PROpar.VectFlag[self.Vect_widgets.index(wedit)]=not FlagError
        return split_text, vect, FlagError

    def set_Wind_vectors(self,wedit:QLineEdit,wlab:QLabel,i):
        _, vect, FlagError=self.edit_Wind_vectors(wedit,wlab)     
        self.set_Wind_vectors_new(i,vect,FlagError) 
        
    def set_Wind_vectors_new(self,i,vect,FlagError=False):
        if not FlagError: 
            Nit_i=len(vect) 
            if Nit_i>self.PROpar.Nit:
                self.PROpar.Nit=Nit_i
            else:
                if all([v==w for v,w in zip(vect[:Nit_i],self.PROpar.Vect[i][:Nit_i])]):
                    self.PROpar.Nit=Nit_i    
            Vect2=[]
            for j in range(4):
                if self.PROpar.flag_rect_wind:
                    k=j
                else: 
                    k=j%2
                if k==i:
                    Vect2.append(copy.deepcopy(vect))
                else:
                    Vect2.append(copy.deepcopy(self.PROpar.Vect[k]))      
            self.PROpar.Vect=self.adjustVect(Vect2)
        self.line_edit_size_set()

    def adjustVect(self,Vect):
        for i,v in enumerate(Vect):
            if self.PROpar.Nit<len(v):
                Vect[i]=v[:self.PROpar.Nit]
            elif self.PROpar.Nit>len(v):
                Vect[i]=v+[v[-1] for _ in range(self.PROpar.Nit-len(v))] #np.append(v,np.repeat(v[-1],self.PROpar.Nit-len(v)))
        """
        rep=np.array([0,0,0,0])
        for i,v in enumerate(Vect):
            if len(v)>1:
                while rep[i]<len(v)-1:
                    if v[-1-rep[i]]==v[-2-rep[i]]: rep[i]+=1
                    else: break
        #si potrebbe programmare meglio...
        dit=np.min(rep)
        if dit:
            self.PROpar.Nit-=dit
            for i in range(4):
                Vect[i]=Vect[i][:self.PROpar.Nit]
            self.ui.spin_final_iter.setValue(self.ui.spin_final_iter.value()+dit)
        """
        self.line_edit_size_set()
        return Vect

    def button_more_size_action(self):
        self.PROpar.flag_rect_wind=not self.PROpar.flag_rect_wind
        if not self.PROpar.flag_rect_wind:
            self.PROpar.Vect[2]=copy.deepcopy(self.PROpar.Vect[0])
            self.PROpar.Vect[3]=copy.deepcopy(self.PROpar.Vect[1])

    def check_Bordo_action(self):
        if self.ui.check_Bordo.isChecked():
            self.PROpar.FlagBordo=1
        else:
            self.PROpar.FlagBordo=0   
        pass

#******************** Settings
    def line_edit_size_set(self):
        for i in range(len(self.Vect_widgets)):
            w=self.Vect_widgets[i]
            v=self.PROpar.Vect[i]
            l=self.Vect_Lab_widgets[i]
            text="".join([str(t)+", " for t in v[:-1]]) + str(v[-1])
            w.setText(text)
            if self.PROpar.VectFlag[i]:
                l.setPixmap(self.Lab_greenv)
                l.setToolTip('')
                l.setStatusTip('')
            else:
                l.setPixmap(self.Lab_redx)
        self.check_more_iter()
   
    def button_more_size_set(self):
         self.ui.button_more_size.setChecked(self.PROpar.flag_rect_wind)

#******************** Layout       
    def setPROlayout_IW(self):
        if self.PROpar.flag_rect_wind:
            self.ui.button_more_size.setIcon(self.icon_minus)
            self.ui.w_IW_size_2.show()
            #self.ui.label_size.setText("Width")
            #self.ui.label_spacing.setText("Horizontal")
            self.ui.label_size.setText("Height")
            self.ui.label_spacing.setText("Vertical")
        else:
            self.ui.button_more_size.setIcon(self.icon_plus)
            self.ui.w_IW_size_2.hide()
            self.ui.label_size.setText("Size")
            self.ui.label_spacing.setText("Spacing")

#*************************************************** FINAL ITERATIONS
#******************** Actions  
    def spin_final_iter_action(self):
        self.PROpar.NIterazioni=self.ui.spin_final_iter.value()
        self.check_more_iter()

    def check_DC_action(self):
        self.PROpar.FlagDirectCorr=int(self.ui.check_DC.isChecked())
        self.PROpar.vDC=[self.PROpar.FlagDirectCorr]*len(self.PROpar.vDC)

#******************** Settings  
    def spin_final_iter_preset(self):
        if self.PROpar.FlagAdaptative:
            self.ui.spin_final_iter.setMinimum(minNIterAdaptative)
        else:
            self.ui.spin_final_iter.setMinimum(0)
    
    def spin_final_iter_set(self):
        self.ui.spin_final_iter.setValue(self.PROpar.NIterazioni)
    
    def check_DC_set(self):
        self.ui.check_DC.setChecked(self.PROpar.FlagDirectCorr)

#*************************************************** TYPE OF PROCESS
#******************** Actions 
    def combo_top_action(self):
        self.PROpar.prev_top=self.ui.combo_top.currentIndex()
        if not self.PROpar.top:
            self.setPROpar_custom()
        else:
            self.PROpar.change_top(self.PROpar.top)
        return
    
    def setPROpar_custom(self):
        fields=[f for f in self.PROpar.fields if not f in self.PROpar.IW_fields+['ind']]
        i=self.combo_custom_top_ind()
        if len(self.PROpar_customs) and i>-1:
            self.PROpar.copyfromfields(self.PROpar_customs[i],fields)
        else:
            self.PROpar.copyfromfields(self.PROpar_custom,fields)

    def combo_custom_top_action(self): 
        self.PROpar.custom_top_name=self.ui.combo_custom_top.currentText()
        self.combo_top_action()
    
    def button_save_custom_action(self):
        name=self.save_as_custom()
        if name!='':
            if name in self.custom_top_items:
                k=self.custom_top_items.index(name)
                self.custom_top_items.pop(k)
                self.PROpar_customs.pop(k)
            self.custom_top_items.insert(0,name)
            self.PROpar_customs.insert(0,self.PROpar.duplicate())
            rewriteCustomList(self.custom_top_items)

            self.PROpar_custom.copyfrom(self.PROpar)
            self.PROpar.top=0
            self.PROpar.FlagCustom=False
        return True  #prevent addition of redos/undos

    def save_as_custom(self):
        title="Save custom type of process"
        label="Enter the name of the custom type of process:"
        ok,text=inputDialog(self,title,label,completer_list=self.custom_top_items)

        if ok and text!='':
            filename=pro_path+text+outExt.pro
            if os.path.exists(filename):
                Message=f'Process "{text}" already exists.\nDo you want to overwrite it?'
                flagOverwrite=questionDialog(self,Message)
                if not flagOverwrite: return
                OptionValidRoot=True
            else:
                dummyfilename=pro_path+text+outExt.dum
                try:
                    open(dummyfilename,'w')
                except:
                    OptionValidRoot=False
                else:
                    OptionValidRoot=True
                finally:
                    if os.path.exists(dummyfilename):
                        os.remove(dummyfilename)
            if not OptionValidRoot: 
                warningDialog(self,'Invalid root name! Please, retry.')
                return
            
            try:
                with open(filename,'wb') as file:

                    self.PROpar.top=0
                    self.PROpar.FlagCustom=False
                    self.PROpar.name=text

                    pickle.dump(self.PROpar,file)
                    pri.Info.blue(f'Saving custom process file {filename}')
            except Exception as inst:
                pri.Error.red(f'Error while saving custom process file {filename}:\n{traceback.format_exc()}\n\n{inst}')
                text=''
        return text

    def button_edit_custom_action(self):
        self.edit_dlg = Custom_Top(self.custom_top_items)
        self.edit_dlg.close=lambda: self.edit_dlg.done(0)
        self.edit_dlg.exec()

        self.edit_dlg.close()
        self.setCustomTops()
        self.combo_custom_top_preset()
        self.combo_top_action()
        return 
    
    def setCustomTops(self):
        self.PROpar_customs=[]
        self.custom_top_items=setCustomList(lambda var,name: self.PROpar_customs.append(var))

#******************** Settings 
    def combo_custom_top_preset(self):
        custom_list=[self.ui.combo_custom_top.itemText(i) for i in range(self.ui.combo_custom_top.count())]
        if custom_list!=self.custom_top_items:
            self.ui.combo_custom_top.clear()
            self.ui.combo_custom_top.addItems(self.custom_top_items) 
    
    def combo_custom_top_set(self):
        self.ui.combo_custom_top.setCurrentIndex(self.combo_custom_top_ind())
    
    def combo_custom_top_ind(self):
        if self.PROpar.custom_top_name in self.custom_top_items:
            ind=self.custom_top_items.index(self.PROpar.custom_top_name)
        else:
            ind=0
        return ind

#******************** Layout 
    def setPROlayout_ToP(self):
        #Type of process
        flagCustomTop=self.PROpar.top==0
        self.ui.w_custom_top.setVisible(flagCustomTop)
        if flagCustomTop:
            flagEn=bool(len(self.custom_top_items))
            if flagEn:
                self.ui.label_custom_top.setText('Custom types')
            else:
                self.ui.label_custom_top.setText('No custom types available')
            self.ui.combo_custom_top.setEnabled(flagEn)
            #self.ui.button_edit_custom.setEnabled(flagEn)
            if flagEn:
                i=-1
                fields=['name']+self.PROpar.FinalIt_fields+self.PROpar.Int_fields+self.PROpar.Validation_fields+self.PROpar.Wind_fields
                for k,p in enumerate(self.PROpar_customs):
                    if p.isEqualTo(self.PROpar,[],fields): i=k
                if i>-1:  
                    self.ui.combo_custom_top.setCurrentIndex(i)

#*************************************************** INTERPOLATION
#******************** Actions  
    def combo_ImInt_action_gen(self,par:str,w:QComboBox,p:QStackedWidget,ImInt_ind_list:list):
        ind_old=getattr(self.PROpar,par)
        if w.currentText()==ImInt_items[0]: #none
            ind=0
        elif w.currentText()==ImInt_items[4]: #Quad4Simplex
            ind=1
        elif w.currentText()==ImInt_items[1]: #Moving S, aS
            q=p.widget(1)
            qcombo:QComboBox=q.findChild(QComboBox)
            ind=qcombo.currentIndex()+3
        elif w.currentText()==ImInt_items[3]: #BiLinear, BiQuad, BiCubic, BiCubic Matlab
            q=p.widget(2)
            qcombo=q.findChild(QComboBox)
            indeff=(5,2,7,6)
            ind=indeff[qcombo.currentIndex()]
        elif w.currentText()==ImInt_items[2]: #Linear revitalized
            ind=10
        elif w.currentText()==ImInt_items[5]: #Shift
            q=p.widget(3)
            qspin:QSpinBox=q.findChild(QSpinBox)
            if ind_old>=23 and ind_old<=40:
                ind=qspin.value()+20
            else:
                ind=ImInt_ind_list[0]+20
        elif w.currentText()==ImInt_items[6]: #Sinc 
            q=p.widget(p.currentIndex())
            qspin=q.findChild(QSpinBox)
            if ind_old>=41 and ind_old<=50:
                ind=qspin.value()+40
            else:
                ind=ImInt_ind_list[1]+40
        elif w.currentText()==ImInt_items[7]: #BSpline
            q=p.widget(p.currentIndex())
            qspin=q.findChild(QSpinBox)
            if ind_old>=52 and ind_old<=70:
                ind=qspin.value()+50
            else:
                ind=ImInt_ind_list[2]+50
        setattr(self.PROpar,par,ind)
        return

    def button_more_iter_action(self):
        self.PROpar.FlagInt=1 if self.PROpar.FlagInt==0 else 0
    
    def spin_final_it_action(self):
        self.PROpar.FlagInt=self.ui.spin_final_it.value()

    def combo_int_vel_action_gen(self,par:str,w:QComboBox,p:QStackedWidget):
        for j in range(5):    
            if w.currentText()==VelInt_items[j]: #none
                indeff=(1,5,2,3,4)
                ind=indeff[j]
                break
        if w.currentText()==VelInt_items[5]: #BSpline
            q=p.widget(1)
            qspin:QSpinBox=q.findChild(QSpinBox) 
            ind=qspin.value()+50
        setattr(self.PROpar,par,ind)
        return

#******************** Settings                         
    def combo_ImInt_set_gen(self,par:str,w:QComboBox,p:QStackedWidget,ImInt_ind_list:list):
        ind=getattr(self.PROpar,par)
        if ind==0:
            w.setCurrentIndex(w.findText(ImInt_items[0])) #none #così se scelgo un nome diverso è automatico
            p.setCurrentIndex(0)
        elif ind==1: #Quad4Simplex
            w.setCurrentIndex(w.findText(ImInt_items[4]))
            p.setCurrentIndex(0)
        elif ind in (3,4): #Moving S, aS
            w.setCurrentIndex(w.findText(ImInt_items[1]))
            p.setCurrentIndex(1)
            q=p.widget(p.currentIndex())
            qcombo:QComboBox=q.findChild(QComboBox)
            qcombo.setCurrentIndex(ind-3)
        elif ind in (5,2,7,6): #BiLinear, BiQuad, BiCubic, BiCubic Matlab
            w.setCurrentIndex(w.findText(ImInt_items[3]))
            p.setCurrentIndex(2)
            q=p.widget(p.currentIndex())
            qcombo=q.findChild(QComboBox)
            indeff=(-1,-1,  1  ,-1,-1,  0,3,2)
            qcombo.setCurrentIndex(indeff[ind])
        elif ind==10: #Linear revitalized
            w.setCurrentIndex(w.findText(ImInt_items[2])) 
            p.setCurrentIndex(0)
        elif ind>=23 and ind<=40: #Shift
            w.setCurrentIndex(w.findText(ImInt_items[5]))
            p.setCurrentIndex(3)
            q=p.widget(p.currentIndex())
            qlabel:QLabel=q.findChild(QLabel)
            qlabel.setText('Kernel width')
            qspin:MyQSpin=q.findChild(MyQSpin)
            qspin.setMinimum(3)
            qspin.setMaximum(20)
            qspin.setValue(ind-20)
            ImInt_ind_list[0]=ind-20
        elif ind>=41 and ind<=50: #Sinc
            w.setCurrentIndex(w.findText(ImInt_items[6]))
            p.setCurrentIndex(3)
            q=p.widget(p.currentIndex())
            qlabel=q.findChild(QLabel)
            qlabel.setText('Kernel half-width')
            qspin=q.findChild(MyQSpin)
            qspin.setMinimum(1)
            qspin.setMaximum(10)
            qspin.setValue(ind-40)
            ImInt_ind_list[1]=ind-40
        elif ind>=52 and ind<=70: #BSpline
            w.setCurrentIndex(w.findText(ImInt_items[7]))
            p.setCurrentIndex(3)
            q=p.widget(p.currentIndex())
            qlabel=q.findChild(QLabel)
            qlabel.setText('Order (=Kernel width-1)')
            qspin=q.findChild(MyQSpin)
            qspin.setMinimum(2)
            qspin.setMaximum(20) 
            qspin.setValue(ind-50)
            ImInt_ind_list[2]=ind-50
    
    def spin_final_it_set(self):
        self.ui.spin_final_it.setValue(self.PROpar.FlagInt)

    def combo_int_vel_set_gen(self,par:str,w:QComboBox,p:QStackedWidget):
        ind=getattr(self.PROpar,par)
        if ind>=1 and ind<=5:
            indeff=(-1,  0,2,3,4,1)
            w.setCurrentIndex(w.findText(VelInt_items[indeff[ind]])) #così se scelgo un nome diverso è automatico
            p.setCurrentIndex(0)
        elif ind>=52 and ind<=70: #BSpline
            w.setCurrentIndex(w.findText(VelInt_items[5]))
            p.setCurrentIndex(1)
            q=p.widget(p.currentIndex())
            qspin:QSpinBox=q.findChild(QSpinBox)
            qspin.setMinimum(2)
            qspin.setMaximum(20)   
            qspin.setValue(ind-50)
  
#******************** Layout    
    def setPROlayout_Int(self):
        max_it=len(self.PROpar.Vect[0])+self.PROpar.NIterazioni
        if max_it==1:
            self.ui.button_more_iter.hide()
        else:
            self.ui.label_max_it.setText("of " +str(max_it)+ " iterations")
            self.ui.button_more_iter.show()
        if self.PROpar.FlagInt:
            self.ui.button_more_iter.setIcon(self.icon_minus)
            self.ui.w_ImInt_2.show()
            self.ui.w_ImInt_par_2.show()
        else:
            self.ui.button_more_iter.setIcon(self.icon_plus)
            self.ui.w_ImInt_2.hide()
            self.ui.w_ImInt_par_2.hide()
    
#*************************************************** VALIDATION
#******************** Actions  
    def radio_MedTest_action(self):
        if self.ui.radio_MedTest.isChecked():
            self.PROpar.FlagNogTest=0
    
    def radio_SNTest_action(self):
        if self.ui.radio_SNTest.isChecked():
            self.PROpar.FlagNogTest=0
    
    def radio_CPTest_action(self):
        if self.ui.radio_CPTest.isChecked():
            self.PROpar.FlagNogTest=0

    def radio_Nogueira_action(self):
        if self.ui.radio_Nogueira.isChecked():
            self.PROpar.FlagMedTest=0
            self.PROpar.FlagSNTest=0
            self.PROpar.FlagCPTest=0

#******************** Settings
    def combo_TypeMed_set(self):
        self.ui.w_MedTest_eps.setVisible(self.PROpar.TypeMed==1 and self.PROpar.FlagMedTest)

#******************** Layout  
    def setPROlayout_Valid(self):
        self.showMedTestwid()
        self.showSNTestwid()
        self.showCPTestwid()
        self.showNogTestwid()

    def showMedTestwid(self):
        self.ui.label_MedTest_box.setVisible(self.PROpar.FlagMedTest)
        self.ui.w_MedTest_type.setVisible(self.PROpar.FlagMedTest)
        self.ui.w_MedTest_ker.setVisible(self.PROpar.FlagMedTest)
        self.ui.w_MedTest_alfa.setVisible(self.PROpar.FlagMedTest)
        self.ui.w_MedTest_jump.setVisible(self.PROpar.FlagMedTest)
        self.ui.w_MedTest_eps.setVisible(self.PROpar.TypeMed==1 and self.PROpar.FlagMedTest)

    def showSNTestwid(self):
        self.ui.label_SNTest.setVisible(self.PROpar.FlagSNTest)
        self.ui.w_SNTest_thres.setVisible(self.PROpar.FlagSNTest)

    def showCPTestwid(self):
        self.ui.label_CPTest.setVisible(self.PROpar.FlagCPTest)
        self.ui.w_CPTest_thres.setVisible(self.PROpar.FlagCPTest)

    def showNogTestwid(self):
        self.ui.label_Nogueira.setVisible(self.PROpar.FlagNogTest)
        self.ui.w_Nog_tol.setVisible(self.PROpar.FlagNogTest)
        self.ui.w_Nog_numvec.setVisible(self.PROpar.FlagNogTest)

#*************************************************** WINDOWING
#******************** Actions
    def combo_Wind_Vel_action_gen(self,par:str,w:QComboBox,p:QStackedWidget):
        if w.currentText()==Wind_items[0]:     # top-hat/rectangular
            q=p.widget(1)
            qcombo:QComboBox=q.findChild(QComboBox)
            indeff=(0,3,4)
            ind=indeff[qcombo.currentIndex()]
        elif w.currentText()==Wind_items[1]:   # Nogueira
            q=p.widget(2)
            qcombo=q.findChild(QComboBox)
            indeff=(1,21)
            ind=indeff[qcombo.currentIndex()]
        elif w.currentText()==Wind_items[2]:   # Blackman
            """
            #Blackman options
            q=p.widget(3)
            qcombo=q.findChild(QComboBox)
            indeff=(5,2,6)
            ind=indeff[qcombo.currentIndex()]
            """
            ind=2
        elif w.currentText()==Wind_items[3]:   # Blackman-Harris
            q=p.widget(4)
            qcombo=q.findChild(QComboBox)
            indeff=(7,8,9,10)
            ind=indeff[qcombo.currentIndex()]
        elif w.currentText()==Wind_items[4]:   # Triangular
            ind=22
        elif w.currentText()==Wind_items[5]:   # Hann
            ind=23
        elif w.currentText()==Wind_items[6]:   # Gaussian
            q=p.widget(5)
            qspin:MyQDoubleSpin=q.findChild(MyQDoubleSpin)
            ind=int(qspin.value()*10+100)
        setattr(self.PROpar,par,ind)
        if w.objectName()=='combo_Wind_Corr_type':
            self.PROpar.vFlagWindowing[self.PROpar.row]=self.PROpar.FlagWindowing
            self.PROpar.col=1
        else:
            self.PROpar.vFlagCalcVel[self.PROpar.row]=self.PROpar.FlagCalcVel
            self.PROpar.col=2
        return
     
    def spin_Wind_halfwidth_action(self):
        self.PROpar.SemiDimCalcVel=self.ui.spin_Wind_halfwidth.value()
        self.PROpar.vSemiDimCalcVel[self.PROpar.row]=self.PROpar.SemiDimCalcVel
        self.PROpar.col=2

    def combo_MaxDisp_type_action(self):
        ind=self.ui.combo_MaxDisp_type.currentIndex()
        k=min([self.PROpar.row,self.PROpar.Nit-1])
        if self.PROpar.MaxDisp<0 and ind==1: 
            self.PROpar.MaxDisp=int(1/(-self.PROpar.MaxDisp)*min( [self.PROpar.Vect[0][k], self.PROpar.Vect[2][k]] ))
        elif self.PROpar.MaxDisp>0 and ind==0:
            maxDisp=round(min( [self.PROpar.Vect[0][k], self.PROpar.Vect[2][k]] )/self.PROpar.MaxDisp)
            if maxDisp in [2,3,4,5]:
                self.PROpar.MaxDisp=-maxDisp
            elif maxDisp<2:
                self.PROpar.MaxDisp=-2
            else:
                self.PROpar.MaxDisp=-5
        self.PROpar.vMaxDisp[self.PROpar.row]=self.PROpar.MaxDisp
        self.PROpar.col=3
    
    def combo_MaxDisp_action(self):
        ind=self.ui.combo_MaxDisp_type.currentIndex()
        if ind: 
            self.PROpar.MaxDisp=self.ui.spin_MaxDisp_absolute.value()
        else:
            self.PROpar.MaxDisp=-[2,3,4,5][self.ui.combo_MaxDisp_relative.currentIndex()]
        self.PROpar.vMaxDisp[self.PROpar.row]=self.PROpar.MaxDisp
        self.PROpar.col=3

    def check_DC_it_action(self):
        self.PROpar.vDC[self.PROpar.row]=int(self.ui.check_DC_it.isChecked())
        self.PROpar.col=4

    def radio_Adaptative_action(self):
        self.PROpar.NIterazioni=minNIterAdaptative if self.PROpar.NIterazioni<minNIterAdaptative else self.PROpar.NIterazioni

    def spin_LarMin_changing(self):
        if self.PROpar.FlagAdaptative and self.PROpar.row==self.PROpar.Nit-1:
            self.ui.spin_Wind_halfwidth.setValue(self.ui.spin_LarMin.value())

    def line_edit_IW_action(self):
        text=self.ui.line_edit_IW.text()
        split_text=re.split(r'(\d+)', text)[1:-1:2]
        vect=[int(split_text[i]) for i in (0,2,1,3)]
        if len(vect)==4:
            k=self.PROpar.row
            FlagValid=True
            if k>0: FlagValid=FlagValid and all([vect[i]<=self.PROpar.Vect[i][k-1] for i in range(4)])
            if k<self.PROpar.Nit-1 and FlagValid: FlagValid=FlagValid and all([vect[i]>=self.PROpar.Vect[i][k+1] for i in range(4)])
            if FlagValid:
                for i in range(4):
                    self.PROpar.Vect[i][k]=vect[i] #np.array([vect[i]])
            else:
                message='IW sizes o r spacings were assigned inconsistently! Please, retry!'
                showTip(self,message)
        self.PROpar.flag_rect_wind=any([v!=w for v,w in zip(self.PROpar.Vect[0],self.PROpar.Vect[2])]) or any([v!=w for v,w in zip(self.PROpar.Vect[1],self.PROpar.Vect[3])])
        return
    
    def line_edit_IW_addfuncin(self):
        k=self.PROpar.row
        label=[]
        if k<self.PROpar.Nit-1:
            label.append('min. = ['+",".join([str(self.PROpar.Vect[i][k+1]) for i in (0,2,1,3)])+']')
        if k>0: 
            label.append('max. = ['+",".join([str(self.PROpar.Vect[i][k-1]) for i in (0,2,1,3)])+']')
        if label: label=',   '.join(label)
        else: label='Select arbitrary sizes and spacings'
        rowInfo=self.ui.table_iter.RowInfo[self.PROpar.row]
        tip="<br>".join([label,rowInfo])
        self.ui.table_iter.InfoLabel.setText(tip)

    def table_iter_action(self):
        self.PROpar.row=self.ui.table_iter.currentRow()
        self.PROpar.col=self.ui.table_iter.currentColumn()
        pri.Callback.green(f'{"*"*10}   Table selection: r={self.PROpar.row}, c={self.PROpar.col}')

    def tableContextMenuEvent(self, table_iter:QTableWidget, event):
        item=table_iter.currentItem()
        if not item: return
        menu=QMenu(table_iter)
        buttons=['add', 'delete']
        name=[]
        tips=['Add new iteration to the PIV process','Delete current iteration from the PIV process']
        act=[]
        fun=[]
        for k,nb in enumerate(buttons):
            if type(nb)==str:
                b:QPushButton=getattr(self.ui,'button_'+nb)
                if b.isVisible() and b.isEnabled():
                    if hasattr(self,'button_'+nb+'_callback'):
                        name.append(nb)
                        act.append(QAction(b.icon(),toPlainText(b.toolTip().split('.')[0]),table_iter))
                        menu.addAction(act[-1])
                        callback=getattr(self,'button_'+nb+'_callback')
                        fcallback=self.addParWrapper(callback,tips[k])
                        fun.append(fcallback)
            else:
                if len(act): menu.addSeparator()

        if len(act):
            pri.Callback.yellow(f'||| Opening image list context menu |||')
            action = menu.exec_(table_iter.mapToGlobal(event.pos()))
            for nb,a,f in zip(name,act,fun):
                if a==action: 
                    f()
                    break
        else:
            toolTip=item.toolTip()
            item.setToolTip('')
            item.setStatusTip('')

            message='No context menu available! Please, pause processing.'
            toolTipDuration=self.toolTipDuration()
            self.setToolTipDuration(3000)
            QToolTip.showText(QCursor.pos(),message)
            self.setToolTipDuration(toolTipDuration)
            item.setToolTip(toolTip)
            item.setStatusTip(toolTip)

    def button_mtf_action(self):
        self.fig_MTF, self.ax_MTF= plt.subplots()
        self.ax_MTF.grid()
        line_NIt=self.ax_MTF.plot(self.MTF[0],self.MTF[1][:,0],color='k',label=f'{self.PROpar.NIterazioni+1:d} iterations')
        line_inf=self.ax_MTF.plot(self.MTF[0],self.MTF[1][:,1],color='r',linestyle='--',label='∞ iterations')
        lgnd=self.ax_MTF.legend(loc='lower right')
        self.ax_MTF.set(xlim=(1, np.max(self.MTF[0])),ylim=(-.30, 1.1))
        self.ax_MTF.set_title(self.MTF[2])
        self.ax_MTF.set_xlabel("wavelength (pixels)")
        self.ax_MTF.set_ylabel("Modulation Transfer Function (MTF)")
        
        self.ax_MTF.grid(which='minor', linestyle='-', alpha=0.25)       
        self.ax_MTF.minorticks_on()
        
        if self.MTF[3]:
            def forward(x):
                return x/self.MTF[3]
            def inverse(x):
                return x*self.MTF[3]

            secax = self.ax_MTF.secondary_xaxis('top', functions=(forward, inverse))
            secax.set_xlabel('wavelength (mm)')
            addTexts=[secax.xaxis.label]+secax.get_xticklabels()
        else:
            addTexts=[]

        for item in ([self.ax_MTF.title, self.ax_MTF.xaxis.label, self.ax_MTF.yaxis.label] +self.ax_MTF.get_xticklabels() + self.ax_MTF.get_yticklabels()+addTexts+lgnd.get_texts()):
                item.set_fontsize(self.font().pixelSize())
        self.fig_MTF.tight_layout()

        self.gui.setEnabled(False)
        self.fig_MTF.canvas.mpl_connect('close_event', lambda e: self.gui.setEnabled(True))
        self.fig_MTF.canvas.manager.set_window_title('Modulation Transfer Function')
        self.fig_MTF.canvas.manager.window.setWindowIcon(self.windowIcon())
        self.fig_MTF.show()
        return

    def button_add_action(self):
        k=self.PROpar.row
        for i in range(4):
            self.PROpar.Vect[i].insert(k,self.PROpar.Vect[i][k])  #=np.insert(self.PROpar.Vect[i],k,self.PROpar.Vect[i][k].copy())
        self.PROpar.Nit+=1
        fields=['vFlagCalcVel','vFlagWindowing','vSemiDimCalcVel','vDC','vMaxDisp']
        for f in fields:
            v=getattr(self.PROpar,f)
            v.insert(k,v[k])
        self.PROpar.row=k+1
    
    def button_delete_action(self):
        k=self.PROpar.row
        if k<self.PROpar.Nit:
            for i in range(4):
                self.PROpar.Vect[i].pop(k) #=np.delete(self.PROpar.Vect[i],k)
            self.PROpar.Nit-=1
            fields=['vFlagCalcVel','vFlagWindowing','vSemiDimCalcVel','vDC','vMaxDisp']
            for f in fields:
                v=getattr(self.PROpar,f)
                v.pop(k)
            self.PROpar.row=k-1
        else:
            self.PROpar.FlagAdaptative=0

#******************** Settings
    def combo_Wind_Vel_set_gen(self,par:str,w:QComboBox,p:QStackedWidget):
        ind=getattr(self.PROpar,par)
        if Flag_type_of_DCs:
            if w.objectName()=='combo_Wind_Corr_type':
                if w.currentText()==Wind_items[0]: 
                    self.ui.w_type_of_DCs.hide()
                else: 
                    self.ui.w_type_of_DCs.show()
        if ind in (0,3,4):          # top-hat
            w.setCurrentIndex(w.findText(Wind_items[0]))
            p.setCurrentIndex(1)
            p.show()
            q=p.widget(p.currentIndex())
            qcombo:QComboBox=q.findChild(QComboBox)
            indeff=(0, -1,-1, 1, 2)
            qcombo.setCurrentIndex(indeff[ind])
        elif ind in (1,21):         # Nogueira
            w.setCurrentIndex(w.findText(Wind_items[1]))
            p.setCurrentIndex(2)
            p.show()
            q=p.widget(p.currentIndex())
            qcombo=q.findChild(QComboBox)
            if ind==1:
                qcombo.setCurrentIndex(0)
            else:
                qcombo.setCurrentIndex(1)
        elif ind in (5,2,6):        # Blackman
            w.setCurrentIndex(w.findText(Wind_items[2]))
            p.hide()
            """
            #Blackman options
            p.setCurrentIndex(3)
            q=p.widget(p.currentIndex())
            qcombo=q.findChild(QComboBox)
            indeff=(-1,-1, 1, -1,-1, 0,2)
            qcombo.setCurrentIndex(indeff[ind])
            """
        elif ind in (7,8,9,10):     # Blackman-Harris
            w.setCurrentIndex(w.findText(Wind_items[3]))
            p.setCurrentIndex(4)
            p.show()
            q=p.widget(p.currentIndex())
            qcombo=q.findChild(QComboBox)
            qcombo.setCurrentIndex(ind-7)
        elif ind==22:               # Triangular
            w.setCurrentIndex(w.findText(Wind_items[4]))
            p.hide()
        elif ind==23:               # Hann
            w.setCurrentIndex(w.findText(Wind_items[5]))
            p.hide()
        elif ind>100 and ind<=200: #Gaussian
            w.setCurrentIndex(w.findText(Wind_items[6]))
            p.setCurrentIndex(5)
            p.show()
            q=p.widget(p.currentIndex())
            qspin:MyQDoubleSpin=q.findChild(MyQDoubleSpin)
            qspin.setValue(float(ind-100)/10)       
   
    def combo_Wind_Vel_acr_optionText(self,ind):
        optionText=''
        if ind in (0,3,4):          # top-hat
            acr=Wind_abbrev[0]
            optionText+=Wind_items[0]
            qcombo=self.ui.combo_par_tophat
            indeff=(0, -1,-1, 1, 2)
            optionText+=f' [{qcombo.itemText(indeff[ind])}]'
        elif ind in (1,21):
            acr=Wind_abbrev[1]
            optionText+=Wind_items[1]
            qcombo=self.ui.combo_par_Nog
            if ind==1: optionText+=f' [{qcombo.itemText(0)}]'
            else: optionText+=f' [{qcombo.itemText(1)}]'
        elif ind in (5,2,6):
            acr=Wind_abbrev[2]
            optionText+=Wind_items[2]
        elif ind in (7,8,9,10):     # Blackman-Harris
            acr=Wind_abbrev[3]
            optionText+=Wind_items[3]
            qcombo=self.ui.combo_par_Har
            optionText+=f' [{qcombo.itemText(ind-7)}]'
        elif ind==22:               # Triangular
            acr=Wind_abbrev[4]
            optionText+=Wind_items[4]
        elif ind==23:               # Hann
            acr=Wind_abbrev[5]
            optionText+=Wind_items[5]
        elif ind>100 and ind<=200: #Gaussian
            acr=Wind_abbrev[6]
            optionText+=Wind_items[6]
            alpha=float(ind-100)/10
            optionText+=f' [α thresh.={alpha}]'
        return acr,optionText

    def spin_Wind_halfwidth_set(self):
        self.ui.spin_Wind_halfwidth.setValue(self.PROpar.SemiDimCalcVel)

    def combo_MaxDisp_type_set(self):
        ind=0 if self.PROpar.MaxDisp<0 else 1
        self.ui.combo_MaxDisp_type.setCurrentIndex(ind)
        self.ui.w_MaxDisp_par.setCurrentIndex(ind)
        if not ind: 
            ind_rel=[2,3,4,5].index(-self.PROpar.MaxDisp)
            self.ui.combo_MaxDisp_relative.setCurrentIndex(ind_rel)
        else:
            k=min([self.PROpar.row,self.PROpar.Nit-1])
            maxVal=int( 0.5*min( [self.PROpar.Vect[0][k], self.PROpar.Vect[2][k]] ) )
            self.ui.spin_MaxDisp_absolute.setMaximum(maxVal)
            self.PROpar.MaxDisp=self.PROpar.vMaxDisp[self.PROpar.row]=maxVal if self.PROpar.MaxDisp>maxVal else self.PROpar.MaxDisp
            self.ui.spin_MaxDisp_absolute.setValue(self.PROpar.MaxDisp)

    def spin_MaxC_preset(self):
        self.ui.spin_MaxC.setMinimum(self.PROpar.MinC+0.01)
        
    def spin_MinC_preset(self):
        self.ui.spin_MinC.setMaximum(self.PROpar.MaxC-0.01)
        
    def spin_LarMax_preset(self):
        self.ui.spin_LarMax.setMinimum(self.PROpar.LarMin+1)
        
    def spin_LarMin_preset(self):
        self.ui.spin_LarMin.setMaximum(self.PROpar.LarMax-1)
    
    def line_edit_IW_set(self):
        r=self.PROpar.row
        #c=self.PROpar.col

        kVect=min([r,self.PROpar.Nit-1])
        vect=[f'{self.PROpar.Vect[i][kVect]}' for i in (0,2,1,3)]
        vectStr=', '.join(vect)
        self.ui.line_edit_IW.setText(vectStr)
    
    def table_iter_set(self):
        nRow=self.ui.table_iter.rowCount()
        for k in range(len(self.PROpar.vFlagCalcVel),nRow):
            self.ui.table_iter.removeRow(self.ui.table_iter.rowAt(k))

        nWind=len(self.PROpar.vFlagCalcVel)
        Nit=self.PROpar.Nit
        NIterazioni=self.PROpar.NIterazioni
        self.ui.table_iter.RowInfo=['']*nWind

        flagFocus=not self.ui.line_edit_IW.hasFocus()

        def genTableCell(item_name,tooltip,c,cc):
            if c<0: return cc
            item=QTableWidgetItem(item_name)
            item.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setToolTip(tooltip)
            item.setStatusTip(tooltip)
            cc+=1
            self.ui.table_iter.setItem(c, cc, item)
            if self.PROpar.row==c and self.PROpar.col==cc: 
                item.setSelected(True)
                self.ui.table_iter.setCurrentItem(item)
            return cc

        for k in range(nWind):
            if k==self.ui.table_iter.rowCount():
                self.ui.table_iter.insertRow(k)
            c=k
            cc=-1

            it=k-Nit+1
            if k==Nit-1 and it!=NIterazioni:
                item_name=f'{it}:{NIterazioni}'
                tooltip=f'iterations from {it} to {NIterazioni}'
                str_adapt=''
            elif k==Nit:
                item_name=f'{NIterazioni+1}:{NIterazioni+self.PROpar.NItAdaptative}'
                tooltip=f'iterations from {NIterazioni+1} to {NIterazioni+self.PROpar.NItAdaptative}'   
                str_adapt=' (adaptative)'
            else:
                item_name=f'{it}'
                tooltip=f'iteration {it}'
                str_adapt=''
            kVect=min([k,self.PROpar.Nit-1])
            IWSize=f'{self.PROpar.Vect[0][kVect]} x {self.PROpar.Vect[2][kVect]}'
            IWSize_max=max([self.PROpar.Vect[0][kVect],self.PROpar.Vect[2][kVect]])
            IWSpac=f'{self.PROpar.Vect[1][kVect]} x {self.PROpar.Vect[3][kVect]}'
            self.ui.table_iter.RowInfo[k]=f'{item_name}   Window size: {IWSize},   grid distance: {IWSpac}'+str_adapt
            
            cc=genTableCell(item_name,tooltip,c,cc)
            
            """
            item_name=IWSize
            tooltip=f'Window size: {IWSize}'
            cc=genTableCell(item_name,tooltip,c,cc)

            item_name=IWSpac
            tooltip=f'Window size: {IWSize}'
            cc=genTableCell(item_name,tooltip,c,cc)
            """

            acr,optionText=self.combo_Wind_Vel_acr_optionText(self.PROpar.vFlagWindowing[k])
            item_name=CorrWin=f'{acr}{IWSize_max:d}'
            tooltip=f'{optionText} window'
            cc=genTableCell(item_name,tooltip,c,cc)

            acr,optionText=self.combo_Wind_Vel_acr_optionText(self.PROpar.vFlagCalcVel[k])
            if k==Nit:
                CorrWinWidth0=self.PROpar.vSemiDimCalcVel[k-1]*2+IWSize_max%2 if self.PROpar.vSemiDimCalcVel[k-1] else IWSize_max
                CorrWinWidth1=self.PROpar.vSemiDimCalcVel[k]*2+IWSize_max%2 if self.PROpar.vSemiDimCalcVel[k] else IWSize_max
                item_name=f'{acr}{CorrWinWidth0:d}-{CorrWinWidth1:d}'
                tooltip=f'{optionText} window; half-width = {self.PROpar.vSemiDimCalcVel[k-1]:d}-{self.PROpar.vSemiDimCalcVel[k]:d}'
            else:
                CorrWinWidth=self.PROpar.vSemiDimCalcVel[k]*2+IWSize_max%2 if self.PROpar.vSemiDimCalcVel[k] else IWSize_max
                item_name=VelWin=f'{acr}{CorrWinWidth:d}'
                tooltip=f'{optionText} window; size = {CorrWinWidth:d}'
            cc=genTableCell(item_name,tooltip,c,cc)

            maxDisp=self.PROpar.vMaxDisp[k]
            if maxDisp<0:
                item_name=f'1/{-maxDisp:d} IW'
                tooltip=f'Maximum allowed displacement = 1/{-maxDisp:d} of the interrogation window size'
            else:
                item_name=f'{maxDisp} pix'
                tooltip=f'Maximum allowed displacement = {maxDisp:d} pixels'
            cc=genTableCell(item_name,tooltip,c,cc)

            item_name=f'{"❌✅"[self.PROpar.vDC[k]]}'
            tooltip=f'Direct correlations: {["disactivated","activated"][self.PROpar.vDC[k]]}'
            cc=genTableCell(item_name,tooltip,c,cc)

            item_name, tooltip=self.calcStability(k,VelWin,CorrWin)
            if k==Nit-1: item_name+='⭐'
            cc=genTableCell(item_name,tooltip,c,cc)

            continue

    def calcStability(self,k,VelWin,CorrWin):
        kVect=min([k,self.PROpar.Nit-1])
        FlagStable=True
        flagLambda=True
        #FlagIntVel=(self.PROpar.IntVel==1) or (52<=self.PROpar.IntVel<=70)
        #if FlagIntVel:
        for j in range(2):
            Niter=np.array([self.PROpar.NIterazioni, np.inf])
            nPointPlot=1000
            # A  correlation window
            Wa=self.PROpar.Vect[j*2][kVect]
            WBase=1.5*Wa
            FlagWindowing=self.PROpar.vFlagWindowing[k] # Weighting window for the correlation map (0=TopHat 1= Nogueira 2=Blackman 3=top hat at 50#).
            # B  weighted  average
            FlagCalcVel=self.PROpar.vFlagCalcVel[k]   # Weighting window for absolute velocity (0=TopHat, 1=Nogueira, 2=Blackman,...)
            hWb=self.PROpar.vSemiDimCalcVel[k]# Half-width of the filtering window (0=window dimension).
            # C dense predictor 
            IntVel=self.PROpar.IntVel  # Type of interpolation of the velocity (1=bilinear, 52-70 Bspline)
            Wc=self.PROpar.Vect[1+j*2][kVect]#  Grid distance (overlap)
            #   end input *********************************************
            oMax=0.5 # frequenza massima per c (legata all'overlap ov/lambda) non penso che abbia senso oltre 0,5 perchè 
                    # andremmo oltre Nyquist
            
            (_,_,_,_,_,_,_,_,_,flagUnstable,_,lam,MTF,_,_,_)= mtfPIV1(Wa,FlagWindowing,hWb, FlagCalcVel,Wc, IntVel, oMax, WBase,nPointPlot,Niter,flagLambda)
            FlagStable=FlagStable and not flagUnstable
            if k==self.PROpar.Nit-1:
                if j==0:
                    if self.father and hasattr(self.father,'w_Export'): Res=self.father.w_Export.OUTpar.xres
                    else: Res=0
                    self.MTF=[lam,MTF.T,f'IW size-spacing: {Wa:d}-{Wc:d}.   Vel.-correl. windowing: {VelWin}-{CorrWin}.',Res]
                    
                else:
                    if self.PROpar.Vect[j*2][kVect]>self.PROpar.Vect[(j-1)*2][kVect]:
                        if self.father: Res=self.father.w_Export.OUTpar.xres*self.father.w_Export.OUTpar.pixAR
                        else: Res=0
                        self.MTF=[lam,MTF.T,f'IW size-spacing: {Wa:d}-{Wc:d}.   Vel.-correl. windowing: {VelWin}-{CorrWin}.',Res]
        if FlagStable:
            name='stable'
            tooltip='Stable process through an infinite number of iterations'
        else:
            name='⚠ unstable'
            tooltip='Unstable process through an infinite number of iterations'
        #else:
        #    name='-'
        #    tooltip='No information on stability available'
        return name, tooltip

#******************** Layout
    def setPROlayout_Wind(self):
        self.ui.w_adaptative_iter.setVisible(self.PROpar.FlagAdaptative)
        self.ui.w_Adaptative.setVisible(self.PROpar.FlagAdaptative)

        self.ui.table_iter.resizeInfoLabel()
        r=self.PROpar.row
        #c=self.PROpar.col
        self.ui.button_mtf.setVisible(r==self.PROpar.Nit-1)
        
        FlagAdaptativeNotSelected=self.PROpar.row<self.PROpar.Nit
        self.ui.edit_IW.setEnabled(FlagAdaptativeNotSelected)
        self.ui.button_add.setEnabled(FlagAdaptativeNotSelected)
        FlagDeleteEnabled=(FlagAdaptativeNotSelected and self.PROpar.Nit>1) or self.PROpar.row>=self.PROpar.Nit
        self.ui.button_delete.setEnabled(FlagDeleteEnabled)

        self.ui.combo_Wind_Vel_type.setEnabled(FlagAdaptativeNotSelected)
        self.ui.w_Wind_par.setEnabled(FlagAdaptativeNotSelected)
        self.ui.combo_Wind_Corr_type.setEnabled(FlagAdaptativeNotSelected)
        self.ui.w_Wind_par_2.setEnabled(FlagAdaptativeNotSelected)
        self.ui.spin_Wind_halfwidth.setEnabled(FlagAdaptativeNotSelected and not(self.PROpar.FlagAdaptative and self.PROpar.row==self.PROpar.Nit-1))
        self.ui.combo_MaxDisp_type.setEnabled(FlagAdaptativeNotSelected)
        self.ui.combo_MaxDisp_relative.setEnabled(FlagAdaptativeNotSelected)
        self.ui.spin_MaxDisp_absolute.setEnabled(FlagAdaptativeNotSelected)
        self.ui.check_DC_it.setEnabled(FlagAdaptativeNotSelected and self.PROpar.FlagDirectCorr)
        self.ui.w_Adaptative.setVisible(self.PROpar.FlagAdaptative)
        self.ui.w_adaptative_iter.setVisible(self.PROpar.FlagAdaptative)
        
        nWind=len(self.PROpar.vFlagCalcVel)
        self.ui.table_iter.setMinimumHeight((nWind+1)*22)
        self.ui.table_iter.setMaximumHeight((nWind+1)*22)
        self.ui.CollapBox_Windowing.heightArea=(nWind+1)*22+200
        self.ui.CollapBox_Windowing.heightOpened=self.ui.CollapBox_Windowing.heightArea+20
        self.ui.CollapBox_Windowing.on_click()
        return
    

if __name__ == "__main__":
    import sys
    app=QApplication.instance()
    if not app:app = QApplication(sys.argv)
    app.setStyle('Fusion')
    object = Process_Tab(None)
    object.show()
    app.exec()
    app.quit()
    app=None

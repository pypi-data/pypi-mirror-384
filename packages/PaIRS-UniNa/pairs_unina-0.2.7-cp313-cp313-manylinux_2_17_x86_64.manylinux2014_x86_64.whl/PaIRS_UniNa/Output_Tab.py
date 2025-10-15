from .ui_Output_Tab import*
from .TabTools import *

outType_dict={
    '.mat': 'binary (.mat)',
     '.plt': 'tecplot (.plt)', 
    #'tecplot (ASCII)':  '.plt',
}
outType_items=[outType_dict[i] for i in outType_dict]

spin_tips={
    'x'  :  'First column of image area to process',
    'y'  :  'First row of image',
    'w'  :  'Width of image area to process',
    'h'  :  'Height of image area to process',
    'xres' :  'Image resolution along X',
    'pixAR' :  'Image resolution along Y',
    'dt'    :  'Time delay between frames',
    'x_min' :   'Minimum x world coordinate',
    'x_max' :   'Maximum x world coordinate',
    'y_min' :   'Minimum y world coordinate',
    'y_max' :   'Maximum y world coordinate',
    'zconst' :  'Laser plane equation constant',
    'xterm'  :  'Laser plane equation x-slope',
    'yterm'  :  'Laser plane equation y-slope',
}
button_tips={
    'rot_counter'    :  'Counterclockwise rotation of image',  
    'rot_clock'      :  'Clockwise rotation of image',
    'mirror_x'       :  'Horizontal mirroring of image',
    'mirror_y'       :  'Vertical mirroring of image',
    'rotv_counter'   :  'Counterclockwise rotation of velocity field',
    'rotv_clock'     :  'Clockwise rotation of velocity field',
    'flip_u'         :  'Flip of velocity vectors along X',
    'flip_v'         :  'Flip of velocity vectors along Y',
    'reset_rot_flip' :  'Reset of rotations and mirroring/flip',
    'path'           :  'Output folder path',
    'resize'         :  'Reset of image sizes',
    'tool_CollapBox_Flip'   : 'Graphics',
    'CollapBox_Flip'        : 'Graphics',
    'unit'           :  'Type of resolution unit',
    'def_reg'        :  'Reset sizes of area to process',
    'automatic_reshape' : 'Automatic resize/reshape',
    'read_disp'      : 'Read .clz file',
}
radio_tips={
    'Save'          :  'Save results',
    'Same_as_input' :  'Output folder path same as input',
    'Subfold'       :  'Create subfolder',
}
check_tips={}
line_edit_tips={
    'root'          :  'Root of output files',
    'path'          :  'Output folder path',
    'subfold'       :  'Output subfolder path',
}
combo_tips={
    'process'      :  'Type of process',
    'outType'  :  'Type of output files',
}

class OUTpar(TABpar):
    FlagAutoReshape   = True

    def __init__(self,Process=ProcessTypes.null,Step=StepTypes.null):
        self.setup(Process,Step)
        super().__init__('OUTpar','Output')
        self.OptionDone=0
        self.unchecked_fields+=['FlagAutoReshape','OptionValidPath','OptionValidSubFold','OptionValidRoot']

    def setup(self,Process,Step):
        self.Process            = Process
        self.Step               = Step
        self.FlagProc           = self.Process!=StepTypes.min
        self.FlagCalib          = self.Process not in ProcessTypes.singleCamera
        
        self.FlagSave    		= True 
        self.root        		= 'out'   
        self.OptionValidRoot    = 1                
        self.outType     		= 0       
        self.FlagSame_as_input  = True    
        self.path        		= basefold
        self.inputPath        	= basefold                         
        self.OptionValidPath  	= 1         

        self.FlagSubfold 		= True                  
        self.subfold     		= 'out_PaIRS/'  
        self.userSubfold     	= self.subfold 
        self.OptionValidSubFold = 1      

        self.imageFile          = None
        self.imageFileMin       = None
        self.OptionValidMin     = 1
        self.x           		= 0                
        self.y           		= 0                 
        self.w           		= 1                 
        self.h           		= 1                  
        self.W           		= 1                
        self.H           		= 1    

        self.aimop        		= [0]
        self.bimop        		= [0]
        self.vecop        		= [0]   

        self.xres        		= float(1.000)                   
        self.pixAR       		= float(1.000)                     
        self.dt          		= float(1000)   
        self.unit               = False #Step not in (StepTypes.disp,StepTypes.spiv)
        self.res                = float(0.0)

        self.def_reg             = [float(-20), float(20), float(-20), float(20)]
        self.x_min              = float(-50)
        self.x_max              = float(+50)
        self.y_min              = float(-50)
        self.y_max              = float(+50)
        self.FlagWarnCR         = False
        self.warnCR             = ''

        self.zconst         = 0.0
        self.xterm          = 0.0
        self.yterm          = 0.0
        self.FlagDISP       = Step==StepTypes.disp
        
class Output_Tab(gPaIRS_Tab):
    class Export_Tab_signals(gPaIRS_Tab.Tab_Signals):
        pass

    def __init__(self,parent: QWidget =None, flagInit= __name__ == "__main__"):
        super().__init__(parent,Ui_OutputTab,OUTpar)
        self.signals=self.Export_Tab_signals(self)

        #------------------------------------- Graphical interface: widgets
        self.TABname='Output'
        self.ui: Ui_OutputTab
        ui=self.ui
        ui.spin_x.addwid=[ui.spin_w]
        ui.spin_y.addwid=[ui.spin_h]
        ui.combo_outType.clear()
        for item in outType_dict.values():
            ui.combo_outType.addItem(item)

        #necessary to change the name and the order of the items
        for g in list(globals()):
            if '_items' in g or '_ord' in g or '_tips' in g:
                #pri.Info.blue(f'Adding {g} to {self.name_tab}')
                setattr(self,g,eval(g))

        if __name__ == "__main__": 
            self.app=app
            setAppGuiPalette(self)

        #------------------------------------- Graphical interface: miscellanea
        self.pixmap_x  = QPixmap(''+ icons_path +'redx.png')
        self.pixmap_v  = QPixmap(''+ icons_path +'greenv.png')
        self.pixmap_wait  = QPixmap(''+ icons_path +'sandglass.png')
        self.pixmap_warn  = QPixmap(u""+ icons_path +"warning.png")

        self.aim_qtim=ImageQt(''+ icons_path +'axes.png')
        self.bim_qtim=ImageQt(''+ icons_path +'background.png')
        self.vim_qtim=ImageQt(''+ icons_path +'background_vectors.png')


        self.aim_qtim=ImageQt(''+ icons_path +'axes.png')
        self.bim_qtim=ImageQt(''+ icons_path +'background.png')
        self.vim_qtim=ImageQt(''+ icons_path +'background_vectors.png')
        self.image_labels=[None,ImageQt(''+ icons_path +'rotate_counter.png'),
                           ImageQt(''+ icons_path +'mirror_x.png'),ImageQt(''+ icons_path +'mirror_y.png'),
                           ImageQt(''+ icons_path +'rotate_clock.png')]
        self.velocity_labels=[None,ImageQt(''+ icons_path +'rotate_v_counter.png'),
                           ImageQt(''+ icons_path +'mirror_u.png'),ImageQt(''+ icons_path +'mirror_v.png'),
                           ImageQt(''+ icons_path +'rotate_v_clock.png')]

        aim,bim,vim=self.getQPixmap()
        self.ui.aim.setPixmap(aim)  
        self.ui.aim_2.setPixmap(aim) 
        self.ui.aim_3.setPixmap(aim) 
        self.ui.bim.setPixmap(vim)  
        self.ui.bim_2.setPixmap(bim) 
        self.ui.bim_3.setPixmap(vim) 
        
        self.rotate_counter = QTransform().rotate(-90)
        self.rotate_clock   = QTransform().rotate(+90)
        self.mirror_x       = QTransform().scale(1,-1)
        self.mirror_y       = QTransform().scale(-1,1)     

        self.CollapBox_Flip_height=self.ui.CollapBox_Flip.minimumHeight()
        self.w_Flip_Image_height=self.ui.w_Flip_Image.minimumHeight()  

        #self.ui.label_WarnCR.setPixmap( self.pixmap_warn )

        #------------------------------------- Declaration of parameters 
        self.OUTpar_base=OUTpar()
        self.OUTpar:OUTpar=self.TABpar
        self.OUTpar_old:OUTpar=self.TABpar_old

        #------------------------------------- Callbacks
        self.defineWidgets()
        self.setupWid()  #---------------- IMPORTANT
        
        #self.defineActions()
        self.defineReshapeButtonActions()
        self.ui.spin_xres.valueChanged.connect(lambda v: self.resLabelLayout())
        self.ui.spin_pixAR.valueChanged.connect(lambda v:self.resLabelLayout())
        self.ui.spin_dt.valueChanged.connect(lambda v: self.resLabelLayout())

        self.defineCallbacks()
        self.connectCallbacks()
        #self.defineAdditionalCallbacks()

        #self.defineSet()
        self.defineSettings()

        self.adjustTABpar=self.adjustOUTpar
        self.setTABlayout=self.setOUTlayout
        self.checkTABpar=self.checkOUTpar
        self.setTABwarn=self.setOUTwarn

        #------------------------------------- Initializing 
        if flagInit:
            self.initialize()
        #else:
        #    self.setTABpar(FlagBridge=False)          
                 
    def initialize(self):
        pri.Info.yellow(f'{"*"*20}   OUTPUT initialization   {"*"*20}')
        self.OUTpar.Process = ProcessTypes.piv
        self.OUTpar.w=self.OUTpar.h=self.OUTpar.W=self.OUTpar.H=1000
        self.setTABpar(FlagBridge=False)

#*************************************************** Rotation and flip
    def getQPixmap(self):
        aim=QPixmap.fromImage(self.aim_qtim)
        bim=QPixmap.fromImage(self.bim_qtim)
        vim=QPixmap.fromImage(self.vim_qtim)
        return aim, bim, vim

    def RotMirror(self,addop):
        if addop[0]!=0:
            self.OUTpar.aimop=self.OUTpar.aimop+[addop[0]]
            Itransf=np.eye(2,2)
            Itransf=self.imTransf_op2I(Itransf,self.OUTpar.aimop,False)
            self.OUTpar.aimop=self.imTransf_I2op(Itransf)
        if addop[1]!=0:
            self.OUTpar.bimop=self.OUTpar.bimop+[addop[1]]
            Itransf=np.eye(2,2)
            Itransf=self.imTransf_op2I(Itransf,self.OUTpar.bimop,False)
            self.OUTpar.bimop=self.imTransf_I2op(Itransf)
        self.OUTpar.vecop=self.OUTpar.bimop+self.OUTpar.aimop
        Itransf=np.eye(2,2)
        Itransf=self.imTransf_op2I(Itransf,self.OUTpar.vecop,False)
        self.OUTpar.vecop=self.imTransf_I2op(Itransf)           
                  
    def RotMirror_Pixmaps(self):
        #aim_qtim,bim_qtim,aim_rot,bim_rot,v_rot,vmat_rot = self.allocateQPixmap()
        _,bim_rot,vim_rot = self.getQPixmap()
        opList=[self.OUTpar.bimop,self.OUTpar.vecop]
        labList=[self.ui.bim_2,self.ui.bim_3]
        imList=[bim_rot,vim_rot]

        for ops,lab,im in zip(opList,labList,imList):
            for _,op in enumerate(ops):
                if op==1:
                    im=im.transformed(self.rotate_counter)
                elif op==-1:
                    im=im.transformed(self.rotate_clock)
                elif op==3:
                    im=im.transformed(self.mirror_x)
                elif op==2:
                    im=im.transformed(self.mirror_y)
            geom=lab.geometry()
            geom.setWidth(im.width())
            geom.setHeight(im.height())
            geom.setY(lab.parentWidget().maximumHeight()-im.height()-5)
            lab.setMinimumSize(im.width(),im.height())
            lab.setMaximumSize (im.width(),im.height())
            lab.setGeometry(geom)
            lab.setPixmap(im) 
            
        opList=[self.OUTpar.bimop,self.OUTpar.aimop]
        imageList=[self.image_labels,self.velocity_labels]
        nList=[2,3]
        for ops,image_labels,n in zip(opList,imageList,nList):
            cont=0
            for k,op in enumerate(ops):
                if op:
                    cont+=1
                    lab:QLabel=getattr(self.ui,f'lab_op{k+1}_{n}')
                    lab.setPixmap(QPixmap.fromImage(image_labels[op]))
            for j in range(cont,3):
                lab:QLabel=getattr(self.ui,f'lab_op{j+1}_{n}')
                lab.setPixmap(QPixmap())
            if cont:
                getattr(self.ui,f'lab_op{0}_{n}').hide()
            else:
                getattr(self.ui,f'lab_op{0}_{n}').show()
        return 

    def imTransf_op2I(self,I,op,flagInv):
        for i in range(len(op)):
            if op[i]==1:   #rotation counter
                I=self.matRot90(I.copy(),flagInv)
            elif op[i]==-1:  #clock
                I=self.matRot90(I.copy(), not flagInv)
            elif op[i]==3 or op[i]==2:  
                I=self.matMirror(I.copy(),op[i]-2)
        return I
            
    def matRot90(self,I,flagInv):
        #RH =(I[0,0]==I[1,1]) and (I[0,1]==-I[1,0])
        #if not RH: flagInv= not flagInv
        if not flagInv:  #direct counter
            a=I[0:np.size(I,0),0].copy()
            I[0:np.size(I,0),0]=-I[0:np.size(I,0),1]
            I[0:np.size(I,0),1]=+a   
        else:
            a=I[0:np.size(I,0),0].copy()
            I[0:np.size(I,0),0]=+I[0:np.size(I,0),1]
            I[0:np.size(I,0),1]=-a    
        return I

    def matMirror(self,I,ind):
        #ind=1 mirror_x, ind=0 mirror_y 
        I[0:np.size(I,0),ind]=-I[0:np.size(I,0),ind]
        return I
            
    def imTransf_I2op(self,I):
        op=[0]
        RHim= I[0,0]==I[1,1] and I[1,0]==-I[0,1]
        if RHim:
            if I[0,0]==1: op=[0]
            elif I[0,0]==-1: op=[1,1]
            elif I[0,1]==1: op=[1]
            elif I[0,1]==-1: op=[-1]
        else:
            if I[0,0]==1: op=[3]
            elif I[0,0]==-1: op=[2]
            elif I[0,1]==1: op=[1,2]
            elif I[0,1]==-1: op=[1,3]
        return op

    def defineReshapeButtonActions(self):
        self.button_rot_counter_action=lambda:  self.RotMirror([0,1])
        self.button_rot_clock_action=lambda: self.RotMirror([0,-1])
        self.button_mirror_x_action=lambda: self.RotMirror([0,3])
        self.button_mirror_y_action=lambda: self.RotMirror([0,2])
        self.button_rotv_counter_action=lambda: self.RotMirror([1,0])
        self.button_rotv_clock_action=lambda: self.RotMirror([-1,0])
        self.button_flip_v_action=lambda: self.RotMirror([3,0])
        self.button_flip_u_action=lambda: self.RotMirror([2,0,2])
    
    def button_reset_rot_flip_action(self):
        self.OUTpar.aimop=[0]
        self.OUTpar.bimop=[0]
        self.OUTpar.vecop=[0]
        self.RotMirror([-2,-2,-2])

    def button_automatic_reshape_action(self):
        OUTpar.FlagAutoReshape=self.ui.button_automatic_reshape.isChecked()
        return True
    
    def button_automatic_reshape_set(self):
        self.ui.button_automatic_reshape.setChecked(OUTpar.FlagAutoReshape)
        return True
    
#*************************************************** Adjusting parameters
    def adjustOUTpar(self):
        self.OUTpar.FlagProc=self.OUTpar.Process!=ProcessTypes.min
        self.OUTpar.FlagCalib=self.OUTpar.Process not in ProcessTypes.singleCamera
        if self.OUTpar.FlagSame_as_input: self.OUTpar.path=self.OUTpar.inputPath
        
        self.OUTpar.path=myStandardPath(self.OUTpar.path)
        if self.OUTpar.FlagSubfold:
            self.OUTpar.subfold=myStandardPath(self.OUTpar.subfold)
            self.OUTpar.userSubfold=self.OUTpar.subfold
        else:
            self.OUTpar.subfold=''
        #else:
        #    self.OUTpar.subfold=''
        self.OUTpar.root=myStandardRoot(self.OUTpar.root)

        if self.OUTpar.imageFile: self.OUTpar.W,self.OUTpar.H=self.get_image_dimensions(self.OUTpar.inputPath+self.OUTpar.imageFile)
        if (self.OUTpar.isDifferentFrom(self.OUTpar_old,fields=['W','H','inputPath']) and self.OUTpar.ind[:-1]==self.OUTpar_old.ind[:-1] and OUTpar.FlagAutoReshape) or (self.OUTpar_old.imageFile is None and self.OUTpar.W>0 and self.OUTpar.H>0):
            self.button_resize_action()
            self.button_reset_rot_flip_action()

        #if self.OUTpar.isDifferentFrom(self.OUTpar_old,fields=['x_min','x_max','y_min','y_max']) or not self.OUTpar.FlagInit:
        if self.OUTpar.Step in (StepTypes.disp,StepTypes.spiv):
            if self.OUTpar.unit: self.OUTpar.xres=float(1)
            else: self.OUTpar.xres=self.OUTpar.res

        self.checkOUTpar()
        return

    def checkOUTpar(self,ind=None):
        if ind is None: OUT:OUTpar=self.OUTpar
        else: OUT:OUTpar=self.TABpar_at(ind)
        self.setOptionValidPath(ind)
        self.setOptionValidSubFold(ind)
        self.setOptionValidRoot(ind)
        self.checkMinCompatibility(ind)
        self.checkCommonRegion(ind)
        OUT.OptionDone=1 if OUT.OptionValidPath==1 and OUT.OptionValidSubFold in (1,-1) and OUT.OptionValidRoot==1 and OUT.OptionValidMin==1 and not OUT.FlagWarnCR else 0 if OUT.OptionValidPath==0 or OUT.OptionValidSubFold==0 or OUT.OptionValidRoot in (0,-1) or OUT.OptionValidMin==0 or OUT.FlagWarnCR else -1
        #pri.Info.blue(f'Output OptionDone = {OUT.OptionDone}')

    def get_image_dimensions(self,file_name):        
        try:
            # Attempt to open the image file
            with Image.open(file_name) as img:
                # Get image dimensions
                width, height = img.size
                return [width,height]
        except IOError:
            # Handle the case where the file is not a valid image
            return [0,0]
    
    def checkMinCompatibility(self,ind):
        if ind is None:
            OUT:OUTpar=self.OUTpar
            ind=OUT.ind
        else: OUT:OUTpar=self.TABpar_at(ind)

        if  OUT.Step!=StepTypes.min and OUT.imageFile is not None and OUT.imageFileMin is not None and self.get_image_dimensions(OUT.inputPath+OUT.imageFile)!=self.get_image_dimensions(OUT.imageFileMin):
            OUT.OptionValidMin=0
        else:
            OUT.OptionValidMin=1

    def checkCommonRegion(self,ind=None):
        if ind is None:
            OUT:OUTpar=self.OUTpar
            if OUT.Step==StepTypes.disp:
                PRO=self.gui.w_Process_Disp.PROpar
            elif OUT.Step in (StepTypes.piv,StepTypes.spiv):
                PRO=self.gui.w_Process.PROpar
            else:
                PRO=None
            ind=OUT.ind
        else: 
            OUT:OUTpar=self.TABpar_at(ind)
            if OUT.Step==StepTypes.disp:
                PRO=self.gui.w_Process_Disp.TABpar_at(ind)
            elif OUT.Step in (StepTypes.piv,StepTypes.spiv):
                PRO=self.gui.w_Process.TABpar_at(ind)
            else:
                PRO=None

        OUT.FlagWarnCR=False
        OUT.warnCR=''
        if OUT.Step==StepTypes.piv:
            errorString=''
            Vect=[v[0] for v in PRO.Vect]
            
            nMin=2
            W=OUT.w
            H=OUT.h
            DueDistBordoW=Vect[2] if not PRO.FlagBordo else Vect[3]*2
            DueDistBordoH=Vect[0] if not PRO.FlagBordo else Vect[1]*2
            DX=W-DueDistBordoW
            DY=H-DueDistBordoH
            #if W*0.5<Vect[2] or H*0.5<Vect[0]:
            #    errorString='Processing image region too small to accommodate the selected interrogation windows! Expand the processing image region or reduce the size of the interrogation windows. The size of the interrogation window should not exceed the half of the image size in order to have at least 2 vectors in the x and/ y directions.'
            if int(DX/Vect[3])<nMin-1 or int(DY/Vect[1])<nMin-1:
                errorString=f'Processing image region is too small to contain at least {nMin} vectors in the x and/or y direction! Expand the processing image region or decrease the spacing of the interrogation windows! Please also notice that the "First vector at ↓" flag in the Interrogation window box of the Process tab determines the number of vectors in the computed fields.'
            pass
            if errorString:
                errorString='Issue with processing region! ' + errorString
                pri.Callback.white(errorString)
                OUT.FlagWarnCR=True
                OUT.warnCR=errorString
        elif OUT.Step in (StepTypes.disp,StepTypes.spiv):
            if hasattr(self.gui,'ui') and hasattr(self.gui.ui,'Explorer'):
                OUT.res=0.0
                from .procTools import dataTreePar, data2Disp, data2StereoPIV
                procdata:dataTreePar=self.gui.ui.Explorer.ITEfromInd(OUT.ind).procdata
                data=procdata.duplicate()
                data.Process=procdata.Process
                data.Step=procdata.Step
                INP_ind=self.gui.w_Input.TABpar_at(ind)
                OUT_ind=OUT #self.gui.w_Output.TABpar_at(ind)
                PRO_ind=self.gui.w_Process.TABpar_at(ind)
                PRO_Min_ind=self.gui.w_Process_Min.TABpar_at(ind)
                PRO_Disp_ind=self.gui.w_Process_Disp.TABpar_at(ind)
                data.setProc(INP_ind,OUT_ind,PRO_ind,PRO_Min_ind,PRO_Disp_ind)
                try:
                    errorString='Error while setting camera calibration parameters! Check if calibration files are not correctly specified or are missing.'
                    if OUT.Step==StepTypes.disp: disp=data2Disp(data)
                    elif OUT.Step==StepTypes.spiv: disp=data2StereoPIV(data)
                    errorString='Error while setting the laser plane equation constants!'
                    ve=disp.vect
                    ve.PianoLaser[0]=np.float32(OUT.zconst)
                    ve.PianoLaser[1]=np.float32(OUT.xterm)
                    ve.PianoLaser[2]=np.float32(OUT.yterm)
                    errorString='Invalid common region'
                    disp.evalCommonZone()
                    errorString='Common region incompatible with selected interrogation windows!'
                    OUT.res=1./disp.dataProc.RisxRadd
                    if OUT.Step==StepTypes.disp:
                        Vect=PRO.Vect
                        nMin=4
                        FlagBordo=False
                    else:
                        Vect=[v[0] for v in PRO.Vect]
                        nMin=2
                        FlagBordo=PRO.FlagBordo

                    w=OUT.x_max-OUT.x_min
                    h=OUT.y_max-OUT.y_min
                    W=w/disp.dataProc.RisxRadd
                    H=h/disp.dataProc.RisxRadd

                    DueDistBordoW=Vect[2] if not FlagBordo else Vect[3]*2
                    DueDistBordoH=Vect[0] if not FlagBordo else Vect[1]*2
                    DX=W-DueDistBordoW
                    DY=H-DueDistBordoH

                    #if W*0.5<Vect[2] or H*0.5<Vect[0]:
                    #    errorString='Common region too small to accommodate the selected interrogation windows! Expand the common region or reduce the size of the interrogation windows. The size of the interrogation window should not exceed the half of the image size in order to have at least 2 vectors in the x and/ y directions.'
                    #    raise('Common region/IW incompatibility issue')
                    if int(DX/Vect[3])<nMin-1 or int(DY/Vect[1])<nMin-1:
                        errorString=f'Common region is too small to contain at least {nMin-1 if OUT.Step==StepTypes.disp else nMin} vectors in the x and/or y direction! Expand the common region or decrease the spacing of the interrogation windows. Please also notice that the "First vector at ↓" flag in the Interrogation window box of the Process tab determines the number of vectors in the computed fields.'
                        raise('Common region/IW incompatibility issue')
                    pass
                except Exception as exc:
                    if errorString=='Invalid common region':
                        pattern = r'\*+ Error(.*?) \*+'
                        matches = re.findall(pattern, str(exc))
                        for m,ma in enumerate(matches):
                            matches[m]=ma.replace('camera 1','camera 2').replace('camera 0','camera 1')
                        if matches:
                            errorString+=':\n-'+'\n-'.join(matches)
                    if errorString=='Common region incompatible with selected interrogation windows!':
                        pri.Error.red(f'{errorString}\n{traceback.format_exc()}\n\n')
                        pass
                    errorString='Issue with physical region! ' + errorString
                    pri.Callback.white(errorString)
                    OUT.FlagWarnCR=True
                    OUT.warnCR=errorString
                if not self.OUTpar.unit: OUT.xres=OUT.res
        
#*************************************************** Layout
    def setOUTlayout(self):
        self.ui.label_process.setVisible(__name__ == "__main__")
        self.ui.combo_process.setVisible(__name__ == "__main__")

        self.ui.w_combo_outType.setVisible(self.OUTpar.FlagProc and self.OUTpar.Step!=StepTypes.min)
        FlagValidProc=self.OUTpar.FlagProc and self.OUTpar.imageFile is not None
        self.ui.w_FurtherOptions.setVisible(FlagValidProc and self.OUTpar.Step!=StepTypes.min)
        if FlagValidProc:
            self.ui.w_Flip_Mirror.setVisible(not self.OUTpar.FlagCalib)

            height=self.w_Flip_Image_height-self.ui.w_Flip_Mirror.minimumHeight()*int(self.OUTpar.FlagCalib)
            self.ui.w_Flip_Image.setMinimumHeight(height)
            self.ui.w_Flip_Image.setMaximumHeight(height)
            height=self.CollapBox_Flip_height-self.ui.w_Flip_Mirror.minimumHeight()*int(self.OUTpar.FlagCalib)
            #self.ui.CollapBox_Flip.setMinimumHeight(height)
            #self.ui.CollapBox_Flip.setMaximumHeight(height)
            self.ui.CollapBox_Flip.heightOpened=height
            self.ui.CollapBox_Flip.heightArea=height-self.ui.CollapBox_Flip.toolHeight
            self.ui.CollapBox_Flip.on_click()
            #self.ui.w_Flip_Image.setEnabled(self.OUTpar.FlagDone)
            
            self.setMinMaxSpinxywh()
            self.RotMirror_Pixmaps()
            self.resLabelLayout()
        
        """
        if self.OUTpar.Step==StepTypes.disp:
            self.ui.w_Resolution.setVisible(False)
        else:
            self.ui.w_Resolution.setVisible(True)
        """
        self.ui.w_Resolution.setVisible(True)
        self.ui.w_dt.setVisible(self.OUTpar.Step!=StepTypes.disp)
        self.ui.w_Res_eff.setVisible(self.OUTpar.Step!=StepTypes.disp)
        self.ui.button_unit.setVisible(self.OUTpar.FlagCalib)
        self.ui.button_unit.setEnabled(self.OUTpar.Step!=StepTypes.disp)
        self.ui.spin_xres.setEnabled(not self.OUTpar.FlagCalib)
        self.ui.w_y_Resolution.setVisible(not self.OUTpar.FlagCalib)
        self.ui.label_x_res.setText('Resolution' if self.OUTpar.FlagCalib else 'X resolution')

        self.ui.g_CommonRegion.setVisible(self.OUTpar.FlagCalib)
        self.ui.button_def_reg.setVisible(False)  
        self.ui.label_WarnCR.setVisible(self.OUTpar.FlagWarnCR)
        #self.check_def_reg()

        self.ui.g_laser_plane_eq.setVisible(self.OUTpar.Step in (StepTypes.disp,StepTypes.spiv))
        self.ui.g_laser_plane_eq.setEnabled(not self.OUTpar.FlagDISP or self.OUTpar.Step==StepTypes.disp)

        self.ui.w_SaveResults.setVisible(self.OUTpar.FlagSave)
        self.ui.w_OutputFold_Button.setVisible(self.OUTpar.FlagSave)
        self.ui.w_OutputSubfold.setVisible(self.OUTpar.FlagSave)
        self.ui.label_path.setEnabled(not self.OUTpar.FlagSame_as_input)
        self.ui.w_edit_path.setEnabled(not self.OUTpar.FlagSame_as_input)
        self.ui.w_button_path.setEnabled(not self.OUTpar.FlagSame_as_input)
        self.ui.w_OutputSubfold_name.setVisible(self.OUTpar.FlagSubfold)

        self.setRootLabel()
        self.setPathLabel()
        self.setSubFoldLabel()

        self.checkOUTpar()
        self.setOUTwarn()
        self.setTABWarnLabel()
        self.ui.label_WarnCR.setToolTip(self.OUTpar.warnCR)
        self.ui.label_WarnCR.setStatusTip(self.ui.label_WarnCR.toolTip())
        return

    def setOUTwarn(self,ind=None):
        if ind is None: OUT:OUTpar=self.OUTpar
        else: OUT:OUTpar=self.TABpar_at(ind)

        if OUT.OptionDone==1:
            OUT.warningMessage='Output paths correctly identified!'
        else:
            warningMessage=''
            if not OUT.OptionValidPath: 
                warningMessage+=self.setPathLabel(ind)
            if not OUT.OptionValidSubFold: 
                if warningMessage: warningMessage+='\n*  '
                warningMessage+=self.setSubFoldLabel(ind)
            if not OUT.OptionValidRoot==1: 
                if warningMessage: warningMessage+='\n*  '
                warningMessage+=self.setRootLabel(ind)
            if not OUT.OptionValidMin==1: 
                if warningMessage: warningMessage+='\n*  '
                warningMessage+='Sizes of historical minimum background image incompatible with current image set!'
            if OUT.FlagWarnCR: 
                if warningMessage: warningMessage+='\n*  '
                warningMessage+=OUT.warnCR
            if '\n*  ' in warningMessage: warningMessage='*  '+warningMessage
            OUT.warningMessage=warningMessage

#*************************************************** Mode
#******************** Actions
    def combo_process_action(self):
        current_ind=self.ui.combo_process.currentIndex()
        self.OUTpar.Process=list(process)[current_ind]

#******************** Set
    def combo_process_set(self):
        current_proc=process[self.OUTpar.Process]
        self.ui.combo_process.setCurrentIndex(process_items.index(current_proc))

#*************************************************** Resolution
#******************** Actions      
    def button_unit_action(self):
        self.OUTpar.unit=self.ui.button_unit.isChecked()

#******************** Settings         
    def button_unit_set(self):   
        self.ui.button_unit.setChecked(self.OUTpar.unit)
        if not self.OUTpar.unit:
            text='Physical units'
        else:
            text='Pixel units'
        self.ui.button_unit.setText(text)

#******************** Layout   
    def resLabelLayout(self,FlagSet=False):
        dt=self.OUTpar.dt if FlagSet else self.ui.spin_dt.value()
        xres=self.OUTpar.xres if FlagSet else self.ui.spin_xres.value()
        #xres=max([xres,0.0000001])
        if self.OUTpar.Process==ProcessTypes.piv:
            
            pixAR=self.OUTpar.pixAR if FlagSet else self.ui.spin_pixAR.value()
            
            Velx=float(1000/(xres*dt)) if xres else None
            Vely=float(Velx/pixAR) if xres else None
            self.ui.label_Res_x.setText(f"X: {Velx:.6g} m/s" if Velx else "X: -")
            self.ui.label_Res_y.setText(f"Y: {Vely:.6g} m/s" if Vely else "Y: -")
        else:
            Velx=float(1000/(xres*dt)) if xres else None
            self.ui.label_Res_x.setText(f"   {Velx:.6g} m/s" if Velx else f"   -")
            self.ui.label_Res_y.setText(f"")
        adjustFont(self.ui.label_Res_x)
        adjustFont(self.ui.label_Res_y)

#*************************************************** Common Region
#******************** Actions      
    def button_def_reg_action(self):
        self.OUTpar.x_min=self.OUTpar.def_reg[0]
        self.OUTpar.x_max=self.OUTpar.def_reg[1]
        self.OUTpar.y_min=self.OUTpar.def_reg[2]
        self.OUTpar.y_max=self.OUTpar.def_reg[3]

#******************** Layout
    def check_def_reg(self):
        FlagHidden=self.OUTpar.x_min==self.OUTpar.def_reg[0] and self.OUTpar.x_max==self.OUTpar.def_reg[1] and self.OUTpar.y_min==self.OUTpar.def_reg[2] and self.OUTpar.y_max==self.OUTpar.def_reg[3]  
        self.ui.button_def_reg.setVisible(not FlagHidden)    

#*************************************************** Laser Plane constants
#******************** Actions      
    def button_read_disp_action(self):
        dispName, _ = QFileDialog.getOpenFileName(self,\
            "Select a laser plane equation file", filter=f'*.clz',\
                dir=self.OUTpar.inputPath,\
                options=optionNativeDialog)
        if not dispName: return
        if os.path.exists(dispName):
            PianoLaser=self.readLaserPlaneConst(dispName)
            self.OUTpar.zconst=PianoLaser[0]
            self.OUTpar.xterm=PianoLaser[1]
            self.OUTpar.yterm=PianoLaser[2]
        
    def readLaserPlaneConst(self, filename: str):
        try:
            with open(filename, "r") as cfg:
                lines = cfg.readlines()
                planeConst = [
                    float(lines[3].strip().rstrip(',')),
                    float(lines[4].strip().rstrip(',')),
                    float(lines[5].strip().rstrip(','))
                ]
                return planeConst
        
        except Exception as inst:
            errorPrint = f"\n!!!!!!!!!! Error while reading the file:\n{str(inst)}\n"
            return [0.0,0.0,0.0]
        
#*************************************************** Edit root
#******************** Actions
    def line_edit_root_changing(self):
         self.ui.label_check_root.setPixmap(QPixmap()) 
        
    def line_edit_root_preaction(self):
        entry=myStandardRoot(self.ui.line_edit_root.text())
        self.ui.line_edit_root.setText(entry)

#******************** Settings 
    def setRootLabel(self,ind=None):
        if ind is None: OUT:OUTpar=self.OUTpar
        else: OUT:OUTpar=self.TABpar_at(ind)
        #Clickable label: no need for setStatusTip
        if OUT.OptionValidRoot==-2:
            message="Files with the same root name already exist in the selected output folder!"
            pixmap=self.pixmap_warn
        elif OUT.OptionValidRoot==-1:
            pixmap=self.pixmap_warn
            message="It was not possible to create the specified output folder!"
        elif OUT.OptionValidRoot==0:
            pixmap=self.pixmap_x
            message="The root of the output filenames is not admitted!"
        if OUT.OptionValidRoot==1:
            pixmap=self.pixmap_v
            message="The root of the output filenames is admitted!"  
        if ind is None:
            self.ui.label_check_root.setPixmap(pixmap)
            self.ui.label_check_root.setToolTip(message)
        return message

#******************** Layout 
    def setOptionValidRoot(self,ind=None):
        if ind is None: OUT:OUTpar=self.OUTpar
        else: OUT:OUTpar=self.TABpar_at(ind)

        if OUT.Step == StepTypes.min:
            ext='_min.png'
        else:
            ext=list(outType_dict)[OUT.outType]
        FlagExistPath=False
        FlagCreateSubFold=False
        if OUT.OptionValidPath:
            currpath=myStandardPath(OUT.path)
            if OUT.OptionValidSubFold:
                currpath=myStandardPath(currpath+OUT.subfold)
                if OUT.OptionValidSubFold==1: FlagCreateSubFold=not os.path.exists(currpath)
                elif OUT.OptionValidSubFold==-1: FlagExistPath=True
        else:
            currpath='./'
        pattern=myStandardRoot(currpath+OUT.root)+'*'+ext
        FlagExist=False
        if FlagExistPath:
            files=findFiles_sorted(pattern)
            FlagExist=len(files)>0
        if  FlagExist: 
            OUT.OptionValidRoot=-2
        else:
            try:
                if FlagCreateSubFold:
                    os.mkdir(currpath)
                    FlagDeleteSubFold=True
                else:
                    FlagDeleteSubFold=False
            except:
                FlagDeleteSubFold=False
                OUT.OptionValidRoot=-1
            else:
                try:
                    filename=pattern.replace('*','a0')+'.delmeplease'
                    open(filename,'w')
                except:
                    FlagDeleteFile=False
                    OUT.OptionValidRoot=0
                else:
                    FlagDeleteFile=True
                    OUT.OptionValidRoot=1
                finally:
                    if FlagDeleteFile:
                        os.remove(filename)
            finally:
                if FlagDeleteSubFold:
                    os.rmdir(currpath)

#*************************************************** Edit path
#******************** Actions        
    def radio_Same_as_input_action(self):
        self.OUTpar.path=self.OUTpar.inputPath

    def line_edit_path_changing(self): 
         self.ui.label_check_path.setPixmap(QPixmap()) 

    def line_edit_path_preaction(self):
        currpath=myStandardPath(self.ui.line_edit_path.text())     
        directory_path = myStandardPath(os.getcwd())
        if directory_path in currpath:
            currpath=currpath.replace(directory_path,'./')         
        self.ui.line_edit_path.setText(currpath)

    def button_path_action(self):
        directory = str(QFileDialog.getExistingDirectory(self,\
            "Choose an output folder", dir=self.OUTpar.path,options=optionNativeDialog))
        currpath='{}'.format(directory)
        if not currpath=='':
            self.ui.line_edit_path.setText(currpath)
            self.line_edit_path_preaction()
            self.OUTpar.path=self.ui.line_edit_path.text()

#******************** Settings 
    def setPathLabel(self,ind=None):
        if ind is None: OUT:OUTpar=self.OUTpar
        else: OUT:OUTpar=self.TABpar_at(ind)
        #Clickable label: no need for setStatusTip
        if OUT.OptionValidPath:
            pixmap=self.pixmap_v
            message="The specified path of the output folder exists!"
        else:
            pixmap=self.pixmap_x
            message="The specified path of the output folder does not exist!"
        if ind is None:
            self.ui.label_check_path.setPixmap(pixmap)
            self.ui.label_check_path.setToolTip(message)
        return message
    
#******************** Layout        
    def setOptionValidPath(self,ind=None):
        if ind is None: OUT:OUTpar=self.OUTpar
        else: OUT:OUTpar=self.TABpar_at(ind)
        OUT.OptionValidPath=int(os.path.exists(OUT.path))

#*************************************************** Edit subfold
#******************** Actions
    def radio_Subfold_action(self):
        if not self.OUTpar.subfold and self.OUTpar.FlagSubfold:
            self.OUTpar.subfold=self.OUTpar.userSubfold

    def line_edit_subfold_changing(self): 
         self.ui.label_check_path_subfold.setPixmap(QPixmap()) 

    def line_edit_subfold_preaction(self):
        entry=myStandardPath(self.ui.line_edit_subfold.text())
        self.ui.line_edit_subfold.setText(entry)

    def line_edit_subfold_action(self):
        self.setOptionValidSubFold()
    
#******************** Settings   
    def setSubFoldLabel(self,ind=None):
        if ind is None: OUT:OUTpar=self.OUTpar
        else: OUT:OUTpar=self.TABpar_at(ind)

        """
        if OUT.OptionValidSubFold==-1:
            pixmap=self.pixmap_warn
            message="Current path already exists! 😰"
        """
        #Clickable label: no need for setStatusTip
        if OUT.OptionValidSubFold==0:
            pixmap=self.pixmap_x
            message="The specified path of the output subfolder is not admitted!"
        elif OUT.OptionValidSubFold in (-1,1):
            pixmap=self.pixmap_v
            message="The specified path of the output subfolder is admitted!"
        if ind is None:
            self.ui.label_check_path_subfold.setPixmap(pixmap)
            self.ui.label_check_path_subfold.setToolTip(message)
        return message


#******************** Layout        
    def setOptionValidSubFold(self,ind=None):
        if ind is None: OUT:OUTpar=self.OUTpar
        else: OUT:OUTpar=self.TABpar_at(ind)
        if OUT.OptionValidPath:
            currpath=myStandardPath(OUT.path)
        else:
            currpath='./'
        currpath=myStandardPath(currpath+OUT.subfold)
        if  OUT.OptionValidPath and os.path.exists(currpath):
            OUT.OptionValidSubFold=-1
        else:
            if OUT.flagRun>0 and not os.path.exists(currpath):
                OUT.OptionValidSubFold=0
            else:
                try:
                    os.mkdir(currpath)
                except:
                    FlagDeleteFolder=False
                    OUT.OptionValidSubFold=0
                else:
                    FlagDeleteFolder=True
                    OUT.OptionValidSubFold=1
                finally:
                    if FlagDeleteFolder:
                        os.rmdir(currpath)

if __name__ == "__main__":
    import sys
    app=QApplication.instance()
    if not app:app = QApplication(sys.argv)
    app.setStyle('Fusion')
    object = Output_Tab(None)
    object.show()
    app.exec()
    app.quit()
    app=None    
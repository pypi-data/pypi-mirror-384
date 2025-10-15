FLAG_SERIALIZED=True

import os, json, pickle, traceback
from .PaIRS_pypacks import pri

from .TabTools import TABpar
from .procTools import dataTreePar, CompMin, MediaPIV
from .Explorer import TREpar, ITEpar, currentTimeString
from .Input_Tab import INPpar
globals()['ImportPar'] = INPpar.ImportPar
from .Input_Tab_tools import ImageSet
from .Output_Tab import OUTpar
from .Process_Tab import PROpar
from .Log_Tab import LOGpar
from .Vis_Tab import VISpar, NamesPIV
globals()['OUT'] = VISpar.OUT
globals()['PRO'] = VISpar.PRO
from .Process_Tab_Min import PROpar_Min
from .Process_Tab_Disp import PROpar_Disp
from .Calibration_Tab import CALpar
from .Input_Tab_CalVi import INPpar_CalVi
from .Process_Tab_CalVi import PROpar_CalVi
from .Vis_Tab_CalVi import VISpar_CalVi
from .tabSplitter import SPLpar
from .PaIRS_pypacks import identifierName, fontPixelSize, printTypes
from .__init__ import __version__,__subversion__,__year__,__mail__,__website__

class GPApar(TABpar):
    def __init__(self):
        self.setup()
        super().__init__(self.name,'gPaIRS')
        self.unchecked_fields+=[]

    def setup(self):
        self.name_work, self.username, self.version = identifierName(typeObject='wksp')
        self.outName   = ''
        self.createdDate    = currentTimeString()
        self.modifiedDate   = self.createdDate
        self.savedDate      = ''
        self.FlagSaved      = False
        self.FlagQueue      = True
        self.FlagRunnable   = True

        self.name = 'Workspace'
        self.date = f'Created: {self.createdDate}'
        self.icon = 'workspace.png'

        self.infoFields=[f for f,_ in self.__dict__.items()]

        self.Geometry           = None
        self.WindowState        = None
        self.SplitterSizes      = {}
        self.ScrollAreaValues   = {}

        #legacy
        self.FloatGeometry      = []
        self.FloatVisible       = []

        self.paletteType        = 2   #-1,2=standard, 0=light, 1=dark
        self.fontPixelSize      = fontPixelSize
        self.FlagOutDated       = 0
        self.currentVersion     = __version__
        self.latestVersion      = ''

        self.printTypes         = printTypes
        self.NumCores           = 0

        self.stateFields=[f for f,_ in self.__dict__.items() if f not in self.infoFields]

    def saveBullet(self):
        return '' if self.FlagSaved else '<span style="color: #7A8B8B;"><sup>&#9679;</sup></span>'

    def InfoMessage(self):
        InfoMessage=f'{self.name}'
        if self.FlagSaved:
            InfoMessage+=f'\nFile location: {self.outName}'
        else:
            if self.savedDate: 
                InfoMessage+=' (unsaved)'
            else:
                InfoMessage+=' (never saved)'
        InfoMessage+=f'\n\nCreated : {self.createdDate}'
        InfoMessage+=f'\nModified: {self.modifiedDate}'
        if self.savedDate: InfoMessage+=f'\nSaved   : {self.savedDate}'
        InfoMessage+=f'\n\nUser: {self.username}'
        InfoMessage+=f'\nPaIRS version: {self.version}'
        return InfoMessage
 
def save_list_to_file_serialized(l, filename, flagJSON=False):
    basename = os.path.splitext(filename)[0]
    pickle_data = {}
    pickle_counter = 0
    info_pickle =[]

    def serialize_element(elem:TABpar, idx_path):
        nonlocal pickle_counter
        if elem is None:
            return None
        data = {}
        for field in elem.fields:
            value = getattr(elem, field)
            if isinstance(value, TABpar):
                data[field] = serialize_element(value, idx_path + [field])
            elif isinstance(value, CompMin) or isinstance(value, MediaPIV):
                data[field] = {'__file_ref__': value.outName,
                               'varClass':  value.__class__.__name__}
                if isinstance(value, MediaPIV):
                    data[field]['stepType']=value.stepType
                try:
                    if value.outName:
                        with open(value.outName, 'wb') as file:
                            pickle.dump(value, file)
                except Exception as e:
                    print(f'Error while saving the file {filename}!\n{e}\n')
            elif is_non_json_serializable(value):
                info=f'Element: {elem.__class__.__name__} --> field: {field} --> value type: {type(value)}'
                info_pickle.append(info)
                key = f"ref_{pickle_counter}"
                pickle_data[key] = value
                data[field] = {'__file_ref__': key}
                pickle_counter += 1
            else:
                data[field] = value
        data['parClass'] = elem.__class__.__name__
        return data
    
    def serialize_list(lst, idx_path=[]):
        if isinstance(lst, list):
            return [serialize_list(item, idx_path + [i]) for i, item in enumerate(lst)]
        else:
            return serialize_element(lst, idx_path)
    
    serialized_list = serialize_list(l)
    
    try:
        if flagJSON:
            with open(filename, 'w') as file:
                json.dump(serialized_list, file, indent=2)
        else:
            with open(filename, 'wb') as file:
                pickle.dump(serialized_list, file)
    except Exception as e:
        print(f'Error while saving the file {filename}!\n{e}\n')
        
    if pickle_counter:
        pri.IOError.yellow(f'The following non-json serializable items were found in {filename}:\n'+"\n".join(info_pickle))
        pickle_filename = basename+'.pairs_data'
        try:
            with open(pickle_filename, 'wb') as file:
                pickle.dump(pickle_data, file)
        except Exception as e:
            print(f'Error while saving the file {pickle_filename}!\n{e}\n')


def load_list_from_file_serialized(filename):
    basename = os.path.basename(filename)
    pickle_filename =  basename+'.pairs_data'
    
    serialized_list=None
    error=''
    try:
        with open(filename, 'rb') as file:
            first_byte = file.read(1)
            if first_byte in [b'{', b'[']:
                file.seek(0)
                try:
                    serialized_list=json.load(file)
                except Exception as e:
                    error=e
            else:
                file.seek(0)
                try:
                    import numpy 
                    serialized_list=pickle.load(file)
                except Exception as e:
                    error=e
    except Exception as e:
        error=e
    if error:
        pri.IOError.red(f'Error while loading the file {filename}!\n{error}\n')
        return serialized_list, str(error)
    
    error=''
    pickle_data = None
    if os.path.exists(pickle_filename):
        try:
            with open(pickle_filename, 'rb') as file:
                pickle_data = pickle.load(file)
        except Exception as e:
            pri.IOError.red(f'Error while loading the file {pickle_filename}!\n{e}\n')
            error+=str(e)

    info_pickle=[]

    def deserialize_element(data):
        if data is None:
            return None  
        try:  
            cls_name = data.pop('parClass')
        except:
            pass
        cls = globals()[cls_name]
        if cls_name=='dataTreePar':
            pass
        instance:TABpar = cls()
        fields  = {}
        for key, value in data.items():
            if isinstance(value, dict) and 'parClass' in value:
                fields[key] = deserialize_element(value)
            elif isinstance(value, dict) and 'varClass' in value:
                filename =  value['__file_ref__']
                field_cls_name = value['varClass']
                field_cls = globals()[field_cls_name]
                if field_cls==MediaPIV:
                    new_instance:MediaPIV=field_cls(value['stepType'])
                else:
                    new_instance:CompMin=field_cls()
                if filename:
                    try:
                        if os.path.exists(filename):
                            with open(filename, 'rb') as file:
                                loaded_instance:CompMin=pickle.load(file)
                            for f in loaded_instance.fields:
                                v_loaded=getattr(loaded_instance,f)
                                if isinstance(v_loaded,TABpar):
                                    v_new:TABpar=getattr(new_instance,f)
                                    v_new.copyfrom(v_loaded)
                                else:
                                    setattr(new_instance,f,v_loaded)
                    except Exception as e:
                        pri.IOError.red(f'Error while reading the file {filename} (setting "{key}" field of {cls_name} item)\n{traceback.format_exc()}\n')
                fields[key] = new_instance
            elif isinstance(value, dict) and '__file_ref__' in value:
                ref_key = value['__file_ref__']
                if pickle_data:
                    fields[key] = pickle_data[ref_key]
                else:
                    fields[key] = None
                    info=f'Element: {cls_name} --> field: {key} --> value type: {type(value)}'
                    info_pickle.append(info)
                    None
            else:
                fields[key] = value
        for f,v in fields.items():
            if f in instance.fields: setattr(instance,f,v)
        #instance.copyfromdiz(fields)
        return instance
    
    def deserialize_list(lst):
        if isinstance(lst, list):
            return [deserialize_list(item) for item in lst]
        else:
            return deserialize_element(lst)
    
    if info_pickle:
        pri.IOError.red(f'The following non-json serializable items were not found in {filename}:\n'+"\n".join(info_pickle))
    l=None
    try:
        l=deserialize_list(serialized_list)
    except Exception as e:
        pri.IOError.red(f'Error while loading the file {filename}!\n{e}\n{traceback.format_exc()}\n')
        error+=str(e)
    return l, error

def is_non_json_serializable(value):
    try:
        json.dumps(value)
        return False
    except (TypeError, OverflowError):
        return True
    

def save_list_to_file(l,filename):
    try:
        with open(filename, 'wb') as file:
            pickle.dump(l, file)
    except Exception as e:
        print(f'Error while saving the file {filename}!\n{e}\n')

def load_list_from_file(filename):
    l=None
    errorMessage=''
    try:
        with open(filename, 'rb') as file:
            l=pickle.load(file)
    except Exception as e:
        errorMessage=f'Error while loading the file {filename}!\n{e}\n'
        pri.IOError.red(errorMessage)
    return l, errorMessage

if FLAG_SERIALIZED:
    saveList=save_list_to_file_serialized
    loadList=load_list_from_file_serialized
else:
    saveList=save_list_to_file
    loadList=load_list_from_file

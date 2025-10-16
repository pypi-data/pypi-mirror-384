###default __init__ 
__version__='0.3.1' 

ADD_GEN=True
ADD_BK=True


from pathlib import Path
import sys
path = str(Path(Path(__file__).parent.absolute()).parent.absolute())
sys.path.insert(0, path)
 
  
 
from rdfobj.utils import *
from rdfobj.owl_modeler import ModelProcessor
from rdfobj.meta_model import TAttributeModel, TClassModel, ModelToolBox
from rdfobj.mapper import ModelPopulator,StoreClient 
from rdfobj.validation import *

if ADD_GEN==True:
   from rdfobj.code_generator import ModelCodeGenerator   

if ADD_BK==True:
   from rdfobj.graph_backend import *

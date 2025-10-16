
import os

import graphviz
import networkx as nx
from networkx.drawing.nx_agraph import write_dot
import pathlib
import rdflib
import sys,time,copy,json
import pydot
from xsdata.models.enums import DataType
from xsdata.models.enums import QNames
from xsdata.formats.converter import QNameConverter
from xsdata.utils.namespaces import build_qname
from rdflib.namespace import RDF

from jinja2 import Environment, FileSystemLoader, BaseLoader
 
import rdfextras
from urllib.parse import urldefrag
import textwrap
import importlib
import dill
import traceback
from io import StringIO
import csv

 
 

from SPARQLWrapper import SPARQLWrapper, JSON, POST, DIGEST
from rdflib import Namespace, Graph, URIRef,Literal
from rdflib.namespace import RDF, FOAF,XSD,split_uri

import logging 


from .utils import *

from .meta_model import *

logger = logging.getLogger(__name__) 

DO_LOG=False

def alert_err(msg):
    print(msg)

def active_log(act):
    
    global DO_LOG
    DO_LOG=act

def logger_info(msg,msg2=""):
    global DO_LOG
    if DO_LOG==True:
      logger.info(str(msg)+str(msg2))

def  normDom(doma):
    if doma.endswith('#'):
       doma = doma[:-1] 
    return doma

###utils to mock entities
class PK():
    def __init__(self,pk,cls=None,meta_label=None):
      self.pk = pk
      self.cls=cls
      self.pop_state=None
      self.exhausted=None
      self.meta_label=meta_label

    def __str__(self):
      return "PK(pk:%s,cls:%s)" %(self.pk,self.cls )
    

    def to_json(self):
        attributes = vars(self)  
        return json.dumps(attributes, indent=2 )    
    
def define_instance_from_name(module,class_name):
   #logger_info("==define_instance_from_name==%s" %(class_name))
 
   if isinstance(module,str):
      module = importlib.import_module(module)

   class_ = getattr(module, class_name)
   instance = class_()
   return instance

def define_module_from_name( module_name):
    module = importlib.import_module(module_name)
    globals()[module] = module
    return module

class ModelPopulator():
    
  def __init__(self,classDict,package):
    self.classDict=classDict
    self.rdf_type_classMap=self.define_rdf_type_classMap()
    self.package_name=package
    self.templatePath_sparql = pathlib.Path().resolve().parent.absolute() / 'script/template/sparql'
    self.model_instance_dict=dict()
     
    self.list_instance = list()
    self.KEY_ONLY=1
    self.FULL_ATTR_KEYS=2
    self.attribute_error=list()
    self.max_count=None #maximum elements in list_instance (for testing)
    self.limit=1000
    self.toolbox=ModelToolBox(self.classDict)
    self.type_schema_uri = rdflib.namespace.RDF
    constdict=constantDict()
    self.type_suffix=constdict['type_suffix']
    self.dataset_file=None # if not None, we use file based in memory store
    self.in_mem=None
    self.module_dict={}

 
 
  #def define_instance_from_name(self,module,class_name):
  # return  define_instance_from_name( module,class_name)
 
  def defineModulebyName(self,module_name):
     if module_name in self.module_dict.keys():
        mod=self.module_dict[module_name]
        return mod
     else:
        mod = define_module_from_name( module_name) 
        self.module_dict[module_name]=mod
        return mod 
  
  
  def instance_by_uri_sparql(self,qparam):
     return self.instance_by_uri_sparql_impl(qparam,"")
  
  def instance_by_uri_sparql_impl(self,qparam,frag,do_no_type_clause=True):
    
    tpf="?s  a    {{qparam.domain_prefix}}:{{qparam.instance_class}}."
    if do_no_type_clause:
       tpf=""

    tmpl="""
    PREFIX {{qparam.domain_prefix}}: <{{qparam.domain_namespace}}>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

    SELECT  * 
     WHERE
     { 
      { %s
       ?s  ?p1  ?o1 .
       %s
      FILTER (  str(?s) ="{{qparam.instance_uri}}" )
     }
    }
    ORDER BY ?s
    LIMIT 1000
    """ % (tpf,frag)

    j2_env = Environment(loader=BaseLoader,trim_blocks=True).from_string(tmpl)
    return j2_env.render(qparam=qparam)
  


   

  #def all_instance_by_classname_sparql_from_file(self,qparam):
#
#    j2_env = Environment(loader=FileSystemLoader("%s" %(self.templatePath_sparql)),trim_blocks=True)
#    return j2_env.get_template('getAllInstanceByClassName.rq').render(
#        qparam=qparam
#    )

  def all_instance_by_classname_sparql(self,qparam):
    tmpl="""
    PREFIX {{qparam.domain_prefix}}: <{{qparam.domain_namespace}}>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    SELECT  ?s
    WHERE
    { 
     ?s a {{qparam.domain_prefix}}:{{qparam.instance_class}}
    }
    ORDER BY ?s
    LIMIT {{qparam.limit}}
    OFFSET {{qparam.offset}}
    """
    j2_env = Environment(loader=BaseLoader,trim_blocks=True).from_string(tmpl)
    return j2_env.render(qparam=qparam)
  
    

  def limit_and_offset(self,qparam):
    tmpl="""
    LIMIT {{qparam.limit}}
    OFFSET {{qparam.offset}}
    """
    j2_env = Environment(loader=BaseLoader,trim_blocks=True).from_string(tmpl)
    return j2_env.render(qparam=qparam)
  
  def initInMem(self,dsfile):
     rdfextras.registerplugins()
     self.in_mem=rdflib.Graph()
     self.in_mem.parse(dsfile)

  def executeQuery(self,db,dataset,query,cr=None): 
      if self.dataset_file is None:
        return self.executeQueryImpl(db,dataset,query)
      else:
        if self.in_mem is None:
          self.initInMem(self.dataset_file)
        return self.executeQueryFromFileImpl(query) 
  
  def formatBindings(self,bindings):
    #logger_info("===formatBindings===")
    rsl=[]
    for bi in bindings :   
      d={}
      for k,v in bi.items():
         if isinstance(v,URIRef) :
           tp="uri"
         else:
           tp="literal"
         d[str(k)]={'type':tp,'value':str(v)}
      rsl.append(d)    
     
    return rsl

  def executeQueryFromFileImpl(self,query ):
      #we wrap the results 
      
      procres  = self.in_mem.query(query)
      results={"results":{}}
      results["results"]["bindings"]=self.formatBindings(procres.bindings)
      #results["results"]["vars"]=procres.vars # usefull ?
      return results

  def executeQueryImpl(self,db,dataset,query,cr=None): 
      
      url=db 
      if dataset is not None and "%s" in db:
         url=db %(dataset)

      sparql = SPARQLWrapper(url)
      sparql.setQuery(query)
      sparql.setMethod('POST')
      sparql.setReturnFormat(JSON)
      if cr is not None:
        sparql.setCredentials(cr[0], cr[1])
      results = sparql.query().convert()
      return results
  
  def instances(self):
     return self.model_instance_dict
      
  
  def init_instances(self):
      # usefull to populate entities from multiple dataset
      for instance_uri in self.model_instance_dict.keys():
        inst=self.model_instance_dict[instance_uri] 
        inst.exhausted=False
        inst.pop_state=self.KEY_ONLY
        self.model_instance_dict[instance_uri]=inst

      return self.model_instance_dict
  
  ###public 
  def executePump(self,db, dataset,inputInstDict, ml,prefix,schema_uri,type_uri=None,do_populate_asso=False,level=1):
     
     inputInD=inputInstDict
     outputInD=None
     for i in range(0,level):
         #logger_info("@@level:%s"%(level))
         outputInD=self.executePump_impl(db, dataset,inputInD, ml,prefix,schema_uri,type_uri=None,do_populate_asso=False)
         #logger_info("len outputInD :%s"%(len(outputInD))) 
     return outputInD

  def executePump_impl(self,db, dataset,inputInstDict, ml,prefix,schema_uri,type_uri=None,do_populate_asso=False):
     # populate the missing attributes in already selected entities (with at least pk/uri ans class)
     self.model_instance_dict=inputInstDict
     qparam=self.init_qparam(prefix,schema_uri,self.limit,0)
     module=self.defineModulebyName(self.package_name)
     if type_uri is None:
        type_uri=self.type_schema_uri
     
     ukeys=list(self.model_instance_dict.keys())
     for instance_uri in ukeys:
              inst=self.model_instance_dict[instance_uri] 
              
              if isinstance(inst,PK):
                 instn=inst.cls
                 #logger_info(">>>>>><%s||%s||%s||%s||" %(self.package_name,inst,instn,module))
                 inst=self.cast_instance(inst,instn,module)
                 ###meta_label tag copy
                 #logger_info("mlab:",inst.meta_label)
                  

                 self.model_instance_dict[instance_uri]=inst
              else:
                 instn=inst.__class__.__name__      
              #logger_info(instance_uri+"  "+instn+"  "+inst.__class__.__name__ )   
              forcegoon=False
              if forcegoon==True or inst.exhausted is None or inst.exhausted==False:
                logger_info("GOON PUMP %s %s" %(inst.pk,inst.exhausted)) 
                #if instn=="UnificationXref":
                #  logger_info(inst.to_json()) 
                if instn in   self.classDict.keys():
                   metaClass=self.classDict[instn]
                   meta_label=inst.meta_label
                   qparam["instance_uri"] =instance_uri
                   qparam["instance_class"] =metaClass.name
                   inst=self.populate_inst(db,dataset,qparam, metaClass,module,type_uri,do_populate_asso,meta_label)
                   self.model_instance_dict[inst.pk]=inst 
     return self.model_instance_dict 
  
  #public
  def executeCustomQuery(self,db,dataset,query,ml,prefix,schema_uri,do_pk_only=False, tuple_result: bool = False):
     #logger_info("--executeCustomQuery")
     #logger_info(">>ml:"+str(ml))
     def fctQ(param):
       #logger_info("--fctQ")
       q=query 
       
       if 'limit' in param.keys():
          q=q+self.limit_and_offset(param)
       return q

     self.model_instance_dict={}
     self.list_instance = []

     
     qparam=self.init_qparam(prefix,schema_uri,self.limit,0)

     if tuple_result:
        self.populate_impl(qparam,None,fctQ,db,dataset,ml,None,do_pk_only, True)
        return self.truncate_list(self.list_instance)
     
     else:
        self.populate_impl(qparam,None,fctQ,db,dataset,ml,None,do_pk_only)
        return self.truncate_dict(self.model_instance_dict)

     
  def truncate_list(self,lst):
    if  self.max_count is None:
       return lst 
    else:
       return lst[:self.max_count]
    
  def truncate_dict(self,dt):
    if  self.max_count is None:
       return dt 
    else:
       ix=0
       mapd={}
       for k in dt.keys():
          ix+=1
          if ix <=self.max_count:
            mapd[k]=dt[k]
          else:
             break

       return mapd
    
  def populate_domain_instance(self,db,dataset,prefix,schema_uri,type_uri=None,do_pk_only=False):
     
     varmeta={}
     varmeta['vartag']="s"
     varmeta=self.check_varmeta(varmeta)
     fct=self.all_instance_by_classname_sparql
     self.model_instance_dict={}
     for k in self.classDict.keys():
      
        metaClass=self.classDict[k]
        
        varmeta['class']=metaClass.name

        qparam=self.init_qparam(prefix,schema_uri,self.limit,0)
         
        if unexpected_name(metaClass.name)==False:
          qparam["instance_class"] =metaClass.name
          #logger_info(qparam)  
          self.populate_impl(qparam,metaClass,fct,db,dataset,[varmeta],type_uri,do_pk_only)
     return self.model_instance_dict
  

  def init_qparam(self,prefix,schema_uri,limit,offset):

      qparam=dict()    
      qparam["domain_prefix"]=prefix 
      qparam["domain_namespace"]=schema_uri 
      qparam["limit"]=self.limit
      qparam["offset"]=0

      return qparam

  def check_varmeta(self,varmeta) :
     
     for k in ["label","vartag"]:
       if k not in varmeta.keys():
         varmeta[k]=None
     return varmeta
  
  def filter_binding_var_and_types(self,bindings):
       
       nb=[]
       nbt=[]
       for result in bindings:
          r={}
          rt={}
          for k in result.keys():
             if k.endswith(self.type_suffix):
                rt[k]=result[k]
             else:
                r[k]=result[k]
          nb.append(r)      
          nbt.append(rt)      

       return nb,nbt

  def populate_impl(self,qpara,metaClass,fct,db,dataset,ml ,type_uri=None, do_pk_only=False, tuple_result: bool = False):
         unknownClass=False
         if metaClass is None:
           unknownClass=True # multiple class option due to EntityNode (OR)

         do_populate_asso=True 
         qparam=copy.deepcopy(qpara)  

         if type_uri is None:
           type_uri=self.type_schema_uri

         #TODO: optimize with inst.exhausted
    
         module=self.defineModulebyName(self.package_name)
      #logger_info(module)

      
         mt={}
         for varmeta in ml:
           mt[varmeta['vartag']]=varmeta
     
      ###
      #   logger_info("---------mt----")
      #   for k in mt.keys():
      #     logger_info("mt:k:" +str(k))
      #   logger_info("---------------")         
      ###
         goon=True
         while goon==True:
           
           query=fct(qparam)

            
           logger_info(query)   
           #logger_info(query)      
           results=self.executeQuery(db,dataset,query)
           #logger_info(results)
           bindings= results["results"]["bindings"]
           if unknownClass==True:
              # we expect %x_t_y_p_e vars
              bindings,bind_types=self.filter_binding_var_and_types(bindings)

           #logger_info("========GOON %s  %s = %s  len %s" %(k,goon, qparam["offset"] ,len(bindings)) )    
           if bindings is None or len(bindings)==0:
              goon=False  
           else:
              qparam["offset"]=qparam["offset"]+qparam["limit"]
              
           #logger_info(results)
           #logger_info("============================================================")
           
           countel=-1
           for result in bindings:
             countel+=1
             ########warning attention : on a aussi des assos !!! ????


             
             if unknownClass==True:
                 btypes=bind_types[countel]
                 for vtag_type in btypes.keys():
                   #logger_info("vtag_type:-%s-%s-%s-" %(vtag_type,btypes[vtag_type],type(btypes[vtag_type])))
                   uri,cls=urldefrag(URIRef( btypes[vtag_type]['value']))
                   vtag=vtag_type.replace(self.type_suffix,"")
                   metaClass=self.classDict[cls]
                   varmeta=mt[vtag]
                   varmeta['class']=metaClass.name
 
      
             if unknownClass==True or metaClass.has_unexpected_name()==False:    
              # CHANGE HERE
              result_line = []
              for vartag in result.keys():
                if vartag not in mt.keys():
                   
                   raise Exception("vartag  %s not in mt.keys()" %(vartag ))

                varmeta=mt[vartag]
                if varmeta.get('class',None) is not  None: # is a class / not an association
                      
                      # use PK()
            
                      meta_label=varmeta['label']
                      varmeta=self.check_varmeta(varmeta)
                       
                      metaClass = self.classDict[varmeta['class']]
                      # logger_info(f"{vars(metaClass) = }")
                      qparam["instance_class"]=metaClass.name
                      ############### 
                      instance_uri=result[vartag]["value"]

                      qparam["instance_uri"]=instance_uri
                      #logger_info("qparam:"+str(qparam))
                     
                      if do_pk_only:
            
                        if self.model_instance_dict.get(instance_uri) is None:
                          inst=PK(instance_uri,str(metaClass.name),meta_label)
                        else:
                           inst = self.model_instance_dict.get(instance_uri)

            
                        if tuple_result:
                          result_line.append(inst)
                      else:   
                        inst=self.populate_inst(db,dataset,qparam, metaClass,module,type_uri,do_populate_asso,meta_label)

                      self.model_instance_dict[inst.pk]=inst
             if tuple_result:
              self.list_instance.append(result_line.copy())
             #for testing purpose
             if self.max_count is not None and len(self.model_instance_dict.keys() ) >= self.max_count:
                goon=False

  #FM 07 2024 : list management
  def defineAttVal(self,inst_att,attn,inst,meta_att):
     logger_info("  defineAttVal:start %s./ att %s"%(inst.pk,meta_att.name))
     att_setter=getattr(inst,'set_'+attn)
     
     if meta_att.list is None or meta_att.list==False:
         logger_info("  defineAttVal:2:NOT_LST case :%s" %(meta_att.name))
         att_setter(inst_att)
     else:
         ###list case
         logger_info("  defineAttVal:2:list case :%s" %(meta_att.name))
         att_getter=getattr(inst,'get_'+attn)
         currentdtl=att_getter()
         logger_info("  defineAttVal:3:init:"+str(currentdtl))
         dtl=None
         if currentdtl is None: #void 
            dtl=[]
            logger_info("  defineAttVal:3:x1")
         elif isinstance(currentdtl, list) ==True: # is a list 
              dtl=currentdtl
              logger_info("  defineAttVal:3:x2")
         else:
             dtl=[currentdtl] # not expected: issue management
             logger_info("  defineAttVal:3:x3:not expected")
         dtl.append(inst_att)
         logger_info("  defineAttVal:3:dtl:size:"+str(len(dtl)))
         att_setter(dtl)

     return True


  def populate_inst(self,db,dataset,qparam, metaClass,module,type_uri,do_populate_asso,meta_label=None):
                      logger_info("populate_inst:start"+str(qparam))
                      inst=self.inst_create_or_get(db,dataset,qparam,metaClass.name,metaClass,module,type_uri)
                      self.model_instance_dict[inst.pk]=inst
                      logger_info(">populate_inst %s" %(inst.pk))
                      #EntityNode>label copied in entity instance as meta_label:
                      if meta_label is not None:
                         inst.meta_label=meta_label

                      meta_att_list=self.toolbox.getMetaAttributeFromHierarchy(metaClass)
                      #logger_info("pop1 %s" %(inst))
                      for meta_att in meta_att_list:
                          if meta_att.base==False and do_populate_asso==True:
                            attn=meta_att.name   
                            clname_att=meta_att.type 
                            try: 
                              att_getter=getattr(inst,'get_'+attn)
                              attval=att_getter()
                              if attval is not None: 
                                #logger_info("!!attval not none")
                                att_qparam=copy.deepcopy(qparam)  
                                att_qparam["offset"]=0
                                att_qparam["limit"]=self.limit  
                                att_qparam["instance_uri"]=attval.pk
                                att_qparam["instance_class"]=clname_att  
                                matt_class=self.toolbox.getMetaClassByClassName(clname_att)
                                logger_info(att_qparam)
                                inst_att=self.inst_create_or_get(db,dataset,att_qparam,matt_class.name,matt_class,module,type_uri)
                                
                                self.model_instance_dict[inst_att.pk]=inst_att
                                logger_info("  ==>>populate_inst:DEFATT:adding inst_att:x1: %s" %(inst_att.pk) )
                                self.defineAttVal(inst_att,attn,inst,meta_att)
                                
                                #logger_info("pop2 %s" %(inst_att))

                            except AttributeError:
                              einf=sys.exc_info()  
                              err1 = einf[0]
                              err2 = einf[1]  
                              emsg="1: %s=%s; %s ; %s ;%s  " %(inst.__class__,metaClass.name,attn,err1,err2)
                              self.attribute_error.append(emsg)
                      return inst                  
                    
  def simple_class_name(self,lcn):
   
      sp=lcn.split(".")
      cn=sp[len(sp)-1]
      return cn

  def class_name_from_instance(self,inst):
      cn = str(type(inst)).split("'")[1]
      return cn
 
  def cast_instance(self,source_inst,target_class,module):
        
    target_inst = define_instance_from_name(module,target_class)

    for key, value in source_inst.__dict__.items():
        target_inst.__dict__[key] = value
    return target_inst
  
  def inst_create_or_get(self,db,dataset,qparam,cm_name,cm,module,type_uri):

           instance_uri=qparam["instance_uri"] 
           
           logger_info("inst_create_or_get:1:" +str(instance_uri))
           logger_info("instance_uri:%s"%(instance_uri))
           if instance_uri is None:
                logger_info("warning instance_uri  is None")
                return None
            
           dokeep=False
            
           if instance_uri in self.model_instance_dict.keys(): 
              inst=self.model_instance_dict[instance_uri]    
              if inst.exhausted is not None and inst.exhausted==True: 
                dokeep=True
           logger_info("inst_create_or_get:2:dokeep" +str(dokeep))
           if dokeep==True:     
              #logger_info("keep")
               
              ###########cast analysis
             
              class_simple_name=self.simple_class_name_from_instance(inst)
              #logger_info(">>>%s || %s" %(class_name,class_simple_name))
              if cm_name.lower() != class_simple_name.lower():
                 #logger_info("==>@@@@ Is CAST possible ? %s => %s  %s" %(class_simple_name,cm_name,inst.pop_state))
                 ## 1/ we  test if inst not full populated (regarding 1 source graph)
                 ##   (if so , inst was only referenced by a main entity at this point)
                  
                 if inst.pop_state==self.KEY_ONLY  :
                    
                 ##  2/we  test if   CAST possible       
                   if self.toolbox.is_children_class_of(cm_name,class_simple_name):
                        #we cast
                        #logger_info("==>@@@@YES WE CAST1 !! %s is children of  %s" %(cm_name,class_simple_name))
                        
                        targetClass=cm_name
                        #logger_info(inst)
                        inst=self.cast_instance(inst,targetClass,module)
                        #self.model_instance_dict[instance_uri]=inst
                        #logger_info(inst)
                    
                 ##
           else:

              #inst=self.define_instance_triple_defined_cls(db,dataset,qparam,cm,module,type_uri)
              logger_info("--- define_instance_user_defined_cls ---%s" %(cm_name))
               
              inst=self.define_instance_user_defined_cls(db,dataset,qparam,cm,module,type_uri,cm_name)
              
              #logger_info(inst.to_json())
              #logger_info(qparam)
              #logger_info("===define_instance DONE")  
              #logger_info(inst)  
              #logger_info("=====")  
              
           return inst
  def simple_class_name_from_instance(self,inst):  
     class_name = self.class_name_from_instance(inst)
     class_simple_name=self.simple_class_name(class_name)  
     return class_simple_name
          
  def init_clsmodel_instance(self,clname):
       cls_instance=self.define_cmodel_instance(clname)
       #logger_info("@@@@===>%s %s" %(clname ,cls_instance))  
       return cls_instance
  def parse_tripe_member(self,kw,res):
    obj=None
    tp=res[kw]['type']
    if 'type' in res[kw] :
      if tp=='uri':
           uri=URIRef(res[kw]['value'])
           #logger_info(dir(s_uri))
           #logger_info(s_uri.toPython())   
           #url, frag = urldefrag(uri)
           #logger_info(url) 
           #logger_info(frag)
           obj=uri
      elif tp=='literal':
           val=res[kw]['value']
           obj=val        
    return obj,tp


  def define_rdf_type_classMap(self):
       
      rdf_type_classMap=dict()
      for k in self.classDict.keys():
           metaclass=self.classDict[k]
           rdf_type_classMap[k]=metaclass.rdf_type
      return rdf_type_classMap

  



#####################################################

############################################################ 

  def define_instance_user_defined_cls(self,db,dataset,qparam,metaClass,module,type_uri,clname):
    #clname is not None
    return self.define_instance_impl(db,dataset,qparam,metaClass,module,type_uri,clname)



###FIXME : there is null instances 
  #def define_instance_triple_defined_cls(self,db,dataset,qparam,metaClass,module,type_uri):
    #clname is None
  #  return self.define_instance_impl(db,dataset,qparam,metaClass,module,type_uri)


  def define_instance_impl(self,db,dataset,qparam,metaClass,module,type_uri,clname=None,do_create_from_clname=False):
    #do_create_from_clname force the type of the entity
    # default is using the rdf type in the dataset
    ###TODO paging here
    #rdf_type="%s#type"%(type_uri)
    #logger_info("--*-*-* %s" % (type(type_uri)))
    #logger_info(type_uri)
    if isinstance(type_uri, str):
       rdf_type="%s#type"%(type_uri)
    else:
       rdf_type=type_uri['type']
 
     
    inst=None
    if clname is not None and do_create_from_clname:
       # we create instance from user selected class
       inst= define_instance_from_name(module,clname)
       # in this case we create the entity even if there is no data in triple store

    instance_uri=qparam["instance_uri"] 
    
    ##warning : for asso the type we have can be from parent so we can not add ?s  a    bi:tp. here
    query=self.instance_by_uri_sparql(qparam)
    
    iresults=self.executeQuery(db,dataset,query)
    bindings=list()
    #logger_info("bindings")
    for res in iresults["results"]["bindings"]:
        
        s,tp_s=self.parse_tripe_member('s',res) 
        p1,tp_p1=self.parse_tripe_member('p1',res)
        o1,tp_o1=self.parse_tripe_member('o1',res)
        tpl=dict()
        tpl['s']=s
        tpl['p1']=p1
        tpl['o1']=o1
        tpl['tp_s']=tp_s
        tpl['tp_p1']=tp_p1
        tpl['tp_o1']=tp_o1

        bindings.append(tpl)
        #logger_info("@@@   %s ==%s==> %s" %(s,p1,o1))
        #logger_info("   @@@   %s ==%s==> %s" %(tp_s,tp_p1,tp_o1))
        
        #logger_info(   "@@@   %s ==%s==> %s" %(tp_s,tp_p1,tp_o1))
        if inst is None and p1==rdf_type :
           
               
            #we create instance from class defined in triples  
            # in this case we create the entity only  if there is data in triple store
            url_o1, frag_o1 = urldefrag(o1)
            clname=frag_o1
        
            #  logger_info("!!!!!!!!!!!!!!!!!!!!!!! %s  %s %s  TP: %s" %(p1,o1,rdf_type,clname))
            inst= define_instance_from_name(module,clname)
            #logger_info(inst)
    if inst is None and len(bindings) >0:
         alert_err("ERROR:instance is None from URI %s , instantiation issue caused by missing rdf type or classe name %s" %(s,clname)) 
    if inst is None and len(bindings) ==0:
         alert_err("WARNING:we need to create the instance from scratch . URI:%s "  %(instance_uri))

    for tpl in bindings:
        
        s=tpl['s'] 
        p1=tpl['p1']
        o1=tpl['o1']
        pk=str(s)
        rowcase=0
        if pk == instance_uri:
           rowcase=1
           inst.__dict__['pk']=pk
           inst.pop_state=self.FULL_ATTR_KEYS
           inst.exhausted=True #
           #logger_info("define_instance_impl:PARSED_ROW_TPL:rowcase_%s:____:%s"%(rowcase,tpl))
        if p1!=rdf_type :
          rowcase=2
          try:
           # logger_info("define_instance_impl:PARSED_ROW_TPL:rowcase_%s:____:%s"%(rowcase,tpl))
            self.populate_attr(metaClass,module,type_uri,inst,s,p1,o1)
          except AttributeError as ex:
            err = sys.exc_info()[0]  
            errm = sys.exc_info()[1] 
            
            emsg="2:pk:%s:s:%s;p:%so:%s  %s - %s" %(pk,s,p1,o1,err,errm)
            logger_info(emsg+" || exception: %s" %(ex) )
            #print(ex)
               
            self.attribute_error.append(emsg)  

        

    if inst.__dict__['pk'] is None:
       inst.__dict__['pk']=instance_uri
       inst.pop_state=self.KEY_ONLY
       inst.exhausted=True # warning must remove exhausted with another dataset /connection /file

    if inst is not None and clname is not None:
       icn=type(inst).__name__
       classChecked=self.checkClassInHeritaneCoherence(icn,clname)
       #logger_info(">>>>>>>%s %s %s" %(icn,clname,classChecked))
       if classChecked==False:
         raise("class inheritance incoherence error %s / %s" %(icn,clname)) 
         
    return inst


  def checkClassInHeritaneCoherence(self,icn,clname):
       classChecked=False
 
       if icn==clname or self.toolbox.is_children_class_of(icn,clname):   
          classChecked=True
       return  classChecked
     
  def populate_attr(self,metaClass,module,type_uri,inst,s,p1,o1):
        logger_info("populate_attr %s %s %s" %(metaClass.name,p1,o1))
        url_p1, frag_p1 = urldefrag(p1)
        
        code_trace=1
        if url_p1==str(type_uri) and frag_p1=="type":
            code_trace=11
            #logger_info("url_p1=type_uri +type")
            url_o1, frag_o1 = urldefrag(o1)
            s_type=frag_o1
             
        else:
          code_trace=12
          attn="%s" %(frag_p1)  
          ##test if attribute exists
          asatt=False
          if "_"+attn in inst.__dict__.keys() or attn in inst.__dict__.keys() :
             code_trace=121
             asatt=True
          if asatt==False:
             code_trace=122
             # we do not raise exception because some unexpected user defined triple may exist 
             return False
          meta_att=self.toolbox.getMetaAttributeByAttName(metaClass,attn,dict()) 
          if type(o1)==URIRef:
                code_trace=code_trace+1000
                att_getter=getattr(inst,'get_'+attn)

                attval=att_getter()
 
                #attribute instanciation
                #logger_info("%s == %s"%(attn, metaClass.name))
                
                if meta_att is None:
                   logger_info("WARNING %s not found in meta class hierarchy" %(attn))
                    
                clname_att=meta_att.type
                #logger_info("==att to be populated=>>> %s %s" %(attn,clname_att))
                if meta_att.base==False:
                   code_trace=code_trace+10000
                   if attval is None: 
                      code_trace=code_trace+100000
                      inst_att= define_instance_from_name(module,clname_att)
                      #we create the att
                     
                      logger_info("  ==>>populate_attr::DEFATT_A:adding inst_att:uriref+base==False:attval_is_None: %s" %(inst_att) ) 
                      self.defineAttVal(inst_att,attn,inst,meta_att)
                   elif isinstance(attval,list):
                      inst_att= define_instance_from_name(module,clname_att)
                      logger_info("  ==>>populate_attr::DEFATT_B:adding inst_att:uriref+base==False:attval_is_None: %s" %(inst_att) ) 
                      self.defineAttVal(inst_att,attn,inst,meta_att)
                   else:
                      code_trace=code_trace+2000000
                      logger_info("  ==>>populate_attr::DEFATT_C:adding inst_att:uriref+base==False:attval_NOT_None:__REUSED__: %s" %(attval) )  
                      inst_att=attval

                   #then we populate the pk attribute (uri)
                   if isinstance(inst_att,list) and len(inst_att)>0:
                      ix=len(inst_att)-1
                      inst_att_el=inst_att[ix]
                      inst_att_el.pk=str(o1)
                      inst_att_el.pop_state=self.KEY_ONLY
                      code_trace=code_trace+9900000000
                   else:
                     inst_att.pk=str(o1)
                     inst_att.pop_state=self.KEY_ONLY
                     code_trace=code_trace+7700000000
                else:
                   code_trace=code_trace+8000000
                   logger_info("we keep None for base type")
                #logger_info("%s" %( attn) )   
          else:     
            code_trace=code_trace+100000000
            logger_info("  ==>>populate_attr:DEFATT:adding inst_att:o1:NO_uriref '%s'" %(o1) ) 
            self.defineAttVal(o1,attn,inst,meta_att)
        logger_info("populate_attr end code_trace :%s" %(code_trace))     
          

#####################

def create_dictionaries_from_csv(csv_file_path):
    """
    Creates two dictionaries from a CSV file where:
    - d1 has the 'Subject' column as keys.
    - d2 has the 'Object' column as keys.

    :param csv_file_path: The file path of the input CSV file.
    :return: Tuple of two dictionaries (d1, d2).
    """
    d1 = {}
    d2 = {}

    with open(csv_file_path, mode='r', encoding='utf-8') as csv_file:
        reader = csv.DictReader(csv_file)
        
        for row in reader:
            subject = row['Subject']
            predicate = row['Predicate']
            obj = row['Object']
            triple = (subject, predicate, obj)
            
            # Add to d1
            if subject in d1:
                d1[subject].append(triple)
            else:
                d1[subject] = [triple]

            # Add to d2
            if obj in d2:
                d2[obj].append(triple)
            else:
                d2[obj] = [triple]

    return d1, d2

def removeSep(nm):
    if nm.endswith(':'):
        nm = nm[:-1]    
    return nm
    
def parseurl(url):
    """
    Parses a URL and extracts the namespace and local name.
    If the namespace ends with '#', it removes the last character.

    :param url: The input URL string.
    :return: Tuple containing the namespace and local name.
    """
    namespace, local_name = split_uri(url)
    if namespace.endswith('#'):
        namespace = namespace[:-1]
    return namespace, local_name



def cast_any_instance( source_inst,target_class,module):
        
    target_inst = define_instance_from_name(module,target_class)

    for key, value in source_inst.__dict__.items():
        target_inst.__dict__[key] = value
    return target_inst
    
def create_instance(type_name, value=None):
    """
    Creates an instance of a class from its name as a string.

    :param type_name: The name of the type as a string ('str', 'float', or 'int').
    :param value: The value to initialize the instance with (optional).
    :return: An instance of the specified type.
    """
    try:
        # Use eval to create an instance of the type
        instance = eval(f"{type_name}({repr(value)})") if value is not None else eval(f"{type_name}()")
        return instance
    except NameError as e:
        raise ValueError(f"Unknown type name: {type_name}") from e
    except TypeError as e:
        raise ValueError(f"Invalid value for type {type_name}: {value}") from e


def join_except_last(lst):
    """
    Joins all elements of the list except the last one using '.' as the separator.

    :param lst: The input list of strings.
    :return: A string with all elements joined by '.' except the last element.
    """
    if not lst:  # Check if the list is empty
        return ''
    if len(lst) == 1:  # If there's only one element, return it as is
        return lst[0]
    return '.'.join(lst[:-1])



#####################



class InMemoryStoreClient():
    
  def __init__(self,guList ):
      
    self.classDictL=[]  
    self.gul=guList  
    for cgu in guList :
        self.classDictL.append(cgu.modelPopulator().classDict)
        
    self.bp_template=self.define_template()
 
    self.rscl=[]
    self.domainl=[]  
    self.prefixl=[]  
    for cdi in  self.classDictL: 
      self.rscl.append(StoreClient(cdi))

    self.s2t={}      
    self.g = Graph()  
    self.g.parse(data=self.bp_template, format="xml")  

  def define_template(self):

   return """<?xml version="1.0" encoding="UTF-8"?>
<rdf:RDF
 xmlns:xsd="http://www.w3.org/2001/XMLSchema#"
 xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
 xmlns:owl="http://www.w3.org/2002/07/owl#"
  >
</rdf:RDF>
     """
     
  def entity_to_graph(self,triples_data):

 
    
      for res in triples_data:
        subject=res['s']
        predicate=res['p']
        obj=res['o']  
        self.g.add((subject, predicate, obj))

      return self.g


  def insert_instance_in_graph(self,inst):
        uri_id=inst.pk
        ix=-1 
        found=0
        for classDict in self.classDictL:
          ix=ix=1
          rsc=self.rscl[ix]  
          rdf_type_map=rsc.define_rdf_type_classMap(classDict)      
          for  k in   classDict.keys():
            cls_rdf_type=rdf_type_map[k]
             
            if cls_rdf_type==inst.rdf_type: 
                found=1
            if found==1:    
               triples_data,domain,prefix=rsc.define_triples_data(inst, classDict)  
               self.entity_to_graph(triples_data)
          
 
  def  save_graph_as_rdf_xml(self,exfile):   
       csc=self.rscl[0]
       csc.g=self.g
       csc.save_graph_as_rdf_xml(exfile)


  def graph_to_csv(self, csv_file_path):
    """
    Generates a CSV file from an RDFLib graph.

    :param graph: An RDFLib graph object.
    :param csv_file_path: The file path for the output CSV file.
    """
    graph=self.g
    # Open the CSV file for writing
    with open(csv_file_path, mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)

        # Write the header
        writer.writerow(['Subject', 'Predicate', 'Object'])

        # Write the triples
        for subj, pred, obj in graph:
            writer.writerow([subj, pred, obj])


  def csv2entities(self,csv_file_path):
      endict=self.csv2Dict(csv_file_path)
      return self.dict2entities(endict)
      
  def csv2Dict(self,csv_file_path):

    s2t, o2t = create_dictionaries_from_csv(csv_file_path)
    self.s2t=s2t
    entdict={}
    for key, tripleList in  self.s2t.items():
      for triple in tripleList:
        #logger_info(triple)
        #logger_info(f"{key}: {triple}")
        subj= triple[0] 
        if triple[1]=='rdf:type':  
          #logger_info(f"root_type!")
            namespace, local_name = parseurl(triple[2]) 
          
            logger_info(f"-TYPE-{namespace}: {local_name}") 
          
            for cgu in self.gul: 
            #logger_info("===============",cgu.domain())  
              doma=normDom(cgu.domain())

              if  doma==namespace:
              
                inst=cgu.define_model_instance(local_name)
                if inst is not None:  
                   inst.pk=subj
                   entdict[inst.pk]=inst 
                   logger_info("---->"+str(inst.pk)+"---"+str(inst) )
                 
    return entdict       
      
  def dict2entities(self,entdict):

    entk=list(entdict.keys())
    nbgu={}
    for subj in entk :
      inst=entdict[subj]
      logger_info("<<>>PK:::"+subj+"inst::"+str(inst))
      ix=-1
      for cgu in self.gul: 
        ix=ix+1
        doma=normDom(cgu.domain())
        if doma in inst.rdf_type:
            nbgu[subj]=ix

    for subj in entk :
      inst=entdict[subj]
    
      cm=None
      cln=inst.__class__.__name__
      #inst.rdf_type
      logger_info("PK:::"+str(subj))
      ix=nbgu[subj]
      curclassDictSubj=self.classDictL[ix] 
      rsc=self.rscl[ix]
      cgu=self.gul[ix] 
    
      if cln in curclassDictSubj.keys():
         cm= curclassDictSubj[cln]
         curattributes=rsc.toolbox.getMetaAttributeFromHierarchy(cm)
      if subj in  self.s2t.keys():
         logger_info("subj:"+subj) 
         tripleList=self.s2t[subj]
         for triple in tripleList:  
            if triple[1]=='rdf:type': 
               logger_info("-[--triple   :"+str(triple) )
            else:
               logger_info("-+--triple   :"+str(triple))
               pnamespace, plocal_name = parseurl(triple[1])
               pnamespace=removeSep(pnamespace)
               logger_info("P::" + str(pnamespace)+ str( plocal_name))
            
               doma=normDom(cgu.domain())
               prefx=cgu.prefix()
               pnamespaceN=normDom(pnamespace)
               if  doma==pnamespaceN or prefx ==pnamespaceN :
                  
                  att_name=plocal_name
                  att_val=triple[2]
                  
                  logger_info(">>>>>>!!!! " +att_name +att_val + str(cm.name))
                  
                  for attx in curattributes:
                      logger_info(""+attx.name+"==?"+att_name)
                      if attx.name==att_name: #obj member

                          
                         tpn= attx.type

                         if attx.base==True:
                                   try:
                                     att_inst = create_instance( attx.type,att_val) 
                                      
                                   except Exception as ex:
                                     alert_err("E0::"+str(ex))
                                     pass  
                         ddd=0
                         att_inst=None               
                         if attx.base==False and ddd==0:              
                           logger_info(tpn+"------ #obj member "+att_val+"(att) FOUND -------, ref if "+subj) 
                           att_inst=None 
                           if att_val in  entk:
                             # att_val is  an uri pk
                             att_inst=entdict[att_val]
                             logger_info(att_inst.pk+" "+att_inst.__class__.__name__ +" found in entdict att IS_REF")
                           else:    
                             if tpn in curclassDictSubj.keys(): 
                                att_inst=cgu.define_model_instance(tpn)
                             else:
                                  
                                  packgr=join_except_last(tpn.split('.'))
                                  #logger_info("|||||||||package processing") 
                                  #logger_info("||||||missing processing :%s %s %s     %s"%(attx.name,att_pk,tpn, packgr))
                                  module = None
                                  pkl=packgr
                                  foundm=0
                                  try:
                                    #logger_info(pkl)  
                                    module=self.defineModulebyName(pkl)
                                    foundm=1  
                                  except Exception as ex:
                                     alert_err("E1::"+str(ex))
                                     pass 
                                  if foundm==0    :
                                    try:
                                      pkl=packgr.split('.')[0] 
                                      #logger_info(pkl)    
                                      module=self.defineModulebyName(pkl)
                                      foundm=2  
                                    except Exception as ex:
                                     alert_err("E2::"+str(ex))
                                     pass     
                                
                                  if foundm !=0 and module  is not None:
                                      
                                      stpn=tpn.replace(pkl,"")
                                       
                                      att_inst = define_instance_from_name(module,stpn)
                                      
 
                         if att_inst is not None:  
                              logger_info("att_inst:" +str(att_inst) )
                              #logger_info("***********"+att_inst.to_json())
                              if  attx.base==False and "pk" in att_inst.__dict__.keys():
                                  #att_inst.pk=att_val  
                                  entdict[att_inst.pk]=att_inst  
                                  
                              inst.__dict__["_"+plocal_name] = att_inst
                         
                                

               else:    
                 pass  
 
    return entdict

class StoreClient():
    
  def __init__(self,classDict):
    self.g=None
    self.namespace_manager=None
    self.toolbox=ModelToolBox(classDict)
    self.classDict=classDict 
    self.bp_template=self.define_bp_template()
    self.custom_query_list=list()


  def define_bp_template(self):

   return """<?xml version="1.0" encoding="UTF-8"?>
<rdf:RDF
 xmlns:xsd="http://www.w3.org/2001/XMLSchema#"
 xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
 xmlns:owl="http://www.w3.org/2002/07/owl#"
  >
</rdf:RDF>
     """
 
    
  def define_namespace_manager(self,prefix,domain):
     if self.namespace_manager is None:
      g = Graph()
      g.namespace_manager.bind(prefix, URIRef(domain))
      self.namespace_manager=g.namespace_manager
    
  def delete_from_store_by_uri_id(self,sparql,uri_id,prefix,domain):
    
  

      self.define_namespace_manager(prefix,domain)
      uri_id=self.format_sparql(URIRef(uri_id),self.namespace_manager)
    
    
      query="""

PREFIX %s:   <%s>  

DELETE { ?s ?p ?o }
WHERE { 
  %s ?p ?o.  ?s ?p ?o 
};
#id as ?p

DELETE { ?s ?p ?o }
WHERE { 
 ?s ?p  %s .  ?s ?p ?o 
}

    """ %(prefix,domain,uri_id,uri_id)


      sparql.setQuery(query)
      sparql.setReturnFormat(JSON)
      logger_info(query)
      res=sparql.query()
      logger_info(res)

    



  def select_all_query(self,prefix,domain_schema_uri,unwanted_subject_uri,limit,offset):
    query="""

PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX %s: <%s>

SELECT ?s ?p ?o
WHERE {
  ?s ?p ?o
   FILTER(?s != <%s>)
}
LIMIT %s
OFFSET %s
    
  """ %(prefix,domain_schema_uri,unwanted_subject_uri,limit,offset)
    return query

#logger_info(query)

  def defineTerm(self,el):
    #logger_info(el)
    if el["type"]=='uri':
         term= URIRef(el["value"])

    elif el["type"]=='literal':
        if "datatype" in el: 
       
          term= Literal(el["value"],datatype=el["datatype"])
        else:
          term= Literal(el["value"], datatype=XSD.string)  
    #logger_info("  ==> %s"% (term))
    return term
    

    
    #term=Literal
    #return term

  def file_to_graph(self,file) :
     g = Graph()
     g.parse(file, format="xml")
     self.g=g
     return g

  def string_to_graph(self,xml) :
     f=StringIO(xml)
     g = Graph()
     g.parse(f, format="xml")
     self.g=g
     return g
  
  def rdf_xml_string(self,g=None): 
      if g is None:
         g=self.g
      rdf_xml_str  = g.serialize(format='xml')
      return rdf_xml_str 
  

  def store_to_graph(self,db,prefix,domain_schema_uri,unwanted_subject_uri,limit=1000):

    self.g = Graph()
    self.g.parse(data=self.bp_template, format="xml")    
    
    offset=0
    sparql = SPARQLWrapper(db)
    go_on=True
    while go_on==True:
      query=self.select_all_query(prefix,domain_schema_uri,unwanted_subject_uri,limit,offset)
      sparql.setQuery(query)
      sparql.setReturnFormat(JSON)
      res=sparql.query()
      results = res.convert()
      bindings=results["results"]["bindings"]
      if len(bindings)==0:
         go_on=False
      else:
        offset=offset+limit
    
      for result in bindings:
        subject =self.defineTerm(result["s"])
        predicate  =self.defineTerm(result["p"])
        obj =  self.defineTerm(result["o"])
        self.g.add((subject, predicate, obj))

    return self.g


  def extends_graph(self,sparql,size,labels,limit):
   l=labels
   if size is None or size ==0:
      return  


   for s, p, o in self.g:
      #logger_info("%s %s %s" %(s,p,o))
    q="""
prefix bp: <http://www.biopax.org/release/biopax-level3.owl#>

SELECT  * 
WHERE
 { 
  { 
    ?s  ?p  ?o .
    FILTER (  str(?s) ="%s" )
  }
}
    """ 
    qs=q %(s)
    qo=q%(o)
    extend_query_list=list()
    if size>=1:
      extend_query_list.append(qs)
    if size>=2:
      extend_query_list.append(qo)

    for query_template in extend_query_list:    
     offset=0
    
     go_on=True
     while go_on==True:
       query=query_template + " LIMIT %s OFFSET %s" %(limit,offset)
       #logger_info("====+====")
       #logger_info(query)
       #logger_info("========")
       sparql.setQuery(query)
       sparql.setReturnFormat(JSON)
       res=sparql.query()
       results = res.convert()
       bindings=results["results"]["bindings"]
       if len(bindings)==0:
         go_on=False
       else:
        offset=offset+limit
       
       for result in bindings:
         subject =self.defineTerm(result[l[0]])
         predicate  =self.defineTerm(result[l[1]])
         obj =  self.defineTerm(result[l[2]])
         self.g.add((subject, predicate, obj))
         

  def store_custom_query_to_graph(self,db,ext_size=2,labels=["s","p","o"],limit=1000):

    l=labels
    self.g = Graph()
    self.g.parse(data=self.bp_template, format="xml")    
    sparql = SPARQLWrapper(db)
    for query_template in self.custom_query_list:    
     offset=0
    
     go_on=True
     while go_on==True:
       query=query_template + " LIMIT %s OFFSET %s" %(limit,offset)
       #logger_info("====+====")
       #logger_info(query)
       #logger_info("========")
       sparql.setQuery(query)
       sparql.setReturnFormat(JSON)
       res=sparql.query()
       results = res.convert()
       bindings=results["results"]["bindings"]
       if len(bindings)==0:
         go_on=False
       else:
        offset=offset+limit
       #"rdftype": { "type": "uri" , "value": "http://www.w3.org/1999/02/22-rdf-syntax-ns#type" } ,
       for result in bindings:
         #logger_info(result)
         subject=None
         predicate=None
         obj=None 
         if len(l)>0 and l[0] in result.keys():
           subject =self.defineTerm(result[l[0]])
         if  len(l)>1 and  l[1] in result.keys():  
           predicate  =self.defineTerm(result[l[1]])
         if  len(l)>2 and  l[2] in result.keys():
           obj =  self.defineTerm(result[l[2]])
         # add  RDF.type in some cases ??
         self.g.add((subject, predicate, obj))

    self.extends_graph(sparql,ext_size,labels, limit)
    return self.g



  def save_graph_as_rdf_xml(self,exfile, gr=None):
    logger_info("exporting %s triples in file %s" %(len(self.g),exfile))
    g=None
    if gr is not None:
       g=gr
    else:
       g=self.g
    g.serialize(destination=exfile, format='xml')
    pf=pathlib.Path(exfile)  
    try:
      pf.chmod(0o0777)   
    except:
      pass

    

    

    


  def define_rdf_type_classMap(self,classDict):
 
      rdf_type_classMap=dict()
      for k in  classDict.keys():
           metaclass= classDict[k]
           rdf_type_classMap[k]=metaclass.rdf_type
      return rdf_type_classMap



  def define_literal(self,value,datatype=None):
   if value is None:
      v=None
   else:
    #v=value.encode('unicode_escape')
      v=value
    
   if datatype is not None:   
     term= Literal(v,datatype= datatype )
   else:
     term= Literal(v, datatype=XSD.string) 
   return term




  def define_triples_data(self,inst,classDict):
   #logger_info(inst)
   #logger_info(inst.rdf_type)
   domain=None
   prefix=None
   data=list()
   rdf_type_map=self.define_rdf_type_classMap(classDict)
   uri_id="http:/:mydomain/565675"
   ct=0 
   for  k in   classDict.keys():
    
      cls_rdf_type=rdf_type_map[k]
      ct=ct+1
   
      if cls_rdf_type==inst.rdf_type: 
         metaclass=classDict[k]
         domain=metaclass.domain   
         prefix=metaclass.prefix   
         attributes=self.toolbox.getMetaAttributeFromHierarchy(metaclass)
         #logger_info("-->%s %s = %s" %(cls_rdf_type,k,metaclass))   
         s=URIRef(inst.pk)
         #p=URIRef(RDF.type) 
         p=URIRef("rdf:type")     
         o=URIRef(inst.rdf_type)
        
         #logger_info("    %s %s %s" %(s,p,o))
         elt=dict()
         elt["s"]=s
         elt["p"]=p
         elt["o"]=o 
         data.append(elt)
          
         for att in attributes:
            #logger_info(att.name)
            #logger_info("%s %s  %s %s" %(att.base,att.name,att.type,att.xtype))
            s1=uri_id
            p1=att.name
            o1=att.xtype 
            #logger_info("    %s %s %s" %(s1,p1,o1))
            
            s=URIRef(inst.pk)
            #p=metaclass.domain + att.name
            p=URIRef(metaclass.prefix+":"+att.name)
            datatype=None
            o=None
            doshow=True
            ogetter=getattr(inst,'get_'+att.name)
            #logger_info("==x=>%s" %(ogetter()))
            if att.base==True:
                 
                datatype=att.type
                atvalue=ogetter()
                if atvalue is   None: 
                   doshow=False 
                o=self.define_literal(atvalue,datatype)
            else:
 
                att_inst=ogetter()
                if att_inst is not None:
                  o=URIRef(att_inst.pk)
                else:
                    doshow=False
                  
            if doshow:    
               #logger_info("  ===  %s %s %s" %(s,p,o))
               el=dict()
               el["s"]=s
               el["p"]=p
               el["o"]=o 
               data.append(el)
   return data,domain,prefix

  def format_sparql(self,term,namespace_manager=None):
    #logger_info(term)
    v=term
    doquote=False 
    if  isinstance(term, URIRef) :
         
        if str(term).startswith("http"):     
            if namespace_manager:
                
                v2= namespace_manager.normalizeUri(v)
         
                if v2 ==v:
                       doquote=True
                else:
                    logger_info("!! %s    == %s "%(v,v2)  )
                v=v2  
    elif  isinstance(term, Literal) :  
        v="'''%s'''" %(term)
    return v

  def update_or_insert_instance(self,sparql,inst):
        uri_id=inst.pk
        triples_data,domain,prefix=self.define_triples_data(inst,self.classDict)
        self.delete_from_store_by_uri_id(sparql,uri_id,prefix,domain)
        
        return self.insert_instance_impl(sparql,inst,triples_data,domain,prefix)
        
        
  def insert_instance(self,sparql,inst):
     triples_data,domain,prefix=self.define_triples_data(inst,self.classDict)
     return self.insert_instance_impl(sparql,inst,triples_data,domain,prefix)
    
    
  def insert_instance_impl(self,sparql,inst,triples_data,domain,prefix):
    
    self.define_namespace_manager(prefix,domain)
    content=""
     
    ct=0
    for triple in triples_data:
       
       s=triple["s"]
       p=triple["p"]
       o=triple["o"]
       s=self.format_sparql(s,self.namespace_manager)
       p=self.format_sparql(p,self.namespace_manager)
       o=self.format_sparql(o,self.namespace_manager)
       ct=ct+1
       if ct==1:
          content=content+"%s %s %s;\n"  %(s,p,o)
       else:
          content=content+"     %s %s;\n"  %(p,o)
     
    query="""
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> 
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> 
PREFIX owl:  <http://www.w3.org/2002/07/owl#> 
PREFIX %s:   <%s>  
INSERT DATA
{
 
 
%s

} 

    """ %(prefix,domain,content)
    

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    logger_info(query)
    res=sparql.query()
    logger_info(res)    
 


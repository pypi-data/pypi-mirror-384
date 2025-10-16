#!/usr/bin/env python
# coding: utf-8

# In[1]:


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

from jinja2 import Environment, FileSystemLoader
from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Graph, URIRef, Namespace, RDF, Literal
import rdfextras
from urllib.parse import urldefrag
import textwrap
import importlib
import dill
import traceback
import base64
import pickle
 
from .utils import *
from .meta_model import *

import logging as logger
logger.basicConfig(level=4, format='%(asctime)s - %(levelname)s - %(message)s')

class ModelCodeGenerator():
    
  def __init__(self,package_name,classDict,prefix,domain,shortprefix=None):
    
    self.classDict=classDict
    self.package_name=package_name
    self.version="1.0.0"
    self.templatePath_python = pathlib.Path().resolve().parent.absolute() / 'script/template/python'
    spa="script/%s/" %(self.package_name)
    self.codegenPath = pathlib.Path().resolve().parent.absolute() / spa
    self.codegen_extension=".py"
    self.perm=0o0777
    self.cgdir="%s" %(self.codegenPath)
    self.dochelperdir="%s/%s" %(self.cgdir,"doc")
    self.utilsdir="%s/%s" %(self.cgdir,"utils")
    self.compactdir="%s/%s" %(self.cgdir,"compact")
    self.toolbox=ModelToolBox(self.classDict)
    self.prefix=prefix
    if shortprefix is not None:
       self.shortprefix=shortprefix
    else:
       self.shortprefix=prefix[0:2]   
    self.domain=domain
    
  def codegen_class(self,cm,classDict):
    
    j2_env = Environment(loader=FileSystemLoader("%s" %(self.templatePath_python)),
                         trim_blocks=True
                         )
    templatefile=None
    
    if cm.is_multi()==True:
       templatefile='classmulti.template'
       cm.configMulti(classDict) 
    else:
       templatefile='class.template'  

    return j2_env.get_template(templatefile).render(
        cm=cm,
        package_name=self.package_name
    )
  
  def codegen_compact_class(self,cm,classDict):
    
    j2_env = Environment(loader=FileSystemLoader("%s" %(self.templatePath_python)),
                         trim_blocks=True
                         )
    templatefile=None
    
    templatefile='compactclass.template'   # no inheritance. all attr copied 
    cm.configMulti(classDict) 
    return j2_env.get_template(templatefile).render(
        cm=cm,
        package_name=self.package_name
    )

  def codegen_doc_class(self,cm,classDict):
    
    j2_env = Environment(loader=FileSystemLoader("%s" %(self.templatePath_python)),trim_blocks=True)

    templatefile='doc_class.template'  
    cm.configMulti(classDict)
    return j2_env.get_template(templatefile).render(
        cm=cm,
        package_name=self.package_name
    )

  def codegen_init(self,class_dict):
    
    j2_env = Environment(loader=FileSystemLoader("%s" %(self.templatePath_python)),trim_blocks=True)
    return j2_env.get_template('init.template').render(
        class_dict=class_dict,
        package_name=self.package_name,
        version=self.version
    )

  def codegen_init_doc(self,class_dict):
    
    j2_env = Environment(loader=FileSystemLoader("%s" %(self.templatePath_python)),trim_blocks=True)
    return j2_env.get_template('init_doc.template').render(
        class_dict=class_dict,
        package_name=self.package_name,
        version=self.version
    )

  def codegen_gen_utils(self,class_dict):
    
    mchld=dict()
     
    for k in self.classDict.keys():
        cm=self.classDict[k]
        if cm.has_unexpected_name()==False:
          cln=cm.name
          children=self.toolbox.class_children(cln)
          mchld[cln]=children
           

    b64conf=base64.b64encode(pickle.dumps(self.classDict,-1))

    j2_env = Environment(loader=FileSystemLoader("%s" %(self.templatePath_python)),trim_blocks=True)
    return j2_env.get_template('gen_utils.template').render(
        class_dict=class_dict,
        mchildren=mchld,
        package_name=self.package_name,
        version=self.version,
        domain=self.domain,
        b64conf=b64conf,
        prefix=self.prefix,
        shortprefix=self.shortprefix
        
    )

  def codegen_validate_utils(self,class_dict):
    
    j2_env = Environment(loader=FileSystemLoader("%s" %(self.templatePath_python)),trim_blocks=True)
    return j2_env.get_template('validate_utils.template').render(
        class_dict=class_dict,
        package_name=self.package_name,
        version=self.version
    )

  

  def codegen_dochelper(self,class_dict):
    
    j2_env = Environment(loader=FileSystemLoader("%s" %(self.templatePath_python)),trim_blocks=True)
    return j2_env.get_template('dochelper.template').render(
        class_dict=class_dict,
        package_name=self.package_name,
        version=self.version
    )

  def codegen_class_utils(self,class_dict):
    
    j2_env = Environment(loader=FileSystemLoader("%s" %(self.templatePath_python)),trim_blocks=True)
    return j2_env.get_template('class_utils.template').render(
        class_dict=class_dict,
        package_name=self.package_name,
        version=self.version
    )

  def writecode(self,filepath,code,perm):
     pf=pathlib.Path(filepath)  
     pf.write_text(code)   
     pf.chmod(perm)

  def codegen(self):
    
     
     cgdir=self.cgdir

     
     dochelperdir=self.dochelperdir
     utilsdir=self.utilsdir
     perm=self.perm  

     filename="__init__"+self.codegen_extension
     code=self.codegen_init(self.classDict)
     filepath=cgdir+"/"+filename   
     self.writecode(filepath,code,perm)
     

     filename="__init__"+self.codegen_extension
     code=""
     filepath=utilsdir+"/"+filename   
     self.writecode(filepath,code,perm)


     filename="gen_utils"+self.codegen_extension
     code=self.codegen_gen_utils(self.classDict)
     filepath=utilsdir+"/"+filename   
     self.writecode(filepath,code,perm)   
 
     filename="validate_utils"+self.codegen_extension
     code=self.codegen_validate_utils(self.classDict)
     filepath=utilsdir+"/"+filename   
     self.writecode(filepath,code,perm)    
    

     filename="class_utils"+self.codegen_extension
     code=self.codegen_class_utils(self.classDict)
     filepath=utilsdir+"/"+filename   
     self.writecode(filepath,code,perm)




     filename="__init__"+self.codegen_extension
     code=self.codegen_init_doc(self.classDict)
     filepath=dochelperdir+"/"+filename   
     self.writecode(filepath,code,perm)

     filename="__init__"+self.codegen_extension
     code=self.codegen_init_doc(self.classDict)
     filepath=self.compactdir+"/"+filename   
     self.writecode(filepath,code,perm)
   
     filename="helper"+self.codegen_extension
     code=self.codegen_dochelper(self.classDict)
     filepath=dochelperdir+"/"+filename   
     self.writecode(filepath,code,perm)    

     for k in self.classDict.keys():
        cm=self.classDict[k]
        if cm.has_unexpected_name()==False:
              
         code=self.codegen_class(cm,self.classDict)
         filename=cm.name.lower()+self.codegen_extension
       
         filepath=cgdir+"/"+filename
         try:
           logger.info("writing "+filepath)

           self.writecode(filepath,code,perm)
            
         except:
           logger.error("error writing code in %s" %(filepath)) 
    ##############
    # Fm + 03 2025
     for k in self.classDict.keys():
        cm=self.classDict[k]
        if cm.has_unexpected_name()==False:
              
         code=self.codegen_compact_class(cm,self.classDict)
         filename=cm.name.lower()+self.codegen_extension
       
         filepath=self.compactdir+"/"+filename
         try:
           logger.info("writing "+filepath)

           self.writecode(filepath,code,perm)
            
         except:
           logger.error("error writing code in %s" %(filepath)) 



     ############
     for k in self.classDict.keys():
        cm=self.classDict[k]
        if cm.has_unexpected_name()==False:
             
         code=self.codegen_doc_class(cm,self.classDict)
         filename="dh_"+cm.name.lower()+self.codegen_extension
    
         filepath=dochelperdir+"/"+filename
         try:
           logger.info("writing "+filepath)
           self.writecode(filepath,code,perm)
            
         except:
           logger.error("error writing code in %s" %(filepath))              





  def prepare_codegen(self):
 
     self.prepare_codegen_dir(self.cgdir)
     self.prepare_codegen_dir(self.dochelperdir)
     self.prepare_codegen_dir(self.utilsdir)
     self.prepare_codegen_dir(self.compactdir)
        
  def prepare_codegen_dir(self,dirp):
    if dirp=="/" or len(dirp)<2 or "." in dirp:
       raise Exception("error. will not create directory. directory name issue : %s"  %(dirp))
    try:
        os.makedirs(dirp)
        
    except FileExistsError:
        logger.warning("directory  %s already created " %(dirp))
    try:
         self.codegenPath.chmod(self.perm)
    except:
         logger.warning("cannot  chmod  %s   " %(dirp))
    for root, dirs, files in os.walk(dirp):
        for file in files:
            #print("removing "+file)
            pf=pathlib.Path(root,file)
            pf.chmod(self.perm)
            pf.unlink()
            




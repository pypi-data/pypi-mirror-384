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

 
from .utils import *

       
class TAttributeModel():
    
  def __init__(self, name,base,tp,xtp):
      self.name = name
      self.base=base  
      self.xtype=xtp
      self.type=tp 
      self.comment=None
      self.rawcomment=None
      self.enum_values=None

      self.nullable=True
      self.list=False
      self.min=None
      self.max=None
      self.external=False
      
      self.overwrite=False # for cardinality an typiong prop overwrite
   
      
  def has_unexpected_type(self):
   
   if self.type is not None and '<' in self.type:
           return True   
   return False      
    
  def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)

  def __str__(self):
      return "name:%s;type%s;xtype:%s" %(self.name,self.type,self.xtype)
                                    
class TClassModel():
  def __init__(self, name,parent,domain,prefix,rdf_type):
      self.name = name
      self.parent=[]
      if parent is not None:
         if isinstance(parent, str):
           self.appendValidParent(parent)
         elif isinstance(parent, list):
           for p in parent:
             self.appendValidParent(p)

      self.is_root=False
      self.children=list()
      self.attribute=list()
      self.__attribute_name=dict()
      self.comment=None
      self.rawcomment=None
      self.pk=None
      self.domain=domain
      self.prefix=prefix  
      self.rdf_type=rdf_type
      self.object_attribute_name=list()
      self.type_attribute_name=list()

      ##mutliple inheritance management
      self.attribute_all=list()
      self.__attribute_name_all=dict()
      self.object_attribute_name_all=list()
      self.type_attribute_name_all=list()

  def is_multi(self):   #multiple inheritance management
      ismulti=False
      if len(self.parent)>1:
          ismulti=True
      return ismulti
  

  def configMulti(self,classDict):
    n2a=self.attributesByName()
    object_attribute_name_all={}
    type_attribute_name_all={}
    att_all={}
    for  att_name   in self.__attribute_name.keys():
            doadd=0
            if att_name in self.object_attribute_name:
                object_attribute_name_all[att_name]=att_name 
                doadd=1
            elif att_name in self.type_attribute_name:
                type_attribute_name_all[att_name]=att_name
                doadd=1
            if doadd==1:    
                self.__attribute_name_all[att_name]=1
                att=n2a[att_name]
                att_all[att_name]=att

    for  pn in self.parent: 
       cp=classDict[pn] 
       n2ap=cp.attributesByName()
       for  att_name   in cp.object_attribute_name:
            self.__attribute_name_all[att_name]=1
            att=n2ap[att_name]
            #print("B-",att_name,":",att)
            att_all[att_name]=att
            object_attribute_name_all[att_name]=att_name

       for  att_name   in cp.type_attribute_name:
            self.__attribute_name_all[att_name]=1
            att=n2ap[att_name]
            #print("C-",att_name,":",att)
            att_all[att_name]=att
            type_attribute_name_all[att_name]=att_name      
            
       self.object_attribute_name_all=list(object_attribute_name_all.values())
       self.type_attribute_name_all=list(type_attribute_name_all.values())
       self.attribute_all=list(att_all.values())
       print(self.attribute_all)
  """
  def configMultiV0(self,classDict):
    n2a=self.attributesByName()
    
    for  att_name   in self.__attribute_name.keys():
            doadd=0
            if att_name in self.object_attribute_name:
                self.object_attribute_name_all.append(att_name)
                doadd=1
            elif att_name in self.type_attribute_name:
                self.type_attribute_name_all.append(att_name)
                doadd=1
            if doadd==1:    
                self.__attribute_name_all[att_name]=1
                att=n2a[att_name]

                #print("A-",att_name,":",att)
                self.attribute_all.append(att)

    for  pn in self.parent: 
       cp=classDict[pn] 
       n2ap=cp.attributesByName()
       for  att_name   in cp.object_attribute_name:
            self.__attribute_name_all[att_name]=1
            att=n2ap[att_name]
            #print("B-",att_name,":",att)
            self.attribute_all.append(att)
            self.object_attribute_name_all.append(att_name)

       for  att_name   in cp.type_attribute_name:
            self.__attribute_name_all[att_name]=1
            att=n2ap[att_name]
            #print("C-",att_name,":",att)
            self.attribute_all.append(att)
            self.type_attribute_name_all.append(att_name)        
            
  """

  def appendValidParent(self,p):
     if not unexpected_name(p):
       self.parent.append(p)

  def has_unexpected_name(self):
   # management of blank node. e.g. for owl:range
   #<N14b5c94e6c124577b80891010b711d1f>======
   #dflib.term.BNode 
   # see http://www.w3.org/TR/rdf11-concepts/#section-skolemization
   
   return unexpected_name(self.name)

  def has_unexpected_parent(self):
   if self.is_root==False: 
     if self.parent is not None :
        for p in self.parent:
          if '<' in p:
             return True   
   return False

  def add_attribute(self,att,is_object):
      if att.name not in self.__attribute_name.keys():
            self.__attribute_name[att.name]=1
            self.attribute.append(att)
            if is_object==True:
               self.object_attribute_name.append(att.name)
            else:
               self.type_attribute_name.append(att.name)
  def attributesByName(self):
      n2a=dict()
      for att in self.attribute:
           n2a[att.name]=att
      return n2a
  
  def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)
    
  def __str__(self):
      return "name:%s;pk:%s;parent:%s" %(self.name,self.pk,self.parent)



class ModelToolBox():

  def __init__(self,classDict):
      self.version=1.0
      self.classDict=classDict
    
  def is_children_class_of(self,child,parent):
      

      is_children=False
      goon=True  
      clsname=child
      while goon==True:
        pmetaclassl=self.getMetaClassParentByClassName(clsname)
        if pmetaclassl is None or len(pmetaclassl)==0 :
             goon=False
        for pmetaclass  in pmetaclassl:
           clsname=pmetaclass.name 
           #print("  parent: %s"  %(clsname))
           if pmetaclass.name == parent:
               is_children=True
               goon=False
               
      return is_children

         
        
  def getMetaClassParentByClassName(self,clsname):
      if clsname in self.classDict.keys():
         cm=self.classDict[clsname]
         if cm.has_unexpected_name()==False:    
            metaclass=cm
            if metaclass.parent is not None:
                l=[]
                for p in metaclass.parent:
                   pmetaclass=self.getMetaClassByClassName(p)
                   l.append(pmetaclass)
                return l
      return []

  def getMetaAttributeByAttName(self,metaclass,attn,visited=dict()):
      ldebug=False
      #if attn=="dataSource":
      #   ldebug=True
      metaatt=None  
      if ldebug:
            if len(visited.keys())==0:
               print("-----START----")
            print("d* class %s , v %s"  %(metaclass.name, visited))
      for catt in metaclass.attribute: 
         if ldebug:
            print(catt.name)
         if catt.name ==attn:
            
            metaatt= catt
            if ldebug:
              print("*==metaatt==>%s %s %s" %(metaatt,metaatt.name,attn)) 
            return metaatt
      visited[metaclass.name]=1
      if metaatt is None and metaclass.parent is not None:
 
        for p in metaclass.parent:
          if p not in visited.keys(): 
           
           pmetaclass=self.getMetaClassByClassName(p)
           if ldebug:
             print("  dp class %s %s , v %s"  %(p,pmetaclass.name, visited)) 
           cattp=self.getMetaAttributeByAttName(pmetaclass,attn,visited)
           if cattp is not None:
              if cattp.name==attn:
                 metaatt= cattp
                 if ldebug:
                   print("==metaatt==>%s %s %s" %(metaatt,metaatt.name,attn)) 
                 return metaatt
           visited[p.name]=1
      if ldebug:
         print("==metaatt %s ==>None" %(attn) )  
            
      return None

  def getMetaAttributeFromHierarchy(self,metaclass):
      atts=list()  
      for catt in metaclass.attribute: 
         atts.append(catt)
      if metaclass.parent is not None:
        for p in metaclass.parent:
         pmetaclass=self.getMetaClassByClassName(p)
         if pmetaclass is not None:
           patts=self.getMetaAttributeFromHierarchy(pmetaclass)
           for patt in patts:
             atts.append(patt)  
      return atts

  def getMetaClassByClassName(self,cln):
       
      metaclass=None  
      if cln in self.classDict.keys():
            cm=self.classDict[cln]
            if cm.has_unexpected_name()==False:    
                metaclass=cm

      return metaclass

  def class_children(self,clsname):
      metaClass=self.getMetaClassByClassName(clsname)
      children=list()
      if metaClass is not None:    
          for chln in metaClass.children:
             children.append(chln)
             pchildClass=self.getMetaClassByClassName(chln)
             if pchildClass is not None:  
                 ccl=self.class_children(pchildClass.name)
                 for cl in ccl:
                     children.append(cl)

      children = list(set(children))                     
      return  children


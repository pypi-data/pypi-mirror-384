#!/usr/bin/env python
 

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

backup_stderr = sys.stderr
sys.stderr = open(os.devnull, "w")
from owlready2 import *
sys.stderr = backup_stderr



from  .utils import *
from  .meta_model import *


import logging as logger
logger.basicConfig(level=4, format='%(asctime)s - %(levelname)s - %(message)s')

EXPERIMENTAL_OVER=True
DEFINE_CARD=True

def extractstr(s,x,y):
    return s[x:y]

def find_indices(s, c):
    
    indices=[]
    index=-1
    for pos, char in enumerate(s):
        index+=1
        if char ==c:
            indices.append(index)

    return indices

def keeplast(txt, sep='.'):
    txt=str(txt)
    # Check if the separator is present in the string
    if sep in txt:
        # Split the string by the separator and return the last element
        return txt.split(sep)[-1]
    else:
        # Return the whole string if the separator is not present
        return txt
    
PREFX="""
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX dct: <http://purl.org/dc/terms/>

"""


queries_getFuncProp=PREFX+"""
SELECT ?property ?domain ?maxCardinality
WHERE {
    {
        ?property rdf:type owl:FunctionalProperty .
        ?property rdfs:domain ?domain .
        BIND(1 AS ?maxCardinality)
    }
    UNION
    {
        ?property rdf:type owl:InverseFunctionalProperty .
        ?property rdfs:domain ?domain .
        BIND(1 AS ?maxCardinality)
    }
}
"""
queries_getFuncPropSimple=PREFX+"""
SELECT ?property ?domain ?maxCardinality
WHERE {
    {
        ?property rdf:type owl:FunctionalProperty.
    }
    UNION
    {
        ?property rdf:type owl:InverseFunctionalProperty.
    }
}
"""


queries_getClasses=PREFX+"""
SELECT ?class (str(?classLabel) AS ?classLabelValue) ?classMetaClass
WHERE {
  VALUES ?classMetaClass { owl:Class rdfs:Class }
  ?class rdf:type ?classMetaClass .
  OPTIONAL { ?class rdfs:label ?classLabel . }
  FILTER NOT EXISTS {
    ?class owl:deprecated "true"^^xsd:boolean .
  }
}
"""

queries_getClassesV0=PREFX+"""

SELECT ?class (str(?classLabel) AS ?classLabelValue) ?classMetaClass
WHERE {
  VALUES ?classMetaClass { owl:Class rdfs:Class }
  ?class rdf:type ?classMetaClass .
  ?class rdfs:label ?classLabel .
  FILTER NOT EXISTS {
    ?class owl:deprecated "true"^^xsd:boolean .
  }
}
"""


queries_getAllComments=PREFX+"""
SELECT ?s ?o
 WHERE {
 ?s ?p ?o.
      ?s   rdfs:comment ?o .
 }
ORDER BY (?s)
"""



 

queries_getClassesHierarchy=PREFX+"""SELECT ?class ?superClass
WHERE {
  VALUES ?classMetaClass1 { owl:Class rdfs:Class }
  VALUES ?classMetaClass2 { owl:Class rdfs:Class }

  ?class rdf:type ?classMetaClass1 .
  FILTER NOT EXISTS {
    ?class owl:deprecated "true"^^xsd:boolean .
  }
  ?class rdfs:subClassOf ?superClass .
  ?superClass rdf:type ?classMetaClass2 .

  FILTER NOT EXISTS {
    ?superClass owl:deprecated "true"^^xsd:boolean .
  }
}
"""


queries_getProperties=PREFX+"""
SELECT ?property (str(?propertyLabel) AS ?propertyLabelValue) ?propertyType ?propertyDomain ?propertyRange
WHERE {
  VALUES ?propertyType { owl:ObjectProperty owl:DatatypeProperty rdf:Property }

  ?property rdf:type ?propertyType .
  OPTIONAL { ?property rdfs:label ?propertyLabel . }
  FILTER NOT EXISTS {
    ?property owl:deprecated "true"^^xsd:boolean .
  }

  OPTIONAL { 
    {
    ?property (rdfs:subPropertyOf*)/rdfs:domain ?propertyDomain .
    FILTER NOT EXISTS { ?propertyDomain owl:unionOf ?domainUnionValue . }
    }
    UNION
    {
    ?property (rdfs:subPropertyOf*)/rdfs:domain/owl:unionOf ?domainUnion .
    ?domainUnion (rdf:rest*)/rdf:first ?propertyDomain .
    }
  }

  OPTIONAL { 
    {
    ?property (rdfs:subPropertyOf*)/rdfs:range ?propertyRange .
    FILTER NOT EXISTS { ?propertyRange owl:unionOf ?rangeUnionValue . }
    }
    UNION
    {
    ?property (rdfs:subPropertyOf*)/rdfs:range/owl:unionOf ?rangeUnion .
    ?rangeUnion (rdf:rest*)/rdf:first ?propertyRange .
    }
  }
}
"""


queries_getPropertyRestrictionsGraph=PREFX+"""
SELECT ?property (str(?propertyLabel) AS ?propertyLabelValue) ?restrType ?propertyDomain ?propertyRange
WHERE {
  VALUES ?restrType { owl:someValuesFrom owl:allValuesFrom }
  ?propertyDomain rdfs:subClassOf ?restr .
  ?restr rdf:type owl:Restriction .
  ?restr owl:onProperty ?property .
  ?restr ?restrType ?propertyRange .

  OPTIONAL { ?property rdfs:label ?propertyLabel . }
  FILTER NOT EXISTS {
    ?property owl:deprecated "true"^^xsd:boolean .
  }
}
"""

queries_getPropertyRestrictions=PREFX+"""
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX dct: <http://purl.org/dc/terms/>

SELECT   (STRAFTER(STR(?propertyDomain), "#") AS ?propertyDomainID)  ?property     (STRAFTER(STR(?property), "#") AS ?propertyID) ?propertyLabel 
   (STR(?cardinality) AS ?cardinalityValue) (STR(?minCardinality) AS ?minCardinalityValue) (STR(?maxCardinality) AS ?maxCardinalityValue) 
 WHERE {
 
  ?propertyDomain rdfs:subClassOf ?restr .
  ?restr rdf:type owl:Restriction .
  ?restr owl:onProperty ?property .
 
  #OPTIONAL {
  #?property rdfs:range ?range .
  #?range owl:oneOf ?list .
  #?list rdf:rest*/rdf:first ?enumv . # for enum
  #}  
  OPTIONAL { ?property rdfs:label ?propertyLabel . }
  OPTIONAL { ?restr owl:cardinality ?cardinality . }
  OPTIONAL { ?restr owl:minCardinality ?minCardinality . }
  OPTIONAL { ?restr owl:maxCardinality ?maxCardinality . }
  
  FILTER NOT EXISTS {
    ?property owl:deprecated "true"^^xsd:boolean .
  }
}
""" 






class ModelProcessor():
    
  def __init__(self, rdfGraphObj,scriptDir,creation_mode="lib"):
     
      self.scriptDir=scriptDir
      self.classDict=dict()
      self.pref=":"
      self.line_wrap_size=80
      self.creation_mode=creation_mode
      self.owl_file=None
      self.onto=None
      self.meta_cls_attribute_lib=dict()
      self.domd=None
      self.extdomainlist = []
      self.extpackagelist = []
      if isinstance(rdfGraphObj,Graph):
         self.rdfGraph =rdfGraphObj
      elif isinstance(rdfGraphObj,str): 
         self.owl_file=rdfGraphObj
         self.rdfGraph =self.load_graph(self.owl_file)

  def formatUriStr(self,suri):
   r=self.rdfGraph.namespace_manager.normalizeUri(suri)
   s=self.clean2p(r)
   ixl=find_indices(s,"'")
   if len(ixl)>=2:
     r=extractstr(s,ixl[0]+1,ixl[1])
   return r 
  def clean2p(self,str):
    #print(str)
    str2= str.replace(":",  self.pref)
    return str2      
  def formatstr(self,str):
    #print(str)
    str2= self.clean2p(str)
    if str2.startswith("<N"):
    #fixed blank nodes issue for dot generation
       str2=str2.replace("<","").replace(">","")
    #print(str2)   
    return str2
  
  def load_graph(self,gpath):

         rdfFormat = {}
         rdfFormat['.owl'] = 'xml'
         rdfFormat['.ttl'] = 'ttl'
         dsFormat = rdfFormat[pathlib.PurePath(gpath).suffix]
         rdfGraph = rdflib.Graph()
         #rdfGraph.load(gpath, format=dsFormat) #error caused by rdflib changed
         #fixed 
         rdfGraph.parse(gpath, format=dsFormat)
         return rdfGraph





  
    
  def defineClassHierarchy(self):
    keys=list(self.classDict.keys())
    for k in keys:
      clmodel=self.classDict[k]
      for p in clmodel.parent:
        if p in keys:
          clmodel.is_root=False 
        else:
          if p is not None:
           
            rdf_type=clmodel.prefix+":"+p 
            logger.info("WARNING: parent class  %s not in classDict, creating it with  infered rdf_type %s" %(clmodel.parent,rdf_type))
            clmodel_root=TClassModel(p, None,self.domain,self.prefix,rdf_type)
            clmodel_root.is_root=True
         
            self.addClass(clmodel_root)
            #print(">>>>>>>><new class n0  %s" %(clmodel_root.name))
    


    keys=list(self.classDict.keys())
    for k in keys:
      clmodel=self.classDict[k]
      for p in clmodel.parent:
        if p is not None and p in keys:
          clmodel_parent=self.classDict[p]
          clmodel_parent.children.append(clmodel.name) 
          

  def displayChildren(self):

    keys=list(self.classDict.keys())
    for k in keys:
      clmodel=self.classDict[k]
      for p in clmodel.parent:
        if p is not None and p in keys:
          clmodel_parent=self.classDict[p]
          print("--%s has child %s" %(clmodel_parent.name,clmodel.name))
            
  def displayParent(self):

    keys=list(self.classDict.keys())
    for k in keys:
      clmodel=self.classDict[k]
      print("--%s has parent %s" %(clmodel.name,clmodel.parent))

  def defineAllParents(self,metacl):
    ct=0
    all_parents = set()  # Use a set to avoid duplicates
    
    def _get_all_parents(instance,ct):
        
        for parentn in instance.parent:
            
            #print("@@@@",ct,"  ",parentn)
            parent=self.classDict[parentn]
            if parent not in all_parents:
                all_parents.add(parentn)
                ct=ct+1
                _get_all_parents(parent,ct)
     
    _get_all_parents(metacl,ct)

    return list(all_parents)          


  def createOntologySchemaGraph(self, filePath=""):
    schemaGraph = graphviz.Digraph('G')
    #schemaGraph.attr(rankdir="LR")
    schemaGraph.attr(rankdir="BT")

    prefixToNamespace = {}
    namespaceToPrefix = {}
    for currentNS in self.rdfGraph.namespace_manager.namespaces():
        prefixToNamespace[currentNS[0]] = currentNS[1]
        namespaceToPrefix[currentNS[1]] = currentNS[0]

    sparqlQuery =queries_getClasses
     
    
    qres = self.rdfGraph.query(sparqlQuery)
    for row in qres:
        nodeIdent = self.formatUriStr(str(row[0]))
        nodeLabel = str(row[1])
        schemaGraph.node(nodeIdent, label=nodeLabel + "\n" + self.formatUriStr(str(row[0])), shape='box', color='black', fontcolor='black')

    sparqlQuery =queries_getClassesHierarchy
     
    qres = self.rdfGraph.query(sparqlQuery)
    for row in qres:

        sourceIdent = self.formatstr(self.formatUriStr(str(row[0])))

        destIdent = self.formatstr(self.formatUriStr(str(row[1])))
        schemaGraph.edge(sourceIdent, destIdent, arrowhead='onormal')
    sparqlQuery =queries_getProperties
     
    qres = self.rdfGraph.query(sparqlQuery)
    for row in qres:
        if row[3] == None or row[4] == None:
            continue
        propIdent = self.formatstr(self.formatUriStr(str(row[0])))
        propLabel = str(row[1])
        if propLabel == "":
            propLabel = self.formatUriStr(str(row[0]))
        else:
            propLabel += "\n" + self.formatUriStr(str(row[0]))
        propType = self.formatUriStr(str(row[2]))
        sourceIdent = self.formatUriStr(str(row[3]))
        destIdent = self.formatstr(self.formatUriStr(str(row[4])))
        if propType == 'owl:ObjectProperty':
            schemaGraph.edge(sourceIdent, destIdent, label=propLabel)
        elif propType == 'owl:DatatypeProperty':
            destIdent = 'str' + str(time.time())
            schemaGraph.node(destIdent, label=self.formatUriStr(str(row[4])), shape='box', color='black', fontcolor='black', style='rounded')
            schemaGraph.edge(sourceIdent, destIdent, label=propLabel)
    sparqlQuery =queries_getPropertyRestrictionsGraph
     
    qres = self.rdfGraph.query(sparqlQuery)
    for row in qres:
        propIdent = self.formatstr(self.formatUriStr(str(row[0])))
        propLabel = str(row[1])
        if propLabel == "":
            propLabel = self.formatUriStr(str(row[0]))
        restrType = self.formatUriStr(str(row[2]))
        sourceIdent = self.formatstr(self.formatUriStr(str(row[3])))
        destIdent = self.formatstr(self.formatUriStr(str(row[4])))
        if restrType == 'owl:someValuesFrom':
            schemaGraph.edge(sourceIdent, destIdent, label=propLabel + " (some) ", color='grey', fontcolor='grey', arrowhead='odot')
        elif restrType == 'owl:allValuesFrom':
            schemaGraph.edge(sourceIdent, destIdent, label=propLabel + " (all) ", color='grey', fontcolor='grey', arrowhead='oinv')

    schemaGraph.save(filename=filePath)            

  def dump_meta_model(self,  fpath):  

    with open(fpath, 'wb') as f:
       m={}
       m['prefix']=self.prefix   
       m['domain']=self.domain   
       m['classDict']=self.classDict   
       dill.dump(m,f, byref=True)

  def createObjectModelGraph(self,domain=None, prefix=None):
         return self.createObjectModelGraphImplLib(domain, prefix)
        
 
  def define_ontology(self):
    if self.owl_file is None:
        print("error: missing owl_file attribute is None")
        return None
    self.onto = get_ontology("file://"+self.owl_file).load()

  def describe_ontology(self):
   
   if self.onto is None:
        print("error: onto attribute  is None")
        return None
  
   cllist=list(self.onto.classes())
   for cl in cllist:
      print("==================")
      print("cl.name:%s,cl.is_a:%s" %(cl.name,cl.is_a))
      print("subclasses:%s" %(list(cl.subclasses())))
      print("ancestors:%s" %(cl.ancestors()))

   proplist=list(self.onto.object_properties())
   for prop in proplist:
      print("  obj prop:%s , domain:%s, range:%s"%(prop,prop.domain,prop.range))
    
   proplist=list(self.onto.data_properties())
   for prop in proplist:
      print("  data prop:%s  %s   , domain:%s, range:%s"%(prop._name,prop,prop.domain,prop.range))
      print("  data prop-class:%s , dir:%s"%(prop.__class__,dir(prop) ))
      for k in prop.__dict__.keys():
          print("%s=%s" %(k,prop.__dict__[k]))
#  data prop:biopax-level3.templateDirection , domain:[biopax-level3.TemplateReaction], range:[OneOf(['FORWARD', 'REVERSE'])]

  def extract_ontology_classes(self):
   
   if self.onto is None:
        print("error: onto attribute  is None")
        return None  
    
   class_names = [cls.name for cls in self.onto.classes()]
   for cln in class_names:
      self.meta_cls_attribute_lib[cln]=dict()
    
   proplist=list(self.onto.data_properties())
   for prop in proplist:

      name=str(prop._name)
      domain_list=prop.domain
      for domain in domain_list:
          arr=str(domain).split(".")
          cln=arr[len(arr)-1]
          #print("==%s" %(cln))
          self.meta_cls_attribute_lib[cln]=dict()

      tp=None
      xtp=None
      base=True
      att=TAttributeModel(name,base,tp,xtp)
      self.meta_cls_attribute_lib[cln][att.name]=att
      #'name', 'base', 'tp', and 'xtp'          
      range_list=prop.range
      for rang in range_list:
          #print("==>RANGX:%s" %(rang.__class__.__name__))
          if isinstance(rang,OneOf):
             enum_val=list()
             for v in rang.instances:
                 enum_val.append(str(v))
             #print("ONEOF!! %s " %(enum_val)) 
             att.enum_values=enum_val
             att.xtype="xsd:string"
             att.type="str"
          elif isinstance(rang,type):
             #print("TYPE!!")
             att.enum_values=None


 

  def addClass(self,cm):
     mh=0
     if cm.name in self.classDict.keys():
        fcm=self.classDict[cm.name]
        for fcmp in fcm.parent:
         for cmp in cm.parent:
           if fcmp is not None and fcmp != cmp:
            logger.info(">>>multiple inheritance  for class %s " %(cm.name))
            if unexpected_name(cmp)==True:
               logger.info("unexp %s" %(cmp))
            else:
              logger.info("exp %s" %(cmp))
              fcm.parent.append(cmp)
              self.classDict[fcm.name]=fcm
              mh=1
        
     if mh==0:      
      self.classDict[cm.name]=cm

  def defineComment(self,el,com):
     el.comment=wrap(com,self.line_wrap_size)
     el.rawcomment=com
  
  def propByDomain(self, cm_name,att_name,propType) :
      domd=self.domd
      ret=False
      if cm_name in domd.keys():
         propl=domd[cm_name][propType]
         if att_name in propl:
            ret=True
      if '__ANY_DOM__' in domd.keys():
         propl=domd['__ANY_DOM__'][propType]
         if att_name in propl:
            ret=True
      return ret
     
  def propertiesByDomain(self):

    ak='__ANY_DOM__'
    cllist=list(self.onto.classes())
    domd={} 
    domd[ak]={'data':[],'object':[]} 
    for cl in cllist:
      domd[keeplast(cl.name)]={'data':[],'object':[]}
 

    oproplist=list(self.onto.object_properties())
    for prop in oproplist:
      #print("  obj prop:%s , domain:%s, range:%s"%(prop.name,prop.domain,prop.range))
      pdoml=[]
      # hack to fix strange behaviour with pipe in prop.domain
      for pdomr in prop.domain :
         v1=str(pdomr)
         vl=v1.split("|")
         for v in vl:
             pdoml.append(v.strip())

      for pdom in pdoml:
        cln=keeplast(pdom)
        #print("--->",cln,"  ", prop.name)
        if cln in domd.keys():
            domd[cln]['object'].append(keeplast(prop.name))
        else:
            print("error"+cln+"not found in dom")
      if len(prop.domain)==0:  
         domd[ak]['object'].append(keeplast(prop.name))




    dproplist=list(self.onto.data_properties())
    for prop in dproplist:
      #print("  obj prop:%s , domain:%s, range:%s"%(prop.name,prop.domain,prop.range))

      pdoml=[]
      # hack to fix strange behaviour with pipe in prop.domain
      for pdomr in prop.domain :
         v1=str(pdomr)
         vl=v1.split("|")
         for v in vl:
             pdoml.append(v.strip())

      for pdom in pdoml:

        cln=keeplast(pdom)
 
        if cln in domd.keys():
            domd[cln]['data'].append(keeplast(prop.name))
        else:
            print("error"+cln+"not found in dom")
      if len(prop.domain)==0: # strange prop without domain like StandardName
         domd[ak]['data'].append(keeplast(prop.name))

    return domd
  def createObjectModelGraphImplLib(self,domain=None, prefix=None):
    #print("start")
    self.domain=domain
    self.prefix=prefix

    self.define_ontology()
    #self.describe_ontology()
    self.extract_ontology_classes()


    self.domd=self.propertiesByDomain()
    ########debug
    #with open('/tmp/domd.json', 'w') as sfp:
    #   json.dump(self.domd, sfp)
    #####
    comment=dict()
     

    prefixToNamespace = {}
    namespaceToPrefix = {}
    for currentNS in self.rdfGraph.namespace_manager.namespaces():
        prefixToNamespace[currentNS[0]] = currentNS[1]
        namespaceToPrefix[currentNS[1]] = currentNS[0]
    docomment=True
    if docomment==True:
      # a data prop sub case
      #  data prop:biopax-level3.comment , domain:[biopax-level3.Entity | biopax-level3.UtilityClass], range:[<class 'str'>]
      sparqlQuery =queries_getAllComments
       
      qres = self.rdfGraph.query(sparqlQuery)
      for crow in qres:
        csuri=str(crow[0])
        cval=str(crow[1])
        comment[csuri]=cval

        
        
    sparqlQuery =queries_getClassesHierarchy
     
    qres = self.rdfGraph.query(sparqlQuery)
    classParent=dict() #for root class management
    print(">>>>>>get_class hierarchy")
    for row in qres:
        #print(row)
        sourceuri=str(row[0])
        desturi=str(row[1])
        #print(type(sourceuri)) 
        #print(type(desturi)) 
        #ur=URIRef(desturi)
        #print(type(ur)) 
        #print(ur.defrag()) 
        

        sourceIdent = self.formatUriStr(sourceuri)
        destIdent = self.formatUriStr(desturi)
         
        cm_name=removeFirst(sourceIdent,self.pref)
        cm_parent=removeFirst(destIdent,self.pref)
        #print("cm_parent:%s  cm_name:%s" %(cm_parent,cm_name))
        #rdf_type=self.prefix+":"+cm_name # prefixed version
        rdf_type=sourceuri # long version
        cm=TClassModel(cm_name , cm_parent,self.domain,self.prefix,rdf_type)
        cm.pk=sourceuri
        #p_rdf_type=self.prefix+":"+cm_parent # prefixed version
        p_rdf_type=desturi # long version
        cp=TClassModel(cm_parent,None,self.domain,self.prefix,p_rdf_type)
        cp.pk=desturi
        if cp.name is not None:
           classParent[cp.name]=cp
        if cm.pk in comment.keys(): 
            self.defineComment(cm,comment[cm.pk])
        if cm.name is not None:   
           #print(">>>>>>>><new class n5  %s" %(cm.name)) 
            
           self.addClass(cm)

        
        
    sparqlQuery =queries_getClasses
     
    qres = self.rdfGraph.query(sparqlQuery)
    logger.info("get_classes")
    for row in qres:
        #logger.info(row)

        sourceuri=str(row[0])
        sourceliteral=str(row[1])
        sourcetypeuri=str(row[2])
        
        source = self.formatUriStr(sourceuri)
        sourcetype = self.formatUriStr(sourcetypeuri)
          
        cm_name=removeFirst(source,self.pref)
        
        #rdf_type=self.prefix+":"+cm_name # prefixed version
        rdf_type=sourceuri # long version
        
        cm=TClassModel(cm_name , None,self.domain,self.prefix,rdf_type)
        cm.pk=sourceuri
        #logger.info(">>>>>>>>!  %s  %s" %(cm.name,cm.pk))
        if cm.pk in comment.keys():
            
            self.defineComment(cm,comment[cm.pk])
        if cm.name is not None and cm.name not in self.classDict.keys() :    
           
           self.addClass(cm)
           #logger.info(">>>>>>>><new class  n4 %s" %(cm.name))
    
 
        
        
        
    for cp_name in classParent.keys():
        if cp_name is not None and cp_name not in self.classDict.keys():
            cp=classParent[cp_name]
            if cp.pk in comment.keys():
              
              self.defineComment(cp,comment[cp.pk])
            self.addClass(cp)
            #print(">>>>>>>><new class n3  %s" %(cp.name))
            
        
    sparqlQuery =queries_getProperties
     
    qres = self.rdfGraph.query(sparqlQuery)
    for row in qres:
        #print("===========+++++++==============")
        #print(row)
        
        if row[3] == None or row[4] == None:
            continue
        attsourceuri=str(row[0])
        propIdent = self.formatUriStr(attsourceuri)
        
        propLabel = str(row[1])
        attname=None
        
        if propLabel == "":
            propLabel = self.formatUriStr(attsourceuri)
            attname=propLabel
        else:
            propLabel += "\n" + self.formatUriStr(attsourceuri)
            attname=self.formatUriStr(attsourceuri) 
        attname=removeFirst(attname,self.pref)
        
        propType = self.formatUriStr(str(row[2]))
        
        sourceIdent = self.formatUriStr(str(row[3]))

        
        atttype = self.formatUriStr(str(row[4]))
        #print("==========")
        #print(row)
        #print(" 1 %s  :  %s %s %s" %(sourceIdent,atttype,propType,propLabel.strip()))
        if propType == 'owl:ObjectProperty':
            clsname=removeFirst(sourceIdent,self.pref)
            if clsname in self.classDict:
                cm=self.classDict[clsname]
                tp=removeFirst(atttype,self.pref)
                xtp=str(row[4])
                

                ################
                # external type management
                is_external=False
                if "<" in tp and len(self.extdomainlist)>0 and  len(self.extpackagelist)>0:
              
                  prefixed_class = convert_rawtype_to_prefixed(tp, self.extdomainlist, self.extpackagelist)
                  if prefixed_class is not None:
                    
                     tp=prefixed_class
                     is_external=True
                ################
                
                att=TAttributeModel(attname,False,tp,xtp)
                 
                att.external=is_external
                if attsourceuri in comment.keys():    
                   self.defineComment(att,comment[attsourceuri])

                #print(att.name, att.type,att.xtype,"   atttype: ",atttype," added") 
                 
                if self.propByDomain(cm.name,att.name,'object')==True:
                   cm.add_attribute(att,True) 


        elif propType == 'owl:DatatypeProperty':
            #print("3 %s  :  %s" %(propType,propLabel))
              

            clsname=removeFirst(sourceIdent,self.pref)
            
            
            
            if clsname in self.classDict:
                cm=self.classDict[clsname]
                xtp=removeFirst(atttype,self.pref)
                tp=schemaType2PythonType(xtp,row[4])
                att=TAttributeModel(attname,True,tp,xtp)
                #print("___ add att %s " %(attname))
                if attsourceuri in comment.keys():
                   
                   self.defineComment(att,comment[attsourceuri])
                if self.propByDomain(cm.name,att.name,'data')==True:
                   cm.add_attribute(att,False)
            else:
                logger.info("warning: %s not in classDict. %s" %(clsname,row ) )
  
            
            
    sparqlQuery =queries_getPropertyRestrictions
     
    qres = self.rdfGraph.query(sparqlQuery)
    #print("::",len(qres))
    global DEFINE_CARD
    if DEFINE_CARD==True:
      ct=0
      for row in qres:
        ct=ct+1
        #print("::",ct,"  ",row) 
        try:
         #print("--defineCard--")
         self.defineCard(row)
        except Exception as ex:
          logger.info("defineCard error:%s  " %(ex  ))

        #print("::end")             
    

    for cln in self.meta_cls_attribute_lib.keys():
        metaclass=self.classDict[cln]
        attd={}
        for attr in metaclass.attribute:
           attd[attr.name]=attr
        att_dict=self.meta_cls_attribute_lib[cln]

        for att in metaclass.attribute:
            if att.name in att_dict.keys():
               attx=att_dict[att.name]
               if attx.enum_values is not None:
                 att.enum_values=attx.enum_values           
                 att.xtype=attx.xtype
               if attx.list is not None:
                 att.list=attx.list           
               if attx.min is not None:
                 att.min=attx.min   
               if attx.max is not None:
                 att.max=attx.max   
               if attx.nullable is not None:
                 att.nullable=attx.nullable 

        

        global EXPERIMENTAL_OVER
        if EXPERIMENTAL_OVER==True:
          att_dict=self.meta_cls_attribute_lib[cln]
          #overwritting management 
          for anm,attx in att_dict.items():
            
            if attx.overwrite==True:
               print(cln, "!!!attx: ",attx.name,attx.list,attx.min,attx.max, attx.nullable)
               if attx.name in attd.keys():
                  att=attd[attx.name]
               else:
                  att=attx
               
               if attx.enum_values is not None:
                 att.enum_values=attx.enum_values           
                 att.xtype=attx.xtype
               if attx.list is not None:
                 att.list=attx.list           
               if attx.min is not None:
                 att.min=attx.min   
               if attx.max is not None:
                 att.max=attx.max   
               if attx.nullable is not None:
                 att.nullable=attx.nullable    

    return 
  
  def defineCardFromFuncProp(self):
      fpropbydom={}
      

      qres = self.rdfGraph.query(queries_getFuncProp)
      allp={}
      for row in qres:
         row_property = self.formatUriStr(str(row[0]))
         row_domain = self.formatUriStr(str(row[1]))
         row_domain=row_domain.lower()
         row_cardinality = int(row[2])
         fp=None
         if row_domain in  fpropbydom.keys():
            fp=fpropbydom[row_domain]
         else:
            fp={}
         fp[row_property.lower()]=row_cardinality
         fpropbydom[row_domain]=fp
         allp[row_property.lower()]=1

      qres0 = self.rdfGraph.query(queries_getFuncPropSimple)
      ak='__ANY_DOM__'  # prop without domain  like displayName or standardName in BIOPAX Level 3

      for row in qres0:
         row_property = self.formatUriStr(str(row[0]))
         if row_property.lower() not in allp.keys():
           fp=None
           if ak in  fpropbydom.keys():
            fp=fpropbydom[ak]
           else:
            fp={}
         
           fp[row_property.lower()]=1
           fpropbydom[ak]=fp

      return fpropbydom
    
  def defineCard(self,row):
 
        global EXPERIMENTAL_OVER


        fprop= self.defineCardFromFuncProp()
        #print(json.dumps(fprop))
        
        sourceDomIdent =   strOrNone(row[0]) 
        
        propIdentOp = self.formatUriStr(str(row[1]))
        propIdent = strOrNone(row[2]) 
        propLabel = strOrNone(row[3])
        #print(">>>>>>>>>><defineCard" ) 
        if propLabel is None  :
            if propIdent is not None:
               propLabel = propIdent
        if propLabel is None :
            if propIdentOp is not None:
               propLabel = propIdentOp
        #print(" ::propLabel::",propLabel) 
        cardinality=None
        va=strOrNone(row[4])
        try:
          cardinality=int(va)
        except:
          #print("cardinality:%s" %(va))
          cardinality=None
        
        
        
        minCardinality=None
        va=strOrNone(row[5])
        try:
          minCardinality=int(va)
        except:
          #print("minCardinality:%s" %(va))
          minCardinality=None

        maxCardinality=None
        va=strOrNone(row[6])
        try:
          maxCardinality=int(va)
        except:
          #print("maxCardinality:%s" %(va))
          maxCardinality=None

        islist=True
        nullable=True



       
       
        clsname=removeFirst(sourceDomIdent,self.pref)
        attname=propLabel
        #funstionalProperties analysis
        if clsname.lower() in fprop.keys():
           fpropdict=fprop[clsname.lower()]# prop with domain  
           if attname.lower() in  fpropdict.keys():
              cardinality=1
              maxCardinality=1
        ak='__ANY_DOM__' # prop without domain  
        if ak in fprop.keys():
           fpropdict=fprop[ak]
           if attname.lower() in  fpropdict.keys():
              cardinality=1
              maxCardinality=1
         

         
        if cardinality is not None and cardinality == 1:
           islist=False

        if cardinality is not None and cardinality > 1:
           islist=True
        if minCardinality is not None  and  minCardinality >1: 
           islist=True
        if maxCardinality is not None  and  maxCardinality >1: 
           islist=True
        if cardinality is not None  :
           nullable=False
        if minCardinality is not None  and  minCardinality >=1: 
           nullable=False


        allclsk=self.classDict.keys()
       
        if clsname  in allclsk:
           metaclass=self.classDict[clsname]
            
           attd={}
           
           for patt in metaclass.attribute:    
                attd[patt.name]=patt
           
           att_dictp={}
           allparents=self.defineAllParents(metaclass)
           for pacls in allparents:
               #print("--@@:",pacls)
               pmetaclass=self.classDict[pacls]
               patt_lst=pmetaclass.attribute
               for patt in patt_lst: 
                    if patt.name not in  attd.keys():      
                       attd[patt.name]=patt # FIXME  --> needed for list=True in participant for example
                    att_dictp[patt.name]=1 # to manage overwriting cardinality for parent att
           ## warning: cardinality defined on parent attributes
           # example GeneticInteraction:participant
           # not managed during class generation-> fixme
           att_lst=list(attd.values())
           ispresent=False
           for att in att_lst:
            if attname == att.name:
              if clsname in  self.meta_cls_attribute_lib.keys() :
                 if att.name in self.meta_cls_attribute_lib[clsname].keys():
                    ispresent=True
 
              addedinfo=False
              
              if minCardinality is not None:
                  addedinfo=True
                  
              if maxCardinality is not None:
                  if att.name in att_dictp.keys():
                    addedinfo=True
                  
              if nullable is not None and nullable==False:
                  addedinfo=True
                  
              if islist ==True:
                 addedinfo=True
                  
              if addedinfo==True: 
                 
                 if ispresent==True:
                    attc=self.meta_cls_attribute_lib[clsname][att.name]
                 else:
                    attc=att  
                 attc.list=islist
                 attc.min=minCardinality
                 attc.max=maxCardinality
                 attc.nullable=nullable
                 #print(clsname, "!!!     >>>att  ",attc, attc.list, attc.min, attc.max,attc.nullable)
                 if  att.name in att_dictp.keys(): # parent att
                  if EXPERIMENTAL_OVER==True:
                    att.overwrite=True #overwrite cardinality prop like min, max, list, nullable
                    #print(clsname, "!!!over--------------    >>>att  ",att, att.list, att.min, att.max,att.nullable)
                    self.meta_cls_attribute_lib[clsname][att.name]=attc

                 else:
                   self.meta_cls_attribute_lib[clsname][att.name]=attc
              
              break
        return              

def strOrNone(v):
   if v is None:
      return v
   else:
      return str(v)

def convert_rawtype_to_prefixed(rawtype, extdomainlist, extpackagelist):
    # Remove angle brackets if present
    rawtype = rawtype.strip('<>').strip()

    # Iterate through extdomainlist and extpackagelist
    for i, domain in enumerate(extdomainlist):
        if rawtype.startswith(domain):
            # Get the corresponding package prefix
            package_prefix = extpackagelist[i]

            # Extract the class name from rawtype
            class_name = rawtype[len(domain):].lstrip('#/')

            # Combine package prefix and class name
            prefixed_class = f"{package_prefix}.{class_name}"
            return prefixed_class

    # If no match is found, return None or handle the case as needed
    return None

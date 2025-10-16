

import os

import graphviz
import networkx as nx
from networkx.drawing.nx_agraph import write_dot
import pathlib

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


import rdflib



show_log_info=False


#python in memory
#blacklist implementation
 


def constantDict():
    cd={}
    cd['type_suffix']="__rdft"


    cd['common_prefixes']={
         "rdf":"http://www.w3.org/1999/02/22-rdf-syntax-ns#",
         "rdfs":"http://www.w3.org/2000/01/rdf-schema#",
         "owl":"http://www.w3.org/2002/07/owl#",
         "xsd":"http://www.w3.org/2001/XMLSchema#"
      }
    cd['type_predicate']="rdf:type"

    return cd

def load_meta_instance(fpath):
    obj=None
    with open(fpath, 'rb') as f:
       obj = dill.load(f) #, ignore=True
    return obj

def load_cls_instance(fpath):
    m=load_meta_instance(fpath)
    obj=m['classDict']
    return obj

def  unexpected_name(name):
   if  '<' in  name:
           return True
   return False

def wrap(content, w):
    
    content = content.replace("\\n", " ")
    content = content.replace("\\r", "")

    txt= textwrap.fill(content, w)
    arr=txt.split("\n")
    #print(arr)
    r=""
    for el in arr:
        #print(el)
        el="##   "+ el+"\n"
        r=r+el
    return r

def enable_sparql_local_file_query():
    
  rdfextras.registerplugins() # so we can Graph.query()

def define_graph_from_file(filename):

  enable_sparql_local_file_query()

  g=rdflib.Graph()
  g.parse(filename)

  return g


def sparql_query_from_file(g,query):
      
  results = g.query(query)
  #dir(results)
  #print("==========")
  #for result in results:  
  #  print(str(result)+"     ")
  return results

def flatten_collec(collec):
    flattened_collec = []
    
    for ent in collec:
        if isinstance(ent, list):
            flattened_collec.extend(ent)  # Add all items in the nested list to the flattened list
        else:
            flattened_collec.append(ent)  # Add the single item to the flattened list
    
    return flattened_collec

def always_list(obj):
    if obj is None:
        return None
    elif isinstance(obj, list):
        return obj
    else:
        return [obj]

def log_info(msg):

   if show_log_info==True:
     print("info: %s" %(msg) )

def schemaType2PythonType(xtype,uriref,ns_map=None):
    
    default_type='str'
    
    if ns_map is None:

        ns_map  = {'xsi':"http://www.w3.org/2001/XMLSchema-instance", 
         'xsd': "http://www.w3.org/2001/XMLSchema",
         'xs': "http://www.w3.org/2001/XMLSchema"        
          }
    
    if  "<" in xtype:
        #print("warning possible blank node (range/domain...) not managed by this implementation :======%s======" %(xtype))
        return default_type
    
     
    #print("xtype : %s ; uriref:%s" %(xtype,uriref) )
    if "rdfs:Literal" in xtype:
        #print("   xtype : %s ; uriref:%s" %(xtype,URIRef(uriref)) )
        return default_type
    
    try:
        namespace, suffix = QNameConverter.resolve(xtype, ns_map)

        #print("%s  / %s" %(namespace,suffix) )
    
        qname = build_qname(namespace, suffix)
        datatype = DataType.from_qname(qname)
        #print(datatype)
        cls_name=datatype.type.__name__
    except :
            einf=sys.exc_info()
            print(" schemaType2PythonType error: %s" %(einf[0]))
            cls_name='str'
        
    return cls_name



def removeFirst(s,ch):

        if s.startswith(ch)==True:
            st=s[1:]
        else:
            st=s
        
        return st

def is_leaf_class(cls):
    return not any(issubclass(sub_cls, cls) for sub_cls in cls.__subclasses__())

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

from urllib.parse import urlparse
import networkx as nx
from itertools import islice
import operator
from .utils import flatten_collec, always_list


has_gt=None
try:
   import  graph_tool.all as gt
   has_gt=True
   
except:
   has_gt=False



class GraphModelLayer():
    
   def __init__(self):
    self.g = nx.DiGraph() 
    self.nodeIdMap=dict()
    self.maxid=0



   def visited(self,n):
       if n in  self.nodeIdMap.keys():
         return True
       else:
         return False
   def nodeId(self,n):
       nid=None
       if n in  self.nodeIdMap.keys():
         nid= self.nodeIdMap[n] 
       return nid

   def defineId(self,n):
       nid=None
       if n in  self.nodeIdMap.keys():
         nid= self.nodeIdMap[n]
       else:
         self.maxid=self.maxid+1
         nid=self.maxid 
         self.nodeIdMap[n]=nid
       return nid

   def write_graphml(self,file):
       nx.write_graphml(self.g,file)
        
        
   def add_node(self,cln):
     nid=self.defineId(cln)
     self.g.add_node(nid,name=cln)
     return nid

   def build(self,gu):
    for cln in gu.classes():
      #print(cln)
      if not self.visited(cln):
        nid1=self.add_node(cln)
        #print(cln," ",nid1)
        inst=gu.createInstance(cln)
        ol=inst.object_attributes()
        tl=inst.type_attributes()
        ma=inst.attribute_type_by_name()
        m1=dict()
        for t in tl:
            if t != "name":
              m1[t]="NA"
   
        nx.set_node_attributes(self.g, {nid1:m1})
        #print(ma)
        for att in ol:
          pcln=ma[att]
          nid2=None
          if not self.visited(pcln):
            nid2=self.add_node(pcln)
            #pma=inst.attribute_type_by_name()
            tl2=inst.type_attributes()
            m2=dict()
            for t in tl2:
              if t != "name":
                m2[t]="NA"
          
            nx.set_node_attributes(self.g, {nid2:m2})
          else:
            nid2=self.nodeId(pcln) 
          #print("   ",att," ", pcln,"  ",nid1,"  ",nid2)
          self.g.add_edge(nid1,nid2,weight=10,name=att)
        
    






class GraphDatasetLayerAbsBK():
    
   def __init__(self):
       self.back=None
       self.initialize()  

   def initialize(self):         
     self.g = self.newGraph()
     
     self.nodeIdMap=dict()
     self.maxid=0
     self.nodeid2val={}
     self.val2nodeid={}

   def newGraph(self):
      #print("new graph from nx")
      gr=nx.Graph()
      self.back="NX"
      return gr

   def write_graphml(self,file):
       nx.write_graphml(self.g,file)
    
   def write_gexf(self,file):
       nx.write_gexf(self.g,file)
        
   def clone_node(self,g,nid,attdict):
      g.add_node(nid) 
      nx.set_node_attributes(g, {nid:attdict})   

   def add_node(self,obj):
     nid=self.defineId(obj)
 
     cln=type(obj).__name__
     nm=obj.pk
     if "_displayName" in  obj.__dir__():
        nm=obj._displayName
     if nm is None:
        nm=obj.pk
        
     self.g.add_node(nid,name="%s" %(nm),pk=obj.pk,rdf_type=obj.rdf_type, ctype=cln)
     return nid
   
   def selectNodeByAttributeValue(self,att,val):
     ll=[]
     for n,v in  self.g.nodes(data=True):
      #print(v)
      if val in v[att]  :
        ll.append(n)
        
     return ll

   def indexNodeAttValues(self):
     self.nodeid2val={}
     attnl = {}
     
     nodesl=self.g.nodes(data=True)
     for n, d in nodesl:
       attnl=list(d.keys())
       break
     
     for nn, d in nodesl: 
       self.nodeid2val[nn] = {}
       for an in attnl:
         self.nodeid2val[nn][an]=None
         if an in d.keys():
            self.nodeid2val[nn][an]=d[an]
         
     return  self.nodeid2val



   def revIndexNodeAttValues(self):
     
     self.val2nodeid={}
     attnl = {}
     
     nodesl=self.g.nodes(data=True)
     for n, d in nodesl:
       attnl=list(d.keys())
       break
     for an in attnl: 
       #print(an)
       self.val2nodeid[an] = {}

     for an in attnl: 
      atvalues = self.val2nodeid[an]
      for n, d in nodesl:
        if an in d.keys(): 
          l = d[an]
          #print(an)
          #print("   ",l)
          atvalues[l] = atvalues.get(l, [])
          atvalues[l].append(n)
      self.val2nodeid[an]=atvalues   
     return  self.val2nodeid
      
     
   def init_index(self):
     if len(list(self.nodeid2val.keys()))==0:
      self.indexNodeAttValues()  

   def add_edge(self,nid1,nid2,weight,name):
       self.g.add_edge(nid1,nid2,weight=weight,name=name)      


   def set_node_attributes(self,g,nid,mat):
      nx.set_node_attributes(g, {nid:mat})

   def k_shortest_paths(self, source, target, k, weight=None):
     try:
       pl= list(islice(nx.shortest_simple_paths(self.g, source, target, weight=weight), k))
     except nx.NetworkXNoPath:
       pl=[]
     return pl




class GraphDatasetLayerAbs(GraphDatasetLayerAbsBK):
    
   def __init__(self):
    super().__init__() 
    



   def visited(self,obj):
       
       if obj.pk in  self.nodeIdMap.keys():
         return True
       else:
         return False
   def nodeId(self,obj):
       nid=None
       if obj.pk  in  self.nodeIdMap.keys():
         nid= self.nodeIdMap[obj.pk] 
       return nid

   def defineId(self,obj):
       nid=None
       if obj.pk in  self.nodeIdMap.keys():
         nid= self.nodeIdMap[obj.pk]
       else:
         self.maxid=self.maxid+1
         nid=self.maxid 
         self.nodeIdMap[obj.pk]=nid
       return nid
        
   
 
    
   def build(self,result):
    super().initialize() 
    collec=None
    is_list_of_lists = isinstance(result, list) and all(isinstance(sublist, list) for sublist in result)
    if is_list_of_lists==True:
      collec = [item for sublist in result for item in sublist]
    else:
      collec=result

    self.g = self.newGraph()
    #print("==>start")
    for inst in flatten_collec(collec):
      cln=type(inst).__name__
      #print("==>",cln)
      if not self.visited(inst):
        nid1=self.add_node(inst)
        ol=inst.object_attributes()
        tl=inst.type_attributes()
        ma=inst.attribute_type_by_name()
          
        m1=dict()
        m1['uri']=inst.pk 
        for t in tl:
            if t!="name":
              v=getattr(inst,"_"+t)
              if v is None:
                v=""
              m1[t]=v  
        #print(m1)
        self.set_node_attributes(self.g,nid1,m1)
          
        #print(ma)
        for att in ol:
          pcln=ma[att]
          inst2L=getattr(inst,"_"+att)


          nid2=None
          if inst2L is not None:
           
           ilst=always_list(inst2L)

           for inst2 in ilst:
              if inst2 is not None:
           
               if not self.visited(inst2):
                 nid2=self.add_node(inst2)
                 #pma=inst.attribute_type_by_name()
                 tl2=inst2.type_attributes()
                 m2=dict()
                 m2['uri']=inst2.pk 
                 for t in tl2:
                  if t!="name":
                    v=getattr(inst2,"_"+t)
                    if v is None:
                      v=""
                    m2[t]=v
                
 
                 self.set_node_attributes(self.g,nid2,m2)  
               else:
                 nid2=self.nodeId(inst2) 
           #print("   ",att," ", pcln,"  ",nid1,"  ",nid2)
           
               self.add_edge(nid1,nid2,weight=10,name=att)





    #TODO
    # to be ported to Graph-tool
   def filter_graph(self,edge_att=None,edge_val=None,node_att=None,node_val=None,op_edge=None,op_node=None):

  
     g=self.g
  
     if op_edge is None:
        op_edge=operator.eq
     if op_node is None:
        op_node=operator.eq      
      
     #op_mapping = {
     #  '<': operator.lt,
     #  '>': operator.gt,
     #  '=': operator.eq,
     #  '!=': operator.ne,
     #}
     
       

     def filter_node_impl(ina,n1):
       r=False 
       if node_att is None:
           r=True
       elif node_val is None:
           r=True
       else:  
         if n1 in ina.keys():
           attd=ina[n1]
        
           if node_att in attd.keys():
             a=attd[node_att]
             #print(a," ",node_val)
             nvl=None
             if isinstance(node_val,list):
               nvl=node_val
             else:  
               nvl=[node_val]
             for val_e in nvl: 
               #print(val_e,"  ",a)
               if op_node(a,val_e)==True  :
                 #print("!") 
                 r=True    
       return r

 

     def filter_edge_impl(gr,n1, n2):
       r=False 
       if edge_att is None:
           r= True
       elif edge_val is None:
           r= True
       else:
         a= gr[n1][n2].get(edge_att)

         evl=None
         if isinstance(edge_val,list):
          evl=edge_val
         else:  
          evl=[edge_val]
         for val_e in evl:
          if op_edge(a,val_e)==True:
            r= True
          else:
            r= False
       return r

     gg = self.newGraph()
     kn={}
     self.init_index()
     ina=self.nodeid2val
     nodesl=ina.keys()
     for nid in ina.keys():
      k=filter_node_impl(ina,nid)
      if k ==True:
         kn[nid]=1
         self.clone_node(gg,nid,ina[nid]) 
    
     for n1,n2,attv in self.g.edges(data=True):
       if n1 in kn.keys() and n2 in kn.keys():
         if filter_edge_impl(self.g,n1, n2)==True:
          gg.add_edge(n1,n2)  
          for k,v in attv.items()   :
            gg.edges[n1, n2][k]=v
 
     return gg
   



class GraphDatasetLayerAbsBKGT(GraphDatasetLayerAbs):
    
   def __init__(self):
     super().__init__()  
     self.initialize()  
            
   def initialize(self):   

     self.g = self.newGraph()
      
       
      
     self.nodeImplByCustomId={}

     self.nodeIdMap=dict()
     self.maxid=0
     self.nodeid2val={}
     self.val2nodeid={}

   def newGraph(self):
      #print("new graph from gt")
      g= gt.Graph(directed=False)
      self.back="GT" 
      self.create_or_get_nprop(g,"custom_id","int")
      self.create_or_get_nprop(g,"pk","string")
      self.create_or_get_nprop(g,"rdf_type","string")
      self.create_or_get_nprop(g,"ctype","string")  
      self.create_or_get_nprop(g,"name","string")    
      
      self.create_or_get_eprop(g,"name","string") 
      self.create_or_get_eprop(g,"weight","double") 
 
      
      return g
   
    ##new
   def node_attributes(self,g,node_id):
     node_attributes = {}
     for prop_name, prop_value in g.vp.items():  # Iterate over all properties
           node_attributes[prop_name] = prop_value[node_id] 
     return node_attributes
       
   
   def write_graphml(self,file):
       
       gt.draw.graph_draw(self.g, output=file, output_format="graphml")
   def create_or_get_nprop(self,g,property_name,tp) :

      has_property = property_name in g.vertex_properties
      if has_property:
         prop = g.vp[property_name]
      else:
         prop = g.new_vertex_property(tp)
         g.vp[property_name]=prop  
   
      return prop
 
   def create_or_get_eprop(self,g,property_name,tp) :

      has_property = property_name in g.edge_properties
      if has_property:
         prop = g.ep[property_name]
      else:
         prop = g.new_edge_property(tp)
         g.ep[property_name]=prop  
   
      return prop
 

   def add_node_impl(self,g,nid,name,pk,rdf_type,ctype):
       
       n = g.add_vertex()
       
       self.g.vp["custom_id"][n]=nid
       self.g.vp["pk"][n]=pk
       self.g.vp["name"][n]=name
       self.g.vp["rdf_type"][n]=rdf_type
       self.g.vp["ctype"][n]=ctype
       self.nodeImplByCustomId[nid]=n
              
    #######    
    
   def write_gexf(self,file):
       gt.gexf.export(self.g, file)
        
   def clone_node(self,g,nid,attdict):
       
      v_clone = g.add_vertex()
 
      vp_custom_id=self.create_or_get_nprop(g,"custom_id","int")
 
      vp_custom_id[v_clone] = nid 
       
      nat=self.node_attributes(nid) 
      for k, v in nat.items(): 
         g.vp[k]=v

      return g
       
     

   def add_node(self,obj):
     nid=self.defineId(obj)
 
     cln=type(obj).__name__
     nm=obj.pk
     if "_displayName" in  obj.__dir__():
        nm=obj._displayName
     if nm is None:
        nm=obj.pk
        
     self.add_node_impl(self.g,nid,name="%s" %(nm),pk=obj.pk,rdf_type=obj.rdf_type, ctype=cln)
       
     return nid


   def selectNodeByAttributeValue(self,att,val):
     
     # Select nodes with 'at1' attribute matching the target value
     vp_at1=self.g.vp[att]
     matching_nodes = [v for v in self.g.vertices() if vp_at1[v] == val]
    
     return matching_nodes


   def indexNodeAttValues(self):
     self.nodeid2val={}
     attnl = {}
     # Select all vertices in the graph
     all_vertices = list(self.g.vertices())  
     attnl=self.g.vertex_properties  
     propid=self.g.vp["custom_id"]  
     for n in all_vertices: 
       nid=propid[n]  
       self.nodeid2val[nid] = {}
       for an in attnl:
         self.nodeid2val[nid][an]=None  
         d=self.g.vp[an]  
         if n in d.keys():
            self.nodeid2val[nid][an]=d[n]
             
         
     return  self.nodeid2val



   def revIndexNodeAttValues(self):
     
     self.val2nodeid={}
     attnl = {}

     # Select all vertices in the graph
     all_vertices = list(self.g.vertices()) 
     attnl=self.g.vertex_properties    
    
     for an in attnl: 
       
       self.val2nodeid[an] = {}

     for an in attnl: 
      atvalues = self.val2nodeid[an]
      for n  in nodesl:
        nid=propid[n]   
        d=self.g.vp[an]     
        if nid in d.keys(): 
          l = d[nid]
          atvalues[l] = atvalues.get(l, [])
          atvalues[l].append(nid)
      self.val2nodeid[an]=atvalues   
     return  self.val2nodeid
      
     
   def init_index(self):
     if len(list(self.nodeid2val.keys()))==0:
      self.indexNodeAttValues()  
 
   def add_edge(self,nid1,nid2,weight,name):
      
       v1=self.nodeImplByCustomId[nid1]
       v2=self.nodeImplByCustomId[nid2]
        #v2=self.selectNodeByAttributeValue("custom_id",nid1) # inefficient way to find nodes of the edges
       e1 = self.g.add_edge(v1, v2)
       self.g.ep["name"][e1]=name
       self.g.ep["weight"][e1]=weight
        
   def set_node_attributes(self,g,nid,mat):
      for k,v in mat.items():
         if k=="uri":
           k="pk"
         prop=self.create_or_get_nprop(g,k,"string")  #TODO improve type
         prop[nid]=v
      

   def k_shortest_paths(self, source, target, k, weight=None):
     #weight: not implemented  
     graph=self.g  
     paths = []
     for _ in range(k):
        dist, pred = gt.shortest_distance(graph, source, pred_map=True)
        if dist[target] == float('inf'):
            break  # No more paths available
        path = [target]
        while target != source:
            target = pred[target]
            path.append(target)
        path.reverse()
        paths.append(path)
        # Mark the used edges to avoid finding the same path again
        for u, v in zip(path[:-1], path[1:]):
            graph.edge(u, v).remove()
     return paths

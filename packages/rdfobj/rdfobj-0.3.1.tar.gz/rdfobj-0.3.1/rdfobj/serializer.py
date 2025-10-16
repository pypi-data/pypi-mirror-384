from rdflib import Namespace, URIRef, Literal
from rdflib.graph import Graph

from .utils import flatten_collec,always_list

class Visitor():
  #abstract
  def __init__(self,userns,gen_utils):  
    self.g=None
    self.visited={}
    self.collect_entity_dict={}
    self.collect_void_uri=[]
    self.ns = Namespace(gen_utils.domain()) 
    self.userns = Namespace(userns) 
    self.rdf_type = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
    self.template=""
      
  def populate(self,collec):
    
    for ent in flatten_collec(collec):
      if ent.pk is not None :
        self.collect_entity_dict[ent.pk]=ent
      else:    
       self.collect_void_uri.append(ent)
 
  def attval(self,ent, attn) :
      attv=None
      try: 
             att_getter=getattr(ent,'get_'+attn)
             attval=att_getter()
             ##print(attval) 
             if attval is not None: 
                ##print("not null") 
               attv=attval
      except:
              print("error")
              pass
      return attv
  def get_connected(self,ent):
      lst=[]
      for attn in ent.object_attributes():
          attval=self.attval(ent, attn)
          if attval is not None: 
             lst.append(attval) 
      return flatten_collec(lst)
          
          
      
  def visit(self,cdi):
    pkl= cdi.keys()
    tovisit=[]  
    for pk in pkl:
       ent=cdi[pk]
       if pk in self.visited.keys():
          pass
       else:
         #self.process(ent)    
         self.visited[pk]=1 
         entchl=self.get_connected(ent) 
         for ench in entchl:  
            tovisit.append(ench)  
            
    #print("tovisit:",tovisit)       
    return tovisit
      
  def traverse(self):
      
    dovisit=True
    tovisit=self.visit(self.collect_entity_dict)
    self.populate(tovisit)  
    while len(tovisit)>0: 
       for ent in flatten_collec(tovisit):
           self.collect_entity_dict[ent.pk]=ent
       tovisit=self.visit(self.collect_entity_dict)
       self.populate(tovisit)

  def lf(self,text):
      ln=len(text)
      if ln==0:
          r=text
      elif ln==1:
          r=text.lower()  
      elif ln>1:
        r=text[0].lower() + text[1:]
      return r
  
  def addEntity2Graph(self,ent):   
      if ent.pk is not None:
        ns=self.ns
        userns=self.userns
        #att_type_dict=ent.attribute_type_by_name() 
        
      
        subj = userns[ent.pk]
        
        cls=ns[ent.__class__.__name__]
        self.g.add((subj, self.rdf_type, cls))
        
        for attn in ent.type_attributes():
           attval=self.attval(ent, attn)  
           if attval is not None:
             attval_lst=always_list(attval)
             for atv in attval_lst:
               obj=Literal(atv)
               pre=ns[self.lf(attn)] 
               self.g.add((subj, pre, obj)) 
               
        for attn in ent.object_attributes():
           attval=self.attval(ent, attn)
           if attval is not None:
             attval_lst=always_list(attval)
             for atv in attval_lst:
               if atv.pk is not None:
                 obj = userns[atv.pk]  
                 pre=ns[self.lf(attn)] 
                 self.g.add((subj, pre, obj))       
 
  def toRDFGraph(self):
      self.g=Graph()
      self.g.parse(data=self.template, format="xml")    
      #for subj, pred, obj in self.g:
      #   print(f"-------Subject: {subj}, Predicate: {pred}, Object: {obj}")
      for pk, ent in self.collect_entity_dict.items():
         self.addEntity2Graph(ent)
      return self.g

    
  def write(self,exfile):
     self.g.serialize(destination=exfile, format='xml')
  def rdf_xml(self):
     rdf_xml_str  = self.g.serialize(format='xml')
     return rdf_xml_str

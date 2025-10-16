
import networkx as nx
 
 
from enum import Enum
from . import utils


INTERNAL_URI_TAG="INTERNAL_URI"
class TARGET_LANG(Enum):

    SPARQL = "SPARQL"
    GRAPH_PATTERN = "GRAPH_PATTERN"
    ENTITY = "ENTITY"

class OPERATOR(Enum):

    EQ = "EQ"
    NE = "NE"
    GT = "GT"
    LT = "LT"
    STARTSWITH = "STARTSWITH"
    ENDSWITH = "ENDSWITH"
    CONTAINS = "CONTAINS"
    SAME_URI = "SAME_URI"
    NOT_SAME_URI = "NOT_SAME_URI"
    IS_URI = "IS_URI" 
    IS_NOT_URI = "IS_NOT_URI"

def validate_operator(op):
    try:
        # Attempt to get the enum member with the value matching op.upper()
        operator = OPERATOR[op.upper()]
    except KeyError:
        # Raise an exception if the value is not found in the enum
        raise ValueError(f"Invalid operator: {op}. Must be one of {[op.value for op in OPERATOR]}")
    return operator.value
 

class QueryBuilder():

  def __init__(self):
    self.elements=dict()
    self.toolBoxes=dict()
    self.defaultToolBox=None
    self.g = nx.Graph() 
    self.op=self.operators()
    self.add_children=True
    self.nid2e=dict()
    self.param_var_masked=dict() # to list all variables
    self.param_var_unmasked=dict()
    self.vmask="__MSK__"

    constdict=utils.constantDict()
    self.type_suffix=constdict['type_suffix']

  def addToolBox(self,tb):
    self.toolBoxes[tb.target_language]=tb
    self.defaultToolBox=tb
  
  def operators(self):
     lst=[]
     for k,v in OPERATOR._member_map_.items():
      lst.append(k)
     return lst
  
  # CHANGE HERE

  def add(self,element_list):
    # Add the possibility of adding several node
    if not isinstance(element_list, list):
      element_list = [element_list]

    for element in element_list:
      if element.label not in self.elements.keys():
        # Creation of nid ("e" + self.elements length)
        nid="n"+str(len( self.elements.keys()))

        # Check if the element has a label. If not, label = nid
        if element.label is None:
            element.label=nid

        # Update the nid of the element
        element.nid=nid

        # Add the node to the graph
        clsinf=""
        for il in element.instL:
          clsinf+=str(il.__class__.__name__)+" " 
         
        self.g.add_node(nid,label=element.label,cls_info=clsinf)

        # Update the self.elements and self.nid2e dictionaries
        self.elements[element.label]=element
        self.nid2e[element.nid]=element
      else:
         raise Exception(f"The label {element.label} is already taken or this element has already been added.")
        
 

  def connected_components_count(self,g):
    
    cct=0
    for c in  nx.connected_components(g):
      cct+=1
     
    return cct
  
  def edge_attributes(self,g,k,ecount):
    if ecount==0:
       return []
    
    al=None
    eattrl=list(list( self.g.edges(data=True))[0][-1].keys())
    if k in  eattrl:
       al = nx.get_edge_attributes(g, k)  
    return al  

  def edge_id(self,s,t):
    eid="%s_%s" %(s,t)
    return eid 
  def mask(self,v):
     return "%s%s%s" %(self.vmask,v,self.vmask)
  
  def simplenames(self,code):
     umdict={}
     umdict_ct={}
     for k in self.param_var_masked.keys():
        uk=k.replace(self.vmask,"")
        skl=uk.split("__")
        sk=skl[0]
        ct=0
        if sk in umdict_ct.keys():
           ct=umdict_ct[sk]
        ct+=1
        umdict_ct[sk]=ct
        if ct>1:
         sk="%s%s" %(sk,ct)

        umdict[sk]=uk
        self.param_var_unmasked[sk]=k
        self.param_var_masked[k]=sk
        
     for sk,uk in  umdict.items():
        #print("%s => %s"  %(uk,sk))
        code= code.replace(self.mask(uk),self.mask(sk))

     return code
  
  def unmask(self,code):
     
     code=self.simplenames(code)
     umsk= code.replace(self.vmask,"")
     return umsk
  
  def edge_vartag(self,a,b):
    vartag= "%s__%s_%s"%(b,"p",a)
    return vartag
  
  def assolVarName(self,assol,aid, k = ""):
    # If element has several association
    
    if len(assol) > 1:
        assol_labl = "asso"
    else:  
        assol_labl = "".join(assol)
    assol_labl = assol_labl + "%s%s" % (aid, k)
    return assol_labl
  
  # CHANGE HERE : new add_edges function
  

  def addEdge(self,nid, referenceLabel,association_list):
           assol = association_list
           assol_labl = self.assolVarName(assol, nid, referenceLabel)
           vartag = self.mask(self.edge_vartag(nid, assol_labl))
           nidE = self.elements.get(referenceLabel).nid
           eid = self.edge_id(nid, nidE)
           ainf=""
           for il in association_list:
             ainf+=str(il)+" " 
           self.g.add_edge(nid, nidE, vartag=vartag, eid=eid, asso=assol_labl, asso_info=ainf)

  def add_edges(self):
     for _, element in self.elements.items():
        nid = element.nid
        for referenceLabel, association_list in element.associationDict.items():
           self.addEdge(nid, referenceLabel,association_list)
 

   
  
  # CHANGE HERE : No more used

  """
  def add_egdes(self):
 
       for label, element in self.elements.items():
           nid=element.nid
           assol=element.association 
           if assol is not None :
               
               assol_labl=self.assolVarName(assol,nid)
               rent=element.referencedEntity 
               vartag= self.mask(self.edge_vartag(nid,assol_labl))
               eid=self.edge_id(nid,rent.nid)
               self.g.add_edge(nid,rent.nid,vartag=vartag,eid=eid)
    """
            

  def defineVarTagMap(self,tb,g):

    

    
    nodes=list(self.g.nodes)
    edges=list(self.g.edges)  
 
    evartag=self.edge_attributes(g,"vartag",len(edges))
  
    vartagMap=dict()
     
    for nid in nodes:
      el=self.nid2e[nid]
      vt=el.vartag
      vartagMap[nid]=vt
      # all nodes var
      tb.selectnodes[nid]=[vt]

      # instance type extraction for futur query
      vtt=self.instype_var_format(vt)
      tb.selected_instance_type[nid]=[vt,vtt]
      
      # 
      self.param_var_masked[vtt]=1
      self.param_var_masked[vt]=1

    for ed in edges:
      if evartag is not None:
        nid1=ed[0] 
        nid2=ed[1] 

        vtn1_s=vartagMap[nid1]
        vtn2_o=vartagMap[nid2]
        
        eid=self.edge_id(nid1,nid2)
        vt_p=evartag[ed]
        vartagMap[eid]=vt_p

        tb.selectpath_edge[eid]=[vtn1_s,vt_p,vtn2_o]
        self.param_var_masked[vt_p]=1
 

    return vartagMap
  
  def instype_var_format(self,refvar):
      ts=self.type_suffix
      tvar= "%s%s" %(refvar,ts)
      return tvar

  def defineVarTag(self):
    
    ct=0
    vct=0

    for label, element in self.elements.items():
         if ct % 2==0:
           vct+=1
           cti=0
         cti+=1  
         ct+=1
         if isinstance(element,EntityNode):
           vartag=None
           if cti==1:
              vartag=self.mask('s__'+str(vct))
           elif cti==2:
              vartag=self.mask('o__'+str(vct))
              
           element.vartag=vartag
           
   

           for referenceLabel, association_list in element.associationDict.items():

            if association_list is not None:
              assol_labl=self.assolVarName(association_list,element.nid, referenceLabel)
            
              vartag=self.mask(assol_labl)
              element.associationVarTag[assol_labl]=vartag
           

           act=0 
           for attn, param in element.filterTypeAttributes.items():
                act+=1
                pvar=self.mask(attn+'__'+str(element.nid)+str(act))
                param['refvar']=pvar

                self.param_var_masked[pvar]=1
                element.filterTypeAttributesVar[attn]=pvar
         else:
           element.vartag=element.nid 
          


  def sparql_generate(self):
    # Get the value of TARGET_LANG enum for SPARQL.
    k=TARGET_LANG.SPARQL.value

    # Check if the toolBox of SPARQL is here.
    if k in self.toolBoxes.keys():
       tb=self.toolBoxes[k]

       query=""

       # Compteurs
       ct=0
       vct=0

       # Filters
       filters=[]
       a_filters=[]

       # Triples
       t_triples=[]
       
       # Template
       template=None
       
       # Define the VarTag of each elements and of their association(s)
       self.defineVarTag()

       # Add the edges to the graph
      #  self.add_egdes()
       self.add_edges() # CHANGE HERE

      #test connectivity ---start ------------------------
       # Get the number of nodes in the graph
       nn=self.g.number_of_nodes()

       # Get the number of elements connected in the graph
       cct=self.connected_components_count(self.g)
       if nn==0 or cct==0:
         #print(self.g)
         raise Exception("no element found. please add at least one EntityNode in QueryBuilder")
       elif cct>1:
         print(cct)
         raise Exception("elements not connected. use 'connectedWith' method from EntityNode class") 
      #test connectivity ---end ------------------------- 
       

       vn=self.defineVarTagMap(tb,self.g)
       
       #print(vn) 

       #print(q1)
       sbc=[]

     
       template=tb.root_query_template()
       
        #print(query)
       ##########TODO: debug this : order x,y ....
       for label, element in self.elements.items():
         # Pass this condition 1 out of 2 times
         if ct % 2==0:
           # vct is incremented and cti is set to 0.
           vct += 1
           cti = 0
         
         # cti and ct are incremented
         cti += 1  
         ct += 1
         #print(label," -> ",element)

         # Check if the element validate the constraints.
         if element.validateConstraint()==False:
            raise Exception("%s %s (%s) constraints not validated"  %(element.vartag,element.label,element.__class__)) 
         
         # Check if element is an EntityNode
         if isinstance(element,EntityNode):
           #print(str(cti),"-->element.targetClass",element.targetClass)
           
           #cti 1 or 2==> alternatively S / O ????
           if cti==1:
              #print("cti=1")
              sfg=tb.select_byclass(element.targetClass,element.vartag, self.add_children)
              sbc.append(sfg)
              #print(sfg) 
           elif cti==2:
              #print("cti=2")

              filt=tb.select_byclass(element.targetClass,element.vartag, self.add_children)
               
              #print(filt)
              a_filters.append(filt)
           
           vartag=None
           
        
          
           for key, value in element.associationDict.items():
              # print(value)
              assol = value
           
           
              if assol is not None:
                assol_labl=self.assolVarName(assol,element.nid, key)
                vartag=element.associationVarTag[assol_labl]
                filt=tb.filter_clause(vartag,assol)
                filters.append(filt)
            
          
         for attn,param in element.filterTypeAttributes.items():
         
            pvar=param['refvar']
            vartag=element.vartag

            if param["operator"] == OPERATOR.SAME_URI or   param["operator"] == OPERATOR.NOT_SAME_URI:
               param["left_vartag"] = vartag

            elif param["operator"] == OPERATOR.IS_URI or   param["operator"] == OPERATOR.IS_NOT_URI: # 03 2024 add filter by uri string 
               param["left_vartag"] = vartag

            else:
              tpl=tb.add_triple_palias(vartag,param['name'],pvar)
              t_triples.append(tpl)
               
              #print(tpl)
        
            
            filt=tb.filter_clause_param([param],"AND")
            filters.append(filt)

         flcl=self.addFilterNode(tb,element)   
         for flc in flcl:
           #print("-flc-")
           #print(flc)
           filters.append(flc)

       #print(template)       
       #print(a_filters)
       #print(filters)
       q=tb.build( template,a_filters=a_filters,filters=filters,t_triples=t_triples,sbc=sbc)
       q=self.unmask(q)
       q=self.cleanq(q)
       return q
    else:
      return k+"toolbox not available"

  def cleanq(self,iq):
     ql=iq.split('\n')    
     rl=[]
     for l in ql:
        ll=l.strip()
        if len(ll)>0 and  ll.startswith('#') ==False:
          rl.append(ll)
     rs= "\n".join(rl)
     return rs


  def variable_metadata(self):
    #print("variable_metadata--+")
    vartag2label={}
    vartag2Cls={}
    mld={}
    mask=self.param_var_masked
    for k,element in self.elements.items():
      vartag=mask[element.vartag]
      #print("---- %s=%s"  %(k,  mv ) )
      
      #label2vartag[k]=mv
      vartag2label[vartag]=k
      tc=element.targetClass
      vartag2Cls[vartag]=tc
      #print(tc)
      m={}
      m['index']=None 
      m['vartag']=vartag 
      m['class']=tc
      label=None
      if vartag in  vartag2label.keys():
         label=vartag2label[vartag]    
      m['label']=label 
      mld[vartag]=m
    
    idxm=self.defaultToolBox.selectpath_indexes()
    ml=[]
    for k,idx in idxm.items():
        m={} 
        vartag=mask[k] 
        #print(" - %s=%s"  %(idx,  vartag) )
        cls=None
        label=None
        if vartag in  vartag2Cls.keys():
          cls= vartag2Cls[vartag]
          label=vartag2label[vartag]     
        m['index']=idx 
        m['vartag']=vartag 
        m['class']=cls
        m['label']=label 
        
        mld[vartag]=m
    i=-1   
    last_cls=None
    last_cls_ix=None
    mldk=list(mld.keys())
    for vartag in mldk:
      m=mld[vartag]
      i+=1
      idx=m['index']
      cls=m['class']
      s=None
      t=None
      if last_cls is not None and cls is None:
        #association detected   
        m['source']=last_cls_ix
        m['target']=idx+1
      else:
        m['source']=None
        m['target']=None
        
      last_cls=cls  
      last_cls_ix=idx
      mld[vartag]=m
    #print(ml)
    #print("variable_metadata----")
    ml=list(mld.values()) 
    return ml





  def addFilterNode(self,tb,element):
    #print(">>addFilterNode")
    ql=[]
    #mappvar={}
    for fnode in element.filternodes:
       
       paramL=[]
       ix=0
       xop=fnode.indexOperator[ix]
       # at this step do not mix operators
       for an in fnode.attnList:
         
         n=fnode.attnList[ix]   
         v=fnode.attvList[ix]
         o=fnode.opList[ix] 
         param=element.defineParam(n,v,o)

         #fixed : pvar is centralized using  filterTypeAttributesVar
    
         pvar=None
         for uattn,uparam in element.filterTypeAttributes.items():
            upvar=element.filterTypeAttributesVar[uattn]
            if uparam['name']==n:
              #print(uattn)
              #print(uparam)
              #print(upvar)
              pvar=upvar
            else:
               pvar = "--undef--"

          
         param['refvar']=pvar
         self.param_var_masked[pvar]=1
         paramL.append(param)
         ix+=1 

       q=""
       #q+=">>>"
       #print(">paramL")
       #print(paramL)
       q+=tb.filter_clause_param(paramL,xop)
       #q+="<<<<"
       ql.append(q)
    return ql
     
  def graph_generate(self):
    return "not yet implemented"
  
  def entity_generate(self):
    return "not yet implemented"
  

class GNodeAbstract():
   def __init__(self):
     self.debug=False
     self.label=None
     self.nid=None
     self.vartag=None

   def validateConstraint(self):    
     #TODO : helper - check the validity of the asso and att filter constraints
     return True

###########################################
class FilterNode():
  def __init__(self):
       
       self.attnList=[]
       self.attvList=[]
       self.opList=[]
       self.indexOperator=dict() 

class FilterOr(FilterNode):
  def __init__(self):
       super().__init__() 
 

  def whereAttribute(self,attn,attv,op):
       op=validate_operator(op)
       self.attnList.append(attn)
       self.attvList.append(attv)
       self.opList.append(op)
       ix=len(self.attnList)-1
       self.indexOperator[ix]="OR"
       return None 


class FilterAnd(FilterNode):
    def __init__(self):
       super().__init__() 

    def whereAttribute(self,attn,attv,op):
       op=validate_operator(op)
       self.attnList.append(attn)
       self.attvList.append(attv)
       self.opList.append(op)
       ix=len(self.attnList)-1
       self.indexOperator[ix]="AND"
       return None      
  
###########################################

class EntityNode(GNodeAbstract):
    
   def __init__(self,label,clsIL):
    super().__init__()
    self.isOperator=False
    self.label = label
    clsInstL=[]

    if isinstance(clsIL,list) ==True:
       clsInstL=clsIL
    else:
       clsInstL.append(clsIL)

    self.instL=clsInstL


    self.targetClass =[]
    for inst in self.instL:
      self.targetClass.append(inst.__class__.__name__)

 
    self.associationDict = {} # {key = elementReference.id --> value = associationList}

 
    self.filterTypeAttributes={}
    self.filterTypeAttributesVar={}
    self.associationVarTag={}
    self.filternodes=[]

   def defineParam(self,attn,value, operator ):
       param=dict()
       if operator is None:
         operator=OPERATOR.EQ.value
       param['refvar']=None  
       param['name']=attn
       param['value']=value
       param['operator']=operator
       return param
   
   def where(self,fnode:FilterNode):
      self.filternodes.append(fnode)
      return None
   
   
   def whereAttribute(self,attn,value, op=None):
       # Definit la filter clause
       op=validate_operator(op)
       param=self.defineParam(attn,value, op)
       tatall=[] 
       for inst in self.instL: 
           tat=inst.type_attributes()
           tatall.extend(tat)
       if attn not in tatall:
           raise Exception("no primitive type  attribute '%s' in classes %s. Options are %s " %(attn,self.targetClass,tatall)) 
       self.filterTypeAttributes[attn]=param 

   
   def equal(self, otherNode):
      param=self.defineParam(otherNode, None, OPERATOR.SAME_URI)
      self.filterTypeAttributes[otherNode.label]=param

       
   def not_equal(self, otherNode):
       param=self.defineParam(otherNode, None, OPERATOR.NOT_SAME_URI)
       self.filterTypeAttributes[otherNode.label]=param 

   #03 2024 : added filter by uri value for pattern
   def has_uri(self, uristr):
      
      attn=INTERNAL_URI_TAG
      param=self.defineParam(attn,uristr,  OPERATOR.IS_URI)  
      self.filterTypeAttributes[attn]=param 

   def has_not_uri(self, uristr):
      attn=INTERNAL_URI_TAG
      param=self.defineParam(attn,uristr,  OPERATOR.IS_NOT_URI)  
      self.filterTypeAttributes[attn]=param 


  ################
   def connectedWith(self,referencedEntity,association,reverse=False):
    # Check if association is a list or not
    if isinstance(association,list):
      assol=association
    else:
      assol=[association]

     
    # Check if the key already exists in associationDict

    if self.associationDict.get(referencedEntity.label) :
      self.associationDict[referencedEntity.label].extend(assol)
      # Unicity of the elements in the array.
      self.associationDict[referencedEntity.label] = list(set(self.associationDict.get(referencedEntity.label)))
    else:
      self.associationDict[referencedEntity.label] = list(set(assol))

 
    ################ --- 31 may 2023
    #oatall=[] 
    #for inst in self.instL: 
    #     oat=inst.object_attributes()
    #     oatall.extend(oat)
    ################
    oatall=[] 
    ###############FM+########        
    if reverse==False:
     for inst in self.instL: 
         oat=inst.object_attributes() ## standard way here (left to right navigation)
         oatall.extend(oat)
    else:    
      for inst in referencedEntity.instL: 
         oat=inst.object_attributes() ## reverse way here (right to left navigation)
         oatall.extend(oat)
    ###############FM-########        
        
        
        
    for associa in assol:
      if associa not in oatall:
          raise Exception("no object  attribute '%s' in classes  %s . Options are %s " %(associa,self.targetClass,oatall)) 
            

 
  

  ##########
 

   def validateConstraint(self):    
     vc = super().validateConstraint()
     if vc ==False:
       return False
     else:
       #impl here
       return True

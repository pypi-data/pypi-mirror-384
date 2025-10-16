
from .query import OPERATOR
from . import utils

def vn(v):
   return "?%s" %(v)

class Toolbox():
    
    def __init__(self ,alias,uri,module):
      self.target_language="SPARQL"
      self.gen_utils=module
      self.alias= alias
      self.uri= uri
      self.use_subclassof=False
      self.use_instance_type=True
       
      
      self.selectnodes={}
      self.selectpath_edge={}
      self.selected_instance_type={}
      constdict=utils.constantDict()
      self.common_prefixes=constdict['common_prefixes']
      self.type_predicate=constdict['type_predicate']

      

 

      #sparql primitive to build queries
    def prefixes(self,aliases) :
       d={}
       for p in aliases:
         if p in  self.common_prefixes.keys():
           d[p]=self.common_prefixes[p]
       return d
    
    def filter_template(self):
        query_t="FILTER ( %s )"
        return query_t

    
    def spaWhere(self):       
       # merge tripe info related to instances, associations and types
       sepa=self.selectpath_edge
       spm={}
       for k, triple in sepa.items():
          vl=[]
          for v in triple:
              
             vl.append(vn(v))

          spm[k]=vl

       sit=self.selected_instance_type
       p=self.type_predicate
       for k, v in sit.items():
          
          triple=[vn(v[0]),p,vn(v[1])]
          spm[k+p]=triple

       return spm
    
    
    def spaSelect(self):   
       # merge tripe info related to instances, associations and types
       addk={}
       spm={}
       snl=self.selectnodes
       #print("*******")
       #print(snl)
       #print("*******")
       
       for k, triple in snl.items():
          vl=[]
          for v in triple:
             if v not in addk.keys():
                vl.append(vn(v))
                addk[v]=1
          spm[k]=vl


       sepa=self.selectpath_edge
        
       for k, triple in sepa.items():
          vl=[]
          for v in triple:
             if v not in addk.keys():
                vl.append(vn(v))
                addk[v]=1
          spm[k]=vl

       sit=self.selected_instance_type
       p=self.type_predicate
       for k, v in sit.items():
          spm[k+p]=[vn(v[1])]

       #for k,v in spm.items():
       #   print(k,"-->",v)   
       return spm


    def wherepath_frag(self):
       selectpath=""
       i=0
       spa=self.spaWhere()
       for k, triple in spa.items():
          i+=1
          ct=0
          if i>1 :
            selectpath+=".\n    "
          for v in triple:
             selectpath+="%s " %(v)
       return selectpath

    def selectpath_frag(self):
       selectpath=""
       i=0
       spa=self.spaSelect()
       for k, triple in spa.items():
          i+=1
          #ct=0
          for v in triple:
            #ct+=1
            selectpath+="%s " %(v)
            

       return selectpath


    #usefull for variable_metadata 
    def selectpath_indexes(self):
       idxm=dict()
       i=-1
       spa=self.selectpath_edge
       for k, triple in spa.items():
          i+=1
          ct=-1
          for v in triple:
            ct+=1
            idxm[v]=i+ct
       return idxm  
    
    
    def root_query_template(self,addprefix={}):
        alias=self.alias
        duri=self.uri

        if self.use_subclassof==True:
           als=self.prefixes(['rdf','rdfs'])
           for k,v in als.items():
              addprefix[k]=v
        elif self.use_instance_type==True:
              als=self.prefixes(['rdf'])
              for k,v in als.items():
                addprefix[k]=v

        qp=""
        for prefix,uri in addprefix.items():
           qp+="\n    prefix %s: <%s>" %(prefix,uri) 


        selectpath=self.selectpath_frag()
        wherepath=self.wherepath_frag()
        query_t0="""
    %s    
    prefix %s: <%s>
    select %s
    where {
    %s.
    #Q1 
    %s
    #Q2
    %s
    #Q3
    %s
    }
        """
        query_t=query_t0 %(
                            qp,alias,duri,
                            selectpath,
                            wherepath,
                            "%s","%s","%s"
                            )
        
        return query_t
        
    def a_clause_union(self,va,classnames):

    
        q1=""
        ct=0

        for cln in classnames:
            ct+=1
            if ct==1:
            
                sep=""
            else:
                sep=" UNION "
            q1+="%s { ?%s a %s:%s } " %(sep, va ,self.alias,cln)
            
        return q1


    def select_byclass(self,clnlist,va="s1",add_children=False):
        subc_frag=""
        if self.use_subclassof==True:
          add_children=False
          subc_frag= self.subclassof( clnlist,va)
        
        frag = self.union_classes( clnlist,va,add_children ) 
        frag = frag + subc_frag
        return frag
 
 
    
    def union_classes(self,clnlist,va,add_children  ):        
        
        clsl=[]
        for cln in clnlist:
           clsl.append(cln)

        if add_children==True:
          for cln in clnlist:
            children=self.gen_utils.class_children(cln)
            clsl.extend(children)
        

        q1=self.a_clause_union(va,clsl)  
        
        return q1

    def subclassof(self,clnlist,va):
        q="\n"
        ct=0
        for cln in clnlist:
          ct+=1
          if ct>1:
             q+=" UNION "
          #q1="""{ ?%s rdf:type ?type%s. ?type%s rdfs:subClassOf  %s:%s }""" %( va ,va,va,self.alias,cln)   
          q1="{ ?%s rdf:type/rdfs:subClassOf* %s:%s }" %( va ,self.alias,cln) 
          q+=q1
 
        return q
    
    
    def filter_clause_param(self, paramL,opcl="AND"):
        
        #print("filter_clause_param")
        #print(paramL)
        #print(opcl)

        F1="FILTER ("
        PEND=" )"
        F2=PEND
        AND_STR=" && "
        OR_STR=" || "

        if opcl=="AND":
           OP_STR=AND_STR
        elif opcl=="OR":
           OP_STR=OR_STR

        cond=""
        i=0
      
        for param in paramL:
          if i>0  :
             cond+=OP_STR
          fc=self.filter_clause_param_impl( param) 
          #print("=%s=" %fc)
          cond+=fc
          i+=1   

        q="%s %s %s" %(F1,cond,F2) 
        return q

    def filter_clause_param_impl(self, param):
        #print(param)
        
        s=param["refvar"]

        op="="
        if param['operator']==OPERATOR.EQ.value:
          op="="
        elif param['operator']==OPERATOR.NE.value:
          op="!="
        elif param['operator']==OPERATOR.GT.value:
          op=">"
        elif param['operator']==OPERATOR.LT.value:
          op="<"

        val=param['value']

        if param["operator"] == OPERATOR.SAME_URI or   param["operator"] == OPERATOR.NOT_SAME_URI: # for joining # 2023
           val = param['name'].vartag
           s = param["left_vartag"]

        elif param["operator"] == OPERATOR.IS_URI or   param["operator"] == OPERATOR.IS_NOT_URI: #03 2024  filter on uri string / spacial case of where attribute by pk
            
           s = param["left_vartag"]   

        attn=param['name']
        
        
        if param['operator']==OPERATOR.STARTSWITH.value:
          cond="STRSTARTS(STR(?%s),'%s')" %(s,val)
        elif param['operator']==OPERATOR.ENDSWITH.value:
          cond="STRENDS(STR(?%s),'%s')" %(s,val)
        elif param['operator']==OPERATOR.CONTAINS.value:
          cond="CONTAINS(?%s,'%s')" %(s,val)


        elif param['operator'] == OPERATOR.SAME_URI:
          cond = "?%s = ?%s" %(s,val )
        elif param['operator'] == OPERATOR.NOT_SAME_URI:
          cond = "?%s != ?%s" %(s,val )  

        elif param['operator'] == OPERATOR.IS_URI:
          cond = """str(?%s) = "%s" """ %(s,val )
        elif param['operator'] == OPERATOR.IS_NOT_URI:
          cond = """str(?%s) != "%s" """ %(s,val )  


        else:
          opval=""" %s  '%s' """ %(op,val)
          cond="?%s %s" %( s,opval ) 
          
        #print("================>%s<=======" %cond)
        return cond
    
    def add_triple_palias(self,s,p,o):
       pa="%s:%s"%(self.alias,p)
       return self.add_triple("?"+s,pa,"?"+o)
    
    def add_triple(self,s,p,o):
       q="%s %s %s" %(s,p,o)
       return q
    
    def filter_clause(self,vartag,cln):
       pvart="?"+ vartag 
       return self.filter_clause_impl(pvart,cln)
    
    def filter_clause_impl(self,p,cln):
        cl=list()
        if isinstance(cln, list):
          for c in cln:
            cl.append(c)
        else:
          cl.append(cln)

        q=""  
        ct=0
        for c in cl:
            ct+=1
            if ct==1:
                sep=""
            else:
                sep=" || "
            q+= "%s %s =  %s:%s " %(sep,p,self.alias,c)
            
        q= self.filter_template() %(q)
        return q

    def build(self,template,a_filters=list(),filters=list(),t_triples=list(),sbc=[]):
        q1=""
        if len(sbc)>0:
           for sb in sbc:
              q1+=sb

        template=template %("%s",q1,"%s")

        aq=self.clause_frag(a_filters,parenthesis=False, addsep=True)
        tq=self.clause_frag(t_triples,parenthesis=True, addsep=True)
        fq=self.clause_frag(filters,parenthesis=False, addsep=False)

        # print("-------********+********-------")
        # print("--------q1")
        # print(q1)
        # print("--------")
        # print("!!!!!!!!!!template")
        # print("--------")
        # print(template)
        # print("--------aq")
        # print(aq)
        # print("--------tq")
        # print(tq)
        # print("--------fq")
        # print(fq)    
        # print("--------------")
        # print("-------*********-*******-------")
        
        aq="#aq\n"+aq+"#tq\n\n"+tq+"\n"  

        query=template %(aq,fq)
        return query
    

    def add_filt_frag(self,fi,parenthesis):
       #print("----add_filt_frag-----------"+str(fi)+" "+str(parenthesis))
       if parenthesis==True:
         fg="{ %s }" %(fi) 
       else:
         fg=" %s " %(fi) 
       return fg
    
    def clause_frag(self,afilters,parenthesis=False, addsep=True):

        fq=""
        ac=0
        EP="."
        SP=EP+"\n"
        
        
        if afilters is not None:
           for fi in afilters:
            ac+=1
            if ac==1:
              fq+=self.add_filt_frag(fi,parenthesis)
            else:
              if fi.strip().endswith(EP)==False: 
                if addsep==True:
                  sep=SP
                else:
                  sep=""   
              else:
                sep=""
              if fq.strip().endswith(EP)==True:  
                  sep=""  
              fq+=sep+self.add_filt_frag(fi,parenthesis)
             
            if fq.strip().endswith(EP)==False:   
              fq=fq+SP 
        return fq
     
  
import networkx as nx
from regraph import NXGraph, Rule, plot_rule

class GraphTransformer():
    
   def __init__(self):
    self.a = 1
 
   def ruleEngineGraph(self,final_view):
    
     if isinstance(final_view, nx.DiGraph):
       gg=final_view    
     else:  
       gg=nx.DiGraph(final_view)
     nxg= NXGraph(incoming_graph_data=gg)
     return nxg


   def tagRuleOutput(self,rhs,tagged_nodes,tagged_edges):
  #tagged nodes will be added
    
    for tg in tagged_nodes:
      attrs=rhs.get_node(tg)   
      #print("--<",tg,attrs) 
      attrs['tag']=1
      rhs.update_node_attrs(tg,attrs)
      #attrs=rhs.get_node(tg)   
      #print("-->",tg,attrs)
    
    #taged nodes will be added
        
    for tg in tagged_edges:
      attrs=rhs.get_edge(tg[0],tg[1])   
      #print("--<",tg,attrs) 
      attrs['tag']=1
      rhs.update_edge_attrs(tg[0],tg[1],attrs)
      #attrs=rhs.get_node(tg)   
      #print("-->",tg,attrs)
        
   def addRuleOutput(self,rhs,rw_g):
        for nid in rhs.nodes():
          
          if nid not in rw_g.nodes():
            attrs=rhs.get_node(nid)   
            if 'tag' in attrs and attrs['tag']=={1}  :
                print("   add node---- %s" %(nid) )  
                rw_g.add_node(nid,attrs)
        for eid in rhs.edges():        
          if eid not in rw_g.edges(): 
            attrs=rhs.get_edge(eid[0],eid[1])   
            if 'tag' in attrs and attrs['tag']=={1}  :
                print("   add edge---- %s->%s" %(eid[0],eid[1]) ) 
                rw_g.add_edge(eid[0],eid[1],attrs)     
        return rw_g       
   



class RuleGenerator():
    
    def __init__(self,lhs,nodeids):
        #print("==>new RuleGenerator")
        self.lhs=lhs
        self.nodeids=nodeids
        self.rule=Rule.from_transform(lhs)
        #self.idm=dict()
        self.ctn=0
        self.gtr=GraphTransformer()
        
    def nodeIds(self):
        return self.nodeids
    
    
    def defineNodeId(self,lb):
        self.ctn+=1
        lb="%s%s"%(lb,self.ctn)
        return lb
        
    def clone_node(self,node):
        p_clone, clone1 = self.rule.inject_clone_node(node)
        return [ p_clone, clone1]
    
    def add_node(self,label="n"):
     nnid=self.defineNodeId(label)
     self.rule.inject_add_node(nnid)
     return nnid
    
    def add_edge(self,n1id,n2id):
      self.rule.inject_add_edge(n1id,n2id)

    def merge_node(self,x,y):
       merge_node = self.rule.inject_merge_nodes([x,y])
       return merge_node
    

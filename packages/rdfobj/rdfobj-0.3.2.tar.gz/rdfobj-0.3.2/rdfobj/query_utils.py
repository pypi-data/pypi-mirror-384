import functools
import operator
  

def uniqueEntities(inlist):
    
    m=entitiesDict(inlist)
    unique = list(m.values())
    return unique

def entitiesDict(inlist: list):
    m={}
    for element in inlist:
      if (is_listoflist(inlist)):
          s = str()
          for ent in element:
            s += str(ent.pk)
          m[s] = s
      else:
        m[element.pk]=element
    return m

def flatten_list(ll):
    ol = [item for sublist in ll for item in sublist]
    
    return ol

def is_listoflist(obj):
  r=False  
  if isinstance(obj,list) :             
     if any(isinstance(i, list) for i in obj):
         r=True
  return r


def filter_entity(entities,seq):
    
  def func(x):
    if x.__class__ in entities:
        return True
    else:
        return False
  
  sq = filter(func, seq)
  return sq




def filter_attributes_or(attribute,values,seq):
    
  def func(x):
    
    attn='_'+attribute
    if attn in x.__dict__:
       v=x.__dict__[attn] 
       if v in values:
            return True
        
    return False
  
  sq = filter(func, seq)
  return sq


def filter_attribute(attribute,value,seq):
    
  sq = filter(lambda x: operator.eq(x.__dict__['_'+attribute], value), seq)

  return sq



def reduce(objSeq,attributeName, start="",sep=None,prefix="_"):
  # Process the list using functools.reduce
  attn=prefix+attributeName
  if sep is not None:  
    result = functools.reduce(lambda x, obj: x + getattr(obj, attn)+sep, objSeq, start)
  else:
    result = functools.reduce(lambda x, obj: x + getattr(obj, attn) , objSeq, start)
  return result

def attributeList(objSeq,attributeName,prefix="_"):
  #from a list of objects, obtain a list of 'attribute' values by attribute names
  attn=prefix+attributeName
  get_att = lambda obj: obj.__dict__[attn]
  attvals = list(map(get_att , objSeq))
  return attvals




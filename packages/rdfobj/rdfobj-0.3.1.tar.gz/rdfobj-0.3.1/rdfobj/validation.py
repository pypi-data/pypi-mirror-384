 
from urllib.parse import urlparse
import copy
from . import  mapper as ma
 
class Validator():
        
    """
    This class facilitate the entities validation process.

    """
 

    
    def __init__(self,cfg, modules=[]):
        self.cfg = cfg
        self.modules=modules


    def  getattr(self,entity, attribute, default=None):
         attn=attribute
         ret=   getattr(entity, attn, default)
         if ret is None:
             attn="_%s"%(attribute)
             ret=  getattr(entity, attn, default)
         return ret
        
    def define_class(self,clname):
       cls=None
       for module in self.modules:
          try:
            en=ma.define_instance_from_name(module,clname)
            cls=en.__class__
            break
          except:
             pass
          
       return cls
    
    def val_hierarchy(self,entity):
      hier=[]
      for clsn in self.cfg.keys():
          cls= self.define_class(clsn)
          if isinstance(entity,cls):
             hier.append(cls.__name__)
      return hier

    

    def validate(self, ent_collection, limit=None):

     
    
        ct=0 
        err_d={}
        errors = []
        for entity in ent_collection:
            ct=ct+1
            errors_e=[]
            cls=entity.__class__
            entity_class = cls.__name__
            ##only for leaf class
            if entity_class in self.cfg.keys():
              constraints = self.cfg[entity_class]
              for attribute, constraint_list in constraints.items():
                if attribute=="class_name":
                     for constraint in constraint_list: 
                       c=self.define_class(constraint)  
                       if  entity_class!=constraint:
                          emsg="entity class name %s is not equal to %s ." %(entity_class,constraint)
                          errors.append(emsg)
                          errors_e.append(emsg)  
            # for all hierarchy
            hier=self.val_hierarchy(entity)
            for hicl in hier :
              if hicl in    self.cfg.keys():
                constraints = self.cfg[hicl]
                for attribute, constraint_list in constraints.items():
                  if attribute=="class":
                     for constraint in constraint_list: 
                       c=self.define_class(constraint)  
                       if  isinstance(entity,c)==False:
                          emsg="entity class %s not compatible with %s." %(entity_class,constraint)
                          errors.append(emsg)
                          errors_e.append(emsg)
                                           
                      

                  else:  
                      
                    attribute_value = self.getattr(entity, attribute, None)
                    #print(entity)
                    #print(attribute)
                    #print(attribute_value)
                    for constraint in constraint_list:
                        if constraint == 'notNull':
                            if attribute_value is None or attribute_value=="":
                                emsg=f"{entity_class}.{attribute} cannot be null."
                                errors.append(emsg)
                                errors_e.append(emsg)
                        elif constraint == 'unique':
                            [ret,msg ]=self._check_unique(entity,entity_class, attribute, attribute_value, ent_collection)
                            if ret==False:
                                emsg=f"{entity_class}.{attribute} must be unique."
                                emsg_add=f"({msg})."
                                errors.append(emsg+emsg_add)
                                errors_e.append(emsg)
                        elif constraint == 'int':
                            if not isinstance(attribute_value, int):
                                emsg=f"{entity_class}.{attribute} must an integer."
                                errors.append(emsg)
                                errors_e.append(emsg)
                        elif constraint == 'float':
                            if not isinstance(attribute_value, float):
                                emsg=f"{entity_class}.{attribute} must be a float."
                                errors.append(emsg)
                                errors_e.append(emsg)
                        elif constraint == 'string':
                            if not isinstance(attribute_value, str):
                                emsg=f"{entity_class}.{attribute} must be a string."
                                errors.append(emsg)
                                errors_e.append(emsg)
                        elif constraint == 'uri':
                            if self.uri_validator(attribute_value)==False:
                                emsg=f"{entity_class}.{attribute} is not a valid URI ({attribute_value})." 
                                errors.append(emsg)
                                errors_e.append(emsg)
                        elif constraint == 'url':
                            if self.uri_validator(attribute_value)==False:
                                emsg=f"{entity_class}.{attribute} is not a valid URL({attribute_value})." 
                                errors.append(emsg)
                                errors_e.append(emsg)                                
                                
                        elif isinstance(constraint, type):
                            if not isinstance(attribute_value, constraint):
                                emsg=f"{entity_class}.{attribute} must be of type {constraint}."
                                errors.append(emsg)
                                errors_e.append(emsg)
                        else:
                            custom_validation_function = self.getattr(self, constraint, None)
                            if custom_validation_function is not None:
                              [ret,msg ]= custom_validation_function(entity)             
                              if ret==False:
                                 emsg=msg
                                 emsg_add=""
                                 errors.append(emsg+emsg_add)
                                 errors_e.append(emsg)

                                
            if limit is not None and ct >= limit:
                break
                
            err_d[entity.pk]=errors_e
            serr_d=copy.deepcopy(err_d)   
            for  k,v in  err_d.items():
               if len(v)==0:
                  serr_d.pop(k, None) 
                                    
        return [errors,serr_d]


    def uri_validator(self,x):
       try:
         result = urlparse(x)
         if result is not None:
            if result.scheme is None or result.scheme =="":
                #print("---->",result.scheme)
                return False
        
         return True        
       except:
          return False
           
    def url_validator(self,x):
       try:
         result = urlparse(x)
         if result is not None:
            if result.scheme is None or result.scheme =="":
                #print("---->",result.scheme)
                return False
            elif result.scheme != "http" and result.scheme != "https" :
                return False
    
         return True        
       except:
          return False           
          
    def _check_unique(self,entity1, entity1_class, attribute, attribute_value, ent_collection):
        msg=None
        for entity2 in ent_collection:
            if entity2.__class__.__name__ != entity1_class:
                continue
            
            attv=self.getattr(entity2, attribute,None)
             
            if attv == attribute_value and entity1 is not entity2:
                msg=entity1.pk  
                return [False,msg]
                 
        msg=entity1.pk        
        return [True,msg]
    

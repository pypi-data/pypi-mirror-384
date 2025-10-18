from ..feature import KitFeature



class NextjsModelField:
    
    pass

class NextjsModelData:
    
    pass

class Feature(KitFeature):
    
    feature_type = 'nextjs_create_hooks'
    def __init__(self, model_name, model_fields):
        self.params = {'model_name':model_name, 'model_fields':model_fields}
    
    def execute(self):
        pass
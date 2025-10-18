from ..feature import KitFeature



class HookData:
    
    pass

class Feature(KitFeature):
    
    feature_type = 'nextjs_use_hooks'
    def __init__(self, model_name):
        self.params = {'model_name':model_name}
    
    def namespace(self):
        pass
    
    def execute(self):
        pass
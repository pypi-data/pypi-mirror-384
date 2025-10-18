from ..feature import KitFeature



class HookData:
    
    pass

class Feature(KitFeature):
    
    feature_type = 'nextjs_use_hooks'
    def __init__(self):
        self.params = {}
    
    def namespace(self):
        pass
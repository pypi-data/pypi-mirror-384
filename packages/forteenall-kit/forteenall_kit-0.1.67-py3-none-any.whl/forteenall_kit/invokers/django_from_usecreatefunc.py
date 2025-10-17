from ..feature import KitFeature



class HookParser:
    
    pass

class FieldSerializer:
    
    pass

class UrlGenerator:
    
    pass

class UseCreateFuncReader:
    
    pass

class Feature(KitFeature):
    
    def __init__(self, target_dir, backend_dir):
        self.feature_type = 'django_from_usecreatefunc'
        self.params = {'target_dir':target_dir, 'backend_dir':backend_dir}
    
    def execute(self):
        pass
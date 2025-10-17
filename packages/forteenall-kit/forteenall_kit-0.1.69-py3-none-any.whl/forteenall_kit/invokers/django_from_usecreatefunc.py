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
    
    feature_type = 'django_from_usecreatefunc'
    def __init__(self, target_dir, backend_dir):
        self.params = {'target_dir':target_dir, 'backend_dir':backend_dir}
    
    def execute(self):
        pass
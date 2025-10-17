from ..feature import KitFeature



class DjangoAppFeatureData:
    
    pass

class Feature(KitFeature):
    
    def __init__(self, app_name, backend_dir):
        self.feature_type = 'django_start_app'
        self.params = {'app_name':app_name, 'backend_dir':backend_dir}
    
    def execute(self):
        pass
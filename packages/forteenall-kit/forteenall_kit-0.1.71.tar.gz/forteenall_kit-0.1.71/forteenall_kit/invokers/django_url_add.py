from ..feature import KitFeature



class DjangoUrlFeatureData:
    
    pass

class Feature(KitFeature):
    
    feature_type = 'django_url_add'
    def __init__(self, view_name, url_pattern, app_name, backend_dir):
        self.params = {'view_name':view_name, 'url_pattern':url_pattern, 'app_name':app_name, 'backend_dir':backend_dir}
    
    def execute(self):
        pass
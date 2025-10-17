from ..feature import KitFeature



class DjangoUrlFeatureData:
    
    pass

class Feature(KitFeature):
    
    def __init__(self, view_name, url_pattern, app_name, backend_dir):
        feature_type = 'django_url_add'
        super().__init__(view_name=view_name, url_pattern=url_pattern, app_name=app_name, backend_dir=backend_dir, feature_type=feature_type)
    
    def execute(self):
        pass
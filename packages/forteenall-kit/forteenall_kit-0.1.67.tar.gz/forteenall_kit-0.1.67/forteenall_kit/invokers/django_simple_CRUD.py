from ..feature import KitFeature



class DjangoModelField:
    
    pass

class DjangoModelData:
    
    pass

class Feature(KitFeature):
    
    def __init__(self, backend_dir, model_fields, app_name, url_pattern):
        self.feature_type = 'django_simple_CRUD'
        self.params = {'backend_dir':backend_dir, 'model_fields':model_fields, 'app_name':app_name, 'url_pattern':url_pattern}
    
    def execute(self):
        pass
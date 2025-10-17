from ..feature import KitFeature



class DjangoModelField:
    
    pass

class DjangoModelData:
    
    pass

class Feature(KitFeature):
    
    def __init__(self, backend_dir, model_fields, app_name, url_pattern):
        feature_type = 'django_simple_CRUD'
        super().__init__(backend_dir=backend_dir, model_fields=model_fields, app_name=app_name, url_pattern=url_pattern, feature_type=feature_type)
    
    def execute(self):
        pass
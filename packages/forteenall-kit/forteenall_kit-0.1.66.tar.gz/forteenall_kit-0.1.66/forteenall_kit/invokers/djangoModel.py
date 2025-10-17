from ..feature import KitFeature



class DjangoModelField:
    
    pass

class DjangoModelData:
    
    pass

class Feature(KitFeature):
    
    def __init__(self, model_name, model_fields, export_dir):
        feature_type = 'djangoModel'
        super().__init__(model_name=model_name, model_fields=model_fields, export_dir=export_dir, feature_type=feature_type)
    
    def execute(self):
        pass
    
    def get(self):
        pass
from ..feature import KitFeature



class SerializerFeatureData:
    
    pass

class Feature(KitFeature):
    
    def __init__(self, model_name, import_path, export_dir):
        feature_type = 'django_model_viewset'
        super().__init__(model_name=model_name, import_path=import_path, export_dir=export_dir, feature_type=feature_type)
    
    def execute(self):
        pass
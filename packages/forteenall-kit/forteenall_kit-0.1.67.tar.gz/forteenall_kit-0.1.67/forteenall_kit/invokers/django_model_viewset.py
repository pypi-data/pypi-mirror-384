from ..feature import KitFeature



class SerializerFeatureData:
    
    pass

class Feature(KitFeature):
    
    def __init__(self, model_name, import_path, export_dir):
        self.feature_type = 'django_model_viewset'
        self.params = {'model_name':model_name, 'import_path':import_path, 'export_dir':export_dir}
    
    def execute(self):
        pass
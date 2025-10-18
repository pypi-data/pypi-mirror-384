from ..feature import KitFeature



class DjangoModelField:
    
    pass

class DjangoModelData:
    
    pass

class Feature(KitFeature):
    
    feature_type = 'djangoModel'
    def __init__(self, model_name, model_fields, export_dir):
        self.params = {'model_name':model_name, 'model_fields':model_fields, 'export_dir':export_dir}
    
    def execute(self):
        pass
    
    def get(self):
        pass
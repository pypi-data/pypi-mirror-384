from ..feature import KitFeature



class ComponentDefinition:
    
    pass

class NextPageData:
    
    pass

class Feature(KitFeature):
    
    def __init__(self, page_name, output_path, components):
        feature_type = 'nextjs_page_create'
        super().__init__(page_name=page_name, output_path=output_path, components=components, feature_type=feature_type)
    
    def execute(self):
        pass
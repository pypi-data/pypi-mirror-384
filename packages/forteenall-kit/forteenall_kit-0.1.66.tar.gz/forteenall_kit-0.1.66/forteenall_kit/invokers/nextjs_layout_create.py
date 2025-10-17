from ..feature import KitFeature



class ComponentDefinition:
    
    pass

class ProviderDefinition:
    
    pass

class LayoutData:
    
    pass

class Feature(KitFeature):
    
    def __init__(self, page_title, page_description, output_path, components, providers):
        feature_type = 'nextjs_layout_create'
        super().__init__(page_title=page_title, page_description=page_description, output_path=output_path, components=components, providers=providers, feature_type=feature_type)
    
    def execute(self):
        pass
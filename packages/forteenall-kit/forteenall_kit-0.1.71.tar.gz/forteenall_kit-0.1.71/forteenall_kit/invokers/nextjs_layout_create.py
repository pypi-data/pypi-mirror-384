from ..feature import KitFeature



class ComponentDefinition:
    
    pass

class ProviderDefinition:
    
    pass

class LayoutData:
    
    pass

class Feature(KitFeature):
    
    feature_type = 'nextjs_layout_create'
    def __init__(self, page_title, page_description, output_path, components, providers):
        self.params = {'page_title':page_title, 'page_description':page_description, 'output_path':output_path, 'components':components, 'providers':providers}
    
    def execute(self):
        pass
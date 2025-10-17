from ..feature import KitFeature



class ComponentDefinition:
    
    pass

class NextPageData:
    
    pass

class Feature(KitFeature):
    
    feature_type = 'nextjs_page_create'
    def __init__(self, page_name, output_path, components):
        self.params = {'page_name':page_name, 'output_path':output_path, 'components':components}
    
    def execute(self):
        pass
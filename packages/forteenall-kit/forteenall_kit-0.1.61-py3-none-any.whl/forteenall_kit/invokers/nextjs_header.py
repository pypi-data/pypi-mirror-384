from ..feature import KitFeature



class LinkDefinition:
    
    pass

class HeaderFeatureData:
    
    pass

class Feature(KitFeature):
    
    def __init__(self, is_fixed, logo_path, link_position, links):
        feature_type = 'nextjs_header'
        super().__init__(is_fixed=is_fixed, logo_path=logo_path, link_position=link_position, links=links, feature_type=feature_type)
    
    def execute(self):
        pass
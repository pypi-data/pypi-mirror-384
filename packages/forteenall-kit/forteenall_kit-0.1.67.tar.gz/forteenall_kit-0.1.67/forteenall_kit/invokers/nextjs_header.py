from ..feature import KitFeature



class LinkDefinition:
    
    pass

class HeaderFeatureData:
    
    pass

class Feature(KitFeature):
    
    def __init__(self, is_fixed, link_position, links):
        self.feature_type = 'nextjs_header'
        self.params = {'is_fixed':is_fixed, 'link_position':link_position, 'links':links}
    
    def execute(self):
        pass
    
    def html(self):
        pass
    
    def namespace(self):
        pass
from ..feature import KitFeature



class LinkData:
    
    pass

class Feature(KitFeature):
    
    def __init__(self, title, target_dir):
        feature_type = 'nextjs_link_button'
        super().__init__(title=title, target_dir=target_dir, feature_type=feature_type)
    
    def namespace(self):
        pass
    
    def html(self):
        pass
    
    def execute(self):
        pass
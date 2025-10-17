from ..feature import KitFeature



class LinkData:
    
    pass

class Feature(KitFeature):
    
    feature_type = 'nextjs_link_button'
    def __init__(self, title, target_dir):
        self.params = {'title':title, 'target_dir':target_dir}
    
    def namespace(self):
        pass
    
    def html(self):
        pass
    
    def execute(self):
        pass
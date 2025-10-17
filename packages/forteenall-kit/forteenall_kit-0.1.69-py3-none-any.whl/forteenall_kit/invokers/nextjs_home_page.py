from ..feature import KitFeature



class HomeData:
    
    pass

class Feature(KitFeature):
    
    feature_type = 'nextjs_home_page'
    def __init__(self, title):
        self.params = {'title':title}
    
    def execute(self):
        pass
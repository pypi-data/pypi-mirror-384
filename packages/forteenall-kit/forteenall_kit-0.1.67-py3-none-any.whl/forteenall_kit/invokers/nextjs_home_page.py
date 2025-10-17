from ..feature import KitFeature



class HomeData:
    
    pass

class Feature(KitFeature):
    
    def __init__(self, title):
        self.feature_type = 'nextjs_home_page'
        self.params = {'title':title}
    
    def execute(self):
        pass
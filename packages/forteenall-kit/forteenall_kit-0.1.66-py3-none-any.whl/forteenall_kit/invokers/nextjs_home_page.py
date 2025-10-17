from ..feature import KitFeature



class HomeData:
    
    pass

class Feature(KitFeature):
    
    def __init__(self, title):
        feature_type = 'nextjs_home_page'
        super().__init__(title=title, feature_type=feature_type)
    
    def execute(self):
        pass
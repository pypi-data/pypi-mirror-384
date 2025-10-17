from ..feature import KitFeature



class Data:
    
    pass

class Feature(KitFeature):
    
    def __init__(self, name, type):
        feature_type = 'spaceDup'
        super().__init__(name=name, type=type, feature_type=feature_type)
    
    def createDjangoProject(self):
        pass
    
    def createReactNativeProject(self):
        pass
    
    def createNextjsProject(self):
        pass
    
    def execute(self):
        pass
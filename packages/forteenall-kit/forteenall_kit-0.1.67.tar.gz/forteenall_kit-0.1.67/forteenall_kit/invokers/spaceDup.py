from ..feature import KitFeature



class Data:
    
    pass

class Feature(KitFeature):
    
    def __init__(self, name, type):
        self.feature_type = 'spaceDup'
        self.params = {'name':name, 'type':type}
    
    def createDjangoProject(self):
        pass
    
    def createReactNativeProject(self):
        pass
    
    def createNextjsProject(self):
        pass
    
    def execute(self):
        pass
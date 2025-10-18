from ..feature import KitFeature



class Data:
    
    pass

class Feature(KitFeature):
    
    feature_type = 'spaceDup'
    def __init__(self, name, type):
        self.params = {'name':name, 'type':type}
    
    def createDjangoProject(self):
        pass
    
    def createReactNativeProject(self):
        pass
    
    def createNextjsProject(self):
        pass
    
    def execute(self):
        pass
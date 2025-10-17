from ..feature import KitFeature



class CTAButtonData:
    
    pass

class HeroFeatureData:
    
    pass

class Feature(KitFeature):
    
    def __init__(self, title, subtitle, background_image, cta_buttons, use_animation):
        self.feature_type = 'nextjs_hero_component'
        self.params = {'title':title, 'subtitle':subtitle, 'background_image':background_image, 'cta_buttons':cta_buttons, 'use_animation':use_animation}
    
    def execute(self):
        pass
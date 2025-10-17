from ..feature import KitFeature



class CTAButtonData:
    
    pass

class HeroFeatureData:
    
    pass

class Feature(KitFeature):
    
    def __init__(self, title, subtitle, background_image, cta_buttons, use_animation):
        feature_type = 'nextjs_hero_component'
        super().__init__(title=title, subtitle=subtitle, background_image=background_image, cta_buttons=cta_buttons, use_animation=use_animation, feature_type=feature_type)
    
    def execute(self):
        pass
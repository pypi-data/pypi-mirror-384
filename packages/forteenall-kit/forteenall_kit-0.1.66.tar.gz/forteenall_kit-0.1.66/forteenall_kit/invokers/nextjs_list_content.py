from ..feature import KitFeature



class ListContent:
    
    pass

class Feature(KitFeature):
    
    def __init__(self, item_name, list_name, item_content, fetch_item_url):
        feature_type = 'nextjs_list_content'
        super().__init__(item_name=item_name, list_name=list_name, item_content=item_content, fetch_item_url=fetch_item_url, feature_type=feature_type)
    
    def execute(self):
        pass
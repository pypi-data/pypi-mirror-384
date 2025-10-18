from ..feature import KitFeature



class ListContent:
    
    pass

class Feature(KitFeature):
    
    feature_type = 'nextjs_list_content'
    def __init__(self, item_name, list_name, item_content, fetch_item_url):
        self.params = {'item_name':item_name, 'list_name':list_name, 'item_content':item_content, 'fetch_item_url':fetch_item_url}
    
    def execute(self):
        pass
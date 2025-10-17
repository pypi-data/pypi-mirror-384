class Html:
    
    def __init__(self, name:str| None=None, child=None, isSingle:bool=False, attr:dict[str, str]| None=None, className:list[str] | None = None) -> None:
        self.name = "" if name  is None else name
        self.isSingle = isSingle
        self.child = [] if child is None else child
        self.attr = {} if attr is None else attr
        self.className = className if className is not None else []
    
    def __iadd__(self, child): 
        if isinstance(child, list):
            self.child += child
        else:
            self.child.append(child)
        
        return self
    
    def addAttr(self, name, value, isString=False):
        """set attribute of tag standard"""
        
        if name in self.attr.keys():
            raise ValueError("duplicate attribute")
        
        if isString:
            self.attr[name] = f"'{value}'"
        else:
            self.attr[name] = value
    
    def __str__(self) -> str:
        
        attr = ""
        for key, value in self.attr.items():
            if value[-1] == "'":
                attr += f"{key}={value}"
            else:
                attr += f"{key}={{{value}}}"
        
        # check empty className
        if len(self.className) > 0:
            attr += f"className='{' '.join(self.className)}'"
        
        
        child = ""
        # create child in another html
        for tmp in self.child:
            child += f"\n{str(tmp)}"
        if self.isSingle:
            result = f"<{self.name} {attr}/>"
            if child:
                return f"<>{result}{child}</>"
            return result
        return f"<{self.name} {attr}>\n{child}\n</{self.name}>"


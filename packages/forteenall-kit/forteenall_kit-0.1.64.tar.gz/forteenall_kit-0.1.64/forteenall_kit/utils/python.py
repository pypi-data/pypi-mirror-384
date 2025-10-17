
from typing import Union
from .core import Program


class Python(Program):
    def headStyle(self, headName):
        return f"from {headName} import {', '.join(self.head[headName])}"



class PythonClass(Python):
    """genrate Python class"""

    def __init__(self, name, main=None, head=None, ref: list[str]| None = None, first=None):
        if ref is None:
            ref = []
        super().__init__(name=name, main=main, head=head, level=1, first=first)
        _imp = ""
        if len(ref) > 0:
            _imp = f"({', '.join(ref)})"
        self.main = f"class {name}{_imp}:\n" + self.main


class PythonFunc(Python):
    """genrate Python class"""

    def __init__(
        self,
        name,
        main=None,
        head=None,
        args: Union[dict[str, Union[str, None]], None] = None,
    ):
        if args is None:
            args = {}
        super().__init__(name=name, main=main, head=head, level=1)

        # create arguments in function
        args_ = []
        for key, value in list(args.items()):
            funcArg = ""
            funcArg += key
            # check for default value of function
            if value is not None:
                funcArg += "= " + value
            args_.append(funcArg)

        self.main = f"def {name}({', '.join(args_)}):" + self.main
        
# class DjangoSeralizer(DjangoClass):
    
#     def __init__(self, model, fields: list[str] | None = None, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.meta = DjangoClass(
#             name="Meta",
#             head=importModel(model.name)
#         )
        
#         self.fields = []
#         if fields is not None:
#             self.fields = fields
    
#     def addField2Meta(self, field_name):
#         self.fields = list(set([*self.fields, field_name]))
        
#     def getMain(self):
#         temp = self.meta
#         temp += f"fields={self.fields}"
#         self += temp
#         return super().getMain()
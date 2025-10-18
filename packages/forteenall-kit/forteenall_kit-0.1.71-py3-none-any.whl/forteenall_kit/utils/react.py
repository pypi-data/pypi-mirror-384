import re
from typing import Union, Any
from django.db.models import QuerySet
from .core import Program

class React(Program):
    def headStyle(self, headName: str) -> str:
        main = []
        tmp = "import {imp} from '{frm}'"
        imports = []
        mainImport = ""
        # check for main data import
        for h in self.head[headName]:
            if h[-1] == "!":
                mainImport = h
                continue
            imports.append(h)

        if mainImport != "":
            main.append(mainImport[:-1])

        if len(imports) > 0:
            main.append(f"{{ {', '.join(imports)} }}")

        return tmp.format(imp=", ".join(main), frm=headName)

    def add2Head(self, head: dict[str, str] | dict[str, list[str]], default=False):
        # check for import default
        if default:
            for frm, imp in head.items():
                if isinstance(imp, list):
                    head[frm] = [f"{imp[0]}!", *imp[1:]]
                else:
                    # error if last exists
                    if len([im for im in imp if im[-1] == "!"]):
                        raise ValueError("dubble Main import on react file")
                    head[frm] = f"{imp}!"

        return super().add2Head(head)


class ReactFunc(React):
    def __init__(
        self,
        name,
        main=None,
        head=None,
        args=None,
        export=False,
        default=False,
        isAsync=False,
        first=None,
    ):
        if args is None:
            args = {}
        super().__init__(name=name, main=main, head=head, level=1, first=first)

        # add txt to main content
        self.args = args
        self.export = export
        self.default = default
        self.isAsync = isAsync

    def addArgs(self, args: Union[dict[str, Union[str, None]], None] = None):
        """add args to function args"""
        if args is None:
            args = {}
        self.args |= args

    def getArgs(self, args):
        """create function arguments"""
        if len(args) == 0:
            return ""

        _args = []
        for k, v in args.items():
            arg = str(k)

            # check arg is not None
            if v is not None:
                # check for nested props
                if isinstance(v, dict):
                    arg += f":{{{self.getArgs(v)}}}"
                else:
                    arg += f":{v}"

            _args.append(arg)

        return ", ".join(_args)

    def getMain(self):
        txt = ""
        args = self.args
        # create txt var data
        if self.export:
            txt += "export "
            if self.default:
                txt += "default "

        if self.isAsync:
            txt += "async "

        txt += f"function {self.name}({self.getArgs(args)}){{\n    {self.main}\n}}"

        return super()._getMain(txt)


class ReactArrowFunc(React):
    def __init__(
        self,
        name=None,
        main=None,
        head=None,
        args: dict[str, str | None] | None | dict[str, None] | dict[str, str] = None,
        isAsync: bool = False,
        isReturn: bool = False,
        **kwargs,
    ):
        txt = ""
        if name is None:
            name = ""
        if args is None:
            args = {}
        self.args = args
        super().__init__(name=name, main=main, head=head, level=1, **kwargs)

        # create txt var data
        self.isAsync = isAsync

        self.isReturn = isReturn

    def _getMain(self, text):
        main = super()._getMain(text)
        _imp = ""

        # create function arguments
        _args = []
        if len(self.args) > 0:
            _args = [
                f"{k}{':' + v if v is not None else ''}" for k, v in self.args.items()
            ]

        # add args to main
        _imp = f"({', '.join(_args)}) => "
        if self.isAsync:
            _imp = "async " + _imp

        # check to ananymous function
        if self.isReturn:
            return f"{_imp} {main}"
        return f"{_imp} {{\n{main}\n}}"


class ReactType(React):
    def __init__(
        self,
        name: str,
        head: None | dict[str, str | list[str]] | Any = None,
        main: Any = None,
        level: int = 1,
        export: bool = False,
        first: str | None = None,
        ref: str | None = None,
        isInterface=True,
    ):
        # create react file
        super().__init__(name, head, "", first, level)
        if main is None:
            main = {}
        self.ref = ref
        self.export = export
        # set main to dict
        self.main = self.serializeFields(main)
        self.isInterface = isInterface

    def serializeFields(self, main):
        """normilize fields in types"""
        if isinstance(main, dict):
            return main
        elif isinstance(main, QuerySet) or isinstance(main, list):
            tmp_main = {}
            for field in main:
                tmp_main[field.name] = Field2TypeScript(field.type)[0]
            return tmp_main

        return {main.name: Field2TypeScript(main.type)[0]}

    def __iadd__(self, program):
        if isinstance(program, ReactType):
            self.add2Head(program.head)
            self.first += "\n" + program.first
            program = self.serializeFields(program.main)
        else:
            program = self.serializeFields(program)
        self.main |= program
        return self

    def _writeValues(self, data: dict):
        main = ""
        # generate types from dicts
        for key, value in data.items():
            if value is None:
                main += f"{key};\n"
            elif isinstance(value, dict):
                main += f"{key}:{{{self._writeValues(value)}}}"
            elif value[-1] == "?":
                main += f"{key}?: {value[:-1]};\n"
            else:
                main += f"{key}: {value};\n"

        return main

    def getMain(self):
        """get main text in type"""
        main = ""
        # set export of interface
        if self.export:
            main += "export "
        # main data in interface
        if self.isInterface:
            main += f"interface {self.name}"
            if self.ref is not None:
                main += f"extends {self.ref}"
        else:
            main += f"type {self.name} = "
        # add extends of interface
        main += "{"
        main += self._writeValues(self.main)
        main += "}"

        return main


class ReactNameSpace(React):
    def __init__(
        self,
        main: Any = None,
        name=None,
        head: None | dict[str, str | list[str]] | dict[str, str] = None,
        level: int = 1,
        export: bool = False,
        first: str | None = None,
        ref: str | None = None,
    ):
        # create react file
        super().__init__(name, head, "", first, level)

        self.ref = ref
        self.export = export
        # set main to dict
        self.main = {}
        if main is not None:
            self.main = main

    def __iadd__(self, program):
        if isinstance(program, ReactNameSpace):
            self.add2Head(program.head)
            self.first += "\n" + program.first
            program = program.main
        self.main |= program
        return self

    def getMain(self):
        """get main text in type"""
        main = ""
        # generate types from dicts
        for key, value in self.main.items():
            # add useEffect in nameSpace
            if key == "useEffect":
                self.add2Head({"react": "useEffect"})
                values = re.sub(r"['\"]", "", str(value[1]))
                main += f"useEffect({value[0]}, {values});\n"
                continue

            main += f"const {key} = {value};\n"

        return main

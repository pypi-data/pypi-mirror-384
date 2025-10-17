"""
FORTEENALL CORE
"""

from __future__ import annotations
from typing import Union, Any


# ------------------------------------------------------------------------+
#                                PROGRAMMING                              |
# ------------------------------------------------------------------------+


class Program:
    """
    programs file generator
    """

    def __init__(
        self,
        name: str | None = None,
        head: Union[None, dict[str, Union[str, list[str]]]] = None,
        main: Union[None, str] = None,
        first: str | None = None,
        level: int = 0,
        parent: str | None = None,
    ):
        if name is None:
            name = ""
        if main is None:
            main = ""
        if head is None:
            head = {}
        if first is None:
            first = ""
        if parent is None:
            parent = ""

        self.first = first
        self.parent: Any = parent
        self.name = name
        self.head = {}
        self.add2Head(head)
        self.main = main
        self.level = level

    def __iadd__(self, program):
        if isinstance(program, list):
            for p in program:
                self += p
            return self
        if isinstance(program, Program):
            self.add2Head(program.head)
            self.first += "\n" + str(program.first)
            self.main += str(program.parent)
            program = program.getMain() + "\n"
        tmp_level = "\n" + "    " * (self.level - 1)
        self.main += "\n" + (tmp_level).join(str(program).split("\n"))
        return self

    def add2Head(self, head: dict[str, str] | dict[str, list[str]]):
        for frm, imp in head.items():
            if isinstance(imp, str):
                imp = [imp]

            if frm in list(self.head.keys()):
                self.head[frm] = list(set([*self.head[frm], *imp]))
            else:
                self.head[frm] = list(set(imp))

    def headStyle(self, headName: str) -> str:
        return f"{headName}-{self.head[headName]}"

    def getMain(self):
        """get main"""
        return self._getMain(self.main)

    def _getMain(self, text):
        """add space to first of line acording by level"""
        return ("\n" + "    " * self.level).join(text.split("\n"))

    def __str__(self) -> str:
        result = ""

        if self.first != "":
            result += self.first + "\n\n"

        # call function before head. maybe adding head in getMain Func
        tmp_main = "\n\n" + self.getMain()

        # set style of head
        for head in list(self.head.keys()):
            result += self.headStyle(head) + "\n"

        if self.parent != "":
            result += f"\n{self.parent}\n"

        # add main to file
        result += tmp_main
        # return the code
        return result.strip()



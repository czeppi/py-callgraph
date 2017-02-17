from typing import Iterator, Optional

from filesystem import File
from exprtreebuilder import ModuleBuilder
from module import Module, ProgContext


class Program:

    def __init__(self, main_file: File):
        self._module_map = {}
        self._main_file = main_file
        self._main_module = Module(main_file.stem, main_file, self.context)
        self.add_module(self._main_module)

    @property
    def context(self):
        return ProgContext(root_dir=self._main_file.dir_, module_map=self._module_map)

    def build(self) -> None:
        ModuleBuilder(self._main_module).build()
         
    @property
    def main_module(self) -> 'Module':
        return self._main_module

    def add_module(self, module):
        self._module_map[module.fullname] = module

    def find_module(self, fullname: str) -> Optional[Module]:
        return self._module_map.get(fullname, None)

    def iter_modules(self) -> Iterator['Module']:
        yield from self._module_map.values()
        
    # def find_module(self, module_path: SymbolPath) -> 'Module':
    #     symbol = self._main_package.find_symbol_path(sym)
    #
    # def find_symbol(self, symbol_path: SymbolPath) -> 'Node':
    #     return self._main_package.find_symbol_path(symbol_path)

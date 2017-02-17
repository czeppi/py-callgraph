from typing import List, Optional, Iterator, Mapping
import ast

from filesystem import Dir, File


class SymbolPath:

    def __init__(self, parts: List[str]):
        assert isinstance(parts, list)
        self._parts = parts  # List[str]
        
    def __str__(self):
        return self.fullname

    def __len__(self):
        return len(self._parts)
        
    def __getitem__(self, key):
        return self._parts[key]
        
    def __add__(self, other):
        if isinstance(other, str):
            return SymbolPath(self._parts + [other])
        elif isinstance(other, SymbolPath):
            return SymbolPath(self._parts + other._parts)
        else:
            raise Exception(str(type(other)))
            
    def __iadd__(self, other):
        if isinstance(other, str):
            self._parts.append(other)
        elif isinstance(other, SymbolPath):
            self._parts += other._parts
        else:
            raise Exception(str(type(other)))
            
        return self
        
    def __radd__(self, other):
        if isinstance(other, str):
            return SymbolPath([other] + self._parts)
        else:
            raise Exception(str(type(other)))
            
    @property
    def fullname(self) -> str:
        return '.'.join(self._parts)

    @property
    def parts(self):
        return self._parts
        
    @property
    def head(self) -> str:
        return self._parts[0]
        
    @property
    def tail(self) -> 'SymbolPath':
        return SymbolPath(self._parts[1:])
        

class Symbol:

    def __init__(self, name: str):
        self._name = name  # type: str
        self._ref_expressions = set()  # type Set[Expression]

    @property
    def name(self) -> str:
        return self._name

    @property
    def fullname(self) -> str:
        return self.path.fullname

    @property
    def path(self) -> SymbolPath:
        raise Exception('not implemented.')

    def add_ref_expr(self, expr: 'Expression'):
        self._ref_expressions.add(expr)

    def iter_ref_expressions(self):
        yield from self._ref_expressions


class Scope(Symbol):

    def __init__(self, name: str, parent: Optional['Scope'], ast_node: ast.AST = None):
        super().__init__(name)
        self._parent_scope = parent  # type: Scope
        self._child_scopes = []      # type: List[Scope]
        self._classes = {}           # type: Mapping[str, ClassDef]
        self._functions = {}         # type: Mapping[str, FuncDef]
        self._variables = {}         # type: Mapping[str, Variable]
        self._ast_node = ast_node    # type: ast.AST
        self._calls = []             # type: List[Call]
        self._symbol_table = {}      # type: Mapping[str, Symbol]
        self._statements = []    # type: List[Expression]

    def __str__(self):
        return str(self.path)

    def clear(self):
        self._child_scopes.clear()
        self._classes.clear()
        self._functions.clear()
        self._variables.clear()
        self._calls.clear()
        self._symbol_table.clear()

    def add_child_scope(self, child_scope: 'Scope'):
        self._child_scopes.append(child_scope)
        self._symbol_table[child_scope.name] = child_scope

    def add_class(self, class_def_node: ast.ClassDef):
        cls_name = class_def_node.name
        assert cls_name not in self._classes
        new_class = ClassDef(class_def_node, parent=self)
        self._classes[cls_name] = new_class
        self.add_child_scope(new_class)
        return new_class

    def add_function(self, func_def_node: ast.FunctionDef) -> 'FuncDef':
        func_name = func_def_node.name
        assert func_name not in self._functions
        new_func = FuncDef(func_def_node, parent=self)
        self._functions[func_name] = new_func
        self.add_child_scope(new_func)
        return new_func

    def add_ann_assign_variable(self, var_name: str, ann_assign_node: ast.AnnAssign) -> 'AnnAssignVariable':
        assert var_name not in self._variables
        new_var = AnnAssignVariable(var_name, ann_assign_node, scope=self)
        self._variables[var_name] = new_var
        self._symbol_table[var_name] = new_var
        return new_var

    def add_assign_variable(self, var_name: str) -> Optional['Variable']:
        if var_name in self._variables:
            return
        new_var = Variable(var_name, var_type=None, scope=self)
        self._variables[var_name] = new_var
        self._symbol_table[var_name] = new_var
        return new_var

    def add_symbol(self, name, symbol: Symbol):
        assert name not in self._symbol_table
        self._symbol_table[name] = symbol

    def add_stmt(self, stmt: 'Statement'):
        self._statements.append(stmt)

    @property
    def parent_scope(self) -> Optional['Scope']:
        return self._parent_scope

    @property
    def path(self) -> SymbolPath:
        if self._parent_scope:
            return self._parent_scope.path + self.name
        else:
            if self.name:
                return SymbolPath([self.name])
            else:
                return SymbolPath([])

    @property
    def ast_node(self):
        return self._ast_node

    def iter_child_scopes(self) -> Iterator['Scope']:
        yield from self._child_scopes

    def iter_self_and_child_scopes_recursive(self) -> Iterator['Scope']:
        yield self
        for child_scope in self._child_scopes:
            yield from child_scope.iter_self_and_child_scopes_recursive()

    def iter_statements(self):
        yield from self._statements

    def iter_variables(self) -> Iterator['Variable']:
        yield from self._variables.values()

    def iter_simple_symbols(self):  # = variables ?!
        yield

    def find_class_def(self, class_name):
        return self._classes.get(class_name, None)

    def find_function_def(self, func_name):
        return self._functions.get(func_name, None)

    def iter_calls_from_here(self) -> Iterator['Call']:
        yield from self._calls

    def iter_calls_to_me(self) -> Iterator['Call']:
        yield

    def add_symbol_annotation(self, name: str, anno_node: ast.AST):
        self._symbol_table[name] = anno_node

    def find_symbol_annotation(self, name: str) -> Optional[ast.AST]:
        return self._symbol_table.get(name, None)

    def find_local_symbol_by_name(self, name: str) -> Optional[Symbol]:
        return self._symbol_table.get(name, None)

    def find_local_symbol_by_fullname(self, fullname: str) -> Optional[Symbol]:
        return self.find_local_symbol_by_path(SymbolPath(fullname.split('.')))

    def find_local_symbol_by_path(self, symb_path: SymbolPath) -> Optional[Symbol]:
        n = len(symb_path)
        if n == 0:
            return

        symbol = self.find_local_symbol_by_name(symb_path.head)
        if symbol is None:
            return

        if n == 1:
            return symbol

        return symbol.find_local_symbol_by_path(symb_path.tail)

    def find_symbol_by_name(self, name: str) -> Optional[Symbol]:
        local_symbol = self.find_local_symbol_by_name(name)
        if local_symbol is not None:
            return local_symbol

        global_scope = self._get_global_scope()
        if global_scope is not None:
            return global_scope.find_local_symbol_by_name(name)

    def find_symbol_by_fullname(self, fullname: str) -> Optional[Symbol]:
        return self.find_symbol_by_path(SymbolPath(fullname.split('.')))

    def find_symbol_by_path(self, symb_path: SymbolPath) -> Optional[Symbol]:
        local_symbol = self.find_local_symbol_by_path(symb_path)
        if local_symbol is not None:
            return local_symbol

        global_scope = self._get_global_scope()
        if global_scope is not None:
            return global_scope.find_local_symbol_by_path(symb_path)

    def _get_global_scope(self):
        if self.parent_scope is None:
            return

        scope = self.parent_scope
        while scope.parent_scope is not None:
            scope = scope.parent_scope
        return scope


class ProgContext:

    def __init__(self, root_dir: Dir, module_map: Mapping[str, 'Module']):
        self._root_dir = root_dir
        self._module_map = module_map

    @property
    def root_dir(self):
        return self._root_dir

    def add_module(self, module: 'Module'):
        assert module.fullname not in self._module_map
        self._module_map[module.fullname] = module

    def find_module(self, fullname: str):
        return self._module_map.get(fullname, None)


class Module(Scope):

    def __init__(self, name: str, file_: File, prog_context: ProgContext):
        super().__init__(name, parent=None)
        self._file = file_                 # type: File
        self._prog_context = prog_context  # type: ProgContext
        self._buf = None                   # type: Optional[str]
        self._call_graph = CallGraph()     # type: Optional[CallGraph]
        
    def read(self):
        self.clear()
        self._buf = self._file.read()
        self._lines = self._buf.split('\n')
        self._ast_node = ast.parse(self._buf)

    @property
    def lines(self):
        return self._lines

    @property
    def is_package(self):
        return self._file.name == '__init__.py'

    @property
    def file_(self) -> File:
        return self._file

    @property
    def prog_context(self):
        return self._prog_context

    @property
    def root_dir(self) -> Dir:
        return self._prog_context.root_dir

    @property
    def source(self) -> str:
        return self._buf

    @property
    def call_graph(self):
        return self._call_graph

    def find_scope_at_position(self, lineno: int, col_offset: int) -> Scope:
        pass
        
    def find_call_at_position(self, lineno: int, col_offset: int) -> 'Call':
        pass
        
            
class ClassDef(Scope):

    def __init__(self, ast_node: ast.ClassDef, parent: Scope):
        super().__init__(ast_node.name, parent, ast_node)
        self.lineno = ast_node.lineno   # type: int
        self._bases = []                # type: List[ClassDef]
        self._derived = []      # type: List[ClassDef]

    def add_base(self, base_class: 'ClassDef'):
        self._bases.append(base_class)

    def add_derived(self, derived_class: 'ClassDef'):
        self._derived.append(derived_class)

    def iter_bases(self):
        yield from self._bases

    def iter_derived(self):
        yield from self._derived

    def iter_self_and_derived(self):
        yield self
        yield from self._derived


class FuncDef(Scope):

    def __init__(self, ast_node: ast.FunctionDef, parent: Scope):
        super().__init__(ast_node.name, parent, ast_node)
        self.lineno = ast_node.lineno  # type: int
        self._return_type = None

    @property
    def return_type(self):
        return self._return_type
        
    def add_func_arg_variable(self, func_arg_node: ast.arg) -> 'FuncArgVariable':
        var_name = func_arg_node.arg
        assert var_name not in self._variables
        new_var = FuncArgVariable(func_arg_node, scope=self)
        self._variables[var_name] = new_var
        self._symbol_table[var_name] = new_var
        return new_var

    def add_self_variable(self, func_arg_node: ast.arg, class_def: ClassDef) -> 'Variable':
        var_name = func_arg_node.arg
        assert var_name not in self._variables
        new_var = Variable(func_arg_node, ClassRef(class_def), self)
        self._variables[var_name] = new_var
        self._symbol_table[var_name] = new_var
        return new_var

    def set_return_type(self, return_type: 'ExprType'):
        self._return_type = return_type


class ExprType:

    def get_attr_type(self, attr_name: str) -> Optional['ExprType']:
        return None

    def get_slice_type(self) -> Optional['ExprType']:
        return None

    def iter_call_return_types(self) -> Optional['ExprType']:
        pass


class ClassRef(ExprType):

    def __init__(self, class_def: ClassDef):
        self._class_def = class_def

    @property
    def class_def(self):
        return self._class_def

    def get_attr_type(self, attr_name: str) -> Optional['ExprType']:
        symbol = self._class_def.find_local_symbol_by_name(attr_name)
        if isinstance(symbol, ClassDef):
            return ClassRef(symbol)
        elif isinstance(symbol, FuncDef):
            return FuncRef(symbol)
        elif isinstance(symbol, Variable):
            return symbol.type_

    def iter_call_return_types(self) -> Optional['ExprType']:
        yield self


class FuncRef(ExprType):

    def __init__(self, func_def: FuncDef):
        self._func_def = func_def

    @property
    def func_def(self):
        return self._func_def

    def iter_call_return_types(self) -> Optional['ExprType']:
        return_type = self._func_def.return_type
        if isinstance(return_type, ClassRef):
            for derived_class in return_type.class_def.iter_self_and_derived():
                yield ClassRef(derived_class)
        else:
            yield return_type


class TSequence(ExprType):

    def __init__(self, item_type: ExprType):
        self._item_type = item_type

    def get_slice_type(self) -> Optional['ExprType']:
        return self._item_type


class TList(TSequence):

    pass


class TMapping(TSequence):

    def __init__(self, key_type: ExprType, value_type: ExprType):
        super().__init__(value_type)
        self._key_type = key_type


# class TIterator(TSequence):
#
#     pass



class Variable(Symbol):

    def __init__(self, name: str, var_type: Optional['ExprType'], scope: Scope):
        super().__init__(name)
        self._type = var_type
        self._scope = scope

    def set_type(self, var_type: ExprType):
        self._type = var_type

    @property
    def type_(self):
        return self._type

    @property
    def anno_node(self):  # for late calculation of self._type
        return None

    @property
    def scope(self):
        return self._scope

    @property
    def path(self) -> SymbolPath:
        return self._scope.path + self.name


class AnnAssignVariable(Variable):

    def __init__(self, var_name: str, assign_node: ast.AnnAssign, scope: Scope):
        var_type = None
        super().__init__(var_name, var_type, scope)
        self._assign_node = assign_node   # type: ast.AnnAssign
#        self.lineno = assign_node.lineno # type: int

    # def _calc_var_name(self, assign_node: ast.AnnAssign) -> str:
    #     target_node = assign_node.target
    #     if isinstance(target_node, ast.Name):
    #         return target_node.id
    #     elif isinstance(target_node, ast.Attribute):
    #         if isinstance(target_node.value, ast.Name):
    #             return target_node.value.id
    #
    @property
    def anno_node(self):
        return self._assign_node.annotation


class FuncArgVariable(Variable):

    def __init__(self, arg_node: ast.arg, scope: Scope):
        arg_name = arg_node.arg
        arg_type = None
        super().__init__(arg_name, arg_type, scope)
        self._arg_node = arg_node      # type: ast.arg
#        self.lineno = arg_node.lineno # type: int

    @property
    def anno_node(self):
        return self._arg_node.annotation


class ExprInfos:

    def __init__(self, scope_of_expr: Scope):
        self._scope_of_expr = scope_of_expr  # the scope, which contains the expression
        self._repr_scopes = set()  # type: Set[Scope]
        self._expr_types = set()  # type: Set[EsprType]

    def add_repr_scope(self, scope: Scope) -> None:
        self._repr_scopes.add(scope)

    def add_var(self, var: Variable) -> None:
        #if isinstance(var, TypedVariable):
        self.expr_types.add(var.type_)

    def add_symbol(self, symbol: Symbol):
        if isinstance(symbol, Scope):
            scope = symbol
            self._repr_scopes.add(scope)
        elif isinstance(symbol, Variable):
            var = symbol
            self.add_var(var)

    def add_expr_type(self, expr_type: ExprType):
        self._expr_types.add(expr_type)

    @property
    def scope_of_expr(self):
        return self._scope_of_expr

    def iter_repr_scopes(self):
        yield from self._repr_scopes

    def iter_expr_types(self):
        yield from self._expr_types


class CallGraph:
    def __init__(self):
        self.calls = set()
        self._call_strings = set()

    def add_call(self, caller: Scope, callee: Scope, call_node: ast.Call):
        call = Call(caller, callee, call_node)
        self.calls.add(call)
        self._call_strings.add(str(call))

    def contains(self,
                 call_str: str):  # p.e. 'g -> f' or 'gui.frame.MyFrame.on_button_clicked -> gui.frame.button.set_icon'
        return call_str in self._call_strings


class Call:
    def __init__(self, caller: Scope, callee: Scope, call_node: ast.Call):  # todo: use FuncDef instead of str
        self.caller = caller
        self.callee = callee
        self.call_node = call_node

    def __str__(self):
        return str(self.caller) + ' -> ' + str(self.callee)

    @property
    def lineno(self):
        return self.call_node.lineno

    @property
    def col_offset(self):
        return self.call_node.col_offset



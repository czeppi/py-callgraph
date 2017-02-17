from typing import Optional, List
import ast

from moduleobjects import Module, ClassDef, ClassRef, FuncDef, FuncRef, Scope, ExprInfos, Symbol, ProgContext, Variable
from filesystem import Dir, File
from annoanalyzer import AnnotationAnalyzer


class ModuleBuilder:

    def __init__(self, module: Module):
        super().__init__()
        self._module = module

    def build(self):
        self._module.read()
        module_node = self._module.ast_node
        ScopeBuildingVisitor(self._module, self._module.lines, self._module.prog_context).visit(module_node)
        TypeCalculator(self._module).calculate()
        NameNodeExprInfosSetter(self._module, module_node).set_expr_infos()
        i = 0
        while True:
            i += 1
            expr_setter = OtherNodeExprInfosSetter(module_node)
            expr_setter.set_expr_infos()
            assert i <= 1 or expr_setter.num_settings == 0
            if expr_setter.num_settings == 0:
                break
        CallVisitor(self._module.call_graph).visit(module_node)


class ScopeBuildingVisitor(ast.NodeVisitor):

    def __init__(self, scope: Scope, lines: List[str], prog_context: ProgContext):
        super().__init__()
        self._scope = scope
        self._lines = lines
        self._prog_context = prog_context

    def visit(self, node):  # only for cc-pyparser
        super().visit(node)
        if False:
            self.visit_ClassDef(node)
            self.visit_FunctionDef(node)
            self.visit_AnnAssign(node)
            self.visit_Import(node)
            self.visit_ImportFrom(node)

    def visit_ClassDef(self, class_def_node: ast.ClassDef):
        new_class = self._scope.add_class(class_def_node)

        for base_node in class_def_node.bases:
            if isinstance(base_node, ast.Name):
                base_class_name = base_node.id
                base_class = self._scope.find_symbol_by_name(base_class_name)
                if not base_class:
                    continue
                new_class.add_base(base_class)
                base_class.add_derived(new_class)

        for child_node in class_def_node.body:
            ScopeBuildingVisitor(new_class, self._lines, self._prog_context).visit(child_node)

    def visit_FunctionDef(self, func_def_node: ast.FunctionDef):
        new_func = self._scope.add_function(func_def_node)

        for i, arg in enumerate(func_def_node.args.args):
            if i == 0 and isinstance(self._scope, ClassDef):
                new_func.add_self_variable(arg, self._scope)
            else:
                new_func.add_func_arg_variable(arg)

        for child_node in func_def_node.body:
            ScopeBuildingVisitor(new_func, self._lines, self._prog_context).visit(child_node)

    def visit_AnnAssign(self, ann_assign_node: ast.AnnAssign):
        target_node = ann_assign_node.target
        if isinstance(target_node, ast.Name):
            var_name = target_node.id
            self._scope.add_ann_assign_variable(var_name, ann_assign_node)
        elif isinstance(target_node, ast.Attribute):
            if not isinstance(self._scope, FuncDef):
                return
            func_def = self._scope
            if func_def.name != '__init__':
                return
            if not isinstance(func_def.parent_scope, ClassDef):
                return
            class_def = func_def.parent_scope
            if not isinstance(target_node.value, ast.Name):
                return
            old_var_name = target_node.value.id
            if old_var_name != 'self':
                return
            old_var = func_def.find_local_symbol_by_name(old_var_name)
            if not isinstance(old_var, Variable):
                return
            if not isinstance(old_var.type_, ClassRef):
                return
            if old_var.type_.class_def != class_def:
                return
            new_var_name = target_node.attr
            class_def.add_ann_assign_variable(new_var_name, ann_assign_node)

    def visit_Assign(self, assign_node: ast.Assign):
        for target_node in assign_node.targets:
            if isinstance(target_node, ast.Name):
                var_name = target_node.id
                self._scope.add_assign_variable(var_name)
            # todo: x, y = ...
            # todo: self.x = ...

    def visit_For(self, for_node: ast.For):
        target_node = for_node.target
        if isinstance(target_node, ast.Name):
            var_name = target_node.id
            target_node.variable = Variable(var_name, var_type=None, scope=self._scope)

        for child_node in ast.iter_child_nodes(for_node):
            self.visit(child_node)

    def visit_Import(self, import_node: ast.Import):
        for alias in import_node.names:
            # import a.b as c  =>  alias.name = 'a.b', alias.asname = 'c'
            # "import .a" or "import ..a" is not allowed !
            fullname = alias.name
            asname = alias.asname
            imported_module = self._import_module_with_parents(fullname)
            if imported_module is not None:
                if asname:
                    module = self._prog_context.find_module(fullname)
                    if module is not None:
                        self._scope.add_symbol(asname, module)
                else:
                    name_parts = fullname.split('.')
                    package_name = name_parts[0]
                    package = self._prog_context.find_module(package_name)
                    self._scope.add_symbol(package_name, package)

    def visit_ImportFrom(self, import_from_node: ast.ImportFrom):
        module_name = import_from_node.module
        module_fullname = self._resolve_module_name(module_name)
        the_module = self._import_module_with_parents(module_fullname)
        if the_module is None:
            return

        for alias in import_from_node.names:
            # !! dot in "from xy import a.b" is invalid !!
            orig_name = alias.name
            as_name = alias.asname
            target_name = as_name if as_name else orig_name
            if the_module.is_package:
                submodule_fullname = module_fullname + '.' + orig_name
                package = the_module
                submodule = self._import_module_without_parents(submodule_fullname, package)
                self._scope.add_symbol(target_name, submodule)
            else:
                symbol = the_module.find_local_symbol_by_name(orig_name)
                if symbol is not None:
                    self._scope.add_symbol(target_name, symbol)

    def _import_module_without_parents(self, module_fullname: str, parent_package: Module) -> Optional[Module]:
        module = self._prog_context.find_module(module_fullname)
        if module is not None:
            return module

        name_parts = module_fullname.split('.')
        return self._import_module(name_parts, parent_package)

    def _import_module_with_parents(self, module_fullname: str) -> Optional[Module]:
        module = self._prog_context.find_module(module_fullname)
        if module is not None:
            return module

        name_parts = module_fullname.split('.')

        parent_package = None
        if len(name_parts) > 1:
            parent_package = self._import_packages(name_parts[:-1])
            if parent_package is None:
                return  # import not possible

        return self._import_module(name_parts, parent_package)

    def _import_packages(self, name_parts: List[str]) -> Optional[Module]:
        n = len(name_parts)
        assert n > 0

        parent_package = None
        if n > 1:
            parent_package = self._import_packages(name_parts[:-1])
            if parent_package is None:
                return  # import not possible

        fullname = '.'.join(name_parts)
        package = self._prog_context.find_module(fullname)
        if package is None:
            package = self._try_to_load_package(name_parts)
            if package is None:
                return  # import not possible

        if parent_package is not None:
            package_name = name_parts[-1]
            parent_package.add_symbol(package_name, package)  # todo: decide what todo, when symbol already exists

        return package

    def _import_module(self, name_parts: List[str], parent_package: Optional[Module]) -> Optional[Module]:
        module = self._try_to_load_regular_module(name_parts)
        if module is not None:
            if parent_package is not None:
                module_name = name_parts[-1]
                parent_package.add_symbol(module_name, module)
            return module

        package = self._try_to_load_package(name_parts)
        if package is not None:
            if parent_package is not None:
                package_name = name_parts[-1]
                parent_package.add_symbol(package_name, package)
            return package

    def _get_dir_by_name_parts(self, name_parts: List[str]) -> Optional[Dir]:
        if len(name_parts) == 0:
            return self._prog_context.root_dir

        parent_dir = self._get_dir_by_name_parts(name_parts[:-1])
        if parent_dir is not None:
            return parent_dir.get_subdir(name_parts[-1])

    def _try_to_load_package(self, name_parts: List[str]) -> Optional[Module]:
        if len(name_parts) > 0:
            fullname = '.'.join(name_parts)
            package_dir = self._get_dir_by_name_parts(name_parts)
            if package_dir is not None:
                return self._try_to_load_module(fullname, package_dir.get_file('__init__.py'))

    def _try_to_load_regular_module(self, name_parts: List[str]) -> Optional[Module]:
        parant_parts = name_parts[:-1]
        module_name = name_parts[-1]
        fullname = '.'.join(name_parts)

        parent_dir = self._get_dir_by_name_parts(parant_parts)
        if parent_dir is not None:
            module_file = parent_dir.get_file(module_name + '.py')
            return self._try_to_load_module(fullname, module_file)

    def _try_to_load_module(self, module_fullname: str, file_: File) -> Optional[Module]:
        if file_ is not None:
            return self._load_module(module_fullname, file_)

    def _load_module(self, module_fullname: str, file_: File) -> Module:
        # module_fullname = module.fullname
        # import_spec = importlib.util.find_spec(module_fullname)
        # if import_spec is None:
        #     return
        # import_fpathname = import_spec.origin
        # if not import_fpathname:
        #     return

        loaded_module = Module(module_fullname, file_, self._prog_context)
        module_builder = ModuleBuilder(loaded_module)
        module_builder.build()
        self._prog_context.add_module(loaded_module)
        return loaded_module

    def _resolve_module_name(self, module_name):
        n_dots = 0
        for i in module_name:
            if i != '.':
                break
            n_dots += 1
        return module_name  # todo: consider leading dots


# class VarFinderVisitor(ast.NodeVisitor):
#
#     def __init__(self, scope: Scope, lines: List[str], prog_context: ProgContext):
#         super().__init__()
#         self._scope = scope
#         self._lines = lines
#         self._prog_context = prog_context
#
#     def visit(self, node):
#
#
#     def visit_AnnAssign(self, ann_assign_node: ast.AnnAssign):
#         target_node = ann_assign_node.target
#         if isinstance(target_node, ast.Name):
#             var_name = target_node.id
#             self._scope.add_ann_assign_variable(var_name, ann_assign_node)
#         elif isinstance(target_node, ast.Attribute):
#             if not isinstance(self._scope, FuncDef):
#                 return
#             func_def = self._scope
#             if func_def.name != '__init__':
#                 return
#             if not isinstance(func_def.parent_scope, ClassDef):
#                 return
#             class_def = func_def.parent_scope
#             if not isinstance(target_node.value, ast.Name):
#                 return
#             old_var_name = target_node.value.id
#             if old_var_name != 'self':
#                 return
#             old_var = func_def.find_local_symbol_by_name(old_var_name)
#             if not isinstance(old_var, Variable):
#                 return
#             if not isinstance(old_var.type_, ClassRef):
#                 return
#             if old_var.type_.class_def != class_def:
#                 return
#             new_var_name = target_node.attr
#             class_def.add_ann_assign_variable(new_var_name, ann_assign_node)
#
#     def visit_Assign(self, assign_node: ast.Assign):
#         pass#sself._scope.add_ann_assign_variable(ann_assign_node)


class TypeCalculator:

    def __init__(self, scope: Scope):
        self._scope = scope

    def calculate(self):
        for var in self._scope.iter_variables():
            self._calc_var_type(var)

        if isinstance(self._scope, FuncDef):
            self._calc_func_return_type()

        for child_scope in self._scope.iter_child_scopes():
            TypeCalculator(child_scope).calculate()

    def _calc_var_type(self, var: Variable):
        anno_node = var.anno_node
        if anno_node is not None:
            var_type = AnnotationAnalyzer(anno_node, self._scope).evaluate_type()
            var.set_type(var_type)

    def _calc_func_return_type(self):
        func_def = self._scope
        parent_scope = func_def.parent_scope
        anno_node = func_def.ast_node.returns
        return_type = AnnotationAnalyzer(anno_node, parent_scope).evaluate_type()
        func_def.set_return_type(return_type)


class NameNodeExprInfosSetter(ast.NodeVisitor):

    def __init__(self, scope: Scope, start_node: ast.AST):
        super().__init__()
        self._scope = scope
        self._start_node = start_node

    def set_expr_infos(self) -> None:
        self.visit(self._start_node)

    def visit(self, node):  # only hint for cc-pyparser
        super().visit(node)
        if False:
            self.visit_Name(node)
            self.visit_ClassDef(node)
            self.visit_FunctionDef(node)

    def visit_Name(self, name_node: ast.Name):
        symbol = self._scope.find_symbol_by_name(name_node.id)
        if symbol is not None:
            name_node.expr_infos = ExprInfos(self._scope)
            if isinstance(symbol, Variable):
                var = symbol
                if var.type_ is not None:
                    if isinstance(var.type_, ClassRef):
                        for derived_class in var.type_.class_def.iter_self_and_derived():
                            name_node.expr_infos.add_expr_type(ClassRef(derived_class))
                    else:
                        name_node.expr_infos.add_expr_type(var.type_)
            elif isinstance(symbol, FuncDef):
                name_node.expr_infos.add_expr_type(FuncRef(symbol))
            elif isinstance(symbol, ClassDef):
                name_node.expr_infos.add_expr_type(ClassRef(symbol))
            else: # p.e. Module
                name_node.expr_infos.add_symbol(symbol)

    def visit_ClassDef(self, class_def_node: ast.ClassDef):
        class_name = class_def_node.name
        class_def = self._scope.find_class_def(class_name)
        assert class_def is not None
        for x in class_def_node.body:
            NameNodeExprInfosSetter(class_def, x).set_expr_infos()

    def visit_FunctionDef(self, func_def_node: ast.FunctionDef):
        func_name = func_def_node.name
        func_def = self._scope.find_function_def(func_name)
        assert func_def is not None
        for x in func_def_node.body:
            NameNodeExprInfosSetter(func_def, x).set_expr_infos()


class OtherNodeExprInfosSetter(ast.NodeVisitor):

    def __init__(self, ast_node: ast.AST):
        super().__init__()
        self._ast_node = ast_node
        self.num_settings = 0

    def visit(self, node):  # only hint for cc-pyparser
        super().visit(node)
        if False:
            self.visit_Attribute(node)
            self.visit_Call(node)
            self.visit_Subscript(node)

    def set_expr_infos(self) -> None:
        self.visit(self._ast_node)

    def visit_Attribute(self, attr_node: ast.Attribute):
        if hasattr(attr_node, 'expr_infos'):
            return

        # call recursive
        attr_expr = attr_node.value
        self._call_recursive(attr_expr)
        if not hasattr(attr_expr, 'expr_infos'):
             return

        # evaluate
        attr_name = attr_node.attr
        new_expr_infos = self._attr_expr(attr_expr.expr_infos, attr_name)
        if new_expr_infos is not None:
            attr_node.expr_infos = new_expr_infos
            self.num_settings += 1

    def _call_recursive(self, expr_node: ast.AST):
        if not hasattr(expr_node, 'expr_infos'):
            sub_setter = OtherNodeExprInfosSetter(expr_node)
            sub_setter.set_expr_infos()
            self.num_settings += sub_setter.num_settings
            if not hasattr(expr_node, 'expr_infos'):
                return

    def _attr_expr(self, old_expr_infos: ExprInfos, attr_name: str) -> Optional[ExprInfos]:
        new_expr_infos = ExprInfos(old_expr_infos.scope_of_expr)

        for old_scope in old_expr_infos.iter_repr_scopes():
            new_symbol = old_scope.find_local_symbol_by_name(attr_name)
            if new_symbol is not None:
                new_expr_infos.add_symbol(new_symbol)

        for old_expr_type in old_expr_infos.iter_expr_types():
            new_expr_type = old_expr_type.get_attr_type(attr_name)
            if isinstance(new_expr_type, ClassRef):
                for derived_class in new_expr_type.class_def.iter_self_and_derived():
                    new_expr_infos.add_expr_type(ClassRef(derived_class))
            else:
                if new_expr_type is not None:
                    new_expr_infos.add_expr_type(new_expr_type)

        return new_expr_infos

    def visit_Call(self, call_node: ast.Call):
        if hasattr(call_node, 'expr_infos'):
            return

        # call recursive
        call_expr = call_node.func
        self._call_recursive(call_expr)
        if not hasattr(call_expr, 'expr_infos'):
           return
        # todo: call args recursive

        # evaluate
        new_expr_infos = self._call_expr(call_expr.expr_infos)
        if new_expr_infos is not None:
            call_node.expr_infos = new_expr_infos
            self.num_settings += 1

    def _call_expr(self, old_expr_infos: ExprInfos) -> Optional[ExprInfos]:
        new_expr_infos = ExprInfos(old_expr_infos.scope_of_expr)

        for old_scope in old_expr_infos.iter_repr_scopes():
            self._call_extend_expr_infos(new_expr_infos, old_scope)

        for old_expr_type in old_expr_infos.iter_expr_types():
            for new_expr_type in old_expr_type.iter_call_return_types():
                new_expr_infos.add_expr_type(new_expr_type)

        return new_expr_infos

    def _call_extend_expr_infos(self, new_expr_infos: ExprInfos, old_symbol: Symbol):
        if isinstance(old_symbol, FuncDef):
            func = old_symbol
            if func.return_type is not None:
                new_expr_infos.add_expr_type(func.return_type)
        elif isinstance(old_symbol, ClassDef):
            cls = old_symbol
            new_expr_infos.add_expr_type(ClassRef(cls))  # A() -> A

    def visit_Subscript(self, subscript_node: ast.Subscript):
        if hasattr(subscript_node, 'expr_infos'):
            return

        # call recursive
        subscript_expr = subscript_node.value
        self._call_recursive(subscript_expr)
        if not hasattr(subscript_expr, 'expr_infos'):
            return
        # todo: call subscript_node.slice.value recursive

        # evaluate
        if hasattr(subscript_node.slice, 'value'):  # todo: not valid for "x[:2]" this has lower, step, upper
            new_expr_infos = self._subscript_expr(subscript_expr.expr_infos, subscript_node.slice.value)
            if new_expr_infos is not None:
                subscript_node.expr_infos = new_expr_infos
                self.num_settings += 1

    def _subscript_expr(self, old_expr_infos: ExprInfos, slice_node: ast.AST) -> Optional[ExprInfos]:
        new_expr_infos = ExprInfos(old_expr_infos.scope_of_expr)

        for old_expr_type in old_expr_infos.iter_expr_types():
            new_expr_type = old_expr_type.get_slice_type()
            if new_expr_type is not None:
                new_expr_infos.add_expr_type(new_expr_type)

        return new_expr_infos

    def visit_For(self, for_node: ast.For):
        target_node = for_node.target
        if not isinstance(target_node, ast.Name):
            return
        var_name = target_node.id

        if not hasattr(target_node, 'variable'):
            return
        var = target_node.variable
        if not isinstance(var, Variable):
            return
        if var.name != var_name:
            return
        if var.type_ is not None:
            return

        # call recursive
        iter_node = for_node.iter
        self._call_recursive(iter_node)
        if not hasattr(iter_node, 'expr_infos'):
            return
        iter_expr_infos = iter_node.expr_infos

        # iter_var_type
        iter_var_types = []
        for iter_expr_type in iter_expr_infos.iter_expr_types():
            new_expr_type = iter_expr_type.get_slice_type()
            if new_expr_type is not None:
                iter_var_types.append(new_expr_type)
        if len(iter_var_types) == 0:
            return

        assert len(iter_var_types) == 1
        iter_var_type = iter_var_types[0]

        var.set_type(iter_var_type)

        for child_node in for_node.body:
            self.visit(child_node)


class CallVisitor(ast.NodeVisitor):

    def __init__(self, call_graph):
        super().__init__()
        self._call_graph = call_graph

    def visit(self, node):  # only for cc-pyparser
        super().visit(node)
        if False:
            self.visit_Call(node)

    def visit_Call(self, call_node: ast.Call):
        call_expr = call_node.func
        if not hasattr(call_expr, 'expr_infos'):
            return

        expr_infos = call_expr.expr_infos
        for expr_type in expr_infos.iter_expr_types():
            callee = None
            if isinstance(expr_type, FuncRef):
                callee = expr_type.func_def
            elif isinstance(expr_type, ClassRef):
                callee = expr_type.class_def
            if callee:
                self._potentially_add_call(expr_infos.scope_of_expr, callee, call_node)

        for callee in expr_infos.iter_repr_scopes():
            self._potentially_add_call(expr_infos.scope_of_expr, callee, call_node)

        for child_node in ast.iter_child_nodes(call_node):
            CallVisitor(self._call_graph).visit(child_node)

    def _potentially_add_call(self, caller: Scope, callee: Symbol, call_node: ast.AST):
        if isinstance(callee, FuncDef) or isinstance(callee, ClassDef):
            self._call_graph.add_call(caller, callee, call_node)



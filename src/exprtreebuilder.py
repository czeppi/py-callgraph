import ast
from typing import List, Optional
from module import Scope, ProgContext, ClassDef, Variable, Module
from expressions import RAttributeExpression, RNameExpression, BinOpExpression, StrExpression
from expressions import LTupleExpression, LAttributeExpression, LNameExpression, NumExpression, LListExpression
from expressions import RListExpression, CallExpression
from statements import AssignStmt
from filesystem import Dir, File


def create_expr(ast_node: ast.AST):
    return ExprCreator(ast_node).create()


def create_rvalue_expr(ast_node: ast.AST):
    return ExprCreator(ast_node).create()


def create_lvalue_expr(ast_node: ast.AST):
    return LValueExprCreator(ast_node).create()


# class ExprTreeBuilder(ast.NodeVisitor):

    # def __init__(self, module_node: ast.Module):
        # self._module_node = module_node
        
    # def build(self):
        # self.visit(self._module)
        
    # def visit_ClassDef(self, class_def_node: ast.ClassDef):
    # def visit_FunctionDef(self, func_def_node: ast.FunctionDef):
    # def visit_AnnAssign(self, ann_assign_node: ast.AnnAssign):
    # def visit_Assign(self, assign_node: ast.Assign):
    # def visit_For(self, for_node: ast.For):


class ModuleBuilder:

    def __init__(self, module: Module):
        super().__init__()
        self._module = module

    def build(self):
        self._module.read()
        module_node = self._module.ast_node
        ScopeBuildingVisitor(self._module, self._module.lines, self._module.prog_context).visit(module_node)
        # TypeCalculator(self._module).calculate()
        # NameNodeExprInfosSetter(self._module, module_node).set_expr_infos()
        # i = 0
        # while True:
        #     i += 1
        #     expr_setter = OtherNodeExprInfosSetter(module_node)
        #     expr_setter.set_expr_infos()
        #     assert i <= 1 or expr_setter.num_settings == 0
        #     if expr_setter.num_settings == 0:
        #         break
        # CallVisitor(self._module.call_graph).visit(module_node)

    
class ScopeBuildingVisitor(ast.NodeVisitor):

    def __init__(self, scope: Scope, lines: List[str], prog_context: ProgContext):
        super().__init__()
        self._scope = scope
        self._lines = lines
        self._prog_context = prog_context

    def visit(self, node):  # only for selftest.py
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

    def visit_Import(self, import_node: ast.Import):
        for alias in import_node.names:
            # import a.b as c  =>  alias.name = 'a.b', alias.asname = 'c'
            # "import .a" or "import ..a" is not allowed !
            fullname = alias.name
            asname = alias.asname
            module_importer = ModuleImporter(self._prog_context)
            imported_module = module_importer.import_module_with_parents(fullname)
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
        module_importer = ModuleImporter(self._prog_context)
        module_fullname = module_importer.resolve_module_name(module_name)
        the_module = module_importer.import_module_with_parents(module_fullname)
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
                submodule = module_importer.import_module_without_parents(submodule_fullname, package)
                self._scope.add_symbol(target_name, submodule)
            else:
                symbol = the_module.find_local_symbol_by_name(orig_name)
                if symbol is not None:
                    self._scope.add_symbol(target_name, symbol)

        # def visit_AnnAssign(self, ann_assign_node: ast.AnnAssign):
        # target_node = ann_assign_node.target
        # if isinstance(target_node, ast.Name):
        # var_name = target_node.id
        # self._scope.add_ann_assign_variable(var_name, ann_assign_node)
        # elif isinstance(target_node, ast.Attribute):
        # if not isinstance(self._scope, FuncDef):
        # return
        # func_def = self._scope
        # if func_def.name != '__init__':
        # return
        # if not isinstance(func_def.parent_scope, ClassDef):
        # return
        # class_def = func_def.parent_scope
        # if not isinstance(target_node.value, ast.Name):
        # return
        # old_var_name = target_node.value.id
        # if old_var_name != 'self':
        # return
        # old_var = func_def.find_local_symbol_by_name(old_var_name)
        # if not isinstance(old_var, Variable):
        # return
        # if not isinstance(old_var.type_, ClassRef):
        # return
        # if old_var.type_.class_def != class_def:
        # return
        # new_var_name = target_node.attr
        # class_def.add_ann_assign_variable(new_var_name, ann_assign_node)

    def visit_Assign(self, assign_node: ast.Assign):
        lvalues = [create_lvalue_expr(target_node) for target_node in assign_node.targets]
        rvalue = create_rvalue_expr(assign_node.value)
        assign_stmt = AssignStmt(assign_node, lvalues, rvalue, self._scope)  # todo:  self._scope correct?
        assign_stmt.set_parent_recursive()
        self._scope.add_stmt(assign_stmt)

        # if isinstance(target_node, ast.Name):
        # var_name = target_node.id
        # self._scope.add_assign_variable(var_name)
        # todo: x, y = ...
        # todo: self.x = ...

    def visit_AugAssign(self, aug_assign_node: ast.AugAssign):
        pass

    def visit_For(self, for_node: ast.For):
        target_node = for_node.target
        if isinstance(target_node, ast.Name):
            var_name = target_node.id
            target_node.variable = Variable(var_name, var_type=None, scope=self._scope)

        for child_node in ast.iter_child_nodes(for_node):
            self.visit(child_node)


class ModuleImporter:

    def __init__(self, prog_context: ProgContext):
        self._prog_context = prog_context

    def resolve_module_name(self, module_name):
        n_dots = 0
        for i in module_name:
            if i != '.':
                break
            n_dots += 1
        return module_name  # todo: consider leading dots

    def import_module_without_parents(self, module_fullname: str, parent_package: Module) -> Optional[Module]:
        module = self._prog_context.find_module(module_fullname)
        if module is not None:
            return module

        name_parts = module_fullname.split('.')
        return self._import_module(name_parts, parent_package)

    def import_module_with_parents(self, module_fullname: str) -> Optional[Module]:
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


class ExprCreator:

    def __init__(self, ast_node: ast.AST):
        self._ast_node = ast_node
        
    def create(self):
        method_name = '_create_' + self._ast_node.__class__.__name__
        create_method = getattr(self, method_name, None)
        if create_method is None:
            raise Exception('{} not found.'.format(method_name))
        return create_method(self._ast_node)
        
    def _create_Str(self, str_node: ast.Str):
        return StrExpression(str_node)

    def _create_Num(self, num_node: ast.Num):
        return NumExpression(num_node)

    def _create_List(self, list_node: ast.List):
        item_expressions = []
        for elt in list_node.elts:
            item_expr = create_expr(elt)
            item_expressions.append(item_expr)
        list_expr = RListExpression(list_node, item_expressions)
        return list_expr

    def _create_Expr(self, expr_node: ast.Expression):
        return create_expr(expr_node.value)
        # expr = ExprExpression(expr_node, value_expr)

    def _create_Attribute(self, attr_node: ast.Attribute):
        stem_expr = create_expr(attr_node.value)
        return RAttributeExpression(attr_node, stem_expr)

    def _create_Name(self, name_node: ast.AST):
        return RNameExpression(name_node)
        
    def _create_BinOp(self, bin_op_node: ast.BinOp):
        left_expr = create_expr(bin_op_node.left)
        right_expr = create_expr(bin_op_node.right)
        return BinOpExpression(bin_op_node, left_expr, right_expr)

    def _create_Call(self, call_node: ast.Call):
        func_expr = create_expr(call_node.func)
        return CallExpression(call_node, func_expr)


class LValueExprCreator:

    def __init__(self, ast_node: ast.AST):
        self._ast_node = ast_node

    def create(self):
        method_name = '_create_' + self._ast_node.__class__.__name__
        create_method = getattr(self, method_name, None)
        if create_method is not None:
            return create_method(self._ast_node)

    def _create_Tuple(self, tuple_node: ast.Tuple):
        item_expressions = [create_lvalue_expr(elt) for elt in tuple_node.elts]
        tuple_node = self._ast_node
        return LTupleExpression(tuple_node, item_expressions)

    def _create_Attribute(self, attr_node: ast.Attribute):
        stem_expr = create_rvalue_expr(attr_node.value)
        return LAttributeExpression(attr_node, attr_name=attr_node.attr)

    def _create_Name(self, name_node: ast.Name):
        name_node = self._ast_node
        return LNameExpression(name_node)



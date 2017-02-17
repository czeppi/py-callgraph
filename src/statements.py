import ast
from typing import List
from expressions import LExpression, RExpression, ExprGroup
from expressions import UpdateTypeResult
from nodes import Node


class Statement(Node):

    def __init__(self, ast_node: ast.AST, scope: 'Scope'):
        super().__init__(ast_node)
        self._scope = scope


class AssignStmt(Statement):

    def __init__(self, assign_node: ast.Assign, left_sides: List[LExpression], right_side: RExpression, scope: 'Scope'):
        super().__init__(assign_node, scope)
        self._left_sides = left_sides
        self._right_side = right_side
        self._children_group = ExprGroup(left_sides + [right_side])

    def iter_children(self):
        yield from self._left_sides
        yield self._right_side

    def update_type(self):
        if self._right_side.type_identified:
            dirty_nodes = []
            for left_side in self._left_sides:
                left_side.assign_type_from_rtype(self._right_side.type_)
            return UpdateTypeResult(dirty_nodes)  # todo: only True, if something changed
        return UpdateTypeResult([])

    def iter_dependent_expr_and_statements(self):
        yield from self._left_sides  # todo: check it



class ReturnStmt(Statement):

    def __init__(self, return_node: ast.Return, expr: 'Expression', func_def: 'FuncDef'):
        super().__init__(return_node, func_def)
        self._expr = expr

    @property
    def func_def(self):
        return self._scope

    def update_type(self):
        if self._expr.type_identified:
            self.func_def.on_type_identified(self) # todo: make it correct


class ForStmt(Statement):

    def __init__(self, for_node: ast.For, target: 'Expression', iter: 'Expression', scope: 'Scope'):
        super().__init__(for_node, scope)
        self._target = target  # variable
        self._iter   = iter    # iterator for variable

    def update_type(self):
        if self._target.type_identified:
            var_type = self._target.type_.get_dereferencing_type  # todo: is dereferencing correct?
            self._target.set_type(var_type)  # todo: implement


class WhileStmt(Statement):

    def __init__(self, while_node: ast.While, scope: 'Scope'):
        super().__init__(while_node, scope)


class IfStmt(Statement):

    def __init__(self, if_node: ast.If, scope: 'Scope'):
        super().__init__(if_node, scope)


class ExprStmt(Statement):

    def __init__(self, expr_node: ast.Expr, scope: 'Scope'):
        super().__init__(expr_node, scope)


class DeleteStmt(Statement):

    def __init__(self, delete_node: ast.Delete, scope: 'Scope'):
        super().__init__(delete_node, scope)
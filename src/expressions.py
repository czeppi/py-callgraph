
#   !! This file is experimental !!


import ast
from typing import Optional, List, Iterable

from nodes import Node
from exprtypes import ExprType, StrType, NumType, TupleType, ListType, ClassType
from module import ClassDef, Module, Variable, Scope


"""
class A:
    def f(self):
        pass
        
x = []
x.append(A())
x += [A()]

x[0].f()

=>

x = []         =>  type = List(usage_evaluated=False)
x.append(A())  =>  type = List[A]
x += [A()]     =>  type = List[A]  (usage_evaluated=True)
x[0].f()       =>  x is List[A], x[0] is A, x[0].f is A.f
"""

"""
x = {'a': [2, 3]}
a, (b, c) = [[1,2,3], [[3,4,5], [5,6,7]]]
a.x = 17
"""

"""
class A:
    def __init__(self):
        x = []
        
def f(x):
    x.append(17)
    
def g(a: A):
    f(a.x)
"""


"""
Algorithmus:
------------

def specify_all_expr_types():  # advanced strategy (later?)
    for i in range(MAX_OUTER_ITERATIONS):
        specify_all_sure_expr_types()  # => falls hier ein Unsicherer Typ zu Widersprüchen führt, so wird dieser für immer gesperrt
        if found_all_expr_types():
            return
        specify_unsure_expr_types():  # 
    

def specify_all_sure_expr_types():  # standard strategy
    eval_name_expressions()  # => Finde Klassen- und Modulreferenzen
    eval_all_expressions_with_fix_types()  # hier notwendig??
    for i in range(MAX_INNER_ITERATIONS):
        were_types_extended = eval_expressions_for_type_extensions()
        were_expr_types_specifid = eval_all_expressions_with_fix_types()
        if not were_types_extended and not were_expr_types_specifid:
            break:
        
        
Problemfall? (infinte extend and reduce):
-------------------------------------------
class A:
    def f(self):
        pass
        
class B:
    def g(self):
        pass
        
def p(x):
    lst = []
    lst.append(A())   # extend type
    q(lst)
    
def q(lst):
    for x in lst:
        x.g()   # reduce type
"""




class Expression(Node):

    def __init__(self, ast_node: ast.AST):
        super().__init__(ast_node)
        self._type_identified = False
        self._type = None

    @property
    def type_(self):
        return self._type

    @property
    def type_identified(self):
        return self._type_identified

    def iter_dependent_expr_and_statements(self):
        yield self._parent

        # # a type should have no reference to its usages (refs are stored in symbols)
        # if self._type is not None:
        #     for type_expr in self._type.iter_expression():
        #         if type_expr is not self:
        #             yield type_expr

    def update_type(self):
        new_type = self.identify_type()
        # if new_type is not None:
        #     new_type.add_expression(self)  # todo ??
        changed_something = (new_type != self._type)
        self._type_identified = (new_type is not None)
        self._type = new_type

        print('udate_type: {}: new_type: {}'.format(self, new_type))

        return UpdateTypeResult(list(self.iter_dependent_expr_and_statements()), new_type)

        
class LExpression(Expression):

    def assign_type_from_rtype(self, rtype: ExprType) -> bool:
        raise Exception('net yet implemented')
        

class RExpression(Expression):  # todo: is this class necessary or use simple Expression?

    pass

    
class LNameExpression(LExpression):

    def __init__(self, name_node: ast.Name):
        super().__init__(name_node)
        self._name = name_node.id
        # todo: add variable to scope here?

    def iter_children(self):
        return []

    def assign_type_from_rtype(self, rtype: ExprType) -> bool:
        old_var = self.scope.find_local_symbol_by_name(self._name)
        if old_var is None:
            new_var = self.scope.add_assign_variable(self._name)
            new_var.set_type(rtype)
            #new_var.add_ref_expr(self)  # todo: use add_def_expr or omit it at all
        else:
            if old_var.has_type:
                old_var.merge_type(rtype)  # todo: add_ref_expr
            else:
                old_var.set_type(rtype)  # todo: add_ref_expr
            

class RNameExpression(RExpression):

    def __init__(self, name_node: ast.Name):
        super().__init__(name_node)
        self._name = name_node.id
        self._symbol = None

    def iter_children(self):
        return []

    def iter_dependent_expr_and_statements(self):
        self._lazy_init_symbold()
        yield self._parent

        symbol = self._symbol
        if symbol is not None and isinstance(symbol, Variable):
            var = symbol
            for expr in var.iter_ref_expressions():
                if expr is not self:
                    yield expr

    def identify_type(self):
        self._lazy_init_symbold()

        symbol = self._symbol
        if symbol is not None:
            symbol.add_ref_expr(self)

            if isinstance(symbol, Module):
                raise Exception('not yet implemented')
            elif isinstance(symbol, ClassDef):
                return ClassType(symbol)
            elif isinstance(symbol, Variable):
                var = symbol
                return var.type_

    def _lazy_init_symbold(self):
        if self._symbol is None:
            scope = self.scope
            if scope is not None:
                self._symbol = scope.find_local_symbol_by_name(self._name)
                if self._symbol is not None:
                    self._symbol.add_ref_expr(self)


class LAttributeExpression(LExpression):

    def __init__(self, attr_node: ast.Attribute, stem: Expression):
        super().__init__(attr_node)
        self._stem = stem
        self._attr_name = attr_node.attr

    def iter_children(self):
        yield self._stem

    def identify_type(self):
        pass
        
    def assign_type_from_rtype(self, rtype: ExprType) -> bool:
        if not self._stem.type_identified:
            return False
        
        self._stem.type_.set_attr_type(self._attr_name, rtype)

        
class RAttributeExpression(RExpression):

    def __init__(self, attr_node: ast.Attribute, stem: Expression):
        super().__init__(attr_node)
        self._stem = stem
        self._attr_name = attr_node.attr

    def iter_children(self):
        yield self._stem

    pass
    # def identify_type(self):
    #     if self._value.is_evaluated() and is List:
    #         if self._attr_name == 'append':
    #
    #     if isinstance(self._ast_node.value, ast.Name

        
class CallExpression(Expression):

    def __init__(self, call_node: ast.Call, func_expr: Expression):
        super().__init__(call_node)
        self._func_expr = func_expr

    def iter_children(self):
        yield self._func_expr

    def identify_type(self):
        if self._func_expr.type_identified:
            return self._func_expr.type_.get_call_type()


class LSubscriptExpression(LExpression):

    def iter_children(self):
        raise Exception('net yet implemented')


class RSubscriptExpression(RExpression):

    def iter_children(self):
        raise Exception('net yet implemented')


class LTupleExpression(LExpression):

    def __init__(self, tuple_node: ast.Tuple, items: List[Expression]):
        super().__init(tuple_node)
        self._items = ExprGroup(items)

    def __iter__(self):
        yield from self._items

    def __len__(self):
        return len(self._items)
        
    def __getitem__(self, i: int):
        return self._items[i]

    def iter_children(self):
        yield from self._items

    def assign_type_from_rtype(self, rtype: ExprType):
        if isinstance(rtype, TupleType):
            assert len(self) == len(rtype)
            for i, left_item in enumerate(self._items):
                left_item.assign_type_from_rtype(rtype[i])
        elif isinstance(rtype, ListType):
            for left_item in self._items:
                left_item.assign_type_from_rtype(rtype.item_type)
        else:
            raise Exception('not implemented')
                


class RTupleExpression(RExpression):

    def __init__(self, tuple_node: ast.Tuple, items: List[Expression]):
        super().__init__(tuple_node)
        self._items = ExprGroup(items)
            
    def __len__(self):
        return len(self._items)

    def __iter__(self):
        yield from self._items

    def __getitem__(self, i: int):
        return self._items[i]

    def iter_children(self):
        yield from self._items

    def identify_type(self):
        if self._items.are_types_identified():
            return TupleType(x.type_ for x in self._items)


class LListExpression(LExpression):

    def __init__(self, list_node: ast.List, items: List[Expression]):
        super().__init__(list_node)
        self._items = ExprGroup(items)

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        yield from self._items

    def __getitem__(self, i: int):
        return self._items[i]

    def iter_children(self):
        yield from self._items

    def assign_type_from_rtype(self, rtype: ExprType):
        if isinstance(rtype, TupleType):
            assert len(self) == len(rtype)
            for i, left_item in enumerate(self._items):
                left_item.assign_type_from_rtype(rtype[i])
        elif isinstance(rtype, ListType):
            for left_item in self._items:
                left_item.assign_type_from_rtype(rtype.item_type)
        else:
            raise Exception('not implemented')


class RListExpression(LExpression):

    def __init__(self, list_node: ast.List, items: List[Expression]):
        super().__init__(list_node)
        self._items = items
        self._group = ExprGroup(items)

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        yield from self._items

    def __getitem__(self, i: int):
        return self._items[i]

    def iter_children(self):
        yield from self._items

    def identify_type(self):
        #if self._group.all_types_identified:
        if all(x.type_identified for x in self._items):
            item_types = set(x.type_ for x in self._items)
            assert len(item_types) == 1  # todo: support '> 1'
            item_type = item_types.pop()
            return ListType(item_type)


class BinOpExpression(RExpression):

    def __init__(self, bin_op_node: ast.BinOp, left_expr: RExpression, right_expr: RExpression):
        super().__init__(bin_op_node)
        self._left_expr = left_expr
        self._right_expr = right_expr

    @property
    def left_expr(self):
        return self._left_expr

    @property
    def right_expr(self):
        return self._right_expr

    def iter_children(self):
        yield self._left_expr
        yield self._right_expr

    def identify_type(self):
        if self._left_expr.type_identified and self._right_expr.type_identified:
            left_type = self._left_expr.type_
            right_type = self._right_expr.type_

            result_type = self._get_result_type_from_standard_types()
            if result_type is not None:
                return result_type

            result_type = self._get_result_type_from_normal_user_defined_op()
            if result_type is not None:
                return result_type

            result_type = self._get_result_type_from_reversed_user_defined_op()
            if result_type is not None:
                return result_type

    def _get_result_type_from_standard_types(self, left_type, right_type):
        if isinstance(left_type, NumType) and isinstance(right_type, NumType):
            return NumType()
        elif isinstance(left_type, NumType) and isinstance(right_type, StrType):
            return StrType()
        elif isinstance(left_type, StrType) and isinstance(right_type, NumType):
            return StrType()
        elif isinstance(left_type, StrType) and isinstance(right_type, StrType):
            return StrType()
        elif isinstance(left_type, NumType) and isinstance(right_type, ListType):
            return right_type
        elif isinstance(left_type, ListType) and isinstance(right_type, NumType):
            return left_type

    def _get_result_type_from_normal_user_defined_op(self, left_type, right_type):
        if isinstance(left_type, ClassType):
            func_name = self._calc_func_name_from_op_node(self._ast_node.op)
            # todo:
            #   func = left_type.find_function(func_name)
            #   if func is not None and func.return_type_identifed
            #       return func.return_type

    def _get_result_type_from_reversed_user_defined_op(self, left_type, right_type):
        if isinstance(right_type, ClassType):
            func_name = self._calc_reverse_func_name_from_op_node(self._ast_node.op)
            # todo:
            #   func = left_type.find_function(func_name)
            #   if func is not None and func.return_type_identifed
            #       return func.return_type

    def _calc_forward_func_name_from_op_node(self, op_node: ast.AST):
        ast_class2func_name = {
            ast.Add: '__add__',
            ast.Sub: '__sub__',
            ast.Mult: '__mul__',
            ast.MatMult: '__matmul__',
            ast.Div: '__truediv__',
            ast.FloorDiv: '__floordiv__',
            ast.Mod: '__mod__',
            #ast.DivMod: '__divmod__',  # ???
            ast.Pow: '__pow__',
            ast.LShift: '__lshift__',
            ast.RShift: '__rshift__',
            ast.BitAnd: '__and__',
            ast.BitXor: '__xor__',
            ast.BitOr: '__or__',
        }
        for op_node_class, func_name in ast_class2func_name.items():
            if isinstance(op_node, op_node_class):
                return func_name

    def _calc_reverse_func_name_from_op_node(self, op_node: ast.AST):
        ast_class2func_name = {
            ast.Add: '__radd__',
            ast.Sub: '__rsub__',
            ast.Mult: '__rmul__',
            ast.MatMult: '__rmatmul__',
            ast.Div: '__rtruediv__',
            ast.FloorDiv: '__rfloordiv__',
            ast.Mod: '__rmod__',
            #ast.DivMod: '__divmod__',  # ???
            ast.Pow: '__rpow__',
            ast.LShift: '__rlshift__',
            ast.RShift: '__rrshift__',
            ast.BitAnd: '__rand__',
            ast.BitXor: '__rxor__',
            ast.BitOr: '__ror__',
        }
        for op_node_class, func_name in ast_class2func_name.items():
            if isinstance(op_node, op_node_class):
                return func_name


class NumExpression(Expression):
    
    def __init__(self, num_node: ast.Num):
        super().__init__(num_node)
        self._type = None
        self._type_identified = False

    @property
    def type_(self):
        return self._type

    def iter_children(self):
        return []

    def identify_type(self):
        return NumType(value=self._ast_node.n)


class StrExpression(Expression):
    
    def __init__(self, str_node: ast.Str):
        super().__init__(str_node)
        self._type = None
        self._type_identified = False
        
    def iter_children(self):
        return []

    def identify_type(self):
        return StrType(value=self._ast_node.s)


class UpdateTypeResult:

    def __init__(self, dirty_nodes: List[Node], type_: Optional[ExprType] = None):
        self._dirty_nodes = dirty_nodes
        #self._type = type_

    @property
    def changed_something(self):
        return len(self._dirty_nodes) > 0

    def iter_dirty_nodes(self):
        yield from self._dirty_nodes

    # @property
    # def type_(self):
    #     return self._type

#-------------------------------------------------------------------------


class ExprGroup:  # SubExpr:

    def __init__(self, items: Iterable[Expression]):
        self._items_with_identified_types = set()   # type: Set[Expression]
        self._items_with_unidentified_types = set() # type: Set[Expression]
        for item in items:
            self._add(item)

    def _add(self, item: Expression):
        if item.type_identified:
            self._items_with_identified_types.add(item)
        else:
            self._items_with_unidentified_types.add(item)

    @property
    def all_types_identified(self):
        return len(self._items_with_unidentified_types) == 0
        
    def on_item_type_identified(self, item: Expression):
        self._items_with_unidentified_types.remove(item)
        self._items_with_identified_types.add(item)
        
        
#-------------------------------------------------------------------------



"""
alt:

c = C()
a.b(c)[]

=> a muss Attribut b haben
   b muss aufrufbar sein
   b muss als ersten Parameter ein C bekommen können
   Rückgabewert von b muss subscriptable sein
   
   
a.b().c
   |
=> call muss eine Funktion mit dem Namen b sein
   call muss eine Klasse zurückliefern, die ein Attribut c hat
   
   
1. bestimmt Name-Knoten
2. Grenze Types von Expr durch Attributnamen ein
3. Schränke diese weiter ein duch Calls + Subscribes


Expr kann
- klar bestimmt sein
- komplett unbestimmt sein
- falls etwas eigenes, dann eine Obermenge von möglichen Typen
"""        
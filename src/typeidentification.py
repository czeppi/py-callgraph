from typing import Union, Iterable
from collections import deque
from expressions import Expression, NumExpression, StrExpression, RNameExpression, RListExpression
from exprtypes import ExprType


MAX_ITERATIONS = 1000


class TypeIdentification:

    def identify_by_module_list(self, module_list):
        todo_list = list(self._iter_start_todos(module_list))
        self.identify_by_todo_list(todo_list)

    def _iter_start_todos(self, module_list):
        for module in module_list:
            for scope in module.iter_self_and_child_scopes_recursive():
                for stmt in scope.iter_statements():
                    for expr_or_stmt in stmt.iter_self_and_subtrees():
                        if isinstance(expr_or_stmt, NumExpression)\
                        or isinstance(expr_or_stmt, StrExpression)\
                        or isinstance(expr_or_stmt, RNameExpression)\
                        or isinstance(expr_or_stmt, RListExpression):  # for empty lists
                            yield expr_or_stmt

    def identify_by_todo_list(self, todo_list):
        for expr_or_stmt in todo_list:
            # type_todo_list = self._create_and_assign_types(expr_todo_list)
            # expr_todo_list = self._update_types(type_todo_list)
            # changed_expr_and_types = self._process_expr(expr)
            # for expr_or_type in changed_expr_and_types:
            #     if isinstance(expr_or_type, Expression):
            #         changed_expr = expr_or_type
            #         for expr in changed_expr.iter_dependent_expr():
            #             todo_list.append(expr)
            #     elif isinstance(expr_or_type, ExprType):
            #         expr_type = expr_or_type
            #         todo_list.append(expr_type)
            self._process_expr_or_stmt(expr_or_stmt, todo_list)

    def _process_expr_or_stmt(self, expr_or_stmt: 'Union[Expression, Statement]', todo_list: 'TodoList'):
        update_result = expr_or_stmt.update_type()
        if update_result.changed_something:
            for expr_or_stmt2 in expr_or_stmt.iter_dependent_expr_and_statements():
                todo_list.append(expr_or_stmt2)
        return update_result



        # def _create_and_assign_types(self, expr_todo_list):
        # # !! Zuweisung kann auch Typänderung bewirken
          # # a = []      # => Type von a ist List[Unknown]
          # # a[0] = A()  # => Type von a ist List[Union[A, Unknown]]
        # for i, expr in enumerate(expr_todo_list):
            # new_todos = expr.update()
            # self._todo_list.extend(new_todos)
            # if i > MAX_ITERATIONS:
                # raise Exception(str(i))
        # return type_todo_list
        
    # def _update_types(self, type_todo_list):
        # new_expr_todo_list = TodoList()
        # for expr_type in self._types_to_update:
            # for expr in expr_type.dependent_expressions:
                # new_expr_todo_list.append(expr)

       
class TodoList:
    """ 
    Contains Expressions and ExprType.
    An ExprType will be expanded to the dependent Expressions in the moment when it will processed 
    (not when it will appended to the list).
    This can be accelerate:
    - all Expressions that are processed from the moment the ExprType was changed to the 
      moment, when the ExprTye will expanded, can be substract from the expanded list, cause
      they already processed.
    - it is not easy to determine all expressions in the current todo list, cause it contains
      types which should expanded lazy.
    """

    def __init__(self):
        self._deque = deque()
        self._set = set()
        
    def __iter__(self):
        while len(self._deque) > 0:
            item = self._deque.popleft()
            self._set.remove(item)
            if isinstance(item, Expression):
                expr = item
                yield expr
            elif isinstance(item, ExprType):
                expr_type = item
                for expr in expr_type.iter_dependant_expressions():
                    yield expr

    def append(self, expr: Union[Expression, ExprType]):
        if expr not in self._set:
            self._deque.append(expr)
            self._set.add(expr)
            
    def extend(self, expr_iterable: Iterable[Union[Expression, ExprType]]):
        for expr in expr_iterable:
            self.append(expr)
            



# class TodoItem:

    # pass
    
    
# class ExprTodoItem(TodoItem):

    # def __init__(self, expr: Expression):
        # self._expr = expr
        
        
# class TypeTodoItem(TodoItem):

    # def __init__(self, expr_type: ExprType




#   !! This file is experimental !!


import ast

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




class Expression:

    def __init__(self, ast_node: ast.AST):
        self._ast_node = ast_node
        self._parents = []  # dependent
        self._specified = False
        
    @property
    def ast_node(self):
        return self._ast_node
        
    @property
    def specified(self):
        return self._specified
        
    def update(self):
        for parent in self._parents:
            parent.update()
        
        
class NameExpression(Expression):

    def __init__(self, name_node: ast.Name):
        super().__init__(name_node)
    
    
class AttributeExpression(Expression):

    def __init__(self, attribute_node: ast.Atribute):
        super().__init__(attribute_node)
        
    def update(self):
        if self._value.is_evaluated() and is List:
            if self._attr_name == 'append':
                
        if isinstance(self._ast_node.value, ast.Name
        
        
class AssignExpression(Expression):

    def update(self):
        


class CallExpression(Expression):


class TupleExpression(Expression):

    def __init__(self):
        self._items = ExprGroup()
        for x in ...:
            self._items.add(x)

    def update(self):
        if (self._items.are_all_specified()):
            self._specified = True


class IntExpression(Expression):
    
    def update(self):
        pass  # nothing to update - int is constant
        
        
#-------------------------------------------------------------------------


class ExprGroup:  # SubExpr:

    def __init__(self):
        self._specified = set()   # type: Set[Expression]
        self._unspecified = set() # type: Set[Expression]
        
    def add(self, item: Expression):
        self._unspecified.add(item)
        
    def specify(self, item: Expression):
        self._unspecifed.remove(item)
        self._specified.add(item)
        
    def is_specifed(self, item: Expression):
        if item in self._specified:
            return True
        assert item in self._unspecifed
        return False
        
        
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
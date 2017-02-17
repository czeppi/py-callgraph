import ast


class Node:

    def __init__(self, ast_node: ast.AST):
        self._ast_node = ast_node
        self._parent = None

    @property
    def parent(self):
        return self._parent

    @property
    def root(self):
        expr = self
        while expr._parent is not None:
            expr = expr._parent
        return expr

    @property
    def scope(self):
        expr = self
        while expr._parent is not None:
            expr = expr._parent
        return expr._scope

    def iter_self_and_subtrees(self):
        yield self
        for child in self.iter_children():
            yield from child.iter_self_and_subtrees()

    def set_parent_recursive(self):
        for child in self.iter_children():
            child._parent = self
            child.set_parent_recursive()

    def iter_children(self):
        raise Exception('net yet implemented')

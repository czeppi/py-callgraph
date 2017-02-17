import ast
from typing import Optional
from moduleobjects import Scope, ClassDef, FuncDef, ExprType, ClassRef, FuncRef, TList, TMapping


class AnnotationAnalyzer:

    def __init__(self, anno_node: ast.AST, anno_scope: Scope):
        self._anno_node = anno_node
        self._anno_scope = anno_scope

    def evaluate_type(self) -> Optional[ExprType]:
        anno_node = self._anno_node
        if isinstance(anno_node, ast.Name):
            return self._evaluate_scope_type(anno_node.id)
        elif isinstance(anno_node, ast.Str):
            return self._evaluate_scope_type(anno_node.s)
        elif isinstance(anno_node, ast.Subscript):
            if anno_node.value.id == 'List':
                return self._evaluate_list()
            elif anno_node.value.id == 'Mapping':
                return self._evaluate_mapping()

    def _evaluate_scope_type(self, symb_name: str) -> Optional[ExprType]:
        symbol = self._anno_scope.find_symbol_by_name(symb_name)
        if isinstance(symbol, ClassDef):
            return ClassRef(symbol)
        elif isinstance(symbol, FuncDef):
            return FuncRef(symbol)

    def _evaluate_list(self) -> Optional[ExprType]:
        anno_node = self._anno_node
        item_anno_node = anno_node.slice.value
        item_type = AnnotationAnalyzer(item_anno_node, self._anno_scope).evaluate_type()
        if item_type is not None:
            return TList(item_type)

    def _evaluate_mapping(self) -> Optional[ExprType]:
        anno_node = self._anno_node
        slice_ = anno_node.slice.value
        if isinstance(slice_, ast.Tuple):
            key_anno_node = slice_.elts[0]
            key_type = None
            if key_anno_node is not None:
                key_type = AnnotationAnalyzer(key_anno_node, self._anno_scope).evaluate_type()
            value_anno_node = slice_.elts[1]
            value_type = None
            if value_anno_node is not None:
                value_type = AnnotationAnalyzer(value_anno_node, self._anno_scope).evaluate_type()
            if value_type is not None:
                return TMapping(key_type, value_type)


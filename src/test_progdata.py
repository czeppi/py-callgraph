import unittest
import ast
from moduleobjects import SymbolPath, Scope


class TestSymbolPath(unittest.TestCase):

    def test_fullpath(self):
        sym_path = SymbolPath('a.b.c'.split('.'))
        self.assertEqual(sym_path.fullname, 'a.b.c')

    def test_add(self):
        sym_path1 = SymbolPath('a.b'.split('.'))
        sym_path2 = SymbolPath('c.d'.split('.'))
        sym_path3 = sym_path1 + sym_path2
        self.assertEqual(sym_path3.fullname, 'a.b.c.d')

    def test_iadd(self):
        sym_path1 = SymbolPath('a.b'.split('.'))
        sym_path1 += 'c'
        self.assertEqual(sym_path1.fullname, 'a.b.c')


class TestScope(unittest.TestCase):

    def test_find_symbol_by_path(self):
        root = Scope('', parent=None)
        module = self._add_sub_scope(root, 'main')
        class_a = self._add_sub_scope(module, 'A')
        method_f = self._add_sub_scope(class_a, 'f')
        class_b = self._add_sub_scope(module, 'B')
        method_g = self._add_sub_scope(class_b, 'g')

        self._assertFindSymbol(module, 'A')
        self._assertFindSymbol(class_a, 'B')
        self._assertFindSymbol(method_f, 'B')
        self._assertDontFindSymbol(method_f, 'g')

    def _add_sub_scope(self, scope, sub_scope_name):
        new_sub_scope = Scope(sub_scope_name, parent=scope)
        scope.add_child_scope(new_sub_scope)
        return new_sub_scope

    def _assertFindSymbol(self, scope, name):
        find_scope = scope.find_symbol_by_name(name)
        self.assertEqual(find_scope.name, name)

    def _assertDontFindSymbol(self, scope, name):
        find_scope = scope.find_symbol_by_name(name)
        self.assertIsNone(find_scope)


if __name__ == '__main__':
    unittest.main()

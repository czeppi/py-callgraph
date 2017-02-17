import unittest
from typing import Mapping

from proglib import Program
from filesystem import VirtualDir, VirtualFile
from moduleobjects import CallGraph


class TestParseDefinitions(unittest.TestCase):

    def test_empty_class_def(self):
        prg = _create_program({
            'main': """
                class A:
                    pass
            """})
        class_a = prg.main_module.find_class_def('A')
        self.assertIsNotNone(class_a)
        self.assertEqual(class_a.lineno, 1)

    def test_empty_function_def(self):
        prg = _create_program({
            'main': """
                def f():
                    pass
            """})
        f = prg.main_module.find_function_def('f')
        self.assertIsNotNone(f)

    def test_method_def(self):
        prg = _create_program({
            'main': """
                class A:
                    def f():
                        pass
            """})
        class_a = prg.main_module.find_class_def('A')
        f = class_a.find_function_def('f')
        self.assertIsNotNone(f)

    def test_nested_class(self):
        prg = _create_program({
            'main': """
                class A:
                    class B:
                        pass
            """})
        class_a = prg.main_module.find_class_def('A')
        class_b = class_a.find_class_def('B')
        self.assertIsNotNone(class_b)

    def test_nested_function(self):
        prg = _create_program({
            'main': """
                def f():
                    def g():
                        pass
            """})
        f = prg.main_module.find_function_def('f')
        g = f.find_function_def('g')
        self.assertIsNotNone(g)


class TestImport(unittest.TestCase):

    def test_import_one_module(self):
        prg = _create_program({
            'main': """
                import mod2
                """,
            'mod2': """
                class A:
                    pass
                """,
        })
        mod2 = prg.main_module.find_local_symbol_by_name('mod2')
        self.assertIsNotNone(mod2)

    def test_import_two_modules(self):
        prg = _create_program({
            'main': """
                import mod1, mod2
                """,
            'mod2': """
                class A:
                    pass
                """,
        })
        mod2 = prg.main_module.find_local_symbol_by_name('mod2')
        mod1 = prg.main_module.find_local_symbol_by_name('mod1')
        self.assertIsNone(mod1)
        self.assertIsNotNone(mod2)

    def test_import_nested_module(self):
        prg = _create_program({
            'main': """
                import pck1.mod2
                """,
            'pck1.__init__': """
                """,
            'pck1.mod2': """
                class A:
                    pass
                """,
        })
        pck1 = prg.main_module.find_local_symbol_by_name('pck1')
        self.assertIsNotNone(pck1)

        pck1_mod2 = prg.main_module.find_local_symbol_by_name('pck1.mod2')
        self.assertIsNone(pck1_mod2)

        pck1_mod2 = prg.main_module.find_local_symbol_by_fullname('pck1.mod2')
        self.assertIsNotNone(pck1_mod2)

    def test_import_nested_as(self):
        prg = _create_program({
            'main': """
                import pck1.mod2 as m1
                """,
            'pck1.__init__': """
                """,
            'pck1.mod2': """
                class A:
                    pass
                """,
        })
        pck1 = prg.main_module.find_local_symbol_by_name('pck1')
        self.assertIsNone(pck1)

        pck1_mod2 = prg.main_module.find_local_symbol_by_fullname('pck1.mod2')
        self.assertIsNone(pck1_mod2)

        mod2_by_pck1 = prg.find_module('pck1').find_local_symbol_by_name('mod2')
        self.assertIsNotNone(mod2_by_pck1)

        m1 = prg.main_module.find_local_symbol_by_name('m1')
        self.assertIsNotNone(m1)

    def test_from_module_import_class(self):
        prg = _create_program({
            'main': """
                from mod2 import A
                """,
            'mod2': """
                class A:
                    pass
                """,
        })
        mod2 = prg.main_module.find_local_symbol_by_name('mod2')
        self.assertIsNone(mod2)

        class_a = prg.main_module.find_local_symbol_by_name('A')
        self.assertIsNotNone(class_a)

    def test_from_package_import_module(self):
        prg = _create_program({
            'main': """
                from pck1 import mod2
                """,
            'pck1.__init__': """
                """,
            'pck1.mod2': """
                class A:
                    pass
                """,
        })
        pck1 = prg.main_module.find_local_symbol_by_name('pck1')
        self.assertIsNone(pck1)

        mod2 = prg.main_module.find_local_symbol_by_name('mod2')
        self.assertIsNotNone(mod2)


class TestSymbolTables(unittest.TestCase):

    def test_func_parameter(self):
        prg = _create_program({
            'main': """
                class A:
                    pass

                def f(a: A) -> None:
                    pass
            """})
        f = prg.main_module.find_function_def('f')
        a = f.find_symbol_by_name('a')
        self.assertIsNotNone(a)
#        self.assertEqual(str(a.type_expr) == 'main.A')


class TestCallGraph(unittest.TestCase):

    def test_call_func(self):
        call_graph = _create_call_graph("""
            def f():
                pass

            def g():
                f()
        """)
        self.assertTrue(call_graph.contains('main.g -> main.f'))

    def test_constructor(self):
        call_graph = _create_call_graph("""
            class A:
                pass

            def f():
                a = A()
        """)
        self.assertTrue(call_graph.contains('main.f -> main.A'))

    def test_call_method(self):
        call_graph = _create_call_graph("""
            class A:
                def f():
                    pass

            def g():
                a: A = A()
                a.f()

            def h():
                b: 'A' = A()
                b.f()
        """)
        self.assertTrue(call_graph.contains('main.g -> main.A.f'))
        self.assertTrue(call_graph.contains('main.h -> main.A.f'))

    def test_call_method_with_self(self):
        call_graph = _create_call_graph("""
            class A:
                def f(self):
                    self.g()

                def g(self):
                    pass
            """)
        self.assertTrue(call_graph.contains('main.A.f -> main.A.g'))

    def test_late_defined_method_call(self):
        call_graph = _create_call_graph("""
            def f(a: 'A'):
                a.f()

            class A:
                def f():
                    pass
        """)
        self.assertTrue(call_graph.contains('main.f -> main.A.f'))

    def test_ann_assign_with_self(self):
        call_graph = _create_call_graph("""
            class A:
                def f():
                    pass

            class B:
                def __init__(self):
                    self.x: A = A()

                def g(self):
                    self.x.f()
            """)
        self.assertTrue(call_graph.contains('main.B.g -> main.A.f'))

    def test_list_of_classes(self):
        call_graph = _create_call_graph("""
            class A:
                def f():
                    pass

            def g():
                a: List[A] = []
                a[0].f()

            def h():
                b: List['A'] = []
                b[0].f()
        """)
        self.assertTrue(call_graph.contains('main.g -> main.A.f'))
        self.assertTrue(call_graph.contains('main.h -> main.A.f'))

    def test_map_of_classes(self):
        call_graph = _create_call_graph("""
            class A:
                def f():
                    pass

            def g():
                a: Mapping[str, A] = {}
                a['x'].f()
        """)
        self.assertTrue(call_graph.contains('main.g -> main.A.f'))

    def test_map_of_list_of_classes(self):
        call_graph = _create_call_graph("""
            class A:
                def f():
                    pass

            def g():
                a: Mapping[str, List[A]] = {}
                a['x'][0].f()
        """)
        self.assertTrue(call_graph.contains('main.g -> main.A.f'))

    def test_map_of_list_of_classes(self):
        call_graph = _create_call_graph("""
            class A:
                def f():
                    pass

            class B:
                def g() -> A:
                    return A()

            def h():
                b: B = B()
                b.g().f()
        """)
        self.assertTrue(call_graph.contains('main.h -> main.A.f'))
        self.assertTrue(call_graph.contains('main.h -> main.B.g'))

    def test_call_method_of_func_param(self):
        call_graph = _create_call_graph("""
            class A:
                def f():
                    pass

            def g(a: A):
                a.f()
        """)
        self.assertTrue(call_graph.contains('main.g -> main.A.f'))

    def test_call_method_of_func_return(self):
        call_graph = _create_call_graph("""
            class A:
                def f():
                    pass

            def g() -> A:
                return A()

            def h():
                g().f()
        """)
        self.assertTrue(call_graph.contains('main.h -> main.g'))
        self.assertTrue(call_graph.contains('main.h -> main.A.f'))

    def test_derived_class_call(self):
        call_graph = _create_call_graph("""
            class A:
                def f():
                    pass

            class B(A):
                def f():
                    pass

            def g(a: A):
                a.f()

            def h(b: B):
                b.f()
        """)
        self.assertTrue(call_graph.contains('main.g -> main.A.f'))
        self.assertTrue(call_graph.contains('main.g -> main.B.f'))
        self.assertTrue(call_graph.contains('main.h -> main.B.f'))
        self.assertFalse(call_graph.contains('main.h -> main.A.f'))

    def test_long_derived_class_call(self):
        call_graph = _create_call_graph("""
            class A:
                def f():
                    pass

            class B(A):
                def f():
                    pass

            class C:
                def g() -> A:
                    return A()

            def h(c: C):
                c.g().f()
        """)
        self.assertTrue(call_graph.contains('main.h -> main.A.f'))
        self.assertTrue(call_graph.contains('main.h -> main.B.f'))

    def test_local_var_overwrite_global(self):
        call_graph = _create_call_graph("""
            class A:
                def f():
                    pass

            x: A = A()

            def g():
                x = B()
                x.f()
        """)
        self.assertFalse(call_graph.contains('main.g -> main.A.f'))

    def test_iter(self):
        call_graph = _create_call_graph("""
            class A:
                def f():
                    pass

            def g(a_list: List[A]):
                for a in a_list:
                    a.f()
        """)
        self.assertTrue(call_graph.contains('main.g -> main.A.f'))

    # def test_iter(self):
    #     call_graph = _create_call_graph("""
    #         class A:
    #             def f():
    #                 pass
    #
    #         def g(a_list: List[A]):
    #             return [a.f() for a in a_list]
    #     """)
    #     self.assertTrue(call_graph.contains('main.g -> main.A.f'))

    # def test_type_hint_in_comment(self):
    #     call_graph = _create_call_graph("""
    #         class A:
    #             def f():
    #                 pass
    #
    #         def g():
    #             a = A()  # type: A
    #             a.f()
    #     """)
    #     self.assertTrue(call_graph.contains('main.g -> main.A.f'))


def _create_call_graph(raw_source_code: str) -> CallGraph:
    prg = _create_program({'main': raw_source_code})
    return prg.main_module.call_graph


def _create_program(module_fullname2raw_source_code_map: Mapping[str, str]) -> Program:
    root_dir = VirtualDir(name='', parent_dir=None)
    main_file = None
    for module_fullname, raw_source_code in module_fullname2raw_source_code_map.items():
        dir_fullname, module_name = _split_fullname(module_fullname)
        cur_dir = _create_dir(dir_fullname, root_dir)
        source_code = _TestSourceCodeAdapter(raw_source_code).adapt()
        new_file = cur_dir.add_file(module_name + '.py', file_buf=source_code)
        if module_name == 'main':
            main_file = new_file
    program = Program(main_file)
    program.build()
    return program


def _split_fullname(fullname: str):
    parts = fullname.split('.')
    return '.'.join(parts[:-1]), parts[-1]


def _create_dir(fullname, root_dir):
    if fullname == '':
        return root_dir
    name_parts = fullname.split('.')
    cur_dir = root_dir
    for name_part in name_parts:
        subdir = cur_dir.get_subdir(name_part)
        if subdir is None:
            subdir = cur_dir.add_subdir(name_part)
        cur_dir = subdir
    return cur_dir


class _TestSourceCodeAdapter:

    def __init__(self, raw_str):
        self._raw_str = raw_str

    def adapt(self):
        lines = self._raw_str.split('\n')
        self._remove_first_line_if_empty(lines)
        if len(lines) == 0:
            return ''

        indent_len = self._calc_indent_len(lines[0])
        new_lines = self._reverse_indent(lines, indent_len)
        return '\n'.join(new_lines)

    def _remove_first_line_if_empty(self, lines):
        if len(lines) > 0:
            if lines[0].strip() == '':
                del lines[0]

    def _calc_indent_len(self, first_line):
        indent_len = len(first_line) - len(first_line.lstrip())
        return indent_len

    def _reverse_indent(self, lines, indent_len):
        return [x[indent_len:] for x in lines]



if __name__ == '__main__':
    unittest.main()

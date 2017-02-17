import unittest
import re
import ast
from module import SymbolPath, Scope
from program import Program
from exprtypes import ExprType, NumType, ListType, UnionType, StrType, ClassInstanceType
from exprtreebuilder import create_rvalue_expr, create_lvalue_expr, ModuleBuilder
from typeidentification import TodoList, TypeIdentification
from expressions import StrExpression, NumExpression, RNameExpression
from filesystem import VirtualDir, VirtualFile


class TestBase(unittest.TestCase):

    def _create_module(self, raw_code: str):
        code = SourceCode(raw_code).text
        self._program = _create_program(code)
        self._module = self._program.main_module

        module_list = list(self._program.iter_modules())
        type_identification = TypeIdentification()
        type_identification.identify_by_module_list(module_list)

    def _find_symbol(self, symbol_fullname):
        return self._program.main_module.find_symbol_by_fullname(symbol_fullname)

    def _create_rvalue_expr(self, raw_str: str):
        self._source_code = SourceCode(raw_str)
        module_node = ast.parse(self._source_code.text)
        rvalue_expr = create_rvalue_expr(module_node.body[0])
        return rvalue_expr

    def _find_expr(self, tok_name):
        pos = self._source_code.find_tok_pos(tok_name)
        if pos is None:
            return None
            

class TestRValues(unittest.TestCase):

    def test_num(self):
        self._check_type("42", NumType())

    def test_str(self):
        self._check_type("'42'", StrType())

    def test_list(self):
        self._check_type("[42, 43]", ListType(NumType()))

    #def test_list(self):
    #    self._check_type("[42, '42']", ListType(UnionType([NumType(), StrType()])))

    def _check_type(self, code: str, target_type: ExprType):
        module_node = ast.parse(code)
        expr_node = module_node.body[0]
        rvalue_expr = create_rvalue_expr(expr_node)
        rvalue_expr.set_parent_recursive()

        todo_list = TodoList()
        for e in rvalue_expr.iter_self_and_subtrees():
            if isinstance(e, NumExpression) or isinstance(e, StrExpression) or isinstance(e, RNameExpression):
                todo_list.append(e)

        type_identification = TypeIdentification()
        type_identification.identify_by_todo_list(todo_list)

        self.assertEqual(rvalue_expr.type_, target_type)


class TestGeneralTypeIdentifying(TestBase):

    def test_instance(self):
        self._create_module("""
            class A: pass
            a = A()
        """)
        class_a = self._find_symbol('A')
        var_a = self._find_symbol('a')
        self.assertEqual(var_a.type_, ClassInstanceType(class_a))
        #self._check_type('$a', ClassInstanceType('main.A'))

    # def test_return(self):
    #     self._create_module("""
    #         def f(): return 42
    #     """)
    #     f = self._find_symbol('f')
    #     self.assertEqual(f.return_type, NumType())
    #
    # def test_tuple_assign(self):
    #     self._create_module("""
    #         [a, b] = 4, '5'
    #     """)
    #     a = self._find_symbol('a')
    #     b = self._find_symbol('b')
    #     self.assertEqual(a.type_, NumType())
    #     self.assertEqual(b.type_, StrType())


def _create_program(source_code: str) -> Program:
    root_dir = VirtualDir(name='', parent_dir=None)
    main_file = root_dir.add_file('main.py', file_buf=source_code)
    program = Program(main_file)
    program.build()
    return program


class SourceCode:

    def __init__(self, raw_str):
        prepared_lines = self._get_prepared_lines(raw_str)
        
        self._token = {}  # type: Dict[str, Tuple[int, int]]
        for i, line in enumerate(prepared_lines):
            self._find_marked_tokens_in_line(line, lineno=i+1)
            
        self._lines = [''.join(line.split('$')) for line in prepared_lines]
        self._text = '\n'.join(self._lines)
        
    def _get_prepared_lines(self, raw_str):
        raw_lines = raw_str.split('\n')
        
        # remove empty lines at begin
        while len(raw_lines) > 0 and raw_lines[0].strip() == '':
            del raw_lines[0]
        if len(raw_lines) == 0:
            return ''
            
        # re-identing
        indent_len = len(raw_lines[0]) - len(raw_lines[0].lstrip())
        new_lines = [raw_line[indent_len:] for raw_line in raw_lines]
        return new_lines
        
    def _find_marked_tokens_in_line(self, line, lineno):
        rex = re.compile(r"\$([a-zA-Z_]+[a-zA-Z0-9_]*|[0-9]+|[!=]?=|[<>+\-*/%]=?|[({\[])")
        for i, match in enumerate(rex.finditer(line)):
            col_offset = match.start() - i  # subtract i, cause the '$'-characters will remove
            tok_name = match.group(0)
            self._token[tok_name] = (lineno, col_offset)
            
    @property
    def lines(self):
        return self._lines
        
    @property
    def text(self):
        return self._text
        
    def find_token_pos(self, tok_name):
        return self._token.get(tok_name, None)
    
            
            
    
        
if __name__ == '__main__':
    unittest.main()

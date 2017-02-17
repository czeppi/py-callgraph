from typing import Union, Optional
from module import ClassDef, FuncDef, Module, Variable


class ExprType:

    def __init__(self):
        self._are_all_usages_evaluate = False
        self._are_sub_types_ready = False
        self._expr_set = set()  # for update

    def __ne__(self, other):
        return not self == other

    def add_expression(self, expr: 'Expression'):
        self._expr_set.add(expr)

    def iter_expression(self):
        yield from self._expr_set

    def get_call_type(self):
        raise Exception('not yet implemented.')

    def get_subscript_type(self):
        raise Exception('not yet implemented.')

    def get_attribute_type(self, attr_name):
        raise Exception('not yet implemented.')


class ExternType(ExprType):
    """ unspecified external type
    """

    def __eq__(self, other):
        return False  # todo: ok?


class ModuleType(ExprType):

    def __init__(self, module: Module):
        super().__init__()
        self._module = module

    def __eq__(self, other):
        return isinstance(other, ModuleType) and self._module == other._module


class ClassType(ExprType):

    def __init__(self, class_def: ClassDef):
        super().__init__()
        self._class = class_def

    def __eq__(self, other):
        return isinstance(other, ClassType) and self._class == other._class

    def get_attribute_type(self, attr_name):
        return self._class.find_local_symbol_by_name(attr_name)

    def get_call_type(self):
        return ClassInstanceType(self._class)


class ClassInstanceType(ExprType):
     
    def __init__(self, class_def: ClassDef):
        super().__init__()
        self._class = class_def

    def __eq__(self, other):
        return isinstance(other, ClassInstanceType) and self._class == other._class

    def get_attribute_type(self, attr_name):
        return self._class.find_local_symbol_by_name(attr_name)


class FunctionType(ExprType):
     
    def __init__(self, func_def: FuncDef):
        super().__init__()
        self._func_def = func_def

    def __eq__(self, other):
        return isinstance(other, FunctionType) and self._func_def == other._func_def

    def get_call_type(self):
        return self._func_def.return_type

        
class TupleType(ExprType):

    def __init__(self):
        super().__init__()
        self._item_types = []

    def __eq__(self, other):
        return isinstance(other, TupleType) and self._item_types == other._item_types

    def __iter__(self):
        yield from self._item_types

    def __len__(self):
        return len(self._item_types)

    def __getitem__(self, i: int):
        return self._item_types[i]

    def get_subscript_type(self, index=None):
        if index is None:
            return UnionType(self._item_types)
        else:
            return self._item_types[index]
    
    
class ListType(ExprType):

    def __init__(self, item_type: Optional[ExprType] = None):
        super().__init__()
        self._item_type = item_type

    def __eq__(self, other: 'ListType'):
        return isinstance(other, ListType) and self._item_type == other._item_type

    @property
    def item_type(self):
        return self._item_type

    def set_item_type(self, item_type: ExprType):
        self._item_type = item_type
        # todo: set dirty bit or something similar

    def get_subscript_type(self):
        return self._item_type


class DictType(ExprType):

    def __init__(self):
        super().__init__()
        self._key_type = None
        self._value_type = None
        
    def __eq__(self, other: 'DictType'):
        return isinstance(other, DictType) and self._key_type == other._key_type and self._value_type == other._value_type

    @property
    def key_type(self):
        return self._key_type

    @property
    def value_type(self):
        return self._value_type

    def get_subscript_type(self):
        return self._value_type


class UnionType(ExprType):

    def __init__(self):
        super().__init__()
        self._sub_types = set()  # type: Set[ExprType]

    def __eq__(self, other: 'UnionType'):
        return isinstance(other, UnionType) and self._sub_types == other._sub_type


class StrType(ExprType):

    def __init__(self, value=None):
        super().__init__()
        self._value = value
        
    def __eq__(self, other):
        return isinstance(other, StrType) #  and self._value == other._value

    def __hash__(self):
        return hash(StrType)


class NumType(ExprType):

    def __init__(self, value=None):
        super().__init__()
        self._value = value

    def __eq__(self, other):
        return isinstance(other, NumType) #  and self._value == other._value

    def __hash__(self):
        return hash(NumType)

        
# class BuildInSimpleType(ExprType):  # int, float, complex, str
#
#     def __init__(self, build_in_type: Union[int, float, complex, str]):
#         self._build_in_type = build_in_type
#
#     def __eq__(self, other: 'BuildInSimpleType'):
#         self._build_in_type == other._build_in_type


class UnknownExternType(ExprType):

    def __eq__(self, other: 'UnknownExternType'):
        return False


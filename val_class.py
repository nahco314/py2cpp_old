from __future__ import annotations

import ast
import typing
import types

from operator import *
import operator


ast_op = typing.TypeVar("ast_op", bound=ast.AST)


class CppVal:
    def __init__(self, string, val_type):
        self.string, self.type = string, val_type
        self.val_type = None
        if type(val_type) == types.GenericAlias:
            if len(val_type.__args__) > 1:
                raise TypeError
            else:
                self.val_type = val_type.__args__[0]

    def __str__(self):
        return self.string

    @staticmethod
    def ast_tp_func(func):
        func_map = {ast.Add: add, ast.Sub: sub, ast.Mult: mul, ast.Div: truediv,
                    ast.FloorDiv: floordiv, ast.Mod: mod, ast.Pow: pow,
                    ast.LShift: lshift, ast.RShift: rshift, ast.BitOr: or_,
                    ast.BitXor: xor, ast.BitAnd: and_, ast.MatMult: matmul}

        return func_map[func]

    def sample(self, obj=None):
        target = self.type
        if obj is not None:
            target = obj
        if type(target) == types.GenericAlias:
            if target.__origin__ == list:
                return [self.sample(self.val_type)]
        sample_map = {int: 1, float: 1.0, complex: 1j, str: "str", bool: True,
                      types.NoneType: None}
        return sample_map[target]

    def op_type(self, other: CppVal, op: ast_op) -> type:
        op = CppVal.ast_tp_func(type(op))
        return type(op(self.sample(), other.sample()))

    def brackets(self, type1="(", type2=")"):
        self.string = f"{type1}{self.string}{type2}"

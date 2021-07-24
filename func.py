import ast
from operator import *

import typing
import types

from val_class import CppVal


ast_obj = typing.TypeVar("ast_obj", bound=ast.AST)


def priority(op: ast_obj) -> int:
    if type(op) in (ast.UnaryOp, ast.BinOp):
        op = type(op.op)

    else:
        op = type(op)

    if op == ast.Lambda:
        return 0

    elif op == ast.IfExp:
        return 1

    elif op == ast.Or:
        return 2

    elif op == ast.And:
        return 3

    elif op == ast.Not:
        return 4

    elif issubclass(op, ast.cmpop):
        return 5

    elif op == ast.BitOr:
        return 6

    elif op == ast.BitXor:
        return 7

    elif op == ast.BitAnd:
        return 8

    elif op in (ast.LShift, ast.RShift):
        return 9

    elif op in (ast.Add, ast.Sub):
        return 10

    elif op in (ast.Mult, ast.MatMult, ast.Div, ast.FloorDiv, ast.Mod):
        return 11

    elif issubclass(op, ast.unaryop):
        return 12

    else:
        return 13


def to_func(func: ast_obj) -> str:
    func_map = {ast.Is: "py_is", ast.IsNot: "py_is_not", ast.In: "py_in",
                ast.NotIn: "py_not_in", ast.Pow: "pow", ast.Mod: "py_mod"}
    return func_map[func]


def ast_to_op(op_ast: ast_obj) -> types.FunctionType:
    # ToDo: bool演算
    func_map = {ast.UAdd: pos, ast.USub: neg, ast.Not: not_, ast.Invert: invert,
                ast.Add: add, ast.Sub: sub, ast.Mult: mul, ast.Div: truediv,
                ast.FloorDiv: floordiv, ast.Mod: mod, ast.Pow: pow, ast.LShift: lshift,
                ast.RShift: rshift, ast.BitOr: or_, ast.BitXor: xor, ast.BitAnd: and_,
                ast.MatMult: matmul, ast.And: 0}

import ast
from operator import *

import typing
import types

from func import priority, to_func
from val_class import CppVal
from cpp_types import to_int_cast, cpp_format, cpp_type


def Constant(term: ast.Constant) -> CppVal:
    term = term.value
    if str == type(term):
        return CppVal(f'"{term}"s', str)
    else:
        return CppVal(f"{term}", type(term))


def Name(term: ast.Name, var_map) -> CppVal:
    return CppVal(f"{term.id}", var_map[term.id])


def Compare(formula: ast.Compare) -> CppVal:
    left, ops, comparators = formula.left, formula.ops, formula.comparators
    op_map = {ast.Eq: "==", ast.NotEq: "!=", ast.Lt: "<", ast.LtE: "<=", ast.Gt: ">",
              ast.GtE: ">="}
    result = CppVal(str(cpp_eval_sub(left)), bool)
    if priority(left) < priority(ops[0]):
        result.brackets()
    # 処理を簡潔にするためにcomparatorsの最後にleftをつける
    comparators += [left]

    # すべての要素について処理する
    for i in range(len(ops)):
        value_eval = cpp_eval_sub(comparators[i])
        # 項の優先順位がこの演算より低ければ()をつける
        if priority(comparators[i]) < priority(ops[i]):
            value_eval.brackets()

        # 結果に足す
        if type(ops[i]) in op_map:
            result.string += f" {op_map[type(ops[i])]} {value_eval}"

        # is、is not、in、not inはC++にないので別処理
        else:
            result.string += " and "

            # 最初の項なら、resultを初期化する
            if i == 0:
                result = CppVal("", bool)

            # 関数をつける
            left, right = cpp_eval_sub(comparators[i - 1]), cpp_eval_sub(comparators[i])
            result.string += f"{to_func(type(ops[i]))}({left}, {right})"

            # 最後じゃなく、かつ次の演算が特殊ケースじゃないならandをつける
            if i != len(ops) - 1 and type(ops[i + 1]) in op_map:
                result.string += f" and {value_eval}"

    return result


def Attribute(attr: ast.Attribute) -> CppVal:
    value, attr, ctx = cpp_eval_sub(attr.value), attr.attr, attr.ctx

    # 特殊なケースをはじく
    # 今のところ、特殊なケースを知らない

    return CppVal(f"{value}.{attr}", var_map[f"{value.type.__name__}.{attr}"])


def UnaryOp(term: ast.UnaryOp) -> CppVal:
    op_map = {ast.UAdd: "+", ast.USub: "-", ast.Not: "not ", ast.Invert: "~"}
    op, operand = term.op, term.operand
    operand_eval = cpp_eval_sub(operand)

    if priority(operand) < 12:
        operand_eval.brackets()

    return CppVal(f"{op_map[type(op)]}{operand_eval}",
                  operand_eval.type if op != ast.Not else bool)


def BinOp(formula: ast.BinOp) -> CppVal:
    # ToDO: or演算子を、typeやdictに使う時の場合分け
    op, left, right = formula.op, formula.left, formula.right
    left_eval, right_eval = cpp_eval_sub(left), cpp_eval_sub(right)
    left_priority = priority(left)
    right_priority = priority(right)
    op_map = {ast.Add: "+",
              ast.Sub: "-",
              ast.Mult: "*",
              ast.FloorDiv: "/",
              ast.LShift: "<<",
              ast.RShift: ">>",
              ast.BitOr: "|",
              ast.BitXor: "^",
              ast.BitAnd: "&"
              }
    not_associativity = {ast.Sub, ast.Div, ast.Mod, ast.LShift, ast.RShift}
    val_type = left_eval.op_type(right_eval, op)

    # 割り算は処理がめんどくさいのではじく
    if type(op) == ast.Div:
        if left_eval.type != float:
            if right_eval.type != float:
                left_eval.brackets("double(", ")")
        elif left_priority < priority(op):
            left_eval.brackets()
        if right_priority < priority(op) \
                or (right_priority == priority(op) and type(op) in not_associativity):
            right_eval.brackets()

        return CppVal(f"{left_eval} / {right_eval}", float)

    # ToDO: str * intはC++にないのではじく

    # 関数で処理する演算をはじく
    if type(op) not in op_map:
        return CppVal(f"{to_func(type(op))}({left_eval}, {right_eval})", val_type)

    # その他
    # 左辺の優先順位がこの演算より低ければ()をつける
    if left_priority < priority(op):
        left_eval.brackets()

    # 右辺の優先順位がこの演算より低いか、同じで結合律を満たさないなら()を付ける
    if right_priority < priority(op) \
            or (right_priority == priority(op) and type(op) in not_associativity):
        right_eval.brackets()

    result = CppVal(f"{left_eval} {op_map[type(op)]} {right_eval}", val_type)

    # 切り捨て除算なら切り捨てる
    if type(op) == ast.FloorDiv:
        if not left_eval.type == right_eval.type == int:
            result.brackets("py_round(", ")")

    return result


def BoolOp(formula: ast.BoolOp) -> CppVal:
    op, values = formula.op, formula.values
    op_map = {ast.Or: "or", ast.And: "and"}
    result = CppVal("", bool)

    # すべての要素に対して処理する
    for i in range(len(values)):
        value = values[i]
        value_eval = cpp_eval_sub(value)

        # 項の優先順位がこの演算より低ければ()をつける
        if priority(value) < priority(op):
            value_eval.brackets()
        result.string += f"{value_eval}"

        # 最後の要素じゃなければ、演算子をつける
        if i != len(values) - 1:
            result.string += f" {op_map[type(op)]} "

    return result


def IfExp(exp: ast.IfExp) -> CppVal:
    test, body, orelse = exp.test, exp.body, exp.orelse
    test_eval, body_eval, orelse_eval = cpp_eval_sub(test), cpp_eval_sub(body), \
                                        cpp_eval_sub(orelse)
    # それぞれの要素について、優先順位が三項演算子以下か確認し、そうなら()をつける
    # 三項演算子の優先順位は2
    if priority(test) <= 2:
        test_eval.brackets()
    if priority(body) <= 2:
        body_eval.brackets()
    if priority(orelse) <= 2:
        orelse_eval.brackets()

    return CppVal(f"{test_eval} ? {body_eval} : {orelse_eval}", body_eval.type)


def NamedExpr(exp: ast.NamedExpr) -> CppVal:
    target, value = cpp_eval_sub(exp.target), cpp_eval_sub(exp.value)
    return CppVal(f"({target}={value})", value.type)


def List(value: ast.List) -> CppVal:
    elts = value.elts
    list_type = cpp_eval_sub(elts[0]).type
    result = CppVal("{", list[list_type])
    for i in range(len(elts)):
        elt_eval = cpp_eval_sub(elts[i])
        if elt_eval.type != list_type:
            raise TypeError("複数の型をリストに入れるな")
        else:
            result.string += elt_eval.string

        if i != len(elts) - 1:
            result.string += ", "

    result.string += "}"
    return result


def Call(call_func: ast.Call) -> CppVal:
    # ToDo: キーワード周りの実装と組み込み関数の場合分け
    func_type = type(call_func.func)
    func, args, keywords = call_func.func, call_func.args, call_func.keywords

    # メソッドの場合
    if func_type == ast.Attribute:
        value = cpp_eval_sub(func.value)
        attr = func.attr
        func = f"{cpp_eval_sub(call_func.func.value).type.__name__}.{func.attr}"

    else:
        func = func.id

    # print(a, b) -> printf("%d %d", a, b)
    if func == "print":
        result = 'printf("'
        result_vars = ""
        keys = {"sep": " ", "end": "\\n"}
        for key in keywords:
            keys[key.arg] = key.value

        for i in range(len(args)):
            arg = args[i]
            arg_eval = cpp_eval_sub(arg)

            # 定数ならそのまま出力
            # ToDO: 変数がからまないなら定数として評価するようにする
            if type(arg) == ast.Constant:
                result += str(arg.value)

            else:
                # ToDO: リストを出力するときの処理
                result += cpp_format(arg_eval.type)
                result_vars += f", {arg_eval}"

            if i != len(args) - 1:
                # ToDO: 変数がからまないなら定数として評価するようにする
                if type(keys["sep"]) == str:
                    result += keys["sep"]
                else:
                    result += "%s"
                    result_vars += f', ' \
                                   f'{cpp_eval(keys["sep"], var_map, func_map, option)}'

        # endをつける
        if type(keys["end"]) == str:
            result += keys["end"]
        else:
            result += "%s"
            result_vars += \
                f', {cpp_eval(keys["end"], var_map, func_map)}'
        result += f'"{result_vars})'
        result = CppVal(result, types.NoneType)

    # list(map(int, input().split())) -> py_int_split(py_input())
    elif ast.dump(call_func) == "Call(func=Name(id='list', ctx=Load()), " \
                                "args=[Call(func=Name(id='map', ctx=Load()), " \
                                "args=[Name(id='int', ctx=Load()), " \
                                "Call(func=Attribute(value=Call(func=Name(id='input', " \
                                "ctx=Load()), args=[], keywords=[]), attr='split', " \
                                "ctx=Load()), args=[], keywords=[])], keywords=[])], " \
                                "keywords=[])":
        result = CppVal("py_int_split(py_input())", list[int])

    # その他
    else:
        # 扱いが面倒な組み込み関数とかをはじく
        # minとmax
        if func == "min" or func == "max":

            # イテレータに対するmin/maxの場合
            if len(args) == 1:
                iter_eval = cpp_eval_sub(args[0])
                iter_type = iter_eval.val_type
                result = CppVal(f"{func}({iter_eval}", iter_type)

            # そうじゃない場合
            else:
                a, b = args
                a, b = cpp_eval_sub(a), cpp_eval_sub(b)

                # どちらかがfloatならどちらもfloatにしてfloatを返す
                if a.type == float or b.type == float:
                    if a.type != float:
                        a.string = f"double({a})"
                    if b.type != float:
                        b.string = f"double({b})"
                    result = CppVal(f"{func}({a}, {b}", float)

                else:
                    result = CppVal(f"{func}({a}, {b}", int)

            # keyが指定されてるなら、引数を追加
            if len(keywords) == 1:
                key = keywords[0].value

                # 関数なら
                if type(key) == ast.Name:
                    result.string += f", {key.id}"
                # ラムダなら
                elif type(key) == ast.Lambda:
                    result.string += f", {cpp_eval_sub(key)}"

            result.string += ")"

        # abs
        elif func == "abs":
            # 引数の型を返す
            arg = cpp_eval_sub(args[0])
            result = CppVal(f"abs({arg})", arg.type)

        # list
        elif func == "list":
            # 引数のval_typeを返す
            arg = cpp_eval_sub(args[0])
            if arg.type.__origin__ == list:
                result = arg
            else:
                result = CppVal(f"to_vector({arg})", list[arg.val_type])

        # map
        elif func == "map":
            # ToDO: 関数が定数じゃないけど戻り値の型が一意に定まるみたいなケース...
            if type(args[0]) != ast.Name:
                raise TypeError
            map_func, map_iter = args[0].id, cpp_eval_sub(args[1])

            # 関数の種類で、さらに場合分け(きつ)
            # int
            if map_func == "int":
                result = CppVal(f"transform<{cpp_type(map_iter.type)}>"
                                f"({map_iter}, {to_int_cast(map_iter.val_type)})",
                                list[int])

            # ToDO: mapの他の関数のパターン
            else:
                result = CppVal(f"transform<{cpp_type(map_iter.type)}>"
                                f"({map_iter}, {to_func(eval(map_func))})",
                                list[map_func[eval(map_func)]])

        else:
            if func_type == ast.Attribute:
                result = CppVal(f"{value}.{attr}(", func_map[func])
            else:
                result = CppVal(f"{func}(", func_map[func])
            for i in range(len(args)):
                arg = cpp_eval_sub(args[i])
                result.string += arg.string
                if i != len(args) - 1:
                    result.string += ", "
            result.string += ")"
    return result


def Subscript(subscript: ast.Subscript) -> CppVal:
    value, s_slice = subscript.value, subscript.slice
    value_eval = cpp_eval_sub(value)
    # 普通の要素指定
    if type(s_slice) != ast.Slice:
        # 定数ならoperator[]を使う
        # ToDo: 定数として評価できるなら定数にする
        if type(s_slice) == ast.Constant and type(s_slice.value) == int:
            # 0以上ならそのまま
            if s_slice.value >= 0:
                return CppVal(f"{value_eval}[{s_slice.value}]", value_eval.val_type)

            # 負ならsizeから引いて指定
            else:
                return CppVal(f"{value_eval}[{value_eval}.size-{-s_slice.value}]",
                              value_eval.val_type)

        # そうじゃないならpy_index関数に渡す
        else:
            idx = cpp_eval_sub(s_slice)
            return CppVal(f"py_index({value_eval}, {idx})", value_eval.val_type)
    else:
        raise ValueError


def cpp_eval_sub(formula) -> CppVal:
    if type(formula) == ast.Constant:
        return Constant(formula)

    elif type(formula) == ast.Name:
        return Name(formula, var_map)

    elif type(formula) == ast.UnaryOp:
        return UnaryOp(formula)

    elif type(formula) == ast.BinOp:
        return BinOp(formula)

    elif type(formula) == ast.BoolOp:
        return BoolOp(formula)

    elif type(formula) == ast.Compare:
        return Compare(formula)

    elif type(formula) == ast.Attribute:
        return Attribute(formula)

    elif type(formula) == ast.IfExp:
        return IfExp(formula)

    elif type(formula) == ast.NamedExpr:
        return NamedExpr(formula)

    elif type(formula) == ast.List:
        return List(formula)

    elif type(formula) == ast.Call:
        return Call(formula)

    elif type(formula) == ast.Subscript:
        return Subscript(formula)


def cpp_eval(formula, var_map_l, func_map_l, option_l) -> CppVal:
    global var_map, func_map, option
    var_map = var_map_l
    func_map = func_map_l
    option = option_l

    return cpp_eval_sub(formula)

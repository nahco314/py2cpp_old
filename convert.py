import ast
import types

from eval import cpp_eval
from func import ast_to_op, to_func
from cpp_types import cpp_type, cpp_format

import typing

# ToDo: 空リストについての型推論
# ToDo: 内包表記
# ToDo: while
# ToDo: dict, set
# ToDo: 前処理(/=)関数の作成
# ToDo: がんばってファイルを分ける

# ToDo: アンパック代入


def convert_sub(code: typing.List, var_map, func_map, option):
    cpp_code = []
    diveq = set()
    # 前処理
    for line in code:
        if type(line) == ast.AugAssign:
            target = line.target.id
            op = line.op
            if type(op) == ast.Div:
                diveq.add(target)

    for line in code:

        result = ""
        semicolon = True

        # ただの式
        if type(line) == ast.Expr:
            result = cpp_eval(line.value, var_map, func_map, option).string

        # 代入
        elif type(line) == ast.Assign:
            targets = line.targets
            value = cpp_eval(line.value, var_map, func_map, option)

            # 入力などの特殊なケースをはじく
            # n = int(input()) -> scanf("%d\n", &n)
            if ast.dump(line.value) == \
                    "Call(func=Name(id='int', ctx=Load()), args=[Call(func=Name(" \
                    "id='input', ctx=Load()), args=[], keywords=[])], keywords=[])":
                # ターゲットが変数で最初の代入なら変数の型を決定
                if type(targets[0]) == ast.Name and targets[0].id not in var_map:
                    if targets[0].id in diveq:
                        var_map[targets[0].id] = float
                    else:
                        var_map[targets[0].id] = int

                f_target_eval = cpp_eval(targets[0], var_map, func_map, option)
                result += f'scanf("{cpp_format(f_target_eval.type)}\\n", ' \
                          f'&{f_target_eval.string})'

                # 代入先が1つじゃないなら
                if len(targets) != 1:
                    result += ";\n"
                    for target in targets[1:]:

                        # ターゲットが変数で最初の代入なら変数の型を決定
                        if target.id not in var_map:
                            if target.id in diveq:
                                var_map[target.id] = float
                            else:
                                var_map[target.id] = int

                        target = cpp_eval(target, var_map, func_map, option)
                        result += f"{target.string} = "
                    result += f_target_eval.string

            # s = input() -> getline(cin, s)
            elif ast.dump(line.value) == \
                    "Call(func=Name(id='input', ctx=Load()), args=[], keywords=[])":
                # ターゲットが変数で最初の代入なら変数の型を決定
                if type(targets[0]) == ast.Name and targets[0].id not in var_map:
                    var_map[targets[0].id] = str

                f_target_eval = cpp_eval(targets[0], var_map, func_map, option)
                result += f'getline(cin, {f_target_eval.string})'

                # 代入先が1つじゃないなら
                if len(targets) != 1:
                    result += ";\n"
                    for target in targets[1:]:

                        # ターゲットが変数で最初の代入なら変数の型を決定
                        if target.id not in var_map:
                            var_map[target.id] = str

                        target = cpp_eval(target, var_map, func_map, option)
                        result += f"{target.string} = "
                    result += f_target_eval.string

            # a, b, c = map(int, input().split()) -> scanf("%d %d %d\n", &a, &b, &c)
            # ToDO: len(targets) >= 2なケースをどうにかする
            elif ast.dump(line.value) == "Call(func=Name(id='map', ctx=Load()), " \
                                         "args=[Name(id='int', ctx=Load()), " \
                                         "Call(func=Attribute(value=Call(" \
                                         "func=Name(id='input', ctx=Load()), args=[], " \
                                         "keywords=[]), attr='split', ctx=Load()), " \
                                         "args=[], keywords=[])], keywords=[])":
                vars = line.targets[0].elts
                result_vars = ""
                result = 'scanf("'
                for i in range(len(vars)):
                    var = vars[i]

                    # ターゲットが変数で最初の代入なら変数の型を決定
                    if var.id not in var_map:
                        if var.id in diveq:
                            var_map[var.id] = float
                        else:
                            var_map[var.id] = int

                    var = cpp_eval(var, var_map, func_map, option)
                    result += cpp_format(var.type)
                    result_vars += f", &{var.string}"

                    if i != len(vars) - 1:
                        result += " "
                    else:
                        result += "\\n"

                result += f'"{result_vars})'

            # a = scanf(n) -> a = fill_vec(n, 0);for(int i=0;i<n;i++) scanf("%d", &a[i])
            elif type(line.value) == ast.Call and line.value.func.id == "scanf":
                n = cpp_eval(line.value.args[0], var_map, func_map, option)
                target = targets[0]

                # ターゲットが変数で最初の代入なら変数の型を決定
                if target.id not in var_map:
                    var_map[target.id] = list[int]

                target = cpp_eval(target, var_map, func_map, option)
                result += f'{target.string} = fill_vec({n}, 0);' \
                          f'for(int _=0;_<{n};_++) ' \
                          f'scanf("{cpp_format(target.val_type)}", &a[_])'

                # ターゲットが複数なら代入を追加する
                if len(targets) > 1:
                    target_0 = target
                    result += ";"

                    for target in targets:

                        # ターゲットが変数で最初の代入なら変数の型を決定
                        if target.id not in var_map:
                            if value.type == int and target.id in diveq:
                                var_map[target.id] = float
                            else:
                                var_map[target.id] = value.type
                        target = cpp_eval(target, var_map, func_map, option)

                        result += f"{target.string} = "

                    result += target_0.string

            else:
                for target in targets:

                    # ターゲットが変数で最初の代入なら変数の型を決定
                    if target.id not in var_map:
                        var_map[target.id] = value.type
                    target = cpp_eval(target, var_map, func_map, option)

                    result += f"{target.string} = "

                result += value.string

        # ------------------

        # if文
        elif type(line) == ast.If:
            semicolon = False
            test = line.test
            if_conv = convert_sub(line.body, var_map, func_map, option)
            result = f"if({cpp_eval(test, var_map, func_map, option).string})"

            # 下につく行が1つならそのままつける
            if len(line.body) == 1:
                result += f" {if_conv}"

            # そうじゃないなら{}で囲って付ける
            else:
                result += "{" + if_conv + "}"

            # elseがあれば
            if line.orelse:
                orelse_conv = convert_sub(line.orelse, var_map, func_map, option)
                result += "\nelse"

                # 下につく行が1つならそのままつける
                if len(line.orelse) == 1:
                    result += f" {orelse_conv}"

                # そうじゃないなら{}で囲って付ける
                else:
                    result += "{" + orelse_conv + "}"

        # ------------------

        # for文
        elif type(line) == ast.For:
            semicolon = False
            try:
                target = line.target.id
            except AttributeError:
                target = cpp_eval(line.target, var_map, func_map, option)
            r_iter = line.iter
            iter_eval = cpp_eval(r_iter, var_map, func_map, option)
            r_type = iter_eval.val_type
            var_map[target] = r_type
            for_conv = convert_sub(line.body, var_map, func_map, option)
            del var_map[target]

            # for i in range(n) -> for(int i=0; i<n; i++)
            if type(r_iter) == ast.Call and r_iter.func.id == "range":
                args = r_iter.args
                start, end, step = 0, 0, 1
                if len(args) == 1:
                    end = cpp_eval(args[0], var_map, func_map, option)
                else:
                    start = cpp_eval(args[0], var_map, func_map, option)
                    end = cpp_eval(args[1], var_map, func_map, option)
                    if len(args) == 3:
                        step = cpp_eval(args[2], var_map, func_map, option)

                # stepが非負の場合
                if step >= 0:
                    result = f"for(int {target}={start}; {target}<{end}; {target}"
                    # +=1は++
                    if step == 1:
                        result += "++"
                    else:
                        result += f"+={step}"
                else:
                    result = f"for(int {target}={start}; {target}>{end}; {target}"
                    # -=1は--
                    if step == -1:
                        result += "--"
                    else:
                        result += f"-={step}"

                result += ")"

            else:
                # ToDo: Autoじゃなくしてもいいかも
                result = f"for(auto {target}:{iter_eval})"

            # 下につく行が1つならそのままつける
            if len(line.body) == 1:
                result += f" {for_conv}"

            # そうじゃないなら{}で囲って付ける
            else:
                result += "{" + for_conv + "}"

        # ------------------
        # 算術代入演算子

        elif type(line) == ast.AugAssign:
            target = cpp_eval(line.target, var_map, func_map, option)
            value = cpp_eval(line.value, var_map, func_map, option)
            op = line.op
            op_map = {ast.Add: "+",
                      ast.Sub: "-",
                      ast.Mult: "*",
                      ast.Div: "/",
                      ast.FloorDiv: "/",
                      ast.LShift: "<<",
                      ast.RShift: ">>",
                      ast.BitOr: "|",
                      ast.BitXor: "^",
                      ast.BitAnd: "&"
                      }

            # a += 1 -> a++
            if type(op) == ast.Add and value.string == "1":
                result = f"{target}++"

            # a -= 1 -> a--
            elif type(op) == ast.Sub and value.string == "1":
                result = f"{target}--"

            # ToDo: list += [a] -> list.push_back(a)

            else:
                # 関数で処理する演算をはじく
                if type(op) not in op_map:
                    result = f"{target} = {to_func(type(op))}({target}, {value})"

                # 切り捨て除算もはじく
                elif type(op) == ast.FloorDiv:
                    result = f"{target} = py_round({target} / {value})"

                else:
                    result = f"{target} {op_map[type(op)]}= {value}"

        if semicolon:
            result += ";"
        cpp_code.append(result)

    return "\n".join(cpp_code)


def convert(code: typing.List, var_map=None, func_map=None, option=None):
    cpp_code = []
    var_decl = []
    if var_map is None:
        var_map = {}
    if func_map is None:
        func_map = {"int": int, "map": list, "input": str, "str.split": list[str],
                    "print": types.NoneType, "range": list[int], "scanf": list[int]}
    if option is None:
        option = {"neg_index": True}

    # bodyの処理をする
    cpp_code.append(convert_sub(code, var_map, func_map, option))

    # 変数の宣言部分を処理する
    for var_id in var_map:
        result = f"{cpp_type(var_map[var_id])} {var_id};"
        var_decl.append(result)

    return "\n".join(var_decl + cpp_code)

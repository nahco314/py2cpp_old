import types


def cpp_format(py_type: type) -> str:
    format_map = {int: "%lld", str: "%s", float: "%lf"}
    return format_map[py_type]


def cpp_type(py_type: type) -> str:
    if type(py_type) == types.GenericAlias:
        args = py_type.__args__
        if len(args) > 1:
            raise TypeError
        else:
            if py_type.__origin__ == list:
                return f"vector<{cpp_type(args[0])}>"
    type_map = {int: "long long", float: "double", str: "string",
                types.FunctionType: "function"}
    return type_map[py_type]


def to_int_cast(cast_type: type) -> str:
    if cast_type == float:
        return "int"
    elif cast_type == str:
        return "stoll"
    else:
        raise TypeError

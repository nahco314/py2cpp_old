from eval import *


code = """
print(1,2,3)
"""
for line in ast.parse(code).body:
    print(cpp_eval_sub(line.value))

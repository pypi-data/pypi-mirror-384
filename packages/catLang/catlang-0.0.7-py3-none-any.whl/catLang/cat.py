import regex

# ----------------- Patterns -----------------
println_pattern = r"\bprintln\((.*?)\)"
block_pattern = r"\{(?:[^{}]|(?R))*\}"

if_pattern = rf"\bif\((.*?)\)\s?({block_pattern})"
elif_pattern = rf"\belif\((.*?)\)\s?({block_pattern})"
else_pattern = rf"\belse\s?({block_pattern})"

for_pattern = rf"\bfor\(\s?(let\s+\w+\s?=\s?\d+),\s?(\w+\s?[<>=!]+\s?\d+),\s?(\w+\+\+)\s?\)\s?({block_pattern})"

let_pattern = r"\blet\s(.*?)\s?=\s?(.*?)"
func_pattern = rf"\bfunc\s(\w+)\((.*?)\)\s?({block_pattern})"
return_pattern = r"\breturn\((.*?)\)"
cls_pattern = fr"\bcls\s(.*?)\s?({block_pattern})"
comment_pattern = r"\/\/\s(.*?)"
# ----------------- Transpiler -----------------
def transpile(code: str) -> str:
    """Convert CatLang code into Python code."""
    code = regex.sub(println_pattern, r"print(\1)", code, flags=regex.DOTALL)

    def indent_block(block):
        lines = block[1:-1].splitlines()
        return "\n".join("    " + line for line in lines)

    def repl_if(match):
        cond = match.group(1).strip()
        block = indent_block(match.group(2))
        return f"if {cond}:\n{block}"

    def repl_elif(match):
        cond = match.group(1).strip()
        block = indent_block(match.group(2))
        return f"elif {cond}:\n{block}"

    def repl_else(match):
        block = indent_block(match.group(1))
        return f"else:\n{block}"

    def repl_for(match):
        init = match.group(1).strip()
        cond = match.group(2).strip()
        var, start = init.replace("let","").split("=")
        var = var.strip()
        start = start.strip()
        end = cond.split("<=")[1].strip()
        block = indent_block(match.group(4))
        return f"for {var} in range({start}, {int(end)+1}):\n{block}"

    def repl_let(match):
        var = match.group(1).strip()
        val = match.group(2).strip()
        return f"{var} = {val}"

    def repl_func(match):
        name = match.group(1).strip()
        func = match.group(2).strip()
        block = indent_block(match.group(3))
        return f"def {name}({func}):\n{block}"

    def repl_cls(match):
        name = match.group(1).strip()
        block = indent_block(match.group(2))
        return f"class {name}:\n{block}"

    def repl_return(match):
        ret = match.group(1).strip()
        return f"return {ret}"

    def repl_comment(match):
        content = match.group(1)
        return f"# {content}"
    
    for _ in range(10):
        code = regex.sub(if_pattern, repl_if, code, flags=regex.DOTALL)
        code = regex.sub(elif_pattern, repl_elif, code, flags=regex.DOTALL)
        code = regex.sub(else_pattern, repl_else, code, flags=regex.DOTALL)
        code = regex.sub(for_pattern, repl_for, code, flags=regex.DOTALL)
        code = regex.sub(let_pattern, repl_let, code, flags=regex.DOTALL)
        code = regex.sub(func_pattern, repl_func, code, flags=regex.DOTALL)
        code = regex.sub(return_pattern, repl_return, code, flags=regex.DOTALL)
        code = regex.sub(cls_pattern, repl_cls, code, flags=regex.DOTALL)
        code = regex.sub(comment_pattern, repl_comment, code, flags=regex.DOTALL)
    
    return code

# ----------------- Runner -----------------

def exc(code: str):
    """Executes a string of CatLang code."""
    py_code = transpile(code)
    builtins = __import__("builtins")
    builtins.println = print  # optional: make println global
    exec(py_code, globals())

def exec_file(filename: str):
    """Executes a CatLang file (.cat)."""
    with open(filename, "r") as f:
        cat_code = f.read()
    # Transpile before running
    py_code = transpile(cat_code)
    builtins = __import__("builtins")
    builtins.println = print
    exec(py_code, globals())
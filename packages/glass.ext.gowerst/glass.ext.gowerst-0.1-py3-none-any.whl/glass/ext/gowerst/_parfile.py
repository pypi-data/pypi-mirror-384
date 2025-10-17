import ast
import importlib


class ParfileError(SyntaxError):
    def __init__(self, msg, path, source, node):
        lines = source.splitlines()[node.lineno - 1 : node.end_lineno]
        lines[-1] = lines[-1][: node.end_col_offset]
        lines[0] = lines[0][node.col_offset :]
        details = (
            path,
            node.lineno,
            node.col_offset + 1,
            "\n".join(lines),
            node.end_lineno,
            node.end_col_offset,
        )
        super().__init__(msg, details)


class ParfileVisitor(ast.NodeVisitor):
    def __init__(self, path, source, allowed_imports):
        super().__init__()
        self.path = path
        self.source = source
        self.allowed_imports = allowed_imports
        self.imports = {}
        self.namespace = {}

    def visit_Attribute(self, node):
        value = self.visit(node.value)
        return getattr(value, node.attr)

    def visit_Assign(self, node):
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            raise ParfileError("syntax error", self.path, self.source, node)
        name = node.targets[0].id
        value = self.visit(node.value)
        self.namespace[name] = value

    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        raise ParfileError("syntax error", self.path, self.source, node)

    def visit_Call(self, node):
        func = self.visit(node.func)
        args = [self.visit(arg) for arg in node.args]
        return func(*args)

    def visit_Constant(self, node):
        return node.value

    def visit_Import(self, node):
        for imp in node.names:
            if imp.name not in self.allowed_imports:
                msg = f"import not allowed: {imp.name}"
                raise ParfileError(msg, self.path, self.source, node)
            self.imports[imp.asname or imp.name] = importlib.import_module(imp.name)

    def visit_Module(self, node):
        for statement in node.body:
            self.visit(statement)
        return self.namespace

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            if node.id in self.namespace:
                return self.namespace[node.id]
            if node.id in self.imports:
                return self.imports[node.id]
            msg = f"unknown name: {node.id}"
            raise ParfileError(msg, self.path, self.source, node)

    def generic_visit(self, node):
        msg = f"syntax error ({type(node).__name__})"
        raise ParfileError(msg, self.path, self.source, node)


def read_par(path, *, allowed_imports=["math"]):
    with open(path) as fp:
        source = fp.read()
    module = ast.parse(source, filename=path)
    visitor = ParfileVisitor(path, source, allowed_imports)
    return visitor.visit(module)

from types import MethodType, FunctionType
from ..logger import print_info, print_warn, print_error

class T:
    def __init__(self, name: str = None):
        self.name   = name
        self.n      = None
        self.dollar = None
        self.indent = None
    def __call__(self, node: tuple[str, ...], dollar: str = "", indent: int = 0):
        self.n      = node
        self.dollar = dollar
        self.indent = indent
        if self.n == None: return None
        ntype       = self.n[0]
        if ntype == None: return None
        if not hasattr(self, "_"+ntype):
            print_error(f"Language \"{self.name}\" doesn't support \"{ntype}\"")
            exit(1)
        t = getattr(self, "_"+ntype)
        if type(t) in [MethodType, FunctionType]: return t()
        else: return t
    
    def empty_body(s):
        return []
    
    def wt(self, node, dollar: str = None, indent: int = None):
        return type(self)()(node, dollar if dollar else self.dollar, indent if indent else self.indent)
    def wtl(self, nodes, dollar: str = None, indent: int = None):
        return [self.wt(node, dollar, indent) for node in nodes]
    def jwt(self, nodes, sep: str, dollar: str = None, indent: int = None):
        return sep.join(str(self.wt(node, dollar, indent)) for node in nodes)
    def jfwt(self, nodes, func, sep: str, dollar: str = None, indent: int = None):
        return self.jwt(filter(func, nodes), sep, dollar, indent)
    def body(self, content: list[str]):
        clen = 0
        for line in content:
            if line.replace(" ", "") != "": clen += 1
        return "\n"+"\n".join(content if clen > 0 else self.empty_body())
    def escape(self, text: str):
        return text
    
    def _EMPTY_LINE(s):
        return ""
    def _RAWSTRING(s):
        return s.n[1]
    def _PAREN(s):
        return f"({s.wt(s.n[1])})"
    
    def _program(s):
        out = []
        for stmt in s.n[1]:
            if (walked := s.wt(stmt)) != None: out.append((" "*s.indent)+walked)
        return out
    def _raw(s):
        return s.n[1]
    def _var(s):
        return s.n[1] if s.n[1] != "$" else s.dollar
    def _dotid(s):
        return s.n[1]
    def _dotid_dot(s):
        return f"{s.n[1]}.{s.wt(s.n[2])}"
    def _dot(s):
        return f".{s.wt(s.n[1])}"
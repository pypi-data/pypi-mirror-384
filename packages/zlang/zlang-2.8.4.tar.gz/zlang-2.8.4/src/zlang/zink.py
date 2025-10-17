import sys
from sly import Lexer, Parser
from .logger import print_info, print_warn, print_error, info as _info, warn as _warn, error as _error

print(end="zink: ... ", flush=True)

class FilteredLogger(object):
    def __init__(self, f, exit: bool = True):
        self.f = f
        self.exit = exit
        self.had_warnings = False
        self.had_errors = False

    def debug(self, msg, *args, **kwargs):
        self.f.write(_info((msg % args) + '\n'))

    info = debug

    def warning(self, msg, *args, **kwargs):
        self.had_warnings = True
        tolog = (msg % args)
        if "defined, but not used" in tolog: return
        if "unused tokens" in tolog: return
        self.f.write(_warn(tolog + "\n"))
        if self.exit and "conflict" in tolog: exit(1)

    def error(self, msg, *args, **kwargs):
        self.had_errors = True
        self.f.write(_error((msg % args) + "\n"))

    critical = error

    def reset_warnings(self):
        self.had_warnings = False

    def reset_errors(self):
        self.had_errors = False

class ZinkLexer(Lexer):
    tokens = {
        "ID", "NUMBER", "STRING", "BSTRING", "RSTRING", "RAWSTRING", "TRUE", "FALSE", "NONE",
        "EQUAL",
        "DB_PLUS", "DB_MINUS",
        "PLUS", "MINUS", "ASTERISK", "SLASH", "DB_ASTERISK", "DB_SLASH", "PERCENTAGE", "MATMUL", "STRJOIN",
        "PLUS_EQUAL", "MINUS_EQUAL", "ASTERISK_EQUAL", "SLASH_EQUAL", "DOT_EQUAL", "COLON_EQUAL", "DB_ASTERISK_EQUAL", "DB_SLASH_EQUAL", "PERCENTAGE_EQUAL", "MATMUL_EQUAL", "SELF_EQUAL", "STRJOIN_EQUAL",
        "AMPERSAND", "PIPE", "CARET", "TILDE", "DB_LESS_THAN", "DB_GREATER_THAN",
        "AMPERSAND_EQUAL", "PIPE_EQUAL", "CARET_EQUAL", "TILDE_EQUAL", "DB_LESS_THAN_EQUAL", "DB_GREATER_THAN_EQUAL",
        "LPAREN", "RPAREN", "LBRACK", "RBRACK", "LBRACE", "RBRACE",
        "DOT", "COLON", "SEMICOLON", "COMMA", "EXCLAMATION", "QUESTION",
        "IF", "ELIF", "ELSE", "WHILE", "FOR", "ASSERT", "USE", "FROM", "AS", "LIKE", "AT", "IN", "TO", "TRY", "CATCH", "DEF", "CLASS", "NAMESPACE", "WITH", "DEL", "IS", "HAS", "RAISE", "BETWEEN", "MATCH", "CASE", "IGNORE", "TIMES", "ANON",
        "PASS", "CONTINUE", "NEXT", "BREAK", "GLOBAL", "LOCAL",
        "AND", "OR", "NOT",
        "CMP_L", "CMP_G", "CMP_E", "CMP_LE", "CMP_GE", "CMP_NE",
        "LQARROW", "RQARROW", "LARROW", "RARROW", "LDARROW", "RDARROW", "LSMARROW", "RSMARROW", "USMARROW", "DSMARROW", "LBARROW", "RBARROW",
        "DB_ARROW", "DB_DARROW", "DB_SMARROW",
        "DOLLAR", "HASHTAG", "ELLIPSIS", "NEW",
        "SUPER_INIT",
        "NEWLINE", "SPACE",
        "COMMENT"
    }

    ignore                  = " \t"

    @_(r"=== .*(?=\n)")
    def COMMENT(self, t):
        t.value = t.value[4:]
        return t

    @_(r'\\\n')
    def LINE_CONTINUATION(self, t):
        self.lineno += 1
        return None

    @_(r'"(?:[^"\\]|\\.)*"')
    def STRING(self, t):
        t.value = t.value[1:-1]
        return t

    @_(r'b"(?:[^"\\]|\\.)*"')
    def BSTRING(self, t):
        t.value = t.value[2:-1]
        return t

    @_(r'r"(?:[^"\\]|\\.)*"')
    def RSTRING(self, t):
        t.value = t.value[2:-1]
        return t
    
    @_(r'`(?:[^"\\]|\\.)*?`')
    def RAWSTRING(self, t):
        t.value = t.value[1:-1]
        return t

    ID                      = r"[a-zA-Z_][a-zA-Z0-9_]*"

    ELLIPSIS                = r"\.\.\."

    DB_PLUS                 = r"\+\+"
    DB_MINUS                = r"--"

    SELF_EQUAL              = r"@<-"
    SUPER_INIT              = r"@\^"

    LQARROW                 = r"<\?-"
    RQARROW                 = r"-\?>"
    DB_ARROW                = r"<->"
    DB_DARROW               = r"<=>"
    LDARROW                 = r"<<-"
    RDARROW                 = r"->>"
    LARROW                  = r"<-"
    RARROW                  = r"->"
    DB_SMARROW              = r"←→"
    LSMARROW                = r"←"
    RSMARROW                = r"→"
    USMARROW                = r"↑"
    DSMARROW                = r"↓"
    LBARROW                 = r"<\|"
    RBARROW                 = r"\|>"

    DOLLAR                  = r"\$"
    HASHTAG                 = r"#"

    DB_ASTERISK_EQUAL       = r"\*\*="
    DB_SLASH_EQUAL          = r"//="
    PLUS_EQUAL              = r"\+="
    MINUS_EQUAL             = r"-="
    ASTERISK_EQUAL          = r"\*="
    SLASH_EQUAL             = r"/="
    DOT_EQUAL               = r"\.="
    COLON_EQUAL             = r":="
    PERCENTAGE_EQUAL        = r"%="
    MATMUL_EQUAL            = r"@="
    STRJOIN_EQUAL           = r"\.\.="

    DB_ASTERISK             = r"\*\*"
    DB_SLASH                = r"//"
    PLUS                    = r"\+"
    MINUS                   = r"-"
    ASTERISK                = r"\*"
    SLASH                   = r"/"
    PERCENTAGE              = r"%"
    MATMUL                  = r"@"
    STRJOIN                 = r"\.\."

    AMPERSAND_EQUAL         = r"&="
    PIPE_EQUAL              = r"\|="
    CARET_EQUAL             = r"\^="
    TILDE_EQUAL             = r"~="
    DB_LESS_THAN_EQUAL      = r"<<="
    DB_GREATER_THAN_EQUAL   = r">>="

    AMPERSAND               = r"&"
    PIPE                    = r"\|"
    CARET                   = r"\^"
    TILDE                   = r"~"
    DB_LESS_THAN            = r"<<"
    DB_GREATER_THAN         = r">>"

    CMP_E                   = r"=="
    CMP_NE                  = r"!="
    CMP_LE                  = r"<="
    CMP_GE                  = r">="
    CMP_L                   = r"<"
    CMP_G                   = r">"

    EQUAL                   = r"="

    LPAREN                  = r"\("
    RPAREN                  = r"\)"
    LBRACK                  = r"\["
    RBRACK                  = r"\]"
    LBRACE                  = r"\{"
    RBRACE                  = r"\}"

    DOT                     = r"\."
    COLON                   = r":"
    SEMICOLON               = r";"
    COMMA                   = r","
    EXCLAMATION             = r"!"
    QUESTION                = r"\?"

    SPACE                   = r" "

    ID["if"]                = "IF"
    ID["elif"]              = "ELIF"
    ID["else"]              = "ELSE"
    ID["while"]             = "WHILE"
    ID["for"]               = "FOR"
    ID["assert"]            = "ASSERT"
    ID["use"]               = "USE"
    ID["from"]              = "FROM"
    ID["as"]                = "AS"
    ID["like"]              = "LIKE"
    ID["at"]                = "AT"
    ID["in"]                = "IN"
    ID["to"]                = "TO"
    ID["try"]               = "TRY"
    ID["catch"]             = "CATCH"
    ID["pass"]              = "PASS"
    ID["continue"]          = "CONTINUE"
    ID["next"]              = "NEXT"
    ID["global"]            = "GLOBAL"
    ID["local"]             = "LOCAL"
    ID["break"]             = "BREAK"
    ID["True"]              = "TRUE"
    ID["False"]             = "FALSE"
    ID["None"]              = "NONE"
    ID["def"]               = "DEF"
    ID["del"]               = "DEL"
    ID["and"]               = "AND"
    ID["or"]                = "OR"
    ID["not"]               = "NOT"
    ID["is"]                = "IS"
    ID["has"]               = "HAS"
    ID["class"]             = "CLASS"
    ID["with"]              = "WITH"
    ID["raise"]             = "RAISE"
    ID["between"]           = "BETWEEN"
    ID["match"]             = "MATCH"
    ID["case"]              = "CASE"
    ID["ignore"]            = "IGNORE"
    ID["times"]             = "TIMES"
    ID["namespace"]         = "NAMESPACE"
    ID["anon"]              = "ANON"

    @_(r"0x[0-9a-fA-F_]+", r"0b[01_]+", r"[0-9_]+", r"[0-9_]\.[0-9_]", r"\.[0-9_]")
    def NUMBER(self, t):
        if t.value.startswith("0x"):
            t.value = int(t.value[2:].strip("_"), 16)
        elif t.value.startswith("0b"):
            t.value = int(t.value[2:].strip("_"), 2)
        elif "." in t.value:
            t.value = float(t.value.strip("_"))
        else:
            t.value = int(t.value)
        return t
    
    @_(r"\n")
    def NEWLINE(self, t):
        self.lineno += 1
        return t
    
    def find_column(text, token):
        last_cr = text.rfind("\n", 0, token.index)
        if last_cr < 0:
            last_cr = 0
        column = (token.index - last_cr) + 1
        return column

class ZinkParser(Parser):
    debug = False
    debugfile = "parser.txt" if debug else None
    log = FilteredLogger(sys.stderr, exit=not debug)
    had_errors = False

    def __init__(self, ignore_obsolete: bool = False, include_comments: bool = False, include_empty_lines: bool = False):
        super().__init__()
        self.ignore_obsolete = ignore_obsolete
        self.include_comments = include_comments
        self.include_empty_lines = include_empty_lines

    def error(self, token):
        self.had_errors = True
        if token:
            lineno = getattr(token, "lineno", 0)
            if lineno:
                sys.stderr.write(_error(f"Token \"{token.type}\" at line {lineno}\n"))
            else:
                sys.stderr.write(_error(f"Token \"{token.type}\"\n"))
        else:
            sys.stderr.write(_error("Unexpected end of file\n"))
    
    def reset_errors(self):
        self.had_errors = False

    tokens = ZinkLexer.tokens

    precedence = (
        ("right", "EQUAL"),
        ("right", "GENERATOR", "TERNARY"),
        ("nonassoc", "PLUS_EQUAL", "MINUS_EQUAL", "ASTERISK_EQUAL", "SLASH_EQUAL", "DOT_EQUAL", "PERCENTAGE_EQUAL", "AMPERSAND_EQUAL", "MATMUL_EQUAL", "PIPE_EQUAL", "CARET_EQUAL", "TILDE_EQUAL", "DB_LESS_THAN_EQUAL", "DB_GREATER_THAN_EQUAL", "STRJOIN_EQUAL"),
        ("right", "NOT"),
        ("left", "AND", "OR"),
        ("nonassoc", "CMP_L", "CMP_G", "CMP_E", "CMP_LE", "CMP_GE", "CMP_NE", "SAME", "IN"),
        ("left", "INDEX"),
        ("left", "PLUS", "MINUS", "STRJOIN"),
        ("left", "ASTERISK", "SLASH", "DB_ASTERISK", "DB_SLASH", "PERCENTAGE", "MATMUL", "AMPERSAND", "PIPE", "CARET", "DB_LESS_THAN", "DB_GREATER_THAN", "COLON_EQUAL"),
        ("right", "UNARY_PLUS", "UNARY_MINUS", "STRING_UPPER", "STRING_LOWER", "TYPE", "TILDE", "HASHTAG"),
        ("left", "INCREMENT", "DECREMENT"),
        ("left", "AS", "LIKE"),
        ("left", "MEMBER", "DOT", "LPAREN", "EXCLAMATION")
    )

    @_("stmts")
    def program(self, p):
        return ("program", p.stmts)

    @_("stmts stmt")
    def stmts(self, p):
        if p.stmt == None: return p.stmts
        return p.stmts + [p.stmt]
    
    @_("stmt")
    def stmts(self, p):
        return [p.stmt]
    
    @_("ID")
    def type(self, p):
        return ("type", p.ID)
    
    @_("LBRACE expr RBRACE")
    def type(self, p):
        return ("type_expr", p.expr)
    
    @_("NONE")
    def type(self, p):
        return ("type", "None")
    
    @_("types COMMA type")
    def types(self, p):
        return p.types + [p.type]
    
    @_("type")
    def types(self, p):
        return [p.type]
    
    @_("LPAREN type RPAREN")
    def type(self, p):
        return p.type
    
    @_("type LPAREN types RPAREN")
    def type(self, p):
        return ("typelist", p.type, p.types)
    
    @_("type PIPE type")
    def type(self, p):
        return ("typesel", p.type0, p.type1)
    
    @_("expr")
    def arg(self, p):
        return p.expr
    
    @_("ASTERISK ID")
    def arg(self, p):
        return ("arg", p.ID)
    
    @_("DB_ASTERISK ID")
    def arg(self, p):
        return ("kwarg", p.ID)
    
    @_("args COMMA arg")
    def args(self, p):
        return p.args + [p.arg]
    
    @_("args COMMA NEWLINE arg")
    def args(self, p):
        return p.args + [p.arg]
    
    @_("arg")
    def args(self, p):
        return [p.arg]
    
    @_("arg")
    def targ(self, p):
        return p.arg
    
    @_("ID COLON type")
    def targ(self, p):
        return ("typed_arg", p.ID, p.type)
    
    @_("targs COMMA targ")
    def targs(self, p):
        return p.targs + [p.targ]
    
    @_("targ")
    def targs(self, p):
        return [p.targ]
    
    @_("targ")
    def farg(self, p):
        return p.targ
    
    @_("ID EQUAL expr")
    def farg(self, p):
        return ("default_arg", p.ID, p.expr)
    
    @_("ID COLON type EQUAL expr")
    def farg(self, p):
        return ("default_typed_arg", p.ID, p.type, p.expr)
    
    @_("SLASH")
    def farg(self, p):
        return ("slash_arg",)
    
    @_("ASTERISK")
    def farg(self, p):
        return ("asterisk_arg",)
    
    @_("fargs COMMA farg",
       "fargs COMMA MATMUL farg",
       "fargs COMMA CARET farg",
       "fargs COMMA NEWLINE farg",
       "fargs COMMA NEWLINE MATMUL farg",
       "fargs COMMA NEWLINE CARET farg")
    def fargs(self, p):
        if hasattr(p, "MATMUL"): return p.fargs + [("func_assign_self", p.farg)]
        elif hasattr(p, "CARET"): return p.fargs + [("func_assign_super", p.farg)]
        return p.fargs + [p.farg]
    
    @_("farg",
       "MATMUL farg",
       "CARET farg")
    def fargs(self, p):
        if hasattr(p, "MATMUL"): return [("func_assign_self", p.farg)]
        elif hasattr(p, "CARET"): return [("func_assign_super", p.farg)]
        return [p.farg]
    
    @_("arg")
    def fcarg(self, p):
        return p.arg
    
    @_("ID EQUAL expr")
    def fcarg(self, p):
        return ("default_arg", p.ID, p.expr)
    
    @_("ID EQUAL PLUS")
    def fcarg(self, p):
        return ("true_arg", p.ID)
    
    @_("ID EQUAL MINUS")
    def fcarg(self, p):
        return ("false_arg", p.ID)
    
    @_("fcargs COMMA fcarg")
    def fcargs(self, p):
        return p.fcargs + [p.fcarg]
    
    @_("fcargs COMMA NEWLINE fcarg")
    def fcargs(self, p):
        return p.fcargs + [p.fcarg]
    
    @_("fcarg")
    def fcargs(self, p):
        return [p.fcarg]
    
    @_("expr EQUAL expr")
    def kwarg(self, p):
        return (p.expr0, p.expr1)
    
    @_("kwargs COMMA kwarg")
    def kwargs(self, p):
        return p.kwargs + [p.kwarg]
    
    @_("kwargs COMMA NEWLINE kwarg")
    def kwargs(self, p):
        return p.kwargs + [p.kwarg]
    
    @_("kwarg")
    def kwargs(self, p):
        return [p.kwarg]
    
    @_("ID")
    def dotid(self, p):
        return ("dotid", p.ID)
    
    @_("RAWSTRING")
    def dotid(self, p):
        return ("dotid", p.RAWSTRING)

    @_("ID DOT dotid")
    def dotid(self, p):
        return ("dotid_dot", p.ID, p.dotid)

    @_("RAWSTRING DOT dotid")
    def dotid(self, p):
        return ("dotid_dot", p.RAWSTRING, p.dotid)
    
    @_("ELIF expr end program DOT",
       "ELIF expr end program DOT end")
    def if_elif(self, p):
        return (p.expr, p.program)
    
    @_("if_elifs if_elif")
    def if_elifs(self, p):
        return p.if_elifs + [p.if_elif]
    
    @_("if_elif")
    def if_elifs(self, p):
        return [p.if_elif]
    
    @_("CATCH expr end program DOT",
       "CATCH expr end program DOT end")
    def try_catch(self, p):
        return (p.expr, p.program)
    
    @_("try_catches try_catch")
    def try_catches(self, p):
        return p.try_catches + [p.try_catch]
    
    @_("try_catch")
    def try_catches(self, p):
        return [p.try_catch]
    
    @_("SEMICOLON")
    def end(self, p):
        return None
    
    @_("NEWLINE")
    def end(self, p):
        return None
    
    @_("dotid")
    @_("ASTERISK")
    def ref(self, p):
        return getattr(p, "dotid", ("all",))
    
    @_("DOT dotid")
    def ref(self, p):
        return ("dot", p.dotid)
    
    @_("end")
    def stmt(self, p):
        return ("EMPTY_LINE",) if self.include_empty_lines else None
    
    @_("expr end")
    def stmt(self, p):
        return p.expr
    
    @_("COMMENT end")
    def stmt(self, p):
        return ("COMMENT", p.COMMENT) if self.include_comments else None
    
    @_("targs EQUAL args end")
    def stmt(self, p):
        return ("set", p.targs, p.args)
    
    @_("expr PLUS_EQUAL expr end")
    def stmt(self, p):
        return ("set_add", p.expr0, p.expr1)
    
    @_("expr MINUS_EQUAL expr end")
    def stmt(self, p):
        return ("set_subtract", p.expr0, p.expr1)
    
    @_("expr ASTERISK_EQUAL expr end")
    def stmt(self, p):
        return ("set_multiply", p.expr0, p.expr1)
    
    @_("expr SLASH_EQUAL expr end")
    def stmt(self, p):
        return ("set_divide", p.expr0, p.expr1)
    
    @_("expr DOT_EQUAL expr end")
    def stmt(self, p):
        return ("set_dot", p.expr0, p.expr1)
    
    @_("expr PERCENTAGE_EQUAL expr end")
    def stmt(self, p):
        return ("set_modulo", p.expr0, p.expr1)
    
    @_("expr DB_ASTERISK_EQUAL expr end")
    def stmt(self, p):
        return ("set_power", p.expr0, p.expr1)
    
    @_("expr DB_SLASH_EQUAL expr end")
    def stmt(self, p):
        return ("set_floor_divide", p.expr0, p.expr1)
    
    @_("expr MATMUL_EQUAL expr end")
    def stmt(self, p):
        return ("set_matmul", p.expr0, p.expr1)
    
    @_("expr AMPERSAND_EQUAL expr end")
    def stmt(self, p):
        return ("set_bitwise_and", p.expr0, p.expr1)
    
    @_("expr PIPE_EQUAL expr end")
    def stmt(self, p):
        return ("set_bitwise_or", p.expr0, p.expr1)
    
    @_("expr CARET_EQUAL expr end")
    def stmt(self, p):
        return ("set_bitwise_xor", p.expr0, p.expr1)
    
    @_("expr TILDE end")
    def stmt(self, p):
        return ("set_bitwise_not", p.expr)
    
    @_("expr DB_LESS_THAN_EQUAL expr end")
    def stmt(self, p):
        return ("set_bitwise_shl", p.expr0, p.expr1)
    
    @_("expr DB_GREATER_THAN_EQUAL expr end")
    def stmt(self, p):
        return ("set_bitwise_shr", p.expr0, p.expr1)
    
    @_("SELF_EQUAL expr end")
    def stmt(self, p):
        return ("set_self", p.expr)
    
    @_("expr STRJOIN_EQUAL expr end")
    def stmt(self, p):
        return ("set_strjoin", p.expr0, p.expr1)
    
    @_("expr TO expr end")
    def stmt(self, p):
        return ("set_cast", p.expr0, p.expr1)
    
    @_("LBRACE expr RBRACE RARROW expr end")
    def stmt(self, p):
        return ("list_remove_last", p.expr0, p.expr1)
    
    @_("LBRACE expr RBRACE LARROW expr end")
    def stmt(self, p):
        return ("list_append", p.expr0, p.expr1)
    
    @_("LBRACE expr COLON expr RBRACE RARROW expr end")
    def stmt(self, p):
        return ("list_remove", p.expr0, p.expr1, p.expr2)
    
    @_("LBRACE expr COLON expr RBRACE LARROW expr end")
    def stmt(self, p):
        return ("list_insert", p.expr0, p.expr1, p.expr2)
    
    @_("ASSERT expr end")
    def stmt(self, p):
        return ("assert", p.expr)
    
    @_("RAISE expr end")
    def stmt(self, p):
        return ("raise", p.expr)
    
    @_("USE ref end")
    def stmt(self, p):
        return ("use", p.dotid)
    
    @_("USE ref AS dotid end")
    def stmt(self, p):
        return ("use_as", p.ref0, p.dotid0)
    
    @_("USE ref FROM ref end")
    def stmt(self, p):
        return ("use_from", p.ref0, p.ref1)
    
    @_("USE ref AS dotid FROM ref end")
    def stmt(self, p):
        return ("use_as_from", p.ref0, p.dotid0, p.ref1)
    
    @_("WHILE expr end program DOT end")
    def stmt(self, p):
        return ("while", p.expr, p.program)
    
    @_("FOR args RARROW expr end program DOT end")
    def stmt(self, p):
        return ("for", p.args, p.expr, p.program)
    
    @_("FOR args AT expr RARROW expr end program DOT end")
    def stmt(self, p):
        return ("for_at", p.args, p.expr0, p.expr1, p.program)
    
    @_("FOR args RARROW expr end program DOT ELSE end program DOT end")
    def stmt(self, p):
        return ("for_else", p.args, p.expr, p.program0, p.program1)
    
    @_("FOR args AT expr RARROW expr end program DOT ELSE end program DOT end")
    def stmt(self, p):
        return ("for_at_else", p.args, p.expr0, p.expr1, p.program0, p.program1)
    
    @_("FOR var TO expr end program DOT end")
    def stmt(self, p):
        return ("for_to", p.var, p.expr, p.program)
    
    @_("FOR var FROM expr TO expr end program DOT end")
    def stmt(self, p):
        return ("for_from_to", p.var, p.expr0, p.expr1, p.program)
    
    @_("TIMES expr end program DOT end")
    def stmt(self, p):
        return ("times", p.expr, p.program)
    
    @_("IF expr end program DOT end")
    def stmt(self, p):
        return ("if", p.expr, p.program)
    
    @_("IF expr end program DOT ELSE end program DOT end",
       "IF expr end program DOT end ELSE end program DOT end")
    def stmt(self, p):
        return ("if_else", p.expr, p.program0, p.program1)
    
    @_("IF expr end program DOT if_elifs",
       "IF expr end program DOT end if_elifs")
    def stmt(self, p):
        return ("if_elif", p.expr, p.program, p.if_elifs)
    
    @_("IF expr end program DOT if_elifs ELSE end program DOT end",
       "IF expr end program DOT end if_elifs ELSE end program DOT end")
    def stmt(self, p):
        return ("if_elif_else", p.expr, p.program0, p.if_elifs, p.program1)
    
    @_("TRY end program DOT end")
    def stmt(self, p):
        return ("try", p.program)
    
    @_("TRY end program DOT try_catches",
       "TRY end program DOT end try_catches")
    def stmt(self, p):
        return ("try_catch", p.program, p.try_catches)
    
    @_("TRY end program DOT ELSE end program DOT end",
       "TRY end program DOT end ELSE end program DOT end")
    def stmt(self, p):
        return ("try_else", p.program0, p.program1)
    
    @_("TRY end program DOT try_catches ELSE end program DOT end",
       "TRY end program DOT end try_catches ELSE end program DOT end")
    def stmt(self, p):
        return ("try_catch_else", p.program0, p.try_catches, p.program1)
    
    @_("MATCH expr end program DOT end")
    def stmt(self, p):
        return ("match", p.expr, p.program)
    
    @_("CASE expr end program DOT end")
    def stmt(self, p):
        return ("case", p.expr, p.program)
    
    @_("IGNORE expr end")
    def stmt(self, p):
        return ("ignore", p.expr)

    @_("PASS end")
    def stmt(self, p):
        return ("pass",)

    @_("NEXT end")
    def stmt(self, p):
        return ("next",)
    
    @_("BREAK end")
    def stmt(self, p):
        return ("break",)
    
    @_("GLOBAL var end")
    def stmt(self, p):
        return ("global", p.var)
    
    @_("EXCLAMATION LOCAL var end")
    def stmt(self, p):
        return ("nonlocal", p.var)
    
    @_("LOCAL var end")
    def stmt(self, p):
        return ("local", p.var)
    
    @_("GLOBAL targs EQUAL args end")
    def stmt(self, p):
        return ("global_set", p.targs, p.args)
    
    @_("EXCLAMATION LOCAL targs EQUAL args end")
    def stmt(self, p):
        return ("nonlocal_set", p.targs, p.args)
    
    @_("LOCAL targs EQUAL args end")
    def stmt(self, p):
        return ("local_set", p.targs, p.args)
    
    @_("DEF dotid end program DOT",
       "DEF MATMUL dotid end program DOT",
       "DEF QUESTION dotid end program DOT",
       "DEF QUESTION MATMUL dotid end program DOT",
       "DEF dotid LPAREN fargs RPAREN end program DOT",
       "DEF MATMUL dotid LPAREN fargs RPAREN end program DOT",
       "DEF QUESTION dotid LPAREN fargs RPAREN end program DOT",
       "DEF QUESTION MATMUL dotid LPAREN fargs RPAREN end program DOT",
       "DEF dotid COLON type end program DOT",
       "DEF MATMUL dotid COLON type end program DOT",
       "DEF QUESTION dotid COLON type end program DOT",
       "DEF QUESTION MATMUL dotid COLON type end program DOT",
       "DEF dotid LPAREN fargs RPAREN COLON type end program DOT",
       "DEF MATMUL dotid LPAREN fargs RPAREN COLON type end program DOT",
       "DEF QUESTION dotid LPAREN fargs RPAREN COLON type end program DOT",
       "DEF QUESTION MATMUL dotid LPAREN fargs RPAREN COLON type end program DOT",
       "LOCAL DEF dotid end program DOT",
       "LOCAL DEF MATMUL dotid end program DOT",
       "LOCAL DEF QUESTION dotid end program DOT",
       "LOCAL DEF QUESTION MATMUL dotid end program DOT",
       "LOCAL DEF dotid LPAREN fargs RPAREN end program DOT",
       "LOCAL DEF MATMUL dotid LPAREN fargs RPAREN end program DOT",
       "LOCAL DEF QUESTION dotid LPAREN fargs RPAREN end program DOT",
       "LOCAL DEF QUESTION MATMUL dotid LPAREN fargs RPAREN end program DOT",
       "LOCAL DEF dotid COLON type end program DOT",
       "LOCAL DEF MATMUL dotid COLON type end program DOT",
       "LOCAL DEF QUESTION dotid COLON type end program DOT",
       "LOCAL DEF QUESTION MATMUL dotid COLON type end program DOT",
       "LOCAL DEF dotid LPAREN fargs RPAREN COLON type end program DOT",
       "LOCAL DEF MATMUL dotid LPAREN fargs RPAREN COLON type end program DOT",
       "LOCAL DEF QUESTION dotid LPAREN fargs RPAREN COLON type end program DOT",
       "LOCAL DEF QUESTION MATMUL dotid LPAREN fargs RPAREN COLON type end program DOT")
    def stmt(self, p):
        if hasattr(p, "type"):
            return (f"func_def{"_local" if hasattr(p, "LOCAL") else ""}{"_async" if hasattr(p, "QUESTION") else ""}{"_self" if hasattr(p, "MATMUL") else ""}", p.dotid, getattr(p, "fargs", []), p.type, p.program)
        else:
            return (f"func_def{"_local" if hasattr(p, "LOCAL") else ""}{"_async" if hasattr(p, "QUESTION") else ""}{"_self" if hasattr(p, "MATMUL") else ""}_untyped", p.dotid, getattr(p, "fargs", []), p.program)
    
    @_("SLASH ID end program DOT",
       "SLASH ID fargs end program DOT",
       "SLASH QUESTION ID end program DOT",
       "SLASH QUESTION ID fargs end program DOT",
       "SLASH ASTERISK end program DOT",
       "SLASH ASTERISK fargs end program DOT",
       "SLASH QUESTION ASTERISK end program DOT",
       "SLASH QUESTION ASTERISK fargs end program DOT",
       "SLASH PLUS end program DOT",
       "SLASH PLUS fargs end program DOT",
       "SLASH QUESTION PLUS end program DOT",
       "SLASH QUESTION PLUS fargs end program DOT",
       "SLASH MINUS end program DOT",
       "SLASH MINUS fargs end program DOT",
       "SLASH QUESTION MINUS end program DOT",
       "SLASH QUESTION MINUS fargs end program DOT",
       "SLASH EXCLAMATION end program DOT",
       "SLASH EXCLAMATION fargs end program DOT",
       "SLASH QUESTION EXCLAMATION end program DOT",
       "SLASH QUESTION EXCLAMATION fargs end program DOT")
    def stmt(self, p):
        if hasattr(p, "ID"): func_type = p.ID
        elif hasattr(p, "ASTERISK"): func_type = "init"
        elif hasattr(p, "PLUS"): func_type = "enter"
        elif hasattr(p, "MINUS"): func_type = "exit"
        elif hasattr(p, "EXCLAMATION"): func_type = "call"
        return (f"func_def{"_async" if hasattr(p, "QUESTION") else ""}__", func_type, getattr(p, "fargs", []), p.program)
    
    @_("CLASS ID end program DOT")
    def stmt(self, p):
        return ("class_def", p.ID, p.program)
    
    @_("CLASS ID FROM expr end program DOT")
    def stmt(self, p):
        return ("class_def_from", p.ID, p.expr, p.program)
    
    @_("NAMESPACE ID end program DOT")
    def stmt(self, p):
        return ("namespace_def", p.ID, p.program)
    
    @_("WITH expr AS expr end program DOT")
    def stmt(self, p):
        return ("with", p.expr0, p.expr1, p.program)
    
    @_("LARROW end",
       "LARROW expr end",
       "LQARROW end",
       "LQARROW expr end")
    def stmt(self, p):
        return ("yield" if hasattr(p, "LQARROW") else "return", getattr(p, "expr", ("NONE",)))
    
    @_("DEL expr end")
    def stmt(self, p):
        return ("del", p.expr)
    
    @_("LBARROW expr end")
    def stmt(self, p):
        return ("output", p.expr)
    
    @_("MATMUL expr end")
    def stmt(self, p):
        return ("decorator", p.expr)
    
    @_("LPAREN expr COLON_EQUAL expr RPAREN")
    def expr(self, p):
        return ("walrus", p.expr0, p.expr1)
    
    @_("DOLLAR")
    def var(self, p):
        return ("var", "$")
    
    @_("ID")
    def var(self, p):
        return ("var", p.ID)
    
    @_("var")
    def expr(self, p):
        return p.var
    
    @_("TRUE")
    def expr(self, p):
        return ("TRUE",)
    
    @_("FALSE")
    def expr(self, p):
        return ("FALSE",)
    
    @_("NONE")
    def expr(self, p):
        return ("NONE",)
    
    @_("expr LPAREN fcargs RPAREN",
       "expr LPAREN NEWLINE fcargs NEWLINE RPAREN",
       "expr EXCLAMATION")
    def func(self, p):
        return ("func", p.expr, getattr(p, "fcargs", []))
    
    @_("expr DOT var DOLLAR LPAREN fcargs RPAREN",
       "expr DOT var DOLLAR LPAREN NEWLINE fcargs NEWLINE RPAREN",
       "expr DOT var DOLLAR EXCLAMATION",
       "expr DOT RAWSTRING DOLLAR LPAREN fcargs RPAREN",
       "expr DOT RAWSTRING DOLLAR LPAREN NEWLINE fcargs NEWLINE RPAREN",
       "expr DOT RAWSTRING DOLLAR EXCLAMATION",)
    def func(self, p):
        return ("func_self", p.expr, p.var if hasattr(p, "var") else ("raw", p.RAWSTRING), getattr(p, "fcargs", []))

    @_("func")
    def expr(self, p):
        return p.func
    
    @_("LBRACK RBRACK",
       "LBRACK args RBRACK",
       "LBRACK NEWLINE args NEWLINE RBRACK")
    def tuple(self, p):
        return ("tuple", getattr(p, "args", []))
    
    @_("tuple")
    def expr(self, p):
        return p.tuple
    
    @_("LBRACK COMMA RBRACK",
       "LBRACK args COMMA RBRACK",
       "LBRACK NEWLINE args COMMA NEWLINE RBRACK")
    def list(self, p):
        return ("list", getattr(p, "args", []))
    
    @_("list")
    def expr(self, p):
        return p.list
    
    @_("LBRACK EQUAL RBRACK",
       "LBRACK kwargs RBRACK",
       "LBRACK NEWLINE kwargs NEWLINE RBRACK")
    def dict(self, p):
        return ("dict", getattr(p, "kwargs", []))
    
    @_("dict")
    def expr(self, p):
        return p.dict
    
    @_("LBRACK expr DB_ARROW expr RBRACK",
       "LBRACK expr DB_ARROW expr RPAREN",
       "LPAREN expr DB_ARROW expr RBRACK",
       "LPAREN expr DB_ARROW expr RPAREN",
       "LBRACK expr DB_ARROW expr COMMA expr RBRACK",
       "LBRACK expr DB_ARROW expr COMMA expr RPAREN",
       "LPAREN expr DB_ARROW expr COMMA expr RBRACK",
       "LPAREN expr DB_ARROW expr COMMA expr RPAREN")
    def range(self, p):
        return (f"range{"_inc" if hasattr(p, "LBRACK") else "_exc"}{"_inc" if hasattr(p, "RBRACK") else "_exc"}", p.expr0, p.expr1, getattr(p, "expr2", ("NUMBER", "1")))
    
    @_("LBRACE expr DB_ARROW expr RBRACE",
       "LBRACE expr DB_ARROW expr COMMA expr RBRACE")
    def range(self, p):
        return ("range", p.expr0, p.expr1, getattr(p, "expr2", ("NUMBER", "1")))
    
    @_("LBRACE RARROW expr RBRACE",
       "LBRACE RARROW expr COMMA expr RBRACE")
    def range(self, p):
        return ("range", ("NUMBER", "0"), p.expr0 if hasattr(p, "expr0") else p.expr, getattr(p, "expr1", ("NUMBER", "1")))
    
    @_("range")
    def expr(self, p):
        return p.range
    
    @_("expr PLUS expr")
    def expr(self, p):
        return ("add", p.expr0, p.expr1)
    
    @_("expr MINUS expr")
    def expr(self, p):
        return ("subtract", p.expr0, p.expr1)

    @_("expr ASTERISK expr")
    def expr(self, p):
        return ("multiply", p.expr0, p.expr1)

    @_("expr SLASH expr")
    def expr(self, p):
        return ("divide", p.expr0, p.expr1)
    
    @_("expr DB_ASTERISK expr")
    def expr(self, p):
        return ("power", p.expr0, p.expr1)
    
    @_("expr DB_SLASH expr")
    def expr(self, p):
        return ("floor_divide", p.expr0, p.expr1)
    
    @_("expr MATMUL expr")
    def expr(self, p):
        return ("matmul", p.expr0, p.expr1)
    
    @_("expr AMPERSAND expr")
    def expr(self, p):
        return ("bitwise_and", p.expr0, p.expr1)
    
    @_("expr PIPE expr")
    def expr(self, p):
        return ("bitwise_or", p.expr0, p.expr1)
    
    @_("expr CARET expr")
    def expr(self, p):
        return ("bitwise_xor", p.expr0, p.expr1)
    
    @_("TILDE expr")
    def expr(self, p):
        return ("bitwise_not", p.expr)
    
    @_("expr DB_LESS_THAN expr")
    def expr(self, p):
        return ("bitwise_shl", p.expr0, p.expr1)
    
    @_("expr DB_GREATER_THAN expr")
    def expr(self, p):
        return ("bitwise_shr", p.expr0, p.expr1)
    
    @_("expr PERCENTAGE expr")
    def expr(self, p):
        return ("modulo", p.expr0, p.expr1)
    
    @_("expr STRJOIN expr")
    def expr(self, p):
        return ("strjoin", p.expr0, p.expr1)
    
    @_("expr DB_PLUS %prec INCREMENT")
    def expr(self, p):
        return ("inc_after", p.expr)
    
    @_("expr DB_MINUS %prec DECREMENT")
    def expr(self, p):
        return ("dec_after", p.expr)
    
    @_("DB_PLUS expr %prec INCREMENT")
    def expr(self, p):
        return ("inc_before", p.expr)
    
    @_("DB_MINUS expr %prec DECREMENT")
    def expr(self, p):
        return ("dec_before", p.expr)
    
    @_("MINUS expr %prec UNARY_MINUS")
    def expr(self, p):
        return ("unary_minus", p.expr)
    
    @_("PLUS expr %prec UNARY_PLUS")
    def expr(self, p):
        return ("unary_plus", p.expr)
    
    @_("expr IS expr %prec SAME")
    def expr(self, p):
        return ("is", p.expr0, p.expr1)
    
    @_("expr IN expr")
    def expr(self, p):
        return ("in", p.expr0, p.expr1)
    
    @_("expr CMP_E expr")
    def expr(self, p):
        return ("cmp_e", p.expr0, p.expr1)
    
    @_("expr CMP_LE expr")
    def expr(self, p):
        return ("cmp_le", p.expr0, p.expr1)
    
    @_("expr CMP_GE expr")
    def expr(self, p):
        return ("cmp_ge", p.expr0, p.expr1)
    
    @_("expr CMP_L expr")
    def expr(self, p):
        return ("cmp_l", p.expr0, p.expr1)
    
    @_("expr CMP_G expr")
    def expr(self, p):
        return ("cmp_g", p.expr0, p.expr1)
    
    @_("expr CMP_NE expr")
    def expr(self, p):
        return ("cmp_ne", p.expr0, p.expr1)
    
    @_("expr AND expr")
    def expr(self, p):
        return ("and", p.expr0, p.expr1)
    
    @_("expr OR expr")
    def expr(self, p):
        return ("or", p.expr0, p.expr1)
    
    @_("NOT expr")
    def expr(self, p):
        return ("not", p.expr)

    @_("NUMBER")
    def expr(self, p):
        return ("NUMBER", p.NUMBER)
    
    @_("STRING")
    def expr(self, p):
        return ("STRING", p.STRING)
    
    @_("BSTRING")
    def expr(self, p):
        return ("BSTRING", p.BSTRING)
    
    @_("RSTRING")
    def expr(self, p):
        return ("RSTRING", p.RSTRING)

    @_("LPAREN expr RPAREN")
    def expr(self, p):
        return ("PAREN", p.expr)
    
    @_("expr LBRACK expr RBRACK %prec INDEX")
    def expr(self, p):
        return ("index", p.expr0, p.expr1)
    
    @_("expr LBRACK expr COLON RBRACK %prec INDEX")
    def expr(self, p):
        return ("index_from", p.expr0, p.expr1)
    
    @_("expr LBRACK COLON expr RBRACK %prec INDEX")
    def expr(self, p):
        return ("index_to", p.expr0, p.expr1)
    
    @_("expr LBRACK expr COLON expr RBRACK %prec INDEX")
    def expr(self, p):
        return ("index_from_to", p.expr0, p.expr1, p.expr2)
    
    @_("expr LBRACK COLON COLON expr RBRACK %prec INDEX")
    def expr(self, p):
        return ("index_step", p.expr0, p.expr1)
    
    @_("expr LBRACK expr COLON COLON expr RBRACK %prec INDEX")
    def expr(self, p):
        return ("index_from_step", p.expr0, p.expr1, p.expr2)
    
    @_("expr LBRACK COLON expr COLON expr RBRACK %prec INDEX")
    def expr(self, p):
        return ("index_to_step", p.expr0, p.expr1, p.expr2)
    
    @_("expr LBRACK expr COLON expr COLON expr RBRACK %prec INDEX")
    def expr(self, p):
        return ("index_from_to_step", p.expr0, p.expr1, p.expr2, p.expr3)
    
    @_("expr DOT expr %prec MEMBER")
    def expr(self, p):
        return ("member", p.expr0, p.expr1)
    
    @_("USMARROW expr %prec STRING_UPPER")
    def expr(self, p):
        return ("string_upper", p.expr)
    
    @_("DSMARROW expr %prec STRING_LOWER")
    def expr(self, p):
        return ("string_lower", p.expr)
    
    @_("HASHTAG expr")
    def expr(self, p):
        return ("length", p.expr)
    
    @_("expr QUESTION %prec TYPE")
    def expr(self, p):
        return ("get_type", p.expr)
    
    @_("expr AS expr")
    def expr(self, p):
        return ("cast", p.expr0, p.expr1)
    
    @_("expr LIKE expr")
    def expr(self, p):
        return ("cast_type", p.expr0, p.expr1)
    
    @_("LPAREN expr FOR args RARROW expr RPAREN %prec GENERATOR")
    def expr(self, p):
        return ("generator", p.expr0, p.args, p.expr1)
    
    @_("LPAREN expr FOR args AT expr RARROW expr RPAREN %prec GENERATOR")
    def expr(self, p):
        return ("generator_at", p.expr0, p.args, p.expr1, p.expr2)
    
    @_("LPAREN expr IF expr ELSE expr RPAREN %prec TERNARY")
    def expr(self, p):
        return ("ternary", p.expr0, p.expr1, p.expr2)
    
    @_("LPAREN expr IF expr NEWLINE ELSE expr RPAREN %prec TERNARY")
    def expr(self, p):
        return ("ternary", p.expr0, p.expr1, p.expr2)
    
    @_("ELLIPSIS")
    def expr(self, p):
        return ("ellipsis",)
    
    @_("LPAREN expr RPAREN LARROW LPAREN args RPAREN")
    def expr(self, p):
        return ("lambda", p.expr, p.args)
    
    @_("SUPER_INIT")
    def expr(self, p):
        return ("super_init",)
    
    @_("LPAREN expr BETWEEN expr COMMA expr RPAREN")
    def expr(self, p):
        return ("between", p.expr0, p.expr1, p.expr2)
    
    @_("ANON end program DOT",
       "ANON MATMUL end program DOT",
       "ANON QUESTION end program DOT",
       "ANON QUESTION MATMUL end program DOT",
       "ANON LPAREN fargs RPAREN end program DOT",
       "ANON MATMUL LPAREN fargs RPAREN end program DOT",
       "ANON QUESTION LPAREN fargs RPAREN end program DOT",
       "ANON QUESTION MATMUL LPAREN fargs RPAREN end program DOT",
       "ANON COLON type end program DOT",
       "ANON MATMUL COLON type end program DOT",
       "ANON QUESTION COLON type end program DOT",
       "ANON QUESTION MATMUL COLON type end program DOT",
       "ANON LPAREN fargs RPAREN COLON type end program DOT",
       "ANON MATMUL LPAREN fargs RPAREN COLON type end program DOT",
       "ANON QUESTION LPAREN fargs RPAREN COLON type end program DOT",
       "ANON QUESTION MATMUL LPAREN fargs RPAREN COLON type end program DOT")
    def expr(self, p):
        if hasattr(p, "type"):
            return (f"func_def_anon{"_async" if hasattr(p, "QUESTION") else ""}{"_self" if hasattr(p, "MATMUL") else ""}", getattr(p, "fargs", []), p.type, p.program)
        else:
            return (f"func_def_anon{"_async" if hasattr(p, "QUESTION") else ""}{"_self" if hasattr(p, "MATMUL") else ""}_untyped", getattr(p, "fargs", []), p.program)
    
    @_("MATMUL")
    def expr(self, p):
        return ("self",)
    
    @_("CARET")
    def expr(self, p):
        return ("super",)
    
    @_("RAWSTRING")
    def expr(self, p):
        return ("raw", p.RAWSTRING)

print(end="\r          \r", flush=True)
# Build the lexer
import ply.lex as lex
import ply.yacc as yacc


######################
# Lexer for Criteria DSL
######################
tokens = ("ENTRY",)

literals = ["=", "&", "|", "(", ")"]

# Tokens

t_ENTRY = r"[a-zA-Z0-9_]+"

t_ignore = " \t"


def t_newline(t):
    r"\n+"
    t.lexer.lineno += t.value.count("\n")


def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)


lexer = lex.lex()

# Parsing rules
precedence = (("left", "&", "|"),)

######################
# Execution Implementation for Criteria DSL
######################

class Expression:

    def matches(self, context):
        raise NotImplementedError("Subclasses must implement matches method")


class TrueExpression(Expression):
    def matches(self, context):
        return True
    
    def __str__(self):
        return "TRUE"

class Statement(Expression):
    def __init__(self, variable, value):
        self.variable = variable
        self.value = value

    def matches(self, context):
        return context.get(self.variable) == self.value

    def __str__(self):
        return f"{self.variable}={self.value}"


class And(Expression):
    def __init__(self, statement_a, statement_b):
        self.A = statement_a
        self.B = statement_b

    def matches(self, ctx):
        return self.A.matches(ctx) and self.B.matches(ctx)

    def __str__(self):
        return f"({self.A} & {self.B})"


class Or(Expression):
    def __init__(self, statement_a, statement_b):
        self.A = statement_a
        self.B = statement_b

    def matches(self, ctx):
        return self.A.matches(ctx) or self.B.matches(ctx)

    def __str__(self):
        return f"({self.A} | {self.B})"

######################
# Parser for Criteria DSL
######################

def p_expression_assign(p):
    'expression : ENTRY "=" ENTRY'
    value = p[3]
    if p[3] == "true":
        value = True
    elif p[3] == "false":
        value = False
    p[0] = Statement(p[1], value)


def p_expression_binop(p):
    """expression : expression '&' expression
    | expression '|' expression"""
    if p[2] == "&":
        p[0] = And(p[1], p[3])
    elif p[2] == "|":
        p[0] = Or(p[1], p[3])


def p_expression_group(p):
    "expression : '(' expression ')'"
    p[0] = p[2]


def p_error(p):
    if p:
        print("Syntax error at '%s'" % p.value)
    else:
        print("Syntax error at EOF")


parser = yacc.yacc()  # debuglog=TODO

def parse_criteria(criteria_str) -> Expression:
    if criteria_str:
        return parser.parse(criteria_str, lexer=lexer)
    else:
        return TrueExpression()

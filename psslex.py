from ply import lex, yacc
import re

tokens = (
    "WHITESPACE",
    "COLON",
    "SEMICOLON",
    "IDENT",
    "LBRACE",
    "RBRACE",
    "VALUE",
    "CLASS_SELECTOR",
    "SIMPLE_ATTRIBUTE_SELECTOR",
    "ATTRIBUTE_KV_SELECTOR",
    "COMPARISON"
)

states = (
    ('value', 'exclusive'),
)

def t_WHITESPACE(t):
    r"[\t\r\n\f ]+"
    # No return, since we're skipping whitespace.
    # Note this will not match within values

t_IDENT = r"[a-zA-Z0-9_]+"
t_CLASS_SELECTOR = r"\.[a-zA-Z0-9_]+"
t_SIMPLE_ATTRIBUTE_SELECTOR = r"\[[a-zA-Z0-9_]+\]"
t_ATTRIBUTE_KV_SELECTOR = r"\[[a-zA-Z0-9_]+=[a-zA-Z0-9_]+\]"
t_COMPARISON = r'(=|~=|\|=|^=|\$=|\*=)'

def t_COLON(t):
    r":"
    t.lexer.begin('value')
    return t

def t_value_SEMICOLON(t):
    r";"
    t.lexer.begin('INITIAL')
    return t

t_value_VALUE = r"[^;]+"

def t_LBRACE(t):
    r"\{"
    return t

def t_RBRACE(t):
    r"\}"
    t.lexer.begin('INITIAL')
    return t

r_BLOCKCOMMENT = r'\/\*[^*]*\*+([^/*][^*]*\*+)*\/'
r_LINECOMMENT = r'\/\/.*'


def strip_comments(text):
    text = re.sub(r_BLOCKCOMMENT, '', text, flags=re.MULTILINE)
    text = re.sub(r_LINECOMMENT, '', text)
    return text

# Error handling rule
def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

def t_value_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

# Build the lexer
lexer = lex.lex()

# Test the lexer
def test_lexer(input_string):
    no_comments = strip_comments(input_string)
    print(no_comments)
    lexer.input(no_comments)
    while True:
        token = lexer.token()
        if not token:
            break
        print(f"[{token.type}]: '{token.value.strip()}'")

if __name__ == '__main__':
    test_lexer(open("creds.pss.example").read())

"""
.body {
    color: #FF0000; // Red
    font_size: 12px; /* Normal size */
    background_image: url('image.jpg');
    name: John Smith;
}
"""

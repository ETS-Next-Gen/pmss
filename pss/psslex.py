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
    "UNIVERSAL_SELECTOR",
    "COMPARISON",
    "PSEUDO_CLASS_SELECTOR",
    "PSEUDO_ELEMENT_SELECTOR"
)

states = (
    ('value', 'exclusive'),
)

def t_WHITESPACE(t):
    r"[\t\r\n\f ]+"
    # No return, since we're skipping whitespace.
    # Note this will not match within values

t_IDENT = r"[a-zA-Z0-9_]+"
t_COMPARISON = r'(=|~=|\|=|^=|\$=|\*=)'
# Possible TODO:
# * Many of these should move into the parser.
t_CLASS_SELECTOR = r"\." + t_IDENT
t_SIMPLE_ATTRIBUTE_SELECTOR = r"\[" + t_IDENT + "\]"
t_ATTRIBUTE_KV_SELECTOR = r"\[" + t_IDENT + "=" + t_IDENT + "\]"
t_UNIVERSAL_SELECTOR = r"[*]"
t_PSEUDO_CLASS_SELECTOR = r"\:" + t_IDENT
t_PSEUDO_ELEMENT_SELECTOR = r"\:\:" + t_IDENT

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


# Error handling rule
def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

def t_value_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

# Build the lexer
lexer = lex.lex()

def strip_comments(text):
    '''
    Preprocessing step
    '''
    text = re.sub(r_BLOCKCOMMENT, '', text, flags=re.MULTILINE)
    text = re.sub(r_LINECOMMENT, '', text)
    return text

# Test the lexer
def test_lexer(input_string):
    lexer.input(input_string)
    while True:
        token = lexer.token()
        if not token:
            break
        print(f"[{token.type}]: '{token.value.strip()}'")


if __name__ == '__main__':
    example = """
    .body {
        color: #FF0000; /* Red */
        font_size: 12px;
        background_image: url('image.jpg');
        name: John Smith;  // Name
    }
    """

    test_lexer(strip_comments(example))


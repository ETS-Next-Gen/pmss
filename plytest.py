from ply import lex, yacc

tokens = (
    'IDENT',
    'ATKEYWORD',
    'STRING',
    'BAD_STRING',
    'BAD_URI',
    'BAD_COMMENT',
    'HASH',
    'NUMBER',
    'PERCENTAGE',
    'DIMENSION',
    'URI',
    'UNICODE_RANGE',
    'CDO',
    'CDC',
    'COLON',
    'SEMICOLON',
    'LBRACE',
    'RBRACE',
    'LPAREN',
    'RPAREN',
    'LBRACKET',
    'RBRACKET',
    'WHITESPACE',
    'COMMENT',
    'FUNCTION',
    'INCLUDES',
    'DASHMATCH',
    'DELIM'
)

# Regular expression rules for simple tokens
# These were AI-assisted, based on W3C specs:

#   https://www.w3.org/TR/CSS21/syndata.html#tokenization

# They have a few bugs, and need a few test cases. But they're a fine
# starting point.

t_IDENT = r'[a-zA-Z_][a-zA-Z0-9_-]*'
t_ATKEYWORD = r'@' + t_IDENT
t_STRING = r'\"[^\"]*\"|\'' + r'[^\']*\''
t_BAD_STRING = r'\"[^\']*\'|\'' + r'[^\"]*\"'
# t_BAD_URI = r'url\([^\)]*\"|\'' + r'[^\)]*\')'
t_BAD_COMMENT = r'\/\*([^*]|(\*[^\/]))*\*+\/'
t_HASH = r'\#[a-zA-Z0-9_-]+'
t_NUMBER = r'[0-9]+'
t_PERCENTAGE = t_NUMBER + r'%'
t_DIMENSION = t_NUMBER + t_IDENT
t_URI = r'url\(.*?\)'
t_UNICODE_RANGE = r'u\+[0-9a-fA-F?\-]{1,6}(-[0-9a-fA-F]{1,6})?'
t_CDO = r'<\!--'
t_CDC = r'-->'
t_COLON = r':'
t_SEMICOLON = r';'
t_LBRACE = r'\{'
t_RBRACE = r'\}'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBRACKET = r'\['
t_RBRACKET = r'\]'
t_WHITESPACE = r'[\t\r\n\f ]+'
t_COMMENT = r'\/\*[^*]*\*+([^/*][^*]*\*+)*\/'
t_COMMENT = r'\/\*([^\*]|(\*[^\/]))*\*+\/'
t_FUNCTION = t_IDENT + r'\('
t_INCLUDES = r'~='
t_DASHMATCH = r'\|='
t_DELIM = r'.'

# Error handling rule
def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

# Build the lexer
lexer = lex.lex()

# Test the lexer
def test_lexer(input_string):
    lexer.input(input_string)
    while True:
        token = lexer.token()
        if not token:
            break
        print(token.type, token.value)

test_lexer("""
color: #FF0000; // Red
font-size: 12px;
background-image: url('image.jpg');
name: John Smith
""")

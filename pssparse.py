import ply.yacc as yacc
from psslex import strip_comments, lexer, test_lexer, tokens
import selectors

def p_key_value_pair(p):
    'key_value_pair : IDENT COLON VALUE SEMICOLON'
    p[0] = [[p[1], p[3]]]


def p_key_value_pair_merge(p):
    '''key_value_pair : key_value_pair key_value_pair '''
    # Create an empty dictionary for merging
    p[0] = p[1] + p[2]


def p_error(p):
    print("Syntax error in input!")
    print(p)
    if not p:
        print("End of File!")
        return

    while True:
        tok = yacc.token() 
        if not tok or tok.type == 'SEMICOLON': 
            break
    yacc.errok()


def p_type_selector(p):
    ''' selector : IDENT '''
    p[0] = selectors.TypeSelector(p[1])

def p_class_selector(p):
    ''' selector : CLASS_SELECTOR '''
    p[0] = selectors.ClassSelector(p[1])

def p_universal_selector(p):
    ''' selector : UNIVERSAL_SELECTOR '''
    p[0] = selectors.UniversalSelector()

def p_selector_multi(p):
    '''selector : selector selector'''
    p[0] = p[1] + p[2]

def p_block(p):
    '''key_value_pair : selector LBRACE key_value_pair RBRACE
                      | selector LBRACE RBRACE '''
    if len(p) == 5:
        p[0] = [[p[1], p[3]]]
    else:
        p[0] = [[p[1], None]]

def p_simple_attribute_selector(p):
    '''selector : SIMPLE_ATTRIBUTE_SELECTOR'''
    p[0] = selectors.AttributeSelector(attribute=p[1][1:-1], operator=None, value=None)

def p_attribute_kv_selector(p):
    '''selector : ATTRIBUTE_KV_SELECTOR'''
    operator = '='
    attribute = p[1].split("=")[0][1:]
    value = p[1].split("=")[1][:-1]
    p[0] = selectors.AttributeSelector(attribute, operator, value)


def flatten_rules(block_list, parent_selector):
    for selector, block in block_list:
        if block is None:
            continue
        for rule in block:
            if not isinstance(rule[0], selectors.Selector):
                yield parent_selector + selector, rule[0], rule[1]
            else:
                flatten_rules([rule], parent_selector + selector)

def flatten_and_print_parse(block_list):
    for selector, key, value in flatten_rules(result, selectors.NullSelector()):
        print(f"{selector} {{ {key}: {value}; }}")


text = open("creds.pss.example").read()
no_comments = strip_comments(text)
parser = yacc.yacc()
result = parser.parse(no_comments, lexer=lexer)

flatten_and_print_parse(result)

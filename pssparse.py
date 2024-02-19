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


def p_selector(p):
    '''selector : SIMPLE_ATTRIBUTE_SELECTOR
                | ATTRIBUTE_KV_SELECTOR'''
    p[0] = [p[1]]

def p_type_selector(p):
    ''' selector : IDENT '''
    p[0] = selectors.TypeSelector(p[1])

def p_class_selector(p):
    ''' selector : CLASS_SELECTOR '''
    p[0] = selectors.ClassSelector(p[1])

def p_selector_multi(p):
    '''selector : selector selector'''
    p[0] = p[1] + p[2]

def p_block(p):
    '''key_value_pair : selector LBRACE key_value_pair RBRACE'''
    p[0] = [p[1], p[3]]


sample = """
.system {
   hostname: localhost;
   port: 8888;
   protocol: http;
   run_mode: dev;
}

.modules {
   .writing_observer {
       use_nlp: false;
       openai_api_key: ''; // can also be set with OPENAI_API_KEY environment variable
   }
}

.auth .web {
   password_file: passwd.lo;
}

.kvs {
    type: stub;
    expiry: 6000;

    .memoization {
        type: redis-ephemeral;
    }

    .settings {
        type: postgres;
        postgres_auth: local;
    }
}
"""

def flatten_rules(rule_list, parent_selector):
    for selector, rule in rule_list:
        pass

text = open("creds.pss.example").read()
text = sample
no_comments = strip_comments(text)
parser = yacc.yacc()
result = parser.parse(no_comments, lexer=lexer, debug=True)
print(result)


# For now, we're computing a number to get things working, but we probably just want an ordering.

_sample_priorities = {
    'DEFAULTS': 0,         # Built into app
    'GLOBAL_CONFIG': 1000, # E.g. /etc
    'LOCAL_CONFIG': 2000,  # E.g. ~/
    'DATABASE': 3000,     
    'COMMAND_LINE': 40000  # E.g. --port=foo
}


_sample_specificities = {
    'STUDENT': 50,
    'CLASSROOM': 40,
    'TEACHER': 30,
    'SCHOOL': 20,
    'DISTRICT': 10
}

def compute_rule_priority(rule, source):
    '''
    '''
    return 100

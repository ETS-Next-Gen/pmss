import collections
import io
import re

import pss.pssyacc
import pss.psslex

import pss.pssselectors


def flatten_rules(block_list, parent_selector=pss.pssselectors.NullSelector()):
    for selector, block in block_list:
        if block is None:
            continue
        for rule in block:
            combined_selector = parent_selector + selector
            if not isinstance(rule[0], pss.pssselectors.Selector):
                yield combined_selector, rule[0], rule[1]
            else:
                yield from flatten_rules([rule], combined_selector)


def flatten_and_print_parse(parse_results):
    for selector, key, value in flatten_rules(parse_results):
        print(f"{selector} {{ {key}: {value}; }}")


def rule_sheet(parse_results, provenance):
    '''
    We convert a list with a selector / key / value hierarchy as returned by the parser
    into a dictionary of `{ key : { selector: value, selector: value }}`
    '''
    d = collections.defaultdict(lambda:dict())
    for selector, key, value in flatten_rules(parse_results):
        selector.set_provenance(provenance)

        d[key][selector] = value.strip()
    return dict(d)


def load_pss_file(file, provenance, print_debug=False):
    if isinstance(file, str):  # filename
        with open(file, 'r') as f:
            text = f.read()
    elif isinstance(file, io.TextIOBase):  # file-like object
        text = file.read()
    else:
        raise ValueError(f"Incorrect type. Expected filename or file-like object: {file}")
    return load_pss_string(text, provenance=provenance, print_debug=print_debug)

def load_pss_string(text, provenance, print_debug=False):
    no_comments = pss.psslex.strip_comments(text)
    result = pss.pssyacc.parser.parse(no_comments, lexer=pss.psslex.lexer)
    print(result)
    if print_debug:
        flatten_and_print_parse(result)
    rules = rule_sheet(result, provenance)
    return rules



if __name__ == '__main__':
    rules = load_pss_file("creds.pss.example", provenance="test-script")
    print(rules)
    rules2 = load_pss_file(io.StringIO('* {foo:bar;}'), provenance="test-script")
    print(rules2)
    rules3 = load_pss_string('* {foo:bar;}', provenance="test-script")
    print(rules2)

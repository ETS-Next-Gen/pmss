import collections
import re

import pssyacc
import psslex

import pssselectors


def flatten_rules(block_list, parent_selector=pssselectors.NullSelector()):
    for selector, block in block_list:
        if block is None:
            continue
        for rule in block:
            combined_selector = parent_selector + selector
            if not isinstance(rule[0], pssselectors.Selector):
                yield combined_selector, rule[0], rule[1]
            else:
                yield from flatten_rules([rule], combined_selector)


def flatten_and_print_parse(parse_results):
    for selector, key, value in flatten_rules(parse_results):
        print(f"{selector} {{ {key}: {value}; }}")


def rule_sheet(parse_results, metadata={}):
    d = collections.defaultdict(lambda:dict())
    for selector, key, value in flatten_rules(parse_results):
        selector.set_metadata(metadata)

        d[key][selector] = value.strip()
    return dict(d)


def load_pss_file(filename, print_debug=False):
    text = open(filename).read()
    no_comments = psslex.strip_comments(text)
    result = pssyacc.parser.parse(no_comments, lexer=psslex.lexer)
    print(result)
    if print_debug:
        flatten_and_print_parse(result)
    rules = rule_sheet(result)
    return rules



if __name__ == '__main__':
    rules = load_pss_file("creds.pss.example")
    print(rules)

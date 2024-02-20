import collections
import re

import pssyacc
import psslex

import selectors


def flatten_rules(block_list, parent_selector=selectors.NullSelector()):
    for selector, block in block_list:
        if block is None:
            continue
        for rule in block:
            if not isinstance(rule[0], selectors.Selector):
                yield parent_selector + selector, rule[0], rule[1]
            else:
                flatten_rules([rule], parent_selector + selector)


def flatten_and_print_parse(parse_results):
    for selector, key, value in flatten_rules(parse_results):
        print(f"{selector} {{ {key}: {value}; }}")


def rule_sheet(parse_results, metadata={}):
    d = collections.defaultdict(lambda:dict())
    for selector, key, value in flatten_rules(parse_results):
        selector.set_metadata(metadata)

        d[key][selector] = value.strip()
    return dict(d)


def load_pss_file(filename):
    text = open(filename).read()
    no_comments = psslex.strip_comments(text)
    result = pssyacc.parser.parse(no_comments, lexer=psslex.lexer)

    flatten_and_print_parse(result)

    rules = rule_sheet(result)
    return rules



if __name__ == '__main__':
    text = load_pss_file("creds.pss.example")
    print(text)

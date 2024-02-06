import tinycss2

with open('creds.pss.example', 'r') as fd:
    pss = fd.read()

rules = tinycss2.parse_stylesheet(
    pss,
    skip_whitespace=True,
    skip_comments=True
)
for rule in rules:
    print("R>", rule)
    print("P>", rule.prelude)
    print("C>", rule.content)

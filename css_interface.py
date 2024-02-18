# This file is probably obsolete.
#
# tinycss2 has annoying bugs, and ply seems to work better. We're commiting
# to have a snapshot before we (probably) remove it.
#
# Update: There is a PR to fix the tinycss2 bugs which bug us most, but I'm pretty happy with ply,
# so we'll probably take that route


import tinycss2
import tinycss2.ast
import itertools

with open('creds.pss.example', 'r') as fd:
    pss = fd.read()

rules = tinycss2.parse_stylesheet(
    pss,
    skip_whitespace=True,
    skip_comments=True
)

def break_on(ast_list, rule):
    return [
        list(k[1]) for k in itertools.groupby(
            ast_list,
            key=rule
        )
        if not k[0]
    ]


def break_on_whitespace(ast_list):
    return break_on(ast_list, lambda x: isinstance(x, tinycss2.ast.WhitespaceToken))


def break_on_semi(ast_list):
    return break_on(ast_list, lambda x: isinstance(x, tinycss2.ast.LiteralToken) and x.value == ';')

def add_implicit_breaks(ast_list):
    new_list = []
    for token in ast_list:
        new_list.append(token)
        if isinstance(token, tinycss2.ast.CurlyBracketsBlock):
            new_list.append(tinycss2.ast.LiteralToken(0, 0, ';'))
    return new_list

def split_rules(ast_list):
    rules_with_explicit_breaks = add_implicit_breaks(ast_list);
    return break_on_semi(rules_with_explicit_breaks)

class Selector():
    def __init__(self, ast_list=None):
        self.ast_list = ast_list

    @classmethod
    def from_ast_list(cls, ast_list):
        if isinstance(ast_list[0], tinycss2.ast.LiteralToken) and ast_list[0].value == '.':
            return ClassSelector(ast_list)
        elif isinstance(ast_list[0], tinycss2.ast.SquareBracketsBlock):
            return AttributeSelector(ast_list)
        else:
            print(ast_list[0].content)
            raise ValueError(f"Unknown selector: {ast_list}")


class ClassSelector(Selector):
    def __init__(self, ast_list):
        super().__init__(ast_list)

        if len(ast_list) != 2:
            raise ValueError(f"The AST for a .class selector should have exactly two elements. {ast_list}")
        self.class_name = ast_list[1].value

    def get_class(self):
        return self.class_name

    def __repr__(self):
        return f"{self.__class__.__name__}(class_name={self.class_name})"


class AttributeSelector(Selector):
    # https://developer.mozilla.org/en-US/docs/Learn/CSS/Building_blocks/Selectors/Attribute_selectors
    class Operators():
        '''
        TODO: This should probably be abstracted out into it's own
        class, but this is a glorified enum, but with support for
        e.g. iteration or operations like '=' in Operators()

        Note that this needs to be instantiated to work, because of
        class method versus object method issues.

        Probably the right format here is a new Enum class which takes
        a dict as kwargs or similar.
        '''
        EQUALS = "="
        INCLUDES = "~="
        DASH_MATCH = "|="
        PREFIX_MATCH = "^="
        SUFFIX_MATCH = "$="
        SUBSTRING_MATCH = "*="

        def all_keys(self):
            return [x for x in dir(self) if isinstance(getattr(self, x), str) and not x.startswith("__")]

        def all_values(self):
            return [getattr(self, x) for x in self.all_keys()]

        def __iter__(self):
            yield from self.all_values()


    def __init__(self, ast_list):
        super().__init__(ast_list)
        bracket_block = ast_list[0]
        print(bracket_block)
        self.attribute = bracket_block.content[0].value
        if len(bracket_block.content) > 1:
            self.operator = bracket_block.content[1].value
            self.value = bracket_block.content[2].value
        else:
            self.operator = None
            self.value = None
        if len(bracket_block.content) > 3:
            raise AttributeError("To do: Implement parsing attributes. E.g. [foo=bar i]")
        if self.operator not in self.Operators() and self.operator is not None:
            raise AttributeError("Invalid bracket block. Note: Parsing CSS bracket blocks is not complete, so this may be a parser issue.")

    def __repr__(self):
        return f"{self.__class__.__name__}(key={self.attribute}, operator='{self.operator}', value={self.value})"


def handle_rule(rule):
    print("Rule\n====")
    print("R>", rule)
    print("- prelude: ",)
    print("BS:", list(break_on_whitespace(rule.prelude)))
    print("BS:", list(map(lambda x: "".join(map(lambda y: y.value if hasattr(y, 'value') else repr(y), x)), break_on_whitespace(rule.prelude))))
    print("BS:", list(map(Selector.from_ast_list, break_on_whitespace(rule.prelude))))
    for token in rule.prelude:
        print(f"{token}:{token.type}:{token.value}:{tinycss2.serializer.serialize([token])}")
    print()
    print("Content")
    for token in rule.content:
        print(token,token.type,getattr(token,"value",None) or token.content)
    print("R>", split_rules(rule.content))
    print()


for rule in rules:
    handle_rule(rule)

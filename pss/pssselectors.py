# TODO: Equality should compare metadata too.

class Selector():
    def __init__(self):
        self.metadata = None

    def set_metadata(self, metadata):
        self.metadata = metadata

    def __add__(self, other):
        if isinstance(self, NullSelector):
            return other

        if isinstance(other, NullSelector):
            return self

        if not isinstance(other, Selector):
            raise TypeError(f"Unsupported type: {type(other)}")

        if isinstance(self, CompoundSelector):
            self_selectors = self.selectors
        else:
            self_selectors = [ self ]

        if isinstance(other, CompoundSelector):
            other_selectors = other.selectors
        else:
            other_selectors = [ other ]

        return CompoundSelector(self_selectors + other_selectors)

    def __repr__(self):
        return f"<{self.__class__.__name__} {self}>"

    def __hash__(self):
        return hash(str(self))

    def __ne__(self, other):
        return not self == other

    def match(self, id=None, types=[], classes=[], attributes={}):
        raise UnimplementedError("This function should always be overridden.")


class ClassSelector(Selector):
    # e.g. `.foo`
    def __init__(self, class_name):
        super().__init__()
        if class_name[0] == ".":
            class_name = class_name[1:]
        self.class_name = class_name

    def __str__(self):
        return f".{self.class_name}"

    def __eq__(self, other):
        if not isinstance(other, ClassSelector):
            return False

        return self.class_name == other.class_name

    def __hash__(self):
        return super().__hash__()

    def match(self, id=None, types=[], classes=[], attributes={}):
        if self.class_name in classes:
            return True
        return False

class TypeSelector(Selector):
    # e.g. `div`
    def __init__(self, element_type):
        super().__init__()
        self.element_type = element_type

    def __str__(self):
        return self.element_type

    def __eq__(self, other):
        if not isinstance(other, TypeSelector):
            return False

        return self.element_type == other.element_type

    def __hash__(self):
        return super().__hash__()

    def match(self, id=None, types=[], classes=[], attributes={}):
        if self.element_type in types:
            return True
        return False

class IDSelector(Selector):
    # e.g. `#bar`
    def __init__(self, id_name):
        super().__init__()
        if id_name[0] == "#":
            id_name = id_name[1:]
        self.id_name = id_name

    def __str__(self):
        return f"#{self.id_name}"

    def __eq__(self, other):
        if not isinstance(other, IDSelector):
            return False

        return self.id_name == other.id_name

    def __hash__(self):
        return super().__hash__()

    def match(self, id=None, types=[], classes=[], attributes={}):
        if self.id_name == id:
            return True
        return False


class PseudoClassSelector(Selector):
    # e.g. `:hover`
    def __init__(self, pseudo_class):
        super().__init__()
        self.pseudo_class = pseudo_class

    def __str__(self):
        return f":{self.pseudo_class}"

    def __eq__(self, other):
        if not isinstance(other, PseudoClassSelector):
            return False

        return self.pseudo_class == other.pseudo_class

    def __hash__(self):
        return super().__hash__()

    def match(self, id=None, types=[], classes=[], attributes={}):
        return False  # TODO: Implement


class PseudoElementSelector(Selector):
    # e.g. `::before`
    def __init__(self, pseudo_element):
        super().__init__()
        self.pseudo_element = pseudo_element

    def __str__(self):
        return f"::{self.pseudo_element}"

    def __eq__(self, other):
        if not isinstance(other, PseudoElementSelector):
            return False

        return self.pseudo_element == other.pseudo_element

    def __hash__(self):
        return super().__hash__()

    def match(self, id=None, types=[], classes=[], attributes={}):
        return False  # TODO: Implement


class AttributeSelector(Selector):
    # e.g. [foo$=bar] or [biff]
    #
    # https://developer.mozilla.org/en-US/docs/Learn/CSS/Building_blocks/Selectors/Attribute_selectors
    #
    # Note that we treat [biff] (an attribute exists) as operator and value simply being None
    def __init__(self, attribute, operator, value):
        super().__init__()
        self.attribute = attribute
        self.operator = operator
        self.value = value

    def __str__(self):
        if self.operator is None:
            return f"[{self.attribute}]"
        return f"[{self.attribute}{self.operator}{self.value}]"

    def __eq__(self, other):
        if not isinstance(other, AttributeSelector):
            return False

        return self.attribute == other.attribute and self.operator == other.operator and self.value == other.value

    def __hash__(self):
        return super().__hash__()

    def match(self, id=None, types=[], classes=[], attributes={}):
        if self.attribute not in attributes:
            return False
        if self.operator is None:
            return True
        if self.operator != '=':
            raise UnimplementedError("TODO: Implement non-equality operators in AttributeSelector")
        if self.value == attributes[self.attribute]:
            return True
        return False


class CompoundSelector(Selector):
    # e.g. '.foo.bar [baz=biff] [bam] blah
    def __init__(self, selectors):
        super().__init__()
        self.selectors = selectors

    def __str__(self):
        return " ".join(map(str, self.selectors))

    def __eq__(self, other):
        if not isinstance(other, CompoundSelector):
            return False

        # TODO: We should think through if we should sort so:
        #  "foo bar" == "bar foo"
        return all(s1 == s2 for s1, s2 in zip(self.selectors, other.selectors))

    def __hash__(self):
        return super().__hash__()

    def match(self, *args, **kwargs):
        return all([s.match(*args, **kwargs) for s in self.selectors])

class NullSelector(CompoundSelector):
    def __init__(self):
        super().__init__([])

    def __str__(self):
        return '---'

    def __eq__(self, other):
        return isinstance(other, NullSelector)

    def __hash__(self):
        return super().__hash__()

    def match(self, *args, **kwargs):
        return True

class UniversalSelector(Selector):
    def __init__(self):
        super().__init__()

    def __str__(self):
        return "*"

    def __eq__(self, other):
        return isinstance(other, UniversalSelector)

    def __hash__(self):
        return super().__hash__()

    def match(self, *args, **kwargs):
        return True


# Broken. Should be fixed at some point. Neither json nor orjson currently
# support non-string keys.
#
# def selector_encoder(obj, default=None):
#     '''
#     This is a default encoder for JSON encoders to be able to
#     handle selectors. Note that Python's default `json` library won't
#     call this on keys (just values), so we provide an orjson
#     convenience function below.

#     To be able to chain these, we provider a `default`.
#     '''
#     print("I got called!")
#     if isinstance(obj, Selector):
#         return str(obj)
#     elif default is not None:
#         return default(obj)
#     raise TypeError(f"Object of type {type(obj)} is not serializable")

# def json_dumps(j):
#     '''
#     Encode a JSON object with selectors.
#     '''
#     return orjson.dumps(
#         j,
#         default=selector_encoder,
#         option=orjson.OPT_NON_STR_KEYS | orjson.OPT_INDENT_2).decode('utf-8')

def test_selector_classes():
    ID = 'test_id'
    CLASS_NAME = 'test_class'
    ELEMENT_TYPE = 'div'
    ATTRIBUTE_KEY = 'foo'
    ATTRIBUTE_VALUE = '='

    id_selector = IDSelector(ID)
    class_selector = ClassSelector(CLASS_NAME)
    type_selector = TypeSelector(ELEMENT_TYPE)
    attribute_selector = AttributeSelector(ATTRIBUTE_KEY, ATTRIBUTE_VALUE, ELEMENT_TYPE)

    # Testing match function with correct matches
    assert id_selector.match(id=ID)
    assert class_selector.match(classes=[CLASS_NAME])
    assert type_selector.match(types=[ELEMENT_TYPE])
    assert attribute_selector.match(attributes={ATTRIBUTE_KEY:ELEMENT_TYPE})

    # Testing match function with incorrect matches
    assert not id_selector.match(id=f"{ID}_incorrect")
    assert not class_selector.match(classes=[f"{CLASS_NAME}_incorrect"])
    assert not type_selector.match(types=[f"{ELEMENT_TYPE}_incorrect"])
    assert not attribute_selector.match(attributes={ATTRIBUTE_KEY:ATTRIBUTE_VALUE})

    # Testing match function with empty arguments
    assert not id_selector.match()
    assert not class_selector.match()
    assert not type_selector.match()
    assert not attribute_selector.match()

    # Testing match function for compound selectors
    compound_selector = id_selector + class_selector + type_selector + attribute_selector
    assert compound_selector.match(
        id=ID,
        types=[ELEMENT_TYPE],
        classes=[CLASS_NAME],
        attributes={ATTRIBUTE_KEY:ELEMENT_TYPE}
    )
    assert not compound_selector.match(
        id=ID,
        types=[ELEMENT_TYPE],
        classes=[CLASS_NAME + "_incorrect"],
        attributes={ATTRIBUTE_KEY:ELEMENT_TYPE}
    )

if __name__ == "__main__":
    test_selector_classes()
    print("All test cases passed successfully.")

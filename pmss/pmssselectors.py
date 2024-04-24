import json


class Selector():
    def __init__(self, provenance=None):
        self.provenance = provenance

    def set_provenance(self, provenance):
        self.provenance = provenance

    def css_specificity(self):
        '''
        This gives specificity as per CSS standards. This is
        probably not the ordering function which makes the most sense
        in many settings contexts, but it's a good well-defined,
        well-documented default.
        '''
        raise NotImplementedError('This should be defined on a subclass')

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
            self_selectors = [self]

        if isinstance(other, CompoundSelector):
            other_selectors = other.selectors
        else:
            other_selectors = [other]

        return CompoundSelector(self_selectors + other_selectors)

    def __str__(self):
        raise UnimplementedError("This function should always be overridden.")

    def __repr__(self):
        return f"<{self.__class__.__name__} {self} / {self.provenance}>"

    def __hash__(self):
        return hash(str(self.provenance) + ":" + str(self))

    def __ne__(self, other):
        return not self == other

    def match(self, id=None, types=[], classes=[], attributes={}):
        raise UnimplementedError("This function should always be overridden.")


class ClassSelector(Selector):
    # e.g. `.foo`
    def __init__(self, class_name, provenance=None):
        super().__init__(provenance=provenance)
        if class_name[0] == ".":
            class_name = class_name[1:]
        self.class_name = class_name

    def css_specificity(self):
        return 10

    def __str__(self):
        return f".{self.class_name} / {self.provenance}"

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
    def __init__(self, element_type, provenance=None):
        super().__init__(provenance=provenance)
        if element_type is None:
            raise AttributeError("Element type should be a string")
        self.element_type = element_type

    def __str__(self):
        return self.element_type

    def __eq__(self, other):
        if not isinstance(other, TypeSelector):
            return False

        return self.element_type == other.element_type

    def __hash__(self):
        return super().__hash__()

    def css_specificity(self):
        return 1

    def match(self, id=None, types=[], classes=[], attributes={}):
        if self.element_type in types:
            return True
        return False


class IDSelector(Selector):
    # e.g. `#bar`
    def __init__(self, id_name, provenance=None):
        super().__init__(provenance=provenance)
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

    def css_specificity(self):
        return 100

    def match(self, id=None, types=[], classes=[], attributes={}):
        if self.id_name == id:
            return True
        return False


class PseudoClassSelector(Selector):
    # e.g. `:hover`
    def __init__(self, pseudo_class, provenance=None):
        super().__init__(provenance=provenance)
        self.pseudo_class = pseudo_class

    def __str__(self):
        return f":{self.pseudo_class}"

    def __eq__(self, other):
        if not isinstance(other, PseudoClassSelector):
            return False

        return self.pseudo_class == other.pseudo_class

    def __hash__(self):
        return super().__hash__()

    def css_specificity(self):
        return 10

    def match(self, id=None, types=[], classes=[], attributes={}):
        return False  # TODO: Implement


class PseudoElementSelector(Selector):
    # e.g. `::before`
    def __init__(self, pseudo_element, provenance=None):
        super().__init__(provenance=provenance)
        self.pseudo_element = pseudo_element

    def __str__(self):
        return f"::{self.pseudo_element}"

    def __eq__(self, other):
        if not isinstance(other, PseudoElementSelector):
            return False

        return self.pseudo_element == other.pseudo_element

    def __hash__(self):
        return super().__hash__()

    def css_specificity(self):
        return 10

    def match(self, id=None, types=[], classes=[], attributes={}):
        return False  # TODO: Implement


class AttributeSelector(Selector):
    # e.g. [foo$=bar] or [biff]
    #
    # https://developer.mozilla.org/en-US/docs/Learn/CSS/Building_blocks/Selectors/Attribute_selectors
    #
    # Note that we treat [biff] (an attribute exists) as operator and value simply being None
    def __init__(self, attribute, operator, value, provenance=None):
        super().__init__(provenance=provenance)
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

    def css_specificity(self):
        return 10

    def match(self, id=None, types=[], classes=[], attributes={}):
        if self.attribute not in attributes:
            return False
        if self.operator is None:
            return True
        if self.operator != '=':
            raise NotImplementedError("TODO: Implement non-equality operators in AttributeSelector")
        if self.value == attributes[self.attribute]:
            return True
        return False


class CompoundSelector(Selector):
    # e.g. '.foo.bar [baz=biff] [bam] blah
    def __init__(self, selectors, provenance=None):
        super().__init__(provenance=provenance)
        self.selectors = selectors

    def __str__(self):
        return " ".join(map(str, self.selectors))

    def __eq__(self, other):
        if not isinstance(other, CompoundSelector):
            return False

        # TODO: We should think through if we should sort so:
        #  "foo bar" == "bar foo"
        return all(s1 == s2 for s1, s2 in zip(self.selectors, other.selectors))

    def css_specificity(self):
        return sum(s.css_specificity() for s in self.selectors)

    def __hash__(self):
        return super().__hash__()

    def match(self, *args, **kwargs):
        return all([s.match(*args, **kwargs) for s in self.selectors])


class NullSelector(CompoundSelector):
    def __init__(self, provenance=None):
        super().__init__([])

    def __str__(self):
        return '---'

    def __eq__(self, other):
        return isinstance(other, NullSelector)

    def __hash__(self):
        return super().__hash__()

    def css_specificity(self):
        return 0

    def match(self, *args, **kwargs):
        return True


class UniversalSelector(Selector):
    def __init__(self, provenance=None):
        super().__init__(provenance=provenance)

    def css_specificity(self):
        return 0

    def __str__(self):
        return "*"

    def __eq__(self, other):
        return isinstance(other, UniversalSelector)

    def __hash__(self):
        return super().__hash__()

    def match(self, *args, **kwargs):
        return True


sort_hierarchy = [
    AttributeSelector,
    UniversalSelector,
    NullSelector
]


def simple_selector_sort_key(selector):
    '''Stub function for helping sort lists of selectors. Eventually,
    we want to use a comparison function rather than a key
    function. We'll never use this in practice, but it gives an
    alternative to css_selector()
    '''
    selector_type = type(selector)
    try:
        idx = sort_hierarchy.index(selector_type)
    except ValueError:
        raise RuntimeError(f'We are unsure how to sort this selector: `{selector}`')
    return (idx, selector)

def css_selector_key(selector):
    '''
    Follow CSS rules for specificity. These are a little bit odd
    for settings, as 10 classes are equal to one ID, so there are
    weird boundary conditions we might not want in a settings
    language.

    On the upside, it's well-documented and standardized.
    '''
    return -selector.css_specificity()

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
    assert not attribute_selector.match(attributes={ATTRIBUTE_KEY: ATTRIBUTE_VALUE})

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
        attributes={ATTRIBUTE_KEY: ELEMENT_TYPE}
    )
    assert not compound_selector.match(
        id=ID,
        types=[ELEMENT_TYPE],
        classes=[CLASS_NAME + "_incorrect"],
        attributes={ATTRIBUTE_KEY: ELEMENT_TYPE}
    )

if __name__ == "__main__":
    test_selector_classes()
    print("All test cases passed successfully.")

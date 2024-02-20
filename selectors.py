class Selector():
    def __add__(self, other):
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

class ClassSelector(Selector):
    # e.g. `.foo`
    def __init__(self, class_name):
        if class_name[0] == ".":
            class_name = class_name[1:]
        self.class_name = class_name

    def __str__(self):
        return f".{self.class_name}"

    def __eq__(self, other):
        if not isinstance(other, ClassSelector):
            return False

        return self.class_name == other.class_name


class TypeSelector(Selector):
    # e.g. `div`
    def __init__(self, element_type):
        self.element_type = element_type
    
    def __str__(self):
        return self.element_type

    def __eq__(self, other):
        if not isinstance(other, TypeSelector):
            return False

        return self.element_type == other.element_type

    def __ne__(self, other):
        return not self == other


class IDSelector(Selector):
    # e.g. `#bar`
    def __init__(self, id_name):
        if id_name[0] == "#":
            id_name = id_name[1:]
        self.id_name = id_name

    def __str__(self):
        return f"#{self.id_name}"

    def __eq__(self, other):
        if not isinstance(other, IDSelector):
            return False

        return self.id_name == other.id_name


class PseudoClassSelector(Selector):
    # e.g. `:hover`
    def __init__(self, pseudo_class):
        self.pseudo_class = pseudo_class
    
    def __str__(self):
        return f":{self.pseudo_class}"

    def __eq__(self, other):
        if not isinstance(other, PseudoClassSelector):
            return False

        return self.pseudo_class == other.pseudo_class


class PseudoElementSelector(Selector):
    # e.g. `::before`
    def __init__(self, pseudo_element):
        self.pseudo_element = pseudo_element
    
    def __str__(self):
        return f"::{self.pseudo_element}"

    def __eq__(self, other):
        if not isinstance(other, PseudoElementSelector):
            return False

        return self.pseudo_element == other.pseudo_element


class AttributeSelector(Selector):
    # e.g. [foo$=bar] or [biff]
    #
    # https://developer.mozilla.org/en-US/docs/Learn/CSS/Building_blocks/Selectors/Attribute_selectors
    #
    # Note that we treat [biff] (an attribute exists) as operator and value simply being None
    def __init__(self, attribute, operator, value):
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


class CompoundSelector(Selector):
    # e.g. '.foo.bar [baz=biff] [bam] blah
    def __init__(self, selectors):
        self.selectors = selectors

    def __str__(self):
        return " ".join(map(str, self.selectors))

    def __eq__(self, other):
        if not isinstance(other, CompoundSelector):
            return False

        # TODO: We should think through if we should sort so:
        #  "foo bar" == "bar foo"
        return all(s1 == s2 for s1, s2 in zip(self.selectors, other.selectors))


class NullSelector(CompoundSelector):
    def __init__(self):
        super().__init__([])

    def __str__(self):
        return '---'

    def __eq__(self, other):
        return isinstance(other, NullSelector)


class UniversalSelector(Selector):
    def __str__(self):
        return "*"
    def __eq__(self, other):
        return isinstance(other, UniversalSelector)


'''These are used to preprocess data into standardized types.

Design guidelines:

- Where possible, we'd like to reuse other libraries, so formats are
  standardized.
- Conversely, this is intended to be reusable (even without the rest of
  this system)
- It's okay to have overlapping types. For example, a human-friendly
  system might want a datetime with the flexible format of dateutil,
  whereas a critical one might want to be locked down to ISO8601

We would like more thought about how these explicitly map to
types. It'd be nice to advertise conversion to standard JSON types,
database types, as well as types of a range of programming
languages. TSVx has some thoughts about this.
'''


import configparser
import collections
import doctest
import datetime
import enum
import functools
import math
import os.path
import re

_TYPES_DICT = collections.defaultdict(dict)

class DictEnum:
    def __init__(self, d):
        self.d = d

    def __getattr__(self, attr):
        '''
        Just the string.
        '''
        if attr in self.d:
            return attr
        else:
            raise ValueError("No type: ", attr)

    # Adds capability to use 'in' keyword
    def __contains__(self, key):
        return key in self.d

    # Adding a __dir__ to list all attributes
    def __dir__(self):
        return list(self.d.keys())

    def __getitem__(self, key):
        '''
        Dictionary of info for item
        '''
        if key in self.d:
            return self.d[key]
        else:
            raise KeyError(f"Invalid type: {key}")


TYPES = DictEnum(_TYPES_DICT)

def parse(
        value,
        pmsstype,
        extra_args={}):
    '''
    >>> parse("570000", TYPES.port)
    Traceback (most recent call last):
    ...
    ValueError: Value '570000' ('570000') is more than 65535
    >>> parse("57", TYPES.port)
    57
    >>> parse("true", TYPES.boolean)
    True
    >>> parse("/etc/", TYPES.filename, {"exists": True})
    '/etc'
    >>> parse("/f1aa1.xza", TYPES.filename)
    '/f1aa1.xza'
    >>> parse("/f1aa1.xza", TYPES.filename, {"exists": True})
    Traceback (most recent call last):
    ...
    ValueError: File does not exist: /f1aa1.xza (/f1aa1.xza)
    '''
    return TYPES[pmsstype]['parser'](value, **extra_args)


class TransformType(enum.Enum):
    Decorator = 'Decorator'


def parser(
        type_name,
        validation_regexp=None,
        min=None,
        max=None,
        parent=None,
        choices=None,
        transform=TransformType.Decorator
):
    '''We want to be able to call the parser as both a
    decorator and call it without including a function.

    We initially set the `type_name` parser to be an identity
    function (or the passed in `transform` function). If this
    function is being used as a decorator, we overwrite the
    parser with the decorated function.

    Additionally, we use a closure so we can validate (check
    the regex, min, max, choices, etc.) the output of
    whatever function is used for the parser.

    NOTE: the `transform` parameter will do nothing (gets
    overwritten) when this function is called as a decorator
    '''
    def validate_value(value_function):
        def new_func(value, **kwargs):
            if validation_regexp and isinstance(value, str):
                if not re.match(validation_regexp, value):
                    raise ValueError(f"Value '{value}' does not match the required pattern {validation_regexp})")
            if parent:
                value = _TYPES_DICT[parent]['parser'](value)
            parsed = value_function(value, **kwargs)
            if min is not None and parsed < min:
                raise ValueError(f"Value '{value}' ('{parsed}') is less than {min}")
            if max is not None and parsed > max:
                raise ValueError(f"Value '{value}' ('{parsed}') is more than {max}")
            if choices is not None and value not in choices:
                raise ValueError(f"Value '{value}' ('{parsed}') is not a valid option for {type_name}. Available choices: {choices}")
            return parsed
        return new_func

    def inner(func):
        _TYPES_DICT[type_name]['parser'] = validate_value(func)
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper

    if transform != TransformType.Decorator:
        transformation_func = transform if transform is not None else lambda val: val
        if not callable(transformation_func):
            raise TypeError('The transform paramter must be a callable function.')
        _TYPES_DICT[type_name]['parser'] = validate_value(transformation_func)
    return inner

@parser("string")
def _convert_to_string(value):
    return str(value)

@parser("boolean")
def _convert_to_boolean(value):
    """
    Return a boolean value translating from other types if necessary.

    Based on: https://github.com/python/cpython/blob/3.12/Lib/configparser.py

    >>> _convert_to_boolean(True)
    True

    >>> _convert_to_boolean(False)
    False

    >>> _convert_to_boolean(None)
    False

    >>> _convert_to_boolean("True")
    True

    >>> _convert_to_boolean("false")
    False

    >>> _convert_to_boolean("yes")
    True

    >>> _convert_to_boolean("no")
    False

    >>> _convert_to_boolean("on")
    True

    >>> _convert_to_boolean("off")
    False

    >>> _convert_to_boolean("1")
    True

    >>> _convert_to_boolean("0")
    False

    >>> _convert_to_boolean("invalid")
    Traceback (most recent call last):
    ...
    ValueError: Not a boolean: invalid
    """
    try:
        if value in [True]:
            return True
        if value in [False, None]:
            return False

        return configparser.RawConfigParser.BOOLEAN_STATES[value.lower().strip()]
    except KeyError:
        raise ValueError(f"Not a boolean: {value}")

TIME_UNITS = {
    'y': 365 * 24 * 60 * 60,  # years
    'w': 7 * 24 * 60 * 60,  # weeks
    'd': 24 * 60 * 60,  # days
    'h': 60 * 60,  # hours
    'm': 60,  # minutes
    's': 1,  # seconds
    'ms': 0.001  # milliseconds
}

TIME_UNIT_ALIASES = {
    'y': ['year', 'years'],
    'w': ['week', 'weeks'],
    'd': ['day', 'days'],
    'h': ['hour', 'hours'],
    'm': ['min', 'mins', 'minute', 'minutes'],
    's': ['sec', 'secs', 'second', 'seconds'],
    'ms': ['millisecond', 'milliseconds']
}

@parser("timedelta")
def _convert_to_timedelta(value):
    """
    Return a timedelta object translating from other types if necessary.

    >>> _convert_to_timedelta(timedelta(days=5))
    datetime.timedelta(days=5)

    >>> _convert_to_timedelta(3600)
    datetime.timedelta(seconds=3600)

    >>> _convert_to_timedelta("3:30:15")
    datetime.timedelta(seconds=12615)

    >>> _convert_to_timedelta("5 days")
    datetime.timedelta(days=5)

    >>> _convert_to_timedelta("3 h")
    datetime.timedelta(seconds=10800)

    >>> _convert_to_timedelta("10 minutes")
    datetime.timedelta(seconds=600)

    >>> _convert_to_timedelta("invalid")
    Traceback (most recent call last):
    ...
    ValueError: Not a valid timedelta: invalid
    """
    if isinstance(value, datetime.timedelta):
        return value

    try:
        if isinstance(value, (int, float)):
            return datetime.timedelta(seconds=float(value))

        value = str(value).strip().lower()

        if value.endswith("s"):
            value = value[:-1]

        if ":" in value:
            parts = value.split(":")
            parts = [part.strip() for part in parts]
            if len(parts) == 3:
                hours, minutes, seconds = map(float, parts)
            elif len(parts) == 2:
                hours, minutes = map(float, parts)
                seconds = 0
            else:
                raise ValueError(f"Not a valid time representation: {value}")
            return datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds)

        if "day" in value or 'd' in value:
            days = float(value.split()[0])
            return datetime.timedelta(days=days)

        if "h" in value or 'hours' in value:
            hours = float(value.split()[0])
            return datetime.timedelta(hours=hours)

        if "minute" in value or 'm' in value:
            minutes = float(value.split()[0])
            return datetime.timedelta(minutes=minutes)

        raise ValueError(f"Not a valid timedelta: {value}")

    except (ValueError, TypeError):
        raise ValueError(f"Not a valid timedelta: {value}")


@parser("integer")
def _convert_to_int(value):
    """
    Return an int value translating from other types if necessary.

    >>> _convert_to_int(5)
    5

    >>> _convert_to_int("10")
    10

    >>> _convert_to_int("invalid")
    Traceback (most recent call last):
    ...
    ValueError: Not an integer: invalid
    """
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"Not an integer: {value}")


@parser("port",
        parent="integer",
        min=0,
        max=65535)
def _validate_port(value):
    return value


@parser("hostname", validation_regexp=r"[a-zA-Z0-9\-\.]+")
def _convert_to_hostname(value):
    """
    Return a hostname value translating from other types if necessary.

    >>> _convert_to_hostname("example.com")
    'example.com'

    >>> _convert_to_hostname(123)
    '123'

    >>> _convert_to_hostname(None)
    Traceback (most recent call last):
    ...
    ValueError: Not a hostname: None
    """
    if isinstance(value, str):
        return value
    else:
        raise ValueError(f"Not a hostname: {value}")


@parser("filename", parent="string", validation_regexp="^[\w\/\.~-]+$")
def _convert_to_filename(value, exists=False):
    normalized_path = os.path.normpath(os.path.expanduser(os.path.normcase(value)))
    if exists and not os.path.exists(normalized_path):
        raise ValueError(f"File does not exist: {normalized_path} ({value})")
    return normalized_path


@parser("protocol", parent="string", choices=["http", "https"])
def _convert_to_protocol(value):
    return value

@parser("passwordtoken", parent="string")
def _convert_to_password(value):
    # This is a low bar. We probably want more checks in the future,
    # as well as options for specific types of password.
    def entropy(password):
        p, lns = collections.Counter(password), float(len(password))
        return -sum( count/lns * math.log(count/lns, 2) for count in list(p.values()))
    if entropy(value) < 3:
        raise ValueError(f"Insecure security token {value}. Entropy: {entropy(value)}. Required: >3")
    return value

if __name__ == '__main__':
    import doctest
    doctest.testmod()

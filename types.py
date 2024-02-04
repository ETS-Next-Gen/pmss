'''
These are used to preprocess data into standardized types.
'''


import configparser
from collections import defaultdict
import doctest
from datetime import timedelta

_TYPES_DICT = defaultdict(dict)


class DictEnum:
    def __init__(self, d):
        self.d = d

    def __getattr__(self, attr):
        if attr in self.d:
            return attr
        else:
            raise ValueError("No type: ", attr)

TYPES = DictEnum(_TYPES_DICT)


def parser(type_name, validation_regexp=None):
    def inner(func):
        if validation_regexp:
            def new_func(value):
                if isinstance(value, str):
                    if not re.match(validation_regexp, value):
                        raise ValueError(f"Value '{value}' does not match the required pattern")
                return func(value)
        else:
            new_func = func

        _TYPES_DICT[type_name]['parser'] = new_func
        return new_func
    return inner


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
    if isinstance(value, timedelta):
        return value

    try:
        if isinstance(value, (int, float)):
            return timedelta(seconds=float(value))

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
            return timedelta(hours=hours, minutes=minutes, seconds=seconds)

        if "day" in value or 'd' in value:
            days = float(value.split()[0])
            return timedelta(days=days)

        if "h" in value or 'hours' in value:
            hours = float(value.split()[0])
            return timedelta(hours=hours)

        if "minute" in value or 'm' in value:
            minutes = float(value.split()[0])
            return timedelta(minutes=minutes)

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


if __name__ == '__main__':
    import doctest
    doctest.testmod()

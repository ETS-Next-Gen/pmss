# TODO: Break this into multiple files, with appropriate names.
# move to `rulesets.py` and `settings.py`
# TODO: Integrate type conversions.
from collections import defaultdict

import pmss.pmsstypes
import pmss.util

# These are deprecated. We are moving to having these in schema / default_schema.
fields = []
classes = []
attributes = []


class Schema:
    '''
    This may be more of a data structure than a class. It's not
    clear we want to add any methods onto this.

    95% of the time, we expect to be operating on `default_schema`, and
    the use-case of more than one Schema object is pretty rare. As a result,
    a simple, global, `register_field` (and friends) may make sense.
    '''
    def __init__(self, fields, classes, attributes):
        self.fields = fields
        self.classes = classes
        self.attributes = attributes


default_schema = Schema(fields=fields, classes=classes, attributes=attributes)


def register_field(
        name,
        type,
        *args,
        description=None,
        command_line_flags=None,  # Extra matching command-line flags (beyond --key)
        required=None,            # Can be a selector or a list of selectors. True is shorthand for '*'
        env=None,                 # Environment variables this can be pulled from
        default=None,
        context=None,
        schema=default_schema
):
    '''We register fields so we can show usage information, as well
    as validate the schema of the loaded file.

    All calls to this method should be completed before `validate()`.

    `context` is optional, and describes places we need to be able to
    retrieve the field from. For example, we might have a required field:

    .user_database {
       psql_port: 123;
    }

    .user_database {
       psql_port: 1234;
    }

    In this case, we'd like to be able to validate that `psql_port` is
    of the same type in both places, and available in both places, but
    we might not need a universal version.
    '''
    if required and default:
        raise ValueError(f"Required parameters shouldn't have a default! {name}")

    schema.fields.append({
        "name": name,
        "type": type,
        "command_line_flags": command_line_flags,
        "description": description,
        "required": required,
        "default": default,
        "env": env,
        "context": context
    })


def register_class(
        name,
        *args,
        command_line_flags=None,
        description=None,
        schema=default_schema
):
    '''
    For example, 'dev' and 'prod'

    This way, we can define rules such as:
    .dev {}
    .prod {}
    '''
    schema.classes.append({
        "name": name,
        "command_line_flags": command_line_flags,
        "description": description
    })


def register_attribute(
        name,
        *args,
        type,
        description=None,
        schema=default_schema
):
    '''
    For example, `'username'` would let us use a selector
    `[username=bob]`
    '''
    schema.attributes.append({
        "name": name,
        "type": type,
        "description": description
    })


register_field(
    name="verbose",
    type=pmss.pmsstypes.TYPES.boolean,
    command_line_flags=["-v", "--verbose"],
    description="Print additional debugging information.",
    default=False
)


register_field(
    name="help",
    type=pmss.pmsstypes.TYPES.boolean,
    command_line_flags=["-h", "--help"],
    description="Print help information and exit.",
    default=False
)


class ValidationError(Exception):
    pass


def validate_collisions(fields=fields):
    '''
    Make sure we don't have confusingly similar keys (e.g. API_KEY and apikey)

    To do: Make this print good error messages.
    '''
    registered_keys = set(field['name'] for field in fields)
    canonical_keys = defaultdict(list)

    for key in registered_keys:
        canonical_keys[pmss.util.canonical_key(key)].append(key)

    duplicate_keys = [keys for keys in canonical_keys.values() if len(keys) > 1]

    if duplicate_keys:
        error_message = f"Detected duplicate keys: {' : '.join('/'.join(key) for key in duplicate_keys)}"
        raise ValidationError(error_message)


def validate_no_missing_required_keys(keys):
    '''
    Make sure all required keys are there.

    To do: Check selectors versus field specification
    '''
    required_keys = set(field['name'] for field in fields if fields['required'])
    pass


def validate_no_extra_keys(keys):
    '''
    Make sure there are no extra keys.
    '''
    pass


def validate(settings):
    '''Validate all the loaded settings against added fields.

    This will:
    - Check we don't have keys with the same name (even with
      different cases).
    - Check all registered fields exist
    - Check no unregistered variables exist, unless prefixed with `_`
    - Interpolate everything
    '''
    # check that each key is accessed the same way
    available_keys = {}
    for ruleset in [settings.ruleset]:
        src_keys = ruleset.keys()
        for key in src_keys:
            cleaned = pmss.util.canonical_key(key)
            if cleaned not in available_keys:
                available_keys[cleaned] = {}
            if key not in available_keys[cleaned]:
                available_keys[cleaned][key] = set()
            available_keys[cleaned][key].add(ruleset.id())

    for value in available_keys.values():
        print(value)
        if len(value) > 1:
            keys = '\n'.join(f'  {k}: {v}' for k, v in value.items())
            error_msg = 'Different keys are being used to access the same setting. '\
                f'\n{keys}\n'\
                'Please make sure all keys use the same specification.'
            raise RuntimeError(error_msg)

    # check if any missing required fields
    available_fields = []
    for field in fields:
        cleaned = pmss.util.canonical_key(field['name'])
        available_fields.append(cleaned)
        if field['required'] and cleaned not in available_keys:
            error_msg = f'Required field `{field["name"]}` not found in available rulesets.'
            raise KeyError(error_msg)

    # check for any extra keys
    for key in available_keys:
        k = available_keys[key].popitem()[0]
        if not k.startswith('_') and key not in available_fields:
            error_msg = f'Key `{k}` is not registered as a field.'
            raise KeyError(error_msg)


if __name__ == '__main__':
    try:
        validate_collisions([{"name": "API_KEY"}, {"name": "apikey"}])
        print("FAILED TO DETECT COLLISION")
    except ValidationError as error:
        print("Correctly caught collision. ", error)

    try:
        validate_collisions([{"name": "API_KEY"}, {"name": "API_URL"}])
        print("No duplicate keys detected.")
    except ValidationError as error:
        print("INCORRECTLY CAUGHT COLLISION:", error)

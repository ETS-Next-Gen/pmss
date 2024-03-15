# TODO: Break this into multiple files, with appropriate names.
# move to `sources.py` and `settings.py`
# TODO: Integrate type conversions.

import pss.psstypes
import pss.util

fields = []
classes = []
attributes = []

def register_field(
        name,
        type,
        *args,
        description = None,
        command_line_flags = None,  # Extra matching command-line flags (beyond --key)

        required = None,  # Can be a selector or a list of selectors. True is shorthand for '*'
        env = None,  # Environment variables this can be pulled from
        default = None
):
    '''
    Fields are used to validate sources. This adds a field to the
    settings instance. All calls to this method should be completed
    before `validate()`.
    '''
    if required and default:
        raise ValueError(f"Required parameters shouldn't have a default! {name}")

    fields.append({
        "name": name,
        "type": type,
        "command_line_flags": command_line_flags,
        "description": description,
        "required": required,
        "default": default,
        "env": env
    })


def register_class(
        name,
        *args,
        command_line_flags = None,
        description = None
):
    '''
    For example, 'dev' and 'prod'

    This way, we can define rules such as:
    .dev {}
    .prod {}
    '''
    self.classes.append({
        "name": name,
        "command_line_flags": command_line_flags,
        "description": description
    })


def register_attribute(
        name,
        *args,
        type,
        description = None
):
    '''
    For example, `'username'` would let us use a selector
    `[username=bob]`
    '''
    self.attributes.append({
        "name": name,
        "type": type,
        "description": description
    })

register_field(
    name="verbose",
    type=pss.psstypes.TYPES.boolean,
    command_line_flags=["-v", "--verbose"],
    description="Print additional debugging information.",
    default=False
)


register_field(
    name="help",
    type=pss.psstypes.TYPES.boolean,
    command_line_flags=["-h", "--help"],
    description="Print help information and exit.",
    default=False
)


def validate(settings):
    '''Validate all the loaded settings against added fields.

    This will:
    - Check we don't have keys with the same name (even with
      different cases).
    - Check all registered fields exist
    - Check no unregistered variables exist, unless prefixed with `_`
    - Interpolate everything
    '''
    if not settings.loaded:
        raise RuntimeError('Please run `settings.load()` before running `settings.validation()`.')

    # check that each key is accessed the same way
    available_keys = {}
    for source in [ settings.source ]:
        src_keys = source.keys()
        for key in src_keys:
            cleaned = pss.util.canonical_key(key)
            if cleaned not in available_keys:
                available_keys[cleaned] = {}
            if key not in available_keys[cleaned]:
                available_keys[cleaned][key] = set()
            available_keys[cleaned][key].add(source.id())

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
        cleaned = pss.util.canonical_key(field['name'])
        available_fields.append(cleaned)
        if field['required'] and cleaned not in available_keys:
            error_msg = f'Required field `{field["name"]}` not found in available sources.'
            raise KeyError(error_msg)

    # check for any extra keys
    for key in available_keys:
        k = available_keys[key].popitem()[0]
        if not k.startswith('_') and key not in available_fields:
            error_msg = f'Key `{k}` is not registered as a field.'
            raise KeyError(error_msg)

    # interpolate if needed
    if settings.interpolate:
        error_msg = 'Setting interpolation is not yet implemented. '\
            'Interpolation can be a source of security concerns. '\
            'Implement and use with caution.'
        raise NotImplementedError(error_msg)

# TODO: Break this into multiple files, with appropriate names.
# move to `sources.py` and `settings.py`
# TODO: Integrate type conversions.

import pss.psstypes


def deepupdate(d, u):
    '''
    Like dict.update, but handling nested dictionaries.

    Useful for merging several `pss` heirarchies
    '''
    for k, v in u.items():
        if isinstance(v, dict):
            d[k] = deepupdate(d.get(k, {}), v)
        else:
            d[k] = v
    return d


def canonical_key(k):
    '''
    We want to avoid collisions. It's easy to confuse
    `server_port`, `serverPort`, etc. For validation, we convert keys
    to lower-case, and remove word delimieters. If there is a collision,
    we flag it.

    The format doesn't strictly disallow this, but we very much think
    this is a bad idea, so we validate for it not being there. This
    should probably be a flag.
    '''
    return k.lower().replace('-', '').replace('_', '')


fields = []


def register_field(
        name,
        type,
        command_line_flags = None,  # Extra matching command-line flags (beyond --key)
        description = None,
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


register_field(
    name="verbose",
    type=pss.psstypes.TYPES.boolean,
    command_line_flags=["-v", "--verbose"],
    description="Print additional debugging information.",
    default=False
)


if __name__ == "__main__":
    settings = Settings(prog='test_prog')

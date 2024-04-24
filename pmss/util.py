'''
Simple stand-alone utility helper functions.
'''


def deepupdate(d, u):
    '''
    Like dict.update, but handling nested dictionaries.

    Useful for merging several `pmss` heirarchies
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


def command_line_args(field):
    '''Perhaps the wrong place, but this extracts the supported ways
    to reference a field. By default, it is `--name`, but it's possible
    to override with `command_line_flags`

    '''
    return field['command_line_flags'] or ['--{name}'.format(**field)]

# TODO: Break this into multiple files, with appropriate names.
# move to `sources.py` and `settings.py`
# TODO: Integrate type conversions.
import os.path
import sys
import enum
import itertools

import pss.pathfinder
import pss.pssselectors

from pss.sources import *
import pss.psstypes

def verbose():
    return "-v" in sys.argv


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



class Settings():
    '''
    We are trying to figure out whether this should be an object, a module, or what, or how this should be broken out.
    '''
    def __init__(
            self,
            prog=sys.argv[0],    # e.g. lo
            system_name=None,    # e.g. The Learning Observer
            usage=None,          # Override the automatically-generated usage
            description=None,    # Header when generating usage
            epilog=None,         # Footer when generating usage
            sources=None,        # Where to grab config from
            exit_on_failure=True,# If true, exit and print usage. If false, raise an exception for system to handle.
            interpolate=False    # If true, allow settings like `{_foo}/bar` where `_foo` is defined elsewhere
    ):
        self.prog = prog
        self.system_name = system_name
        self.usage = usage
        self.description = description
        self.epilog = epilog
        self.exit_on_failure = exit_on_failure
        self.sources = []
        self.settings = {}
        self.loaded = False
        self.define_ordering = None
        self.interpolate = interpolate

        if not sources:
            sources = self.default_sources()

        self.add_sources(sources)

    def add_sources(self, sources):
        for source in sources:
            self.add_source(source, holdoff=True)

    def default_sources(self):
        filename = f"{self.prog}.pss"
        # TODO: Add: pss.pathfinder.package_config_file(filename)?
        source_files = [
            [SOURCE_IDS.SourceConfigFile, pss.pathfinder.source_config_file(filename)],
            [SOURCE_IDS.SystemConfigFile, pss.pathfinder.system_config_file(filename)],
            [SOURCE_IDS.UserConfigFile, pss.pathfinder.user_config_file(filename)]
        ]
        if verbose():
            print("Source files: ", source_files)
        sources = [
            ArgsSource(settings=self),
            SimpleEnvsSource(settings=self),
        ] + [ PSSFileSource(settings=self, filename=sd[1], sourceid=sd[0]) for sd in source_files if sd[1] is not None and os.path.exists(sd[1]) ]
        return sources

    def add_source(self, source, holdoff=False):
        self.sources.append(source)
        if not holdoff:
            self.load()

    def load(self):
        for source in self.sources:
            source.load()
        self.loaded = True

    def validate(self):
        '''Validate all the loaded settings against added fields.
        This will:
        - Check we don't have keys with the same name (even with
          different cases).
        - Check all registered fields exist
        - Check no unregistered variables exist, unless prefixed with `_`
        - Interpolate everything
        '''
        if not self.loaded:
            raise RuntimeError('Please run `settings.load()` before running `settings.validation()`.')

        # check that each key is accessed the same way
        available_keys = {}
        for source in self.sources:
            src_keys = source.keys()
            for key in src_keys:
                cleaned = canonical_key(key)
                if cleaned not in available_keys:
                    available_keys[cleaned] = {}
                if key not in available_keys[cleaned]:
                    available_keys[cleaned][key] = set()
                available_keys[cleaned][key].add(source.sourceid)

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
            cleaned = canonical_key(field['name'])
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
        if self.interpolate:
            error_msg = 'Setting interpolation is not yet implemented. '\
                'Interpolation can be a source of security concerns. '\
                'Implement and use with caution.'
            raise NotImplementedError(error_msg)

    def usage(self):
        pass

    def get(self, key, context=None, default=None):
        if context is None:
            context = pss.pssselectors.UniversalSelector()
        best_matches = []
        for source in self.sources:
            l = source.query(key, context)
            if not l:
                continue
            # sort list based on selector priority to get best match
            l = sorted(l, key=lambda x: pss.pssselectors.css_selector_key(x[0]))
            best_local_match = l[0]
            best_matches.append((source.sourceid, best_local_match))
            if self.define_ordering is None:
                # If we have no defined order, so we return the best
                # match from the first available source.
                break

        if len(best_matches) == 0:
            return default

        if self.define_ordering is not None:
            # TODO reorder the best local matches from each source
            # based the `defined_ordering`.
            pass
        best_match = best_matches[0][1]
        # find the matching field so we know how to parse
        for field in fields:
            if field["name"] == key:
                field_type = field['type']
        return pss.psstypes.parse(best_match[1], field_type)

    def __getattr__(self, key):
        '''
        Enum-style access to fields.
        '''
        for field in fields:
            if field["name"] == key:
                return self.get(key)

        raise ValueError(f"Invalid Key: {key}")

    def __dir__(self):
        return sorted(set([field["name"] for field in fields]))

    def __hasattr__(self, key):
        return key in dir(self)

    def debug_dump(self):
        return {source.id(): source.debug_dump() for source in self.sources}


register_field(
    name="verbose",
    type=pss.psstypes.TYPES.boolean,
    command_line_flags=["-v", "--verbose"],
    description="Print additional debugging information.",
    default=False
)


if __name__ == "__main__":
    settings = Settings(prog='test_prog')

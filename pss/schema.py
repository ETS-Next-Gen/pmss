# TODO: Break this into multiple files, with appropriate names.
# move to `sources.py` and `settings.py`
# TODO: Integrate type conversions.
import os.path
import sys
import enum
import itertools

import pss.psstypes
import pss.pathfinder
import pss.loadfile
import pss.pssselectors
#import pss.sources

def deepupdate(d, u):
    '''
    Like dict.update, but handling nested dictionaries.
    '''
    for k, v in u.items():
        if isinstance(v, dict):
            d[k] = deepupdate(d.get(k, {}), v)
        else:
            d[k] = v
    return d

SOURCE_IDS = enum.Enum('SOURCE_IDS', ['ENV', 'SourceConfigFile', 'SystemConfigFile', 'UserConfigFile', 'EnvironmentVariables', 'CommandLineArgs'])

class Source():
    def __init__(self, settings, sourceid):
        self.loaded = False
        self.settings = settings
        self.sourceid = sourceid

    def load(self):
        '''Load settings into your source component.
        Upon successful load, set `self.loaded = True`.
        '''
        raise NotImplementedError('This should always be called on a subclass')

    def query(self, *args, **kwargs):
        '''This method should return list of matching selectors
        where each item in the list is `(selector, value)` pair.
        Additionally these methods should check that the data
        is loaded with `self.loaded` before trying to query data.
        '''
        raise NotImplementedError('This should always be called on a subclass')

    def keys(self):
        '''This method should return a list of all
        available keys in the source.
        '''
        raise NotImplementedError('This should always be called on a subclass')

class PSSFileSource(Source):
    def __init__(self, settings, filename, sourceid=None):
        super().__init__(settings=settings, sourceid=sourceid)
        self.filename = filename
        self.results = {}

    def load(self):
        self.results = pss.loadfile.load_pss_file(self.filename)
        self.loaded = True

    def query(self, key, context):
        if not self.loaded:
            raise RuntimeError(f'Please `load()` data from source `{self.sourceid} before trying to `query()`.')
        selector_dict = self.results.get(key)
        return_list = []
        for selector, value in selector_dict.items():
            # FIXME this code is broken as the context is not
            # a mappable object when using the `UniversalSelector`
            params = {} if isinstance(context, pss.pssselectors.UniversalSelector) else context
            if selector.match(**params):
                return_list.append([selector, value])
        return return_list

    def keys(self):
        return self.results.keys()

class SimpleEnvsSource(Source):
    '''
    Note that, for now, we do not permit selectors in environment
    variables (for now), since per IEEE Std 1003.1-2001, environment
    variables consist solely of uppercase letters, digits, and the '_'
    (underscore) and do not begin with a digit.

    In the future, we could make a ComplexEnvsSource where the
    selector is included in the value or encoded in some way. The
    future is not today.

    TODO:
    * Handle case sensitivity cleanly
    * Handle default
    '''
    def __init__(
            self,
            settings,
            sourceid=SOURCE_IDS.EnvironmentVariables,
            env=os.environ,
            default_keys=True  # Do we assume all environment variables may be keys?
    ):
        super().__init__(settings=settings, sourceid=sourceid)
        self.extracted = {}
        self.default_keys=default_keys
        self.env = env

    def load(self):
        if self.default_keys:
            possible_keys = [k.upper() for k in dir(self.settings)]

            for key in self.env:
                if key in possible_keys:
                    self.extracted[key] = self.env[key]
        mapped_keys = dict([(f['env'], f['name']) for f in self.settings.fields if f['env']])
        for key in self.env:
            if key in mapped_keys:
                self.extracted[mapped_keys[key].upper()] = self.env[key]
        self.loaded = True

    def query(self, key, context):
        if not self.loaded:
            raise RuntimeError(f'Please `load()` data from source `{self.sourceid} before trying to `query()`.')
        if key.upper() in self.extracted:
            return [[pss.pssselectors.UniversalSelector(), key]]

        return False

    def keys(self):
        return self.extracted.keys()


def group_arguments(args):
    '''
    Example
    ```python
    ['-x', 'y', 'z', '--a', '--b=c', '--d', 'e f']          # arguments
    [['-x', 'y', 'z'], ['--a'], ['--b=c'], ['--d', 'e f']]  # output
    ```
    '''
    def make_make_key():
        key_index = 1
        def make_key(arg):
            nonlocal key_index
            if arg.startswith('-'):
                key_index = arg
            return key_index
        return make_key

    # We probably just want to return the groupby, but this is for backwards-compatibility. 
    return itertools.groupby(args, make_make_key())


class ArgsSource(Source):
    # --foo=bar
    # --selector:foo=bar
    # --dev (enable class dev, if registered as one of the classes which can be enabled / disabled via commandline)
    def __init__(self, settings, sourceid=SOURCE_IDS.CommandLineArgs, argv=sys.argv):
        super().__init__(settings=settings, sourceid=sourceid)
        self.argv = argv
        self.results = {}

    def load(self):
        '''Manually parse command line arguments.
        This allows us to eventually support the use
        of selectors in command line arguments.

        The args are parsed in 2 steps:
        1. Group the arguments into a list of lists
        where each inner list contains all information
        for a single argument.


        2. Parse each argument
        {x: ['y', 'z'], a: True, b: 'c', 'd': 'e f'}
        '''
        # group arguments together
        args = self.argv[1:]
        grouped_args = group_arguments(args)

        # parse grouped args into results
        for k, garg in grouped_args:
            garg=list(garg)
            print(k, garg)
            flag_split = garg[0].split('=')
            flag = flag_split[0]
            # TODO check if ':' in flag to parse selector
            selector = pss.pssselectors.UniversalSelector()
            name = None
            value = None
            for field in self.settings.fields:
                if flag in (field['command_line_flags'] or ['--{name}'.format(**field)]):
                    name = field['name']
                    if len(flag_split) > 1:
                        value = flag_split[1]
                        break
                    if field['type'] == pss.psstypes.TYPES.boolean:
                        value = True
                        break
                    value = garg[1:] if len(garg) > 2 else garg[1:][0]
                    # check if field is required or set default
                    if value is None and field['required']:
                        raise RuntimeError(f'Field `{name}` required, but no value provided.')
                    elif value is None:
                        value = field['default']

                    break
            if name is None:
                raise RuntimeError(f'Could not locate field with flag `{flag}`.')
            if name not in self.results:
                self.results[name] = {}
            self.results[name][selector] = value
        self.loaded = True

    def query(self, key, context):
        '''The internal `results` have the same structure as PSSSource,
        so the `self.query` is identical.
        '''
        if not self.loaded:
            raise RuntimeError(f'Please `load()` data from source `{self.sourceid} before trying to `query()`.')
        selector_dict = self.results.get(key, {})
        return_list = []
        for selector, value in selector_dict.items():
            # FIXME this code is broken as the context is not
            # a mappable object when using the `UniversalSelector`
            params = {} if isinstance(context, pss.pssselectors.UniversalSelector) else context
            if selector.match(**params):
                return_list.append([selector, value])
        return return_list

    def keys(self):
        return self.results.keys()

class SQLiteSource(Source):
    pass


# We roughly follow:
#   https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser

class Settings():
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
        self.fields = []
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
        sources = [
            ArgsSource(settings=self),
            SimpleEnvsSource(settings=self),
        ] + [ PSSFileSource(settings=self, filename=sd[1], sourceid=sd[0]) for sd in source_files if sd[1] is not None and os.path.exists(sd[1]) ]
        return sources

    def register_field(
            self,
            name,
            type,
            command_line_flags = None,  # Extra matching command-line flags (beyond --key)
            description = None,
            required = None,  # Can be a selector or a list of selectors. True is shorthand for '*'
            env = None,  # Environment variables this can be pulled from
            default = None
    ):
        '''Fields are used to validate sources. This adds a
        field to the settings instance. This method should be
        called before `self.validate()`.
        '''
        if required and default:
            raise ValueError(f"Required parameters shouldn't have a default! {name}")

        self.fields.append({
            "name": name,
            "type": type,
            "command_line_flags": command_line_flags,
            "description": description,
            "required": required,
            "default": default,
            "env": env
        })

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

        def clean_key(k):
            return k.lower().replace('-', '').replace('_', '')

        # check that each key is accessed the same way
        available_keys = {}
        for source in self.sources:
            src_keys = source.keys()
            for key in src_keys:
                cleaned = clean_key(key)
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
        for field in self.fields:
            cleaned = clean_key(field['name'])
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
            l = sorted(l, key=lambda x: pss.pssselectors.simple_selector_sort_key(x[0]))
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
        for field in self.fields:
            if field["name"] == key:
                field_type = field['type']
        return pss.psstypes.parse(best_match[1], field_type)

    def __getattr__(self, key):
        '''
        Enum-style access to fields.
        '''
        for field in self.fields:
            if field["name"] == key:
                return self.get(key)

        raise ValueError(f"Invalid Key: {key}")

    def __dir__(self):
        return sorted(set([field["name"] for field in self.fields]))

    def __hasattr__(self, key):
        return key in dir(self)


if __name__ == "__main__":
    settings = Settings(prog='test_prog')
    settings.register_field('test_field', str, command_line_flags=['-t', '--test'], description='Test Field Description')

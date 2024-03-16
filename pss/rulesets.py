import enum
import itertools
import os
import sys

import pss.pssselectors
import pss.loadfile

SOURCE_IDS = enum.Enum('SOURCE_IDS', ['ENV', 'SourceConfigFile', 'SystemConfigFile', 'UserConfigFile', 'EnvironmentVariables', 'CommandLineArgs'])


def _convert_keys_to_str(d):
    '''
    {'ArgsSource': {'hostname': {<UniversalSelector *>: 'bar'}}, 'SimpleEnvsSource': {}}
    to
    {'ArgsSource': {'hostname': {'*': 'bar'}}, 'SimpleEnvsSource': {}}
}

    '''
    if isinstance(d, dict):
        return {str(k): _convert_keys_to_str(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [_convert_keys_to_str(i) for i in d]
    else:
        return d


class Source():
    def __init__(self, schema, sourceid):
        self.loaded = False
        self.schema = schema
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

    def id(self):
        return type(self).__name__

    def debug_dump(self):
        return "[borked]"


class PSSFileSource(Source):
    def __init__(self, schema, filename, sourceid=None):
        super().__init__(schema=schema, sourceid=sourceid)
        self.filename = filename
        self.results = {}

    def load(self):
        self.results = pss.loadfile.load_pss_file(self.filename, provenance=self.id())
        self.loaded = True

    def query(self, key, context):
        if not self.loaded:
            raise RuntimeError(f'Please `load()` data from source `{self.sourceid} before trying to `query()`.')
        selector_dict = self.results.get(key)
        # Item not in PSS file
        if selector_dict is None:
            return []
        return_list = []
        for selector, value in selector_dict.items():
            if selector.match(**context):
                return_list.append([selector, value])
        return return_list

    def keys(self):
        return self.results.keys()

    def id(self):
        if self.sourceid:
            return self.sourceid
        else:
            return f"{super().id()}:{self.filename}"

    def debug_dump(self):
        return self.results

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
            schema,
            sourceid=SOURCE_IDS.EnvironmentVariables,
            env=os.environ,
            default_keys=True  # Do we assume all environment variables may be keys?
    ):
        super().__init__(schema=schema, sourceid=sourceid)
        self.extracted = {}
        self.default_keys=default_keys
        self.env = env

    def load(self):
        if self.default_keys:
            possible_keys = [k.upper() for k in dir(self.schema)]

            for key in self.env:
                if key in possible_keys:
                    self.extracted[key] = self.env[key]
        mapped_keys = dict([(f['env'], f['name']) for f in pss.schema.fields if f['env']])
        for key in self.env:
            if key in mapped_keys:
                self.extracted[mapped_keys[key].upper()] = self.env[key]
        self.loaded = True

    def query(self, key, context):
        if not self.loaded:
            raise RuntimeError(f'Please `load()` data from source `{self.sourceid} before trying to `query()`.')
        if key.upper() in self.extracted:
            return [[pss.pssselectors.UniversalSelector(provenance=self.id()), key]]

        return False

    def keys(self):
        return self.extracted.keys()

    def id(self):
        return "SimpleEnvsSource"

    def debug_dump(self):
        return _convert_keys_to_str(self.extracted)


def _group_arguments(args):
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


# We roughly follow:
#   https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser
class ArgsSource(Source):
    # --foo=bar
    # --selector:foo=bar
    # --dev (enable class dev, if registered as one of the classes which can be enabled / disabled via commandline)
    def __init__(self, schema, sourceid=SOURCE_IDS.CommandLineArgs, argv=sys.argv):
        super().__init__(schema=schema, sourceid=sourceid)
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
        grouped_args = _group_arguments(args)

        # parse grouped args into results
        for k, garg in grouped_args:
            garg=list(garg)
            print(k, garg)
            flag_split = garg[0].split('=')
            flag = flag_split[0]
            # TODO check if ':' in flag to parse selector
            selector = pss.pssselectors.UniversalSelector(provenance=self.id())
            name = None
            value = None
            for field in pss.schema.fields:
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
            if selector.match(**context):
                return_list.append([selector, value])
        return return_list

    def keys(self):
        return self.results.keys()

    def debug_dump(self):
        return _convert_keys_to_str(self.results)


class SQLiteSource(Source):
    pass


class CombinedSource(Source):
    def __init__(self, sources):
        self.sources = sources

    def add_sources(self, sources):
        for source in sources:
            self.add_source(source, holdoff=True)

    def add_source(self, source, holdoff=False):
        self.sources.append(source)
        if not holdoff:
            self.load()

    def load(self):
        for source in self.sources:
            source.load()
        self.loaded = True

    def keys(self):
        keys_set = set()
        for source in self.sources:
            keys_set.update(source.keys())
        return list(keys_set)

    def query(self, key, context=None):
        '''
        We don't want this. We want query(). But we are mid-refactor.
        '''
        if context is None:
            context = {}
        best_matches = []
        for source in self.sources:
            l = source.query(key, context)
            if not l:
                continue
            # sort list based on selector priority to get best match
            l = sorted(l, key=lambda x: pss.pssselectors.css_selector_key(x[0]))
            best_local_match = l[0]
            best_matches.append((source.sourceid, best_local_match))
            break

        if len(best_matches) == 0:
            return None

        best_match = best_matches[0][1]
        # find the matching field so we know how to parse
        for field in pss.schema.fields:
            if field["name"] == key:
                field_type = field['type']
        return pss.psstypes.parse(best_match[1], field_type)

    def debug_dump(self):
        return { source.id(): source.debug_dump() for source in self.sources }
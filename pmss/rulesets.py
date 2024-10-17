'''
This implements loaders for rule sets from diverse sources. Note that
while PMSS is the "native" format, it is possible to write loaders for
e.g. INI files and other formats. This makes sense to do so projects
can have a smooth transition if they choose to adopt PMSS, with full
backwards-compatibility.
'''

import collections
import enum
import errno
import itertools
import os
import sys
import traceback
import yaml

import pmss.pmssselectors
import pmss.loadfile

from pmss.util import command_line_args

RULESET_IDS = enum.Enum('RULESET_IDS', ['ENV', 'SourceConfigFile', 'SystemConfigFile', 'UserConfigFile', 'EnvironmentVariables', 'CommandLineArgs'])


def _convert_keys_to_str(d):
    '''
    {'ArgsRuleset': {'hostname': {<UniversalSelector *>: 'bar'}}, 'SimpleEnvsRuleset': {}}
    to
    {'ArgsRuleset': {'hostname': {'*': 'bar'}}, 'SimpleEnvsRuleset': {}}
}

    '''
    if isinstance(d, dict):
        return {str(k): _convert_keys_to_str(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [_convert_keys_to_str(i) for i in d]
    else:
        return d


class Ruleset():
    def __init__(self, rulesetid):
        self.loaded = False
        self.rulesetid = rulesetid

    def load(self):
        '''Load settings into your ruleset component.
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
        available keys in the ruleset.
        '''
        raise NotImplementedError('This should always be called on a subclass')

    def id(self):
        return type(self).__name__

    def debug_dump(self):
        '''
        This should never be called directly.
        '''
        return f"[borked / {self.id()}]"


class FileRuleset(Ruleset):
    def __init__(self, filename, rulesetid=None, watch=False):
        super().__init__(rulesetid=rulesetid)
        self.filename = filename
        self.timestamp = None
        self.results = {}
        self.watch = watch
        if not os.path.isfile(filename):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), pathname)

    def check_changes(self):
        if not self.watch:
            return
        if self.timestamp != os.stat(self.filename).st_mtime:
            try:
                self.load()
            except:
                print("Could not reload PMSS file.")
                print("This probably means there was a syntax error in the file.")
                print("Continuing with the old file")
                print("Error:")
                print(traceback.format_exc())

    def query(self, key, context):
        self.check_changes()
        if not self.loaded:
            raise RuntimeError(f'Please `load()` data from ruleset `{self.rulesetid} before trying to `query()`.')
        selector_dict = self.results.get(key)
        # Item not in PMSS file
        if selector_dict is None:
            return []
        return_list = []
        for selector, value in selector_dict.items():
            if selector.match(**context):
                return_list.append([selector, value])
        return return_list

    def keys(self):
        self.check_changes()
        return self.results.keys()

    def id(self):
        if self.rulesetid:
            return self.rulesetid
        else:
            return f"{super().id()}:{self.filename}"

    def debug_dump(self):
        return self.results

class PMSSFileRuleset(FileRuleset):
    def load(self):
        self.timestamp = os.stat(self.filename).st_mtime
        self.results = pmss.loadfile.load_pmss_file(self.filename, provenance=self.id())
        self.loaded = True


class YAMLFileRuleset(FileRuleset):
    '''
    This is to read old-school creds.yaml in Learning
    Observer. Not clear if this belongs here or in Learning
    Observer. It depends on whether we can make this generic.
    '''
    def recurse(self, keys, key, value):
        '''
        '''
        if isinstance(value, dict):
            for k in value:
                self.recurse(keys+[key] if key else keys, k, value[k])
        else:
            selectors = [pmss.pmssselectors.TypeSelector(k, provenance=self.id()) for k in keys]
            selector = pmss.pmssselectors.CompoundSelector(selectors, provenance=self.id())
            self.results[key][selector] = value

    def load(self):
        self.timestamp = os.stat(self.filename).st_mtime
        with open(self.filename, 'r') as f:
            settings = yaml.safe_load(f)

        self.results = collections.defaultdict(dict)
        self.recurse([], None, settings)
        self.results = dict(self.results)
        self.loaded = True


class SimpleEnvsRuleset(Ruleset):
    '''
    Note that, for now, we do not permit selectors in environment
    variables (for now), since per IEEE Std 1003.1-2001, environment
    variables consist solely of uppercase letters, digits, and the '_'
    (underscore) and do not begin with a digit.

    In the future, we could make a ComplexEnvsRuleset where the
    selector is included in the value or encoded in some way. The
    future is not today.

    TODO:
    * Handle case sensitivity cleanly
    * Handle default
    '''
    def __init__(
            self,
            rulesetid=RULESET_IDS.EnvironmentVariables,
            env=os.environ,
            default_keys=True  # Do we assume all environment variables may be keys?
    ):
        super().__init__(rulesetid=rulesetid)
        self.extracted = {}
        self.default_keys = default_keys
        self.env = env

    def load(self):
        if self.default_keys:
            possible_keys = [k.upper() for k in set([field["name"] for field in pmss.schema.fields])]

            for key in self.env:
                if key in possible_keys:
                    self.extracted[key] = self.env[key]
        mapped_keys = dict([(f['env'], f['name']) for f in pmss.schema.fields if f['env']])
        for key in self.env:
            if key in mapped_keys:
                self.extracted[mapped_keys[key].upper()] = self.env[key]
        self.loaded = True

    def query(self, key, context):
        if not self.loaded:
            raise RuntimeError(f'Please `load()` data from ruleset `{self.rulesetid} before trying to `query()`.')
        if key.upper() in self.extracted:
            return [[pmss.pmssselectors.UniversalSelector(provenance=self.id()), key]]

        return False

    def keys(self):
        return self.extracted.keys()

    def id(self):
        return "SimpleEnvsRuleset"

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
class ArgsRuleset(Ruleset):
    # --foo=bar
    # --selector:foo=bar
    # --dev (enable class dev, if registered as one of the classes which can be enabled / disabled via commandline)
    def __init__(self, rulesetid=RULESET_IDS.CommandLineArgs, argv=sys.argv):
        super().__init__(rulesetid=rulesetid)
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
            garg = list(garg)
            print(k, garg)
            flag_split = garg[0].split('=')
            flag = flag_split[0]
            # TODO check if ':' in flag to parse selector
            selector = pmss.pmssselectors.UniversalSelector(provenance=self.id())
            name = None
            value = None
            for field in pmss.schema.fields:
                if flag in command_line_args(field):
                    name = field['name']
                    if len(flag_split) > 1:
                        value = flag_split[1]
                        break
                    if field['type'] == pmss.pmsstypes.TYPES.boolean:
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
        '''The internal `results` have the same structure as PMSSRuleset,
        so the `self.query` is identical.
        '''
        if not self.loaded:
            raise RuntimeError(f'Please `load()` data from ruleset `{self.rulesetid} before trying to `query()`.')
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


class SQLiteRuleset(Ruleset):
    pass


id_counter = 0


class CombinedRuleset(Ruleset):
    def __init__(self, rulesets, id=None):
        global id_counter
        self.rulesets = rulesets
        if id is None:
            self.rulesetid = f"{super().id()}:{id_counter}"
            id_counter = id_counter+1
        else:
            self.rulesetid = id

    def id(self):
        return self.rulesetid

    def add_rulesets(self, rulesets):
        for ruleset in rulesets:
            self.add_ruleset(ruleset, holdoff=True)

    def add_ruleset(self, ruleset, holdoff=False):
        self.rulesets.append(ruleset)
        if not holdoff:
            self.load()
        return ruleset.id()

    def delete_ruleset(self, id):
        for ruleset in self.rulesets:
            if ruleset.id() == id:
                self.rulesets.remove(ruleset)
                return id
        raise KeyError("Ruleset not found")

    def load(self):
        for ruleset in self.rulesets:
            ruleset.load()
        self.loaded = True

    def keys(self):
        keys_set = set()
        for ruleset in self.rulesets:
            keys_set.update(ruleset.keys())
        return list(keys_set)

    def query(self, key, context=None):
        '''
        We don't want this. We want query(). But we are mid-refactor.
        '''
        if context is None:
            context = {}
        best_matches = []
        for ruleset in self.rulesets:
            subquery = ruleset.query(key, context)
            if not subquery:
                continue
            # sort list based on selector priority to get best match
            subquery = sorted(subquery, key=lambda x: pmss.pmssselectors.css_selector_key(x[0]))
            best_local_match = subquery[0]
            best_matches.append((ruleset.rulesetid, best_local_match))
            break
        # Find the matching field so we know how to parse
        for field in pmss.schema.fields:
            if field["name"] == key:
                field_type = field['type']
                break
        if len(best_matches) == 0:
            # No matches, grab the field's default.
            best_match = field.get('default', None)
        else:
            # Here's what we are indexing into:
            # [0] grab the first item (best match)
            # [1] get the match (index 0 at this layer is the rulesetid)
            # [1] get the value (index 0 at this layer is the selector)
            best_match = best_matches[0][1][1]

        # Sometimes it makes sense to default to None which conflicts
        # with the specified data type. For example, ports should
        # be integers, but if a port is not specified, we may want
        # to manually go find one instead. I'm not sure the correct
        # layer of abstraction to make this.
        try:
            return pmss.pmsstypes.parse(best_match, field_type)
        except Exception as e:
            raise ValueError(f'Unable to parse value for key `{key}`. See above exception for more details.') from e

    def debug_dump(self):
        return {ruleset.id(): ruleset.debug_dump() for ruleset in self.rulesets}

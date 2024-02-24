import os.path
import sys

import pss.psstypes
import pss.pathfinder
import pss.loadfile
#import pss.sources

def deep_update(d, u):
    '''
    Like dict.update, but handling nested dictionaries.
    '''
    for k, v in u.items():
        if isinstance(v, dict):
            d[k] = deep_update(d.get(k, {}), v)
        else:
            d[k] = v
    return d


class Source():
    def __init__(self, settings):
        self.loaded = False
        self.settings = settings

class PSSFileSource(Source):
    def __init__(self, settings, filename):
        super().__init__(settings)
        self.filename = filename
        self.results = pss.loadfile.load_pss_file(filename)

class EnvsSource(Source):
    pass

class ArgsSource(Source):
    pass

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
            exit_on_failure=True # If true, exit and print usage. If false, raise an exception for system to handle.
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

        if not sources:
            sources = self.default_sources()

        self.add_sources(sources)

    def add_sources(self, sources):
        pass

    def default_sources(self):
        filename = f"{self.prog}.pss"
        source_files = [
            pss.pathfinder.relative_config_file(filename),
            # TODO: Add: pss.pathfinder.package_config_file(filename),
            pss.pathfinder.system_config_file(filename),
            pss.pathfinder.user_config_file(filename)
        ]
        sources = [
            ArgsSource(self),
            EnvsSource(self),
        ] + [ PSSFileSource(self, fn) for fn in source_files if fn is not None and os.path.exists(fn) ]
        return sources


    def register_field(
            self,
            name,
            type,
            command_line_flags = [],
            description = None,
            required = None,  # Can be a selector or a list of selectors. True is shorthand for '*'
            default = None
    ):
        if required and default:
            raise ValueError(f"Required parameters shouldn't have a default! {name}")

        self.fields.append({
            "name": name,
            "type": type,
            "command_line_flags": command_line_flags,
            "description": description,
            "required": required,
            "default": default
        })

    def add_source(self, source, holdoff=False):
        # Implementation of add_source method would go here
        self.sources.append(source)
        if not holdoff:
            self.load()

    def load(self):
        for source in self.sources:
            source.load()

    def validate(self):
        '''
        '''
        pass

    def usage(self):
        pass

    def get(self, selector, key, default=None):
        pass

    def __getattr__(self, key):
        '''
        Enum-style access to fields.
        '''
        for field in self.fields:
            if field["name"] == key:
                return key

        raise ValueError(f"Invalid Key: {key}")

    def __dir__(self):
        return sorted(set([field["name"] for field in self.fields]))

    def __hasattr__(self, key):
        return key in dir(self)

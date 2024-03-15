import os.path
import sys
import enum
import itertools

import pss.pathfinder
import pss.pssselectors
import pss.schema
import pss.sources

from pss.sources import *


def verbose():
    return "-v" in sys.argv


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
        self.settings = {}
        self.loaded = False
        self.define_ordering = None
        self.interpolate = interpolate
        if sources is None:
            sources = self.default_sources()
        self.source = CombinedSource(sources)

    def load(self):
        self.source.load()
        self.loaded = True

    def usage(self):
        pass

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

    def get(self, key, context=None, default=None):
        return self.source.get(key, context, default)

    def __getattr__(self, key):
        '''
        Enum-style access to pss.schema.fields.
        '''
        for field in pss.schema.fields:
            if field["name"] == key:
                return self.get(key)

        raise ValueError(f"Invalid Key: {key}")

    def __dir__(self):
        return sorted(set([field["name"] for field in pss.schema.fields]))

    def __hasattr__(self, key):
        return key in dir(self)

    def debug_dump(self):
        return self.source.debug_dump()

import os.path
import sys
import enum

import pss.psstypes
import pss.pathfinder
import pss.loadfile
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

    def query(self, *args, **kwargs):
        raise UnimplementedError("This should always be called on a subclass")


class PSSFileSource(Source):
    def __init__(self, settings, filename, sourceid=None):
        super().__init__(settings=settings, sourceid=sourceid)
        self.filename = filename
        self.results = pss.loadfile.load_pss_file(filename)

    def query(self, key, context):
        selector_list = self.results.get(key)
        return_list = []
        for selector, value in selector_list:
            if selector.match(**context):
                return_list.append([selector, value])
        return return_list


class EnvsSource(Source):
    def __init__(self, settings, sourceid=SOURCE_IDS.EnvironmentVariables, env=os.environ):
        super().__init__(settings=settings, sourceid=sourceid)

    def query(self, key, context):
        return False

class ArgsSource(Source):
    def __init__(self, settings, sourceid=SOURCE_IDS.CommandLineArgs, argv=sys.argv):
        super().__init__(settings=settings, sourceid=sourceid)
        self.argv = argv

    def load(self):
        for argument in self.argv[1:]:
            if "=" in argument:
                pass

    def query(self, key, context):
        return False

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
        # TODO: Add: pss.pathfinder.package_config_file(filename)?
        source_files = [
            [SOURCE_IDS.SourceConfigFile, pss.pathfinder.source_config_file(filename)],
            [SOURCE_IDS.SystemConfigFile, pss.pathfinder.system_config_file(filename)],
            [SOURCE_IDS.UserConfigFile, pss.pathfinder.user_config_file(filename)]
        ]
        sources = [
            ArgsSource(settings=self),
            EnvsSource(settings=self),
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

    def get(self, key, context, default=None):
        for source in sources:
            l = source.get(key, context)
            if l:  # TODO: Pick best march
                return l  # TODO: Convert to propert type

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


if __name__ == "__main__":
    settings = Settings(prog='test_prog')
    settings.register_field('test_field', str, command_line_flags=['-t', '--test'], description='Test Field Description')

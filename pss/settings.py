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
            sources=None
    ):
        if sources is None:
            sources = pss.functional.default_sources(self)
        self.source = CombinedSource(sources)
        self.source.load()

    def get(self, key, id=None, types=[], classes=[], attributes={}, default=None):
        results = self.source.query(key, {
            "id": id,
            "types": types,
            "classes": classes,
            "attributes": attributes
        })
        if results is None:
            return default
        return results

    def __getattr__(self, key):
        '''
        Enum-style access to pss.schema.fields.
        '''
        for field in pss.schema.fields:
            if field["name"] == key:
                def getter(**kwargs):
                    return self.get(key, **kwargs)
                return getter

        raise ValueError(f"Invalid Key: {key}")

    def __dir__(self):
        return sorted(set([field["name"] for field in pss.schema.fields]))

    def __hasattr__(self, key):
        return key in dir(self)

    def debug_dump(self):
        return self.source.debug_dump()

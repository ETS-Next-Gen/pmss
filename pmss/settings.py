'''
TODO: We'd like `pmss.settings` to be `pmss.functional.settings`,
for which we need to rename this file.
'''

import os.path
import sys
import enum
import itertools

import pmss.pathfinder
import pmss.pmssselectors
import pmss.schema
import pmss.rulesets

from pmss.rulesets import *


def verbose():
    return "-v" in sys.argv


class Settings():
    '''
    This is a helper class which makes it easy and type-safe to
    query the settings.

    For example, if we would like to query a setting called `verbose`,
    we can use `settings.verbose()`

    Note that this is not `settings.verbose` since:

    1. We can pass parameters if we have e.g. specific classes, ids, attributes, etc.
    2. We want to be explicit that this might e.g. query a setting database

    We probably want also want an `async_settings` object for use in
    asynchronous code in the future.
    '''
    def __init__(
            self,
            rulesets=None
    ):
        if rulesets is None:
            rulesets = pmss.functional.default_rulesets(self)
        self.ruleset = CombinedRuleset(rulesets)
        self.ruleset.load()

    def get(self, key, *args, id=None, types=[], classes=[], attributes={}, default=None):
        results = self.ruleset.query(key, {
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
        Enum-style access to pmss.schema.fields.
        '''
        for field in pmss.schema.fields:
            if field["name"] == key:
                def getter(**kwargs):
                    return self.get(key, **kwargs)
                return getter

        raise ValueError(f"Invalid Key: {key}")

    def __dir__(self):
        return sorted(set([field["name"] for field in pmss.schema.fields]))

    def __hasattr__(self, key):
        return key in dir(self)

    def debug_dump(self):
        return self.ruleset.debug_dump()

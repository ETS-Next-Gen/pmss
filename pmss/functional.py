import os
import sys

import pmss.pathfinder
import pmss.settings
import pmss.rulesets
import pmss.pretty_usage

from pmss.util import command_line_args


def verbose():
    return "-v" in sys.argv


def help():
    return "-h" in sys.argv


_prog = sys.argv[0]
_system_name = None
_usage = None
_description = None
_epilog = None
_rulesets = None
_exit_on_failure = True
_interpolate = False

initialized = False

settings = None


def init(
    prog=_prog,
    system_name=_system_name,
    usage=_usage,
    description=_description,
    epilog=_epilog,
    rulesets=_rulesets,
    exit_on_failure=_exit_on_failure,
    interpolate=_interpolate
):
    global _prog, _system_name, _usage, _description, _epilog
    global _rulesets, _exit_on_failure, _interpolate, settings
    _prog = prog
    _system_name = system_name
    _usage = usage
    _description = description
    _epilog = epilog
    _exit_on_failure = exit_on_failure

    if(interpolate):
        raise NotImplementedError(
            'Setting interpolation is not yet implemented. \n'
            'Interpolation can be a source of security concerns. \n'
            'Implement and use with caution.'
        )

    _interpolate = interpolate
    _rulesets = rulesets

    initialized = True
    if settings is None:
        settings = pmss.settings.Settings(rulesets=rulesets)
    else:
        print("Settings already initialized. Check if init isn't being called twice.")

    return settings


def default_rulesets(settings):
    filename = f"{_prog}.pmss"
    # TODO: Add: pmss.pathfinder.package_config_file(filename)?
    ruleset_files = [
        [pmss.rulesets.RULESET_IDS.SourceConfigFile, pmss.pathfinder.source_config_file(filename)],
        [pmss.rulesets.RULESET_IDS.SystemConfigFile, pmss.pathfinder.system_config_file(filename)],
        [pmss.rulesets.RULESET_IDS.UserConfigFile, pmss.pathfinder.user_config_file(filename)]
    ]
    file_rulesets = [
        pmss.rulesets.PMSSFileRuleset(filename=sd[1], rulesetid=sd[0])
        for sd in ruleset_files
        if sd[1] is not None and os.path.exists(sd[1])
    ]
    if verbose():
        print("Ruleset files: ", ruleset_files)
    rulesets = [
        pmss.rulesets.ArgsRuleset(),
        pmss.rulesets.SimpleEnvsRuleset(),
    ] + file_rulesets
    return rulesets


def usage(schema=pmss.schema.default_schema):
    '''
    TODO:
    * Also needs classes and other types of command line parameters
    * Should provide example, default (if any), type, etc.
    '''
    parameters = [
        (", ".join(command_line_args(f)), f['description']) for f in schema.fields
    ]
    print(parameters)
    pmss.pretty_usage.pretty_usage(_prog, _description, parameters, _epilog)


def register_ruleset(ruleset):
    return settings.ruleset.add_ruleset(ruleset)


def delete_ruleset(ruleset_id):
    return settings.ruleset.delete_ruleset(ruleset_id)

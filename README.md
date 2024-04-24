Preference Management Style Sheets
===

This is intended as a language for settings. The name might be a placeholder. Or final. Who knows?

![XKCD Standards Comic](https://imgs.xkcd.com/comics/standards.png)

Why? WHY???
-----------

The *raison d'etre* is that settings cascade and override. In most cases, we would like to have (e.g. for a learning management system):

- Rosters from Google Classroom
- Except for Central Valley School District, which uses Instructure
- Except for Maplewood Elementary School, which uses Canvas
- Except for Mrs. Johnson's afterschool program, which keeps rosters in a Google Spreadsheet, by virtue of excepting the general community and not just district students.

We'd also like to have:

- System defaults
- Overridden by system settings in `/etc/foo`
- Overridden by user settings in `~/.foo`
- Overridden by environment variables
- Overridden by settings in a database
- Overridden by command line parameters and settings set within the program

In most cases, this generates a spaghetti-like set of special cases and one-offs as systems reach maturity. Very few systems have good ways for settings to cascade. The ones which do create custom *ad-hoc* languages.

What does cascade? CSS. It's a well-specificed, well-documented syntax. As a result, we use a subset of CSS syntax as our native format.

Mindful of backwards-compatibility, it is possible to integrate PMSS into most systems piecemeal. We also have an opinioned, streamlined API which will hopefully make it easy to get started.

What else is needed?
--------------------

- [ ] Validation and reasonable errors
  - [x] Robust typing, with conversions and validation
  - [x] Validation all required fields are provided
  - [ ] Above, considering contexts
  - [x] Validation all fields are declared
  - [ ] Above, for classes and attributes
- [x] Human-friendly (and ideally, standardized) formats. We don't want to reinvent yaml / json / XML / etc.
- [x] Comments
- [ ] Interpolation / DRY / single source of truth
  - [ ] If `system_dir` is `/opt/system`, we'd like to be able to set tokens to e.g. `${system_dir}/tokens.rsa`
  - [ ] Some systems take this further to full Turing-complete automation
  - [ ] THIS IS DANGEROUS IF SETTINGS CAN COME FROM A USER, so it should be behind a flag. Otherwise, you'll have `background_color` set to `${secret_id} ${access_key} ${password}`.
- [ ] Multiple file support. Large config files should be able to break down into smaller ones
  - [ ] This should be configurable and safe. We don't want someone to include `/etc/passwd` or similar.
- [ ] Security. We'd like to be immune to things like injection attacks, which do come up if setting come from e.g. web forms.
- [x] Some support for configuring plug-ins / modules
  - [x] This probably means some level of successive loading, with setting available before the full system is loaded.
- [ ] Lists / aggregations. E.g. if we want to set up a list of modules to import, each with its own settings.
- [ ] Classes provided on the command line
- [x] Dynamic reloading. If a file changes, settings update without a restart. Note this is currently more useful for development than deployment until we have more safety checks.
  - [ ] Robust validation and error handling on a reload.
- [ ] Robust test infrastructure
- [ ] Nice documentation
- [ ] pypi package (this might need a rename, since pmss is taken!)
- [ ] INI file support, to give an example of how to handle backwards-compatibility
- [ ] Better error messages
- [ ] Nicer `usage()`
- [ ] Selectors on the commandline
- [ ] Classes on the commandline

Note that we don't have all of this yet.

Simplified API
--------------

From Python:

```python

import pmss

settings = pmss.init(
    prog="lo",
    description="A system for monitoring",
    epilog="For more information, see PMSS documentation."
)

pmss.register_field(
    name="server_port",
    command_line_flags=["-p", "--port"],
    type=pmss.TYPES.port,
    description="The port our system should run on.",
    default=8888
)

pmss.register_field(
    name="hostname",
    type=pmss.TYPES.hostname,
    description="The hostname",
    required=True
)

pmss.validate(settings)
normal_port = settings.server_port()
exception_port = settings.server_port(attributes={'school': 'middlesex'})
```

Our settings file (can be placed in the standard locations):

```css
* {
    _biff: baz;
    hostname: testhost;
    server_port: 80;
}

[school=middlesex] {
    server_port: 8080;
}
```

And from the commandline:

```bash
python example.py --port=90 --hostname=testhosttwo
```

What's the model
----------------

We're basing this on CSS. Why?

- They cascade
- They're well-specified and libraries exist
- Many people know CSS

The downside, of course, is that many people find CSS a bit complex.

Conceptually, we plan to have series of rule sets. E.g.:

```python
    add_ruleset(args=sys.argsv)
    add_ruleset(file="~/.settings.pmss", name="User settings file", classes=["settings_file"], interpolation=True)
    add_ruleset(environ=sys.environ, id="environ")
    delete_ruleset(id="environ")
```

We also plan to have series of schemas, registered in code. Modules
can define schemas too. For example, a cloud service module could
define that it wants API keys.

Once everything is loaded, we can run:

```python
    validate()
```

Note that settings are usable (just not guaranteed correct) before
validation, as e.g. command line arguments might point to a settings
file and a series of modules to load, and validation might be
impossible until those are loaded.

We're trying to make this batteries included, so by default, the
rulesets look in the standard locations (`~`, `/etc`, etc.) and on the
commandline.

We do not look at parent / child relationships, so the following are
both okay:

```css
    auth {
        google {...}
        microsoft {...}
        github {...}
    }
    rosters {...}
```
or:
```css
   google {
       auth {...}
       rosters {...}
       docs {...}
   }

   microsoft {...}
```

For debugging, we can have fine-grained settings

```python
if settings.verbose(types=['pmss', 'selectors']):
   print("....")
```

And we can decide what to make verbose from the command line whether to run `--verbose=True` or `--pmss:verbose=True` or otherwise.

Likewise, we can define classes for e.g. prod and dev:

```css
.prod {
    database: postgresql;
}

.dev {
    database: sqlite;
}
```

Files
-----

* pmsslex.py and pmssyacc.py are the lexer and parser for our variant of
  CSS. These are designed to be interchangeable if you'd like e.g.
  full CSS or an INI file or whatnot.
* pmsstypes.py handles type validation and conversion. We use other
  libraries where possible, to maintain compatible formats. Conversely,
  this is usable without the rest of the system.


Who else has thought about this?
--------------------------------

* Build tools
  * [Bazel](https://bazel.build/)
* Web servers
  * [nginx](https://www.nginx.com/resources/wiki/start/topics/examples/full/) has a similar set of constraints around routes
* Command line parsers
  * [optparse](https://docs.python.org/3/library/optparse.html)
  * [docopt](http://docopt.org/)
  * [click](https://click.palletsprojects.com/en)
* Configuration languages
  * [Dhall](https://dhall-lang.org/) has very nice tooling which can visualize if a change to a file led to a change in output configuration, as well as diffs to see what the change was.
  * [configparser](https://docs.python.org/3/library/configparser.html) is the Python default, very much based on INI files. Good ideas include interpolation.
* Schemas. There's a whole theory of types, which is out-of-scope for this list (but in-scope for a grad-level course).
  * The best schema definition language seems to be [Cue](https://cuelang.org/) which is in Go, but has basic [Python integration](https://pypi.org/project/pycue/). We should probably use this verbatim.
  * [XML DTDs](https://en.wikipedia.org/wiki/Document_type_definition)
  * [JSON Schema](https://json-schema.org/)
  * [Traitlets](https://traitlets.readthedocs.io/en/stable/using_traitlets.html) thought a little bit about validation, although it seems to mix models in a way I don't like.
* CSS does most of what we want
  * [tinycss2](https://doc.courtbouillon.org/tinycss2/stable/first_steps.html) seems like the right parser to work from.
  * SASS builds on it with useful shortcuts. Should we adopt SASS extensions?
* Configuration languages
  * [pkl](https://pkl-lang.org/blog/introducing-pkl.html) was recently released by Apple. It seems to have some very nice ideas, but misses a lot as well. See also [HN discussion](https://news.ycombinator.com/item?id=39232976). Well worth reviewing, if not adopting.
  * [gcl](https://gcl.readthedocs.io/en/latest/) has nice copy about configuration. The language itself is very Turing-complete, which makes it a bit awkward. It's a little like having a code file, config.py.
  * [hcl](https://github.com/hashicorp/hcl) Seems nice.
  * [JSonnet](https://jsonnet.org/) has nice ideas, but seems to confuse templates and inheritence. Cue, above, is a reaction to this confusion.



PSS Settings
============

This is intended as a language for settings.

![XKCD Standards Comic](https://imgs.xkcd.com/comics/standards.png)

Why? WHY???
-----------

The *raison d'etre* is that settings cascade. In most cases, we would like to have:

- Rosters from Google Classroom
- Except for Central Valley School District, which uses Instructure
- Except for Maplewood Elementary School, which uses Canvas
- Except for Mrs. Johnson's afterschool program, which keeps rosters in a Google Spreadsheet, by virtue of excepting the general community and not just district students.

We'd also like to have:

- System defaults
- Overridden by system settings in `/etc/foo`
- Overridden by user settings in `~/.foo`
- Overridden by environment variables
- Overridden by command line parameters and settings set within the program

In most cases, this generate a spaghetti-like set of special cases and one-offs. Very few systems have good ways for these to cascade (web server routes come to mind as one of the very few examples).

What else is needed?
--------------------

* Validation and reasonable errors
* Human-friendly (and ideally, standardized) formats. We don't want to reinvent yaml / json / XML / etc.
* Comments
* Interpolation / DRY / single source of truth
  * If `system_dir` is `/opt/system`, we'd like to be able to set tokens to e.g. `${system_dir}/tokens.rsa`
  * Some systems take this further to full Turing-complete automation
  * THIS IS DANGEROUS IF SETTINGS CAN COME FROM A USER, so it should be behind a flag. Otherwise, you'll have `background_color` set to `${secret_id} ${access_key} ${password}`.
* Multiple file support. Large config files should be able to break down into smaller ones
* Security. We'd like to be immune to things like injection attacks, which do come up if setting come from e.g. web forms.
* Some support for configuring plug-ins / modules
  * This probably means some level of successive loading.

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
* Schemas
  * [XML DTDs](https://en.wikipedia.org/wiki/Document_type_definition)
  * 
* CSS does most of what we want
  * SASS builds on it with useful shortcuts
  * [tinycss2](https://doc.courtbouillon.org/tinycss2/stable/first_steps.html) seems like the right parser to work from.

http://cuelang.org/

What's the model
----------------

We're basing this on CSS. Why?

- They cascade
- They're well-specified and libraries exist
- Many people know CSS

The downside, of course, is that many people find CSS a bit complex.

We plan to have series of rule sets. E.g.:

  load_ruleset(args=sys.argsv)
  load_ruleset(file="~/.settings.pss", name="User settings file", classes=["settings_file"], interpolation=True)
  load_ruleset(environ=sys.environ, id="environ")
  delete_ruleset(id="environ")

We also plan to have series of schemas, registered in code. Modules
can define schemas too. For example, a cloud service module could
define that it wants API keys.

Once everything is loaded, we can run:

  validate()

Note that settings are usable (just not guaranteed correct) before
validation, as e.g. command line arguments might point to a settings
file and a series of modules to load, and validation might be
impossible until those are loaded.

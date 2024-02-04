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
* Multiple file support. Large config files should be able to break down into smaller ones
* Security. We'd like to be immune to things like injection attacks, which do come up if setting come from e.g. web forms.
* Some support for configuring plug-ins / modules
  * This probably means some level of successive loading.

Who else has thought about this?
--------------------------------

* Build tools
  * https://bazel.build/
* Web servers
  * nginx
* Command line parsers
  * 
* Configuration languages
  * [Dhall](https://dhall-lang.org/) has very nice tooling which can visualize if a change to a file led to a change in output configuration, as well as diffs to see what the change was.


http://cuelang.org/

What's the model
----------------

We're basing this on CSS. Why?

- They cascade
- They're well-specified and libraries exist
- Many people know CSS

The downside, of course, is that many people find CSS a bit complex.
# `alidistlint` - code linter for [alidist][] recipes

`alidistlint` runs [shellcheck][] on the scripts in [alidist][] recipes and [yamllint][] on their YAML headers, in addition to its own validation and checks on the YAML header and scripts in the recipe.

## Installation

To install `alidistlint`, run:

```bash
python3 -m pip install --user alidistlint
```

You should also install [yamllint][] and [shellcheck][], though this is optional.

If you want to use the `--changes` flag, install its dependencies like this:

```bash
python3 -m pip install --user 'alidistlint[git]'
```

## Usage

Run `alidistlint -h` to get more information about its arguments.

```
usage: alidistlint [-h] [-S] [-Y] [-H] [-f FORMAT] [-e | --changes COMMITS] RECIPE [RECIPE ...]
```

You can disable individual checkers using `-S`/`--no-shellcheck` and `-Y`/`--no-yamllint` for external linters, or `-L`/`--no-scriptlint` and `-H`/`--no-headerlint` for `alidistlint`'s built-in linters.
By default, all checkers are run.

Optionally, select the output format of errors using `-f`/`--format`.

You can also make `alidistlint` limit the warnings and notes it outputs.
Use the `-e`/`--errors-only` option to omit them entirely, and only show critical error messages.

Alternatively, you can limit non-critical messages to those that apply to changed code between the given commits using the `--changes` option.
Errors are always shown, even if they apply to unchanged lines.
This can be useful in CI, to gradually transition to using this linter.

Finally, pass one or multiple files to be checked to `alidistlint`.
You can use `-` for the standard input here, but be aware that this will produce spurious errors, as file names are meaningful for alidist recipes.

Errors and warnings will be printed to standard output in the format you selected.

If any messages with "error" severity were produced, `alidistlint` exits with a non-zero exit code.

## Shellcheck validation

The main build recipe (after the `---` line) is passed to `shellcheck`.

Currently, toplevel keys ending in `_recipe` or `_check` (such as `incremental_recipe`) are also checked using `shellcheck`.
This does not work for such keys specified in `overrides` yet.

There is a known issue with the checking of the above keys: if they do not start on a new line (using e.g. `key: |`), the reported line numbers for shellcheck errors will be off by one.

## Internal script checks

The following error codes are produced by the internal linter for scripts in recipes.
This linter checks for alidist-specific pitfalls and bad practices in shell scripts that shellcheck won't know about.
It can be switched off using `-L`/`--no-scriptlint`.
There is currently no way to disable individual checks.

- `ali:script-type` (error):
  The contents of a `*_recipe` or `*_check` value in the YAML header were not parsed as a string.
  Perhaps you used a bare `foo_recipe:`, which results in a `null` value, not an empty string.
- `ali:missing-modulefile` (note):
  The linter could not detect the creation of a Modulefile for this package, even though it has determined that one is needed.
  Ideally, use `alibuild-generate-module` to create a Modulefile for you.
  If you're generating a Modulefile yourself, make sure that it starts with a `#%Module1.0` comment and that this string appears in the script.
- `ali:consider-a-g-m` (note):
  The linter detected that you're manually generating a Modulefile in this recipe.
  You should prefer using `alibuild-generate-module`, which creates the common Modulefile boilerplate for you.
  If using `alibuild-generate-module`, you can still append your own Modulefile commands to the generated file.
- `ali:bad-shebang` (note):
  `aliBuild` runs scripts using `bash -e`.
  Non-trivial scripts (i.e. the "main" script in a recipe and `incremental_recipe`, if provided) must start with a `#!/bin/bash -e` line to signal this to `shellcheck`.
  For other scripts, this check is only enforced if the script in question already has a shebang line, to avoid confusion.
- `ali:colons-prepend-path` (error):
  Modules 4 does not allow colons in `prepend-path`, but the linter detected that you used them.
  Use multiple `prepend-path` calls to prepend multiple things to `$PATH` instead.
- `ali:dyld-library-path` (note):
  On MacOS, the `DYLD_LIBRARY_PATH` variable is not propagated to subprocesses if System Integrity Protection is enabled.
  Recipes must not rely on this variable.
  If there is a problem and libraries cannot be found at runtime, then `aliBuild`'s relocation code must be fixed.
- `ali:masked-exitcode` (note):
  Commands of the form `mkdir ... && rsync ...` are an often-copy-pasted pattern in alidist recipes.
  This is usually used to install Modulefiles.
  However, this line does not behave correctly if the `mkdir` fails: in that case, the `rsync` is silently skipped.
  If you find a false positive for this check, please open an issue.

## Internal YAML header validation

The following error codes are produced by the internal linter for YAML headers.
It can be switched off using `-H`/`--no-headerlint`.
There is currently no way to disable individual checks.

- `ali:empty` (error):
  The YAML header was not found.
  It must be terminated by a `\n`-terminated line containing nothing but three dashes (`---`).
- `ali:parse` (error):
  The YAML header could not be parsed or was fundamentally invalid.
  This is produced when PyYAML's `yaml.load` raises an error or when the provided YAML header is not a dictionary.
  `key: value` pairs must be provided as the YAML header.
- `ali:schema` (error):
  The YAML header did not conform to its schema.
  See the error message for more details.
- `ali:key-order` (warning):
  The `package`, `version` and `tag` keys were not found in the correct order.
  These keys should be the first in the file, in the above order (if present).
  Additionally, the `requires` key must come before `build_requires`.
- `ali:replacement-specs` (warning):
  Either the `prefer_system_check` seems to select a replacement spec, but
  none are defined using the `prefer_system_replacement_specs` key, or
  replacement specs are defined, but none are ever selected by the
  `prefer_system_check`.

## GitHub Actions integration

You can run `alidistlint` as part of a GitHub Action using `-f github`. In that case, `alidistlint` will annotate files with the errors found in them.

`alidistlint` will exit with a non-zero exit code if any errors were found (but not if only warnings were produced), which will cause the workflow to fail.

## Vim integration

Put the following in your `.vimrc`:

```vim
autocmd BufNewFile,BufRead *alidist/*.sh set makeprg=alidistlint\ -f\ gcc\ % errorformat=%f:%l:%c:\ %t%*[a-z]:\ %m
" If you want to automatically re-run the linter on every save:
autocmd BufWritePost *alidist/*.sh make
```

Then you can use `:make` to run the linter, `:cl` to see the error list, and navigate from one error to another using `:cp` (previous), `:cc` (current) and `:cn` (next).

## Emacs integration

Here is a simple Flycheck checker using `alidistlint`.
You can set this to check alidist recipes.

```elisp
(require 'flycheck)
(flycheck-def-executable-var alidist "alidistlint")
(flycheck-define-checker alidist
  "A syntax checker and linter for alidist recipes."
  ;; `flycheck-alidist-executable' automatically overrides the car of the
  ;; :command list if set and non-nil.
  :command ("alidistlint" "--format=gcc" source)
  :error-patterns
  ((error line-start (file-name) ":" line ":" column ": error: " (message)
          " [" (id (minimal-match (one-or-more not-newline))) "]" line-end)
   (warning line-start (file-name) ":" line ":" column ": warning: " (message)
            " [" (id (minimal-match (one-or-more not-newline))) "]" line-end)
   (info line-start (file-name) ":" line ":" column ": note: " (message)
         " [" (id (minimal-match (one-or-more not-newline))) "]" line-end)))
(add-to-list 'flycheck-checkers 'alidist)
```

[alidist]: https://github.com/alisw/alidist
[shellcheck]: https://www.shellcheck.net/
[yamllint]: https://yamllint.readthedocs.io/

"""Run alidistlint as a command-line script."""

from argparse import ArgumentParser, FileType, Namespace
import itertools
import os.path
import sys
import tempfile
from typing import NoReturn

from alidistlint import common, git, __version__
from alidistlint.headerlint import headerlint
from alidistlint.scriptlint import scriptlint
from alidistlint.yamllint import yamllint
from alidistlint.shellcheck import shellcheck, shellcheck_autofix


def run_with_args(args: Namespace) -> int:
    """Functional script entry point, returning the desired exit code."""
    formatter = common.ERROR_FORMATTERS[args.format]
    progname = os.path.basename(sys.argv[0])
    have_error = False
    repo_dir = changed_lines = None
    if git.AVAILABLE:
        repo_dir = git.find_repository(f.name for f in args.recipes)
    if repo_dir is not None and args.changes is not None:
        changed_lines = git.added_lines(repo_dir, args.changes)

    if getattr(args, 'fix', False) and not args.no_shellcheck:
        regular_files = [f.name for f in args.recipes if f.name != '<stdin>']
        if regular_files:
            fixes_applied = shellcheck_autofix(regular_files)
            if fixes_applied:
                # Close and reopen files to get updated content
                for f in args.recipes:
                    if f.name != '<stdin>':
                        f.close()
                args.recipes = [open(f.name, 'rb') if f.name != '<stdin>' else f 
                               for f in args.recipes]

    with tempfile.TemporaryDirectory(prefix=progname) as tempdir:
        errors, headers, scripts = common.split_files(tempdir, args.recipes)
        
        errors = itertools.chain(
            errors,
            () if args.no_headerlint else headerlint(headers),
            () if args.no_scriptlint else scriptlint(scripts),
            () if args.no_yamllint else yamllint(headers),
            () if args.no_shellcheck else shellcheck(scripts),
        )
        for error in errors:
            have_error |= error.level == 'error'
            # Always show errors, but hide warnings for non-changed lines if
            # --changes was given.
            show_error = (
                error.level == 'error' or
                not args.errors_only and (
                    changed_lines is None or
                    error.file_name == '<stdin>' or
                    (os.path.relpath(error.file_name, repo_dir),
                     error.line) in changed_lines
                )
            )
            if not show_error:
                continue
            try:
                print(formatter(error))
            except BrokenPipeError:
                # Carry on looking for errors for our exit code, then quit.
                if not have_error:
                    have_error |= any(e.level == 'error' for e in errors)
                break
    return 1 if have_error else 0


def parse_args() -> Namespace:
    """Parse and return command-line arguments."""
    parser = ArgumentParser(description=__doc__, epilog='''\
    Errors and warnings will be printed to standard output in the format you
    selected. If any messages with "error" severity were produced,
    alidistlint exits with a non-zero exit code.

    If pygit2 is installed, alidistlint can limit its output only to that
    which applies to code that was changes between two commits in the alidist
    repository. The --changes option takes git commit ranges. Use e.g.
    --changes=master..HEAD (or --changes=master..) to check the difference
    between the master branch and the current commit; or --changes=master to
    show the difference between master and the current state of the
    repository, including and uncommitted changes.
    ''')
    parser.add_argument('--version', action='version', version=__version__)
    selector = parser.add_mutually_exclusive_group()
    selector.add_argument('-e', '--errors-only', action='store_true',
                          help='only output the most critical messages')
    selector.add_argument('--changes', default=None, metavar='COMMITS',
                          help=('output warnings and notes only for added lines '
                                'between %(metavar)s (e.g. "master..HEAD"); '
                                'errors are always shown.'))
    parser.add_argument('-S', '--no-shellcheck', action='store_true',
                        help="don't run shellcheck on each script")
    parser.add_argument('-L', '--no-scriptlint', action='store_true',
                        help="don't run internal linter on each script")
    parser.add_argument('-Y', '--no-yamllint', action='store_true',
                        help="don't run yamllint on the YAML header")
    parser.add_argument('-H', '--no-headerlint', action='store_true',
                        help="don't run internal linter on the YAML header")
    parser.add_argument('-f', '--format', metavar='FORMAT',
                        choices=common.ERROR_FORMATTERS.keys(), default='gcc',
                        help=('format of error messages '
                              '(one of %(choices)s; default %(default)s)'))
    parser.add_argument('--fix', action='store_true',
                        help='automatically apply shellcheck fixes to files')
    parser.add_argument('recipes', metavar='RECIPE', nargs='+',
                        type=FileType('rb'),
                        help='a file name to check (use - for stdin)')
    args = parser.parse_args()
    if not git.AVAILABLE and args.changes is not None:
        parser.error('pygit2 is not installed; cannot use --changes')
    return args


def main() -> NoReturn:
    """Script entry point; parse args, run and exit."""
    sys.exit(run_with_args(parse_args()))

"""Shellcheck backend for alidistlint."""

import json
import os
import tempfile
from subprocess import run, PIPE, DEVNULL
import sys
from typing import Iterable

from alidistlint.common import Error, ScriptFilePart


# See shellcheck --list-optional.
ENABLED_OPTIONAL_CHECKS = ','.join((
    # Suggest explicitly using -n in `[ $var ]`.
    'avoid-nullary-conditions',
    # Notify when set -e is suppressed during function invocation.
    'check-set-e-suppressed',
))

DISABLED_CHECKS = ','.join((
    # "Not following: * was not specified as input (see shellcheck -x)."
    'SC1091',
))


def shellcheck(recipes: dict[str, ScriptFilePart]) -> Iterable[Error]:
    """Run shellcheck on a recipe."""
    cmd = 'shellcheck', '--format=json1', '--shell=bash', '--norc', \
        '--enable', ENABLED_OPTIONAL_CHECKS, '--exclude', DISABLED_CHECKS, \
        *recipes.keys()
    try:
        result = run(cmd, stdout=PIPE, stderr=DEVNULL, text=True, check=False)
    except FileNotFoundError:
        # shellcheck is not installed
        print('shellcheck is not installed; skipping', file=sys.stderr)
        return
    try:
        comments = json.loads(result.stdout)['comments']
    except (json.JSONDecodeError, KeyError) as exc:
        raise ValueError('failed to parse shellcheck output') from exc
    for comment in comments:
        part = recipes[comment['file']]
        yield Error(
            comment['level'],
            f"{comment['message']} [SC{comment['code']}]",
            part.orig_file_name,
            comment['line'] + part.line_offset,
            comment['column'] + part.column_offset,
            comment['endLine'] + part.line_offset,
            comment['endColumn'] + part.column_offset,
        )


def shellcheck_autofix(original_files: list[str]) -> bool:
    """Apply automatic fixes from shellcheck using diff format.
    
    Args:
        original_files: List of original file paths to apply fixes to
    
    Returns True if any fixes were applied, False otherwise.
    """
    if not original_files:
        return False
    
    cmd = 'shellcheck', '--format=diff', '--shell=bash', '--norc', \
        '--enable', ENABLED_OPTIONAL_CHECKS, '--exclude', DISABLED_CHECKS, \
        *original_files
    
    try:
        result = run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        print('shellcheck is not installed; skipping autofix', file=sys.stderr)
        return False
    
    if result.returncode != 0 and not result.stdout.strip():
        # Shellcheck failed and produced no diff output
        if result.stderr:
            print(f'shellcheck error: {result.stderr}', file=sys.stderr)
        return False
    
    if not result.stdout.strip():
        # No fixes available
        return False
    
    # Apply the patch using the patch command
    try:
        patch_result = run(['patch', '-p1'], input=result.stdout, 
                          text=True, check=True, capture_output=True)
        print(f'Applied shellcheck fixes to {len(original_files)} file(s)')
        return True
    except FileNotFoundError:
        print('patch command not found; cannot apply fixes', file=sys.stderr)
        return False
    except Exception as exc:
        print(f'Failed to apply shellcheck fixes: {exc}', file=sys.stderr)
        if hasattr(exc, 'stderr') and exc.stderr:
            print(f'patch error: {exc.stderr}', file=sys.stderr)
        return False

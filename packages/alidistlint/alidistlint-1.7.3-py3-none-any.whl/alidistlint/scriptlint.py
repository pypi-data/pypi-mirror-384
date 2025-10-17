"""Internal linter checking build recipe scripts for alidistlint."""

from collections.abc import Iterable
import itertools as it
import os.path
import re

from alidistlint.common import Error, ScriptFilePart


def scriptlint(scripts: dict[str, ScriptFilePart]) -> Iterable[Error]:
    """Apply alidist-specific linting rules to build scripts."""
    def make_error(message: str, code: str, rel_line: int, rel_column: int,
                   level: str) -> Error:
        return Error(level, f'{message} [ali:{code}]', script.orig_file_name,
                     1 + rel_line + script.line_offset,
                     1 + rel_column + script.column_offset)

    for script in scripts.values():
        is_defaults_recipe = os.path.basename(script.orig_file_name) \
                                    .startswith('defaults-')
        modulefile_required = (
            not script.key_path or            # this is the main recipe
            script.key_path[-1] == 'recipe'   # overridden main recipe
        ) and not script.is_system_requirement and not is_defaults_recipe
        if modulefile_required and b'#%Module' not in script.content and \
           b'alibuild-generate-module' not in script.content:
            human_key_name = '.'.join(script.key_path) or 'main recipe'
            yield make_error(
                f'{human_key_name} should create a Modulefile; use alibuild-'
                'generate-module or add a "#%Module1.0" comment to your '
                'manually-created Modulefile', 'missing-modulefile', 0, 0,
                'info',   # Some packages don't need a Modulefile.
            )

        # Non-trivial scripts should start with the proper shebang. This lets
        # shellcheck know that we use "bash -e" to run scripts.
        if not is_defaults_recipe and not script.is_system_requirement and (
                # If the script already has a shebang, make sure it's correct.
                script.content.startswith(b'#!') or
                # The "main" script should always have a shebang.
                not script.key_path or              # this is the main recipe
                script.key_path[-1] == 'recipe' or  # overridden main recipe
                # For small scripts (like system_requirement_check), this is
                # probably more annoying than useful. 4 lines is arbitrary.
                script.content.strip().count(b'\n') >= 3
        ) and not script.content.startswith(b'#!/bin/bash -e\n'):
            yield make_error(
                ('Invalid' if script.content.startswith(b'#!') else 'Missing')
                + ' script shebang. Use exactly "#!/bin/bash -e" to match '
                'aliBuild environment. You may see spurious errors until you '
                'fix the shebang.', 'bad-shebang', 0, 0, 'info',
            )

        lines = script.content.splitlines()
        for lineno, line in enumerate(lines):
            # Modules 4 does not allow having colons in prepend-path anymore
            prepend_path_pos = line.find(b'prepend-path')
            if prepend_path_pos != -1:
                line_tail = line[prepend_path_pos:]
                # "prepend-path PATH $::env(FOO)/bin" is fine!
                # Find all colons that are part of any "$::" on this line and
                # whitelist them.
                colons_allowed = frozenset(it.chain(*(
                    (match.start() + 1, match.start() + 2)
                    for match in re.finditer(br'\$::', line_tail)
                )))
                # If any colons on this line are *not* whitelisted, show an
                # error.
                colons = {m.start() for m in re.finditer(b':', line_tail)}
                for colon_pos in colons - colons_allowed:
                    yield make_error(
                        'Modules 4 does not allow colons in prepend-path',
                        'colons-prepend-path', lineno, colon_pos, 'error',
                    )

            # This should really be cleaned up, since macOS cleans any
            # DYLD_LIBRARY_PATH when launching children processes, making it
            # completely irrelevant. aliBuild handles rpaths in macOS builds,
            # and any bugs should be fixed there.
            for match in re.finditer(br'\bDYLD_LIBRARY_PATH\b', line):
                # "unset DYLD_LIBRARY_PATH" lines are fine.
                if re.fullmatch(br'\s*unset\s+', line[:match.start()]):
                    continue
                yield make_error(
                    'DYLD_LIBRARY_PATH is ignored on recent MacOS versions',
                    'dyld-library-path', lineno, match.start(), 'info',
                )

            # The following is a common (often copy-pasted) pattern in recipes:
            #   mkdir -p $INSTALLROOT/etc/modulefiles &&
            #   rsync -a --delete etc/modulefiles/ $INSTALLROOT/etc/modulefiles
            # However, the && just silently skips the rsync if the mkdir fails.
            # If this is the last line in the recipe, it's not a problem,
            # since that line determines the overall exit code.
            if lineno < len(lines) - 1 and \
               re.search(br'^[^#]*mkdir\s+.*&&\s*rsync\s+', line):
                yield make_error(
                    '"mkdir && rsync" ignores errors if "mkdir" fails; '
                    'prefer writing the commands on separate lines',
                    'masked-exitcode', lineno, line.find(b'&&'), 'info',
                )

            manual_modulefile_pos = line.find(b'#%Module')
            if manual_modulefile_pos != -1 and \
               b'alibuild-generate-module' not in script.content:
                human_key_name = '.'.join(script.key_path) or 'main recipe'
                yield make_error(
                    'Modulefile created manually here; consider using '
                    'alibuild-generate-module', 'consider-a-g-m',
                    lineno, manual_modulefile_pos, 'info',
                )

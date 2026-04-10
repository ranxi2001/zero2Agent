#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check Chinese quote usage in Markdown files."""

import glob as glob_module
import os
import sys

from quote_utils import analyze_markdown_quotes, configure_console_output, preview_line


def check_file(file_path):
    if not os.path.exists(file_path):
        print(f'\033[31mFile not found: {file_path}\033[0m')
        return None

    with open(file_path, 'r', encoding='utf-8') as handle:
        content = handle.read()

    stats = analyze_markdown_quotes(content)
    file_name = os.path.basename(file_path)
    needs_fix = stats['straight_double_text'] > 0
    paired = stats['pairing_issues'] == 0

    print(f'\n{file_name}')
    print(f'   Path: {file_path}')
    print(
        f'   Curly quotes in prose: left({stats["left_double"]}) right({stats["right_double"]}) '
        f'{"paired" if paired else "MISMATCH"}'
    )
    print(
        f'   Straight quotes: {stats["straight_double_total"]} total, '
        f'{stats["straight_double_text"]} in prose (fixable)'
    )

    if needs_fix:
        print(f'   \033[33mNeeds fix: {stats["straight_double_text"]} straight quotes in prose\033[0m')
        for line_number, line in stats['straight_lines']:
            print(f'      L{line_number}: {preview_line(line)}')

    if stats['pairing_issues']:
        print(f'   \033[31mPairing issues: {stats["pairing_issues"]}\033[0m')
        for line_number, line in stats['pairing_lines']:
            print(f'      L{line_number}: {preview_line(line)}')
    elif stats['left_double'] or stats['right_double']:
        print('   \033[32mOK: Curly quotes are properly paired in prose\033[0m')
    elif not needs_fix:
        print('   No quotes found in prose')

    return {'needs_fix': needs_fix, 'paired': paired}


def main():
    configure_console_output()

    args = sys.argv[1:]
    if not args:
        print('Usage: python check_quotes.py <file1.md> [file2.md] ...')
        sys.exit(1)

    files = []
    for arg in args:
        if '*' in arg:
            files.extend(glob_module.glob(arg, recursive=True))
        else:
            files.append(arg)

    if not files:
        print('No files found')
        sys.exit(1)

    print(f'\nChecking {len(files)} file(s)...')

    needs_fix = 0
    unpaired = 0
    for file_path in files:
        result = check_file(file_path)
        if not result:
            continue
        if result['needs_fix']:
            needs_fix += 1
        if not result['paired']:
            unpaired += 1

    print(f'\nSummary: {len(files)} checked, {needs_fix} need fix, {unpaired} pairing issues')

    if needs_fix:
        print(f'\nTo fix: python .claude/skills/chinese-quotes-fix/fix_quotes.py {" ".join(args)}')


if __name__ == '__main__':
    main()

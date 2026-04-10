#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix straight quotes in Markdown prose while preserving protected syntax."""

import glob as glob_module
import os
import sys

from quote_utils import analyze_markdown_quotes, configure_console_output, fix_markdown_quotes


def fix_file(file_path, dry_run=False):
    if not os.path.exists(file_path):
        print(f'\033[31mFile not found: {file_path}\033[0m')
        return False

    with open(file_path, 'r', encoding='utf-8') as handle:
        content = handle.read()

    before = analyze_markdown_quotes(content)
    file_name = os.path.basename(file_path)

    if before['straight_double_text'] == 0:
        print(f'SKIP {file_name} - No fixable straight quotes')
        return True

    fixed = fix_markdown_quotes(content)
    after = analyze_markdown_quotes(fixed)
    preserved = after['straight_double_total'] - after['straight_double_text']

    if dry_run:
        print(f'PREVIEW {file_name}')
        print(
            f'   {before["straight_double_text"]} straight quotes in prose -> '
            f'left({after["left_double"]}) right({after["right_double"]})'
        )
    else:
        with open(file_path, 'w', encoding='utf-8') as handle:
            handle.write(fixed)
        print(f'FIXED {file_name}')
        print(
            f'   {before["straight_double_text"]} straight quotes converted -> '
            f'left({after["left_double"]}) right({after["right_double"]})'
        )

    paired = '\033[32mYes\033[0m' if after['pairing_issues'] == 0 else f'\033[31mNo ({after["pairing_issues"]} issues)\033[0m'
    print(f'   Paired: {paired}')

    if preserved:
        print(f'   {preserved} straight quotes preserved in protected zones')
    if after['straight_double_text']:
        print(f'   \033[31mWarning: {after["straight_double_text"]} fixable straight quotes remain\033[0m')

    return True


def main():
    configure_console_output()

    args = sys.argv[1:]
    dry_run = '--dry-run' in args
    file_args = [arg for arg in args if arg != '--dry-run']

    if not file_args:
        print('Chinese Quote Fixer v4')
        print()
        print('Usage: python fix_quotes.py [--dry-run] <file1.md> [file2.md] ...')
        print()
        print('Protected zones:')
        print('  - YAML front matter')
        print('  - Fenced code blocks')
        print('  - Inline code spans')
        print('  - Mermaid HTML blocks')
        print('  - Markdown links and reference links')
        print('  - HTML tags, comments, and non-prose HTML blocks')
        sys.exit(1)

    files = []
    for arg in file_args:
        if '*' in arg:
            files.extend(glob_module.glob(arg, recursive=True))
        else:
            files.append(arg)

    if not files:
        print('No files found')
        sys.exit(1)

    action = 'Previewing' if dry_run else 'Fixing'
    print(f'\n{action} {len(files)} file(s)...\n')

    ok = sum(1 for file_path in files if fix_file(file_path, dry_run=dry_run))
    print(f'\nDone! Processed {ok}/{len(files)} files')
    if dry_run:
        print('\nRemove --dry-run to apply fixes')


if __name__ == '__main__':
    main()

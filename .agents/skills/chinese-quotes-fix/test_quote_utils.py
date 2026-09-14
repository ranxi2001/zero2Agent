#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression tests for Chinese quote checking and fixing."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from quote_utils import analyze_markdown_quotes, fix_pairing_markdown_quotes


SKILL_DIR = Path(__file__).resolve().parent
CHECKER = SKILL_DIR / 'check_quotes.py'


class QuoteUtilsTest(unittest.TestCase):
    def test_reversed_double_openers_are_counted_once_and_fixed(self):
        content = (
            '这也是为什么”Context Engineering”（上下文工程）成为高频词，'
            '而不是把”完整信息组合”当作附属品。\n'
        )

        before = analyze_markdown_quotes(content)
        self.assertEqual(2, before['pairing_issues'])
        self.assertEqual([1], [line for line, _ in before['pairing_lines']])

        fixed, fixed_count = fix_pairing_markdown_quotes(content)
        self.assertEqual(2, fixed_count)
        self.assertEqual(
            '这也是为什么“Context Engineering”（上下文工程）成为高频词，'
            '而不是把“完整信息组合”当作附属品。\n',
            fixed,
        )
        self.assertEqual(0, analyze_markdown_quotes(fixed)['pairing_issues'])

    def test_reversed_single_opener_is_counted_once_and_fixed(self):
        content = '这里强调’客户为先’原则。\n'

        before = analyze_markdown_quotes(content)
        self.assertEqual(1, before['single_pairing_issues'])

        fixed, fixed_count = fix_pairing_markdown_quotes(content)
        self.assertEqual(1, fixed_count)
        self.assertEqual('这里强调‘客户为先’原则。\n', fixed)
        self.assertEqual(0, analyze_markdown_quotes(fixed)['single_pairing_issues'])

    def test_checker_fails_when_only_pairing_is_wrong(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            markdown_path = Path(temp_dir) / 'sample.md'
            markdown_path.write_text('为什么”Context Engineering”很重要。\n', encoding='utf-8')
            result = subprocess.run(
                [sys.executable, str(CHECKER), str(markdown_path)],
                capture_output=True,
                check=False,
                text=True,
            )

        self.assertEqual(1, result.returncode)
        self.assertIn('Summary: 1 checked, 1 need fix, 1 with pairing issues', result.stdout)
        self.assertNotIn('\nTo fix: ', result.stdout)
        self.assertIn('\nTo fix pairing: ', result.stdout)

    def test_checker_passes_clean_quotes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            markdown_path = Path(temp_dir) / 'sample.md'
            markdown_path.write_text('为什么“Context Engineering”很重要。\n', encoding='utf-8')
            result = subprocess.run(
                [sys.executable, str(CHECKER), str(markdown_path)],
                capture_output=True,
                check=False,
                text=True,
            )

        self.assertEqual(0, result.returncode)
        self.assertIn('Summary: 1 checked, 0 need fix, 0 with pairing issues', result.stdout)


if __name__ == '__main__':
    unittest.main()

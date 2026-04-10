#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared helpers for checking and fixing Chinese quotes in Markdown."""

import re
import sys


YAML_FRONT_MATTER = re.compile(
    r'^---[ \t]*\r?\n[\s\S]*?\r?\n---[ \t]*(?:\r?\n|$)'
)

MERMAID_HTML_BLOCK = re.compile(
    r'(?is)<div\b[^>]*class\s*=\s*(["\'])[^"\']*\bmermaid\b[^"\']*\1[^>]*>'
    r'[\s\S]*?</div>'
)

HTML_BLOCK = re.compile(
    r'(?is)<(?P<tag>details|summary|table|thead|tbody|tfoot|tr|td|th|figure|'
    r'figcaption|pre|code|script|style|textarea|svg)\b[^>]*>[\s\S]*?</(?P=tag)>'
)

FENCED_CODE = re.compile(
    r'(?ms)(^|\n)(?P<fence>`{3,}|~{3,})[^\n]*\n[\s\S]*?\n(?P=fence)[ \t]*(?=\n|$)'
)

INLINE_CODE = re.compile(r'(?<!`)`[^`\n]+`(?!`)')
HTML_COMMENT = re.compile(r'<!--[\s\S]*?-->')
HTML_TAG = re.compile(r'<[^>\n]+>')
MARKDOWN_LINK = re.compile(r'!?\[[^\]\n]+\]\([^\)\n]+\)')
REFERENCE_LINK = re.compile(r'(?m)^[ \t]{0,3}\[[^\]\n]+\]:[^\n]+$')

PROTECTED_PATTERNS = (
    MERMAID_HTML_BLOCK,
    HTML_BLOCK,
    FENCED_CODE,
    INLINE_CODE,
    HTML_COMMENT,
    MARKDOWN_LINK,
    REFERENCE_LINK,
    HTML_TAG,
)

OPENING_CONTEXT = set('([<{（［【《「『〈〔〖“‘:：')
CLOSING_CONTEXT = set(')]}>）］】》」』〉〕〗，。！？；：,.!?;、')
IGNORABLE_CONTEXT = set(' \t*_~')


def configure_console_output():
    """Avoid UnicodeEncodeError on Windows consoles with legacy encodings."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            try:
                stream.reconfigure(errors='replace')
            except ValueError:
                pass


def split_front_matter(content):
    match = YAML_FRONT_MATTER.match(content)
    if not match:
        return '', content, 0

    front_matter = match.group(0)
    return front_matter, content[match.end():], front_matter.count('\n')


def build_protection_mask(text):
    mask = [False] * len(text)
    for pattern in PROTECTED_PATTERNS:
        for match in pattern.finditer(text):
            for index in range(match.start(), match.end()):
                mask[index] = True
    return mask


def _is_cjk(char):
    code = ord(char)
    return (
        0x3400 <= code <= 0x4DBF
        or 0x4E00 <= code <= 0x9FFF
        or 0xF900 <= code <= 0xFAFF
    )


def _is_wordish(char):
    return char.isalnum() or _is_cjk(char)


def _prev_significant_char(segment, index):
    cursor = index - 1
    while cursor >= 0 and segment[cursor] in IGNORABLE_CONTEXT:
        cursor -= 1
    return segment[cursor] if cursor >= 0 else None


def _next_significant_char(segment, index):
    cursor = index + 1
    while cursor < len(segment) and segment[cursor] in IGNORABLE_CONTEXT:
        cursor += 1
    return segment[cursor] if cursor < len(segment) else None


def _is_escaped_quote(segment, index):
    return index > 0 and segment[index - 1] == '\\'


def _classify_straight_quote(segment, index, expect_open):
    prev_char = _prev_significant_char(segment, index)
    next_char = _next_significant_char(segment, index)

    if prev_char is None:
        return 'open'
    if next_char is None:
        return 'close'

    prev_openish = prev_char in OPENING_CONTEXT
    next_closeish = next_char in CLOSING_CONTEXT
    prev_wordish = _is_wordish(prev_char)
    next_wordish = _is_wordish(next_char)

    if prev_openish and not next_closeish:
        return 'open'
    if next_closeish and not prev_openish:
        return 'close'
    if prev_wordish and not next_wordish:
        return 'close'
    if next_wordish and not prev_wordish:
        return 'open'

    return 'open' if expect_open else 'close'


def analyze_segment_quotes(segment, convert=False):
    chars = list(segment)
    stats = {
        'straight': 0,
        'left': 0,
        'right': 0,
        'pairing_issues': 0,
    }
    expect_open = True

    for index, char in enumerate(chars):
        if char == '“':
            stats['left'] += 1
            if not expect_open:
                stats['pairing_issues'] += 1
            expect_open = False
            continue

        if char == '”':
            stats['right'] += 1
            if expect_open:
                stats['pairing_issues'] += 1
            expect_open = True
            continue

        if char != '"' or _is_escaped_quote(segment, index):
            continue

        stats['straight'] += 1
        quote_type = _classify_straight_quote(segment, index, expect_open)

        if quote_type == 'open':
            stats['left'] += 1
            if not expect_open:
                stats['pairing_issues'] += 1
            if convert:
                chars[index] = '“'
            expect_open = False
        else:
            stats['right'] += 1
            if expect_open:
                stats['pairing_issues'] += 1
            if convert:
                chars[index] = '”'
            expect_open = True

    if not expect_open:
        stats['pairing_issues'] += 1

    return ''.join(chars), stats


def analyze_line(line, line_mask):
    stats = {
        'straight': 0,
        'left': 0,
        'right': 0,
        'pairing_issues': 0,
    }
    cursor = 0

    while cursor < len(line):
        while cursor < len(line) and line_mask[cursor]:
            cursor += 1

        segment_start = cursor
        while cursor < len(line) and not line_mask[cursor]:
            cursor += 1

        if segment_start == cursor:
            continue

        _, segment_stats = analyze_segment_quotes(line[segment_start:cursor])
        for key, value in segment_stats.items():
            stats[key] += value

    return stats


def analyze_markdown_quotes(content):
    _, body, yaml_lines = split_front_matter(content)
    mask = build_protection_mask(body)

    stats = {
        'left_double': 0,
        'right_double': 0,
        'straight_double_text': 0,
        'straight_double_total': content.count('"'),
        'pairing_issues': 0,
        'straight_lines': [],
        'pairing_lines': [],
    }

    offset = 0
    for line_number, line_with_end in enumerate(body.splitlines(keepends=True), yaml_lines + 1):
        line = line_with_end.rstrip('\r\n')
        line_mask = mask[offset:offset + len(line)]
        line_stats = analyze_line(line, line_mask)

        stats['left_double'] += line_stats['left']
        stats['right_double'] += line_stats['right']
        stats['straight_double_text'] += line_stats['straight']
        stats['pairing_issues'] += line_stats['pairing_issues']

        if line_stats['straight']:
            stats['straight_lines'].append((line_number, line))
        if line_stats['pairing_issues']:
            stats['pairing_lines'].append((line_number, line))

        offset += len(line_with_end)

    return stats


def fix_markdown_quotes(content):
    front_matter, body, _ = split_front_matter(content)
    mask = build_protection_mask(body)
    chars = list(body)
    line_start = 0

    while line_start <= len(body):
        line_end = body.find('\n', line_start)
        if line_end == -1:
            line_end = len(body)

        cursor = line_start
        while cursor < line_end:
            while cursor < line_end and mask[cursor]:
                cursor += 1

            segment_start = cursor
            while cursor < line_end and not mask[cursor]:
                cursor += 1

            if segment_start == cursor:
                continue

            fixed_segment, _ = analyze_segment_quotes(body[segment_start:cursor], convert=True)
            chars[segment_start:cursor] = list(fixed_segment)

        if line_end == len(body):
            break
        line_start = line_end + 1

    return front_matter + ''.join(chars)


def preview_line(line, limit=100):
    if len(line) <= limit:
        return line
    return line[:limit] + '...'

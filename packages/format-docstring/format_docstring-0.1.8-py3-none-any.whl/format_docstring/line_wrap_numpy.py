from __future__ import annotations

import re
import textwrap

from format_docstring.line_wrap_utils import (
    add_leading_indent,
    collect_to_temp_output,
    finalize_lines,
    process_temp_output,
)


def wrap_docstring_numpy(
        docstring: str,
        line_length: int,
        leading_indent: int | None = None,
        fix_rst_backticks: bool = False,
) -> str:
    """Wrap NumPy-style docstrings with light parsing rules.

    Rules implemented (conservative):
    - Do not wrap section headings or their underline lines.
    - In "Parameters" (and similar) sections, do not wrap signature lines
      like ``name : type, default=...``; wrap indented description lines only.
    - In "Returns"/"Yields" sections, treat the first-level lines (either
      ``name : type`` or just ``type``) as signatures and do not wrap them;
      wrap their indented descriptions.
    - In the "Examples" section, do not wrap lines starting with ``>>> ``.
    - Do not wrap any lines inside fenced code blocks (``` ... ```).
    - Outside these special cases, wrap only lines that exceed ``line_length``
      (keep existing intentional line breaks).
    """
    # Pre-processing: if caller provides indentation context (i.e., the
    # indentation level of the docstring's parent), and the docstring body
    # doesn't begin with a newline followed by that many spaces, prepend it.
    # This helps place the closing quotes on their own indented line later.
    docstring_: str = add_leading_indent(docstring, leading_indent)

    # Apply backtick fixing to the entire docstring first, before line-by-line
    # processing. This ensures that backtick pairs spanning multiple lines are
    # handled correctly.
    if fix_rst_backticks:
        docstring_ = _fix_rst_backticks(docstring_)

    lines: list[str] = docstring_.splitlines()
    if not lines:
        return docstring_

    # Track section state
    SECTION_PARAMS = {
        'parameters',
        'parameter',  # tolerate typo
        'other parameters',
        'other parameter',  # tolerate typo
        'attributes',
        'attribute',  # tolerate typo
    }
    SECTION_RETURNS = {
        'returns',
        'return',  # tolerate typo
        'yields',
        'yield',  # tolerate typo
        'raises',
        'raise',  # tolerate typo
    }
    SECTION_EXAMPLES = {
        'examples',
        'example',  # tolerate typo
    }

    temp_out: list[str | list[str]] = []
    in_code_fence: bool = False
    current_section: str = ''
    in_examples: bool = False

    i: int = 0
    while i < len(lines):
        line: str = lines[i]

        if line == '':
            temp_out.append(line)
            i += 1
            continue

        stripped: str = line.lstrip(' ')
        indent_length: int = len(line) - len(stripped)

        # Detect code fence start/end first; always preserve fence lines
        if stripped.startswith('```'):
            in_code_fence = not in_code_fence
            temp_out.append(line)
            i += 1
            continue

        # Detect and pass-through section headings with underline
        if not in_code_fence:
            heading: str | None = _get_section_heading_title(lines, i)
            if heading:
                current_section = heading
                in_examples = heading in SECTION_EXAMPLES
                temp_out.append(line)
                temp_out.append(lines[i + 1])
                i += 2
                continue

        # Inside fenced code blocks: pass through unchanged
        if in_code_fence:
            temp_out.append(line)
            i += 1
            continue

        # In Examples, skip wrapping and backtick fixing for REPL lines
        if in_examples and (
            stripped.startswith('>>> ') or stripped.startswith('... ')
        ):
            temp_out.append(line)
            i += 1
            continue

        # Parameters-like sections
        section_lower_case: str = current_section.lower()
        if section_lower_case in SECTION_PARAMS:
            if line.strip() == '':
                temp_out.append(line)
                i += 1
                continue

            # Only treat as a signature if it appears at the top level of the
            # section (indentation < 4). This prevents mis-detecting
            # description lines that happen to contain a colon (e.g., tables,
            # examples, notes) as new parameter signatures.
            if _is_param_signature(line) and indent_length <= leading_indent:  # type: ignore[operator]
                fixed_line = _fix_colon_spacing(line)
                fixed_line = _standardize_default_value(fixed_line)
                temp_out.append(fixed_line)
                i += 1
                continue

            # Description lines (typically indented): wrap if too long
            collect_to_temp_output(temp_out, line)
            i += 1
            continue

        # Returns/Yields sections
        if section_lower_case in SECTION_RETURNS:
            if line.strip() == '':
                temp_out.append(line)
                i += 1
                continue

            # Treat top-level lines as signatures
            if indent_length <= leading_indent:  # type: ignore[operator]
                temp_out.append(line)
                i += 1
                continue

            collect_to_temp_output(temp_out, line)
            i += 1
            continue

        # Examples or any other section
        collect_to_temp_output(temp_out, line)
        i += 1

    out: list[str] = process_temp_output(temp_out, width=line_length)
    return finalize_lines(out, leading_indent)


def _is_hyphen_underline(s: str) -> bool:
    """Return True if the line consists of only hyphens (>= 2).

    Leading/trailing whitespace is ignored. This is a relaxed detector for
    NumPy-style section underlines such as the line beneath "Parameters".

    Examples
    --------
    >>> _is_hyphen_underline('---')
    True
    >>> _is_hyphen_underline('  ----  ')
    True
    >>> _is_hyphen_underline('---')
    True
    >>> _is_hyphen_underline(' - - ')
    False

    """
    t = s.strip()
    return len(t) >= 2 and set(t) <= {'-'}


def _get_section_heading_title(lines: list[str], idx: int) -> str | None:
    """Return the lowercased section title at ``idx`` if underlined.

    Looks at ``lines[idx]`` for a non-empty title and ``lines[idx+1]`` for a
    hyphen-only underline (at least 3 hyphens). If the pattern matches,
    returns the lowercased title; otherwise returns ``None``.
    """
    if idx + 1 >= len(lines):
        return None

    title = lines[idx].strip()
    underline = lines[idx + 1]
    if not title:
        return None

    if _is_hyphen_underline(underline):
        return title.lower()

    return None


# Character classes for building the parameter signature regex
START = r'[A-Za-z_]'  # Valid identifier start characters
CONT = r'[A-Za-z0-9_]'  # Valid identifier continuation characters

# Precompiled regex for NumPy parameter signatures
# Pattern: ^\s*\*{0,2}IDENTIFIER(?:\s*,\s*\*{0,2}IDENTIFIER)*\s*:\s*.*$
# Explanation:
# - ^\s*: optional leading spaces
# - \*{0,2}: zero, one, or two asterisks (for *args, **kwargs)
# - [A-Za-z_][A-Za-z0-9_]*: identifier (starts with letter/underscore)
# - (?:\s*,\s*\*{0,2}[A-Za-z_][A-Za-z0-9_]*)*: 0 or more comma+identifier pairs
# - \s*:\s*: a colon with optional surrounding spaces
# - .*$: anything (or nothing) on the right-hand side
_PARAM_SIGNATURE_RE = re.compile(
    rf'^\s*\*{{0,2}}{START}{CONT}*(?:\s*,\s*\*{{0,2}}{START}{CONT}*)*\s*:\s*.*$'
)


def _is_param_signature(text: str) -> bool:
    r"""Return True if a line looks like a NumPy parameter signature.

    This function uses a single, precompiled regex to remain fast even when
    scanning many lines. We purposefully accept a broad set of "signature"
    shapes that appear in real-world NumPy-style docs and avoid false
    negatives, while still rejecting obviously non-signature prose.

    Accepted (examples)
    -------------------
    - ``name : type``
    - ``name: type``  (missing space is fine)
    - ``alpha, beta : list[str] | None``  (comma-separated names)
    - ``abc :`` or ``abc:``  (empty annotation part)
    - ``*args : Any``  (variadic positional arguments)
    - ``**kwargs : dict[str, Any]``  (variadic keyword arguments)
    - ``*args, **kwargs : Any``  (mixed with other parameters)
    - Leading indentation allowed

    Rejected (examples)
    -------------------
    - Lines without a colon
    - Names that are not valid identifiers or comma-separated identifiers
      (e.g. ``1name : int``, ``alpha, beta gamma : int``)
    """
    return bool(_PARAM_SIGNATURE_RE.match(text))


def _fix_colon_spacing(line: str) -> str:
    """Fix spacing around colons in parameter signature lines.

    Ensures there is exactly one space before and one space after the colon
    in parameter signatures. Only operates on lines that are detected as
    parameter signatures by _is_param_signature().

    Parameters
    ----------
    line : str
        The line to fix

    Returns
    -------
    str
        The line with corrected colon spacing

    Examples
    --------
    >>> _fix_colon_spacing('arg1: dict[str, list[str]]')
    'arg1 : dict[str, list[str]]'
    >>> _fix_colon_spacing('arg1 :  dict[str, list[str]]')
    'arg1 : dict[str, list[str]]'
    >>> _fix_colon_spacing('  arg1:dict[str, list[str]]')
    '  arg1 : dict[str, list[str]]'
    """
    # Find the colon's position
    colon_idx = line.find(':')
    if colon_idx == -1:
        return line

    # Split into parts: before colon, colon, after colon
    before_colon = line[:colon_idx].rstrip()
    after_colon = line[colon_idx + 1 :].lstrip()

    # Reconstruct with proper spacing: " : "
    return before_colon + ' : ' + after_colon


# Precompiled regex for default value standardization (colon format)
# Pattern: ^(.*?)(?:,\s*|\s+)default\s*:\s*(.+)$
# Matches formats like "default:XXX" or "default: XXX"
_DEFAULT_COLON_RE = re.compile(
    r'^(.*?)'  # Everything before default (non-greedy)
    r'(?:,\s*|\s+)'  # Either comma+spaces or just spaces
    r'default'  # The word "default"
    r'\s*:\s*'  # Colon with optional spaces
    r'(.+)$',  # The default value
    re.IGNORECASE,
)

# Precompiled regex for default value standardization (space format)
# Pattern: ^(.*?)(?:,\s*|\s+)default\s+(?:is\s+)?(.+)$
# Matches formats like "default XXX" or "default is XXX"
_DEFAULT_SPACE_RE = re.compile(
    r'^(.*?)'  # Everything before default (non-greedy)
    r'(?:,\s*|\s+)'  # Either comma+spaces or just spaces
    r'default'  # The word "default"
    r'\s+'  # Required space after "default"
    r'(?:is\s+)?'  # Optional "is "
    r'(.+)$',  # The default value
    re.IGNORECASE,
)


def _standardize_default_value(line: str) -> str:
    """Standardize default value declarations in parameter signatures.

    Converts various formats of default value specifications to the standard
    `, default=XXX` format. Handles formats like:
    - ` default XXX`
    - `, default XXX`
    - `, default is XXX`
    - ` default is XXX`
    - ` default:XXX`
    - ` default: XXX`
    - `, default:XXX`
    - `, default: XXX`

    Parameters
    ----------
    line : str
        The parameter signature line to standardize

    Returns
    -------
    str
        The line with standardized default value format

    Examples
    --------
    >>> _standardize_default_value('arg : int, default 10')
    'arg : int, default=10'
    >>> _standardize_default_value('arg : str, default is "hello"')
    'arg : str, default="hello"'
    >>> _standardize_default_value('arg : bool, default: True')
    'arg : bool, default=True'
    """
    # Check colon format first to avoid matching colons in space-based pattern
    match = _DEFAULT_COLON_RE.match(line)
    if match:
        before = match.group(1).rstrip()
        default_value = match.group(2).strip()
        return f'{before}, default={default_value}'

    # Try space-separated format with optional "is"
    match = _DEFAULT_SPACE_RE.match(line)
    if match:
        before = match.group(1).rstrip()
        default_value = match.group(2).strip()
        return f'{before}, default={default_value}'

    return line


def handle_single_line_docstring(
        whole_docstring_literal: str | None,
        docstring_content: str,
        docstring_starting_col: int,
        docstring_ending_col: int,
        line_length: int = 79,
) -> str | None:
    """
    Handle single-line docstring that's a bit too long: the docstring content
    is not long enough to be wrapped, but with the leading and ending quotes
    (6 quotes in total) the whole line exceeds length limit.
    """
    if whole_docstring_literal is None:
        return None

    if '\n' in whole_docstring_literal:  # multi-line: do not handle
        return whole_docstring_literal

    if docstring_ending_col > line_length:  # whole docstring exceeds limit
        num_leading_indent: int = docstring_starting_col
        parts: list[str] = whole_docstring_literal.split(docstring_content)
        prefix: str = parts[0]
        postfix: str = parts[-1]
        indent: str = ' ' * num_leading_indent

        # We need to wrap `docstring_content` here because single-line
        # docstrings don't get wrapped anywhere else.
        tw: textwrap.TextWrapper = textwrap.TextWrapper(
            width=line_length - num_leading_indent,
            break_long_words=False,
            break_on_hyphens=False,
            replace_whitespace=False,
            drop_whitespace=True,
        )
        wrapped_list: list[str] = tw.wrap(docstring_content)
        wrapped: str = textwrap.indent('\n'.join(wrapped_list), indent)
        return f'{prefix}\n{wrapped}\n{indent}{postfix}'

    return whole_docstring_literal


# Precompiled regex for fixing RST backticks.
# Pattern matches inline literals while avoiding roles, cross-references, and
# links. See the documentation of _fix_rst_backticks() for more details.
# The pattern allows backticks after: start of line, whitespace, parentheses,
# or certain punctuation (like > and . for `>>> ` and `... ` literals)
# Note: We match [^`]+ (anything except backticks) and then check in the
# replacement function whether it's an external link (contains < followed by >)
# The opening backtick must not be immediately followed by _ or __ (to avoid
# matching the trailing backtick of cross-references like `text`_ or `text`__)
_RST_BACKTICK_PATTERN = re.compile(
    r'(?:^|(?<=\s)|(?<=\()|(?<=[>.]))(?::[\w-]+:)?`(?!_)([^`]+)`(?!`)(?!__)(?!_)'
)


def _fix_rst_backticks(docstring: str) -> str:
    """
    Fix inline-literal single backticks to double backticks per rST syntax.

    This function converts pairs of single backticks (`` `...` ``) that
    represent inline *literals* into pairs of double backticks (`` ``...`` ``).
    It deliberately **does not** modify other rST constructs that require
    single backticks.

    What stays untouched
    --------------------
    - Existing double-backtick literals: ````code````.
    - Roles: ``:role:`text``` (e.g., ``:emphasis:`word```).
    - Cross-references: `` `text`_ `` and anonymous refs `` `text`__ ``.
    - Inline external links: `` `text <https://example.com>`_ ``.
    - Explicit hyperlink targets: ``.. _`Label`: https://example.com``.
    - REPL lines: Lines starting with ``>>> `` or ``... `` (Python examples).

    How it works (regex guards)
    ---------------------------
    The pattern only upgrades a match when **all** these are true:
    - Opening backtick is not part of an existing ````...```` (``(?<!`)``).
    - Opening backtick is not immediately preceded by ``:`` (to avoid roles).
    - Opening backtick is not immediately preceded by ``_`` (to avoid
      explicit targets like ``.. _`Label`: …``).
    - The enclosed text contains **no** backticks and **no** ``<`` (to avoid
      inline-link forms like `` `text <url>`_ ``).
    - Closing backtick is not part of ````...```` (``(?!`)``).
    - Closing backtick is not followed by ``__`` or ``_`` (to avoid
      anonymous/named references).
    - The line does not start with ``>>> `` or ``... `` (Python REPL).

    Parameters
    ----------
    docstring : str
        The docstring content to process.

    Returns
    -------
    str
        The docstring with only inline-literal backticks fixed.

    Examples
    --------
    >>> _fix_rst_backticks('Use `foo` to do something')
    'Use ``foo`` to do something'

    >>> _fix_rst_backticks('Edge punctuation: `x`.')
    'Edge punctuation: ``x``.'

    >>> _fix_rst_backticks(':emphasis:`word`')
    ':emphasis:`word`'

    >>> _fix_rst_backticks('See `Link`_ for details')
    'See `Link`_ for details'

    >>> _fix_rst_backticks('`Python <https://www.python.org>`_')
    '`Python <https://www.python.org>`_'

    >>> _fix_rst_backticks('.. _`Special Target`: https://example.com/special')
    '.. _`Special Target`: https://example.com/special'

    >>> _fix_rst_backticks('Already has ``foo`` double backticks')
    'Already has ``foo`` double backticks'

    >>> _fix_rst_backticks('>>> `foo` in REPL')
    '>>> `foo` in REPL'
    """

    def replace_func(match: re.Match[str]) -> str:
        # match.group(0) is the full match
        # match.group(1) is the content between backticks
        full_match: str = match.group(0)
        content: str = match.group(1)

        # If the match includes a role prefix (like :emphasis:), don't replace
        if ':' in full_match and full_match.index('`') > 0:
            # Check if there's a role prefix before the backtick
            before_backtick = full_match[: full_match.index('`')]
            if ':' in before_backtick:
                return full_match  # Keep original (it's a role)

        # Check if this is an external link (contains <...> pattern)
        # External links look like: `text <url>`_
        if '<' in content and '>' in content:
            # Check if < comes before > (basic validation)
            if content.index('<') < content.rindex('>'):
                return full_match  # Keep original (it's an external link)

        # Otherwise, replace single backticks with double
        # Keep any leading whitespace/parenthesis/punctuation
        prefix = match.group(0)[: match.group(0).index('`')]
        return f'{prefix}``{content}``'

    # Protect REPL lines (>>> and ...) from backtick fixing by temporarily
    # replacing them with placeholders, then restoring after processing.
    # This allows multi-line backtick pairs (such as external links spanning
    # lines) to be handled correctly while still preserving backticks in REPL
    # comments.
    lines = docstring.splitlines(keepends=True)
    repl_lines: dict[int, str] = {}
    protected_lines: list[str] = []

    for i, line in enumerate(lines):
        stripped = line.lstrip()
        # Protect REPL lines (>>> or ...) - don't fix backticks in these
        if stripped.startswith('>>> ') or stripped.startswith('... '):
            repl_lines[i] = line
            # Use a placeholder that won't be matched by the regex
            protected_lines.append(
                '\x00REPL_LINE\x00\n'
                if line.endswith('\n')
                else '\x00REPL_LINE\x00'
            )
        else:
            protected_lines.append(line)

    # Process the entire docstring (with REPL lines protected)
    protected_docstring = ''.join(protected_lines)
    processed = _RST_BACKTICK_PATTERN.sub(replace_func, protected_docstring)

    # Restore REPL lines
    result_lines = processed.splitlines(keepends=True)
    for i, original_line in repl_lines.items():
        if i < len(result_lines):
            result_lines[i] = original_line

    return ''.join(result_lines)

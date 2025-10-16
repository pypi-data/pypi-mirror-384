# btx_lib_list

<!-- Badges -->
[![CI](https://github.com/bitranox/btx_lib_list/actions/workflows/ci.yml/badge.svg)](https://github.com/bitranox/btx_lib_list/actions/workflows/ci.yml)
[![CodeQL](https://github.com/bitranox/btx_lib_list/actions/workflows/codeql.yml/badge.svg)](https://github.com/bitranox/btx_lib_list/actions/workflows/codeql.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Open in Codespaces](https://img.shields.io/badge/Codespaces-Open-blue?logo=github&logoColor=white&style=flat-square)](https://codespaces.new/bitranox/btx_lib_list?quickstart=1)
[![PyPI](https://img.shields.io/pypi/v/btx_lib_list.svg)](https://pypi.org/project/btx_lib_list/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/btx_lib_list.svg)](https://pypi.org/project/btx_lib_list/)
[![Code Style: Ruff](https://img.shields.io/badge/Code%20Style-Ruff-46A3FF?logo=ruff&labelColor=000)](https://docs.astral.sh/ruff/)
[![codecov](https://codecov.io/gh/bitranox/btx_lib_list/graph/badge.svg?token=UFBaUDIgRk)](https://codecov.io/gh/bitranox/btx_lib_list)
[![Maintainability](https://qlty.sh/badges/041ba2c1-37d6-40bb-85a0-ec5a8a0aca0c/maintainability.svg)](https://qlty.sh/gh/bitranox/projects/btx_lib_list)
[![Known Vulnerabilities](https://snyk.io/test/github/bitranox/btx_lib_list/badge.svg)](https://snyk.io/test/github/bitranox/btx_lib_list)

- small list helpers

## Install

```bash
pip install btx_lib_list
```

For alternative install paths (pipx, uv, source builds, etc.), see
[INSTALL.md](./INSTALL.md). All supported methods register both the
`btx_lib_list` and `btx-lib-list` commands on your PATH.

### Python 3.13+ Baseline

- The project now targets **Python 3.13 and newer only**. All compatibility
  shims for older interpreters and legacy tool outputs have been removed; the
  automation helpers now lean on modern conveniences such as `Path.unlink(missing_ok=True)`
  and standard-library `shutil.which()` lookups.
- Runtime dependencies stay on the current stable releases (`rich-click>=1.9.3`
  and `lib_cli_exit_tools>=2.0.0`), while the development extra trims unused
  packages (notably `pytest-asyncio`) and keeps pytest, ruff, pyright, bandit,
  build, twine, codecov-cli, pip-audit, textual, and import-linter pinned to
  their newest majors.
- CI workflows now exercise GitHub's rolling runner images (`ubuntu-latest`,
  `macos-latest`, `windows-latest`) and cover CPython 3.13 alongside the latest
  available 3.x release provided by Actions.


## Usage

The CLI leverages [rich-click](https://github.com/ewels/rich-click) so help output, validation errors, and prompts render with Rich styling while keeping the familiar click ergonomics.
The scaffold keeps a CLI entry point so you can validate packaging flows, but it
currently exposes a single informational command while logging features are
developed:

```bash
btx_lib_list info
btx_lib_list hello
btx_lib_list fail
btx_lib_list --traceback fail
btx-lib-list info
python -m btx_lib_list info
```

For library use you can import the documented helpers directly:

```python
import btx_lib_list

btx_lib_list.emit_greeting()
try:
    btx_lib_list.raise_intentional_failure()
except RuntimeError as exc:
    print(f"caught expected failure: {exc}")

btx_lib_list.print_info()
```

## Development Quickstart

> These steps assume Python 3.13+ (the same baseline enforced by
> `pyproject.toml`).

```bash
make dev           # install the project in editable mode with dev extras
make test          # run linting, type checks, docs/doctests, and pytest
python -m pytest   # thanks to pytest's configured pythonpath, this now works without extra env vars
```

The CLI fixtures exercise the `lib_list` helpers directly, so any changes to
the legacy compatibility layer should be accompanied by matching updates in
`tests/test_lib_list.py`.

## Public API

The helpers are available directly off the package root
(`btx_lib_list.<function_name>`). The summaries below describe the behaviour
and intended use of each helper.

### `btx_lib_list.deduplicate(elements: list[Any]) -> list[Any]`
Removes duplicate, hashable values from `elements` without preserving order. Used when older CLI flows accidentally emit repeat arguments.

Docs: [Module Reference](./docs/systemdesign/module_reference.md#lib_list-utilities)

Example:
```python
>>> from btx_lib_list import deduplicate
>>> deduplicate([])
[]
>>> sorted(deduplicate(['c', 'b', 'a']))
['a', 'b', 'c']
>>> sorted(deduplicate(['b', 'a', 'c', 'b', 'a']))
['a', 'b', 'c']
>>> sorted(deduplicate(['x', 'x', 'x', 'y', 'y']))
['x', 'y']
```


### `btx_lib_list.del_elements_containing(elements: list[str], search_string: str) -> list[str]`
Returns a new list that excludes any string containing `search_string`. Handy for pruning blacklisted patterns before issuing filesystem calls.

Docs: [Module Reference](./docs/systemdesign/module_reference.md#lib_list-utilities)

Example:
```python
>>> from btx_lib_list import del_elements_containing
>>> del_elements_containing(['a', 'abba', 'c'], 'b')
['a', 'c']
>>> del_elements_containing(['a', 'abba', 'c'], 'z')
['a', 'abba', 'c']
>>> del_elements_containing(['a', 'abba', 'c'], '')
['a', 'abba', 'c']
>>> del_elements_containing([], 'b')
[]
```


### `btx_lib_list.filter_contains(elements: list[Any], search_string: str) -> list[str]`
Collects only the string entries that contain `search_string`. When the search text is blank every string element is returned.

Docs: [Module Reference](./docs/systemdesign/module_reference.md#lib_list-utilities)

Example:
```python
>>> from btx_lib_list import filter_contains
>>> filter_contains([], 'bc')
[]
>>> filter_contains(['abcd', 'def', 1, None], 'bc')
['abcd']
>>> filter_contains(['abc'], '')
['abc']
>>> filter_contains(['abc', 123], '')
['abc']
```


### `btx_lib_list.filter_fnmatch(elements: list[Any], search_pattern: str) -> list[str]`
Applies `fnmatch` to each string element and returns the ones that match the shell-style pattern (non-strings are ignored).

Docs: [Module Reference](./docs/systemdesign/module_reference.md#lib_list-utilities)

Example:
```python
>>> from btx_lib_list import filter_fnmatch
>>> filter_fnmatch([], 'a*')
[]
>>> filter_fnmatch(['abc', 'def', 1, None], 'a*')
['abc']
```


### `btx_lib_list.is_element_containing(elements: list[str], search_string: str) -> bool`
Returns `True` if any string in `elements` contains `search_string`, enabling cheap guards before more expensive checks.

Docs: [Module Reference](./docs/systemdesign/module_reference.md#lib_list-utilities)

Example:
```python
>>> from btx_lib_list import is_element_containing
>>> is_element_containing([], '')
False
>>> is_element_containing(['abcd', 'def', 1, None], '')
True
>>> is_element_containing(['abcd', 'def', 1, None], 'bc')
True
>>> is_element_containing(['abcd', 'def', 1, None], 'fg')
False
```


### `btx_lib_list.is_fnmatching(elements: list[Any], search_pattern: str) -> bool`
Boolean probe that reports whether at least one string matches the given `fnmatch` pattern.

Docs: [Module Reference](./docs/systemdesign/module_reference.md#lib_list-utilities)

Example:
```python
>>> from btx_lib_list import is_fnmatching
>>> is_fnmatching([], 'bc')
False
>>> is_fnmatching(['abcd', 'def', 1, None], '*bc*')
True
>>> is_fnmatching(['abcd', 'def', 1, None], '*1*')
False
```


### `btx_lib_list.is_fnmatching_one_pattern(elements: list[Any], search_patterns: list[str]) -> bool`
Iterates over multiple patterns and returns `True` if any of them match one of the string elements.

Docs: [Module Reference](./docs/systemdesign/module_reference.md#lib_list-utilities)

Example:
```python
>>> from btx_lib_list import is_fnmatching_one_pattern
>>> is_fnmatching_one_pattern([], [])
False
>>> is_fnmatching_one_pattern(['abcd', 'def', 1, None], [])
False
>>> is_fnmatching_one_pattern(['abcd', 'def', 1, None], ['*bc*', '*fg*'])
True
>>> is_fnmatching_one_pattern(['abcd', 'def', 1, None], ['*fg*', '*gh*'])
False
```


### `btx_lib_list.substract_all_keep_sorting(minuend: list[Any], subtrahend: list[Any]) -> list[Any]`
Mutates `minuend` by removing every occurrence of values found in `subtrahend` while preserving the original order.

Docs: [Module Reference](./docs/systemdesign/module_reference.md#lib_list-utilities)

Example:
```python
>>> from btx_lib_list import substract_all_keep_sorting
>>> substract_all_keep_sorting([], ['a'])
[]
>>> substract_all_keep_sorting(['a', 'a'], [])
['a', 'a']
>>> minuend = ['a', 'a', 'b']
>>> substract_all_keep_sorting(minuend, ['a', 'c'])
['b']
```


### `btx_lib_list.substract_all_unsorted_fast(minuend: list[Any], subtrahend: list[Any]) -> list[Any]`
Creates a new list representing the set difference between the two lists (order is not guaranteed).

Docs: [Module Reference](./docs/systemdesign/module_reference.md#lib_list-utilities)

Example:
```python
>>> from btx_lib_list import substract_all_unsorted_fast
>>> substract_all_unsorted_fast(['a', 'a', 'b'], ['a', 'c'])
['b']
>>> substract_all_unsorted_fast(['a', 'a', 'b'], ['b'])
['a']
```


### `btx_lib_list.ls_del_empty_elements(ls_elements: list[Any]) -> list[Any]`
Drops any falsey values (`""`, `None`, `0`, etc.) from the provided list.

Docs: [Module Reference](./docs/systemdesign/module_reference.md#lib_list-utilities)

Example:
```python
>>> from btx_lib_list import ls_del_empty_elements
>>> ls_del_empty_elements([])
[]
>>> ls_del_empty_elements(['', ''])
[]
>>> ls_del_empty_elements(['', '', 'a', None, 'b'])
['a', 'b']
>>> ls_del_empty_elements(['   ', '', 'a', None, 'b'])
['   ', 'a', 'b']
>>> ls_del_empty_elements(['   ', '', 'a', None, 'b', 0])
['   ', 'a', 'b']
```


### `btx_lib_list.ls_double_quote_if_contains_blank(ls_elements: list[str]) -> list[str]`
Wraps any string containing spaces in double quotes, keeping shell invocations safe.

Docs: [Module Reference](./docs/systemdesign/module_reference.md#lib_list-utilities)

Example:
```python
>>> from btx_lib_list import ls_double_quote_if_contains_blank
>>> ls_double_quote_if_contains_blank([])
[]
>>> ls_double_quote_if_contains_blank([''])
['']
>>> ls_double_quote_if_contains_blank(['', 'double quote'])
['', '"double quote"']
```


### `btx_lib_list.ls_elements_replace_strings(ls_elements: list[Any], s_old: str, s_new: str) -> list[str]`
Runs `str.replace` on each string element while leaving non-string entries untouched (return type stays `list[str]` to align with consumer expectations).

Docs: [Module Reference](./docs/systemdesign/module_reference.md#lib_list-utilities)

Example:
```python
>>> from btx_lib_list import ls_elements_replace_strings
>>> ls_elements_replace_strings(['a', 'b', 'c', 1], 'a', 'z')
['z', 'b', 'c', 1]
>>> ls_elements_replace_strings([], 'a', 'z')
[]
```


### `btx_lib_list.ls_lstrip_list(list_of_strings: list[str], chars: str = "") -> list[str]`
Returns a slice that omits leading entries equal to `chars` (defaults to empty strings).

Docs: [Module Reference](./docs/systemdesign/module_reference.md#lib_list-utilities)

Example:
```python
>>> from btx_lib_list import ls_lstrip_list
>>> ls_lstrip_list(['', '', 'a', 'b', 'c', '', ''])
['a', 'b', 'c', '', '']
>>> ls_lstrip_list([])
[]
```


### `btx_lib_list.ls_rstrip_elements(ls_elements: list[str], chars: str | None = None) -> list[str]`
Strips the specified characters from the right side of every string element.

Docs: [Module Reference](./docs/systemdesign/module_reference.md#lib_list-utilities)

Example:
```python
>>> from btx_lib_list import ls_rstrip_elements
>>> ls_rstrip_elements(['  a', 'bbb', 'c   '])
['  a', 'bbb', 'c']
>>> ls_rstrip_elements([])
[]
```


### `btx_lib_list.ls_rstrip_list(list_of_strings: list[str], chars: str = "") -> list[str]`
Removes trailing entries that match `chars`, returning the shortened list.

Docs: [Module Reference](./docs/systemdesign/module_reference.md#lib_list-utilities)

Example:
```python
>>> from btx_lib_list import ls_rstrip_list
>>> ls_rstrip_list(['', '', 'a', 'b', 'c', '', ''])
['', '', 'a', 'b', 'c']
>>> ls_rstrip_list([])
[]
```


### `btx_lib_list.ls_strip_afz(ls_elements: list[str] | None) -> list[str]`
Strips surrounding single or double quotes (and leading/trailing whitespace) from each string; returns `[]` when the input is `None`.

Docs: [Module Reference](./docs/systemdesign/module_reference.md#lib_list-utilities)

Example:
```python
>>> from btx_lib_list import ls_strip_afz
>>> ls_strip_afz(['"  a"', "'bbb'", 'ccc', "   'ddd'"])
['  a', 'bbb', 'ccc', 'ddd']
>>> ls_strip_afz([])
[]
>>> ls_strip_afz(None)
[]
```


### `btx_lib_list.ls_strip_elements(ls_elements: list[str], chars: str | None = None) -> list[str]`
Calls `str.strip` on every string element, returning the cleaned list.

Docs: [Module Reference](./docs/systemdesign/module_reference.md#lib_list-utilities)

Example:
```python
>>> from btx_lib_list import ls_strip_elements
>>> ls_strip_elements(['  a', 'bbb', '   '])
['a', 'bbb', '']
>>> ls_strip_elements([])
[]
```


### `btx_lib_list.ls_strip_list(list_of_strings: list[str], chars: str = "") -> list[str]`
Combines `ls_lstrip_list` and `ls_rstrip_list` to remove the sentinel from both ends.

Docs: [Module Reference](./docs/systemdesign/module_reference.md#lib_list-utilities)

Example:
```python
>>> from btx_lib_list import ls_strip_list
>>> ls_strip_list(['', '', 'a', 'b', 'c', '', ''])
['a', 'b', 'c']
```


### `btx_lib_list.ls_substract(ls_minuend: list[Any], ls_subtrahend: list[Any]) -> list[Any]`
Mutates `ls_minuend` by removing a single occurrence of each value found in `ls_subtrahend`.

Docs: [Module Reference](./docs/systemdesign/module_reference.md#lib_list-utilities)

Example:
```python
>>> from btx_lib_list import ls_substract
>>> minuend = ['a', 'a', 'b']
>>> ls_substract(minuend, ['a', 'c'])
['a', 'b']
```


### `btx_lib_list.split_list_into_junks(source_list: list[Any], junk_size: int = sys.maxsize) -> list[list[Any]]`
Splits `source_list` into slices of length `junk_size` (must be >= 1). The final chunk shares references with the original list to avoid copying.

Docs: [Module Reference](./docs/systemdesign/module_reference.md#lib_list-utilities)

Example:
```python
>>> from btx_lib_list import split_list_into_junks
>>> split_list_into_junks([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], junk_size=11)
[[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]]
>>> split_list_into_junks([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], junk_size=3)
[[1, 2, 3], [4, 5, 6], [7, 8, 9], [10]]
>>> split_list_into_junks([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
[[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]]
```


### `btx_lib_list.str_in_list_lower_and_de_double(list_of_strings: list[str]) -> list[str]`
Returns a lowered, deduplicated set of strings (order is not preserved) for case-insensitive comparisons.

Docs: [Module Reference](./docs/systemdesign/module_reference.md#lib_list-utilities)

Example:
```python
>>> from btx_lib_list import str_in_list_lower_and_de_double
>>> sorted(str_in_list_lower_and_de_double(['a', 'b', 'c', 'b', 'A']))
['a', 'b', 'c']
>>> str_in_list_lower_and_de_double([])
[]
```


### `btx_lib_list.str_in_list_non_case_sensitive(string: str, list_of_strings: list[str]) -> bool`
Checks for membership regardless of case by comparing the lowercase variants.

Docs: [Module Reference](./docs/systemdesign/module_reference.md#lib_list-utilities)

Example:
```python
>>> from btx_lib_list import str_in_list_non_case_sensitive
>>> str_in_list_non_case_sensitive('aba', ['abc', 'cde'])
False
>>> str_in_list_non_case_sensitive('aBa', ['abc', 'Aba'])
True
```


### `btx_lib_list.str_in_list_to_lower(list_of_strings: list[str]) -> list[str]`
Lowercases every string element and returns the new list.

Docs: [Module Reference](./docs/systemdesign/module_reference.md#lib_list-utilities)

Example:
```python
>>> from btx_lib_list import str_in_list_to_lower
>>> str_in_list_to_lower(['A', 'b', 'C'])
['a', 'b', 'c']
>>> str_in_list_to_lower([])
[]
```


### `btx_lib_list.strip_and_add_non_empty_args_to_list(*args: str | None) -> list[str]`
Trims each argument, discards blanks/`None`, and returns the remaining non-empty strings in order.

Docs: [Module Reference](./docs/systemdesign/module_reference.md#lib_list-utilities)

Example:
```python
>>> from btx_lib_list import strip_and_add_non_empty_args_to_list
>>> strip_and_add_non_empty_args_to_list('a  ', '  b', 'c', '', '  ')
['a', 'b', 'c']
>>> strip_and_add_non_empty_args_to_list()
[]
```



## Performance Reference

| Helper group | Representative functions | Complexity | Notes |
| --- | --- | --- | --- |
| Deduplication | `deduplicate`, `str_in_list_lower_and_de_double` | O(n) | Uses `set`; ordering and duplicate survivors are not preserved. |
| Filtering | `filter_contains`, `filter_fnmatch`, `del_elements_containing` | O(n) | Single pass over inputs; non-strings skipped where appropriate. |
| Ordered subtraction | `substract_all_keep_sorting`, `ls_substract` | O(n·m)`†` | Relies on repeated `list.remove`; best for small collections. |
| Unordered subtraction | `substract_all_unsorted_fast` | O(n) | Builds a `set`; removes duplicates of survivors. |
| Chunking | `split_list_into_junks` | O(n) | Iterates once and reuses references for the final chunk. |
| String trimming | `ls_strip_elements`, `ls_rstrip_elements`, `ls_strip_list` | O(n) | Applies string trimming per element. |

`†` `n` = length of the minuend and `m` = distinct subtrahend entries. For large lists prefer the unordered subtraction helper or precompute a lookup set.

## Further Documentation

- [Install Guide](./INSTALL.md)
- [Development Handbook](./DEVELOPMENT.md)
- [Contributor Guide](./CONTRIBUTING.md)
- [Changelog](./CHANGELOG.md)
- [Module Reference](./docs/systemdesign/module_reference.md)
- [License](./LICENSE)

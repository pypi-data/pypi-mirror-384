"""List-processing helpers preserved for compatibility with legacy workflows.

Purpose
    Keep the historical convenience functions available to downstream CLI and
    scripting tools while conforming to the repository's clean-code guidance.

Contents
    * Set-like helpers (:func:`deduplicate`, :func:`substract_all_unsorted_fast`).
    * Filtering primitives (:func:`filter_contains`, :func:`filter_fnmatch`).
    * String trimming/quoting helpers (:func:`ls_strip_afz`, etc.).
    * Chunking/normalisation utilities (:func:`split_list_into_junks`,
      :func:`str_in_list_lower_and_de_double`).

Performance
    Unless otherwise noted, helpers iterate the input once (``O(n)``). The
    following are worth highlighting:

    * :func:`deduplicate` and :func:`substract_all_unsorted_fast` build a
      ``set`` internally (``O(n)``) which also removes duplicate survivors.
    * :func:`split_list_into_junks` walks the list once (``O(n)``) while keeping
      references to the original slices.
    * String trimming helpers operate element-wise in ``O(n)`` with small
      constants.

System Role
    The CLI commands (and external callers that embed this package) rely on
    these helpers for list hygiene before invoking richer domain logic. Moving
    them here keeps the public API stable while new behaviours grow elsewhere
    in the codebase.
"""

from __future__ import annotations

import fnmatch
import sys
from typing import Any, Optional, Union

__all__ = [
    "deduplicate",
    "del_elements_containing",
    "filter_contains",
    "filter_fnmatch",
    "is_element_containing",
    "is_fnmatching",
    "is_fnmatching_one_pattern",
    "substract_all_keep_sorting",
    "substract_all_unsorted_fast",
    "ls_del_empty_elements",
    "ls_double_quote_if_contains_blank",
    "ls_elements_replace_strings",
    "ls_lstrip_list",
    "ls_rstrip_elements",
    "ls_rstrip_list",
    "ls_strip_afz",
    "ls_strip_elements",
    "ls_strip_list",
    "ls_substract",
    "split_list_into_junks",
    "str_in_list_lower_and_de_double",
    "str_in_list_non_case_sensitive",
    "str_in_list_to_lower",
    "strip_and_add_non_empty_args_to_list",
]


def deduplicate(elements: list[Any]) -> list[Any]:
    """Remove duplicate values without caring about order preservation.

    Why
        CLI option parsing from the legacy project emitted repeated values; this
        helper keeps downstream consumers resilient to that behaviour.

    What
        Converts the list into a ``set`` and back, ensuring each hashable value
        appears at most once.

    Parameters
        elements:
            List of hashable items. The input list is returned unchanged when it
            is empty.

    Returns
        A list containing one instance of every unique element. Ordering follows
        Python's ``set`` semantics and is therefore not guaranteed.

    Side Effects
        None.

    Examples
        >>> deduplicate([])
        []
        >>> sorted(deduplicate(['c','b','a']))
        ['a', 'b', 'c']
        >>> sorted(deduplicate(['b','a','c','b','a']))
        ['a', 'b', 'c']
        >>> sorted(deduplicate(['x','x','x','y','y']))
        ['x', 'y']
    """

    if not elements:
        return []
    return list(set(elements))


def del_elements_containing(elements: list[str], search_string: str) -> list[str]:
    """Filter out strings that contain a forbidden substring.

    Why
        Older release scripts used this helper to prune blacklisted patterns
        from dynamically generated include lists.

    What
        Iterates through the list and keeps only items that do **not** contain
        ``search_string``. When either argument is empty, the original list is
        returned untouched for compatibility.

    Parameters
        elements:
            List of candidate strings; reused when the list is empty.
        search_string:
            Substring whose presence removes items from the result.

    Returns
        A list comprising all strings that lack the given substring.

    Side Effects
        None; the input list is not mutated.

    Examples
        >>> del_elements_containing(['a', 'abba', 'c'], 'b')
        ['a', 'c']
        >>> del_elements_containing(['a', 'abba', 'c'], 'z')
        ['a', 'abba', 'c']
        >>> del_elements_containing(['a', 'abba', 'c'], '')
        ['a', 'abba', 'c']
        >>> del_elements_containing([], 'b')
        []
    """
    if not elements or not search_string:
        return elements

    return [element for element in elements if search_string not in element]


def filter_contains(elements: list[Any], search_string: str) -> list[str]:
    """Return string elements that contain a requested fragment.

    Why
        Acts as the inverse to :func:`del_elements_containing` for scenarios
        where only matching items should proceed to downstream tooling.

    What
        Scans the list and returns a new list with the elements that are
        strings containing ``search_string``. Non-string entries are ignored.

    Parameters
        elements:
            Any iterable of mixed values. Empty lists are passed through.
        search_string:
            Substring to locate within string elements.

    Returns
        New list holding only the matching string elements. When
        ``search_string`` is empty the function returns every string element in
        the input (non-strings are still dropped).

    Side Effects
        None.

    Examples
        >>> filter_contains([], 'bc')
        []
        >>> filter_contains(['abcd', 'def', 1, None], 'bc')
        ['abcd']
    """
    if not elements:
        return []

    if not search_string:
        return [element for element in elements if isinstance(element, str)]

    return [element for element in elements if isinstance(element, str) and search_string in element]


def filter_fnmatch(elements: list[Any], search_pattern: str) -> list[str]:
    """Return strings that satisfy an ``fnmatch`` pattern.

    Why
        File-globbing support in deployment scripts reused this helper to avoid
        rewriting pattern checks throughout the codebase.

    What
        Applies :func:`fnmatch.fnmatch` to each string element and retains the
        ones that match ``search_pattern``. Non-string entries are skipped.

    Parameters
        elements:
            Sequence of mixed values to inspect.
        search_pattern:
            Shell-style pattern understood by :mod:`fnmatch`.

    Returns
        List of matching string items. Empty input results in an empty list.

    Side Effects
        None.

    Examples
        >>> filter_fnmatch([], 'a*')
        []
        >>> filter_fnmatch(['abc', 'def', 1, None], 'a*')
        ['abc']
    """
    if not elements:
        return elements

    return [element for element in elements if isinstance(element, str) and fnmatch.fnmatch(element, search_pattern)]


def is_element_containing(elements: list[str], search_string: str) -> bool:
    """Report whether any string contains the requested fragment.

    Why
        Provides the boolean probe used by older code paths to skip expensive
        filesystem checks when a quick list scan suffices.

    What
        Returns ``True`` if at least one element is a string that includes
        ``search_string``. An empty list yields ``False``.

    Parameters
        elements:
            Values to inspect, typically strings.
        search_string:
            Substring to locate. Blank values treat empty strings as matches.

    Returns
        ``True`` when a matching string exists, otherwise ``False``.

    Side Effects
        None.

    Examples
        >>> is_element_containing([], '')
        False

        >>> is_element_containing(['abcd', 'def', 1, None], '')
        True

        >>> is_element_containing(['abcd', 'def', 1, None], 'bc')
        True

        >>> is_element_containing(['abcd', 'def', 1, None], 'fg')
        False
    """
    if not elements:
        return False

    return any(search_string in element for element in elements if isinstance(element, str))  # pyright: ignore[reportUnnecessaryIsInstance]


def is_fnmatching(elements: list[Any], search_pattern: str) -> bool:
    """Return ``True`` when any element matches an ``fnmatch`` pattern.

    Why
        Allows callers to guard path-heavy operations with a quick shell-style
        glob check.

    What
        Evaluates :func:`fnmatch.fnmatch` for every string element and short
        circuits on the first match.

    Parameters
        elements:
            Mixed list of candidate values.
        search_pattern:
            Shell glob expression passed to :mod:`fnmatch`.

    Returns
        ``True`` when a matching string exists, otherwise ``False``.

    Side Effects
        None.

    Examples
        >>> is_fnmatching([], 'bc')
        False
        >>> is_fnmatching(['abcd', 'def', 1, None], '*bc*')
        True
        >>> is_fnmatching(['abcd', 'def', 1, None], '*1*')
        False

    """
    if not elements:
        return False

    return any(fnmatch.fnmatch(element, search_pattern) for element in elements if isinstance(element, str))


def is_fnmatching_one_pattern(elements: list[Any], search_patterns: list[str]) -> bool:
    """Check a list of patterns for at least one match within the elements.

    Why
        Bundled pattern checks reduce the boilerplate around nested ``if``/``or``
        logic in legacy scripts.

    What
        Returns ``True`` if any pattern in ``search_patterns`` matches at least
        one string in ``elements``. Empty inputs never match.

    Parameters
        elements:
            Values to test.
        search_patterns:
            ``fnmatch``-compatible patterns; an empty list yields ``False``.

    Returns
        Boolean indicating whether any pattern matched any string element.

    Side Effects
        None.

    Examples
        >>> is_fnmatching_one_pattern([], [])
        False

        >>> is_fnmatching_one_pattern(['abcd', 'def', 1, None], [])
        False

        >>> is_fnmatching_one_pattern(['abcd', 'def', 1, None], ['*bc*', '*fg*'])
        True

        >>> is_fnmatching_one_pattern(['abcd', 'def', 1, None], ['*fg*', '*gh*'])
        False
    """
    if not elements or not search_patterns:
        return False

    return any(is_fnmatching(elements, search_pattern) for search_pattern in search_patterns)


def substract_all_keep_sorting(minuend: list[Any], subtrahend: list[Any]) -> list[Any]:
    """Remove all occurrences of specific values while preserving order.

    Why
        Keeps deterministic ordering for consumers that compare results against
        previously sorted state.

    What
        Mutates ``minuend`` in place by removing every occurrence of items that
        appear in ``subtrahend``.

    Parameters
        minuend:
            List to prune. Returned after mutation.
        subtrahend:
            Values whose occurrences should be removed.

    Returns
        The mutated ``minuend`` list for fluency.

    Side Effects
        ``minuend`` is modified in place.

    Examples
        >>> substract_all_keep_sorting([], ['a'])
        []
        >>> substract_all_keep_sorting(['a', 'a'], [])
        ['a', 'a']

        >>> my_l_minuend = ['a','a','b']
        >>> my_l_subtrahend = ['a','c']
        >>> substract_all_keep_sorting(my_l_minuend, my_l_subtrahend)
        ['b']
    """
    if not minuend or not subtrahend:
        return minuend

    subtrahend_dedup = set(subtrahend)
    retained = [element for element in minuend if element not in subtrahend_dedup]
    minuend[:] = retained
    return minuend


def substract_all_unsorted_fast(minuend: list[Any], subtrahend: list[Any]) -> list[Any]:
    """Return the set difference of two lists without keeping order.

    Why
        Provides a faster alternative to
        :func:`substract_all_keep_sorting` when ordering is irrelevant.

    What
        Converts both lists into ``set`` objects (which also causes deduplication!), subtracts them, and emits a
        new list with the remaining values.

    Parameters
        minuend:
            Source values.
        subtrahend:
            Values to remove.

    Returns
        Fresh list containing the set difference.

    Side Effects
        None; the inputs are not modified.

    Examples
        >>> my_minuend = ['a','a','b']
        >>> my_subtrahend = ['a','c']
        >>> substract_all_unsorted_fast(my_minuend, my_subtrahend)
        ['b']
        >>> my_minuend = ['a','a','b']
        >>> my_subtrahend = ['b']
        >>> substract_all_unsorted_fast(my_minuend, my_subtrahend)
        ['a']

    """
    if not minuend:
        return minuend

    return list(set(minuend) - set(subtrahend))


def ls_del_empty_elements(ls_elements: list[Any]) -> list[Any]:
    """Remove empty or falsey entries from a list.

    Why
        Keeps downstream formatting code from handling empty strings or ``None``
        values repeatedly.

    What
        Uses :func:`filter` to drop any value that evaluates to ``False``.

    Parameters
        ls_elements:
            Sequence potentially containing empty strings, ``None``, or zeros.

    Returns
        New list with only truthy values.

    Side Effects
        None.

    Examples
        >>> ls_del_empty_elements([])
        []
        >>> ls_del_empty_elements(['',''])
        []
        >>> ls_del_empty_elements(['','','a',None,'b'])
        ['a', 'b']
        >>> ls_del_empty_elements(['   ','','a',None,'b'])
        ['   ', 'a', 'b']
        >>> ls_del_empty_elements(['   ','','a',None,'b',0])
        ['   ', 'a', 'b']

    """

    return list(filter(None, ls_elements))


def ls_double_quote_if_contains_blank(ls_elements: list[str]) -> list[str]:
    """Wrap any string containing a space in double quotes.

    Why
        Helps produce shell-safe arguments for commands executed by the legacy
        automation scripts.

    What
        Returns a new list where strings containing spaces are quoted.

    Parameters
        ls_elements:
            Strings to analyse; empty lists return an empty list.

    Returns
        A list with problematic elements quoted.

    Side Effects
        None.

    Examples
        >>> ls_double_quote_if_contains_blank([])
        []
        >>> ls_double_quote_if_contains_blank([''])
        ['']
        >>> ls_double_quote_if_contains_blank(['', 'double quote'])
        ['', '"double quote"']

    """
    if not ls_elements:
        return list(ls_elements or [])

    return [f'"{s_element}"' if " " in s_element else s_element for s_element in ls_elements]


def ls_elements_replace_strings(ls_elements: list[Any], s_old: str, s_new: str) -> list[str]:
    """Replace substrings within each string element.

    Why
        Keeps legacy formatting rules centralised instead of duplicating
        ``str.replace`` loops.

    What
        Applies ``replace`` to every string element and leaves non-string values
        untouched.

    Parameters
        ls_elements:
            List containing values of any type; only string entries are transformed.
        s_old:
            Substring to replace.
        s_new:
            Replacement value used by :meth:`str.replace`.

    Returns
        List[str] typed collection with replaced substrings. Non-string entries are
        returned untouched at runtime, so callers should ensure downstream users
        expect mixed contents.

    Side Effects
        None.

    Examples
        >>> ls_elements_replace_strings(['a', 'b', 'c', 1], 'a', 'z')
        ['z', 'b', 'c', 1]
        >>> ls_elements_replace_strings([], 'a', 'z')
        []

    """

    if not ls_elements:
        return ls_elements

    return [s_element.replace(s_old, s_new) if isinstance(s_element, str) else s_element for s_element in ls_elements]


def ls_lstrip_list(list_of_strings: list[str], chars: str = "") -> list[str]:
    """Remove leading entries that equal the supplied filler value.

    Why
        Keeps consumers from repeatedly trimming placeholder entries before
        processing meaningful values.

    What
        Walks the list from the front until encountering a value that differs
        from ``chars``.

    Parameters
        list_of_strings:
            List to trim.
        chars:
            Sentinel value signifying elements to remove (defaults to empty
            string).

    Returns
        New list view starting from the first non-sentinel element.

    Side Effects
        None; returns a slice.

    Examples
        >>> testlist = ['','','a','b','c','','']
        >>> ls_lstrip_list(testlist)
        ['a', 'b', 'c', '', '']
        >>> testlist = []
        >>> ls_lstrip_list(testlist)
        []
    """
    if not list_of_strings:
        return list_of_strings

    index = 0
    length = len(list_of_strings)
    while index < length and list_of_strings[index] == chars:
        index += 1
    return list_of_strings[index:]


def ls_rstrip_elements(ls_elements: list[str], chars: Union[None, str] = None) -> list[str]:
    """Strip trailing characters from every string element.

    Why
        Reusable helper for trimming whitespace or custom padding before writing
        values back to configuration files.

    What
        Calls :meth:`str.rstrip` on each string.

    Parameters
        ls_elements:
            List of strings to clean.
        chars:
            Optional characters to strip; ``None`` mirrors :meth:`str.rstrip`
            defaults.

    Returns
        New list with the stripped values.

    Side Effects
        None.

    Examples
        >>> ls_rstrip_elements(['  a','bbb','c   '])
        ['  a', 'bbb', 'c']
        >>> ls_rstrip_elements([])
        []

    """

    if not ls_elements:
        return []

    return [s_element.rstrip(chars) for s_element in ls_elements]


def ls_rstrip_list(list_of_strings: list[str], chars: str = "") -> list[str]:
    """Remove trailing filler entries from the list.

    Why
        Complements :func:`ls_lstrip_list` when both ends need pruning before
        serialising output.

    What
        Slices the list from the end while values equal ``chars``.

    Parameters
        list_of_strings:
            List to process.
        chars:
            Sentinel value denoting entries to discard (empty string by
            default).

    Returns
        List containing the original values minus the trailing sentinel block.

    Side Effects
        None.

    Examples
        >>> testlist = ['','','a','b','c','','']
        >>> ls_rstrip_list(testlist)
        ['', '', 'a', 'b', 'c']
        >>> testlist = []
        >>> ls_rstrip_list(testlist)
        []

    """
    if not list_of_strings:
        return list_of_strings

    index = len(list_of_strings)
    while index and list_of_strings[index - 1] == chars:
        index -= 1
    return list_of_strings[:index]


def ls_strip_afz(ls_elements: Optional[list[str]]) -> list[str]:
    """Strip matching quotes from the start and end of each string.

    Why
        Legacy importers frequently produced quoted parameters; this helper
        normalises them for downstream processing.

    What
        Trims whitespace then removes surrounding single or double quotes when
        both ends match.

    Parameters
        ls_elements:
            List of strings or ``None``. ``None`` yields an empty list.

    Returns
        New list without surrounding quotes.

    Side Effects
        None.

    Examples
        >>> ls_strip_afz(['"  a"',"'bbb'",'ccc', "   'ddd'"])
        ['  a', 'bbb', 'ccc', 'ddd']
        >>> ls_strip_afz([])
        []
        >>> ls_strip_afz(None)
        []

    """

    # ['"  a"',"'bbb'",'ccc'] --> ['  a','bbb','ccc']

    if not ls_elements:
        return []

    def _strip_quotes(value: str) -> str:
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            return value[1:-1]
        return value

    return [_strip_quotes(s_element) for s_element in ls_elements]


def ls_strip_elements(ls_elements: list[str], chars: Union[None, str] = None) -> list[str]:
    """Strip leading and trailing characters from each string.

    Why
        Common normalisation step before writing values into templates or
        command arguments.

    What
        Invokes :meth:`str.strip` on each element.

    Parameters
        ls_elements:
            List of strings to trim.
        chars:
            Optional characters to remove. ``None`` uses default whitespace.

    Returns
        List containing stripped strings.

    Side Effects
        None.

    Examples
        >>> ls_strip_elements(['  a','bbb','   '])
        ['a', 'bbb', '']
        >>> ls_strip_elements([])
        []

    """

    if not ls_elements:
        return []

    return [s_element.strip(chars) for s_element in ls_elements]


def ls_strip_list(list_of_strings: list[str], chars: str = "") -> list[str]:
    """Trim leading and trailing sentinel values in one call.

    Why
        Provides a convenience wrapper combining :func:`ls_lstrip_list` and
        :func:`ls_rstrip_list` for scenarios that require both operations.

    What
        Invokes the two directional helpers sequentially and returns the
        cleaned list.

    Parameters
        list_of_strings:
            Target list to trim.
        chars:
            Filler value that should be removed from both edges.

    Returns
        List excluded of leading and trailing filler entries.

    Side Effects
        None.

    Examples
        >>> testlist = ['','','a','b','c','','']
        >>> ls_strip_list(testlist)
        ['a', 'b', 'c']

    """

    list_of_strings = ls_lstrip_list(list_of_strings, chars)
    list_of_strings = ls_rstrip_list(list_of_strings, chars)
    return list_of_strings


def ls_substract(ls_minuend: list[Any], ls_subtrahend: list[Any]) -> list[Any]:
    """Remove a single occurrence of each value in ``ls_subtrahend``.

    Why
        Used when the caller wants multi-set subtraction instead of full
        removal.

    What
        Iterates through ``ls_subtrahend`` and removes the first matching value
        from ``ls_minuend`` each time.

    Parameters
        ls_minuend:
            List to mutate.
        ls_subtrahend:
            Values to subtract.

    Returns
        The mutated ``ls_minuend`` for fluent chaining.

    Side Effects
        ``ls_minuend`` is modified in place.

    Examples
        >>> l_minuend = ['a','a','b']
        >>> l_subtrahend = ['a','c']
        >>> ls_substract(l_minuend, l_subtrahend)
        ['a', 'b']

    """
    for s_element in ls_subtrahend:
        if s_element in ls_minuend:
            ls_minuend.remove(s_element)
    return ls_minuend


def split_list_into_junks(source_list: list[Any], junk_size: int = sys.maxsize) -> list[list[Any]]:
    """Split a list into evenly sized chunks.

    Why
        Power users reused this helper to throttle large operations into
        manageable batches without copying data unnecessarily.

    What
        Returns successive slices of ``junk_size`` elements, including a final
        slice containing the remainder. The final sub-list reuses the original
        list reference to avoid extra allocations.

    Preconditions
        ``junk_size`` must be >= 1. Invalid values raise :class:`ValueError` so
        callers fail fast instead of entering an infinite loop.

    Parameters
        source_list:
            List to partition.
        junk_size:
            Maximum size of each chunk. Defaults to ``sys.maxsize`` which
            effectively returns the original list.

    Returns
        List of sub-lists representing the chunks.

    Side Effects
        None beyond returning references to existing list segments.

    Examples
        >>> result = split_list_into_junks([1,2,3,4,5,6,7,8,9,10],junk_size=11)
        >>> assert result == [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]]

        >>> result = split_list_into_junks([1,2,3,4,5,6,7,8,9,10],junk_size=3)
        >>> assert result == [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10]]

        >>> result = split_list_into_junks([1,2,3,4,5,6,7,8,9,10])
        >>> assert result == [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]]

    """
    if junk_size <= 0:
        msg = "junk_size must be a positive integer"
        raise ValueError(msg)

    l_lists: list[list[Any]] = []
    remaining_list: list[Any] = source_list

    while len(remaining_list) > junk_size:
        part_list = remaining_list[:junk_size]
        l_lists.append(part_list)
        remaining_list = remaining_list[junk_size:]
    l_lists.append(remaining_list)
    return l_lists


def str_in_list_lower_and_de_double(list_of_strings: list[str]) -> list[str]:
    """Normalise case and remove duplicates without preserving order.

    Why
        Often used when constructing case-insensitive allow lists for CLI
        options.

    What
        Lowercases all strings and feeds them through :func:`deduplicate`.

    Parameters
        list_of_strings:
            Strings to normalise.

    Returns
        List of unique, lowercased strings. Ordering is not guaranteed.

    Side Effects
        None.

    Examples
        str_in_list_lower_and_de_double(['a', 'b', 'c', 'b', 'A'])  --> 'a', 'b', 'c'

        >>> assert len (str_in_list_lower_and_de_double(['a', 'b', 'c', 'b', 'A'])) == 3
        >>> str_in_list_lower_and_de_double([])
        []

    """
    if not list_of_strings:
        return list_of_strings
    list_of_strings_lower = str_in_list_to_lower(list_of_strings=list_of_strings)
    list_of_strings_lower_and_de_double = deduplicate(elements=list_of_strings_lower)
    return list_of_strings_lower_and_de_double


def str_in_list_non_case_sensitive(string: str, list_of_strings: list[str]) -> bool:
    """Case-insensitive membership test.

    Why
        Complements the normalisation helpers by providing an immediate lookup.

    What
        Lowercases both the search value and the candidate list, then performs a
        membership test.

    Parameters
        string:
            Value to find.
        list_of_strings:
            Candidate list.

    Returns
        ``True`` if a case-insensitive match exists, otherwise ``False``.

    Side Effects
        None.

    Examples
        >>> str_in_list_non_case_sensitive('aba',['abc','cde'])
        False
        >>> str_in_list_non_case_sensitive('aBa',['abc','Aba'])
        True
    """
    lowered_string = string.lower()
    lower_candidates = [my_string.lower() for my_string in list_of_strings]
    return lowered_string in lower_candidates


def str_in_list_to_lower(list_of_strings: list[str]) -> list[str]:
    """Lowercase every string in the provided list.

    Why
        Shared primitive used before storing values in case-insensitive data
        structures.

    What
        Returns a new list containing lowercased copies of each string.

    Parameters
        list_of_strings:
            Values to normalise.

    Returns
        List of lowercased strings.

    Side Effects
        None.

    Examples
        >>> str_in_list_to_lower(['A','b','C'])
        ['a', 'b', 'c']
        >>> str_in_list_to_lower([])
        []

    """
    if not list_of_strings:
        return list_of_strings

    return [string.lower() for string in list_of_strings]


def strip_and_add_non_empty_args_to_list(*args: Optional[str]) -> list[Any]:
    """Collect trimmed arguments into a list while skipping blanks.

    Why
        Original CLI glue used this helper to normalise optional text fields
        before dispatching to adapters.

    What
        Strips whitespace from each argument, ignores ``None`` and empty
        results, and returns the remaining values.

    Parameters
        args:
            Arbitrary optional strings.

    Returns
        List of stripped, non-empty strings.

    Side Effects
        None.

    Examples
        >>> strip_and_add_non_empty_args_to_list('a  ', '  b', 'c', '', '  ')
        ['a', 'b', 'c']

        >>> strip_and_add_non_empty_args_to_list()
        []

        >>> strip_and_add_non_empty_args_to_list()
        []


    """

    if not args:
        return []

    ls_args: list[str] = []
    for s_arg in args:
        if s_arg is None:
            continue
        stripped = s_arg.strip()
        if stripped:
            ls_args.append(stripped)
    return ls_args

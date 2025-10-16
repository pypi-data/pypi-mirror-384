from __future__ import annotations

from typing import Any, List, cast

import pytest

import btx_lib_list
from btx_lib_list import lib_list


def test_deduplicate_removes_duplicates() -> None:
    result = lib_list.deduplicate(["b", "a", "b"])
    assert set(result) == {"a", "b"}
    assert len(result) == 2
    assert lib_list.deduplicate([]) == []


def test_del_elements_containing_filters_when_search_string_provided() -> None:
    assert lib_list.del_elements_containing(["a", "abba", "c"], "b") == ["a", "c"]
    original = ["a", "abba", "c"]
    assert lib_list.del_elements_containing(original, "") is original


def test_filter_contains_returns_matching_strings_only() -> None:
    assert lib_list.filter_contains(["abcd", "def", 1], "bc") == ["abcd"]
    assert lib_list.filter_contains(["abc"], "") == ["abc"]
    assert lib_list.filter_contains(["abc", 123], "") == ["abc"]


def test_filter_fnmatch_applies_pattern_matching() -> None:
    assert lib_list.filter_fnmatch(["abc", "def", 1], "a*") == ["abc"]
    assert lib_list.filter_fnmatch([], "*") == []


def test_is_element_containing_detects_matches() -> None:
    assert lib_list.is_element_containing(["abc", "def"], "bc") is True
    assert lib_list.is_element_containing(["abc", "def"], "xy") is False


def test_is_fnmatching_behaves_like_fnmatch() -> None:
    assert lib_list.is_fnmatching(["abc", "def"], "*bc*") is True
    assert lib_list.is_fnmatching([], "*") is False


def test_is_fnmatching_one_pattern_checks_all_patterns() -> None:
    assert lib_list.is_fnmatching_one_pattern(["abc"], ["*bc*", "*zz*"])
    assert not lib_list.is_fnmatching_one_pattern(["abc"], [])


def test_substract_all_keep_sorting_mutates_source_list() -> None:
    minuend = ["a", "b", "b"]
    result = lib_list.substract_all_keep_sorting(minuend, ["b"])
    assert result is minuend
    assert minuend == ["a"]


def test_substract_all_unsorted_fast_uses_set_difference() -> None:
    assert sorted(lib_list.substract_all_unsorted_fast(["a", "a", "b"], ["a"])) == ["b"]


def test_ls_del_empty_elements_removes_falsey_entries() -> None:
    assert lib_list.ls_del_empty_elements(["", None, "a", 0]) == ["a"]


def test_ls_double_quote_if_contains_blank_quotes_only_needed_values() -> None:
    assert lib_list.ls_double_quote_if_contains_blank(["simple", "has space"]) == ["simple", '"has space"']


def test_ls_elements_replace_strings_replaces_only_strings() -> None:
    values: List[Any] = ["abc", 1]
    result = lib_list.ls_elements_replace_strings(cast(List[str], values), "a", "z")
    assert result == ["zbc", 1]


def test_ls_lstrip_and_rstrip_list_trim_markers() -> None:
    values = ["", "", "a", "", ""]
    assert lib_list.ls_lstrip_list(values) == ["a", "", ""]
    assert lib_list.ls_rstrip_list(values) == ["", "", "a"]


def test_ls_strip_afz_removes_wrapping_quotes() -> None:
    assert lib_list.ls_strip_afz(['"hello"', "'world'"]) == ["hello", "world"]
    assert lib_list.ls_strip_afz(None) == []


def test_ls_strip_elements_and_list_trim_whitespace() -> None:
    assert lib_list.ls_strip_elements(["  a", "b  "]) == ["a", "b"]
    assert lib_list.ls_strip_list(["", "a", ""]) == ["a"]


def test_ls_substract_removes_only_single_occurrences() -> None:
    minuend = ["a", "a", "b"]
    lib_list.ls_substract(minuend, ["a", "z"])
    assert minuend == ["a", "b"]


def test_split_list_into_junks_respects_chunk_size() -> None:
    data = list(range(7))
    result = lib_list.split_list_into_junks(data, junk_size=3)
    assert result == [data[:3], data[3:6], data[6:]]


def test_str_in_list_lower_and_de_double_normalises_and_deduplicates() -> None:
    outcome = lib_list.str_in_list_lower_and_de_double(["A", "b", "B"])
    assert set(outcome) == {"a", "b"}


def test_str_in_list_non_case_sensitive_checks_membership() -> None:
    assert lib_list.str_in_list_non_case_sensitive("a", ["A", "b"]) is True
    assert lib_list.str_in_list_non_case_sensitive("c", ["A", "b"]) is False


def test_str_in_list_to_lower_handles_empty_sequences() -> None:
    assert lib_list.str_in_list_to_lower(["A", "B"]) == ["a", "b"]
    assert lib_list.str_in_list_to_lower([]) == []


def test_strip_and_add_non_empty_args_to_list_filters_and_strips() -> None:
    assert lib_list.strip_and_add_non_empty_args_to_list(" a ", None, "", "b") == ["a", "b"]
    assert lib_list.strip_and_add_non_empty_args_to_list() == []


def test_package_root_exports_match_module() -> None:
    for name in lib_list.__all__:
        assert getattr(btx_lib_list, name) is getattr(lib_list, name)


@pytest.mark.parametrize(
    "sequence, pattern, expected",
    [
        (["alpha", "beta"], "*ta", True),
        (["alpha", "beta"], "*zz", False),
    ],
)
def test_is_fnmatching_parametrized(sequence: list[str], pattern: str, expected: bool) -> None:
    assert lib_list.is_fnmatching(sequence, pattern) is expected


@pytest.mark.parametrize(
    "sequence, search, expected",
    [
        (["alpha", "beta"], "a", True),
        (["alpha", "beta"], "z", False),
    ],
)
def test_is_element_containing_parametrized(sequence: list[str], search: str, expected: bool) -> None:
    assert lib_list.is_element_containing(sequence, search) is expected


@pytest.mark.parametrize(
    "junk_size",
    [1, 2, 5],
)
def test_split_list_into_junks_handles_various_sizes(junk_size: int) -> None:
    data = list(range(5))
    expected: list[list[int]] = []
    for index in range(0, len(data), junk_size):
        expected.append(data[index : index + junk_size])
    assert lib_list.split_list_into_junks(data, junk_size=junk_size) == expected


def test_split_list_into_junks_returns_reference_for_remainder() -> None:
    data: List[Any] = []
    parts = lib_list.split_list_into_junks(data)
    assert parts == [data]
    assert parts[0] is data


def test_split_list_into_junks_rejects_non_positive_sizes() -> None:
    with pytest.raises(ValueError):
        lib_list.split_list_into_junks([1, 2, 3], junk_size=0)

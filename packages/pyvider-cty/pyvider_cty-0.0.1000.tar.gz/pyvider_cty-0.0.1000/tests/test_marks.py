# tests/test_marks.py
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from pyvider.cty.marks import CtyMark


class TestCtyMark:
    def test_mark_creation(self) -> None:
        mark = CtyMark("sensitive")
        assert mark.name == "sensitive"
        assert mark.details is None

    def test_mark_creation_with_details(self) -> None:
        details = {"source": "user"}
        mark = CtyMark("sensitive", details)
        assert mark.name == "sensitive"
        assert mark.details == frozenset(details.items())

    def test_mark_representation(self) -> None:
        mark = CtyMark("sensitive")
        assert repr(mark) == "CtyMark('sensitive')"
        details = {"source": "user"}
        mark_with_details = CtyMark("sensitive", details)
        assert repr(mark_with_details) == "CtyMark('sensitive', {'source': 'user'})"

    def test_mark_string_representation(self) -> None:
        mark = CtyMark("sensitive")
        assert str(mark) == "sensitive"

    def test_mark_equality(self) -> None:
        mark1 = CtyMark("sensitive")
        mark2 = CtyMark("sensitive")
        mark3 = CtyMark("public")
        assert mark1 == mark2
        assert mark1 != mark3

    def test_mark_equality_with_details(self) -> None:
        details1 = {"source": "user"}
        details2 = {"source": "user"}
        details3 = {"source": "system"}
        mark1 = CtyMark("sensitive", details1)
        mark2 = CtyMark("sensitive", details2)
        mark3 = CtyMark("sensitive", details3)
        assert mark1 == mark2
        assert mark1 != mark3

    def test_convert_details(self) -> None:
        # Test with a list
        mark_list = CtyMark("test", ["a", "b"])
        assert mark_list.details == frozenset(["a", "b"])

        # Test with a set
        mark_set = CtyMark("test", {"a", "b"})
        assert mark_set.details == frozenset({"a", "b"})

        # Test with a tuple
        mark_tuple = CtyMark("test", ("a", "b"))
        assert mark_tuple.details == frozenset(("a", "b"))

        # Test with a single value
        mark_single = CtyMark("test", "a")
        assert mark_single.details == frozenset(["a"])


# 🐍⛓️🤔🪄

"""Tests for ctitools."""

import pytest

from berhoel.ctitools import CTI, Papers, PaperInfo


@pytest.mark.parametrize(
    ("char", "expected"), [("c", Papers.ct), ("i", Papers.iX), ("x", Papers.NONE)]
)
def test_papers_from_char(char: str, expected: Papers):
    assert Papers.from_char(char) == expected


@pytest.mark.parametrize(
    ("inp", "reference"),
    [
        ("c03", PaperInfo(Papers.ct, 3)),
        ("i04", PaperInfo(Papers.iX, 4)),
        ("xxx", PaperInfo(Papers.NONE, -1)),
    ],
)
def test_paper_info_from_match(inp: str, reference: PaperInfo):
    match = CTI.PAPER_YEAR_RE.match(inp)
    assert PaperInfo.from_match(match) == reference

"""Basic tests for generating BibTex entries from c't and iX articles."""

from __future__ import annotations

from berhoel.ctitools import PaperInfo

# First party library imports.
from berhoel.ctitools.cti2bibtex import BiBTeXEntry
from berhoel.ctitools.ctientry import CTIEntry


def test_with_shorttitle() -> None:
    """Test correct generation of BiBTeX file entry."""
    probe = BiBTeXEntry(
        CTIEntry(
            shorttitle="shorttitle",
            title="title",
            author=("author",),
            pages=42,
            issue="issue",
            info=PaperInfo(),
            journaltitle="journaltitle",
            date="date",
            references="references",
            keywords="keywords",
        ),
    )
    result = str(probe)
    reference = """@article{42:journaltitle_issue,
  title = {title},
  shorttitle = {shorttitle},
  author = {author},
  date = {date},
  journaltitle = {journaltitle},
  pages = {42},
  issue = {issue},
  keywords = {keywords},
}
"""
    if result != reference:
        msg = f"{result=} != {reference}"
        raise AssertionError(msg)


def test_without_shorttitle() -> None:
    """Test correct generation of BiBTeX file entry."""
    probe = BiBTeXEntry(
        CTIEntry(
            shorttitle=None,
            title="title",
            author=("author",),
            pages=3,
            issue="issue",
            info=PaperInfo(),
            journaltitle="journaltitle",
            date="date",
            references="references",
            keywords="keywords",
        ),
    )
    result = str(probe)
    reference = """@article{3:journaltitle_issue,
  title = {title},
  author = {author},
  date = {date},
  journaltitle = {journaltitle},
  pages = {3},
  issue = {issue},
  keywords = {keywords},
}
"""
    if result != reference:
        msg = f"{result=} != {reference=}"
        raise AssertionError(msg)

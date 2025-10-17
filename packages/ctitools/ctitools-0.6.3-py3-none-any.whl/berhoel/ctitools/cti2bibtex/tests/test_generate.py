"""Check generation of BibTex output."""

from __future__ import annotations

import pytest

from berhoel.ctitools import PaperInfo, Papers
from berhoel.ctitools.cti2bibtex import BiBTeXEntry
from berhoel.ctitools.ctientry import CTIEntry


@pytest.fixture
def cti_entry_1() -> CTIEntry:
    """Provide test item for `CTIEntry`.

    Returna:
        Sample entry
    """
    return CTIEntry(
        shorttitle=None,
        title="Java nur mit -server-Option",
        author=("Dr. Volker Zota", "Hans T. Meier"),
        pages=154,
        issue="2007 / 10",
        info=PaperInfo(Papers.ct, 7),
        journaltitle="c't magazin für computertechnik",
        date="2007-04-30",
        references="",
        keywords="Praxis,Hotline,Java,Server,Internet,Programmierung,JAR-Archiv",
    )


@pytest.fixture
def cti_entry_2() -> CTIEntry:
    """Provide test item for `CTIEntry`.

    Returns:
        Sample entry
    """
    return CTIEntry(
        shorttitle=None,
        title="Doppelt gemoppelt",
        author=("Torsten T. Will",),
        pages=74,
        issue="2008 / 3",
        info=PaperInfo(Papers.ct, 8),
        journaltitle="c't magazin für computertechnik",
        date="2008-01-21",
        references="",
        keywords="kurz vorgestellt,Code Review,Open Source,Entwicklungssystem,"
        "Entwicklungs-Tools,Open-Source-Projekt Review Board",
    )


@pytest.fixture
def bibtex_entry_1(cti_entry_1: CTIEntry) -> BiBTeXEntry:
    """Provide test item for `BibTeXEntry`.

    Args:
        cti_entry_1: entry to convert

    Returns:
        Sample entry
    """
    return BiBTeXEntry(cti_entry_1)


@pytest.fixture
def bibtex_entry_2(cti_entry_2: CTIEntry) -> BiBTeXEntry:
    """Provide test item for `BibTeXEntry`.

    Args:
        cti_entry_2: elemnent to convert

    Returns:
        Sample entry
    """
    return BiBTeXEntry(cti_entry_2)


def test_autor_enty_1(bibtex_entry_1: BiBTeXEntry) -> None:
    """Test correct generation of BiBTeX file entry.

    Args:
        bibtex_entry_1: element to check
    """
    result = str(bibtex_entry_1)
    reference = """@article{154:c't_2007_/_10,
  title = {{J}ava nur mit -server-{O}ption},
  author = {Zota, Dr. Volker and Meier, Hans T.},
  date = {2007-04-30},
  journaltitle = {c't magazin für computertechnik},
  pages = {154},
  issue = {2007 / 10},
  keywords = {Praxis,Hotline,Java,Server,Internet,Programmierung,JAR-Archiv},
}
"""
    if result != reference:
        msg = f"{result=} != {reference=}"
        raise AssertionError(msg)


def test_autor_enty_2(bibtex_entry_2: BiBTeXEntry) -> None:
    """Test correct generation of BiBTeX file entry.

    Args:
        bibtex_entry_2: element to check
    """
    result = str(bibtex_entry_2)
    reference = """@article{74:c't_2008_/_3,
  title = {{D}oppelt gemoppelt},
  author = {Will, Torsten T.},
  date = {2008-01-21},
  journaltitle = {c't magazin für computertechnik},
  pages = {74},
  issue = {2008 / 3},
  keywords = {kurz vorgestellt,Code Review,Open Source,Entwicklungssystem,Entwicklungs-Tools,Open-Source-Projekt Review Board},
}
"""  # noqa: E501
    if result != reference:
        msg = f"{result=} != {reference=}"
        raise AssertionError(msg)

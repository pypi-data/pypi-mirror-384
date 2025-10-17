"""Export cti as BiBTeX for Zotero."""

from __future__ import annotations

from importlib import metadata
from pathlib import Path
import re
from typing import TYPE_CHECKING

import click

from berhoel.ctitools import CTI, Papers
from berhoel.ctitools.ctientry import CTIEntry

if TYPE_CHECKING:
    from berhoel.ctitools.ct import Ct
    from berhoel.ctitools.ix import Ix


class BiBTeXEntry:
    """Represent BiBTeX entry."""

    def __init__(self, entry: Ct | Ix | CTIEntry):
        """Intitalize.

        Args:
            entry: Entry das from CTI file
        """
        self.entry = entry if isinstance(entry, CTIEntry) else entry()

    @staticmethod
    def fix_title(inp: str) -> str:
        """Prepare string for BiBTeX file.

        Args:
            inp: BiBTeX entry sting to modify.

        Returns:
            BiBTeX entry string wich escaped upper characters
        """
        upper = re.compile(r"([A-Z])")
        return upper.sub(r"{\1}", inp)

    def __str__(self) -> str:
        """Return string for entry."""
        if self.entry.author is None:
            authors = ""
        else:
            authors = " and ".join(
                ", ".join(j[::-1] for j in i[::-1].split(maxsplit=1))
                for ii in self.entry.author
                if (i := (ii if ii is not None else " "))
            )
        papershort = {"c't magazin für computertechnik": "c't"}.get(
            self.entry.journaltitle,
            self.entry.journaltitle,
        )
        keywords = ",".join(
            s for i in self.entry.keywords.split(",") if (s := i.strip())
        )
        res = f"""\
@article{{{self.entry.pages}:{papershort}_{self.entry.issue.replace(" ", "_")},
  title = {{{self.fix_title(self.entry.title)}}},"""
        if self.entry.shorttitle is not None:
            res = f"""{res}
  shorttitle = {{{self.fix_title(self.entry.shorttitle)}}},"""
        return f"""{res}
  author = {{{authors}}},
  date = {{{self.entry.date}}},
  journaltitle = {{{self.entry.journaltitle}}},
  pages = {{{self.entry.pages}}},
  issue = {{{self.entry.issue}}},
  keywords = {{{keywords}}},
}}
"""


@click.command()
@click.argument("cti", type=Path, nargs=1)
@click.argument("bibtex", type=Path, nargs=1, default=None, required=False)
@click.option(
    "--limit-year",
    type=int,
    default=None,
    help="limit output to given year (default: all years in input file)",
)
@click.option(
    "--limit-issue",
    type=int,
    default=None,
    help="limit output to given issue (default: all issues in input file)",
)
@click.option(
    "--limit-journal",
    type=click.Choice(Papers, case_sensitive=False),
    default=None,
    help="limit output to given magazine ('ix' for iX, or 'ct'  for c't) "
    "(default: both magazines)",
)
@click.version_option(version=f"{metadata.version('ctitools')}")
def cti2bibtex(
    cti: Path, bibtex: Path, limit_year: int, limit_issue: int, limit_journal: str
) -> None:
    """Read a cti file and generate a BiBTeX file.

    `CTI`: input file, cti, frm, or zip file containing one of the  previous
         (required)

    `BIBTEX`: output file (name will be derived from input file, if not given)
    """
    cti_data = CTI(
        cti,
        limit_year,
        limit_issue,
        limit_journal,
    )

    out = cti.with_suffix(".bib") if bibtex is None else bibtex

    with out.open("w") as outp:
        for entry in cti_data:
            outp.write(str(BiBTeXEntry(entry)))

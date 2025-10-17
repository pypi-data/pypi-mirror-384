"""Base class for cti (c't iX) entries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import PaperInfo


@dataclass
class CTIEntry:
    """Store information from input file."""

    shorttitle: str | None
    title: str
    author: tuple[str, ...] | None
    pages: int
    issue: str
    info: PaperInfo
    journaltitle: str
    date: str
    references: str
    keywords: str

    def __hash__(self) -> int:
        """Calculate hash value for instance.

        Returns:
          hash value
        """
        return hash(
            (
                self.shorttitle,
                self.title,
                self.author,
                self.pages,
                self.issue,
                self.info,
                self.journaltitle,
                self.date,
                self.references,
                self.keywords,
            ),
        )

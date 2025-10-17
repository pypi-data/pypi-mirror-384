from __future__ import annotations

from typing import Any

from mknodes.data import commitconventions
from mknodes.templatenodes import mktemplate
from mknodes.utils import log


logger = log.get_logger(__name__)


class MkCommitConventions(mktemplate.MkTemplate):
    """Text node containing Commit message conventions."""

    ICON = "simple/conventionalcommits"
    STATUS = "new"

    def __init__(
        self,
        commit_types: (
            list[commitconventions.CommitTypeStr]
            | commitconventions.ConventionTypeStr
            | None
        ) = None,
        **kwargs: Any,
    ):
        """Constructor.

        Args:
            commit_types: Allowed commit commit_types. Can be "basic",
                          "conventional_commits", or a list of commit_types
            kwargs: Keyword arguments passed to parent
        """
        super().__init__(template="output/markdown/template", **kwargs)
        self._commit_types = commit_types

    @property
    def commit_types(self) -> list[commitconventions.CommitType]:
        val: list[commitconventions.CommitTypeStr] | commitconventions.ConventionTypeStr
        match self._commit_types:
            case None:
                val = self.ctx.metadata.commit_types or "conventional_commits"
            case _:
                val = self._commit_types
        return commitconventions.get_types(val)


if __name__ == "__main__":
    conventions = MkCommitConventions()
    print(conventions)

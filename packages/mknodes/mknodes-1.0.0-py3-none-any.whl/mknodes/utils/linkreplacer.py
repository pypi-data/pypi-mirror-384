"""Link replacer."""

from __future__ import annotations

import collections
import re
import urllib.parse

from jinjarope import htmlfilters

from mknodes.utils import log


logger = log.get_logger(__name__)


# For Regex, match groups are:
#       0: Whole markdown link e.g. [Alt-text](url)
#       1: Alt text
#       2: Full URL e.g. url + hash anchor
#       3: Filename e.g. filename.md
#       4: File extension e.g. .md, .png, etc.
#       5. hash anchor e.g. #my-sub-heading-link
AUTOLINK_RE = r"\[([^\]]+)\]\((([^)/]+\.(md|png|jpg))(#.*)*)\)"


class LinkReplacer:
    def __init__(self) -> None:
        self.mapping: collections.defaultdict[str, list[str]] = collections.defaultdict(
            list[str]
        )
        self.page_url = ""

    def __call__(self, match: re.Match[str]) -> str:
        filename = urllib.parse.unquote(match.group(3).strip())
        if filename not in self.mapping:
            return f"`{match.group(1)}`"
        filenames = self.mapping[filename]
        if len(filenames) > 1:
            text = "%s: %s has %s targets"
            logger.debug(text, self.page_url, len(filenames), match.group(3))
        new_link = htmlfilters.relative_url(self.page_url, filenames[0])
        return match.group(0).replace(match.group(2), new_link)
        # new_text = new_text.replace("\\", "/")
        # text = "LinkReplacer: : %s -> %s"
        # logger.debug(text, match.group(3), new_text)

    def replace(self, markdown: str, uri: str) -> str:
        if uri.endswith("SUMMARY.md"):
            return markdown
        self.page_url = uri
        return re.sub(AUTOLINK_RE, self, markdown)

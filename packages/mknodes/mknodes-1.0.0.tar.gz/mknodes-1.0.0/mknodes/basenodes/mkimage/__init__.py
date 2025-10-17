from __future__ import annotations

import pathlib

from typing import TYPE_CHECKING, Any, Literal

from mknodes.basenodes import mknode
from mknodes.utils import helpers, log


if TYPE_CHECKING:
    from mknodes.info import linkprovider


logger = log.get_logger(__name__)


class MkImage(mknode.MkNode):
    """Image including optional caption."""

    ICON = "material/image"
    ATTR_LIST_SEPARATOR = ""

    def __init__(
        self,
        path: str,
        *,
        target: linkprovider.LinkableType | None = None,
        caption: str = "",
        title: str = "",
        align: Literal["left", "right"] | None = None,
        width: int | None = None,
        lazy: bool = False,
        path_dark_mode: str | None = None,
        **kwargs: Any,
    ):
        """Constructor.

        Args:
            path: path of the image
            target: Optional URL or node the image should link to
            caption: Image caption
            title: Image title
            align: Image alignment
            width: Image width in pixels
            lazy: Whether to lazy-load image
            path_dark_mode: Optional alternative image for dark mode
            kwargs: Keyword arguments passed to parent
        """
        super().__init__(**kwargs)
        self.title = title
        self.caption = caption
        self.target = target
        self.align = align
        self.width = width
        self.lazy = lazy
        self._path_dark_mode = path_dark_mode
        self._path = path

    @property
    def path(self) -> str:
        if helpers.is_url(self._path):
            return self._path
        # TODO: linkreplacer doesnt work yet with full path
        return pathlib.Path(self._path).name  # this should not be needed.

    @property
    def path_dark_mode(self):
        match self._path_dark_mode:
            case str() if helpers.is_url(self._path_dark_mode):
                return self._path_dark_mode
            case str():
                return pathlib.Path(self._path_dark_mode).name
            case _:
                return None

    @property
    def url(self) -> str:
        return self.ctx.links.get_url(self.target) if self.target else ""

    def _to_markdown(self) -> str:
        if not self.path_dark_mode:
            markdown_link = self._build(self.path)
        else:
            link_2 = self._build(self.path, "light")
            link_1 = self._build(self.path_dark_mode, "dark")
            markdown_link = f"{link_1} {link_2}"
        if not self.caption:
            return markdown_link
        lines = [
            "<figure markdown>",
            f"  {markdown_link}",
            f"  <figcaption>{self.caption}</figcaption>",
            "</figure>",
        ]
        return "\n".join(lines) + "\n"

    def _build(self, path, mode: Literal["light", "dark"] | None = None) -> str:
        if mode:
            path += f"#only-{mode}"
        markdown_link = f"![{self.title}]({path})"
        if self.align:
            markdown_link += f"{{ align={self.align} }}"
        if self.width:
            markdown_link += f'{{ width="{self.width}" }}'
        if self.lazy:
            markdown_link += "{ loading=lazy }"
        if self.target:
            markdown_link = f"[{markdown_link}]({self.url})"
        return markdown_link


if __name__ == "__main__":
    img = MkImage("Some path", target="http://www.google.de", title="test")

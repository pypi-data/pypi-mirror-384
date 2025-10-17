from __future__ import annotations

import inspect
import pathlib
from typing import TYPE_CHECKING, Any

from mknodes.basenodes import mknode
from mknodes.navs import navigation, navparser, navrouter
from mknodes.pages import metadata as metadata_, mkpage, pagetemplate
from mknodes.utils import inspecthelpers, log, reprhelpers


if TYPE_CHECKING:
    from collections.abc import Sequence
    import types

    import mknodes as mk
    from mknodes.data.datatypes import PageStatusStr


logger = log.get_logger(__name__)


class MkNav(mknode.MkNode):
    """Nav section, representing a nestable menu.

    A nav is named (exception is the root nav, which has section name = None),
    has an associated virtual file (in general a SUMMARY.md),
    an optional index page and can contain other navs as well as pages and links.
    """

    ICON = "material/navigation-outline"

    def __init__(
        self,
        section: str | None = None,
        *,
        filename: str = "SUMMARY.md",
        metadata: dict | None = None,
        **kwargs: Any,
    ):
        """Constructor.

        Args:
            section: Section name for the Nav
            filename: FileName for the resulting nav
            metadata: Metadata for the nav. Child pages will inherit this.
            kwargs: Keyword arguments passed to parent
        """
        self.title = section
        self.filename = filename
        self.nav = navigation.Navigation()
        """Navigation object containing all child items."""
        self.route = navrouter.NavRouter(self)
        """Router used for decorator routing."""
        self.parse = navparser.NavParser(self)
        """Parser object used to build Navs from different data / directory structures."""
        self.metadata = metadata_.Metadata(metadata or {})
        """Page Metadata."""
        self.page_template = pagetemplate.PageTemplate(parent=self, extends="main.html")
        super().__init__(**kwargs)
        if frame := inspect.currentframe():
            self.metadata["created"] = inspecthelpers.get_stack_info(frame, level=1)

    def __repr__(self):
        title = self.title or "<root>"
        return reprhelpers.get_repr(self, section=title, filename=self.filename)

    # The child items are managed by the Navigation object. We forward relevant calls
    # to the Navigation instance.

    def __setitem__(self, index: tuple | str, node: navigation.NavSubType):
        self.nav[index] = node

    def __getitem__(self, index: tuple | str) -> navigation.NavSubType:
        return self.nav[index]

    def __delitem__(self, index: tuple | str):
        del self.nav[index]

    # def __len__(self):
    #     return len(self.children)

    def __iter__(self):
        yield from self.children

    @property
    def index_page(self) -> mk.MkPage | None:
        """Get the current index page if set."""
        return self.nav.index_page

    @index_page.setter
    def index_page(self, value: mkpage.MkPage):
        value.parent = self
        self.nav.index_page = value
        self.nav.index_page._is_index = True
        if not self.nav.index_page.title:
            self.nav.index_page.title = self.title or "Home"

    @property
    def children(self):
        return self.nav.all_items

    @children.setter
    def children(self, items):
        self.nav = navigation.Navigation(items)

    def __add__(self, other: navigation.NavSubType):
        """Use this to to register MkNodes."""
        other.parent = self
        self.nav.register(other)
        return self

    @property
    def resolved_file_path(self) -> str:
        """Returns the resulting section/subsection/../filename.xyz path."""
        path = "/".join(self.resolved_parts) + "/" + self.filename
        return path.lstrip("/")

    def add_nav(self, section: str) -> MkNav:
        """Create a Sub-Nav, register it to given Nav and return it.

        Args:
            section: Name of the new nav.
        """
        navi = MkNav(section=section, parent=self)
        self.nav.register(navi)
        return navi

    def to_markdown(self) -> str:
        return self.nav.to_literate_nav()

    def add_page(
        self,
        title: str | None = None,
        *,
        is_index: bool = False,
        is_homepage: bool = False,
        path: str | None = None,
        hide: list[str] | str | None = None,
        search_boost: float | None = None,
        exclude_from_search: bool | None = None,
        icon: str | None = None,
        status: PageStatusStr | None = None,
        subtitle: str | None = None,
        description: str | None = None,
        template: str | None = None,
        tags: list[str] | None = None,
    ) -> mk.MkPage:
        """Add a page to the Nav.

        Args:
            title: Page title
            is_index: Whether the page should become the index page.
            is_homepage: Whether the page should become the homepage.
            path: optional path override
            hide: Hide parts of the page ("toc", "nav", "path")
            search_boost: multiplier for search ranking
            exclude_from_search: Exclude page from search index
            icon: optional page icon
            status: Page status
            subtitle: Page subtitle
            description: Page description
            template: Page template
            tags: tags to show above the main headline and within the search preview
        """
        page = mkpage.MkPage(
            title=title or self.title or "Home" if is_index else title,
            is_index=is_index,
            is_homepage=is_homepage,
            path=path,
            parent=self,
            hide=hide,
            search_boost=search_boost,
            exclude_from_search=exclude_from_search,
            icon=icon,
            status=status,
            subtitle=subtitle,
            description=description,
            template=template,
            tags=tags,
        )
        if is_index:
            self.index_page = page
        else:
            self.nav.register(page)
        return page

    def add_doc(
        self,
        module: types.ModuleType | Sequence[str] | str | None = None,
        *,
        filter_by___all__: bool = False,
        recursive: bool = False,
        section_name: str | None = None,
        class_template: str | None = None,
        module_template: str | None = None,
        flatten_nav: bool = False,
    ) -> mk.MkDoc:
        """Add a module documentation to the Nav.

        Args:
            module: The module to create a documentation section for.
            filter_by___all__: Whether the documentation
            recursive: Whether to search modules recursively
            section_name: Override the name for the menu (default: module name)
            class_template: Override for the default ClassPage template
            module_template: Override for the default ModulePage template
            flatten_nav: Whether classes should be put into top-level of the nav
        """
        import mknodes as mk

        nav = mk.MkDoc(
            module=module,
            filter_by___all__=filter_by___all__,
            parent=self,
            section_name=section_name,
            recursive=recursive,
            class_template=class_template,
            module_template=module_template,
            flatten_nav=flatten_nav,
        )
        self.nav.register(nav)
        return nav


if __name__ == "__main__":
    docs = MkNav()
    nav_tree_path = pathlib.Path(__file__).parent.parent.parent / "tests/data/nav_tree/"
    nav_file = nav_tree_path / "SUMMARY.md"
    nav = MkNav()
    nav.parse.file(nav_file)
    print(nav)

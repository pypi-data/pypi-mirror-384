import mknodes as mk


nav = mk.MkNav("Development")


@nav.route.page("Dependencies", hide="toc", icon="database")
def _(page: mk.MkPage):
    page += mk.MkDependencyTable(layout="badge")
    page += mk.MkPipDepTree(direction="LR")


@nav.route.page("Development environment", icon="dev-to")
def _(page: mk.MkPage):
    page += mk.MkDevEnvSetup()


@nav.route.page("Dev Tools", icon="wrench")
def _(page: mk.MkPage):
    page += mk.MkDevTools()


@nav.route.page("Code of conduct", icon="octicons/code-of-conduct-24")
def _(page: mk.MkPage):
    page += mk.MkCodeOfConduct()


@nav.route.page("Contributing", icon="help")
def _(page: mk.MkPage):
    page += mk.MkCommitConventions()
    page += mk.MkPullRequestGuidelines()


@nav.route.page("License", hide="toc", icon="license")
def _(page: mk.MkPage):
    page += mk.MkLicense()

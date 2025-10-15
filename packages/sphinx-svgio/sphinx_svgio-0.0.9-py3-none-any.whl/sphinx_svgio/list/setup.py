from sphinx.application import Sphinx


def setup_svgio_list(app: Sphinx):

    from .directives import setup_directives
    from .nodes import setup_nodes

    setup_directives(app)
    setup_nodes(app)

from sphinx.application import Sphinx


def setup_refs(app: Sphinx):
    from .node import setup_node
    from .role import setup_role

    setup_role(app)
    setup_node(app)

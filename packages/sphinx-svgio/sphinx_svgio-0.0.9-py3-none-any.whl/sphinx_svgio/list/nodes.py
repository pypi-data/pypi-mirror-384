import string

from docutils import nodes
from sphinx.application import Sphinx


class ListItemNode(nodes.General, nodes.Element):

    def __init__(self, rawsource='', *children, **attributes):
        super().__init__(rawsource=rawsource, *children, **attributes)

        self.page_id = attributes["page_id"]

    @staticmethod
    def visit(self, node: 'ListItemNode'):

        tmpl = string.Template(
            '<div page=$page_id style="order: $page_id">\n'
        )

        mxgraph = tmpl.substitute(page_id=node.page_id)
        self.body.append(mxgraph)

    @staticmethod
    def depart(self, node: 'ListItemNode'):
        self.body.append("</div>\n")


class ListNode(nodes.General, nodes.Element):

    def __init__(self, rawsource='', *children, **attributes):
        super().__init__(rawsource=rawsource, *children, **attributes)

        self.diagram_name: str = attributes["diagram_name"]
        self.expand: bool = attributes["expand"]

    @staticmethod
    def visit(self, node: 'ListNode'):

        tmpl = string.Template(
            '<div diagram_name=$diagram_name '
            'style="display: flex; '
            'flex-direction: column;" '
            '$expand'
            '>'
        )

        text = tmpl.substitute(
                diagram_name=node.diagram_name,
                expand='expand' if node.expand else ''
                )

        self.body.append(text)

    @staticmethod
    def depart(self, node: 'ListNode'):
        self.body.append("</div>\n")


def setup_nodes(app: Sphinx):

    app.add_node(
        ListNode,
        html=(ListNode.visit, ListNode.depart),
    )
    app.add_node(
        ListItemNode,
        html=(ListItemNode.visit, ListItemNode.depart),
    )

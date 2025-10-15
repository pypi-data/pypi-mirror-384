import string

from docutils import nodes
from sphinx.application import Sphinx


class DiagramPageRefNode(nodes.General, nodes.Element):

    def __init__(self, rawsource='', *children, **attributes):
        super().__init__(rawsource=rawsource, *children, **attributes)

        self.diagram_name = attributes["name"]
        self.page_id = int(attributes["page"]) - 1
        self.ref_text = attributes["text"]

    @staticmethod
    def visit(self, node: 'DiagramPageRefNode'):

        tmpl = string.Template(
            '<a href="#$name" '
            'onclick="diagChangePage(\'$name\', $page)">'
            '$text '
        )

        subst = {
            "name": node.diagram_name,
            "page": node.page_id,
            "text": node.ref_text
        }

        text = tmpl.substitute(subst)
        self.body.append(text)

    @staticmethod
    def depart(self, node: 'DiagramPageRefNode'):
        self.body.append("</a>\n")


def setup_node(app: Sphinx):

    app.add_node(
        DiagramPageRefNode,
        html=(DiagramPageRefNode.visit, DiagramPageRefNode.depart)
    )

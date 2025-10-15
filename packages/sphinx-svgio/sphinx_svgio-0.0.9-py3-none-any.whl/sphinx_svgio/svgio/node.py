import json
import string
from html import escape
from xml.dom import minidom

from docutils import nodes
from sphinx.application import Sphinx


class Svgio(nodes.General, nodes.Element):

    def __init__(self, rawsource='', *children, **attributes):
        super().__init__(rawsource=rawsource, *children, **attributes)

        self.svg_file_path = attributes["svg_file_path"]
        self.page = attributes["page"]

    @staticmethod
    def _get_xml(node: 'Svgio'):
        svg_parsed = minidom.parse(node.svg_file_path)

        svg_tag = svg_parsed.getElementsByTagName("svg")

        return svg_tag[0].getAttribute("content")

    @staticmethod
    def visit(self, node: 'Svgio'):
        self.body.append(self.starttag(node, "div"))

        tmpl = string.Template(
            '<div class="mxgraph"'
            ' style="max-width:100%;border:1px solid transparent;"'
            ' data-mxgraph="$data">'
            "</div>"
        )

        json_data = {}
        json_data["xml"] = node._get_xml(node)
        json_data["page"] = node.page
        json_data["nav"] = True
        json_data["toolbar"] = "pages layers tags"
        json_data["highlight"] = "#0000ff"

        mxgraph = tmpl.substitute(data=escape(json.dumps(json_data)))
        self.body.append(mxgraph)

    @staticmethod
    def depart(self, node: 'Svgio'):
        self.body.append("</div>\n")


def setup_node(app: Sphinx):

    app.add_enumerable_node(
        Svgio,
        figtype="scheme",
        html=(Svgio.visit, Svgio.depart),
    )

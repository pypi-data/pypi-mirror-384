import re

from docutils import nodes
from sphinx.application import Sphinx
from sphinx.util.docutils import ReferenceRole

from .node import DiagramPageRefNode


class DiagramPageRef(ReferenceRole):

    def run(self):

        pattern = re.compile(r"(\w+):\s*(\d+)$")

        matched = pattern.match(self.target)

        if not matched:
            # self.env.docname
            return ([nodes.emphasis(text=f"Bad ref: {self.target}")], [])

        node = DiagramPageRefNode(name=matched.group(1),
                                  page=matched.group(2),
                                  text=self.title)

        return ([node], [])


def setup_role(app: Sphinx):
    app.add_role("pageref", DiagramPageRef())

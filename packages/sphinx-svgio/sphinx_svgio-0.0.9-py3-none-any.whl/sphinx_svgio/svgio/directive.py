import os

from docutils import nodes
from docutils.parsers.rst import directives
from docutils.statemachine import ViewList
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective

from .node import Svgio


class SvgioDirective(SphinxDirective):

    option_spec = {
        "name": directives.unchanged,
        "page": directives.positive_int,
        "caption": directives.unchanged,
    }

    required_arguments = 1
    optional_arguments = 0

    def _validate_file(self, rel_filename: str, filename: str):

        if not os.path.isfile(filename):
            raise self.error(f"File {rel_filename} does not exist.")

        if not rel_filename.endswith(".drawio.svg"):
            raise self.error(
                'Only ".drawio.svg" '
                "file extension is valid for this directive."
            )

    def _add_caption(self, node: Svgio):

        caption = self.options.get("caption")

        if caption is None:
            return node

        parsed = nodes.Element()
        self.state.nested_parse(
            ViewList([caption], source=""), self.content_offset, parsed
        )
        caption_node = nodes.caption(
            parsed[0].rawsource, "", *parsed[0].children
        )
        caption_node.source = parsed[0].source
        caption_node.line = parsed[0].line

        node += caption_node

        return node

    def run(self):

        rel_filename, filename = self.env.relfn2path(self.arguments[0])

        self._validate_file(rel_filename, filename)
        self.env.note_dependency(filename)

        page = self.options["page"] - 1 if "page" in self.options else 0

        node = Svgio(svg_file_path=filename, page=page)
        self.add_name(node)

        return [self._add_caption(node)]


def setup_directive(app: Sphinx):
    app.add_directive("svgio", SvgioDirective)

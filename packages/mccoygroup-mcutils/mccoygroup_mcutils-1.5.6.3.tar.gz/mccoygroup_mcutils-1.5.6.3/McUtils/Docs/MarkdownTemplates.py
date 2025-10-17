
import re, uuid, pathlib
from ..Formatters.TemplateEngine import *
from ..Jupyter.JHTML import *

class MarkdownOps:
    @classmethod
    def format_item(self, item, item_level = 0):
        return "{}- {}".format('  ' * (item_level + 1), item)
    @classmethod
    def format_link(self, alt, link):
        return '[{}]({})'.format(alt, link)
    @classmethod
    def format_obj_link(self, spec, root=None):
        return self.format_link(self.canonical_name(spec), self.canonical_link(spec, root=root))
    @classmethod
    def format_inline_code(self, arg):
        """

        :param arg:
        :type arg: str
        :return:
        :rtype:
        """
        nticks = arg.count("`")
        fence = "`"*(nticks+1)
        return fence + arg + fence
    @classmethod
    def format_code_block(self, arg):
        """

        :param arg:
        :type arg: str
        :return:
        :rtype:
        """
        nticks = arg.count("`")
        fence = "`"*(nticks+3)
        return fence + "python\n" + arg + "\n" + fence
    @classmethod
    def format_quote_block(self, arg):
        """

        :param arg:
        :type arg: str
        :return:
        :rtype:
        """

        return ">" + arg.replace("\n", "\n>")

    link_bar_template='<div class="container{boxed}">\n{links}\n</div>'
    link_row_template='  <div class="row">\n{cols}\n</div>'
    link_item_template='   <div class="col" markdown="1">\n{item}   \n</div>'
    @classmethod
    def format_grid(self, link_grid, boxed=False):
        return self.link_bar_template.format(links="\n".join(
            self.link_row_template.format(
                cols="\n".join(self.link_item_template.format(item=item) for item in row)
            )
            for row in link_grid if len(row) > 0
        ),
        boxed=' alert alert-secondary bg-light' if boxed else ""
        )
    @classmethod
    def split(self, links, ncols=3, pad=""):
        num_cols = ncols
        splits = []
        sub = []
        for x in links:
            sub.append(x)
            if len(sub) == num_cols:
                splits.append(sub)
                sub = []
        splits.append(sub + [pad] * (ncols - len(sub)))
        return splits

    collapse_template="""
<div class="collapsible-section">
 <div class="collapsible-section collapsible-section-header" markdown="1">
{header_fmt} <a class="collapse-link" data-toggle="collapse" href="#{name}" markdown="1">{header}</a> {opener}
 </div>
 <div class="collapsible-section collapsible-section-body collapse {show}" id="{name}" markdown="1">
 {content}
 </div>
</div>
"""
    collapse_opener = '<a class="float-right" data-toggle="collapse" href="#{name}"><i class="fa fa-chevron-down"></i></a>'
    @classmethod
    def format_collapse_section(self, header, content, name=None, open=True, include_opener=True):
        header_fmt = ""
        while header.startswith("#"):
            header_fmt += "#"
            header = header[1:]
        if name is None:
            name = re.sub("\W", "", header) + "-" + str(uuid.uuid4())[:6]
        return self.collapse_template.format(
            header_fmt=header_fmt,
            header=header,
            content=content,
            name=name,
            show="show" if open else "",
            opener=self.collapse_opener.format(name=name) if include_opener else ""
        )

    @classmethod
    def format_obj_link_grid(self, mems, ncols=3, root=None, boxed=True):
        links = self.split(
            [self.format_obj_link(l, root=root) for l in (mems.values() if hasattr(mems, 'values') else mems)],
            ncols=ncols
        )
        return self.format_grid(links, boxed=boxed)

    @classmethod
    def canonical_name(self, identifier, formatter=None):
        return identifier.split(".")[-1]

    @classmethod
    def canonical_link(self, identifier, root=None, formatter=None):
        ups = 0
        # if root is not None and identifier.startswith(root):
        #     identifier = identifier[len(root):]
        #     if identifier.startswith('.'):
        #         identifier = identifier[1:]
        while identifier[0] == ".":
            ups += 1
            identifier = identifier[1:]
        if ups > 0:
            pad = "../"*ups
        else:
            pad = ""
        identifier = "/".join(identifier.split("."))
        return pad + identifier + ".md"

    @classmethod
    def html(kls, tag, content, markdown=True, formatter=None, **styles):
        if markdown:
            styles["markdown"] = "1"
        return getattr(HTML, tag)("\n{content}\n", **styles).tostring().format(content=content)
    @classmethod
    def bootstrap(kls, tag, content, markdown=True, formatter=None, **styles):
        if markdown:
            styles["markdown"] = "1"
        return getattr(Bootstrap, tag)("\n{content}\n", **styles).tostring().format(content=content)
    @classmethod
    def alert(kls, content, variant='warning', markdown=True, formatter=None, **styles):
        return kls.bootstrap('Alert', content, variant=variant, markdown=markdown, **styles)

class MarkdownFormatDirective(FormatDirective):
    Link = "link", TemplateOps.wrap(MarkdownOps.format_link)
    ObjLink = "objlink", TemplateOps.wrap(MarkdownOps.format_obj_link)
    Item = "item", TemplateOps.wrap(MarkdownOps.format_item)
    Code = "code", TemplateOps.wrap(MarkdownOps.format_code_block)
    Quote = "quote", TemplateOps.wrap(MarkdownOps.format_quote_block)
    # Card = "card", TemplateOps.wrap(MarkdownFormatter.format_card)
    # Alert = "alert", TemplateOps.wrap(MarkdownFormatter.format_alert)
    Collapse = "collapse", TemplateOps.wrap(MarkdownOps.format_collapse_section)
    Grid = "grid", TemplateOps.wrap(MarkdownOps.format_grid)
    Split = "split", TemplateOps.wrap(MarkdownOps.split)
    ObjLinkGrid = "objlink_grid", TemplateOps.wrap(MarkdownOps.format_obj_link_grid)
    CanonicalName = "canonical_name", MarkdownOps.canonical_name
    CanonicalLink = "canonical_link", MarkdownOps.canonical_link
    HTML = "html", MarkdownOps.html
    Bootstrap = "bootstrap", MarkdownOps.bootstrap
    Alert = "alert", MarkdownOps.alert
MarkdownFormatDirective = TemplateFormatDirective.extend(MarkdownFormatDirective)

class MarkdownTemplateFormatter(TemplateFormatter):
    directives = MarkdownFormatDirective

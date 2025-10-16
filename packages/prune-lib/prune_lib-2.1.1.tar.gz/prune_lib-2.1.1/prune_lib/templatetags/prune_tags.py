import re

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()

###################
# SETTINGS        #
###################


@register.filter(name="settings_value")
def settings_value(value):
    """feature
    :name: settings_value
    :description: Permet de récupérer la valeur d'une variable du fichier settings.
    :return: Valeur de la variable si elle existe, sinon chaîne vide.
    """
    return getattr(settings, value, "")


###################
# MARKDOWN        #
###################


@register.tag(name="markdown")
def do_markdown(parser, token):
    """feature
    :name: do_markdown
    :description: Transforme un bloc de texte Markdown en HTML sécurisé.
    :param parser:
    :return: Instance de MarkdownNode contenant le contenu transformé.
    """

    nodelist = parser.parse(("endmarkdown",))
    parser.delete_first_token()
    return MarkdownNode(nodelist)


class MarkdownNode(template.Node):
    """feature
    :name: MarkdownNode
    :description: Classe interne gérant la conversion de Markdown en HTML.
    :param nodelist:
    :return: HTML sûr prêt à être inséré dans le template.
    """

    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        output = self.nodelist.render(context).strip()
        lines = output.split("\n")
        html_lines = []
        link_pattern = re.compile(r"\[([^\]]+)\]\((http[s]?://[^\)]+)\)")
        italic_pattern = re.compile(r"_([^_]+)_")
        bold_pattern = re.compile(r"\*\*([^\*]+)\*\*")
        for line in lines:
            line = line.strip()
            if not (line.startswith("<")):
                if line.startswith("### "):
                    line = f"<h3>{line[4:].strip()}</h3>"
                elif line.startswith("## "):
                    line = f"<h2>{line[3:].strip()}</h2>"
                elif line.startswith("# "):
                    line = f"<h1>{line[2:].strip()}</h1>"
                elif line.startswith("- "):
                    line = f"<li>{line[2:].strip()}</li>"
                elif line.startswith("> ") or line.startswith("&gt; "):
                    ind = 2 if line.startswith("> ") else 5
                    line = f"<blockquote>{line[ind:].strip()}</blockquote>"
                elif line == "* * *":
                    line = "<hr/>"
                else:
                    line = f"<p>{line}</p>"
                line = link_pattern.sub(r'<a href="\2">\1</a>', line)
                line = italic_pattern.sub(r"<i>\1</i>", line)
                line = bold_pattern.sub(r"<strong>\1</strong>", line)
            html_lines.append(line)
        content = "".join(html_lines)
        container = f'<div class="markdown-container">{content}</div>'
        style = """
        .markdown-container {
            max-width: 800px;
        }

        .markdown-container p, .markdown-container li {
            margin-top: 12px;
            margin-bottom: 12px;
        }

        .markdown-container a {
            text-decoration: underline;
        }

        .markdown-container hr {
            border-color: black;
        }
        """
        container = f"<style>{style}</style>\n{container}"
        return mark_safe(container)

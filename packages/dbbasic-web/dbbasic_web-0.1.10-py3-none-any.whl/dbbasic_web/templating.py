"""Template rendering with Jinja2"""
from jinja2 import Environment, FileSystemLoader, select_autoescape
from .settings import TEMPLATES_DIR

env = Environment(
    loader=FileSystemLoader([str(TEMPLATES_DIR)]),
    autoescape=select_autoescape(["html", "xml"]),
)


def render(template_name: str, **ctx) -> str:
    """Render a template with context"""
    tmpl = env.get_template(template_name)
    return tmpl.render(**ctx)

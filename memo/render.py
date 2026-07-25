from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from analysis.schema import Analysis

_TEMPLATE_DIR = Path(__file__).parent
_env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)))


def render_memo(candidate: dict, analysis: Analysis) -> str:
    template = _env.get_template("template.md")
    return template.render(candidate=candidate, analysis=analysis)

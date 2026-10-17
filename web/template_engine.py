"""Jinja2 template engine configured for the project."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape


class TemplateEngine:
    """Wraps a Jinja2 Environment with project defaults."""

    def __init__(self, templates_dir: Path) -> None:
        self._env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=select_autoescape(
                enabled_extensions=("html", "htm", "xml"),
                default_for_string=True,
                default=True,
            ),
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        # Globals available in every template
        self._env.globals.update(
            app_name="eventstream",
        )

    @property
    def env(self) -> Environment:
        return self._env

    def render(self, template_name: str, **context) -> str:
        return self._env.get_template(template_name).render(**context)
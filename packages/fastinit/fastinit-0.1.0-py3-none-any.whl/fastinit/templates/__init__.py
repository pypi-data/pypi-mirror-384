"""Template rendering utilities."""

from typing import Dict, Any
from jinja2 import Environment, PackageLoader, select_autoescape


class TemplateRenderer:
    """Renders Jinja2 templates for project and component generation."""

    def __init__(self):
        """Initialize the template renderer."""
        self.env = Environment(
            loader=PackageLoader("fastinit", "templates"),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Add custom filters
        self.env.filters["snake_case"] = self._snake_case
        self.env.filters["pascal_case"] = self._pascal_case
        self.env.filters["kebab_case"] = self._kebab_case

    def render(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render a template with the given context."""
        template = self.env.get_template(template_name)
        return template.render(**context)

    @staticmethod
    def _snake_case(text: str) -> str:
        """Convert text to snake_case."""
        import re

        text = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", text)
        text = re.sub("([a-z0-9])([A-Z])", r"\1_\2", text)
        return text.lower()

    @staticmethod
    def _pascal_case(text: str) -> str:
        """Convert text to PascalCase."""
        return "".join(
            word.capitalize()
            for word in text.replace("_", " ").replace("-", " ").split()
        )

    @staticmethod
    def _kebab_case(text: str) -> str:
        """Convert text to kebab-case."""
        import re

        text = re.sub("(.)([A-Z][a-z]+)", r"\1-\2", text)
        text = re.sub("([a-z0-9])([A-Z])", r"\1-\2", text)
        return text.lower().replace("_", "-")

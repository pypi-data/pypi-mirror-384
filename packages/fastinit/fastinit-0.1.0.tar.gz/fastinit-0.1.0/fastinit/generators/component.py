"""Component generator - creates individual components (models, services, routes)."""

from pathlib import Path
from typing import Dict, Optional

from fastinit.templates import TemplateRenderer


class ComponentGenerator:
    """Generates individual components for a FastAPI project."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.app_dir = project_dir / "app"
        self.renderer = TemplateRenderer()

        # Verify we're in a FastAPI project
        if not (self.app_dir / "main.py").exists():
            raise ValueError(
                "Not a valid FastAPI project directory (app/main.py not found)"
            )

    def generate_model(self, name: str, fields: Optional[Dict[str, str]] = None):
        """Generate a SQLAlchemy model."""
        model_file = self.app_dir / "models" / f"{name.lower()}.py"

        # Check if file already exists
        if model_file.exists():
            raise FileExistsError(
                f"Model file already exists: {model_file}\n"
                f"Please delete the file or use a different name."
            )

        context = {
            "model_name": name,
            "table_name": name.lower() + "s",
            "fields": fields or {},
        }

        content = self.renderer.render("components/model.py.jinja", context)
        model_file.write_text(content, encoding="utf-8")

    def generate_schema(self, name: str, fields: Optional[Dict[str, str]] = None):
        """Generate Pydantic schemas."""
        schema_file = self.app_dir / "schemas" / f"{name.lower()}.py"

        # Check if file already exists
        if schema_file.exists():
            raise FileExistsError(
                f"Schema file already exists: {schema_file}\n"
                f"Please delete the file or use a different name."
            )

        # Ensure schemas directory exists
        schema_dir = self.app_dir / "schemas"
        if not schema_dir.exists():
            schema_dir.mkdir(parents=True, exist_ok=True)
            # Create __init__.py if it doesn't exist
            init_file = schema_dir / "__init__.py"
            if not init_file.exists():
                init_file.write_text('"""Pydantic schemas."""\n', encoding="utf-8")

        context = {
            "model_name": name,
            "fields": fields or {},
        }

        content = self.renderer.render("components/schema.py.jinja", context)
        schema_file.write_text(content, encoding="utf-8")

    def generate_service(
        self,
        name: str,
        model_name: Optional[str] = None,
        pagination_type: str = "limit-offset",
    ):
        """Generate a service class."""
        # Remove 'Service' suffix if present for file naming
        service_base_name = name.replace("Service", "").lower()
        service_file = self.app_dir / "services" / f"{service_base_name}_service.py"

        # Check if file already exists
        if service_file.exists():
            raise FileExistsError(
                f"Service file already exists: {service_file}\n"
                f"Please delete the file or use a different name."
            )

        context = {
            "service_name": name if name.endswith("Service") else f"{name}Service",
            "model_name": model_name or name.replace("Service", ""),
            "pagination_type": pagination_type,
        }

        content = self.renderer.render("components/service.py.jinja", context)
        service_file.write_text(content, encoding="utf-8")

    def generate_route(
        self,
        name: str,
        service_name: Optional[str] = None,
        pagination_type: str = "limit-offset",
    ):
        """Generate an API route."""
        # Ensure plural form for route name
        route_name = name if name.endswith("s") else f"{name}s"
        route_file = self.app_dir / "api" / "routes" / f"{route_name.lower()}.py"

        # Check if file already exists
        if route_file.exists():
            raise FileExistsError(
                f"Route file already exists: {route_file}\n"
                f"Please delete the file or use a different name."
            )

        # Derive model name from route name (singular)
        model_name = route_name.rstrip("s").capitalize()

        context = {
            "route_name": route_name,
            "model_name": model_name,
            "service_name": service_name or f"{model_name}Service",
            "pagination_type": pagination_type,
        }

        content = self.renderer.render("components/route.py.jinja", context)
        route_file.write_text(content, encoding="utf-8")

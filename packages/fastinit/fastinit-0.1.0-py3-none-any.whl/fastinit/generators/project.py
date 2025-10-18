"""Project generator - creates the complete FastAPI project structure."""

from typing import Dict, Any
import shutil

from fastinit.models.config import ProjectConfig
from fastinit.templates import TemplateRenderer


class ProjectGenerator:
    """Generates a complete FastAPI project structure."""

    def __init__(self, config: ProjectConfig):
        self.config = config
        self.renderer = TemplateRenderer()

    def generate(self):
        """Generate the complete project structure."""
        # Create project directory
        self._create_directory_structure()

        # Generate files
        self._generate_main_files()
        self._generate_config_files()
        self._generate_api_files()
        self._generate_core_files()

        if self.config.use_db:
            self._generate_db_files()
            self._generate_models_files()
            self._generate_alembic_files()

        if self.config.use_jwt:
            self._generate_security_files()

        if self.config.use_docker:
            self._generate_docker_files()

        self._generate_requirements()
        self._generate_env_file()
        self._generate_gitignore()
        self._generate_readme()

    def _create_directory_structure(self):
        """Create the project directory structure."""
        project_path = self.config.project_path

        # Clean up if force mode
        if project_path.exists():
            shutil.rmtree(project_path)

        # Create directories
        directories = [
            project_path,
            project_path / "app",
            project_path / "app" / "api",
            project_path / "app" / "api" / "routes",
            project_path / "app" / "core",
            project_path / "app" / "models",
            project_path / "app" / "services",
            project_path / "app" / "schemas",
            project_path / "tests",
        ]

        if self.config.use_db:
            directories.append(project_path / "app" / "db")
            directories.append(project_path / "alembic")
            directories.append(project_path / "alembic" / "versions")

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

            # Create __init__.py files
            if directory.name in [
                "app",
                "api",
                "routes",
                "core",
                "models",
                "services",
                "schemas",
                "db",
                "tests",
            ]:
                (directory / "__init__.py").touch()

    def _generate_main_files(self):
        """Generate main application files."""
        context = self._get_template_context()

        # Generate main.py
        main_content = self.renderer.render("main.py.jinja", context)
        self._write_file("app/main.py", main_content)

    def _generate_config_files(self):
        """Generate configuration files."""
        context = self._get_template_context()

        # Generate config.py
        config_content = self.renderer.render("core/config.py.jinja", context)
        self._write_file("app/core/config.py", config_content)

    def _generate_api_files(self):
        """Generate API-related files."""
        context = self._get_template_context()

        # Generate deps.py
        deps_content = self.renderer.render("api/deps.py.jinja", context)
        self._write_file("app/api/deps.py", deps_content)

        # Generate health route
        health_content = self.renderer.render("api/routes/health.py.jinja", context)
        self._write_file("app/api/routes/health.py", health_content)

    def _generate_core_files(self):
        """Generate core module files."""
        context = self._get_template_context()

        # Generate core __init__.py
        init_content = self.renderer.render("core/__init__.py.jinja", context)
        self._write_file("app/core/__init__.py", init_content)

    def _generate_db_files(self):
        """Generate database-related files."""
        context = self._get_template_context()

        # Generate session.py
        session_content = self.renderer.render("db/session.py.jinja", context)
        self._write_file("app/db/session.py", session_content)

        # Generate base.py
        base_content = self.renderer.render("db/base.py.jinja", context)
        self._write_file("app/db/base.py", base_content)

    def _generate_models_files(self):
        """Generate models directory files."""
        context = self._get_template_context()

        # Generate models __init__.py
        init_content = self.renderer.render("models/__init__.py.jinja", context)
        self._write_file("app/models/__init__.py", init_content)

    def _generate_alembic_files(self):
        """Generate Alembic migration configuration files."""
        context = self._get_template_context()

        # Generate alembic.ini
        alembic_ini_content = self.renderer.render("alembic.ini.jinja", context)
        self._write_file("alembic.ini", alembic_ini_content)

        # Generate alembic/env.py
        env_content = self.renderer.render("alembic/env.py.jinja", context)
        self._write_file("alembic/env.py", env_content)

        # Generate alembic/script.py.mako
        script_mako_content = self.renderer.render(
            "alembic/script.py.mako.jinja", context
        )
        self._write_file("alembic/script.py.mako", script_mako_content)

        # Generate alembic/README.md
        alembic_readme_content = self.renderer.render("alembic/README.jinja", context)
        self._write_file("alembic/README.md", alembic_readme_content)

        # Create .gitkeep in versions directory to ensure it's tracked
        self._write_file("alembic/versions/.gitkeep", "")

    def _generate_security_files(self):
        """Generate security-related files for JWT."""
        context = self._get_template_context()

        # Generate security.py
        security_content = self.renderer.render("core/security.py.jinja", context)
        self._write_file("app/core/security.py", security_content)

    def _generate_docker_files(self):
        """Generate Docker configuration files."""
        context = self._get_template_context()

        # Generate Dockerfile
        dockerfile_content = self.renderer.render("Dockerfile.jinja", context)
        self._write_file("Dockerfile", dockerfile_content)

        # Generate docker-compose.yml
        compose_content = self.renderer.render("docker-compose.yml.jinja", context)
        self._write_file("docker-compose.yml", compose_content)

        # Generate .dockerignore
        dockerignore_content = self.renderer.render("dockerignore.jinja", context)
        self._write_file(".dockerignore", dockerignore_content)

    def _generate_requirements(self):
        """Generate requirements.txt file."""
        context = self._get_template_context()

        requirements_content = self.renderer.render("requirements.txt.jinja", context)
        self._write_file("requirements.txt", requirements_content)

    def _generate_env_file(self):
        """Generate .env.example file."""
        context = self._get_template_context()

        env_content = self.renderer.render("env.example.jinja", context)
        self._write_file(".env.example", env_content)

    def _generate_gitignore(self):
        """Generate .gitignore file."""
        gitignore_content = self.renderer.render("gitignore.jinja", {})
        self._write_file(".gitignore", gitignore_content)

    def _generate_readme(self):
        """Generate README.md file."""
        context = self._get_template_context()

        readme_content = self.renderer.render("README.md.jinja", context)
        self._write_file("README.md", readme_content)

    def _get_template_context(self) -> Dict[str, Any]:
        """Get the template context for rendering."""
        return {
            "project_name": self.config.project_name,
            "use_db": self.config.use_db,
            "db_type": self.config.db_type,
            "use_jwt": self.config.use_jwt,
            "use_logging": self.config.use_logging,
            "use_docker": self.config.use_docker,
            "python_version": self.config.python_version,
        }

    def _write_file(self, relative_path: str, content: str):
        """Write content to a file in the project."""
        file_path = self.config.project_path / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

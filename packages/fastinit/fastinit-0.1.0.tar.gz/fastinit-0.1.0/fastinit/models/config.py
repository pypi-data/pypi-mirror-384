"""Data models for project configuration."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ProjectConfig:
    """Configuration for generating a FastAPI project."""

    project_name: str
    output_dir: Path
    use_db: bool = False
    db_type: Optional[str] = None  # postgresql, mysql, sqlite
    use_jwt: bool = False
    use_logging: bool = False
    use_docker: bool = False
    python_version: str = "3.11"

    @property
    def project_path(self) -> Path:
        """Get the full project path."""
        return self.output_dir / self.project_name

    @property
    def app_path(self) -> Path:
        """Get the app directory path."""
        return self.project_path / "app"


__all__ = ["ProjectConfig"]

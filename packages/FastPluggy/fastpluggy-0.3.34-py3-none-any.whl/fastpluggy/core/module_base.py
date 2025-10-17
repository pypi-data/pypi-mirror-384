from pathlib import Path
from typing import Any, Annotated, Optional, List, Dict
from typing import Callable

from fastapi import APIRouter
from loguru import logger
from packaging.requirements import Requirement
from pydantic import BaseModel, Field, computed_field

from fastpluggy.core.tools.inspect_tools import InjectDependency

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

ModuleRouterType = Any | APIRouter | Callable[[], APIRouter] | List[Any]


class FastPluggyBaseModule(BaseModel):
    """
    Base class for FastPluggy plugins.

    Plugins must inherit from this class and implement lifecycle hooks like `on_load_complete()` 
    and `after_setup_templates()` as needed.

    They can optionally define metadata fields and attributes for integration (e.g., router, settings).
    """

    # --- Identity / version ---
    module_name: Optional[str] = ""
    module_version: Optional[str] = "0.0.0"
    module_settings: Optional[Any] = None
    depends_on: Optional[Dict[str, str]] = Field(default_factory=dict)

    # --- Menu Metadata ---
    module_menu_name: str = ""
    module_menu_icon: str = "fas fa-cube"
    module_menu_type: Optional[str] = "main"

    # --- JS & CSS ---
    extra_js_files: List[str] = Field(default_factory=list)
    extra_css_files: List[str] = Field(default_factory=list)

    # --- Optional Router ---
    module_router: ModuleRouterType = None
    module_mount_url: Optional[str] = None

    # --- Path ---
    module_path: Optional[Path] = None

    class Config:
        arbitrary_types_allowed = True

    # --- Computed Properties ---
    @computed_field
    @property
    def display_name(self) -> Optional[str]:
        return self.module_menu_name or self.module_name

    @computed_field
    @property
    def templates_dir(self) -> Optional[Path]:
        if self.module_path:
            path = self.module_path / "templates"
            return path if path.exists() else None
        return None

    @computed_field
    @property
    def requirements_path(self) -> Optional[Path]:
        return self.module_path / "requirements.txt" if self.module_path else None

    @computed_field
    @property
    def requirements_exists(self) -> bool:
        req = self.requirements_path
        return req.exists() if req else False

    @computed_field
    @property
    def pyproject_path(self) -> Optional[Path]:
        return self.module_path / "pyproject.toml" if self.module_path else None

    @computed_field
    @property
    def pyproject_exists(self) -> bool:
        pyproject = self.pyproject_path
        return pyproject.exists() if pyproject else False

    @computed_field
    @property
    def has_dependencies(self) -> bool:
        """Check if the module has any dependencies (requirements.txt or pyproject.toml)"""
        return self.requirements_exists or self.pyproject_exists

    # --- Lifecycle Hooks ---
    def on_load_complete(self, fast_pluggy: Annotated["FastPluggy", InjectDependency]) -> None:
        """
        This method will be called when all plugins are loaded.

        Use this hook to initialize your plugin, set up database connections,
        register event handlers, or perform any other initialization that depends
        on other plugins being loaded.

        Args:
            fast_pluggy: The FastPluggy instance, automatically injected
        """
        pass

    def after_setup_templates(self, fast_pluggy: Annotated["FastPluggy", InjectDependency]) -> None:
        """
        This method will be called when the Jinja2 environment is set up.

        Use this hook to add custom template filters, globals, or extensions
        to the Jinja2 environment. This is useful for adding custom rendering
        functionality that can be used in your templates.
        You should also create the parent_item of menu here.

        Args:
            fast_pluggy: The FastPluggy instance, automatically injected
        """
        pass

    # --- Static Dependency Management Methods ---
    def get_requirements_list(self) -> list[str]:
        """
        Get a list of dependencies from requirements.txt file.
        Returns a list of dependency strings.
        """
        if not self.requirements_exists:
            return []

        dependencies = []
        with open(self.requirements_path) as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]

        for line in lines:
            try:
                req = Requirement(line)
                dependencies.append(str(req))
            except Exception as e:
                logger.warning(f"Error parsing requirement line '{line}': {e}")
                dependencies.append(line)  # Add original line if parsing fails

        return dependencies

    def get_pyproject_dependencies_list(self) -> list[str]:
        """
        Get a list of dependencies from pyproject.toml file.
        Returns a list of dependency strings.
        """
        if not self.pyproject_exists:
            return []

        if tomllib is None:
            logger.warning("tomllib/tomli not available, cannot parse pyproject.toml files")
            return []

        dependencies = []
        try:
            with open(self.pyproject_path, 'rb') as f:
                data = tomllib.load(f)

            # Get dependencies from project.dependencies
            project_deps = data.get('project', {}).get('dependencies', [])
            dependencies.extend(project_deps)

        except Exception as e:
            logger.error(f"Error reading pyproject.toml file '{self.pyproject_file}': {e}")

        return dependencies

    def get_dependency(self) -> dict[str, List[str]]:
        """
        Returns a dictionary of all dependency files for enabled and loaded plugins.
        Format: {'requirements.txt': [file_paths], 'pyproject.toml': [file_paths]}
        """

        requirements_files = []
        pyproject_files = []

        if self.requirements_exists:
                requirements_files = self.get_requirements_list()

        if self.pyproject_exists:
                pyproject_files = self.get_pyproject_dependencies_list()

        return {
            'requirements.txt': requirements_files,
            'pyproject.toml': pyproject_files
        }

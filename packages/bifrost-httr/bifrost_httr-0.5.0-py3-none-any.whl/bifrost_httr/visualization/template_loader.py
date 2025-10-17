# Bifrost-HTTr- transcriptomics based dose response analysis
# Copyright (C) 2025 as Unilever Global IP Limited
# Bifrost-HTTr is free software: you can redistribute it and/or modify it under the terms
# of the GNU Lesser General Public License as published by the Free Software Foundation,
# either version 3 of the License. Bifrost-HTTr is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.
# You should have received a copy of the GNU Lesser General Public License along with Bifrost-HTTr.
# If not, see https://www.gnu.org/licenses/ . It is the responsibility of Bifrost-HTTr users to
# familiarise themselves with all dependencies and their associated licenses.

"""Template loader for BIFROST MultiQC report templates.

This module provides functionality to load HTML templates from YAML files,
with support for custom template overrides and fallback to default templates.
"""

import importlib.resources
from pathlib import Path

import yaml

from bifrost_httr.utils.logging import get_logger

# Configure logging
logger = get_logger(__name__)


class TemplateLoader:
    """Loads and manages HTML templates for BIFROST MultiQC reports.

    This class handles loading templates from YAML files, with support for:
    - Default templates shipped with the package
    - Custom user-provided template files
    - Fallback to defaults when custom templates are incomplete
    - Template validation and error handling
    """

    def __init__(self, custom_template_file: Path | str | None = None) -> None:
        """Initialize the template loader.

        Args:
            custom_template_file: Optional path to custom template YAML file.
                                If provided, templates from this file will override defaults.
        """
        self._templates: dict[str, str] = {}
        self._custom_template_file = (
            Path(custom_template_file) if custom_template_file else None
        )
        self._load_templates()

    def _load_default_templates(self) -> dict[str, str]:
        """Load default templates from the package data directory.

        Returns:
            Dictionary mapping template names to template strings.

        Raises:
            FileNotFoundError: If default template file cannot be found.
            ModuleNotFoundError: If the package data module cannot be found.
            yaml.YAMLError: If YAML parsing fails.
            PermissionError: If access to the template file is denied.
            OSError: If other I/O errors occur during file access.
        """
        try:
            # Load from package data directory
            with importlib.resources.open_text(
                "bifrost_httr.data",
                "report_templates.yml",
            ) as f:
                data = yaml.safe_load(f)
                return data.get("templates", {})
        except (
            FileNotFoundError,
            ModuleNotFoundError,
            yaml.YAMLError,
            PermissionError,
            OSError,
        ):
            logger.exception("Failed to load default templates")
            raise

    def _load_custom_templates(self, custom_file: Path) -> dict[str, str]:
        """Load custom templates from user-provided YAML file.

        Args:
            custom_file: Path to custom template YAML file.

        Returns:
            Dictionary mapping template names to template strings.

        Raises:
            FileNotFoundError: If custom template file cannot be found.
            yaml.YAMLError: If YAML parsing fails.
            PermissionError: If access to the template file is denied.
            OSError: If other I/O errors occur during file access.
        """
        if not custom_file.exists():
            msg = f"Custom template file not found: {custom_file}"
            raise FileNotFoundError(msg)

        try:
            with custom_file.open(encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data.get("templates", {})
        except (yaml.YAMLError, PermissionError, OSError):
            logger.exception("Failed to load custom template file %s", custom_file)
            raise

    def _load_templates(self) -> None:
        """Load templates from default and custom sources.

        Templates are loaded in the following order:
        1. Default templates from package
        2. Custom templates (if provided) - these override defaults

        This ensures that custom templates can partially override defaults
        while maintaining fallback behavior for missing templates.
        """
        # Load default templates
        self._templates = self._load_default_templates()
        logger.info("Loaded %d default templates", len(self._templates))

        # Load and merge custom templates if provided
        if self._custom_template_file:
            custom_templates = self._load_custom_templates(
                self._custom_template_file,
            )

            # Count overrides
            overrides = set(custom_templates.keys()) & set(self._templates.keys())
            new_templates = set(custom_templates.keys()) - set(
                self._templates.keys(),
            )

            # Merge custom templates (they override defaults)
            self._templates.update(custom_templates)

            logger.info(
                "Loaded custom templates from %s: %d overrides, %d new templates",
                self._custom_template_file,
                len(overrides),
                len(new_templates),
            )

            if overrides:
                logger.debug(
                    "Overridden templates: %s",
                    ", ".join(sorted(overrides)),
                )
            if new_templates:
                logger.debug("New templates: %s", ", ".join(sorted(new_templates)))

    def get_template(self, template_name: str) -> str:
        """Get a template by name.

        Args:
            template_name: Name of the template to retrieve.

        Returns:
            Template string ready for formatting.

        Raises:
            KeyError: If template is not found in either default or custom templates.
        """
        if template_name not in self._templates:
            available = ", ".join(sorted(self._templates.keys()))
            msg = f"Template '{template_name}' not found. Available templates: {available}"
            raise KeyError(msg)

        return self._templates[template_name]

    def get_all_templates(self) -> dict[str, str]:
        """Get all loaded templates.

        Returns:
            Dictionary mapping template names to template strings.
        """
        return self._templates.copy()

    def list_templates(self) -> list[str]:
        """List all available template names.

        Returns:
            Sorted list of template names.
        """
        return sorted(self._templates.keys())

    @property
    def custom_template_file(self) -> Path | None:
        """Get the path to the custom template file, if any.

        Returns:
            Path to custom template file, or None if using defaults only.
        """
        return self._custom_template_file


# Global template loader instance - will be initialized when first accessed
_template_loader: TemplateLoader | None = None


def get_template_loader(
    custom_template_file: Path | str | None = None,
) -> TemplateLoader:
    """Get the global template loader instance.

    Args:
        custom_template_file: Optional path to custom template file.
                            Only used if loader hasn't been initialized yet.

    Returns:
        TemplateLoader instance.
    """
    global _template_loader

    if _template_loader is None:
        _template_loader = TemplateLoader(custom_template_file)
    elif custom_template_file and _template_loader.custom_template_file != Path(
        custom_template_file,
    ):
        # Reinitialize if custom template file changes
        logger.info(
            "Reinitializing template loader with new custom file: %s",
            custom_template_file,
        )
        _template_loader = TemplateLoader(custom_template_file)

    return _template_loader


def get_template(template_name: str) -> str:
    """Convenience function to get a template using the global loader.

    Args:
        template_name: Name of the template to retrieve.

    Returns:
        Template string ready for formatting.
    """
    return get_template_loader().get_template(template_name)

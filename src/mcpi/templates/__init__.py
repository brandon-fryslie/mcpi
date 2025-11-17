"""Configuration templates for MCP servers with interactive prompts."""

from .models import PromptDefinition, ServerTemplate
from .template_manager import (
    TemplateManager,
    create_default_template_manager,
    create_test_template_manager,
)

__all__ = [
    "PromptDefinition",
    "ServerTemplate",
    "TemplateManager",
    "create_default_template_manager",
    "create_test_template_manager",
]

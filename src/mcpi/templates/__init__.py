"""Configuration templates for MCP servers with interactive prompts."""

from .models import PromptDefinition, ServerTemplate
from .prompt_handler import collect_template_values, prompt_for_value
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
    "prompt_for_value",
    "collect_template_values",
]

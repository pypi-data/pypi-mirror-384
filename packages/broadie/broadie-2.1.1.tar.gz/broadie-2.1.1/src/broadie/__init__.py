"""Broadie: Production-grade AI Agent Framework

A robust, scalable framework for building and deploying AI agents
in production environments with enterprise-grade reliability.
"""

import logging
import warnings

from pydantic import BaseModel, Field

from . import server, tools
from .agents import Agent, SubAgent
from .config import settings
from .decorators import tool
from .factory import create_agent, create_sub_agent
from .schemas import AgentSchema, ChannelSchema, ModelSchema, SubAgentSchema
from .tools import ToolResponse, ToolStatus
from .utils import slugify

# Suppress other common warnings from dependencies
warnings.filterwarnings(
    "ignore",
    message="This feature is deprecated as of June 24, 2025",
    module="vertexai._model_garden._model_garden_models",
)


# Also suppress at the logging level as a fallback
class AdditionalPropertiesFilter(logging.Filter):
    def filter(self, record):
        return "additionalProperties" not in record.getMessage()


# Apply the filter to the root logger
logging.getLogger().addFilter(AdditionalPropertiesFilter())

__author__ = "Broad Institute"
__email__ = "broadie@broadinstitute.org"
__license__ = "MIT"

# Import version from setuptools-scm generated file
try:
    from ._version import __version__
except ImportError:
    # Fallback for development without installed package
    __version__ = "0.0.0.dev0+unknown"

__all__ = [
    # Core classes
    "Agent",
    "SubAgent",
    "ToolStatus",
    "ToolResponse",
    # Pydantic exports
    "BaseModel",
    "Field",
    # Factory functions
    "create_agent",
    "create_sub_agent",
    # Schemas
    "AgentSchema",
    "SubAgentSchema",
    "ModelSchema",
    "ChannelSchema",
    # Configuration
    "settings",
    # Subpackages
    "tools",
    "server",
    # Utilities
    "slugify",
    "tool",  # Custom tool decorator with approval support
    # Metadata
    "__version__",
]

"""
Buddy AI - Advanced AI Agent Framework

A comprehensive Python framework for building, deploying, and managing intelligent AI agents.
Designed with enterprise-grade capabilities for sophisticated AI applications.

Key Features:
- Multi-model LLM support (OpenAI, Anthropic, Google, Cohere, AWS, Azure, etc.)
- Intelligent agent management with persistent memory
- Extensible tool system and knowledge management
- Multi-agent team collaboration
- Workflow automation and orchestration
- Multiple deployment options

Author: Sriram Sangeeth Mantha
License: MIT
"""

__version__ = "1.0.0"
__author__ = "Sriram Sangeeth Mantha"
__email__ = "sriram.sangeet@gmail.com"
__license__ = "MIT"
__description__ = "A comprehensive Python framework for building and deploying AI agents"

# Core imports for easy access
from buddy.agent import Agent
from buddy.team import Team
from buddy.models.base import Model
from buddy.tools import Toolkit
from buddy.tools.function import Function
from buddy.memory.agent import AgentMemory
from buddy.knowledge.agent import AgentKnowledge

__all__ = [
    "Agent",
    "Team", 
    "Model",
    "Function",
    "Toolkit",
    "AgentMemory",
    "AgentKnowledge",
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    "__description__",
]
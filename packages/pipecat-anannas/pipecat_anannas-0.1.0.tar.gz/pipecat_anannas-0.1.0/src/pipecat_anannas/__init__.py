#
# Copyright (c) 2024–2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Anannas AI integration for Pipecat.

This package provides an LLM service for accessing Anannas AI's unified model gateway
through Pipecat's framework.
"""

from .llm import AnannasLLMService

__version__ = "0.1.0"
__all__ = ["AnannasLLMService"]


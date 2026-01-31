"""
HTTP clients for external APIs.

This module provides client classes for interacting with external services:
- Azure OpenAI (images, chat, TTS)
- ElevenLabs (TTS)
- Reddit (content scraping)
"""

from faceless.clients.azure_openai import AzureOpenAIClient
from faceless.clients.base import BaseHTTPClient

__all__ = [
    "BaseHTTPClient",
    "AzureOpenAIClient",
]

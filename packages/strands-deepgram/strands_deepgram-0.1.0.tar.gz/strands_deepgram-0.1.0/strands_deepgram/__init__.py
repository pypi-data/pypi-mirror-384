"""Deepgram speech processing tool for Strands Agents SDK.

This package provides a comprehensive Deepgram integration for Strands agents,
enabling speech-to-text, text-to-speech, and audio intelligence capabilities.

Example usage:
    ```python
    from strands import Agent
    from strands_deepgram import deepgram

    agent = Agent(tools=[deepgram])
    agent("transcribe this audio file: recording.mp3")
    ```
"""

from .deepgram import deepgram

__version__ = "0.1.0"
__all__ = ["deepgram"]


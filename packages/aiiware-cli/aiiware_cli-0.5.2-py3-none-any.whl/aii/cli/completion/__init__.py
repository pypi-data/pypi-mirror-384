"""Shell completion functionality for aii CLI.

This module provides tab completion for bash, zsh, and fish shells.
"""

from .generator import CompletionGenerator, CompletionSpec
from .installer import CompletionInstaller

__all__ = ["CompletionGenerator", "CompletionSpec", "CompletionInstaller"]

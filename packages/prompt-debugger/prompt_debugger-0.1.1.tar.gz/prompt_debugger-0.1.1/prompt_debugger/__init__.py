"""
Prompt-Debugger - Debug AI responses, understand failures, get suggestions
"""

__version__ = "0.1.1"  # Changed from 0.1.0
__author__ = "Mohamed Imthiyas"  # Changed
__license__ = "MIT"

from prompt_debugger.debugger import AIDebugger
from prompt_debugger.analyzer import ResponseAnalyzer
from prompt_debugger.prompt_checker import PromptChecker
from prompt_debugger.logger import DebugLogger

__all__ = ['AIDebugger', 'ResponseAnalyzer', 'PromptChecker', 'DebugLogger']

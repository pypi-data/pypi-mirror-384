"""MergeSourceFile - A SQL*Plus script processor with Jinja2 template support for resolving file inclusions and variable substitutions."""

__version__ = "1.1.1"
__author__ = "Alejandro G."
__license__ = "MIT"

from .main import main

__all__ = ["main"]

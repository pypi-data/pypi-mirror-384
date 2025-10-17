"""
This check validates that a model has specified a description in its model config.
"""

from typing import Any

description = "Ensure all models include a description"

def check(node: dict[str, Any]):
    assert node['description'] not in (None, '')

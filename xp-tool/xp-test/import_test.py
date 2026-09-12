"""
Run tests with `pytest -v -s`
"""

import xp

def test_import():
	print(f"XP version: {xp.__version__}")

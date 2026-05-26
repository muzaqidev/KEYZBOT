"""Test core tools module."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from core import tools

def test_get_all_tool_names():
    names = tools.get_all_tool_names()
    assert "bash" in names
    assert "read_file" in names
    assert "write_file" in names
    assert "edit_file" in names
    assert "glob_files" in names
    assert "grep_files" in names
    assert "web_search" in names
    assert "web_fetch" in names
    assert "git" in names
    assert len(names) >= 20

def test_execute_bash():
    result = tools.execute("bash", {"command": "echo hello"})
    assert "hello" in result

def test_execute_unknown():
    result = tools.execute("nonexistent_tool", {})
    assert "Unknown" in result

def test_execute_glob():
    result = tools.execute("glob_files", {"pattern": "*.py", "head_limit": 5})
    assert "file(s)" in result or "No files" in result

def test_execute_grep():
    result = tools.execute("grep_files", {"pattern": "import", "include": "*.py", "output_mode": "count"})
    assert "match" in result

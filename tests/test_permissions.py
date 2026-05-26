"""Test permissions module — per-session state."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from core import permissions

def test_session_isolation():
    permissions.set_mode("auto", "s1")
    permissions.set_mode("confirm", "s2")
    assert permissions.get_mode("s1") == "auto"
    assert permissions.get_mode("s2") == "confirm"

def test_check_safe_tool():
    permissions.set_mode("smart", "test")
    action, reason = permissions.check("read_file", sid="test")
    assert action == "approve"

def test_check_destructive_tool():
    permissions.set_mode("smart", "test2")
    action, reason = permissions.check("bash", {"command": "echo hi"}, sid="test2")
    assert action == "confirm"

def test_check_auto_mode():
    permissions.set_mode("auto", "test3")
    action, reason = permissions.check("bash", {"command": "rm -rf /"}, sid="test3")
    assert action == "approve"

def test_override():
    permissions.override("bash", "approve", "test4")
    action, reason = permissions.check("bash", sid="test4")
    assert action == "approve"

def test_cleanup():
    permissions.set_mode("auto", "to_delete")
    permissions.cleanup_session("to_delete")
    # After cleanup, should get default mode
    assert permissions.get_mode("to_delete") == "smart"

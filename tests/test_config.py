"""Test config module — provider system."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from core import config

def test_preset_providers():
    assert len(config.PRESET_PROVIDERS) >= 5
    ids = [p["id"] for p in config.PRESET_PROVIDERS]
    assert "openai" in ids
    assert "anthropic" in ids
    assert "groq" in ids
    assert "opengateway" in ids

def test_get_all_providers():
    providers = config.get_all_providers()
    assert len(providers) >= 5
    ids = [p["id"] for p in providers]
    assert "openai" in ids

def test_save_and_load_providers():
    # Save custom
    config.save_provider_config("test_provider", api_key="test_key_123")
    loaded = config.load_providers()
    found = [p for p in loaded.get("providers", []) if p.get("id") == "test_provider"]
    assert len(found) == 1
    assert found[0]["api_key"] == "test_key_123"
    # Cleanup
    config.remove_provider("test_provider")

def test_add_custom_provider():
    p = config.add_custom_provider("mytest", "My Test", "https://test.com/v1", "key123", "test-model")
    assert p["id"] == "mytest"
    assert p["name"] == "My Test"
    all_p = config.get_all_providers()
    ids = [x["id"] for x in all_p]
    assert "mytest" in ids
    # Cleanup
    config.remove_provider("mytest")

def test_set_active_provider():
    config.set_active_provider("groq")
    saved = config.load_providers()
    assert saved.get("active") == "groq"
    # Reset
    config.set_active_provider("opengateway")

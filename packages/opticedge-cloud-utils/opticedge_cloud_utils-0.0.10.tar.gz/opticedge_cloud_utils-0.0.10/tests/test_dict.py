# tests/test_utils.py
import pytest
import importlib

MODULE_PATH = "opticedge_cloud_utils.dict"  # adjust if deep_merge is in another file/module


@pytest.fixture
def module():
    """Dynamically import and reload the target module before each test."""
    mod = importlib.import_module(MODULE_PATH)
    importlib.reload(mod)
    return mod


def test_merges_non_overlapping_keys(module):
    base = {"a": 1}
    updates = {"b": 2}
    result = module.deep_merge(base, updates)
    assert result == {"a": 1, "b": 2}


def test_overwrites_existing_value(module):
    base = {"a": 1, "b": 2}
    updates = {"b": 99}
    result = module.deep_merge(base, updates)
    assert result == {"a": 1, "b": 99}


def test_deep_merges_nested_dicts(module):
    base = {"a": {"x": 1, "y": 2}}
    updates = {"a": {"y": 99, "z": 3}}
    result = module.deep_merge(base, updates)
    assert result == {"a": {"x": 1, "y": 99, "z": 3}}


def test_removes_key_when_value_none_and_delete_nulls_true(module):
    base = {"a": 1, "b": 2}
    updates = {"b": None}
    result = module.deep_merge(base, updates, delete_nulls=True)
    assert result == {"a": 1}


def test_preserves_none_when_delete_nulls_false(module):
    base = {"a": 1, "b": 2}
    updates = {"b": None}
    result = module.deep_merge(base, updates, delete_nulls=False)
    assert result == {"a": 1, "b": None}


def test_handles_empty_updates(module):
    base = {"a": 1}
    updates = {}
    result = module.deep_merge(base, updates)
    assert result == {"a": 1}


def test_handles_empty_base(module):
    base = {}
    updates = {"x": 10}
    result = module.deep_merge(base, updates)
    assert result == {"x": 10}


def test_original_base_not_modified(module):
    base = {"a": {"b": 1}}
    updates = {"a": {"c": 2}}
    result = module.deep_merge(base, updates)
    assert result == {"a": {"b": 1, "c": 2}}
    assert base == {"a": {"b": 1}}
    assert id(result) != id(base)

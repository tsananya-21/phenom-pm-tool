import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from synthesis.synthesizer import _parse_json, _strip_fences, _fix_trailing_commas


def test_clean_json():
    raw = '{"a": 1, "b": "hello"}'
    assert _parse_json(raw) == {"a": 1, "b": "hello"}


def test_strip_json_fence():
    raw = '```json\n{"a": 1}\n```'
    assert _strip_fences(raw) == '{"a": 1}'


def test_strip_plain_fence():
    raw = '```\n{"a": 1}\n```'
    assert _strip_fences(raw) == '{"a": 1}'


def test_fix_trailing_comma_object():
    raw = '{"a": 1, "b": 2,}'
    assert _fix_trailing_commas(raw) == '{"a": 1, "b": 2}'


def test_fix_trailing_comma_array():
    raw = '[1, 2, 3,]'
    assert _fix_trailing_commas(raw) == '[1, 2, 3]'


def test_fenced_with_trailing_comma():
    raw = '```json\n{"a": 1, "b": [1, 2,],}\n```'
    result = _parse_json(raw)
    assert result == {"a": 1, "b": [1, 2]}


def test_leading_whitespace():
    raw = '   \n  {"x": true}  \n  '
    assert _parse_json(raw) == {"x": True}


def test_invalid_json_raises():
    with pytest.raises((ValueError, Exception)):
        _parse_json('this is not json at all :::')


def test_nested_structure():
    raw = '{"pitch": {"hook": "test", "problem": "foo",}, "score": 0.8,}'
    result = _parse_json(raw)
    assert result["pitch"]["hook"] == "test"
    assert result["score"] == 0.8


def test_mock_bundle_builds_valid_user_message():
    from search.mock_search import MockSearchProvider
    from synthesis.prompts import build_user_message, build_system_prompt
    import json

    bundle = MockSearchProvider().search_company("HubSpot")
    user_msg = build_user_message(bundle)
    sys_prompt = build_system_prompt()

    assert "HubSpot" in user_msg
    assert "EVIDENCE BUNDLE" in user_msg
    assert "Phenom" in sys_prompt
    assert len(sys_prompt) > 500

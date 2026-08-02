from hindsight.llm.gemini_provider import _clean_schema
from hindsight.llm.structured import submit_spec
from hindsight.models import RecallResult


def test_property_named_title_survives_cleaning():
    schema = _clean_schema(submit_spec(RecallResult, "submit", "d").input_schema)
    items = schema["properties"]["prior_incidents"]["items"]
    assert "title" in items["properties"]
    for name in items.get("required", []):
        assert name in items["properties"]


def test_nested_refs_are_inlined_for_gemini():
    schema = _clean_schema(submit_spec(RecallResult, "submit", "d").input_schema)
    text = str(schema)
    assert "$ref" not in text
    assert "$defs" not in text


def test_schema_metadata_title_is_dropped():
    cleaned = _clean_schema({"type": "object", "title": "Meta", "properties": {}})
    assert "title" not in cleaned
    assert cleaned["type"] == "OBJECT"

from app.agent.parser import parse_model_output


def test_valid_json():
    plan, warnings, recovered = parse_model_output('{"intent":"action","message":"ok","actions":[],"analytics":[]}')
    assert plan is not None
    assert plan.message == "ok"
    assert warnings == []
    assert recovered is False


def test_markdown_json():
    text = '```json\n{"intent":"conversation","message":"ok","actions":[],"analytics":[]}\n```'
    plan, _, _ = parse_model_output(text)
    assert plan is not None


def test_extra_action_fields_are_rejected():
    text = '{"intent":"action","message":"ok","actions":[{"type":"set_accent_color","accent":"red","surprise":"ignored"}],"analytics":[]}'
    plan, warnings, recovered = parse_model_output(text)
    assert plan is not None
    assert plan.actions == []
    assert recovered is True
    assert warnings


def test_unknown_action_is_dropped():
    text = '{"intent":"action","message":"ok","actions":[{"type":"delete_database"}],"analytics":[]}'
    plan, warnings, recovered = parse_model_output(text)
    assert plan is not None
    assert plan.actions == []
    assert recovered is True
    assert warnings


def test_trailing_comma_recovers():
    text = '{"intent":"conversation","message":"ok","actions":[],"analytics":[],}'
    plan, warnings, recovered = parse_model_output(text)
    assert plan is not None
    assert recovered is False
    assert any("repair" in warning.lower() for warning in warnings)


def test_extra_top_level_fields_are_removed_safely():
    text = '{"intent":"conversation","message":"ok","actions":[],"analytics":[],"shell":"rm -rf /"}'
    plan, warnings, recovered = parse_model_output(text)
    assert plan is not None
    assert plan.actions == []
    assert recovered is True
    assert any("top-level" in warning.lower() for warning in warnings)


def test_invalid_accent_value_is_dropped():
    text = '{"intent":"action","message":"ok","actions":[{"type":"set_accent_color","accent":"background:red"}],"analytics":[]}'
    plan, warnings, _ = parse_model_output(text)
    assert plan is not None
    assert plan.actions == []
    assert warnings

def test_invalid_action_value_is_dropped():
    text = '{"intent":"action","message":"ok","actions":[{"type":"set_text_size","size":9999}],"analytics":[]}'
    plan, warnings, _ = parse_model_output(text)
    assert plan is not None
    assert plan.actions == []
    assert warnings


def test_composition_action_round_trips_through_parser():
    text = '{"intent":"action","message":"Model comparison composed.","actions":[{"type":"compose_widgets","title":"Model comparison","widgets":["model-comparison","model-usage","response-time","system-status"]}],"analytics":[]}'
    plan, warnings, _ = parse_model_output(text)
    assert plan is not None
    assert not warnings
    assert plan.actions[0].type == "compose_widgets"
    assert plan.actions[0].widgets == ["model-comparison", "model-usage", "response-time", "system-status"]

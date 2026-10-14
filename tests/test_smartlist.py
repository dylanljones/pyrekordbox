import pytest

from pyrekordbox.masterdb.smartlist import Operator, Property, SmartList


@pytest.mark.parametrize(
    "value",
    [
        "Techno (Raw / Deep)",
        "Techno (Peak Time / Driving)",
        "Techno (Raw / Deep / Hypnotic)",
        'Text /> & <tag> "quoted"',
    ],
)
@pytest.mark.parametrize("field", ["value_left", "value_right", "unit"])
def test_xml_preserves_condition_values(value, field):
    smart = SmartList()
    smart.playlist_id = 123456
    values = {"value_left": "", "value_right": "", "unit": ""}
    values[field] = value
    smart.add_condition(Property.GENRE, Operator.EQUAL, **values)

    source = smart.to_xml()
    assert " />" not in source
    assert source.endswith("/></NODE>")

    restored = SmartList()
    restored.parse(source)
    assert restored.conditions == smart.conditions
    assert restored.playlist_id == str(smart.playlist_id)

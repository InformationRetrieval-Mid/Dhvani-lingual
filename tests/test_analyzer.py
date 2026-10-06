import pytest

from text.analyzer import analyze


def test_none_mode():
    result = analyze("लड़कियों बारिश", "none")

    assert result == [
        ("लड़कियों", 0),
        ("बारिश", 1),
    ]


def test_light_mode():
    result = analyze("लड़कियों किताबों", "light")

    assert result == [
        ("लड़क", 0),
        ("किताब", 1),
    ]


def test_positions_are_preserved():
    result = analyze("बारिश हुई आज", "light")

    assert [position for _, position in result] == [0, 1, 2]


def test_invalid_mode():
    with pytest.raises(ValueError):
        analyze("बारिश", "aggr")
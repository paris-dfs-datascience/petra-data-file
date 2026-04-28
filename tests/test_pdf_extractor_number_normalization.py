from src.pipeline.pdf_extractor import _join_split_numbers


def test_rejoins_thousands_separator_artifacts():
    assert _join_split_numbers("8 9,674") == "89,674"
    assert _join_split_numbers("1 0,358,013") == "10,358,013"
    assert _join_split_numbers("1 0,410,049") == "10,410,049"
    assert _join_split_numbers("2 59,479") == "259,479"
    assert _join_split_numbers("1 86,554") == "186,554"


def test_rejoins_space_before_thousands_comma():
    assert _join_split_numbers("5 ,388") == "5,388"


def test_rejoins_decimal_and_percent_artifact():
    assert _join_split_numbers("1 03.29 %") == "103.29%"


def test_rejoins_in_sentence_context():
    sentence = "Total expenses of 2 59,479 for the year"
    assert _join_split_numbers(sentence) == "Total expenses of 259,479 for the year"


def test_does_not_join_year_columns():
    assert _join_split_numbers("2024 2025") == "2024 2025"


def test_does_not_join_page_of_count():
    assert _join_split_numbers("Page 5 of 10") == "Page 5 of 10"


def test_does_not_join_currency_symbol_gap():
    assert _join_split_numbers("$ 1,234") == "$ 1,234"


def test_only_collapses_a_single_space_between_columns():
    assert _join_split_numbers("12,345  6,789") == "12,345  6,789"


def test_handles_empty_and_none_safe_inputs():
    assert _join_split_numbers("") == ""
    assert _join_split_numbers("no digits here") == "no digits here"

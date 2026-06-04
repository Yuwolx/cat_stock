from src.utils.text_utils import display_value, format_krw_amount, format_krw_eok, format_number


def test_format_krw_eok_switches_to_jo_for_large_amounts() -> None:
    assert format_krw_eok(9_999.9) == "9,999.9억"
    assert format_krw_eok(10_000) == "1조"
    assert format_krw_eok(121_726.1) == "12.2조"
    assert format_krw_eok("-67087.0억") == "-6.7조"
    assert format_krw_eok("+10.0억") == "+10억"


def test_format_krw_amount_cleans_units_and_decimal_noise() -> None:
    assert format_krw_amount("20.0조") == "20조"
    assert format_krw_amount("35000.0억") == "3.5조"
    assert format_krw_amount(1_250_000_000_000) == "1.2조"
    assert format_krw_amount(None) == "—"


def test_number_and_empty_display_are_prompt_friendly() -> None:
    assert format_number(10.0) == "10"
    assert format_number(10.25) == "10.2"
    assert display_value(None) == "—"

from src.collectors.theme.peer_collector import get_theme_peers


def test_theme_peers_do_not_expose_mock_peers_in_real_mode_without_mapping() -> None:
    result = get_theme_peers("HBM", api_key="", use_mock_data=False)

    assert result == {"disclosures": [], "global_peers": []}


def test_theme_peers_keep_sample_values_in_mock_mode() -> None:
    result = get_theme_peers("HBM", api_key="", use_mock_data=True)

    assert result["global_peers"] == ["NVIDIA", "TSMC", "ASML"]

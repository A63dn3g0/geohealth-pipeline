from analysis.geography import join_key

def test_official_lhd_label():
    assert join_key("Sydney LHD") == join_key("Sydney")
    assert join_key("Hunter New England LHD") == join_key("Hunter New England")

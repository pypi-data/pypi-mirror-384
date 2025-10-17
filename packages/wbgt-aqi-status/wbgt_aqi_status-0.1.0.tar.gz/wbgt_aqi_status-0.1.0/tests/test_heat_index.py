from wbgt_aqi_status.core import heat_index_f

def test_heat_index_basic():
    # Known-ish scenario: T=90F, RH=85% → ~117F (within a small tolerance)
    hi = heat_index_f(90, 85)
    assert 114 <= hi <= 120

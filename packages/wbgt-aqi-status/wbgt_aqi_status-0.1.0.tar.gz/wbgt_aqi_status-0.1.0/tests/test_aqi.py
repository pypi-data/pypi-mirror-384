from wbgt_aqi_status.core import aqi_from_pm25

def test_aqi_breakpoints():
    assert aqi_from_pm25(12.0) == 50
    assert aqi_from_pm25(12.1) == 51
    assert aqi_from_pm25(35.4) == 100
    assert aqi_from_pm25(35.5) == 101
    assert aqi_from_pm25(55.4) == 150
    assert aqi_from_pm25(55.5) == 151

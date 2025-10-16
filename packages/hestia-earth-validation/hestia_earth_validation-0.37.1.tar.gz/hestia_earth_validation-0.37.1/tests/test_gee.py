from hestia_earth.validation.gee import id_to_level


def test_id_to_level():
    assert id_to_level('GADM-ITA') == 0
    assert id_to_level('GADM-ITA.16_1') == 1
    assert id_to_level('GADM-ITA.16.10_1') == 2
    assert id_to_level('GADM-ITA.16.10.3_1') == 3
    assert id_to_level('GADM-RWA.5.3.10.4_1') == 4
    assert id_to_level('GADM-RWA.5.3.10.4.3_1') == 5

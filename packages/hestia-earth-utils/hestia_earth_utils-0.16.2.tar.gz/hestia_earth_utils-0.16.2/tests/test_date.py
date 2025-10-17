from hestia_earth.utils.date import diff_in_years, is_in_days, is_in_months


def test_diff_in_years():
    assert diff_in_years('1990-01-01', '1999-02-01') == 9.1


def test_is_in_days():
    assert not is_in_days('2000')
    assert not is_in_days('2000-01')
    assert is_in_days('2000-01-01')


def test_is_in_months():
    assert not is_in_months('2000')
    assert is_in_months('2000-01')
    assert not is_in_months('2000-01-01')

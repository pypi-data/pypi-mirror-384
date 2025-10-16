import numpy

from .utils import fixtures_path
from hestia_earth.utils.lookup import (
    load_lookup,
    column_name,
    get_table_value,
    find_term_ids_by,
    download_lookup,
    extract_grouped_data,
    extract_grouped_data_closest_date,
    _get_single_table_value,
    lookup_term_ids,
    lookup_columns
)


def test_load_lookup_numpy_array():
    lookup = load_lookup(f"{fixtures_path}/lookup.csv")
    assert isinstance(lookup, numpy.recarray)


def test_column_name():
    assert column_name('Maize (corn)') == 'Maize_corn'
    assert column_name('grassland/pasture/meadow') == 'grasslandpasturemeadow'


def test_get_table_value():
    lookup = load_lookup(f"{fixtures_path}/lookup.csv")

    # single column match
    assert get_table_value(lookup, column_name('Col1'), 'val10', column_name('Col3')) == 'val30'
    # multiple column match
    assert get_table_value(lookup, [
        column_name('Col1'),
        column_name('Col2'),
    ], [
        'val10',
        'val21'
    ], column_name('Col3')) == 'val31'
    # no match
    assert not get_table_value(lookup, column_name('Col10'), 'val10', column_name('Col3'))

    # column does not exist
    assert not get_table_value(lookup, [
        column_name('Col1'),
        column_name('Col2'),
    ], [
        'random',
        'val21'
    ], column_name('random'))

    # table does not exist
    assert not get_table_value(None, column_name('Col10'), 'val10', column_name('Col3'))


def test_get_table_value_empty():
    lookup = load_lookup(f"{fixtures_path}/lookup.csv")
    assert get_table_value(lookup, column_name('Col1'), 'val10', column_name('Col4')) is None
    assert get_table_value(lookup, column_name('Col2'), 'val22', column_name('Col1')) is None


def test_find_term_ids_by():
    lookup = download_lookup('crop.csv')
    assert 'wheatGrain' in find_term_ids_by(lookup, column_name('cropGroupingFAO'), 'Temporary crops')


def test_download_lookup_with_index():
    filename = 'crop.csv'
    lookup = download_lookup(filename, keep_in_memory=False, build_index=True)
    assert isinstance(lookup, dict)


def test_download_lookup_without_index():
    filename = 'crop.csv'
    lookup = download_lookup(filename, keep_in_memory=False, build_index=False)
    assert isinstance(lookup, numpy.recarray)


def test_handle_missing_float_value():
    filename = 'measurement.csv'
    lookup = download_lookup(filename)
    assert get_table_value(lookup, 'termid', 'rainfallPeriod', 'maximum') is None


def test_handle_missing_string_value():
    filename = 'crop.csv'
    lookup = download_lookup(filename)
    assert get_table_value(lookup, 'termid', 'fixedNitrogen', 'combustion_factor_crop_residue') is None


def test_handle_missing_lookup_value():
    filename = 'region-crop-cropGroupingFaostatProduction-price.csv'
    lookup = download_lookup(filename)
    assert get_table_value(lookup, 'termid', 'GADM-CYP', column_name('Sugar crops nes')) is None


def test_extract_grouped_data_no_data():
    assert not extract_grouped_data('', '2000')
    assert not extract_grouped_data('-', '2000')


def test_extract_grouped_data():
    data = 'Average_price_per_tonne:106950.5556;1991:-;1992:-'
    assert extract_grouped_data(data, 'Average_price_per_tonne') == '106950.5556'
    assert extract_grouped_data(data, '2010') is None


def test_extract_grouped_data_lookup():
    filename = 'region-crop-cropGroupingFaostatProduction-price.csv'
    lookup = download_lookup(filename)
    data = get_table_value(lookup, 'termid', 'GADM-NPL', column_name('Chick peas, dry'))
    assert extract_grouped_data(data, '2000') is None
    assert extract_grouped_data(data, '2012') is not None

    filename = 'region-animalProduct-animalProductGroupingFAO-price.csv'
    lookup = download_lookup(filename)
    data = get_table_value(lookup, 'termid', 'GADM-NPL', column_name('Eggs from other birds in shell, fresh, n.e.c.'))
    assert extract_grouped_data(data, '2000') is None
    assert extract_grouped_data(data, '2012') is not None


def test_get_single_table_value_float_values():
    filename = 'ecoClimateZone.csv'
    lookup = download_lookup(filename)
    column = column_name('STEHFEST_BOUWMAN_2006_N2O-N_FACTOR')
    assert _get_single_table_value(lookup, column_name('ecoClimateZone'), 11, column) == -0.3022


def test_extract_grouped_data_closest_date_no_data():
    assert not extract_grouped_data_closest_date('', 2000)
    assert not extract_grouped_data_closest_date('-', 2000)


def test_extract_grouped_data_closest_date():
    data = '2000:-;2001:0.1;2002:0.2;2003:0.3;2004:0.4;2005:0.5'
    assert extract_grouped_data_closest_date(data, 2000) == '0.1'
    assert extract_grouped_data_closest_date(data, 2001) == '0.1'
    assert extract_grouped_data_closest_date(data, 2020) == '0.5'


def test_lookup_term_ids():
    assert 'wheatGrain' in lookup_term_ids(download_lookup('crop.csv'))


def test_lookup_columns():
    assert 'termid' in lookup_columns(download_lookup('crop.csv'))

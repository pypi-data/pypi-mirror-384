import io
import csv
import re
import numpy as np

_MISSING_VALUE = '-'
_MISSING = -99999
_DELIMITER = ','
_QUOTE_CHAR = '"'
ENCODING = 'ISO-8859-1'
# default: " !#$%&'()*+,-./:;<=>?@[\\]^{|}~"
_DELETE_CHARS = " !#$%&'()*,./:;<=>?@^{|}~"


def is_missing_value(value): return value == _MISSING_VALUE or value == _MISSING or value == str(_MISSING)


def _replace_missing_values(value: str): return str(_MISSING) if str(value) == _MISSING_VALUE else value


def _replace_chars(value: str): return re.sub(f'[{re.escape(_DELETE_CHARS)}]', '', value.replace(' ', '_'))


def _text_to_csv(csv_content: str):
    return csv.reader(io.StringIO(csv_content.strip()), delimiter=_DELIMITER, quotechar=_QUOTE_CHAR)


def _csv_reader_converter(field_str_bytes):
    try:
        field_str = field_str_bytes if isinstance(field_str_bytes, str) else field_str_bytes.decode('utf-8')
        return _replace_missing_values(field_str)
    except Exception:
        return str(_MISSING)


def _get_columns(csv_content: str):
    try:
        reader = _text_to_csv(csv_content)
        names = next(reader)
        return list(map(_replace_chars, names))
    except StopIteration:
        return []


def csv_str_to_recarray(csv_content: str) -> np.recarray:
    names = _get_columns(csv_content)
    num_cols = len(names)

    converters_dict = {
        i: _csv_reader_converter
        for i in range(num_cols)
    }

    # TODO: find the maximum column size instead of using 1000
    max_size = 1000
    return np.loadtxt(
        io.StringIO(csv_content.strip()),
        delimiter=_DELIMITER,
        quotechar=_QUOTE_CHAR,
        skiprows=1,
        converters=converters_dict,
        dtype=[(name, f"U{max_size}") for name in names],
        encoding=ENCODING
    ).view(np.recarray)


def csv_file_to_recarray(filepath: str):
    with open(filepath, 'r', encoding=ENCODING) as f:
        content = f.read()
    return csv_str_to_recarray(content)

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


def _get_columns(csv_content: str):
    try:
        reader = _text_to_csv(csv_content)
        names = next(reader)
        return list(map(_replace_chars, names))
    except StopIteration:
        return []


def _get_rows(csv_content: str):
    string_io = io.StringIO(csv_content.strip())
    try:
        next(string_io)
    except StopIteration:
        return

    return csv.reader(string_io, delimiter=_DELIMITER, quotechar=_QUOTE_CHAR)


def _csv_str_to_recarray_chunks_numpy(csv_content: str, chunk_size: int = 5):
    names = _get_columns(csv_content)
    num_cols = len(names)

    max_size = 1000
    dtype = [(name, f"U{max_size}") for name in names]

    reader = _get_rows(csv_content)

    # 4. Process the file in batches
    chunk_rows = []
    for row in reader:
        if not row:
            continue
        if len(row) != num_cols:
            continue

        # replace missing values
        processed_row = tuple(_replace_missing_values(field) for field in row)
        chunk_rows.append(processed_row)

        if len(chunk_rows) >= chunk_size:
            yield np.array(chunk_rows, dtype=dtype).view(np.recarray)
            chunk_rows = []

    if chunk_rows:
        yield np.array(chunk_rows, dtype=dtype).view(np.recarray)


def csv_str_to_recarray(csv_content: str) -> np.recarray:
    array_rows = list(_csv_str_to_recarray_chunks_numpy(csv_content))
    return np.hstack(array_rows).view(np.recarray)


def csv_file_to_recarray(filepath: str):
    with open(filepath, 'r', encoding=ENCODING) as f:
        content = f.read()
    return csv_str_to_recarray(content)

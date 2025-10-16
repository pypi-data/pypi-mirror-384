from io import BytesIO
import pandas as pd
from hestia_earth.schema import TermTermType

from .utils import NO_VALUE
from .utils.csv import df_to_csv_buffer
from .utils.storage import file_exists, load_from_storage, write_to_storage
from .utils.cycle import INDEX_COLUMN, find_cycles
from .cycle import cycle_yield_distribution

FOLDER = 'likelihood_files'
TERM_TYPE_TO_KEY = {
    TermTermType.CROP.value: 'products',
    TermTermType.INORGANICFERTILISER.value: 'inputs',
    TermTermType.ORGANICFERTILISER.value: 'inputs'
}


def _read_likl_file(likl_filename: str):
    data = load_from_storage(likl_filename)
    df = pd.read_csv(BytesIO(data), na_values=NO_VALUE)
    return df.set_index(INDEX_COLUMN) if not df.empty else df


def _generate_likl_file(country_id: str, product_id: str, filepath: str, limit: int):
    cycles = find_cycles(country_id, product_id, limit=limit)
    df = cycle_yield_distribution(cycles)
    df.fillna(NO_VALUE, inplace=True)
    write_to_storage(filepath, df_to_csv_buffer(df))
    return df


def likl_filename(country_id: str, product_id: str): return f'{country_id}_{product_id}_non-aggregated_cycles.csv'


def generate_likl_file(country_id: str, product_id: str, limit: int = 10000, overwrite=False):
    """
    Return all likelihood data for a given country and a given product.
    If likelihood file exisits, data will be read in; otherwise, generate likelihood data and store
    into likl_filename path.

    Parameters
    ----------
    country_id: str
        Country `@id` from Hestia glossary, e.g. 'GADM-GBR' (regions not supported yet).
    product_id: str
        Product `@id` from Hestia glossary, e.g. 'wheatGrain' as a crop product ID.
    limit: int
        Max number of Cycles to compute likelihood data. Defaults to `10000`.
    overwrite: bool
        Whether to overwrite existing likelihood file or not. Defaults to `False`.

    Returns
    -------
    pd.DataFrame
        A dataframe storing the likelihood data.
    """
    filepath = f"{FOLDER}/{likl_filename(country_id, product_id)}"
    read_existing = file_exists(filepath) and not overwrite
    return _read_likl_file(filepath) if read_existing else _generate_likl_file(country_id, product_id, filepath, limit)

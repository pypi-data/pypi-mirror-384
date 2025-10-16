import numpy as np
from hestia_earth.schema import SchemaType, TermTermType
from hestia_earth.utils.lookup import download_lookup, lookup_term_ids
from hestia_earth.utils.api import find_node

SIGMA_SCALER = 3.0  # Scaler (for standard deviation) value of the prior
NO_VALUE = '-'


def get_product_ids():
    """
    Get the list of product `@id` included in the prior/posterior files.

    Returns
    -------
    List[str]
        A list of Hestia `@id`.
    """
    return lookup_term_ids(download_lookup('crop.csv'))


def get_country_ids():
    """
    Get the list of country `@id` included in the prior/posterior files.

    Returns
    -------
    List[str]
        A list of Hestia `@id`.
    """
    terms = find_node(SchemaType.TERM, {
        'termType': TermTermType.REGION.value,
        'gadmLevel': 0
    }, 1000)
    return sorted(list(map(lambda n: n['@id'], terms)))


def is_nonempty_str(value): return (type(value) in [str, np.str_, np.string_]) and value != '' and value != NO_VALUE


def get_stats_from_df(df, column: str, row_id: str):
    try:
        yield_stats = df.loc[row_id][column]
        # this happens when read priors in from a CSV file
        vals = [float(v) for v in yield_stats.strip('()').split(',')] if isinstance(yield_stats, str) else yield_stats
        return vals[0], vals[1]  # mu, sigma
    except Exception:
        return None, None  # data could not be parsed


def _progress(values: list):
    import os
    # disable when using on AWS
    if os.environ.get('AWS_REGION') is None:
        try:
            from tqdm import tqdm
            return tqdm(values)
        except ModuleNotFoundError:
            pass
    return values

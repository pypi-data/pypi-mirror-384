from .utils import get_stats_from_df, get_product_ids
from .utils.storage import file_exists
from .utils.fao import get_fao_yield
from .utils.priors import (
    FOLDER, read_prior_stats, generate_and_save_priors, get_countries_priors
)

PRIOR_YIELD_FILENAME = 'FAO_Yield_prior_per_product_per_country.csv'


def _get_priors():
    product_ids = get_product_ids()
    return get_countries_priors(product_ids, get_fao_yield)


def generate_prior_yield_file(overwrite=False):
    """
    Return all prior statistics (means, std and n_years) of FAO yield from a CSV file.
    If prior file exisits, prior data will be read in; otherwise, generate priors and store into prior_file path.

    Parameters
    ----------
    n: int
        Optional - number of rows to return. Defaults to all.
    overwrite: bool
        Optional - whether to overwrite existing prior file or not. Defaults to `False`.

    Returns
    -------
    pd.DataFrame
        DataFrame storing the prior of the means.
    """
    filepath = f"{FOLDER}/{PRIOR_YIELD_FILENAME}"
    read_existing = file_exists(filepath) and not overwrite
    return read_prior_stats(filepath) if read_existing else generate_and_save_priors(filepath, _get_priors)


def get_prior(country_id: str, product_id: str):
    """
    Return prior data for a given country and a given product.
    Data is read from the file containing all prior data.

    Parameters
    ----------
    country_id: str
        Region `@id` from Hestia glossary, e.g. 'GADM-GBR', or 'region-south-america'.
    product_id: str
        Fertiliser term `@id` from Hestia glossary, e.g. 'ureaKgN'.

    Returns
    -------
    tuple(mu, sd)
        Mean value (mu) and weighted standard deviation (sigma). Could be None is no prior found for the combination.
    """
    df = read_prior_stats(f"{FOLDER}/{PRIOR_YIELD_FILENAME}")
    return get_stats_from_df(df, country_id, product_id)

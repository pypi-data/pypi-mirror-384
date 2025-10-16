from .utils import get_stats_from_df
from .utils.storage import file_exists
from .utils.fao import get_fao_pestuse
from .utils.priors import FOLDER, read_prior_stats, generate_and_save_priors, get_countries_priors
from .utils.cycle import PESTICIDE_COLUMN

PRIOR_PEST_FILENAME = 'FAO_Pest_prior_per_country.csv'
PEST_COLUMN_FAO = 'Pesticides (total)'


def get_fao_pest(country_id: str, term_id: str = '', n_years: int = 10):
    """
    Look up the FAO pesticide use per country from the glossary.

    Parameters
    ----------
    country_id: str
        Region `@id` from Hestia glossary, e.g. 'GADM-GBR', or 'region-south-america'.
    term_id : str
        Not used.
    n_years: int
        Number of years (in reverse chronological order) of FAO data record to get. Defaults to `10` years.

    Returns
    -------
    nunpy.array or None
        A 2-D array with years and pesticide use values from FAO pesticide record, if successful.
    """
    return get_fao_pestuse(country_id, PEST_COLUMN_FAO, n_years=n_years)


def _get_priors():
    return get_countries_priors([PESTICIDE_COLUMN], get_fao_pest)


def generate_prior_pest_file(overwrite=False):
    """
    Return all prior statistics (means, std and n_years) of FAO pesticide use from a CSV file.
    If prior file exisits, prior data will be read in; otherwise, generate priors and stores it on disk.

    Parameters
    ----------
    overwrite: bool
        Optional - whether to overwrite existing prior file or not.

    Returns
    -------
    pd.DataFrame
        The prior of the means.
    """
    filepath = f"{FOLDER}/{PRIOR_PEST_FILENAME}"
    read_existing = file_exists(filepath) and not overwrite
    return read_prior_stats(filepath) if read_existing else generate_and_save_priors(filepath, _get_priors)


def get_prior(country_id: str):
    """
    Return prior data for a given country. Data is read from the file containing all prior data.

    Parameters
    ----------
    country_id: str
        Region `@id` from Hestia glossary, e.g. 'GADM-GBR', or 'region-south-america'.

    Returns
    -------
    tuple(mu, sd)
        Mean value (mu) and worldwide/regional sd (sigma). Could be None is no prior found for the combination.
    """
    df = read_prior_stats(f"{FOLDER}/{PRIOR_PEST_FILENAME}")
    return get_stats_from_df(df, country_id, PESTICIDE_COLUMN)

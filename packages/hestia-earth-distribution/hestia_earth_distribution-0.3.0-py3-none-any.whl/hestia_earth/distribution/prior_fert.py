from .utils import get_stats_from_df
from .utils.storage import file_exists
from .utils.fao import get_fao_fertuse
from .utils.cycle import get_fert_group_id, get_fert_ids
from .utils.priors import FOLDER, read_prior_stats, generate_and_save_priors, get_countries_priors

PRIOR_FERT_FILENAME = 'FAO_Fert_prior_per_input_per_country.csv'


def get_fao_fert(country_id: str, input_id: str, n_years: int = 10):
    """
    Look up the FAO fertiliser use per country from the glossary.

    Parameters
    ----------
    country_id: str
        Region `@id` from Hestia glossary, e.g. 'GADM-GBR', or 'region-south-america'.
    fert_id: str
        Inorganic or organic fertiliser term ID from Hestia glossary, e.g. 'ammoniumNitrateKgN'.
    n_years: int
        Number of years (in reverse chronological order) of FAO data record to get. Defaults to `10` years.

    Returns
    -------
    nunpy.array or None
        A 2-D array with years and fertiliser values from FAO record, if successful.
    """
    fert_id = get_fert_group_id(input_id)
    return get_fao_fertuse(country_id, fert_id, n_years=n_years)


def _get_priors():
    input_ids = get_fert_ids()
    return get_countries_priors(input_ids, get_fao_fertuse)


def generate_prior_fert_file(overwrite=False):
    """
    Return all prior statistics (means, std and n_years) of FAO fertiliser use from a CSV file.
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
    filepath = f"{FOLDER}/{PRIOR_FERT_FILENAME}"
    read_existing = file_exists(filepath) and not overwrite
    return read_prior_stats(filepath) if read_existing else generate_and_save_priors(filepath, _get_priors)


def get_prior(country_id: str, input_id: str):
    """
    Return prior data for a given country and a given input.
    Data is read from the file containing all prior data.

    Parameters
    ----------
    country_id: str
        Region `@id` from Hestia glossary, e.g. 'GADM-GBR', or 'region-south-america'.
    input_id: str
        Fertiliser term `@id` from Hestia glossary, e.g. 'ureaKgN'.

    Returns
    -------
    tuple(mu, sd)
        Mean value (mu) and weighted standard deviation (sigma). Could be None is no prior found for the combination.
    """
    df = read_prior_stats(f"{FOLDER}/{PRIOR_FERT_FILENAME}")
    fert_id = get_fert_group_id(input_id)
    return get_stats_from_df(df, country_id, fert_id)

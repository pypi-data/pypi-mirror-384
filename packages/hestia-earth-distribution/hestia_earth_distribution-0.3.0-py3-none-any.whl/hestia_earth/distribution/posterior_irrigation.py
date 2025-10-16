from .utils.cycle import IRRIGATION_COLUMN
from .utils.posterior import update_all_post_data, get_post_data, get_post_ensemble_data
from .prior_irrigation import generate_prior_irrigation_file


def get_post_ensemble(country_id: str, product_id: str, overwrite=False, df_prior=None):
    """
    Return posterior data for a given country, a given product and a given input.
    If posterior file exisits, data will be read in; otherwise, generate posterior data and store
    into a pickle or json file.

    Parameters
    ----------
    country_id: str
        Region `@id` from Hestia glossary, e.g. 'GADM-GBR', or 'region-south-america'.
    product_id: str
        Product term `@id` from Hestia glossary, e.g. 'wheatGrain'.
    overwrite: bool
        Whether to overwrite existing posterior file or not. Defaults to `False`.
    df_prior: pd.DataFrame
        Optional - if prior file is already loaded, pass it here.

    Returns
    -------
    tuple(mu, sd)
        List of float storing the posterior mu and sd ensembles.
    """
    return get_post_ensemble_data(country_id, product_id, 'waterSourceUnspecified', overwrite=overwrite,
                                  df_prior=df_prior, generate_prior=generate_prior_irrigation_file)


def update_all_post(country_id: str, overwrite=True):
    """
    Update posterior irrigation data for a specific country and all crop products.
    It creates or re-write json files to store posterior data.
    It also writes all distribution stats (mu, sigma) into one csv file.

    Parameters
    ----------
    country_id : str
        Region `@id` from Hestia glossary, e.g. 'GADM-GBR', or 'region-south-america'.
    overwrite: bool
        Whether to overwrite the posterior json files. Defaults to `True`.

    Returns
    -------
    DataFrame
        A DataFrame storing all posterior data.
    """
    df_prior = generate_prior_irrigation_file()
    return update_all_post_data(df_prior, country_id, columns=[IRRIGATION_COLUMN], overwrite=overwrite)


def get_post(country_id: str, product_id: str):
    """
    Return posterior data for a given country and a given product.
    Data is read from the file containing all posterior data.
    Cannot use this function to generate new post files.

    Parameters
    ----------
    country_id: str
        Region `@id` from Hestia glossary, e.g. 'GADM-GBR', or 'region-south-america'.
    product_id: str
        Product term `@id` from Hestia glossary, e.g. 'wheatGrain'.

    Returns
    -------
    tuple(mu, sd)
        Mean values of mu and sd.
    """
    return get_post_data(country_id, product_id, IRRIGATION_COLUMN)

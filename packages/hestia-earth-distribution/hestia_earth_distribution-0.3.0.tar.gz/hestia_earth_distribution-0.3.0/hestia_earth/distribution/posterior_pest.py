from .utils.cycle import PESTICIDE_COLUMN
from .utils.posterior import update_all_post_data, get_post_data, get_post_ensemble_data
from .prior_pest import generate_prior_pest_file


def get_post_ensemble(country_id: str, product_id: str, sub_class: str = PESTICIDE_COLUMN,
                      overwrite=False, df_prior=None):
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
    sub_class: str
        Pesticide SubClass according to Hestia glossary, e.g. 'herbicideUnspecifiedAi', 'insecticideUnspecifiedAi' etc.
        Default PESTICIDE_COLUMN (i.e. 'pesticideUnspecifiedAi' to include all types of pesticides.
    overwrite: bool
        Whether to overwrite existing posterior file or not. Defaults to `False`.
    df_prior: pd.DataFrame
        Optional - if prior file is already loaded, pass it here.

    Returns
    -------
    tuple(mu, sd)
        List of float storing the posterior mu and sd ensembles.
    """
    return get_post_ensemble_data(country_id, product_id, sub_class,
                                  overwrite=overwrite, df_prior=df_prior, generate_prior=generate_prior_pest_file)


def update_all_post(country_id: str, overwrite=True):
    """
    Update crop posterior pesticide data for a specific country and all products.
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
    df_prior = generate_prior_pest_file()
    return update_all_post_data(df_prior, country_id, columns=[PESTICIDE_COLUMN], overwrite=overwrite)


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
    return get_post_data(country_id, product_id, PESTICIDE_COLUMN)

import os
from io import BytesIO
import numpy as np
import math
import pandas as pd

from hestia_earth.distribution.log import logger
from . import SIGMA_SCALER, NO_VALUE, get_country_ids, is_nonempty_str
from .storage import load_from_storage, write_to_storage
from .fao import get_cropland_area, get_mean_std_per_country_per_product

FOLDER = 'prior_files'
WEIGHTED_AVG_HEADER = 'total-mean-cov (area weighted)'  # total (woldwiden or regional) average column in prior files
READ_BY_TYPE = {
    '.pkl': lambda x: pd.read_pickle(x),
    '.csv': lambda x: pd.read_csv(x, na_values=NO_VALUE, index_col=['term.id']),
    None: lambda *args: logger.error('Unsupported file type.')
}
WRITE_BY_TYPE = {
    '.pkl': lambda df, buffer: df.to_pickle(buffer),
    '.csv': lambda df, buffer: df.to_csv(buffer, na_rep=NO_VALUE, index=True, index_label='term.id'),
    None: lambda *args: logger.error('Unsupported file type.')
}


def read_prior_stats(filepath: str):
    logger.info(f'Reading existing file {filepath}')
    filename, file_ext = os.path.splitext(filepath)
    data = load_from_storage(filepath)
    return READ_BY_TYPE.get(file_ext)(BytesIO(data))


def generate_and_save_priors(filepath: str, func):
    """
    Return all prior statistics (means, std and n_years) of FAO data from a CSV file.
    If prior file exisits, prior data will be read in; otherwise, generate priors and store into filepath path.

    Parameters
    ----------
    filepath: str
        Output csv file of FAO prior data, if it doesn't exist yet. Otherwise, read in from it.
    func: function
        Prior function to use.

    Returns
    -------
    pd.DataFrame
        DataFrame storing the prior of the means.
    """
    logger.info(f'Generating prior file to {filepath}.')
    filename, file_ext = os.path.splitext(filepath)
    result = func()
    buffer = BytesIO()
    WRITE_BY_TYPE.get(file_ext)(result, buffer)
    write_to_storage(filepath, buffer.getvalue())
    return result


def get_prior_by_country_by_product(filepath: str, country_id: str, term_id: str):
    """
    Return prior statistics (means, std and n_years) of FAO prior for one product for one country.

    Parameters
    ----------
    filepath: str
        Existing .pkl or .csv file of yield prior data.
    country_id: str
        Region `@id` from Hestia glossary, e.g. 'GADM-GBR', or 'region-south-america'.
    term_id: str
        Crop product term `@id` from Hestia glossary, e.g. 'wheatGrain'.

    Returns
    -------
    list or None
        list of four values: mu, sigma, n_years and -999 (placeholder for sigma_of_mu)), or None if unsuccssful.
    """
    df_stats = read_prior_stats(filepath)

    country_name = ' '.join(country_id.split(NO_VALUE)[1:])
    vals = df_stats.loc[term_id, country_id]

    if isinstance(vals, float):
        logger.error(f'No result of {term_id} from {country_name}')
        return None

    return [float(v) for v in vals.strip('()').split(',')] if is_nonempty_str(vals) else vals


def _weighted_avg_and_cov(values: list, weights: list):
    weights = weights / sum(weights)
    average = np.dot(values, weights)
    variance = np.average((values-average)**2, weights=weights)
    return (round(average, 8), round(math.sqrt(variance)/average, 8))


def _update_stats_with_cov(values: list, cov: float):
    # (mu, scaled_sigma, n, sigma) = val
    return [
        (val[0], max(round(val[0] * cov, 8), val[1]), val[2], val[3]) if val is not None else None for val in values
    ]


def get_countries_priors(term_ids: list, get_fao_func):
    country_ids = get_country_ids()

    df = pd.DataFrame(columns=country_ids, index=term_ids)
    world_means = np.empty_like(df.index)
    area_weights = list(map(get_cropland_area, country_ids))

    for term_index, term_id in enumerate(term_ids):
        logger.info(f'Processing {term_id}...')
        means = []
        weights = []
        output_values = []
        for country_index, country_id in enumerate(country_ids):
            stats = get_mean_std_per_country_per_product(term_id, country_id, get_fao_func)
            if None not in stats and not np.isnan(stats[0]) and not np.isinf(stats[0]):
                output_values.append((stats[0], round(stats[1]*SIGMA_SCALER, 8), stats[2], stats[1]))
                if not np.isnan(area_weights[country_index]):
                    means.append(stats[0])
                    weights.append(area_weights[country_index])
            else:
                output_values.append(None)
        value = _weighted_avg_and_cov(means, weights) if sum(weights) > 0 else np.nan
        world_means[term_index] = value
        df.loc[term_id, :] = _update_stats_with_cov(output_values, value[1]) if not isinstance(value, float) else np.nan

    df[WEIGHTED_AVG_HEADER] = world_means.tolist()

    df.index.rename('term.id', inplace=True)
    logger.info('Processing finished.')
    return df.dropna(axis=1, how='all').dropna(axis=0, how='all')

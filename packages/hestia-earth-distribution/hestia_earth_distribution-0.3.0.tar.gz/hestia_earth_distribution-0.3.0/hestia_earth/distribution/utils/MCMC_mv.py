import numpy as np
import os
import json
from hestia_earth.utils.tools import non_empty_list

from hestia_earth.distribution.likelihood import generate_likl_file
from . import get_product_ids, _progress
from .cycle import YIELD_COLUMN, FERTILISER_COLUMNS
from .storage import file_exists, write_to_storage, load_from_storage


FOLDER = 'mv_files'
MV_COLUMNS = FERTILISER_COLUMNS[:3] + [YIELD_COLUMN]


def _compute_MC_likelihood(candidate: list, kernel, size=100):
    iso = kernel(candidate)
    sample = kernel.resample(size)
    insample = kernel(sample) < iso
    integral = insample.sum() / float(insample.shape[0])
    return integral


def _get_data_bounds(data: list):
    return (data, min(data), max(data)) if len(data) > 0 else ([], None, None)


def _get_df_bounds(df, columns: list,):
    df = df[columns].dropna(axis=0, how='any')
    results = [_get_data_bounds(df[col].to_list()) for col in columns] if len(df) > 0 else (
            [None, None, None]
    )
    return [[r[i] for r in results] for i in range(3)]  # [m, mins, maxs]


def _fit_user_data_mv(candidate, df, columns: list, return_z: bool = False, dim_x: int = 0, dim_y: int = 1):
    m, mins, maxs = _get_df_bounds(df, columns)

    plottable = all([m[i] != [] and mins[i] != maxs[i] for i in range(len(m))])

    values = np.vstack(m)

    try:
        import scipy.stats as st

        def calculate_likl(values):
            kernel = st.gaussian_kde(values)
            return _compute_MC_likelihood(candidate, kernel) if (
                                          plottable and ~np.isnan(candidate).any()) else None

        def calculate_Z(dim_x: int = 0, dim_y: int = 1):
            X, Y = np.mgrid[mins[dim_x]:maxs[dim_x]:100j, mins[dim_y]:maxs[dim_y]:100j]
            positions = np.vstack([X.ravel(), Y.ravel()])

            kernel = st.gaussian_kde(values)
            Z = np.reshape(kernel(positions).T, X.shape)
            return Z / Z.sum()

        likelihood = calculate_likl(values) if len(df) > 2 else None
        return likelihood, calculate_Z(dim_x, dim_y) if return_z and plottable else [
            [mins[dim_x], maxs[dim_x]],
            [[mins[dim_y], maxs[dim_y]]]
        ]
    except ImportError:
        raise ImportError("Run `pip install scipy` to use this functionality")


def calculate_fit_mv(candidate: list, country_id: str, product_id: str,
                     columns=MV_COLUMNS, return_z: bool = False):
    """
    Return the likelihood of a combination of candidate values using bivariate or multivariate distribution.
    The returned probability approximates how reasonable the candidate is by using Monte Carlo integration.
    Any returned probability above 5% should be acceptable.

    Parameters
    ----------
    candidate: list
        List of values to be tested following the order of 'columns', e.g. [250, 8500] by default
        meaning the Nitrogen use is 250 and yield is 8500.
    country_id: str
        Region `@id` from Hestia glossary, e.g. 'GADM-GBR'.
    product_id: str
        Product term `@id` from Hestia glossary, e.g. 'wheatGrain'.
    columns: list
        List of column names in the likelihood csv file, by defualt:
        'Nitrogen (kg N)' and 'Grain yield (kg/ha)'
    return_z: bool
        Whether to calculate Z for plotting. Defaults to `False`.
        Only set to 'True' when plotting 2D distributions.

    Returns
    -------
    likelihood: float
        The probability of how likely the candidate is reasonable, or an
        approximation of what percentage of samples the candidate stands above
    """
    df = generate_likl_file(country_id, product_id)
    return _fit_user_data_mv(candidate, df, columns, return_z=return_z)


def calculate_fit_2d(candidate: list, country_id: str, product_id: str,
                     columns=[FERTILISER_COLUMNS[0], YIELD_COLUMN],
                     return_z: bool = False):
    """
    Return the likelihood of a combination of candidate values using bivariate distribution.
    The returned probability approximates how reasonable the candidate is by using Monte Carlo integration.
    Any returned probability above 5% should be acceptable.

    Parameters
    ----------
    candidate: list
        List of values to be tested following the order of 'columns', e.g. [250, 8500] by default
        meaning the Nitrogen use is 250 and yield is 8500.
    country_id: str
        Region `@id` from Hestia glossary, e.g. 'GADM-GBR'.
    product_id: str
        Product term `@id` from Hestia glossary, e.g. 'wheatGrain'.
    columns: list
        List of column names in the likelihood csv file, by defualt:
        'Nitrogen (kg N)' and 'Grain yield (kg/ha)'
    return_z: bool
        Whether to calculate Z for plotting. Defaults to `False`.

    Returns
    -------
    likelihood: float
        The probability of how likely the candidate is reasonable, or an
        approximation of what percentage of samples the candidate stands above
    """
    return calculate_fit_mv(candidate, country_id, product_id, columns, return_z)


def _mv_filename(country_id: str, product_id: str = ''):
    return f"{FOLDER}/{'_'.join(non_empty_list(['mv_samples', country_id, product_id]))}.json"


def update_mv(country_id: str, product_id: str, sample_size: int = 30):
    """
    Generate static samples on fixed 4 dimensions (MV_COLUMNS) to be used
    for validaiton or visualisation.

    Parameters
    ----------
    country_id: str
        Region `@id` from Hestia glossary, e.g. 'GADM-GBR'.
    product_id: str
        Product term `@id` from Hestia glossary, e.g. 'wheatGrain'.
    sample_size: int
        Size of sample grid on each dimension, default 30 meaning the
        sample space will be of size 30x30x30x30

    Returns
    -------
    output_likl: ndarrady
        The output will be a N-D array of probabilities or likelihood of the
        combinated input values (from MV_COLUMNS)

    """
    df = generate_likl_file(country_id, product_id)

    # generate 'static' samples

    m, mins, maxs = _get_df_bounds(df, MV_COLUMNS)
    values = np.vstack(m)
    try:
        import scipy.stats as st
        kernel = st.gaussian_kde(values)
    except ImportError:
        raise ImportError("Run `pip install scipy` to use this functionality")

    mesh = [np.linspace(mins[i], maxs[i], sample_size) for i in range(len(MV_COLUMNS))]
    sample_grid = np.meshgrid(*mesh)
    samples = np.array(sample_grid).T

    output_likl = np.empty_like(samples[:, :, :, :, 0])

    for index, sample in np.ndenumerate(samples[:, :, :, :, 0]):
        candidate = samples[index]
        output_likl[index] = _compute_MC_likelihood(candidate, kernel)

    # store sample grid and likelihood
    fn = _mv_filename(country_id, product_id)
    data = {
        'multivariate': {'likelihood': output_likl.tolist(), 'grids': samples.tolist()}
    }
    write_to_storage(fn, json.dumps(data).encode('utf-8')) if not file_exists(fn) else None
    return output_likl, samples


def read_mv(filename: str):
    """
    Read static samples on fixed dimensions (MV_COLUMNS) to be used for validaiton or visualisation.

    Parameters
    ----------
    filename: str
        JSON filename where the static samples are stored.

    Returns
    -------
    likelihood: ndarrady
        An N-D array of probabilities or likelihood of the combinated input values (from MV_COLUMNS)
    sample_grid: ndarrady
        An N-D array of sample grids ranging between the min and max of each column in MV_COLUMNS

    """
    data = json.loads(load_from_storage(filename))
    likelihood = data.get('multivariate', {}).get('likelihood', [])
    sample_grid = data.get('multivariate', {}).get('grids', [])
    return likelihood, sample_grid


def get_mv_data(country_id: str, product_id: str, sample_size: int = 30, overwrite=False):
    """
    Get static samples on fixed dimensions (MV_COLUMNS) to be used for validaiton or visualisation.

    Parameters
    ----------
    country_id: str
        Region `@id` from Hestia glossary, e.g. 'GADM-GBR'.
    product_id: str
        Product term `@id` from Hestia glossary, e.g. 'wheatGrain'.
    sample_size: int
        Size of sample grid on each dimension, default 30 meaning the
        sample space will be of size 30x30x30x30

    Returns
    -------
    likelihood: ndarrady
        An N-D array of probabilities or likelihood of the combinated input values (from MV_COLUMNS)
    sample_grid: ndarrady
        An N-D array of sample grids ranging between the min and max of each column in MV_COLUMNS

    """
    filepath = f"{FOLDER}/{_mv_filename(country_id, product_id)}"
    read_existing = file_exists(filepath) and not overwrite
    return read_mv(filepath) if read_existing else update_mv(country_id, product_id, sample_size=sample_size)


def update_all_mv(country_id: str, sample_size: int = 100, overwrite=False):
    """
    Similar to 'update_mv' function, but update the 'mv_sample_' files for all products
    for a given country.
    """
    product_ids = get_product_ids()

    for product_id in _progress(product_ids):
        try:
            # try to load existing file
            filepath = _mv_filename(country_id, product_id)
            if not os.path.exists(filepath) or overwrite:
                update_mv(country_id, product_id, sample_size)
        except KeyError:
            # data on product or country or input does not exist
            print(f'Not enough likelihood data for {country_id} {product_id}')


def find_likelihood_from_static_file(candidate: list, country_id: str, product_id: str):
    """
    Find the nearest position of a candidate on a static sample space, and return its likelihood
    to be used for validaiton or visualisation.
    (scale plays an important role here, ideally 100 but takes too long. Further debug needed).

    Parameters
    ----------
    candidate: list
        The fertiliser input values and yield of a candidate, e.g. [250, 50, 50, 8500]
    country_id: str
        Region `@id` from Hestia glossary, e.g. 'GADM-GBR'.
    product_id: str
        Product term `@id` from Hestia glossary, e.g. 'wheatGrain'.

    Returns
    -------
    likelihood: float
        Probability or likelihood of the combinated input values (from MV_COLUMNS) being reasonable
    loc: list
        Positions of candidate on the grid space of each column in MV_COLUMNS

    """
    def _find_nearest_grid(grid_4d):
        index = [-1] * len(MV_COLUMNS)
        for i, c in enumerate(candidate):
            index[i] = (np.abs(np.asarray(grid_4d[i])-c)).argmin()
        return index

    likl, grids = read_mv(_mv_filename(country_id, product_id))
    grids = np.array(grids)
    grid_n = [n[0] for n in grids[0, 0, :, 0]]
    grid_p = [p[1] for p in grids[0, 0, 0, :]]
    grid_k = [k[2] for k in grids[0, :, 0, 0]]
    grid_yield = [y[3] for y in grids[:, 0, 0, 0]]
    grid_4d = [grid_n, grid_p, grid_k, grid_yield]
    loc = _find_nearest_grid(grid_4d)
    likelihood = np.array(likl)[loc[0], loc[1], loc[2], loc[3]]
    return likelihood, loc

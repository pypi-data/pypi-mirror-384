import numpy as np
from hestia_earth.utils.lookup import download_lookup, get_table_value, column_name, lookup_columns

from . import NO_VALUE, is_nonempty_str

LOOKUP_YIELD = 'region-crop-cropGroupingFaostatProduction-yield.csv'
LOOKUP_FERTUSE = 'region-inorganicFertiliser-fertilisersUsage.csv'
LOOKUP_PESTUSE = 'region-crop-pesticidesUsage.csv'
LOOKUP_AREA = 'region-faostatArea.csv'
LOOKUP_IRRIGATED = 'region-irrigated.csv'
LOOKUP_WATER = 'region-irrigationWaterWithdrawal.csv'


def get_FAO_crop_name(product_id: str):
    """
    Look up the FAO term from Hestia crop term.

    Parameters
    ----------
    product_id: str
        Crop product term `@id` from Hestia glossary, e.g. 'wheatGrain'.

    Returns
    -------
    str
        FAO Crop product term, e.g. 'Wheat'.
    """
    lookup = download_lookup('crop.csv')
    return get_table_value(lookup, 'termid', product_id, column_name('cropGroupingFaostatProduction'))


def fao_str_record_to_array(fao_str: str, output_type=np.float32, n_years: int = 10, scaler: int = 1):
    """
    Converts FAO string records to np.array, and rescale if needed.

    Parameters
    ----------
    fao_str: str
        A string with time-series data read from FAO lookup file.
    output_type: dtype
        Output data type, default `np.float32`.
    n_years: int
        Only fecth the latest N year of data, it will be restricted to any integer between 0 and 70.
    scaler: int
        Scaler for converting FAO units to Hestia units, defaults to `1`.
        Use `10` for converting from hg/ha to kg/ha, when reading FAO yield strings.
        This scaler will only be applied to the data array, not the year array.

    Returns
    -------
    np.array
        FAO Crop product term, e.g. 'Wheat'.
    """
    values = [r.split(":") for r in [r for r in fao_str.split(";")]]

    for val in values[::-1]:
        if NO_VALUE == val[1]:
            values.pop(values.index(val))

    n_years = min(max(0, n_years), 70)

    vals = np.array(values).transpose().astype(output_type)

    years_sorted = vals[0][np.argsort(vals[0])].astype(np.int32)
    vals_sorted = vals[1][np.argsort(vals[0])] / scaler

    gap = int(max(vals_sorted) - min(vals_sorted) + 1)
    return np.vstack([years_sorted[-min(n_years, gap):], vals_sorted[-min(n_years, gap):]])


def get_fao_yield(country_id: str, product_id: str, n_years: int = 10):
    """
    Look up the FAO yield per country per product from the glossary.

    Parameters
    ----------
    country_id: str
        Region `@id` from Hestia glossary, e.g. 'GADM-GBR', or 'region-south-america'.
    product_id: str
        Crop product term `@id` from Hestia glossary, e.g. 'wheatGrain'.
    n_years: int
        Only fecth the latest N year of data, it will be restricted to any integer between 0 and 70.

    Returns
    -------
    nunpy.array or None
        A 2-D array with years and yield values from FAO yield record, if successful.
    """
    lookup = download_lookup(LOOKUP_YIELD)
    product_name = get_FAO_crop_name(product_id)
    yield_str = get_table_value(lookup, 'termid', country_id, column_name(product_name))
    return fao_str_record_to_array(yield_str, n_years=n_years, scaler=10) if is_nonempty_str(yield_str) else None


def get_fao_fertuse(country_id: str, fert_id: str, n_years: int = 10):
    """
    Look up the FAO fertiliser useage per country from the glossary.

    Parameters
    ----------
    country_id: str
        Region `@id` from Hestia glossary, e.g. 'GADM-GBR', or 'region-south-america'.
    fert_id: str
        Fertiliser term `@id` from Hestia glossary, restricted to the three options availible from FAO:
        'inorganicNitrogenFertiliserUnspecifiedKgN', 'inorganicPhosphorusFertiliserUnspecifiedKgP2O5',
        or 'inorganicPotassiumFertiliserUnspecifiedKgK2O'.
    n_years: int
        Only fecth the latest N year of data, it will be restricted to any integer between 0 and 70.

    Returns
    -------
    nunpy.array or None
        A 2-D array with years and yield values from FAO yield record, if successful.
    """
    lookup = download_lookup(LOOKUP_FERTUSE)
    fert_str = get_table_value(lookup, 'termid', country_id, column_name(fert_id))
    return fao_str_record_to_array(fert_str, np.single, n_years, 1) if is_nonempty_str(fert_str) else None


def get_fao_pestuse(country_id: str, pest_col_name: str, n_years: int = 10):
    """
    Look up the FAO pesticide useage per country from the glossary.

    Parameters
    ----------
    country_id: str
        Region `@id` from Hestia glossary, e.g. 'GADM-GBR', or 'region-south-america'.
    pest_col_name: str
        Column name of the pesticide use data.
    n_years: int
        Only fecth the latest N year of data, it will be restricted to any integer between 0 and 70.

    Returns
    -------
    nunpy.array or None
        A 2-D array with years and yield values from FAO yield record, if successful.
    """
    lookup = download_lookup(LOOKUP_PESTUSE)
    col_name = column_name(pest_col_name).replace('(', '').replace(')', '')
    output_str = get_table_value(lookup, 'termid', country_id, col_name)
    return fao_str_record_to_array(output_str, np.single, n_years, 1) if is_nonempty_str(output_str) else None


def _pad_fao_array(series1: np.array, series2: np.array):
    # inputs should be 2D arrays following the FAO returned value format, i.e. [years, values]
    if (series1 is not None) and (series2 is not None):

        series1 = np.array(series1)
        series2 = np.array(series2)

        if len(series1[0]) < len(series2[0]):
            output_1d = np.pad(series1[1], (len(series2[0])-len(series1[0]), 0), mode='edge')
            return np.vstack([series2[0], output_1d, series2[1]])
        elif len(series1[0]) > len(series2[0]):
            output_1d = np.pad(series2[1], (len(series1[0])-len(series2[0]), 0), mode='edge')
            return np.vstack([series1[0], series1[1], output_1d])
        else:
            return np.vstack([series1[0], series1[1], series2[1]])  # years, value1s, value2s
    else:
        return [np.nan, np.nan, np.nan]


def get_fao_irrigation(country_id: str, n_years: int = 10):
    def _get_irrigation_rates(irrigation_column: str, landarea_column: str):
        water_str = get_table_value(lookup_water, 'termid', country_id, column_name(irrigation_column))
        water = fao_str_record_to_array(water_str, n_years=n_years, scaler=1e-9) if is_nonempty_str(water_str) else None

        land_str = get_table_value(lookup_irrigated_land, 'termid', country_id, column_name(landarea_column))
        land = fao_str_record_to_array(land_str, n_years=n_years, scaler=0.001) if is_nonempty_str(land_str) else None
        year_water_land = _pad_fao_array(water, land)

        return year_water_land[0], year_water_land[1] / year_water_land[2]

    lookup_irrigated_land = download_lookup(LOOKUP_IRRIGATED)
    land_columns = [v for v in lookup_columns(lookup_irrigated_land) if v != 'termid']

    lookup_water = download_lookup(LOOKUP_WATER)
    irri_columns = [v for v in lookup_columns(lookup_water) if v != 'termid']

    rates = [_get_irrigation_rates(ir, land) for ir in irri_columns for land in land_columns]

    return next((r for r in rates if isinstance(r[0], np.ndarray)), [])


def get_mean_std_per_country_per_product(term_id: str, country_id: str, get_fao_func):
    """
    Get the means and standard deviations of FAO yield for a specific country/region for a specific product.

    Parameters
    ----------
    term_id: str
        Ferteliser term `@id` or crop product term `@id` from Hestia glossary, e.g. 'ammoniumNitrateKgN', 'wheatGrain'.
    country_id: str
        Region `@id` from Hestia glossary, e.g. 'GADM-GBR', or 'region-south-america'.
    get_fao_func: Function
        Function being used to get FAO time-series values.

    Returns
    -------
    list or None
        A list of [mu, sigma, n_years] values, if successful. Otherwise, return `None`.
    """
    yields10yr = get_fao_func(country_id, term_id, n_years=10)
    value = yields10yr[1] if (yields10yr is not None) and len(yields10yr) > 0 else None
    return (round(value.mean(), 8), round(value.std(), 8), len(value)) if value is not None else (None, None, None)


def get_cropland_area(country_id: str):
    lookup = download_lookup(LOOKUP_AREA)
    area_str = get_table_value(lookup, 'termid', country_id, column_name('Cropland'))
    return fao_str_record_to_array(area_str).mean() if area_str is not None else np.nan

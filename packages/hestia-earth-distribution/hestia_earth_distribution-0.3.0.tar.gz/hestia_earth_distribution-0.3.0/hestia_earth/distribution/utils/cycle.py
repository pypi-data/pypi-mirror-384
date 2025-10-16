from functools import reduce
import numpy as np
from hestia_earth.utils.api import search, download_hestia
from hestia_earth.utils.tools import non_empty_list, list_average, list_sum, flatten
from hestia_earth.utils.model import find_primary_product, filter_list_term_type
from hestia_earth.schema import CycleFunctionalUnit, TermTermType

from .property import get_property_by_id

_FERT_GROUPS = {
    'N': 'inorganicNitrogenFertiliserUnspecifiedKgN',
    'P2O5': 'inorganicPhosphorusFertiliserUnspecifiedKgP2O5',
    'K2O': 'inorganicPotassiumFertiliserUnspecifiedKgK2O'
}

INDEX_COLUMN = 'cycle.id'
YIELD_COLUMN = 'Grain yield (kg/ha)'
FERTILISER_COLUMNS = [
    'Nitrogen (kg N)',
    'Phosphorus (kg P2O5)',
    'Potassium (kg K2O)',
    'Magnesium (kg Mg)'
    # 'Sulphur (kg S)'
]
PESTICIDE_COLUMN = 'pesticideUnspecifiedAi'  # 'Total pesticides (kg active ingredient)'
IRRIGATION_COLUMN = 'waterSourceUnspecified'  # 'Total water inputs (m3 / ha)'


def _get_fert_group_name(fert_id: str): return fert_id.split('Kg')[-1]


def get_fert_group_id(term_id: str):
    """
    Look up the fertiliser group (N, P2O5, K2O) of a Hestia fertliser term.

    Parameters
    ----------
    term_id: str
        Inorganic or organic fertiliser term `@id` from Hestia glossary, e.g. 'ammoniumNitrateKgN'.

    Returns
    -------
    str
        Fertiliser group '@id', e.g. 'inorganicNitrogenFertiliserUnspecifiedKgN'.
    """
    return _FERT_GROUPS.get(_get_fert_group_name(term_id))


def get_fert_ids():
    """
    Get a list of '@id' of the ferttiliser inputs that can be used to get data.
    """
    return list(_FERT_GROUPS.values())


def get_input_ids():
    """
    Get a list of '@id' of the Input that can be used to get data.
    """
    return get_fert_ids() + [PESTICIDE_COLUMN, IRRIGATION_COLUMN]


def find_cycles(country_id: str, product_id: str, limit: int, recalculated: bool = False):
    country_name = download_hestia(country_id).get('name')
    product_name = download_hestia(product_id).get('name')

    cycles = search({
        'bool': {
            'must': [
                {
                    'match': {'@type': 'Cycle'}
                },
                {
                    'nested': {
                        'path': 'products',
                        'query': {
                            'bool': {
                                'must': [
                                    {'match': {'products.term.name.keyword': product_name}},
                                    {'match': {'products.primary': 'true'}}
                                ]
                            }
                        }
                    }
                },
                {
                    'match': {
                        'site.country.name.keyword': country_name
                    }
                },
                {
                    'match': {
                        'functionalUnit': CycleFunctionalUnit._1_HA.value
                    }
                }
            ],
            'must_not': [{'match': {'aggregated': True}}]
        }
    }, limit=limit)
    cycles = [download_hestia(c['@id'], 'Cycle', 'recalculated' if recalculated else None) for c in cycles]
    return non_empty_list(cycles)


_CONVERT_FROM_KG_MASS = {
    'kg N': 'nitrogenContent',
    'kg P2O5': 'phosphateContentAsP2O5',
    'kg K2O': 'potassiumContentAsK2O'
}

_TERM_IDS = [
    'organicNitrogenFertiliserUnspecifiedKgN',
    'organicPhosphorusFertiliserUnspecifiedKgP2O5',
    'organicPotassiumFertiliserUnspecifiedKgK2O'
]


_FERTILISER_TERM_TYPES = [
    TermTermType.ORGANICFERTILISER,
    TermTermType.INORGANICFERTILISER
]

_TYPE_TO_COLUMN = {
    TermTermType.PESTICIDEAI.value: PESTICIDE_COLUMN,
    TermTermType.PESTICIDEBRANDNAME.value: PESTICIDE_COLUMN,
    TermTermType.WATER.value: IRRIGATION_COLUMN
}


def _nansum(val1: float, val2: float):
    return np.nan if all([np.isnan(val1), np.isnan(val2)]) else np.nansum([val1, val2])


def _convert_to_nutrient(input_node: dict, nutrient_unit: str = 'kg N'):
    nutrient = _CONVERT_FROM_KG_MASS.get(nutrient_unit, '')
    prop = get_property_by_id(input_node, nutrient)
    nutrient_content = prop.get('value')
    input_value = list_sum(input_node.get('value', []), None)
    return np.nan if any([nutrient_content is None, input_value is None]) else input_value * nutrient_content / 100


def _pct_activate_ingredients(brand_name: str):
    name = download_hestia(brand_name, 'Term')
    return list_sum([i.get('value') for i in name.get('defaultProperties', [])
                     if i.get('term', {}).get('@id') == 'activeIngredient'], np.nan)


def _pesticideBrandNames_per_cycle(cycle: dict):
    return [
            i for i in cycle.get('inputs', []) if all([
                i.get('term', {}).get('termType') == TermTermType.PESTICIDEBRANDNAME.value,
                list_sum(i.get('value', []), np.nan) >= 0  # default nan, instead of zero 0
            ])
    ]


def _pesticideBrandName_IDs_per_cycle(cycle: dict):
    brandnames = _pesticideBrandNames_per_cycle(cycle)
    return [i.get('term', {}).get('@id') for i in brandnames]


def get_totalAI_of_brandnames(cycles: list):
    pestBrandNames = list(set(flatten([_pesticideBrandName_IDs_per_cycle(c) for c in cycles])))
    pct_ai = [_pct_activate_ingredients(brand) for brand in pestBrandNames]
    return {pestBrandNames[i]: pct_ai[i] for i in range(len(pestBrandNames))}


def _get_fert_group(input: dict):
    term_units = input.get('term', {}).get('units')
    return next((group for group in FERTILISER_COLUMNS if term_units in group), None)


def get_input_group(input: dict):
    term_type = input.get('term', {}).get('termType')
    return _get_fert_group(input) if 'Fertiliser' in term_type else _TYPE_TO_COLUMN.get(term_type)


def _get_fert_composition(input: dict):
    def _get_term_dict(term_id: str):
        term = download_hestia(term_id)
        return {'term': term, 'value': [_convert_to_nutrient(input, term.get('units'))]}

    return [_get_term_dict(t) for t in _TERM_IDS] if 'KgMass' in input.get('term', {}).get('@id') else [input]


def _group_fert_inputs(inputs: list, convert_nan_to_zero: bool = False):
    # decomposit compost fertilisers, by replacing original input with decompisit inputs
    fert_inputs = reduce(lambda p, c: p + _get_fert_composition(c), inputs, [])

    def exec(group: dict, group_key: str):
        sum_inputs = list_sum(flatten([
            input.get('value', []) for input in fert_inputs if get_input_group(input) == group_key
        ]), np.nan)
        sum_inputs = 0 if np.isnan(sum_inputs) and convert_nan_to_zero else sum_inputs
        return {**group, group_key: sum_inputs}
    return exec


def _sum_input_values(inputs: list, percentages: list = []):
    vals = flatten([input.get('value', []) for input in inputs])
    return list_sum(vals, np.nan) if not percentages else np.dot(vals, percentages)


def sum_fertilisers(cycle: dict):
    fertilisers = [
        i for i in filter_list_term_type(cycle.get('inputs', []), _FERTILISER_TERM_TYPES) if all([
            list_sum(i.get('value', []), 0) > 0
        ])
    ]
    convert_nan_to_zero = cycle.get('completeness', {}).get('fertiliser', False)
    values = reduce(_group_fert_inputs(fertilisers, convert_nan_to_zero), FERTILISER_COLUMNS, {})
    return values


def sum_pesticides(cycle: dict, brandname_to_ai: dict = {}):
    pestAIs = [
        i for i in filter_list_term_type(cycle.get('inputs', []), TermTermType.PESTICIDEAI) if all([
            list_sum(i.get('value', []), np.nan) >= 0
        ])
    ]
    pestBrandNames = _pesticideBrandNames_per_cycle(cycle)
    brandname_to_ai = brandname_to_ai or get_totalAI_of_brandnames([cycle])
    pestAI_percentages = [brandname_to_ai.get(brand_name.get('term', {}).get('@id')) for brand_name in pestBrandNames]
    value = _nansum(_sum_input_values(pestAIs), _sum_input_values(pestBrandNames, pestAI_percentages))
    return 0 if np.isnan(value) and cycle.get('completeness', {}).get('pesticideVeterinaryDrug', False) else value


def sum_water(cycle: dict):
    waters = [
        i for i in cycle.get('inputs', []) if all([
            i.get('term', {}).get('termType') == TermTermType.WATER.value,
            list_sum(i.get('value', []), 0) > 0
        ])
    ]
    value = _sum_input_values(waters)
    return 0 if np.isnan(value) and cycle.get('completeness', {}).get('water', False) else value


def sum_yield(cycle: dict):
    product = find_primary_product(cycle) or {}
    products = [
        p for p in cycle.get('products', []) if all([
            p.get('term', {}).get('@id') == product.get('term', {}).get('@id'),
            list_average(p.get('value', []), 0) > 0
        ])
    ]
    value = list_sum(flatten([list_average(p.get('value', [])) for p in products]))
    return np.nan if np.isnan(value) else value


def group_cycle_inputs(cycle: dict, brandname_to_ai: dict = {}):
    fertilisers_values = sum_fertilisers(cycle)
    pesticides_value = sum_pesticides(cycle, brandname_to_ai)
    water_values = sum_water(cycle)
    yield_value = sum_yield(cycle)
    completeness = cycle.get('completeness') or {}

    return {
        INDEX_COLUMN: cycle.get('@id'),
        YIELD_COLUMN: yield_value,
        'completeness.product': completeness.get('product', False),
        **fertilisers_values,
        'completeness.fertiliser': completeness.get('fertiliser', False),
        PESTICIDE_COLUMN: pesticides_value,
        'completeness.pesticideVeterinaryDrug': completeness.get('pesticideVeterinaryDrug', False),
        IRRIGATION_COLUMN: water_values,
        'completeness.water': completeness.get('water', False)
    }

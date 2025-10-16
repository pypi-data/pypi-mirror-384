from hestia_earth.utils.api import download_hestia
from hestia_earth.utils.model import find_term_match


def get_default_property_by_id(blank_node: dict, term_id: str):
    term = download_hestia(blank_node.get('term', {}).get('@id', ''))
    defaultProperties = term.get('defaultProperties', [])
    return find_term_match(defaultProperties, term_id, {})


def get_property_by_id(blank_node: dict, term_id: str):
    prop = find_term_match(blank_node.get('properties', []), term_id, {})
    return prop if prop != {} else get_default_property_by_id(blank_node, term_id)

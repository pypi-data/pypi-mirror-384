import pandas as pd

from .utils.cycle import (
    INDEX_COLUMN,
    group_cycle_inputs,
    get_totalAI_of_brandnames
)


def cycle_yield_distribution(cycles: list):
    dict_brandname_to_ai = get_totalAI_of_brandnames(cycles)

    values = list(map(lambda c: group_cycle_inputs(c, dict_brandname_to_ai), cycles))
    # in case there are no values, we should still set the columns
    columns = group_cycle_inputs({}).keys()
    return pd.DataFrame.from_records(values, index=[INDEX_COLUMN], columns=columns)

from enum import Enum
from typing import Callable, List

from apheris_preprocessing._internal.remote_functions import (
    DATETIME_LIKE_PROPERTIES,
    _read_csv,
    _read_file_from_zip,
    _read_parquet,
    add_number,
    add_table,
    addition,
    astype,
    charlson_comorbidities,
    charlson_comorbidity_score,
    compare_to_table,
    compare_to_value,
    concat,
    count,
    cumsum,
    datetime_like_properties,
    diff,
    div,
    divide,
    divide_by_constant,
    drop_column,
    drop_duplicates,
    dropna,
    fillna,
    fillna_table,
    first,
    getitem,
    getitem_at_mask_table,
    groupby,
    inv,
    invert,
    isin,
    isna,
    last,
    loc_getter,
    loc_setter,
    logical_conjunction,
    mean,
    merge,
    mult,
    multiply,
    multiply_by_constant,
    neg,
    negation,
    prepare_sankey_plot,
    rank,
    rename,
    reset_index,
    rolling,
    rolling_mean,
    rolling_sum,
    sample,
    setitem,
    shift,
    size,
    sort_values,
    str_contains,
    str_len,
    subtraction,
    sum,
    to_datetime,
    transform_columns,
)
from .str_object_converter import (
    ALL_SUPPORTED_TYPES,
    ARITHMETIC_TYPES,
)
from .formats import InputFormat


class NodeCommands(Enum):
    """Mapping between node commands and remote functions"""

    read_csv = {
        "func": _read_csv,
    }
    read_zip = {
        "func": _read_file_from_zip,
    }
    read_parquet = {
        "func": _read_parquet,
    }
    setitem = {
        "func": setitem,
    }
    getitem = {
        "func": getitem,
    }
    getitem_at_index_table = {
        "func": getitem_at_mask_table,
    }
    addition = {
        "func": addition,
    }
    negation = {
        "func": negation,
    }
    subtraction = {
        "func": subtraction,
    }
    compare_to_table = {
        "func": compare_to_table,
    }
    compare_to_value = {
        "func": compare_to_value,
    }
    to_datetime = {
        "func": to_datetime,
    }
    fillna_table = {
        "func": fillna_table,
    }
    fillna = {
        "func": fillna,
    }
    dropna = {
        "func": dropna,
    }
    isna = {
        "func": isna,
    }
    astype = {
        "func": astype,
    }
    merge = {
        "func": merge,
    }
    concat = {
        "func": concat,
    }
    rename = {
        "func": rename,
    }
    drop_column = {
        "func": drop_column,
    }
    add_table = {
        "func": add_table,
    }
    add_number = {
        "func": add_number,
    }
    divide = {
        "func": divide,
    }
    divide_by_constant = {
        "func": divide_by_constant,
    }
    multiply = {
        "func": multiply,
    }
    multiply_by_constant = {
        "func": multiply_by_constant,
    }
    neg = {
        "func": neg,
    }
    invert = {
        "func": invert,
    }
    logical_conjunction_table = {
        "func": logical_conjunction,
    }
    logical_conjunction_number = {
        "func": logical_conjunction,
    }
    sample = {
        "func": sample,
    }
    str_contains = {
        "func": str_contains,
    }
    str_len = {
        "func": str_len,
    }
    sort_values = {
        "func": sort_values,
    }
    isin = {
        "func": isin,
    }
    datetime_like_properties = {
        "func": datetime_like_properties,
        "datetime_like_property": DATETIME_LIKE_PROPERTIES,
    }
    drop_duplicates = {
        "func": drop_duplicates,
    }
    reset_index = {
        "func": reset_index,
    }
    loc_setter = {
        "func": loc_setter,
    }
    loc_getter = {
        "func": loc_getter,
    }
    groupby = {
        "func": groupby,
    }
    first = {
        "func": first,
    }
    last = {
        "func": last,
    }
    size = {
        "func": size,
    }
    mean = {
        "func": mean,
    }
    count = {
        "func": count,
    }
    cumsum = {
        "func": cumsum,
    }
    sum = {
        "func": sum,
    }
    diff = {
        "func": diff,
    }
    shift = {
        "func": shift,
    }
    rank = {
        "func": rank,
    }
    mult = {"func": mult}
    div = {"func": div}
    inv = {"func": inv}
    prepare_sankey_plot = {"func": prepare_sankey_plot}
    rolling = {
        "func": rolling,
    }
    rolling_sum = {"func": rolling_sum}
    rolling_mean = {"func": rolling_mean}
    charlson_comorbidities = {
        "func": charlson_comorbidities,
    }
    charlson_comorbidity_score = {
        "func": charlson_comorbidity_score,
    }

    transform_columns = {
        "func": transform_columns,
    }

    @classmethod
    def get_read_data_function(
        cls,
        read_format: InputFormat,
    ) -> "NodeCommands":
        return {
            InputFormat.CSV: NodeCommands.read_csv,
            InputFormat.ZIP: NodeCommands.read_zip,
            InputFormat.PARQUET: NodeCommands.read_parquet,
        }.get(read_format, NodeCommands.read_csv)

    @property
    def remote_function(self) -> Callable:
        return self.value.get("func")

    def get_supported_values_for_remote_function_attr(
        self,
        remote_function_attr: str,
    ) -> set:
        return set(self.value.get(remote_function_attr, set()))

    @classmethod
    def get_all_supported_remote_functions(cls) -> List[Callable]:
        return [e.remote_function for e in cls]

    @staticmethod
    def get_arithmetic_types() -> tuple:
        return ARITHMETIC_TYPES

    @staticmethod
    def get_all_supported_types() -> tuple:
        return ALL_SUPPORTED_TYPES

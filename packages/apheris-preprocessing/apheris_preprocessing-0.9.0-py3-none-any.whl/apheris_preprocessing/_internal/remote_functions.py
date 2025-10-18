import copy
import zipfile
from datetime import timedelta
from typing import Any, Callable, Dict, Iterable, List, Literal, Optional, Tuple, Union

import numpy as np
import pandas as pd
import pandas.core.groupby.generic
from pandas.core.dtypes.common import is_datetime64_dtype, is_string_dtype
from pandas.core.groupby.generic import DataFrameGroupBy
from pandas.core.indexes.accessors import DatetimeProperties, TimedeltaProperties
from pandas.core.window.rolling import Rolling

from apheris_preprocessing._internal.utils.exceptions_handling import (
    PrivacyException,
    TransformationsException,
    hide_traceback_decorator,
)

from apheris_preprocessing._internal.utils.str_object_converter import (
    ALL_SUPPORTED_TYPES,
    ALL_SUPPORTED_TYPES_WITH_PANDAS_DF,
    ARITHMETIC_TYPES,
    PANDAS_DF_TYPES,
)
from apheris_preprocessing._internal.utils.formats import get_default_comorbidity_mapping

DATETIME_LIKE_PROPERTIES_CLASSES = (  # for now PeriodProperties are not supported
    DatetimeProperties,
    TimedeltaProperties,
)
DATETIME_LIKE_PROPERTIES = {
    property_name
    for properties_class in DATETIME_LIKE_PROPERTIES_CLASSES
    for property_name, property_class in vars(properties_class).items()
    if not property_name.startswith("_")
}


def _validate_object_type(obj: Any, obj_type: Any) -> None:
    """
    Raise a TypeError if `obj` is not of type `obj_type`.
    """
    if not isinstance(obj, obj_type):
        raise TypeError(f"Expected {str(obj_type)}, got {type(obj)}")


def _check_data_read_correctly(data):
    if len(data.columns) == 1:
        raise PrivacyException(
            "The pandas dataframe only has one column, "
            "looks like the data of several columns is read into one column. "
            "Please double-check the data format to read it correctly."
        )


def _read_csv(fpath):
    try:
        res = pd.read_csv(fpath)
    except ValueError as e:
        if "Multiple files found in ZIP file." in e.args[0]:
            with zipfile.ZipFile(fpath, mode="r") as archive:
                raise RuntimeError(
                    "You are trying to initialize a FederatedDataFrame from a zip "
                    "archive but you have not specified the name of a particular "
                    "csv-file. The zip archive contains following files: "
                    f"{archive.namelist()}. "
                    "You can try to init a FederatedDataFrame the following way: "
                    "`fdf = FederatedDataFrame('my-dataset-id', "
                    "filename_in_zip='file1.csv')`"
                )
        else:
            raise e

    _check_data_read_correctly(res)
    return res


def _read_file_from_zip(fpath, filename):
    with zipfile.ZipFile(fpath) as z:
        filenames = [x.filename for x in z.filelist if not x.is_dir()]
        if filename not in filenames:
            raise FileNotFoundError(
                f"The file `{filename}` does not exist in the zip-archive. Instead, "
                f"the following files are available: {filenames}"
            )
        with z.open(filename) as f:
            df = pd.read_csv(f)
            _check_data_read_correctly(df)
            return df


def _read_parquet(fpath):
    res = pd.read_parquet(fpath)
    _check_data_read_correctly(res)
    return res


def getitem(column: str, df: pd.DataFrame):
    _validate_object_type(df, pd.DataFrame)

    @hide_traceback_decorator
    def getitem_dataframes():
        df_new = df.copy(deep=True)
        df_subset = df_new[[column]]
        return df_subset

    return getitem_dataframes()


def getitem_at_mask_table(table: pd.DataFrame, mask: pd.DataFrame) -> pd.DataFrame:
    _validate_object_type(table, pd.DataFrame)
    for df, name in zip([table, mask], ["table", "index"]):
        if not isinstance(df, pd.DataFrame):
            raise TypeError(
                f"`{name}` is of type {type(df)}. We expected " f"pandas.DataFrame."
            )
    if not len(mask.columns) == 1:
        raise ValueError(
            f"We expected index to only have 1 column but it has {len(mask.columns)} "
            "columns."
        )

    index_type = mask[mask.columns[0]].dtype
    if index_type != bool:
        raise TypeError(
            "We expected the index column to have type bool but it has "
            f"type {index_type}."
        )

    @hide_traceback_decorator
    def getitem_at_mask_table_dataframes():
        return copy.deepcopy(table[mask[mask.columns[0]]])

    new_table = getitem_at_mask_table_dataframes()
    if not isinstance(new_table, pd.DataFrame):
        raise TypeError(
            "Expected getitem_at_mask_table to return a pandas.DataFrame but got "
            f"{type(new_table)}."
        )
    return new_table


def setitem(
    table: pd.DataFrame, item_to_add: Union[pd.DataFrame, int, float, str], index: str
):
    _validate_object_type(table, pd.DataFrame)
    new_table = copy.deepcopy(table)
    item = item_to_add
    # if item_to_add is a constant value we can just use it as it is. Only if it is a
    # single column DataFrame we convert it to a Series.
    if isinstance(item_to_add, pd.DataFrame):
        cols = item_to_add.columns
        item = item_to_add[cols[0]]
        if len(cols) != 1:
            raise ValueError(
                f"We expect 'column_to_add' to have only 1 column. "
                f"It has {len(cols)} columns."
            )

    @hide_traceback_decorator
    def setitem_dataframes():
        new_table[index] = item
        return new_table

    return setitem_dataframes()


def negation(table: pd.DataFrame, column_to_negate, result_column):
    # if table contains datatypes, that can not be converted to numerics negation is not
    # meaningful as well. ValueError is raised by pandas function.
    _validate_object_type(table, pd.DataFrame)
    new_table = copy.deepcopy(table)

    @hide_traceback_decorator
    def negation_dataframes():
        new_table[result_column] = -table[column_to_negate]
        return new_table

    return negation_dataframes()


def inv(table: pd.DataFrame, column_to_invert, result_column):
    # if table contains datatypes, that can not be converted to numerics negation is not
    # meaningful as well. ValueError is raised by pandas function.
    _validate_object_type(table, pd.DataFrame)
    new_table = copy.deepcopy(table)

    @hide_traceback_decorator
    def inv_dataframes():
        new_table[result_column] = ~table[column_to_invert]
        return new_table

    return inv_dataframes()


def addition(this: pd.DataFrame, summand_column1, summand2, result_column):
    _validate_object_type(this, pd.DataFrame)
    if summand_column1 not in this.columns:
        raise KeyError(
            "We expect summand_column1 to be an existing column "
            f"in the table, but {summand_column1} is not part of {this.columns}."
        )
    if not (summand2 in this.columns or isinstance(summand2, ARITHMETIC_TYPES)):
        raise KeyError(
            "We expect summand2 to be an existing column "
            "in the table or a constant float or integer, "
            f"but {summand2} is not part of {this.columns}."
        )

    new_table = copy.deepcopy(this)

    @hide_traceback_decorator
    def add_dataframes():
        if summand2 in this.columns:
            new_table[result_column] = new_table[summand_column1] + new_table[summand2]
        else:
            new_table[result_column] = new_table[summand_column1] + summand2
        return new_table

    return add_dataframes()


def subtraction(this: pd.DataFrame, left, right, result):
    _validate_object_type(this, pd.DataFrame)
    new_table = copy.deepcopy(this)
    if left in this.columns and right in this.columns:
        df1 = new_table[left]
        df2 = new_table[right]
    elif left in this.columns and isinstance(right, ARITHMETIC_TYPES):
        df1 = new_table[left]
        df2 = right
    elif right in this.columns and isinstance(left, ARITHMETIC_TYPES):
        df1 = left
        df2 = new_table[right]
    else:
        raise AssertionError(
            "We can only subtract two columns from each "
            "other, or one column and one constant, "
            "or one constant and one column, "
            f"but not {left} and {right}, "
            f"columns available: {this.columns}"
        )

    @hide_traceback_decorator
    def subtract_dataframes(df1, df2):
        new_table[result] = df1 - df2
        return new_table

    return subtract_dataframes(df1, df2)


def mult(this: pd.DataFrame, left, right, result):
    _validate_object_type(this, pd.DataFrame)
    if left not in this.columns:
        raise KeyError(
            "We expect left to be an existing column "
            f"in the table, but {left} is not part of {this.columns}."
        )
    if not (right in this.columns or isinstance(right, ARITHMETIC_TYPES)):
        raise KeyError(
            "We expect right to be an existing column "
            "in the table or a constant float or integer, "
            f"but {right} is not part of {this.columns}."
        )

    new_table = copy.deepcopy(this)

    @hide_traceback_decorator
    def mult_dataframes():
        if right in this.columns:
            new_table[result] = new_table[left] * new_table[right]
        else:
            new_table[result] = new_table[left] * right
        return new_table

    return mult_dataframes()


def div(this: pd.DataFrame, left, right, result):
    _validate_object_type(this, pd.DataFrame)
    new_table = copy.deepcopy(this)

    if left in this.columns and right in this.columns:
        df1 = new_table[left]
        df2 = new_table[right]
    elif left in this.columns and isinstance(right, ARITHMETIC_TYPES):
        df1 = new_table[left]
        df2 = right
    elif right in this.columns and isinstance(left, ARITHMETIC_TYPES):
        df1 = left
        df2 = new_table[right]
    else:
        raise AssertionError(
            f"We can only divide two columns by each "
            f"other, or one column and one constant, "
            f"or one constant and one column, "
            f"but not {left} and {right}"
        )

    @hide_traceback_decorator
    def div_dataframes(df1, df2):
        new_table[result] = df1 / df2
        return new_table

    return div_dataframes(df1, df2)


def compare_to_table(left: pd.DataFrame, right: pd.DataFrame, comparison_type: str):
    _validate_object_type(left, pd.DataFrame)
    _validate_object_type(right, pd.DataFrame)
    cols1 = left.columns
    if len(cols1) != 1:
        raise ValueError(
            f"We expect 'left' to have only 1 column. " f"It has {len(cols1)} columns."
        )
    cols2 = right.columns
    if len(cols2) != 1:
        raise ValueError(
            f"We expect 'right' to have only 1 column. " f"It has {len(cols2)} columns."
        )
    if comparison_type not in [">", "<", ">=", "<=", "!=", "=="]:
        raise ValueError(
            'We only support following compare_types: ">", "<", ">=", "<=", "!=", '
            f'"==". Following compare_type was given: {comparison_type}'
        )

    @hide_traceback_decorator
    def compare_dataframes():
        left_series = left[cols1[0]]
        right_series = right[cols2[0]]
        if comparison_type == ">":
            result_series = left_series > right_series
        elif comparison_type == "<":
            result_series = left_series < right_series
        elif comparison_type == ">=":
            result_series = left_series >= right_series
        elif comparison_type == "<=":
            result_series = left_series <= right_series
        elif comparison_type == "!=":
            result_series = left_series != right_series
        elif comparison_type == "==":
            result_series = left_series == right_series
        df = pd.DataFrame()
        df[cols1[0]] = result_series
        return df

    return compare_dataframes()


def compare_to_value(
    left: pd.DataFrame,
    right: Union[ALL_SUPPORTED_TYPES],
    comparison_type: str,
) -> pd.DataFrame:
    _validate_object_type(left, pd.DataFrame)
    if comparison_type not in [">", "<", ">=", "<=", "!=", "=="]:
        raise ValueError(
            'We only support following compare_types: ">", "<", ">=", "<=", "!=", '
            f'"==". Following compare_type was given: {comparison_type}'
        )
    cols1 = left.columns
    if len(cols1) != 1:
        raise ValueError(
            f"We expect 'left' to have only 1 column. " f"It has {len(cols1)} columns."
        )

    @hide_traceback_decorator
    def compare_dataframes():
        left_series = left[cols1[0]]
        if comparison_type == ">":
            result_series = left_series > right
        elif comparison_type == "<":
            result_series = left_series < right
        elif comparison_type == ">=":
            result_series = left_series >= right
        elif comparison_type == "<=":
            result_series = left_series <= right
        elif comparison_type == "!=":
            result_series = left_series != right
        elif comparison_type == "==":
            result_series = left_series == right
        df = pd.DataFrame()
        df[cols1[0]] = result_series
        return df

    return compare_dataframes()


def to_datetime(table: pd.DataFrame, column=None, result=None, **kwargs):
    _validate_object_type(table, pd.DataFrame)
    if column:
        if column not in table.columns:
            raise ValueError(
                "We expected column to be an existing column in {table.columns}."
            )
    else:
        column = get_single_column_name(table, "to_datetime")
    if not result:
        result = column
    new_table = copy.deepcopy(table)

    @hide_traceback_decorator
    def dataframe_to_datetime():
        new_table[result] = pd.to_datetime(table[column], **kwargs).to_frame()
        return new_table

    return dataframe_to_datetime()


def rename(table: pd.DataFrame, mapping: List[Tuple]) -> pd.DataFrame:

    _validate_object_type(table, pd.DataFrame)
    if not isinstance(table, pd.DataFrame):
        raise TypeError(f"Expected pandas.DataFrame but got {type(table)}")
    if not isinstance(mapping, List):
        raise TypeError(f"Expected list of tuples but got {type(mapping)}")
    new_table = copy.deepcopy(table)
    mapping = dict(mapping)

    @hide_traceback_decorator
    def rename_dataframes():
        return new_table.rename(columns=mapping)

    return rename_dataframes()


def drop_column(table: pd.DataFrame, column) -> pd.DataFrame:
    _validate_object_type(table, pd.DataFrame)
    if column not in table.columns:
        raise KeyError(
            f"Invalid column {column}, " f"needs to be one of {table.columns}"
        )

    @hide_traceback_decorator
    def drop_column_dataframes():
        new_table = copy.deepcopy(table)
        return new_table.drop(columns=column)

    return drop_column_dataframes()


def merge(
    left: pd.DataFrame,
    right: pd.DataFrame,
    how: str,
    on,
    left_on,
    right_on,
    left_index: bool,
    right_index: bool,
    sort: bool,
    suffixes,
    copy: bool,
    indicator: bool,
    validate: Optional[str],
) -> pd.DataFrame:
    _validate_object_type(left, pd.DataFrame)
    _validate_object_type(right, pd.DataFrame)

    @hide_traceback_decorator
    def merge_dataframes():
        df_merged = left.merge(
            right=right,
            how=how,
            on=on,
            left_on=left_on,
            right_on=right_on,
            left_index=left_index,
            right_index=right_index,
            sort=sort,
            suffixes=suffixes,
            copy=copy,
            indicator=indicator,
            validate=validate,
        )
        return df_merged

    return merge_dataframes()


def concat(
    table1: pd.DataFrame,
    table2: pd.DataFrame,
    join: str = "outer",
    ignore_index: bool = True,
    verify_integrity: bool = False,
    sort: bool = False,
) -> pd.DataFrame:
    _validate_object_type(table1, pd.DataFrame)
    _validate_object_type(table2, pd.DataFrame)

    @hide_traceback_decorator
    def concat_dataframes():
        return pd.concat(
            [table1, table2],
            join=join,
            ignore_index=ignore_index,
            verify_integrity=verify_integrity,
            sort=sort,
        )

    return concat_dataframes()


def fillna_table(
    table: pd.DataFrame,
    value: Union[(pd.DataFrame,) + ALL_SUPPORTED_TYPES],
    column=None,
    result=None,
):
    _validate_object_type(table, pd.DataFrame)

    @hide_traceback_decorator
    def fillna_table_dataframe():
        return fillna(
            table,
            value,
            column,
            result,
        )

    return fillna_table_dataframe()


def fillna(
    table: pd.DataFrame,
    value: Union[(pd.DataFrame,) + ALL_SUPPORTED_TYPES],
    column=None,
    result=None,
):
    _validate_object_type(table, pd.DataFrame)
    if not isinstance(value, (pd.DataFrame,) + ALL_SUPPORTED_TYPES):
        raise ValueError(
            "Invalid fillna value, needs to "
            f"be a float or an int or a string or Timestamp or Timedelta and not {value}"
        )

    @hide_traceback_decorator
    def fillna_dataframe():
        if isinstance(value, pd.DataFrame):
            new_table = copy.deepcopy(table)
            colname = get_single_column_name(table, "fillna")
            valcolname = get_single_column_name(value, "fillna")
            return new_table[colname].fillna(value[valcolname]).to_frame()

        elif column is None:
            return table.fillna(value=value)
        else:
            new_table = copy.deepcopy(table)
            new_table[result] = new_table[column].fillna(value)
            return new_table

    return fillna_dataframe()


def dropna(table: pd.DataFrame, axis, how, thresh, subset):
    _validate_object_type(table, pd.DataFrame)
    if subset is not None:
        if axis == 1 or axis == "columns":
            raise PrivacyException(
                "Considering only a subset of rows "
                "for dropping is not privacy preserving."
            )
        for s in subset:
            if s not in table.columns:
                raise KeyError(
                    f"Found invalid column {s}, " f"columns available: {table.columns}"
                )

    @hide_traceback_decorator
    def dropna_dataframes():
        args = {"axis": axis, "subset": subset}
        for var, name in [(how, "how"), (thresh, "thresh")]:
            if var is not None:
                args[name] = var
        return table.dropna(**args)

    return dropna_dataframes()


def isna(table: pd.DataFrame, column, result):
    _validate_object_type(table, pd.DataFrame)

    @hide_traceback_decorator
    def isna_dataframes():
        if column is None:
            return table.isna()
        else:
            new_table = copy.deepcopy(table)
            new_table[result] = new_table[column].isna()
            return new_table

    return isna_dataframes()


def astype(table: pd.DataFrame, dtype: type, column, result):
    _validate_object_type(table, pd.DataFrame)
    new_table = copy.deepcopy(table)
    if column is not None:
        if column not in table.columns:
            raise KeyError(
                f"Invalid column {column}, needs to be one of {table.columns}"
            )
        dtype = {column: dtype}
        if result != column:

            @hide_traceback_decorator
            def astype_dataframe_column(new_table):
                new_table[result] = new_table[column].astype(dtype)
                return new_table

            return astype_dataframe_column(new_table)

    @hide_traceback_decorator
    def astype_dataframe(new_table):
        new_table = new_table.astype(dtype)
        return new_table

    return astype_dataframe(new_table)


def get_single_column_name(table, fname):
    _validate_object_type(table, pd.DataFrame)
    if len(table.columns) != 1:
        table_columns = ", ".join(table.columns)
        raise ValueError(
            f"Function {fname} can be applied to single column only. Please "
            f"select one out of [{table_columns}]"
        )

    @hide_traceback_decorator
    def get_single_column_name_dataframes():
        return table.columns[0]

    return get_single_column_name_dataframes()


def add_number(summand1: pd.DataFrame, summand2: Union[ARITHMETIC_TYPES]):
    _validate_object_type(summand1, pd.DataFrame)
    cols1 = summand1.columns
    if len(cols1) != 1:
        raise ValueError(
            f"We expect 'summand1' to have only 1 column. "
            f"It has {len(cols1)} columns."
        )
    if not isinstance(summand2, ARITHMETIC_TYPES):
        raise ValueError(
            f"We only support addition of an int or float but summand2 is "
            f"of type {type(summand2)}"
        )
    new_table = copy.deepcopy(summand1)

    @hide_traceback_decorator
    def add_number_dataframe():
        new_table[cols1[0]] = new_table[cols1[0]] + summand2
        return new_table

    return add_number_dataframe()


def add_table(summand1: pd.DataFrame, summand2: pd.DataFrame):
    _validate_object_type(summand1, pd.DataFrame)
    cols1 = summand1.columns
    if len(cols1) != 1:
        raise ValueError(
            f"We expect 'summand1' to have only 1 column. "
            f"It has {len(cols1)} columns."
        )
    cols2 = summand2.columns
    if len(cols2) != 1:
        raise ValueError(
            f"We expect 'summand2' to have only 1 column. "
            f"It has {len(cols1)} columns."
        )

    @hide_traceback_decorator
    def add_table_dataframe():
        new_table = copy.deepcopy(summand1)
        new_table = new_table[[cols1[0]]]
        datetime_converted = False
        if is_datetime64_dtype(new_table[cols1[0]]):
            new_table[cols1[0]] = pd.to_numeric(new_table[cols1[0]])
            datetime_converted = True

        if is_datetime64_dtype(summand2[cols2[0]]):
            summand2[cols2[0]] = pd.to_numeric(summand2[cols2[0]])
            datetime_converted = True

        new_table[cols1[0]] = new_table[cols1[0]] + summand2[cols2[0]]
        if datetime_converted:
            return pd.to_timedelta(new_table[cols1[0]]).to_frame()
        return new_table

    return add_table_dataframe()


def divide(dividend: pd.DataFrame, divisor: pd.DataFrame):
    _validate_object_type(dividend, pd.DataFrame)
    _validate_object_type(divisor, pd.DataFrame)
    if isinstance(divisor, pd.DataFrame) and dividend.shape != divisor.shape:
        raise ValueError(
            f"Broadcasting is not permitted for the division: "
            f"{dividend.shape} != {divisor.shape}. "
            f"Please use FederatedDataFrames of the same size."
        )
    elif isinstance(divisor, pd.DataFrame):
        divisor = divisor.values  # to avoid remapping based on index
    else:
        raise TypeError(
            f"Unsupported type of divisor for division operation: {type(divisor)}. "
            f"Supported types are: {[pd.DataFrame]}."
        )

    @hide_traceback_decorator
    def divide_dataframe():
        return dividend.astype("float") / divisor

    return divide_dataframe()


def divide_by_constant(dividend: pd.DataFrame, divisor: Union[int, float, bool]):
    _validate_object_type(dividend, pd.DataFrame)

    if not isinstance(divisor, (int, float, bool)):
        raise TypeError(
            f"Unsupported type of divisor for division operation: {type(divisor)}. "
            f"Supported types are: {[int, float, bool]}."
        )

    @hide_traceback_decorator
    def divide_by_constant_dataframe():
        return dividend.astype("float") / divisor

    return divide_by_constant_dataframe()


def multiply(multiplicand: pd.DataFrame, multiplier: pd.DataFrame):
    _validate_object_type(multiplicand, pd.DataFrame)
    _validate_object_type(multiplier, pd.DataFrame)
    if isinstance(multiplier, pd.DataFrame) and multiplicand.shape != multiplier.shape:
        raise ValueError(
            f"Broadcasting is not permitted for the multiplication: "
            f"{multiplicand.shape} != {multiplier.shape}. "
            f"Please use FederatedDataFrames of the same size."
        )
    elif isinstance(multiplier, pd.DataFrame):
        multiplier = multiplier.values  # to avoid remapping based on index
    else:
        raise TypeError(
            f"Unsupported type of multiplicand for multiplication operation: "
            f"{type(multiplier)}. Supported types are: {[pd.DataFrame]}."
        )

    @hide_traceback_decorator
    def multiply_dataframe():
        return multiplicand * multiplier

    return multiply_dataframe()


def multiply_by_constant(multiplicand: pd.DataFrame, multiplier: Union[int, float, bool]):
    _validate_object_type(multiplicand, pd.DataFrame)
    if not isinstance(multiplier, (int, float, bool)):
        raise TypeError(
            f"Unsupported type of divisor for division operation: {type(multiplier)}. "
            f"Supported types are: {[int, float, bool]}."
        )

    @hide_traceback_decorator
    def multiply_by_constant_dataframe():
        return multiplicand * multiplier

    return multiply_by_constant_dataframe()


def neg(table: pd.DataFrame):
    _validate_object_type(table, pd.DataFrame)
    colname = get_single_column_name(table, "__neg__")

    @hide_traceback_decorator
    def neg_dataframe():
        return (-pd.to_numeric(table[colname])).to_frame()

    return neg_dataframe()


def invert(table: pd.DataFrame):
    """Tilde operator which can be applied to Series and DataFrame, to bool type"""
    _validate_object_type(table, pd.DataFrame)

    @hide_traceback_decorator
    def invert_dataframe():
        return ~table

    return invert_dataframe()


def logical_conjunction(
    left: pd.DataFrame, right: Union[int, bool, pd.DataFrame], conjunction_type: str
):
    """
    Logical and conjunction of a single column DataFrame with a constant value or another
    single column DataFrame
    Args:
        left: single column DataFrame to conjunct
        right: constant value or single column DataFrame to conjunct
        conjunction_type: type of conjunction ("and", "or")
    Returns:
        logical conjunction of left and right argument.
    """
    _validate_object_type(left, pd.DataFrame)
    col_name_left = get_single_column_name(left, "logical_and")
    if not isinstance(right, (int, bool, pd.DataFrame)):
        raise ValueError(
            f"We only support logical_and with pandas.DataFrame, int or boolean but "
            f"right is of type {type(right)}"
        )

    @hide_traceback_decorator
    def dataframe_logical_conjunction():
        if isinstance(right, (int, bool)):
            if conjunction_type == "and":
                left[col_name_left] = left[col_name_left] & right
            elif conjunction_type == "or":
                left[col_name_left] = left[col_name_left] | right

        elif isinstance(right, pd.DataFrame):
            col_name_right = get_single_column_name(right, "logical_and")
            if conjunction_type == "and":
                left[col_name_left] = left[col_name_left] & right[col_name_right]
            elif conjunction_type == "or":
                left[col_name_left] = left[col_name_left] | right[col_name_right]

        return left

    return dataframe_logical_conjunction()


def str_len(table: pd.DataFrame):
    _validate_object_type(table, pd.DataFrame)
    col_name = get_single_column_name(table, "str.contains")
    if len(table[col_name]) == 0:
        raise ValueError(
            f"Column {col_name} of DataFrame has no data. String "
            f"accessors not supported on empty DataFrames."
        )

    if not is_string_dtype(table[col_name]):
        raise ValueError(
            f"Column {col_name} of DataFrame is of type "
            f"{type(table[col_name].iloc[0])}. String accessors are only supported on "
            f"string types."
        )

    @hide_traceback_decorator
    def str_len_dataframes():
        table[col_name] = table[col_name].str.len()
        return table

    return str_len_dataframes()


def str_contains(table: pd.DataFrame, pattern: str):
    """
    Checks if string values in single column DataFrame contain pattern.
    Args:
        table: single column DataFrame containing string values
        pattern: string to match
    Return:
        single column boolean value DataFrame
    """
    _validate_object_type(table, pd.DataFrame)
    col_name = get_single_column_name(table, "str.contains")
    if len(table[col_name]) == 0:
        raise ValueError(
            f"Column {col_name} of DataFrame has no data. String "
            f"accessors not supported on empty DataFrames."
        )

    if not is_string_dtype(table[col_name]):
        raise ValueError(
            f"Column {col_name} of DataFrame is of type "
            f"{type(table[col_name].iloc[0])}. String accessors are only supported on "
            f"string types."
        )

    @hide_traceback_decorator
    def str_contains_dataframe():
        table[col_name] = table[col_name].str.contains(pattern)
        return table

    return str_contains_dataframe()


def datetime_like_properties(table: pd.DataFrame, datetime_like_property: str):
    """
    Checks if string values in single column DataFrame contain pattern.
    Args:
        table: single column DataFrame containing Timedelta values
        datetime_like_property: datetime-like property
    Return:
        single column boolean value DataFrame
    """
    _validate_object_type(table, pd.DataFrame)
    new_table = copy.deepcopy(table)

    if datetime_like_property not in DATETIME_LIKE_PROPERTIES:
        raise ValueError(
            f"The operation {datetime_like_property} "
            f"is not supported for TimedeltaArray. "
            f"List of supported operations: {DATETIME_LIKE_PROPERTIES}."
        )
    col_name = get_single_column_name(new_table, f"dt.{datetime_like_property}")
    if len(new_table[col_name]) == 0:
        raise ValueError(
            f"Column {col_name} of DataFrame {new_table} has no data. "
            f"dt accessors not supported on empty DataFrames."
        )
    if hasattr(new_table[col_name], "dt") and hasattr(
        new_table[col_name].dt, datetime_like_property
    ):

        @hide_traceback_decorator
        def datetime_like_properties_dataframes():
            new_table[col_name] = getattr(new_table[col_name].dt, datetime_like_property)
            return new_table

        return datetime_like_properties_dataframes()
    else:
        raise TypeError(
            f"dt accessor is supported only "
            f"for {DATETIME_LIKE_PROPERTIES_CLASSES} objects."
        )


def sort_values(
    table: pd.DataFrame, by, axis, ascending, kind, na_position, ignore_index
):
    """Sort values using pandas' sort_values function"""
    _validate_object_type(table, pd.DataFrame)
    new_table = copy.deepcopy(table)

    @hide_traceback_decorator
    def sort_values_dataframes():
        return new_table.sort_values(
            by=by,
            axis=axis,
            ascending=ascending,
            kind=kind,
            na_position=na_position,
            ignore_index=ignore_index,
        )

    return sort_values_dataframes()


def isin(table: pd.DataFrame, values):
    _validate_object_type(table, pd.DataFrame)

    @hide_traceback_decorator
    def isin_dataframes():
        return table.isin(values)

    return isin_dataframes()


def _loc(
    table: pd.DataFrame,
    index_mask: Union[pd.DataFrame, pd.Series, List[bool], slice],
    columns: Union[slice, str, List[str]],
    is_setter: bool,
    values: Union[ALL_SUPPORTED_TYPES_WITH_PANDAS_DF + (None,)] = None,
) -> pd.DataFrame:
    _validate_object_type(table, pd.DataFrame)
    """Apply loc for setting values"""
    new_table = copy.deepcopy(table) if is_setter else table
    table_n_rows = new_table.shape[0]
    validate_index_mask_size, index_mask_n_rows = True, -1

    # Verify index mask type
    if isinstance(index_mask, PANDAS_DF_TYPES):
        index_mask_n_rows = index_mask.shape[0]
    elif isinstance(index_mask, list) and len(set(map(type, index_mask))) == 1:
        index_mask_n_rows = len(index_mask)
        if index_mask_n_rows > 0:
            if not isinstance(index_mask[0], bool):
                raise TypeError(
                    f"Unsupported type of index mask for .loc: {type(index_mask[0])}."
                    f"Supported types are: {(bool,)}."
                )
    elif isinstance(index_mask, list):
        raise TypeError(
            f"Index mask for .loc includes different types: {set(map(type, index_mask))}."
        )
    elif isinstance(index_mask, slice):
        validate_index_mask_size = False  # allowed type, no need for size to match
    else:
        raise TypeError(
            f"Type of index mask for .loc is not supported: {set(map(type, index_mask))}."
            f"Supported types are: {(list, slice) + PANDAS_DF_TYPES}."
        )
    # Convert pd.DataFrame to pd.Series if needed
    if isinstance(index_mask, pd.DataFrame) and len(index_mask.columns) > 0:
        index_mask = index_mask[index_mask.columns[0]]

    # Verify that sizes of the table and index mask are matching
    if validate_index_mask_size and table_n_rows != index_mask_n_rows:
        raise IndexError(
            f"Size of index mask for .loc is not matching the data source: "
            f"{index_mask_n_rows} != {table_n_rows}."
        )

    # Verify type of columns argument
    if isinstance(columns, slice):
        slice_properties_values = {
            getattr(columns, pr)
            for pr in dir(columns)
            if not pr.startswith("_") and not callable(getattr(columns, pr))
        }
        if slice_properties_values != {None}:
            raise NotImplementedError(
                ".loc is not supporting slice different from (None, None, None) "
                "for column selection. Please use one of the permitted operations: "
                ".loc[mask, column] or .loc[mask, [column1, columns2]] or .loc[mask, :]."
            )
    elif isinstance(columns, (str, list)):
        if isinstance(columns, str):
            columns = [columns]
        for column in columns:
            if column not in new_table.columns:
                raise KeyError(
                    f"'{column}' is not in columns. Available "
                    f"columns are {new_table.columns}"
                )
    else:
        raise TypeError(
            f"Unsupported type of columns for .loc: {type(columns)}."
            f"Supported types are: {(slice, str, list)}."
        )

    if is_setter:
        # Verify type of values argument
        if not isinstance(values, ALL_SUPPORTED_TYPES_WITH_PANDAS_DF):
            raise TypeError(
                f"Unsupported type of values for .loc: {type(values)}."
                f"Supported types are: {ALL_SUPPORTED_TYPES_WITH_PANDAS_DF}."
            )

        # Verify that sizes of the table and values are matching
        if isinstance(values, PANDAS_DF_TYPES):
            values_n_rows = values.shape[0]
        elif isinstance(values, list):
            values_n_rows = len(values)
        else:
            values_n_rows = 1

        assigned_n_rows = new_table.loc[index_mask, columns].shape[0]
        if values_n_rows != 1 and values_n_rows != assigned_n_rows:
            raise ValueError(
                f"Must have equal len keys and value when setting with an iterable: "
                f"{values_n_rows} != {assigned_n_rows}."
            )

        # Convert pd.DataFrame to pd.Series if needed
        if isinstance(values, pd.DataFrame) and len(values.columns) > 0:
            values = values[values.columns[0]]

        # Make sure that format won't be converted after the assignment
        if isinstance(values, pd.Series):
            values = pd.Series(values, dtype=object)

        @hide_traceback_decorator
        def loc_setter_dataframes():
            new_table.loc[index_mask, columns] = values
            return new_table

        return loc_setter_dataframes()
    else:

        @hide_traceback_decorator
        def loc_dataframes():
            return new_table.loc[index_mask, columns]

        return loc_dataframes()


def loc_getter(
    table: pd.DataFrame,
    index_mask: Union[pd.DataFrame, pd.Series, List[bool], slice],
    columns: Union[slice, str, List[str]],
) -> pd.DataFrame:
    return _loc(
        table=table,
        index_mask=index_mask,
        columns=columns,
        is_setter=False,
        values=None,
    )


def loc_setter(
    table: pd.DataFrame,
    index_mask: Union[pd.DataFrame, pd.Series, List[bool], slice],
    columns: Union[slice, str, List[str]],
    values: Union[ALL_SUPPORTED_TYPES_WITH_PANDAS_DF],
) -> pd.DataFrame:
    return _loc(
        table=table,
        index_mask=index_mask,
        columns=columns,
        is_setter=True,
        values=values,
    )


def groupby(table: pd.DataFrame, by, axis, sort, group_keys, observed, dropna):
    _validate_object_type(table, pd.DataFrame)

    args = {"by": by, "axis": axis, "sort": sort, "observed": observed, "dropna": dropna}
    for var, name in [(group_keys, "group_keys")]:
        if var is not None:
            args[name] = var

    if isinstance(by, Callable):
        raise PrivacyException(
            "Only predefined functions are allowed within a graph, "
            "so grouping by a function is not possible."
        )
    new_table = copy.deepcopy(table)

    @hide_traceback_decorator
    def groupby_dataframes():
        return new_table.groupby(**args)

    return groupby_dataframes()


def last(table: DataFrameGroupBy):
    _validate_object_type(table, pandas.core.groupby.generic.DataFrameGroupBy)

    @hide_traceback_decorator
    def last_groupby():
        return table.last()

    return last_groupby()


def first(table: DataFrameGroupBy):
    _validate_object_type(table, pandas.core.groupby.generic.DataFrameGroupBy)

    @hide_traceback_decorator
    def first_goupby():
        return table.first()

    return first_goupby()


def size(table: DataFrameGroupBy):
    _validate_object_type(table, pandas.core.groupby.generic.DataFrameGroupBy)

    @hide_traceback_decorator
    def size_goupby():
        res = table.size()
        if isinstance(res, pd.Series):
            res = res.to_frame().rename({0: "size"}, axis=1)
        return res

    return size_goupby()


def mean(table: DataFrameGroupBy):
    _validate_object_type(table, pandas.core.groupby.generic.DataFrameGroupBy)

    @hide_traceback_decorator
    def mean_goupby():
        return table.mean()

    return mean_goupby()


def count(table: DataFrameGroupBy):
    _validate_object_type(table, pandas.core.groupby.generic.DataFrameGroupBy)

    @hide_traceback_decorator
    def count_groupby():
        return table.count()

    return count_groupby()


def cumsum(table: DataFrameGroupBy):
    _validate_object_type(table, pandas.core.groupby.generic.DataFrameGroupBy)

    @hide_traceback_decorator
    def cumsum_groupby():
        return table.cumsum()

    return cumsum_groupby()


def sum(table: DataFrameGroupBy):
    _validate_object_type(table, pandas.core.groupby.generic.DataFrameGroupBy)

    @hide_traceback_decorator
    def sum_groupby():
        return table.sum()

    return sum_groupby()


def diff(
    table: DataFrameGroupBy,
    periods: int = 1,
    axis: int = 0,
):
    _validate_object_type(table, pandas.core.groupby.generic.DataFrameGroupBy)

    @hide_traceback_decorator
    def diff_groupby():
        return table.diff(periods=periods, axis=axis)

    return diff_groupby()


def shift(
    table: DataFrameGroupBy,
    periods: int = 1,
    freq: Optional[str] = None,
    axis: int = 0,
    fill_value=None,
):
    _validate_object_type(table, pandas.core.groupby.generic.DataFrameGroupBy)

    @hide_traceback_decorator
    def shift_groupby():
        return table.shift(periods=periods, freq=freq, axis=axis, fill_value=fill_value)

    return shift_groupby()


def rank(
    table: DataFrameGroupBy,
    method: str = "average",
    ascending: bool = True,
    na_option: str = "keep",
    pct: bool = False,
    axis: int = 0,
):
    _validate_object_type(table, pandas.core.groupby.generic.DataFrameGroupBy)

    @hide_traceback_decorator
    def rank_groupby():
        return table.rank(method, ascending, na_option, pct, axis)

    return rank_groupby()


def drop_duplicates(
    table: pd.DataFrame,
    subset,
    keep: Union[Literal["first"], Literal["last"], Literal[False]],
    ignore_index: bool,
):
    _validate_object_type(table, pd.DataFrame)
    new_table = copy.deepcopy(table)

    @hide_traceback_decorator
    def drop_duplicates_dataframes():
        return new_table.drop_duplicates(
            subset=subset, keep=keep, inplace=False, ignore_index=ignore_index
        )

    return drop_duplicates_dataframes()


def reset_index(table: pd.DataFrame, drop):
    _validate_object_type(table, pd.DataFrame)
    new_table = copy.deepcopy(table)

    @hide_traceback_decorator
    def reset_index_dataframes():
        return new_table.reset_index(drop=drop)

    return reset_index_dataframes()


def prepare_sankey_plot(table: pd.DataFrame, time_col, group_col, observable_col):
    _validate_object_type(table, pd.DataFrame)

    @hide_traceback_decorator
    def prepare_sankey_dataframes():
        data = table.sort_values(by=time_col)
        #     build list of observed items (e.g. applied treatments per person)
        #     sorted by time
        df_history = data.groupby(group_col)[observable_col].apply(np.array)

        #    create tuples of predecessor, successor, which are the edges
        #    of the sankey graph
        res = pd.DataFrame(
            df_history.apply(lambda x: list(zip(x[:-1], x[1:]))).sum(),
            columns=["source", "target"],
        )
        return res

    return prepare_sankey_dataframes()


def rolling(table: pd.DataFrame, window, min_periods, center, on, axis, closed):
    _validate_object_type(table, pd.DataFrame)
    _validate_object_type(window, (int, timedelta))
    _validate_object_type(min_periods, (int, type(None)))
    _validate_object_type(center, bool)
    _validate_object_type(on, (str, type(None)))
    _validate_object_type(axis, (int, str, type(None)))
    _validate_object_type(closed, (str, type(None)))

    new_table = copy.deepcopy(table)

    @hide_traceback_decorator
    def rolling_dataframes():
        return new_table.rolling(
            window=window,
            min_periods=min_periods,
            center=center,
            on=on,
            axis=axis,
            closed=closed,
        )

    return rolling_dataframes()


def rolling_sum(table):
    _validate_object_type(table, Rolling)
    new_table = copy.deepcopy(table)

    @hide_traceback_decorator
    def rolling_sum_dataframes():
        return new_table.sum()

    return rolling_sum_dataframes()


def rolling_mean(table):
    _validate_object_type(table, Rolling)
    new_table = copy.deepcopy(table)

    @hide_traceback_decorator
    def rolling_mean_dataframes():
        return new_table.mean()

    return rolling_mean_dataframes()


@hide_traceback_decorator
def get_comorbidities(row, mapping):
    res = pd.Series(dtype=bool)
    for key in mapping.keys():
        res[key] = len(set(mapping[key]) & set(row)) > 0
    return res


def _validate_mapping(mapping: Dict[str, List[str]]):
    expected_keys = set(get_default_comorbidity_mapping().keys())

    for key, val in mapping.items():
        _validate_object_type(key, str)
        _validate_object_type(val, Iterable)
        for entry in val:
            _validate_object_type(entry, str)
    missing = expected_keys - set(mapping.keys())
    if len(missing):
        raise TransformationsException(f"Missing keys {missing} in comorbidity mapping!")


def _validate_datafame_column(df: pd.DataFrame, col: str):
    if col not in df.columns:
        raise KeyError(f"The column name {col} was not found in the pandas dataframe.")


def charlson_comorbidities(
    table: pd.DataFrame,
    index_column: str,
    icd_columns: List[str],
    mapping: Dict[str, List[str]],
) -> pd.DataFrame:
    _validate_object_type(mapping, Dict)
    _validate_mapping(mapping)
    _validate_object_type(table, pd.DataFrame)
    for col in icd_columns + [index_column]:
        _validate_datafame_column(table, col)

    @hide_traceback_decorator
    def charlson_comorbidities_dataframes():
        df_processed = table.groupby(index_column).apply(
            lambda x: np.concatenate(x[icd_columns].dropna(axis=1).values)
        )
        result = df_processed.apply(get_comorbidities, args=[mapping]).sort_index()

        return result

    return charlson_comorbidities_dataframes()


def charlson_comorbidity_score(
    table: pd.DataFrame,
    index_column: str,
    icd_columns: List[str],
    mapping: Dict[str, List[str]],
) -> pd.DataFrame:
    _validate_mapping(mapping)
    df_comorbidities = charlson_comorbidities(table, index_column, icd_columns, mapping)

    @hide_traceback_decorator
    def charlson_comorbidity_score_dataframes():
        """Function uses hard coded ICD categories and scores per category
        as defined by the NCI and validated with client Data Scientists.
        Possibility to move this into the json mapping
        if studies require alternative groups or scores."""

        df_comorbidities["MILD LIVER DISEASE"] = (
            df_comorbidities["MILD LIVER DISEASE"]
            & ~df_comorbidities["MODERATE-SEVERE LIVER DISEASE"]
        )
        df_comorbidities["DIABETES"] = (
            df_comorbidities["DIABETES"]
            & ~df_comorbidities["DIABETES WITH COMPLICATIONS"]
        )

        charlson_score = pd.Series(index=df_comorbidities.columns, data=1, name="CCI")
        charlson_score["DIABETES WITH COMPLICATIONS"] = 2.0
        charlson_score["PARALYSIS"] = 2.0
        charlson_score["MODERATE-SEVERE RENAL DISEASE"] = 2.0
        charlson_score["MODERATE-SEVERE LIVER DISEASE"] = 3.0
        charlson_score["AIDS"] = 6.0

        return pd.DataFrame(
            {"cci": df_comorbidities.astype(int).dot(pd.Series(charlson_score))}
        )

    return charlson_comorbidity_score_dataframes()


def transform_columns(
    table: pd.DataFrame,
    transformation: dict,
) -> pd.DataFrame:
    transformation = pd.DataFrame(transformation)
    _validate_object_type(table, pd.DataFrame)
    _validate_object_type(transformation, pd.DataFrame)
    for col in transformation.index:
        _validate_datafame_column(table, col)

    @hide_traceback_decorator
    def transform_columns_dataframes():
        return table.dot(transformation)

    return transform_columns_dataframes()


def sample(
    table: pd.DataFrame,
    n: Optional[int],
    frac: Optional[float],
    replace: bool,
    random_state: Optional[int],
    ignore_index: bool,
):
    _validate_object_type(table, pd.DataFrame)

    @hide_traceback_decorator
    def sample_dataframes():
        return table.sample(
            n=n,
            frac=frac,
            replace=replace,
            random_state=random_state,
            ignore_index=ignore_index,
        )

    if n and n > table.shape[0] and not replace:
        raise ValueError(
            """n cannot be greater than the number of rows
            in the DataFrame, if replace is False."""
        )
    return sample_dataframes()

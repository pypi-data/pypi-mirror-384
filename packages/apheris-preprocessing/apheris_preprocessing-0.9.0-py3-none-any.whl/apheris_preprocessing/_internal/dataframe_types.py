from apheris_preprocessing._internal.utils.commands import NodeCommands
from typing import Union
import pandas as pd

ColumnIdentifier = Union[str, int, float, bool, None]
BasicTypes = Union[float, int, str, bool, pd.Timestamp, pd.Timedelta]

ARITHMETIC_TYPES = NodeCommands.get_arithmetic_types()
BASIC_TYPES = NodeCommands.get_all_supported_types()
ALL_TYPES = ("FederatedDataFrame",) + BASIC_TYPES
BASIC_TYPES_WITH_LIST = (list,) + BASIC_TYPES
ALL_TYPES_WITH_LIST = ("FederatedDataFrame",) + BASIC_TYPES_WITH_LIST

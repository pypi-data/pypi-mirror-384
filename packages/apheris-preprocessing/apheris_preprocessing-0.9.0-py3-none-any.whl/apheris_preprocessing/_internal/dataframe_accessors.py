from typing import (
    Dict,
    Literal,
    Optional,
    Union,
)

from apheris_preprocessing._internal.utils.commands import NodeCommands

from apheris_preprocessing._internal.utils.exceptions_handling import (
    TransformationsInvalidGraphException,
    TransformationsNotImplementedException,
    TransformationsNotMatchingNumberOfArgumentsException,
    TransformationsOperationArgumentTypeNotAllowedException,
)

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .dataframe_client import FederatedDataFrame

from .dataframe_types import (
    ALL_TYPES_WITH_LIST,
    BASIC_TYPES,
    BASIC_TYPES_WITH_LIST,
)


class _LocIndexer:
    def __init__(self, obj: "FederatedDataFrame"):
        self.obj = obj

    def __parse_inputs_construct_graph_inputs(
        self,
        key: tuple,
        is_setter: bool,
        value: Optional[Union[ALL_TYPES_WITH_LIST]] = None,
    ):
        # lazy import to avoid circular dependency
        from .dataframe_client import FederatedDataFrame

        other_srcs, edges_labels = list(), dict()
        node_command_other_srcs_keys, node_command_kwargs = list(), dict()

        # Extract loc index mask and columns
        if not isinstance(key, tuple):
            raise TransformationsOperationArgumentTypeNotAllowedException(
                function_name=".loc",
                argument_name="key",
                argument_type=type(key),
                supported_argument_types=[tuple],
            )
        elif len(key) != 2:
            raise TransformationsNotMatchingNumberOfArgumentsException(
                trigger_argument_name=".loc",
                numbers_of_arguments=[2],
            )
        index_mask, columns = key

        # Verify index mask type
        if isinstance(index_mask, FederatedDataFrame):
            other_srcs.append(index_mask)
            node_command_other_srcs_keys.append("index_mask")
            edges_labels[index_mask._uuid] = "index_mask"
        elif isinstance(index_mask, list) and len(set(map(type, index_mask))) == 1:
            if not isinstance(index_mask[0], bool):
                raise TransformationsOperationArgumentTypeNotAllowedException(
                    function_name=".loc",
                    argument_name="index mask",
                    argument_type=type(
                        index_mask[0],
                    ),
                    supported_argument_types=[bool],
                )
            node_command_kwargs["index_mask"] = index_mask
        elif isinstance(index_mask, slice):
            node_command_kwargs["index_mask"] = index_mask
        elif isinstance(index_mask, list):
            raise TransformationsOperationArgumentTypeNotAllowedException(
                function_name=".loc",
                argument_name="index mask",
                argument_type=set(map(type, index_mask)),
                supported_argument_types=[bool],
            )
        else:
            raise TransformationsOperationArgumentTypeNotAllowedException(
                function_name=".loc",
                argument_name="index mask",
                argument_type=type(index_mask),
                supported_argument_types=[FederatedDataFrame, list],
            )

        # Verify columns type
        if isinstance(columns, slice):
            slice_properties_values = {
                getattr(columns, pr)
                for pr in dir(columns)
                if not pr.startswith("_") and not callable(getattr(columns, pr))
            }
            if slice_properties_values != {None}:
                raise TransformationsNotImplementedException(
                    function_name=".loc",
                    message=(
                        ".loc is not supporting slice different from (None, None, None) "
                        "for column selection. Please use one of the permitted "
                        "operations: "
                        ".loc[mask, column] or "
                        ".loc[mask, [column1, columns2]] or "
                        ".loc[mask, :]."
                    ),
                )
        elif not isinstance(columns, (str, list)):
            raise TransformationsOperationArgumentTypeNotAllowedException(
                function_name=".loc",
                argument_name="columns",
                argument_type=type(columns),
                supported_argument_types=[slice, str, list],
            )
        node_command_kwargs["columns"] = columns

        # Extract values
        values = value
        if not is_setter:
            values = None  # for getter no values are specified
        elif isinstance(values, FederatedDataFrame):
            other_srcs.append(values)
            node_command_other_srcs_keys.append("values")
            edges_labels[values._uuid] = "values"
        elif isinstance(values, BASIC_TYPES_WITH_LIST):
            node_command_kwargs["values"] = values
        else:
            raise TransformationsOperationArgumentTypeNotAllowedException(
                function_name=".loc",
                argument_name="values",
                argument_type=type(values),
                supported_argument_types=ALL_TYPES_WITH_LIST,
            )

        if isinstance(columns, slice):
            node_label_columns = ":"
        elif isinstance(columns, str):
            node_label_columns = f"'{columns}'"
        else:
            node_label_columns = str(columns)

        index_mask_label = "index_mask"
        if isinstance(index_mask, slice):
            if index_mask is slice(None, None, None):
                index_mask_label = ":"
            else:
                index_mask_label = str(index_mask)
        node_label = f".loc[{index_mask_label}, {node_label_columns}]"
        if is_setter and isinstance(values, BASIC_TYPES):
            node_label_values = f"'{values}'" if isinstance(values, str) else values
            node_label = f"{node_label} = {node_label_values}"
        elif is_setter:
            node_label = f"{node_label} = values"

        # reference to keys which represent FederatedDataFrames, to be used in run()
        node_command_kwargs["other_srcs_keys"] = node_command_other_srcs_keys
        return self.obj._add_graph_dst_node_with_multiple_edges(
            node_label=node_label,
            other_srcs=other_srcs,
            node_command=(
                NodeCommands.loc_setter.name
                if is_setter
                else NodeCommands.loc_getter.name
            ),
            node_command_src_key="table",
            node_command_other_srcs_keys=node_command_other_srcs_keys,
            node_command_kwargs=node_command_kwargs,
            edges_labels=edges_labels,
            create_a_copy=not is_setter,
        )

    def __setitem__(
        self,
        key,
        value: Union[ALL_TYPES_WITH_LIST],
    ):
        return self.__parse_inputs_construct_graph_inputs(
            key=key,
            value=value,
            is_setter=True,
        )

    def __getitem__(
        self,
        key,
    ):
        return self.__parse_inputs_construct_graph_inputs(
            key=key,
            is_setter=False,
        )


class _Accessor:
    """
    Pandas-like accessor set of functions supported by FederatedDataFrame
    """

    def __init__(self, federated_df: "FederatedDataFrame"):
        """
        Creates an accessor for FederatedDataFrame
        Args:
            federated_df: FederatedDataFrame for which accessor is called.
        """
        self._df = federated_df


class _StringAccessor(_Accessor):
    """
    Pandas-like accessor for string functions on string valued single column
    FederatedDataFrames
    """

    def contains(self, pattern: str) -> "FederatedDataFrame":
        """
        Returns boolean mask according to the string valued entries of a
        FederatedDataFrame contain pattern string or not.
        The following arguments from pandas implementation are not supported:
        `missing case`, `flags`, `na` , `regex`
        Args:
            pattern: pattern string to check.
        Returns:
            new FederatedDataFrame object with updated computation graph.
        Example:
        ```
            fdf = FederatedDataFrame(DATASET_ID)
            mask_pattern = fdf[some_column].str.contains("some_pattern")
        ```
        """
        return self._df.str_contains(pattern)

    def len(self) -> "FederatedDataFrame":
        """
        Determines string length for each entry of a single column FederatedDataFrame.
        This function is called via str accessor.

        Returns:
            string length for each entry.

        Example:
        ```
            fdf = FederatedDataFrame(DATASET_ID)
            fdf[some_column].str.len()
        ```

        """
        return self._df.str_len()


class _DatetimeLikeAccessor(_Accessor):
    """
    Pandas-like accessor for datetime-like properties of a single column of a
    FederatedDataFrame
    """

    @classmethod
    def fill_in_dt_properties(cls, supported_remote_function_attr):
        @property
        def inner_property(self):
            return self._df.dt_datetime_like_properties(
                datetime_like_property=supported_remote_function_attr,
            )

        setattr(cls, supported_remote_function_attr, inner_property)


class _SpecialAccessor(_Accessor):
    """
    Pandas-like accessor for special monolithic operations on a FederatedDataFrame,
    currently used for Sankey Plots.
    """

    def prepare_sankey_plot(
        self, time_col: str, group_col: str, observable_col: str
    ) -> "FederatedDataFrame":
        """
        Convert historical list of observables [a, b, c, d] into predecessor-successor
        tuples (a,b), (b,c), (c,d) which build the edges of sankey graph.

        Args:
            time_col: column name of temporal sort column
            group_col: group column to build history on (e.g. patient_id)
            observable_col: observable, for which history is visualized
        ```
        """
        node_label = (
            f"prepare_sankey_plot with time_col {time_col}, group_col {group_col}, "
            f"observable_col {observable_col}"
        )
        return self._df._add_graph_dst_node_with_edge(
            node_label=node_label,
            node_command=NodeCommands.prepare_sankey_plot.name,
            node_command_src_key="table",
            node_command_kwargs={
                "time_col": time_col,
                "group_col": group_col,
                "observable_col": observable_col,
            },
        )


class _FederatedDataFrameGroupBy:
    """A FederatedDataFrame on which a group_by operation was defined,
    but not yet an aggregation operation,
    similar to Pandas' DataFrameGroupBy object"""

    def __init__(self, federated_data_frame: "FederatedDataFrame"):
        self._df = federated_data_frame

    def last(self) -> "FederatedDataFrame":
        """To be used after groupby, to select the last row of each group.
        We do not support any further arguments.
        The following arguments from pandas implementation are not supported:
        `numeric_only`, `min_count`

        Returns:
            new instance of the FederatedDataFrame with updated graph.

        Example:
            ```fdf.groupby([columns]).last()```

        """
        return self._df._add_operation_to_graph(command=NodeCommands.last.name)

    def first(self) -> "FederatedDataFrame":
        """To be used after groupby, to select the first row of each group.
        We do not support any further arguments.
        The following arguments from pandas implementation are not supported:
        `numeric_only`, `min_count`

        Returns:
            new instance of the FederatedDataFrame with updated graph.

        Example:
            ```fdf.groupby([columns]).first()```

        """
        return self._df._add_operation_to_graph(command=NodeCommands.first.name)

    def size(self) -> "FederatedDataFrame":
        """To be used after groupby, to select the size of each group.
        We do not support any further arguments.
        Returns:
            new instance of the FederatedDataFrame with updated graph.
        Example:
            ```fdf.groupby([columns]).size()```
        """
        return self._df._add_operation_to_graph(command=NodeCommands.size.name)

    def mean(self) -> "FederatedDataFrame":
        """To be used after groupby, to select the mean of each group.
        We do not support any further arguments.
        The following arguments from pandas implementation are not supported:
        `numeric_only`, `engine`, `engine_kwargs`
        Returns:
            new instance of the FederatedDataFrame with updated graph.
        Example:
            ```fdf.groupby([columns]).mean()```
        """
        return self._df._add_operation_to_graph(command=NodeCommands.mean.name)

    def sum(self) -> "FederatedDataFrame":
        """To be used after groupby, to select the sum of each group.
        The following arguments from pandas implementation are not supported:
        `numeric_only`, `min_count`, `engine`, `engine_kwargs`
        Returns:
            new instance of the FederatedDataFrame with updated graph.
        Example:
            ```fdf.groupby([columns]).sum()```
        """
        return self._df._add_operation_to_graph(command=NodeCommands.sum.name)

    def cumsum(self) -> "FederatedDataFrame":
        """To be used after groupby, to select the cumulative sum of each group.
        The following arguments from pandas implementation are not supported:
        `axis`,`*args`, `**kwargs`
        Returns:
            new instance of the FederatedDataFrame with updated graph.
        Example:
            ```fdf.groupby([columns]).cumsum()```
        """
        return self._df._add_operation_to_graph(command=NodeCommands.cumsum.name)

    def count(self):
        """To be used after groupby, to select the count of each group.

        Returns:
            new instance of the FederatedDataFrame with updated graph.
        Example:
            ```fdf.groupby([columns]).count()```

        """
        return self._df._add_operation_to_graph(command=NodeCommands.count.name)

    def diff(self, periods: int = 1, axis: int = 0) -> "FederatedDataFrame":
        """To be used after groupby, to calculate differences between table elements;
        similar to `pandas.DataFrameGroupBy.diff`. We support all arguments that are
        available for `pandas.DataFrameGroupBy.diff`.
        Returns:
            new instance of the FederatedDataFrame with updated graph.
        Example:
            ```fdf.groupby([columns]).diff()```
        """
        return self._df._add_operation_to_graph(
            command=NodeCommands.diff.name,
            args={
                "periods": periods,
                "axis": axis,
            },
        )

    def shift(
        self, periods: int = 1, freq: Optional[str] = None, axis: int = 0, fill_value=None
    ) -> "FederatedDataFrame":
        """To be used after groupby, to shift table elements; similar to
        `pandas.DataFrameGroupBy.shift`. We support all arguments that are available for
        `pandas.DataFrameGroupBy.shift`.
        Returns:
            new instance of the FederatedDataFrame with updated graph.
        Example:
            ```fdf.groupby([columns]).shift(offset)```
        """
        return self._df._add_operation_to_graph(
            command=NodeCommands.shift.name,
            args={
                "periods": periods,
                "freq": freq,
                "axis": axis,
                "fill_value": fill_value,
            },
        )

    def rank(
        self,
        method: Literal["average", "min", "max", "first", "dense"] = "average",
        ascending: bool = True,
        na_option: Literal["keep", "top", "bottom"] = "keep",
        pct: bool = False,
        axis: int = 0,
    ) -> "FederatedDataFrame":
        """To be used after groupby, to rank table elements; similar to
        `pandas.DataFrameGroupBy.rank`. We support all arguments that are available for
        `pandas.DataFrameGroupBy.rank`.
        Returns:
            new instance of the FederatedDataFrame with updated graph.
        Example:
            ```fdf.groupby([columns]).rank()```
        """
        return self._df._add_operation_to_graph(
            command=NodeCommands.rank.name,
            args={
                "method": method,
                "ascending": ascending,
                "na_option": na_option,
                "pct": pct,
                "axis": axis,
            },
        )

    def run(self, filepaths: Dict[str, str] = None):
        raise TransformationsInvalidGraphException(
            reason="groupby was found as the last operation",
            do_that="define an aggregation after groupby",
        )

    def export(self) -> str:
        return self._df.export()

    def display_graph(self):
        self._df.display_graph()

    def save_graph_as_image(
        self,
        filepath: str,
        image_format: str = "svg",
    ):
        self._df.save_graph_as_image(filepath=filepath, image_format=image_format)


class _FederatedDataFrameRolling:
    """
    A FederatedDataFrame on which a `rolling` operation was called, but not yet an
    aggregation operation. It is similar to `pandas.core.window.rolling.Rolling`
    object.

    We don't support following pandas rolling operations:
    `count`, `median`, `var`, `std`, `min`, `max`, `corr`, `cov`, `skew`, `rank`
    """

    def __init__(self, federated_data_frame: "FederatedDataFrame"):
        self._df = federated_data_frame

    def sum(self) -> "FederatedDataFrame":
        """
        The following arguments from `pandas.core.window.rolling.Rolling.sum` are not
        supported:
        `numeric_only`,`engine`
        """
        return self._df._add_operation_to_graph(command=NodeCommands.rolling_sum.name)

    def mean(self) -> "FederatedDataFrame":
        """
        The following arguments from `pandas.core.window.rolling.Rolling.mean` are not
        supported:
        `numeric_only`,  `engine`, `engine_kwargs`
        """
        return self._df._add_operation_to_graph(command=NodeCommands.rolling_mean.name)

    def run(self, filepaths: Dict[str, str] = None):
        raise TransformationsInvalidGraphException(
            reason="`rolling` was found as the last operation",
            do_that="define an aggregation after `rolling`",
        )

    def export(self) -> str:
        return self._df.export()

    def display_graph(self):
        self._df.display_graph()

    def save_graph_as_image(
        self,
        filepath: str,
        image_format: str = "svg",
    ):
        self._df.save_graph_as_image(filepath=filepath, image_format=image_format)

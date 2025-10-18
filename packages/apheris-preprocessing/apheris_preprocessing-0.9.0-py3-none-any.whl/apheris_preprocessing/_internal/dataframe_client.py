from __future__ import annotations

import copy
from datetime import timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Literal, Optional, Sequence, Union

import networkx as nx
import pandas as pd
from pandas.core.indexes.accessors import DatetimeProperties, TimedeltaProperties
from pandas.core.groupby.generic import DataFrameGroupBy


from apheris_preprocessing._internal.utils.exceptions_handling import (
    PrivacyException,
    TransformationsException,
)
from apheris_utils.data import download_dataset

from apheris_utils.data import get_asset_policies

from apheris_preprocessing._internal.utils.comparison_types import ComparisonType
from apheris_preprocessing._internal.utils.digraph import (
    DiGraph,
    DiGraphManager,
    DiGraphVisualizer,
)
from apheris_preprocessing._internal.utils.formats import InputFormat
from apheris_preprocessing._internal.utils.commands import NodeCommands
from apheris_preprocessing._internal.utils.node_uuid import NodeUUID

import tempfile

from apheris_preprocessing._internal.utils.exceptions_handling import (
    TransformationsFailedExecutionException,
    TransformationsFileExtensionNotDefinedWarning,
    TransformationsFileExtensionNotSupportedException,
    TransformationsInputTypeException,
    TransformationsInvalidGraphException,
    TransformationsInvalidSourceDataException,
    TransformationsMissingArgumentException,
    TransformationsMissingArgumentWarning,
    TransformationsModuleCommandNotFoundException,
    TransformationsNotMatchingNumberOfArgumentsException,
    TransformationsOperationArgumentTypeNotAllowedException,
    TransformationsOperationNotAllowedException,
    TransformationsUnknownCommandException,
)
from apheris_preprocessing._internal.utils.formats import get_default_comorbidity_mapping
from .dataframe_types import (
    ALL_TYPES,
    BASIC_TYPES,
    ColumnIdentifier,
    BasicTypes,
)


from .dataframe_accessors import (
    _LocIndexer,
    _StringAccessor,
    _SpecialAccessor,
    _DatetimeLikeAccessor,
    _FederatedDataFrameGroupBy,
    _FederatedDataFrameRolling,
)

from json import JSONDecodeError, loads

BasicTypes_Fdf = Union[float, int, str, bool, pd.Timestamp, pd.Timedelta,
                       "FederatedDataFrame"]


def _is_json(datasource: str) -> bool:
    try:
        loads(datasource)
        return True
    except JSONDecodeError:
        return False


class FederatedDataFrame:
    """
    Object that simplifies preprocessing by providing a pandas-like interface
    to preprocess tabular data.
    The FederatedDataFrame contains preprocessing transformations that are to
    be applied on a remote dataset. On which dataset it operates is specified in
    the constructor.
    """

    def __init__(
        self,
        dataset_id: Optional[str] = None,
        graph_json: Optional[str] = None,
        read_format: Union[str, InputFormat, None] = None,
        filename_in_zip: Union[str, None] = None,
    ):
        """
        Args:
            dataset_id: Dataset ID or path to a data file. A FederatedDataFrame
                can be created only either from a dataset id
                or from a graph JSON file. Both arguments cannot be used at the same time.
            graph_json: JSON file with a graph to be imported. If provided, the dataset_id
                must not be None.
            read_format: format of data source
            filename_in_zip: used for ZIP format to identify which file out of ZIP to take
                The argument is optional, but must be specified for ZIP format.
                If read_format is ZIP, the value of this argument is used to read one CSV.


        Example:

        * via dataset id: assume your dataset id is 'data-cloudnode':
        ```
            df = FederatedDataFrame('data-cloudnode')
        ```

        * optional: for remote data containing multiple files, choose which file to read:
        ```
            df = FederatedDataFrame('data-cloudnode', filename_in_zip='patients.csv')
        ```
        """
        self.str = _StringAccessor(self)
        self.special = _SpecialAccessor(self)
        self._tmp_dummy_data_folder = tempfile.TemporaryDirectory()
        self._remote_data_to_path_cache = {}
        nc = NodeCommands.datetime_like_properties

        remote_function_attrs = nc.get_supported_values_for_remote_function_attr(
            remote_function_attr="datetime_like_property"
        )
        for remote_function_attr in remote_function_attrs:
            _DatetimeLikeAccessor.fill_in_dt_properties(remote_function_attr)
            self.dt = _DatetimeLikeAccessor(self)

        if dataset_id and graph_json:
            raise TransformationsException(
                message=(
                    "Both dataset_id and graph_json cannot be provided at the same time. "
                    "Please provide only one of them."
                ),
            )
        elif dataset_id:

            self._from_dataset_id(
                dataset_id=dataset_id,
                read_format=read_format,
                filename_in_zip=filename_in_zip,
            )

        elif graph_json:
            self._import_graph(graph_json=graph_json)

        else:
            raise TransformationsException(
                message=(
                    "Either dataset_id or graph_json must be provided to create a "
                    "FederatedDataFrame. Please provide one of them."
                ),
            )

    def _from_dataset_id(
        self,
        dataset_id: str,
        read_format: Union[str, InputFormat, None] = None,
        filename_in_zip: Union[str, None] = None,
    ):
        """
        Initializes a FederatedDataFrame from a dataset id and adds the first node
        to computation graph for reading the data.
        Args:
            dataset_id: id of the dataset to create the FederatedDataFrame from.
        Returns:
            FederatedDataFrame object.
        """
        if _is_json(dataset_id):
            raise TransformationsException(
                message=(
                    "The dataset_id provided is a JSON string. "
                    "Please provide a valid dataset ID or create the"
                    "FederatedDataFrame from a graph_json with "
                    " ``` FederatedDataFrame(graph_json=json_str) ```."
                ),
            )

        self.__nx_graph = DiGraph()
        self.__uuid_instance = NodeUUID()
        if not read_format and filename_in_zip:
            read_format = InputFormat.ZIP
        elif not read_format:
            read_format = self._parse_file_extension(
                filepath_or_filename=dataset_id,
            )
        self._validate_if_read_format_supported(
            read_format=read_format,
        )
        self._validate_if_filename_for_zip_provided(
            read_format=read_format,
            filename_in_zip=filename_in_zip,
        )
        self._read_data(
            src_node_uuid=self._uuid,
            data_source=dataset_id,
            read_format=read_format,
            read_args={"filename": filename_in_zip},
        )

    ######################################################################################
    # properties
    ######################################################################################
    @property
    def _uuid(self):
        """Returns a unique id for the object"""
        return self.__uuid_instance.uuid

    @property
    def _graph(self):
        return self.__nx_graph

    @property
    def loc(self) -> "_LocIndexer":
        """Use pandas .loc notation to access the data"""
        return _LocIndexer(obj=self)

    ######################################################################################
    # graph construction methods
    ######################################################################################

    def _get_src_and_dst_uuids(self):
        """
        Get current node uuid, generate new one, assign it to the node and
            return this new uuid
        Returns: a pair of uuids (old and current which was newly generated)

        """
        src_node_uuid = self._uuid
        dst_node_uuid = self.__uuid_instance.update_uuid()
        return src_node_uuid, dst_node_uuid

    def _add_graph_dst_node_with_edge(
        self,
        node_label: str,
        node_command: str,
        node_command_src_key: Union[str, None] = None,
        node_command_kwargs: Union[dict, None] = None,
        create_a_copy: bool = True,
        include_identifier: bool = False,  # No need to provide more details
    ):
        """
        Add a node with an edge to the graph
        Args:
            node_label: label to be displayed on the graph
            node_command: the command which will be applied during the run call
            node_command_src_key: a key where the source node uuid to be stored
            node_command_kwargs: other arguments to be used for the command
            create_a_copy: bool, if True a copy of the current object will be created and
                returned
            include_identifier: bool, if True command arguments
                will be included in the node label

        Returns: if create_a_copy if True returns new instance of the current object with
            updated graph
        otherwise updates graph inplace and returns itself

        """
        new_self = copy.deepcopy(self) if create_a_copy else self

        src_node_uuid, dst_node_uuid = new_self._get_src_and_dst_uuids()

        node_command_kwargs = node_command_kwargs or dict()
        if node_command_src_key:
            node_command_kwargs[node_command_src_key] = src_node_uuid

        new_self.__nx_graph.add_graph_dst_node_with_edge(
            src_node_uuid=src_node_uuid,
            dst_node_uuid=dst_node_uuid,
            node_label=node_label,
            node_command=node_command,
            node_command_kwargs=node_command_kwargs,
            include_identifier=include_identifier,
        )

        return new_self

    @staticmethod
    def _convert_to_list(obj):
        if isinstance(obj, list):
            return obj
        else:
            return [obj]

    def _add_graph_dst_node_with_multiple_edges(
        self,
        node_label: str,
        other_srcs: Union[List["FederatedDataFrame"], "FederatedDataFrame"],
        node_command: str,
        node_command_src_key: Union[str, None] = None,
        node_command_other_srcs_keys: Union[List[Union[str, None]], str, None] = None,
        node_command_kwargs: Union[dict, None] = None,
        edges_labels: Union[Dict, None] = None,
        create_a_copy: bool = True,
        include_identifier: bool = False,  # No need to provide more details
    ):
        """
        Compose a graph from multiple: the initial graph and other (more than 1) sources,
            add a node with multiple (more than 2) edges
        Args:
            node_label: label to be displayed on the graph
            other_srcs: list of uuids of other source nodes
            node_command: the command which will be applied during the run call
            node_command_src_key: a key where the source node uuid to be stored
            node_command_other_srcs_keys: a list of keys where other source nodes uuids
                to be stored
            node_command_kwargs: other arguments to be used for the command
            edges_labels: dict with labels to be assigned to the edges
            create_a_copy: bool, if True a copy of the current object will be created and
                returned
            include_identifier: bool, if True command arguments
                will be included in the node label

        Returns: if create_a_copy if True returns new instance of the current object
        with updated graph otherwise updates graph inplace and returns itself

        """
        # Perform inputs types conversion and checks
        other_srcs = self._convert_to_list(other_srcs)
        node_command_other_srcs_keys = self._convert_to_list(node_command_other_srcs_keys)
        arguments = [other_srcs, node_command_other_srcs_keys]
        if edges_labels:
            arguments.append(edges_labels)
        numbers_of_arguments = list(map(len, arguments))
        if len(set(numbers_of_arguments)) > 1:
            raise TransformationsNotMatchingNumberOfArgumentsException(
                trigger_argument_name=f"{node_command} sources",
                numbers_of_arguments=numbers_of_arguments,
            )
        for other_src_i, other_src in enumerate(other_srcs):
            if not isinstance(other_src, FederatedDataFrame):
                raise TransformationsOperationArgumentTypeNotAllowedException(
                    function_name=node_command,
                    argument_name=node_command_other_srcs_keys[other_src_i],
                    argument_type=type(other_src),
                    supported_argument_types=[FederatedDataFrame],
                )

        # Create the copy of the self and update the uuid
        new_self = copy.deepcopy(self) if create_a_copy else self
        src_node_uuid, dst_node_uuid = new_self._get_src_and_dst_uuids()

        # Process sources to fill in other uuids in node command kwargs, compose graph
        src_nodes_uuids = [src_node_uuid]
        node_command_kwargs = node_command_kwargs or dict()
        if node_command_src_key:
            node_command_kwargs[node_command_src_key] = src_node_uuid
        for other_src_i, other_src in enumerate(other_srcs):
            new_self.__nx_graph = nx.compose(new_self.__nx_graph, other_src._graph)
            another_src_node_uuid = other_src._uuid
            src_nodes_uuids.append(another_src_node_uuid)
            node_command_another_src_key = node_command_other_srcs_keys[other_src_i]
            if node_command_another_src_key:
                node_command_kwargs[node_command_another_src_key] = another_src_node_uuid

        # Add destination node with multiple edges
        new_self.__nx_graph.add_graph_dst_node_with_multiple_edges(
            src_nodes_uuids=src_nodes_uuids,
            dst_node_uuid=dst_node_uuid,
            node_label=node_label,
            node_command=node_command,
            node_command_kwargs=node_command_kwargs,
            edges_labels=edges_labels,
            include_identifier=include_identifier,
        )
        return new_self

    ######################################################################################
    # methods which are called by user and are mapped to the remote functions
    ######################################################################################
    def _read_data(
        self,
        src_node_uuid: str,
        data_source: str,
        read_format: Union[str, InputFormat],
        read_args: Union[dict, None] = None,
        include_identifier: bool = True,
    ):
        """
        Read inout data source
        Args:
            src_node_uuid: uuid to the source node
            data_source: dataset id or path to a file
            read_format: input format
            read_args: used for ZIP format to identify which file out of ZIP to take
            include_identifier: bool, if True command arguments
                will be included in the node label
        """
        try:
            if isinstance(read_format, str):
                read_format = InputFormat[read_format.upper()]
        except KeyError:
            raise TransformationsFileExtensionNotSupportedException(
                file_extension=read_format,
                supported_file_extensions=InputFormat.get_supported_formats(),
            )
        if read_format == InputFormat.ZIP and not read_args.get("filename"):
            raise TransformationsMissingArgumentException(
                function_name="read", argument_name="filename_in_zip"
            )
        # additional arguments: no need to fail here, but educate user
        if read_format != InputFormat.ZIP and read_args.get("filename"):
            print(
                f"Argument 'filename_in_zip' is ignored "
                f"as is is not supported for reading {read_format.value}."
            )
            del read_args["filename"]

        self.__nx_graph.add_graph_src_node(
            src_node_uuid=src_node_uuid,
            node_label=f"Read {read_format.value}",
            node_command=NodeCommands.get_read_data_function(read_format).name,
            node_command_kwargs={
                "data_source": data_source,
                "read_args": read_args,
            },
            include_identifier=include_identifier,
        )

    def __setitem__(
        self,
        index: Union[str, int],
        value: Union[ALL_TYPES],
    ):
        """
        Manipulates values of columns or rows of a FederatedDataFrame. This
        operation does not return a copy of the FederatedDataFrame object,
        instead this operation is implemented inplace.
        That means, the computation graph within the FederatedDataFrame
        object is modified on the object level.
        This function is not available in a privacy fully preserving mode.

        Example:

            Assume the dummy data for 'data_cloudnode' looks like this:

            ```
                patient_id  age  weight
            0           1   77      55
            1           2   88      60
            2           3   93      83

            df = FederatedDataFrame('data_cloudnode')
            df["new column"] = df["weight"]
            df.preprocess_on_dummy()
            ```

            results in
            ```
               patient_id  age  weight  new_column
            0           1   77      55          55
            1           2   88      60          60
            2           3   93      83          83
            ```

        Args:
            index: column index or name or a boolean valued FederatedDataFrame as index
                mask.
            value: a constant value or a single column FederatedDataFrame
        """
        if isinstance(value, FederatedDataFrame):
            self._add_graph_dst_node_with_multiple_edges(
                node_label=f"Set column '{index}'",
                other_srcs=value,
                node_command=NodeCommands.setitem.name,
                node_command_src_key="table",
                node_command_other_srcs_keys="column_to_add",
                node_command_kwargs={
                    "index": index,
                },
                create_a_copy=False,  # This is an inplace operation
            )
        elif isinstance(value, (str, int, float)):
            value_for_label = f"'{value}'" if isinstance(value, str) else value
            self._add_graph_dst_node_with_edge(
                node_label=f"Set column '{index}' = {value_for_label}",
                node_command=NodeCommands.setitem.name,
                node_command_src_key="table",
                node_command_kwargs={"index": index, "value_to_add": value},
                create_a_copy=False,  # This is an inplace operation
            )
        else:
            raise TransformationsOperationArgumentTypeNotAllowedException(
                function_name=NodeCommands.setitem.name,
                argument_name="value",
                argument_type=type(value),
                supported_argument_types=[FederatedDataFrame, str, int, float],
            )

    def __getitem__(
        self,
        key: Union[str, int, "FederatedDataFrame"],
    ) -> "FederatedDataFrame":
        """

        Example:
            Assume the dummy data for 'data_cloudnode' looks like this:
            ```
                patient_id  age  weight
            0           1   77      55
            1           2   88      60
            2           3   93      83

            df = FederatedDataFrame('data_cloudnode')
            df = df["weight"]
            df.preprocess_on_dummy()
            ```

            results in
            ```
               weight
            0    55
            1    60
            2    83
            ```
        Args:
            key: column index or name or a boolean valued FederatedDataFrame as index
            mask.

        Returns:
            new instance of the current object with updated graph. If the key was a
            column identifier, the computation graph results in a single-column
            FederatedDataFrame. If the key was an index mask the resulting computation
            graph will produce a filtered FederatedDataFrame.
        """
        if isinstance(key, (str, int, float)):
            # We want to get a column
            return self._add_graph_dst_node_with_edge(
                node_label=f"Get column '{key}'",
                node_command=NodeCommands.getitem.name,
                node_command_kwargs={
                    "column": key,
                },
            )
        elif isinstance(key, FederatedDataFrame):
            # We want to select rows w.r.t. index `key`
            return self._add_graph_dst_node_with_multiple_edges(
                node_label="Filter using index_mask",
                other_srcs=key,
                node_command=NodeCommands.getitem_at_index_table.name,
                node_command_src_key="table",
                node_command_other_srcs_keys="index",
                edges_labels={key._uuid: "index_mask"},
            )
        else:
            raise TransformationsInputTypeException(
                function_name=self.__getitem__.__name__,
                argument_name="key",
                argument_type=type(key),
            )

    def add(
        self, left: ColumnIdentifier,
        right: BasicTypes,
        result: Optional[ColumnIdentifier] = None
    ) -> FederatedDataFrame:
        """Privacy-preserving addition: to a column (`left`)
        add another column or constant value (`right`)
        and store the result in `result`.
        Adding arbitrary iterables would allow for
        singling out attacks and is therefore disallowed.

        Example:
            Assume the dummy data for 'data_cloudnode' looks like this:
            ```
                patient_id  age  weight
            0           1   77      55
            1           2   88      60
            2           3   93      83

            df = FederatedDataFrame('data_cloudnode')
            df.add("weight", 100, "new_weight")
            df.preprocess_on_dummy()
            ```

            returns
            ```
               patient_id  age  weight  new_weight
            0           1   77      55         155
            1           2   88      60         160
            2           3   93      83         183

            df.add("weight", "age", "new_weight")
            ```

            returns
            ```
               patient_id  age  weight  new_weight
            0           1   77      55         132
            1           2   88      60         148
            2           3   93      83         176
            ```

        Args:
            left: a column identifier
            right: a column identifier or constant value
            result: name for the new result column
                can be set to None to overwrite the left column

        Returns:
            new instance of the current object with updated graph.

        """
        if isinstance(right, FederatedDataFrame):
            raise TransformationsOperationArgumentTypeNotAllowedException(
                function_name=self.add.__name__,
                argument_name="right",
                argument_type=type(right),
                supported_argument_types=list(BASIC_TYPES),
            )
        if isinstance(left, FederatedDataFrame):
            raise TransformationsOperationArgumentTypeNotAllowedException(
                function_name=self.add.__name__,
                argument_name="left",
                argument_type=type(left),
                supported_argument_types=["column identifier"],
            )
        if result is None:
            result = left

        return self._add_graph_dst_node_with_edge(
            node_label=f"{result} = {left} + {right}",
            node_command=NodeCommands.addition.name,
            node_command_src_key="table",
            node_command_kwargs={
                "summand_column1": left,
                "summand2": right,
                "result_column": result,
            },
        )

    def neg(
        self,
        column_to_negate: ColumnIdentifier,
        result_column: Optional[ColumnIdentifier] = None,
    ) -> FederatedDataFrame:
        """Privacy-preserving negation: negate column `column_to_negate` and store
        the result in column `result_column`, or leave `result_column` as None
        and overwrite `column_to_negate`.
        Using this form of negation removes the need for __setitem__ functionality
        which is not privacy-preserving.

        Example:
            Assume the dummy data for 'data_cloudnode' looks like this:
            ```
                patient_id  age  weight
            0           1   77      55
            1           2   88      60
            2           3   93      83

            df = FederatedDataFrame('data_cloudnode')
            df = df.neg("age", "neg_age")
            df.preprocess_on_dummy()
            ```

            returns
            ```
               patient_id  age  weight  neg_age
            0           1   77      55      -77
            1           2   88      60      -88
            2           3   93      83      -93
            ```

        Args:
            column_to_negate: column identifier
            result_column: optional name for the new column,
                if not specified, column_to_negate is overwritten

        Returns:
            new instance of the current object with updated graph.

        """
        if result_column is None:
            result_column = column_to_negate

        return self._add_graph_dst_node_with_edge(
            node_label=f"{result_column} = Negate {column_to_negate}",
            node_command=NodeCommands.negation.name,
            node_command_src_key="table",
            node_command_kwargs={
                "column_to_negate": column_to_negate,
                "result_column": result_column,
            },
        )

    def sub(self, left: ColumnIdentifier,
            right: BasicTypes,
            result: ColumnIdentifier) -> FederatedDataFrame:
        """Privacy-preserving subtraction:
        computes `left` - `right` and stores
        the result in the column `result`.
        Both left and right can be column names,
        or one of it a column name and one a constant.
        Arbitrary subtraction with iterables would allow for
        singling-out attacks and is therefore disallowed.

        Example:
            Assume the dummy data for 'data_cloudnode' looks like this:
            ```
                patient_id  age  weight
            0           1   77      55
            1           2   88      60
            2           3   93      83

            df = FederatedDataFrame('data_cloudnode')
            df = df.sub("weight", 100, "new_weight")
            df.preprocess_on_dummy()
            ```

            returns
            ```
               patient_id  age  weight  new_weight
            0           1   77      55         -45
            1           2   88      60         -40
            2           3   93      83         -17

            df.sub("weight", "age", "new_weight")
            ```

            returns
            ```
               patient_id  age  weight  new_weight
            0           1   77      55         -22
            1           2   88      60         -28
            2           3   93      83         -10
            ```

        Args:
            left: column identifier or constant
            right: column identifier or constant
            result: column name for the new result column

        Returns:
            new instance of the current object with updated graph.

        """
        if isinstance(right, FederatedDataFrame):
            raise TransformationsOperationArgumentTypeNotAllowedException(
                function_name=self.sub.__name__,
                argument_name="right",
                argument_type=type(right),
                supported_argument_types=list(BASIC_TYPES),
            )
        if isinstance(left, FederatedDataFrame):
            raise TransformationsOperationArgumentTypeNotAllowedException(
                function_name=self.sub.__name__,
                argument_name="left",
                argument_type=type(left),
                supported_argument_types=list(BASIC_TYPES),
            )

        return self._add_graph_dst_node_with_edge(
            node_label=f"{result} = {left} - {right}",
            node_command=NodeCommands.subtraction.name,
            node_command_src_key="table",
            node_command_kwargs={"left": left, "right": right, "result": result},
        )

    def mult(
        self, left: BasicTypes,
        right: ColumnIdentifier, result: Optional[ColumnIdentifier] = None
    ) -> FederatedDataFrame:
        """Privacy-preserving multiplication: to a column (`left`)
        multiply another column or constant value (`right`)
        and store the result in `result`.
        Multiplying arbitrary iterables would allow for
        singling out attacks and is therefore disallowed.

        Example:
            Assume the dummy data for 'data_cloudnode' looks like this:
            ```
                patient_id  age  weight
            0           1   77      55
            1           2   88      60
            2           3   93      83

            df = FederatedDataFrame('data_cloudnode')
            df.mult("weight", 2, "new_weight")
            df.preprocess_on_dummy()
            ```

            returns
            ```
                patient_id  age  weight  new_weight
            0           1   77      55         110
            1           2   88      60         120
            2           3   93      83         166

            df.mult("weight", "patient_id", "new_weight")
            ```

            returns
            ```
               patient_id  age  weight  new_weight
            0           1   77      55          55
            1           2   88      60         120
            2           3   93      83         249
            ```

        Args:
            left: a column identifier
            right: a column identifier or constant value
            result: name for the new result column,
                can be set to None to overwrite the left column

        Returns:
            new instance of the current object with updated graph.

        """
        if isinstance(right, FederatedDataFrame):
            raise TransformationsOperationArgumentTypeNotAllowedException(
                function_name=self.mult.__name__,
                argument_name="right",
                argument_type=type(right),
                supported_argument_types=["column identifier"],
            )
        if isinstance(left, FederatedDataFrame):
            raise TransformationsOperationArgumentTypeNotAllowedException(
                function_name=self.mult.__name__,
                argument_name="left",
                argument_type=type(left),
                supported_argument_types=list(BASIC_TYPES),
            )
        if result is None:
            result = left
        return self._add_graph_dst_node_with_edge(
            node_label=f"{result} = {left} * {right}",
            node_command=NodeCommands.mult.name,
            node_command_src_key="table",
            node_command_kwargs={
                "left": left,
                "right": right,
                "result": result,
            },
        )

    def truediv(
        self, left: ColumnIdentifier,
        right: BasicTypes,
        result: Optional[ColumnIdentifier] = None
    ) -> FederatedDataFrame:
        """Privacy-preserving division: divide a column or constant (`left`)
        by another column or constant (`right`)
        and store the result in `result`.
        Dividing by arbitrary iterables would allow for
        singling out attacks and is therefore disallowed.

        Example:
            Assume the dummy data for 'data_cloudnode' looks like this:
            ```
                patient_id  age  weight
            0           1   77      55
            1           2   88      60
            2           3   93      83

            df = FederatedDataFrame('data_cloudnode')
            df.truediv("weight", 2, "new_weight")
            df.preprocess_on_dummy()
            ```

            returns
            ```
                patient_id  age  weight  new_weight
            0           1   77      55        27.5
            1           2   88      60        30.0
            2           3   93      83        41.5

            df.truediv("weight", "patient_id", "new_weight")
            ```

            returns
            ```
               patient_id  age  weight  new_weight
            0           1   77      55   55.000000
            1           2   88      60   30.000000
            2           3   93      83   27.666667
            ```

        Args:
            left: a column identifier
            right: a column identifier or constant value
            result: name for the new result column

        Returns:
            new instance of the current object with updated graph.

        """
        if isinstance(right, FederatedDataFrame):
            raise TransformationsOperationArgumentTypeNotAllowedException(
                function_name=self.truediv.__name__,
                argument_name="right",
                argument_type=type(right),
                supported_argument_types=list(BASIC_TYPES),
            )
        if isinstance(left, FederatedDataFrame):
            raise TransformationsOperationArgumentTypeNotAllowedException(
                function_name=self.truediv.__name__,
                argument_name="left",
                argument_type=type(left),
                supported_argument_types=list(BASIC_TYPES),
            )
        return self._add_graph_dst_node_with_edge(
            node_label=f"{result} = {left} / {right}",
            node_command=NodeCommands.div.name,
            node_command_src_key="table",
            node_command_kwargs={
                "left": left,
                "right": right,
                "result": result,
            },
        )

    def invert(
        self,
        column_to_invert: ColumnIdentifier,
        result_column: Optional[ColumnIdentifier] = None,
    ) -> FederatedDataFrame:
        """Privacy-preserving inversion (~ operator):
        invert column `column_to_invert` and store
        the result in column `result_column`, or leave `result_column` as None
        and overwrite `column_to_invert`.
        Using this form of negation removes the need for __setitem__ functionality
        which is not privacy-preserving.

        Example:
            Assume the dummy data for 'data_cloudnode' looks like this:
            ```
               patient_id  age  weight  death
            0           1   77    55.0   True
            1           2   88    60.0  False
            2           3   23     NaN   True

            df = FederatedDataFrame('data_cloudnode')
            df = df.invert("death", "survival")
            df.preprocess_on_dummy()
            ```

            returns
            ```
               patient_id  age  weight  death  survival
            0           1   77    55.0   True     False
            1           2   88    60.0  False      True
            2           3   23     NaN   True     False
            ```

        Args:
            column_to_invert: column identifier
            result_column: optional name for the new column,
                if not specified, column_to_negate is overwritten

        Returns:
            new instance of the current object with updated graph.

        """
        if isinstance(column_to_invert, FederatedDataFrame):
            raise TransformationsOperationArgumentTypeNotAllowedException(
                function_name=self.invert.__name__,
                argument_name="column_to_invert",
                argument_type=type(column_to_invert),
                supported_argument_types=["column identifier"],
            )

        if result_column is None:
            result_column = column_to_invert

        return self._add_graph_dst_node_with_edge(
            node_label=f"{result_column} = Invert {column_to_invert}",
            node_command=NodeCommands.inv.name,
            node_command_src_key="table",
            node_command_kwargs={
                "column_to_invert": column_to_invert,
                "result_column": result_column,
            },
        )

    def __lt__(self, other: BasicTypes_Fdf) -> FederatedDataFrame:
        """
        Compare a single-column FederatedDataFrame with a constant using the operator '<'
        Example:
            Assume the dummy data for 'data_cloudnode' looks like this:
            ```
               patient_id  age  weight
            0           1   77      55
            1           2   88      60
            2           3   40      50

            df = FederatedDataFrame('data_cloudnode')
            df = df["age"] < df["weight"]
            df.preprocess_on_dummy()
            ```

            returns
            ```
            0    False
            1    False
            2     True
            ```

        Args:
            other: FederatedDataFrame or value to compare with

        Returns:
            single column FederatedDataFrame with computation graph resulting in a
            boolean Series.

        """
        return self._comparison(other, ComparisonType.LESS_THAN)

    def __gt__(self,  other: BasicTypes_Fdf) -> FederatedDataFrame:
        """
        Compare a single-column FederatedDataFrame with a constant using the operator '>'

        Example:
            Assume the dummy data for 'data_cloudnode' looks like this:
            ```
               patient_id  age  weight
            0           1   77      55
            1           2   88      60
            2           3   40      50

            df = FederatedDataFrame('data_cloudnode')
            df = df["age"] > df["weight"]
            df.preprocess_on_dummy()
            ```

            returns
            ```
            0     True
            1     True
            2    False
            ```

        Args:
            other: FederatedDataFrame or value to compare with

        Returns:
            single column FederatedDataFrame with computation graph resulting in a
            boolean Series.


        """
        return self._comparison(other, ComparisonType.GREATER_THAN)

    def __eq__(self,  other: BasicTypes_Fdf) -> FederatedDataFrame:
        """
        Compare a single-column FederatedDataFrame with a constant using the operator '=='

        Example:
            Assume the dummy data for 'data_cloudnode' looks like this:
            ```
               patient_id  age  weight
            0           1   77      55
            1           2   88      60
            2           3   40      40

            df = FederatedDataFrame('data_cloudnode')
            df = df["age"] == df["weight"]
            df.preprocess_on_dummy()
            ```

            returns
            ```
            0    False
            1    False
            2     True
            ```

        Args:
            other: FederatedDataFrame or value to compare with

        Returns:
            single column FederatedDataFrame with computation graph resulting in a
            boolean Series.

        """
        return self._comparison(other, ComparisonType.EQUAL_TO)

    def __le__(self,  other: BasicTypes_Fdf) -> FederatedDataFrame:
        """
        Compare a single-column FederatedDataFrame with a constant using the operator '<='

        Example:
            Assume the dummy data for 'data_cloudnode' looks like this:
            ```
               patient_id  age  weight
            0           1   77      55
            1           2   88      60
            2           3   40      40

            df = FederatedDataFrame('data_cloudnode')
            df = df["age"] <= df["weight"]
            df.preprocess_on_dummy()
            ```

            returns
            ```
            0    False
            1    False
            2     True
            ```

        Args:
            other: FederatedDataFrame or value to compare with

        Returns:
            single column FederatedDataFrame with computation graph resulting in a
            boolean Series.

        """
        return self._comparison(other, ComparisonType.LESS_THAN_OR_EQUAL_TO)

    def __ge__(self,  other: BasicTypes_Fdf) -> FederatedDataFrame:
        """
        Compare a single-column FederatedDataFrame with a constant using the operator '>='

        Example:
            Assume the dummy data for 'data_cloudnode' looks like this:
            ```
               patient_id  age  weight
            0           1   77      55
            1           2   88      60
            2           3   40      40

            df = FederatedDataFrame('data_cloudnode')
            df = df["age"] >= df["weight"]
            df.preprocess_on_dummy()
            ```

            returns
            ```
            0    True
            1    True
            2    True
            ```

        Args:
            other: FederatedDataFrame or value to compare with

        Returns:
            single column FederatedDataFrame with computation graph resulting in a
            boolean Series.

        """
        return self._comparison(other, ComparisonType.GREATER_THAN_OR_EQUAL_TO)

    def __ne__(self,  other: BasicTypes_Fdf) -> FederatedDataFrame:
        """
        Compare a single-column FederatedDataFrame with a constant using the operator '!='

        Example:
            Assume the dummy data for 'data_cloudnode' looks like this:
            ```
               patient_id  age  weight
            0           1   77      55
            1           2   88      60
            2           3   40      40

            df = FederatedDataFrame('data_cloudnode')
            df = df["age"] != df["weight"]
            df.preprocess_on_dummy()
            ```

            returns
            ```
            0     True
            1     True
            2    False
            ```

        Args:
            other: FederatedDataFrame or value to compare with

        Returns:
            single column FederatedDataFrame with computation graph resulting in a
            boolean Series.

        """
        return self._comparison(other, ComparisonType.NOT_EQUAL_TO)

    def _comparison(
        self,
        other: BasicTypes_Fdf,
        comparison_type: ComparisonType,
    ):
        """Generic comparison of a single-column FederatedDataFrame with a constant or
        another single-column FederatedDataFrame.
        Args:
            other: constant or single-column FederatedDataFrame to compare with
            comparison_type: string denoting comparison type
        """
        if not isinstance(comparison_type, ComparisonType):
            if hasattr(comparison_type, "value"):
                operation_type = comparison_type.value
            else:
                operation_type = type(comparison_type)
            raise TransformationsOperationNotAllowedException(
                operation_type=operation_type,
                supported_operation_types=ComparisonType.get_supported_types(),
            )
        comparison_type_value = comparison_type.value
        if isinstance(other, BASIC_TYPES):
            value_to_display = f"'{other}'" if isinstance(other, str) else other
            return self._add_graph_dst_node_with_edge(
                node_label=f"{comparison_type_value} {value_to_display}",
                node_command=NodeCommands.compare_to_value.name,
                node_command_src_key="left",
                node_command_kwargs={
                    "right": other,
                    "comparison_type": comparison_type_value,
                },
            )
        elif isinstance(other, FederatedDataFrame):
            return self._add_graph_dst_node_with_multiple_edges(
                node_label=f"{comparison_type_value} column",
                other_srcs=other,
                node_command=NodeCommands.compare_to_table.name,
                node_command_src_key="left",
                node_command_other_srcs_keys="right",
                node_command_kwargs={
                    "comparison_type": comparison_type_value,
                },
            )

        else:
            raise TransformationsOperationArgumentTypeNotAllowedException(
                function_name=self._comparison.__name__,
                argument_name="other",
                argument_type=type(other),
                supported_argument_types=list(BASIC_TYPES + tuple([FederatedDataFrame])),
            )

    def to_datetime(
        self,
        on_column: Optional[ColumnIdentifier] = None,
        result_column: Optional[ColumnIdentifier] = None,
        errors: str = "raise",
        dayfirst: bool = False,
        yearfirst: bool = False,
        utc: bool = None,
        format: str = None,
        exact: bool = True,
        unit: str = "ns",
        infer_datetime_format: bool = False,
        origin: str = "unix",
    ) -> FederatedDataFrame:
        """Convert the column `on_column` to datetime format.
        Further arguments can be passed to the respective underlying pandas'
        to_datetime function with kwargs.
        Results in a table where `column` is updated,
        no need for the unsafe __setitem__ operation.


        Example:
            Assume the dummy data for 'data_cloudnode' looks like this:
            ```
               patient_id  start_date    end_date
            0           1  "2015-08-01"  "2015-12-01"
            1           2  "2017-11-11"  "2020-11-11"
            2           3  "2020-01-01"         NaN

            df = FederatedDataFrame('data_cloudnode')
            df = df.to_datetime("start_date", "new_start_date")
            df.preprocess_on_dummy()
            ```

            returns
            ```
                   patient_id  start_date    end_date new_start_date
            0           1  "2015-08-01"  "2015-12-01"     2015-08-01
            1           2  "2017-11-11"  "2020-11-11"     2017-11-11
            2           3  "2020-01-01"          NaN      2020-01-01
            ```

        Args:
            on_column: column to convert
            result_column: optional column where the result should be stored,
                defaults to on_column if not specified
            errors: optional argument how to handle errors during parsing,
                "raise": raise an exception upon errors (default),
                "coerce": set value to NaT and continue,
                "ignore": return the input and continue
            dayfirst: optional argument to specify the parse order,
                if True, parses with the day first,
                e.g. 01/02/03 is parsed to 1st February 2003
                defaults to False
            yearfirst: optional argument to specify the parse order,
                if True, parses the year first,
                e.g. 01/02/03 is parsed to 3rd February 2001
                defaults to False
            utc: optional argument to control the time zone,
                if False (default), assume input is in UTC,
                if True, time zones are converted to UTC
            format: optional strftime argument to parse the time,
                e.g. "%d/%m/%Y, defaults to None
            exact: optional argument to control how "format" is used,
                if True (default), an exact format match is required,
                if False, the format is allowed to match anywhere
                    in the target string
            unit: optional argument to denote the unit, defaults to "ns",
                e.g. unit="ms" and origin="unix" calculates the number
                of milliseconds to the unix epoch start
            infer_datetime_format: optional argument to attempt to infer
                the format based on the first (non-NaN) argument when
                set to True and no format is specified, defaults to False
            origin: optional argument to define the reference date,
                numeric values are parsed as number of units defined by
                the "unit" argument since the reference date,
                e.g. "unix" (default) sets the origin to 1970-01-01,
                "julian" (with "unit" set to "D") sets the origin to the
                beginning of the Julian Calendar (January 1st 4713 BC).

        Returns:
            new instance of the current object with updated graph.

        """

        if result_column is None:
            result_column = on_column
        kwargs = {
            "errors": errors,
            "dayfirst": dayfirst,
            "yearfirst": yearfirst,
            "utc": utc,
            "format": format,
            "exact": exact,
            "unit": unit,
            "infer_datetime_format": infer_datetime_format,
            "origin": origin,
        }
        # avoid "ValueError: cannot specify both format and unit" for default values
        if format is None:
            kwargs.pop("format")
        if unit == "ns":
            kwargs.pop("unit")
        return self._add_graph_dst_node_with_edge(
            node_label=f"'{result_column}' = pandas.to_datetime('{on_column}')",
            node_command=NodeCommands.to_datetime.name,
            node_command_src_key="table",
            node_command_kwargs={
                "column": on_column,
                "result": result_column,
                "args": kwargs,
            },
            include_identifier=True,
        )

    def _add_operation_to_graph(self, command: str, args: dict = None):
        """
        Helper function for adding a new operation to the computation graph
        Args:
            command: identifier of the function to be called
            args: function arguments as a dict

        """
        return self._add_graph_dst_node_with_edge(
            node_label=f"Apply {command}",
            node_command=command,
            node_command_src_key="table",
            node_command_kwargs={
                "args": args,
            },
            include_identifier=True,
        )

    def fillna(
        self,
        value: BasicTypes_Fdf,
        on_column: Optional[ColumnIdentifier] = None,
        result_column: Optional[ColumnIdentifier] = None,
    ) -> FederatedDataFrame:
        """
        Fill NaN values with a constant (int, float, string)
        similar to pandas' fillna.
        The following arguments from pandas implementation are not supported:
        `method`, `axis`, `inplace`, `limit`, `downcast`

        Example:
            Assume the dummy data for 'data_cloudnode' looks like this:
            ```
               patient_id   age  weight
            0           1  77.0    55.0
            1           2   NaN    60.0
            2           3  88.0     NaN
            df = FederatedDataFrame('data_cloudnode')
            df2 = df.fillna(7)
            df2.preprocess_on_dummy()
            ```

            returns
            ```
               patient_id   age  weight
            0           1  77.0    55.0
            1           2   7.0    60.0
            2           3  88.0     7.0
            df3 = df.fillna(7, on_column="weight")
            df3.preprocess_on_dummy()
            ```

            returns
            ```
               patient_id   age  weight
            0           1  77.0    55.0
            1           2   NaN    60.0
            2           3  88.0     7.0
            ```

        Args:
            value: value to use for filling up NaNs
            on_column: only operate on the specified column,
                defaults to None, i.e., operate on the entire table
            result_column: if on_column is specified,
                optionally store the result in a new column with this name,
                defaults to None, i.e., overwriting the column

        Returns:
            new instance of the current object with updated graph.

        """
        if isinstance(value, FederatedDataFrame):
            return self._add_graph_dst_node_with_multiple_edges(
                node_label=NodeCommands.fillna_table.name,
                other_srcs=value,
                node_command=NodeCommands.fillna_table.name,
                node_command_src_key="table",
                node_command_other_srcs_keys="value",
            )
        elif not isinstance(value, BASIC_TYPES):
            raise TransformationsOperationArgumentTypeNotAllowedException(
                function_name=self.fillna.__name__,
                argument_name="value",
                argument_type=type(value),
                supported_argument_types=list(BASIC_TYPES),
            )

        label = "fillna"
        if on_column is not None and result_column is None:
            result_column = on_column
        if on_column is not None:
            label = f"{result_column} = fillna {on_column}"

        extra_quotes_if_needed = "'" if isinstance(value, str) else ""
        label += " with " + extra_quotes_if_needed + str(value) + extra_quotes_if_needed
        return self._add_graph_dst_node_with_edge(
            node_label=label,
            node_command=NodeCommands.fillna.name,
            node_command_src_key="table",
            node_command_kwargs={
                "value": value,
                "column": on_column,
                "result": result_column,
            },
        )

    def dropna(
        self,
        axis: Union[int, str] = 0,
        how: str = None,
        thresh: Optional[int] = None,
        subset: Union[ColumnIdentifier, List[ColumnIdentifier], None] = None,
    ) -> FederatedDataFrame:
        """Drop Nan values from the table with arguments like for pandas' dropna.

        Example:
            Assume the dummy data for 'data_cloudnode' looks like this:
            ```
               patient_id   age  weight
            0           1  77.0    55.0
            1           2  88.0     NaN
            2           3   NaN     NaN
            df = FederatedDataFrame('data_cloudnode')
            df2 = df.dropna()
            df2.preprocess_on_dummy()
            ```

            returns
            ```
                patient_id   age  weight
            0           1  77.0    55.0
            df3 = df.dropna(axis=0, subset=["age"])
            df3.preprocess_on_dummy()
            ```
            returns
            ```
               patient_id   age  weight
            0           1  77.0    55.0
            1           2  88.0     NaN
            ```

        Args:
            axis: axis to apply this operation to, defaults to zero
            how: determine if row or column is removed from FederatedDataFrame,
                when we have at least one NA or all NA, defaults to "any".
                ‘any’ : If any NA values are present, drop that row or column.
                ‘all’ : If all values are NA, drop that row or column.
            thresh: optional - require that many non-NA values to drop,
                defaults to None
            subset: optional - use only a subset of columns,
                defaults to None, i.e., operate on the entire data frame,
                subset of rows is not permitted for privacy reasons.

        Returns:
            new instance of the current object with updated graph.

        """
        if subset is not None:
            if axis == 1 or axis == "columns":
                raise PrivacyException(
                    "Considering only a subset of rows "
                    "for dropping is not privacy preserving."
                )
        return self._add_operation_to_graph(
            NodeCommands.dropna.name,
            args={
                "axis": axis,
                "how": how,
                "thresh": thresh,
                "subset": subset,
            },
        )

    def isna(
        self,
        on_column: Optional[ColumnIdentifier] = None,
        result_column: Optional[ColumnIdentifier] = None,
    ) -> FederatedDataFrame:
        """
        Checks if an entry is null for given columns or FederatedDataFrame and sets
        boolean value accordingly in the result column.

        Example:
            Assume the dummy data for 'data_cloudnode' looks like this:
            ```
                patient_id   age  weight
            0           1  77.0    55.0
            1           2  88.0     NaN
            2           3   NaN     NaN
            df = FederatedDataFrame('data_cloudnode')
            df2 = df.isna()
            df2.preprocess_on_dummy()
            ```
            returns
            ```
                patient_id    age  weight
            0       False  False   False
            1       False  False   False
            2       False   True    True
            df3 = df.isna("age", "na_age")
            df3.preprocess_on_dummy()
            ```
            returns
            ```
                patient_id   age  weight na_age
            0           1  77.0    55.0  False
            1           2  88.0     NaN  False
            2           3   NaN     NaN  True
            ```

        Args:
            on_column: column name which is being checked
            result_column: optional result columns. If specified, a new column is added to
                the FederatedDataFrame, otherwise on_column is overwritten.

        Returns:
            new instance of the current object with updated graph.

        """
        label = "isna"
        if on_column is not None and result_column is None:
            result_column = on_column
        if on_column is not None:
            label = f"{result_column} = isna {on_column}"
        return self._add_graph_dst_node_with_edge(
            node_label=label,
            node_command=NodeCommands.isna.name,
            node_command_src_key="table",
            node_command_kwargs={
                "column": on_column,
                "result": result_column,
            },
        )

    def astype(
        self,
        dtype: Union[type, str],
        on_column: Optional[ColumnIdentifier] = None,
        result_column: Optional[ColumnIdentifier] = None,
    ) -> FederatedDataFrame:
        """Convert the entire table to the given datatype
        similarly to pandas' astype.
        The following arguments from pandas implementation are not supported:
        `copy`, `errors`
        Optionally arguments not present in pandas implementation:
        `on_column` and `result_column`: give a column to which the astype function
        should be applied.

        Example:
            Assume the dummy data for 'data_cloudnode' looks like this:
            ```
               patient_id  age  weight
            0           1   77    55.4
            1           2   88    60.0
            2           3   99    65.5
            df = FederatedDataFrame('data_cloudnode')
            df2 = df.astype(str)
            df2.preprocess_on_dummy()
            ```
            returns
            ```
               patient_id   age  weight
            0         "1"  "77"  "55.4"
            1         "2"  "88"  "60.0"
            2         "3"  "99"  "65.5"

            df3 = df.astype(float, on_column="age")

               patient_id   age  weight
            0           1  77.0    55.4
            1           2  88.0    60.0
            2           3  99.0    65.5
            ```

        Args:
            dtype: type to convert to
            on_column: optional column to convert, defaults to None,
                i.e., the entire FederatedDataFrame is converted
            result_column: optional result column if on_column is specified,
                defaults to None, i.e., the on_column is overwritten

        Returns:
            new instance of the current object with updated graph.
        """
        if on_column is not None and result_column is None:
            result_column = on_column
        if isinstance(dtype, type):
            dtype = dtype.__name__

        return self._add_graph_dst_node_with_edge(
            node_label=f"astype {dtype}",
            node_command=NodeCommands.astype.name,
            node_command_src_key="table",
            node_command_kwargs={
                "dtype": dtype,
                "column": on_column,
                "result": result_column,
            },
        )

    def merge(
        self,
        right: FederatedDataFrame,
        how: Literal["left", "right", "outer", "inner", "cross"] = "inner",
        on: Optional[ColumnIdentifier] = None,
        left_on: Optional[ColumnIdentifier] = None,
        right_on: Optional[ColumnIdentifier] = None,
        left_index: bool = False,
        right_index: bool = False,
        sort: bool = False,
        suffixes: Sequence[Optional[str]] = ("_x", "_y"),
        copy: bool = True,
        indicator: bool = False,
        validate: Optional[str] = None,
    ) -> FederatedDataFrame:
        """
        Merges two FederatedDataFrames. When the preprocessing privacy guard is enabled,
        merges are only possible as the first preprocessing step. See also
        [pandas documentation](https://pandas.pydata.org/docs/reference/api/
        pandas.merge.html).

        Example:
            Assume the dummy data for 'data_cloudnode' looks like this:
            ```
            patients.csv
                id  age  death
            0  423   34      1
            1  561   55      0
            2  917   98      1
            insurance.csv
                id insurance
            0  561        TK
            1  917       AOK
            2  123      None
            patients = FederatedDataFrame('data_cloudnode',
                filename_in_zip='patients.csv')
            insurance = FederatedDataFrame('data_cloudnode',
                filename_in_zip="insurance.csv")
            merge1 = patients.merge(insurance, left_on="id", right_on="id", how="left")
            merge1.preprocess_on_dummy()
            returns
                id  age  death insurance
            0  423   34      1       NaN
            1  561   55      0        TK
            2  917   98      1       AOK
            merge2 = patients.merge(insurance, left_on="id", right_on="id", how="right")
            merge2.preprocess_on_dummy()
            ```
            returns
            ```
                id   age  death insurance
            0  561  55.0    0.0        TK
            1  917  98.0    1.0       AOK
            2  123   NaN    NaN      None
            ```


            ```
            merge3 = patients.merge(insurance, left_on="id", right_on="id", how="outer")
            merge3.preprocess_on_dummy()
            ```
            returns
            ```
                id   age  death insurance
            0  423  34.0    1.0       NaN
            1  561  55.0    0.0        TK
            2  917  98.0    1.0       AOK
            3  123   NaN    NaN      None
            ```

        Args:
            right: the other FederatedDataFrame to merge with
            how: type of merge ("left", "right", "outer", "inner", "cross")
            on: column or index to join on, that is available on both sides
            left_on: column or index to join the left FederatedDataFrame
            right_on: column or index to join the right FederatedDataFrame
            left_index: use the index of the left FederatedDataFrame
            right_index: use the index of the right FederatedDataFrame
            sort: Sort the join keys in the resulting FederatedDataFrame
            suffixes: A sequence of two strings. If columns overlap, these suffixes are
                appended to column names
                defaults to ("_x", "_y"), i.e., if you have the column "id" in both
                tables, the left table's id column will be renamed to "id_x"
                and the right to "id_y".
            copy: If False, avoid copy if possible.
            indicator: If true, a column "_merge" will be added to the resulting
                FederatedDataFrame that indicates the origin of a row
            validate: “one_to_one”/“one_to_many”/“many_to_one”/“many_to_many”. If set, a
                check is performed if the specified type is met.

        Returns:
            new instance of the current object with updated graph.

        Raises:
            PrivacyException: if merges are unsecure due the operations done before

        """
        node_label_args = list()
        for arg_name, arg_value in {
            "left_on": left_on,
            "right_on": right_on,
            "on": on,
        }.items():
            if arg_value:
                node_label_args.append(f"{arg_name}='{arg_value}'")
        node_label_args = ", ".join(node_label_args) or f"on={on}"
        return self._add_graph_dst_node_with_multiple_edges(
            node_label=f"Merge with {node_label_args}",
            other_srcs=right,
            node_command=NodeCommands.merge.name,
            node_command_src_key="left",
            node_command_other_srcs_keys="right",
            node_command_kwargs={
                "how": how,
                "on": on,
                "left_on": left_on,
                "right_on": right_on,
                "left_index": left_index,
                "right_index": right_index,
                "sort": sort,
                "suffixes": suffixes,
                "copy": copy,
                "indicator": indicator,
                "validate": validate,
            },
        )

    def concat(
        self,
        other: FederatedDataFrame,
        join: Literal["inner", "outer"] = "outer",
        ignore_index: bool = True,
        verify_integrity: bool = False,
        sort: bool = False,
    ) -> FederatedDataFrame:
        """
        Concatenate two FederatedDataFrames vertically.
        The following arguments from pandas implementation are not supported:
        `keys`, `levels`, `names`, `verify_integrity`, `copy`.
        Args:
            other: the other FederatedDataFrame to concatenate with
            join: type of join to perform ('inner' or 'outer'), defaults to 'outer'
            ignore_index: whether to ignore the index, defaults to True
            verify_integrity: whether to verify the integrity of the result, defaults
                to False
            sort: whether to sort the result, defaults to False
        """

        return self._add_graph_dst_node_with_multiple_edges(
            node_label="Concatenate",
            other_srcs=other,
            node_command=NodeCommands.concat.name,
            node_command_src_key="table1",
            node_command_other_srcs_keys="table2",
            node_command_kwargs={
                "ignore_index": ignore_index,
                "join": join,
                "verify_integrity": verify_integrity,
                "sort": sort,
            },
        )

    def rename(
        self,
        columns: Dict[ColumnIdentifier, ColumnIdentifier],
    ) -> FederatedDataFrame:
        """
        Rename column(s) similarly to pandas' rename.
        The following arguments from pandas implementation are not supported:
        `mapper`,`index`, `axis`, `copy`, `inplace`, `level`, `errors`


        Example:
            Assume the dummy data for 'data_cloudnode' looks like this:
            ```
               patient_id  age  weight
            0           1   77    55.4
            1           2   88    60.0
            2           3   99    65.5
            df = FederatedDataFrame('data_cloudnode')
            df = df.rename({"patient_id": "patient_id_new", "age": "age_new"})
            df.preprocess_on_dummy()
            ```
            returns
            ```
               patient_id_new  age_new  weight
            0           1           77    55.4
            1           2           88    60.0
            2           3           99    65.5
            ```

        Args:
            columns: dict containing the remapping of old names to new names

        Returns:
            new instance of the current object with updated graph
        """
        if not isinstance(columns, dict):
            raise TransformationsOperationArgumentTypeNotAllowedException(
                function_name=self.rename.__name__,
                argument_name="columns",
                argument_type=type(columns),
                supported_argument_types=[dict],
            )
        else:
            return self._add_graph_dst_node_with_edge(
                node_label=f"Rename using {columns}",
                node_command=NodeCommands.rename.name,
                node_command_kwargs={
                    # adding columns as dict will convert all dict keys as strings when
                    # the json is serialized with dumps. Converting it to a list of
                    # tuples preserves the original datatype of the dict keys
                    "mapping": list(columns.items()),
                },
            )

    def drop_column(
        self, column: Union[ColumnIdentifier, List[ColumnIdentifier]]
    ) -> FederatedDataFrame:
        """Remove the given column from the table.

        Example:
            Assume the dummy data for 'data_cloudnode' looks like this:
            ```
            patient_id  age  weight
            0           1   77      55
            1           2   88      60
            2           3   93      83
            df = FederatedDataFrame('data_cloudnode')
            df = df.drop_column("weight")
            df.preprocess_on_dummy()
            ```
            returns
            ```
            patient_id  age
            0           1   77
            1           2   88
            2           3   93
            ```

        Args:
            column: column name or list of column names to drop

        Returns:
            new instance of the current object with updated graph.
        """

        return self._add_graph_dst_node_with_edge(
            node_label=f"drop {column}",
            node_command=NodeCommands.drop_column.name,
            node_command_src_key="table",
            node_command_kwargs={
                "column": column,
            },
        )

    def sample(
        self,
        n: Optional[int] = None,
        frac: Optional[float] = None,
        replace: bool = False,
        random_state: Optional[int] = None,
        ignore_index: bool = False,
    ):
        """Sample the data frame based on a given mask and percentage.
        Only one of `n` (number of samples) or `frac` (fraction of the data)
        can be specified. The following arguments from pandas implementation are not
        supported: `weights` and `axis`.

        Args:
            n: number of samples to take
            frac: fraction of the data to sample between 0 and 1
            replace: whether to sample with replacement
            random_state: seed for the random number generator
            ignore_index: whether to ignore the index when sampling
        """
        if (n is not None and frac is not None) or (n is None and frac is None):
            raise ValueError("Please enter a value for `frac` OR `n`, not both")

        if frac and (frac <= 0 or frac > 1):
            raise ValueError("Please enter a value between 0 and 1 for `frac`")

        return self._add_operation_to_graph(
            command=NodeCommands.sample.name,
            args={
                "n": n,
                "frac": frac,
                "replace": replace,
                "random_state": random_state,
                "ignore_index": ignore_index,
            },
        )

    def __add__(
        self,
        other: BasicTypes_Fdf,
    ) -> FederatedDataFrame:
        """
        Arithmetic operator, which adds a constant value or a single column
        FederatedDataFrame to a single column FederatedDataFrame. This operator is
        useful only in combination with setitem. In a privacy preserving mode use
        the `add` function instead.

        Example:
            Assume the dummy data for 'data_cloudnode' looks like this:
            ```
                patient_id  age  weight
            0           1   77      55
            1           2   88      60
            2           3   93      83
            df = FederatedDataFrame('data_cloudnode')
            df["new_weight"] = df["weight"] + 100
            df.preprocess_on_dummy()
            ```
            returns
            ```
               patient_id  age  weight  new_weight
            0           1   77      55         155
            1           2   88      60         160
            2           3   93      83         183
            ```

            ```
            df["new_weight"] = df["weight"] + df["age"]
            ```
            returns
            ```
               patient_id  age  weight  new_weight
            0           1   77      55         132
            1           2   88      60         148
            2           3   93      83         176
            ```


        Args:
            other: constant value or a single column FederatedDataFrame to add.

        Returns:
            new instance of the current object with updated graph.

        """
        if isinstance(other, FederatedDataFrame):
            # We want to add two columns
            return self._add_graph_dst_node_with_multiple_edges(
                node_label="Sum",
                other_srcs=other,
                node_command=NodeCommands.add_table.name,
                node_command_src_key="summand1",
                node_command_other_srcs_keys="summand2",
            )
        elif isinstance(other, BASIC_TYPES):
            return self._add_graph_dst_node_with_edge(
                node_label=f"Add a value '{other}'",
                node_command=NodeCommands.add_number.name,
                node_command_src_key="summand1",
                node_command_kwargs={
                    "summand2": other,
                },
            )
        else:
            raise TransformationsOperationArgumentTypeNotAllowedException(
                function_name=self.__add__.__name__,
                argument_name="other",
                argument_type=type(other),
                supported_argument_types=list(BASIC_TYPES + tuple([FederatedDataFrame])),
            )

    def __radd__(self, other: BasicTypes_Fdf) -> FederatedDataFrame:
        """
        Arithmetic operator, which adds a constant value or a single column
        FederatedDataFrame to a single column FederatedDataFrame from right. This operator
        is useful only in combination with setitem. In a privacy preserving mode use
        the `add` function instead.

        Example:
            Assume the dummy data for 'data_cloudnode' looks like this:
            ```
                patient_id  age  weight
            0           1   77      55
            1           2   88      60
            2           3   93      83
            df = FederatedDataFrame('data_cloudnode')
            df["new_weight"] = 100 + df["weight"]
            df.preprocess_on_dummy()
            ```
            returns
            ```
               patient_id  age  weight  new_weight
            0           1   77      55         155
            1           2   88      60         160
            2           3   93      83         183
            ```


        Args:
            other: constant value or a single column FederatedDataFrame to add.

        Returns:
            new instance of the current object with updated graph.
        """
        return self.__add__(other)

    def __neg__(self) -> FederatedDataFrame:
        """
        Logical operator, which negates values of a single column
        FederatedDataFrame. This operator is
        useful only in combination with setitem. In a privacy preserving mode use
        the `neg` function instead.

        Example:
            Assume the dummy data for 'data_cloudnode' looks like this:
            ```
                patient_id  age  weight
            0           1   77      55
            1           2   88      60
            2           3   93      83
            df = FederatedDataFrame('data_cloudnode')
            df["neg_age"] = - df["age"]
            df.preprocess_on_dummy()
            ```
            returns
            ```
                patient_id  age  weight  neg_age
            0           1   77      55      -77
            1           2   88      60      -88
            2           3   93      83      -93
            ```

        Returns:
            new instance of the current object with updated graph.

        """
        return self._add_graph_dst_node_with_edge(
            node_label="Negate",
            node_command=NodeCommands.neg.name,
            node_command_src_key="table",
        )

    def __invert__(self) -> FederatedDataFrame:
        """
        Logical operator, which inverts bool values (known as tilde in pandas, ~).

        Example:
            Assume the dummy data for 'data_cloudnode' looks like this:
            ```
               patient_id  age  weight  death
            0           1   77    55.0   True
            1           2   88    60.0  False
            2           3   23     NaN   True
            df = FederatedDataFrame('data_cloudnode')
            df["survival"] = ~df["death"]
            df.preprocess_on_dummy()
            ```
            returns
            ```
               patient_id  age  weight  death  survival
            0           1   77    55.0   True     False
            1           2   88    60.0  False      True
            2           3   23     NaN   True     False
            ```

        Returns:
            new instance of the current object with updated graph.
        """
        return self._add_graph_dst_node_with_edge(
            node_label="~",
            node_command=NodeCommands.invert.name,
            node_command_src_key="table",
        )

    def __sub__(self, other: BasicTypes_Fdf) -> FederatedDataFrame:
        """
        Arithmetic operator, which subtracts a constant value or a single column
        FederatedDataFrame to a single column FederatedDataFrame. This operator is
        useful only in combination with setitem. In a privacy preserving mode use
        the `sub` function instead.

        Example:
            Assume the dummy data for 'data_cloudnode' looks like this:
            ```
                patient_id  age  weight
            0           1   77      55
            1           2   88      60
            2           3   93      83
            df = FederatedDataFrame('data_cloudnode')
            df["new_weight"] = df["weight"] - 100
            df.preprocess_on_dummy()
            ```
            returns
            ```
               patient_id  age  weight  new_weight
            0           1   77      55         -45
            1           2   88      60         -40
            2           3   93      83         -17
            ```

            ```
            df["new_weight"] = df["weight"] - df["age"]
            ```
            returns
            ```
               patient_id  age  weight  new_weight
            0           1   77      55         -22
            1           2   88      60         -28
            2           3   93      83         -10
            ```


        Args:
            other: constant value or a single column FederatedDataFrame to subtract.

        Returns:
            new instance of the current object with updated graph.
        """
        return self.__add__(other.__neg__())

    def __rsub__(self, other: BasicTypes_Fdf) -> FederatedDataFrame:
        """
        Arithmetic operator, which subtracts a single column FederatedDataFrame from a
        constant value or a single column FederatedDataFrame. This operator is
        useful only in combination with setitem. In a privacy preserving mode use
        the `sub` function instead.

        Args:
            other: constant value or a single column FederatedDataFrame from which to
                subtract.

        Returns:
            new instance of the current object with updated graph.

        Example:
            Assume the dummy data for 'data_cloudnode' looks like this:
            ```
                patient_id  age  weight
            0           1   77      55
            1           2   88      60
            2           3   93      83

            df = FederatedDataFrame('data_cloudnode')
            df["new_weight"] = 100 - df["weight"]
            df.preprocess_on_dummy()
            ```

            returns
            ```
               patient_id  age  weight  new_weight
            0           1   77      55         45
            1           2   88      60         40
            2           3   93      83         17
            ```
        """

        return self.__neg__().__add__(other)

    def __truediv__(
        self,
        other: Union[(FederatedDataFrame, int, float, bool)],
    ) -> FederatedDataFrame:
        """
        Arithmetic operator, which divides FederatedDataFrame by a constant or
        another FederatedDataFrame.

        Example:
            Assume the dummy data for 'data_cloudnode' looks like this:
            ```
                patient_id  age  weight
            0           1   77      55
            1           2   88      60
            2           3   93      83
            df = FederatedDataFrame('data_cloudnode')
            df["new_weight"] = df["weight"] / 2
            df.preprocess_on_dummy()
            ```
            returns
            ```
                patient_id  age  weight  new_weight
            0           1   77      55        27.5
            1           2   88      60        30.0
            2           3   93      83        41.5
            ```

            ```
            df["new_weight"] = df["weight"] / df["patient_id"]
            ```
            returns
            ```
               patient_id  age  weight  new_weight
            0           1   77      55   55.000000
            1           2   88      60   30.000000
            2           3   93      83   27.666667
            ```


        Args:
            other: constant value or another FederatedDataFrame to divide by.

        Returns:
            new instance of the current object with updated graph.
        """
        if isinstance(other, FederatedDataFrame):
            # We want to add two columns
            return self._add_graph_dst_node_with_multiple_edges(
                node_label="dividend / divisor",
                other_srcs=other,
                node_command=NodeCommands.divide.name,
                node_command_src_key="dividend",
                node_command_other_srcs_keys="divisor",
                edges_labels={other._uuid: "divisor"},
            )
        elif isinstance(other, (int, float, bool)):
            return self._add_graph_dst_node_with_edge(
                node_label=f"dividend / {other}",
                node_command=NodeCommands.divide_by_constant.name,
                node_command_src_key="dividend",
                node_command_kwargs={
                    "divisor": other,
                },
            )
        else:
            raise TransformationsOperationArgumentTypeNotAllowedException(
                function_name=self.__truediv__.__name__,
                argument_name="other",
                argument_type=type(other),
                supported_argument_types=[FederatedDataFrame, int, float, bool],
            )

    def __mul__(
        self,
        other: Union[(FederatedDataFrame, int, float, bool)],
    ) -> FederatedDataFrame:
        """
        Arithmetic operator, which multiplies FederatedDataFrame by a constant or
        another FederatedDataFrame.

        Example:
            Assume the dummy data for 'data_cloudnode' looks like this:
            ```
                patient_id  age  weight
            0           1   77      55
            1           2   88      60
            2           3   93      83
            df = FederatedDataFrame('data_cloudnode')
            df["new_weight"] = df["weight"] * 2
            df.preprocess_on_dummy()
            ```
            returns
            ```
                patient_id  age  weight  new_weight
            0           1   77      55         110
            1           2   88      60         120
            2           3   93      83         166
            ```

            ```
            df["new_weight"] = df["weight"] * df["patient_id"]
            ```
            returns
            ```
               patient_id  age  weight  new_weight
            0           1   77      55          55
            1           2   88      60         120
            2           3   93      83         249
            ```

        Args:
            other: constant value or another FederatedDataFrame to multiply by.

        Returns:
            new instance of the current object with updated graph.


        """
        if isinstance(other, FederatedDataFrame):
            # We want to add two columns
            return self._add_graph_dst_node_with_multiple_edges(
                node_label="multiplicand * multiplier",
                other_srcs=other,
                node_command=NodeCommands.multiply.name,
                node_command_src_key="multiplicand",
                node_command_other_srcs_keys="multiplier",
                edges_labels={other._uuid: "multiplier"},
            )
        elif isinstance(other, (int, float, bool)):
            return self._add_graph_dst_node_with_edge(
                node_label=f"multiplicand / {other}",
                node_command=NodeCommands.multiply_by_constant.name,
                node_command_src_key="multiplicand",
                node_command_kwargs={
                    "multiplier": other,
                },
            )
        else:
            raise TransformationsOperationArgumentTypeNotAllowedException(
                function_name=self.__mul__.__name__,
                argument_name="other",
                argument_type=type(other),
                supported_argument_types=[FederatedDataFrame, int, float, bool],
            )

    def __rmul__(
        self,
        other: Union[(FederatedDataFrame, int, float, bool)],
    ) -> FederatedDataFrame:
        """
        Arithmetic operator, which multiplies FederatedDataFrame by a constant or
        another FederatedDataFrame.

        Example:
            Assume the dummy data for 'data_cloudnode' looks like this:
            ```
                patient_id  age  weight
            0           1   77      55
            1           2   88      60
            2           3   93      83
            df = FederatedDataFrame('data_cloudnode')
            df["new_weight"] = 2 * df["weight"] * 2
            df.preprocess_on_dummy()
            ```
            returns
            ```
                patient_id  age  weight  new_weight
            0           1   77      55         110
            1           2   88      60         120
            2           3   93      83         166
            ```

        Args:
            other: constant value or another FederatedDataFrame to multiply by.
        Returns:
            new instance of the current object with updated graph.
        """
        return self.__mul__(other=other)

    def __and__(self, other: Union[FederatedDataFrame, bool, int]) -> FederatedDataFrame:
        """
        Logical operator, which conjuncts values of a single column
        FederatedDataFrame with a constant or another single column
        FederatedDataFrame.

        Example:
            Assume the dummy data for 'data_cloudnode' looks like this:
            ```
               patient_id  age  death  infected
            0           1   77      1         1
            1           2   88      0         1
            2           3   40      1         0
            df = FederatedDataFrame('data_cloudnode')
            df = df["death"] & df["infected"]
            df.preprocess_on_dummy()
            ```
            returns
            ```
            0    1
            1    0
            2    0
            ```
        Args:
            other: constant value or another FederatedDataFrame to logically conjunct

        Returns:
            new instance of the current object with updated graph.

        """
        if isinstance(other, FederatedDataFrame):
            # We want to and-conjunct two columns
            return self._add_graph_dst_node_with_multiple_edges(
                node_label="And",
                other_srcs=other,
                node_command=NodeCommands.logical_conjunction_table.name,
                node_command_src_key="left",
                node_command_other_srcs_keys="right",
                node_command_kwargs={"conjunction_type": "and"},
            )
        elif isinstance(other, (bool, int)):
            return self._add_graph_dst_node_with_edge(
                node_label=f"And '{other}'",
                node_command=NodeCommands.logical_conjunction_number.name,
                node_command_src_key="left",
                node_command_kwargs={"right": other, "conjunction_type": "and"},
            )
        else:
            raise TransformationsOperationArgumentTypeNotAllowedException(
                function_name=self.__and__.__name__,
                argument_name="other",
                argument_type=type(other),
                supported_argument_types=[FederatedDataFrame, bool],
            )

    def __or__(self, other: Union[FederatedDataFrame, bool, int]) -> FederatedDataFrame:
        """
        Logical operator, which conjuncts values of a single column
        FederatedDataFrame with a constant or another single column
        FederatedDataFrame.

        Example:
            Assume the dummy data for 'data_cloudnode' looks like this:
            ```
               patient_id  age  death  infected
            0           1   77      1         1
            1           2   88      0         1
            2           3   40      1         0
            df = FederatedDataFrame('data_cloudnode')
            df = df["death"] | df["infected"]
            df.preprocess_on_dummy()
            ```
            returns
            ```
            0    1
            1    1
            2    1
            ```

        Args:
            other: constant value or another FederatedDataFrame to logically conjunct

        Returns:
            new instance of the current object with updated graph.
        """
        if isinstance(other, FederatedDataFrame):
            # We want to or-conjunct two columns
            return self._add_graph_dst_node_with_multiple_edges(
                node_label="Or",
                other_srcs=other,
                node_command=NodeCommands.logical_conjunction_table.name,
                node_command_src_key="left",
                node_command_other_srcs_keys="right",
                node_command_kwargs={"conjunction_type": "or"},
            )
        elif isinstance(other, (bool, int)):
            return self._add_graph_dst_node_with_edge(
                node_label=f"Or '{other}'",
                node_command=NodeCommands.logical_conjunction_number.name,
                node_command_src_key="left",
                node_command_kwargs={"right": other, "conjunction_type": "or"},
            )
        else:
            raise TransformationsOperationArgumentTypeNotAllowedException(
                function_name=self.__or__.__name__,
                argument_name="other",
                argument_type=type(other),
                supported_argument_types=[FederatedDataFrame, bool],
            )

    def str_contains(self, pattern: str) -> FederatedDataFrame:
        """
        Checks if string values of single column FederatedDataFrame contain
        pattern. Typical usage
        `federated_dataframe[column].str.contains(pattern)`

        Example:
            Assume the dummy data for 'data_cloudnode' looks like this:
            ```
               patient_id  age  weight   race
            0           1   77      55  white
            1           2   88      60  black
            2           3   93      83  asian
            df = FederatedDataFrame('data_cloudnode')
            df = df["race"].str.contains("a")
            df.preprocess_on_dummy()
            ```
            returns
            ```
            0    False
            1     True
            2     True
            ```

        Args:
            pattern: pattern string to check for
        Returns:
            new instance of the current object with updated graph.
        """
        return self._add_graph_dst_node_with_edge(
            node_label=f"contains {pattern}",
            node_command=NodeCommands.str_contains.name,
            node_command_src_key="table",
            node_command_kwargs={
                "pattern": pattern,
            },
        )

    def str_len(self) -> FederatedDataFrame:
        """
        Computes string length for each entry. Typical usage
        `federated_dataframe[column].str.len()`

        Example:
            Assume the dummy data for 'data_cloudnode' looks like this:
            ```
               patient_id  age  weight   race
            0           1   77      55      w
            1           2   88      60     bl
            2           3   93      83  asian
            df = FederatedDataFrame('data_cloudnode')
            df = df["race"].str.len()
            df.preprocess_on_dummy()
            ```
            returns
            ```
            0    1
            1    2
            2    5
            ```

        Returns:
            new instance of the current object with updated graph.
        """
        return self._add_graph_dst_node_with_edge(
            node_label="length",
            node_command=NodeCommands.str_len.name,
            node_command_src_key="table",
        )

    def dt_datetime_like_properties(self, datetime_like_property: Union[
            DatetimeProperties, TimedeltaProperties]) -> FederatedDataFrame:
        """
        Checks if a property of datetime-like object can be applied to a column
        of FederatedDataFrame. Typical usage
        `federated_dataframe[column].dt.days`

        Example:
            Assume the dummy data for 'data_cloudnode' looks like this:
            ```
               patient_id  start_date    end_date
            0           1  2015-08-01  2015-12-01
            1           2  2017-11-11  2020-11-11
            2           3  2020-01-01  2022-06-16
            df = FederatedDataFrame('data_cloudnode')
            df = df.to_datetime("start_date")
            df = df.to_datetime("start_date")
            df = df.sub("end_date", "start_date", "duration")
            df = df["duration"] = df["duration"].dt.days - 5
            df.preprocess_on_dummy()
            ```
            returns
            ```
               patient_id start_date   end_date  duration
            0           1 2015-08-01 2015-12-01       117
            1           2 2017-11-11 2020-11-11      1091
            2           3 2020-01-01 2022-06-16       892
            ```

        Args:
            datetime_like_property: datetime-like (.dt) property to be accessed
        Returns:
            new instance of the current object with updated graph.
        """
        return self._add_graph_dst_node_with_edge(
            node_label=f"Get dt.{datetime_like_property}",
            node_command=NodeCommands.datetime_like_properties.name,
            node_command_src_key="table",
            node_command_kwargs={"datetime_like_property": datetime_like_property},
        )

    def sort_values(
        self,
        by: Union[ColumnIdentifier, List[ColumnIdentifier]],
        axis: Union[int, str] = 0,
        ascending: bool = True,
        kind: str = "quicksort",
        na_position: str = "last",
        ignore_index: bool = False,
    ) -> FederatedDataFrame:
        """Sort values, similar to pandas' sort_values.
        The following arguments from pandas implementation are not supported:
        `key` - we do not support the `key` argument, as that could be an arbitrary
        function.

        Example:
            Assume the dummy data for 'data_cloudnode' looks like this:
            ```
               patient_id  age  weight
            0           1   77    55.0
            1           2   88    60.0
            2           3   93    83.0
            3           4   18     NaN
            df = FederatedDataFrame('data_cloudnode')
            df = df.sort_values(by="weight", axis="index", ascending=False)
            df.preprocess_on_dummy()
            ```
            returns
            ```
               patient_id  age  weight
            2           3   93    83.0
            1           2   88    60.0
            0           1   77    55.0
            3           4   18     NaN
            ```

        Args:
            by: column name or list of column names to sort by
            axis: axis to be sorted:
                0 or "index" means sort by index, thus, by contains column labels
                1 or "column" means sort by column, thus, by contains index labels
            ascending: defaults to ascending sorting,
                but can be set to False for descending sorting
            kind: defaults to the `quicksort` sorting algorithm;
                `mergesort`, `heapsort` and `stable` are available as well
            na_position: defaults to sorting NaNs to the end,
                set to "first" to put them in the beginning
            ignore_index: defaults to false,
                otherwise, the resulting axis will be labelled 0, 1, ... length-1

        Returns:
            new instance of the current object with updated graph.

        """
        return self._add_operation_to_graph(
            command=NodeCommands.sort_values.name,
            args={
                "by": by,
                "axis": axis,
                "ascending": ascending,
                "kind": kind,
                "na_position": na_position,
                "ignore_index": ignore_index,
            },
        )

    def isin(self, values: BasicTypes_Fdf) -> FederatedDataFrame:
        """
        Whether each element in the data is contained in values,
        similar to pandas' isin.

        Example:
            Assume the dummy data for 'data_cloudnode' looks like this:
            ```
            patients.csv:
               patient_id  age  weight
            0           1   77    55.0
            1           2   88    60.0
            2           3   93    83.0
            3           4   18     NaN
            other.csv:
               patient_id  age  weight
            0           1   77    55.0
            1           2   88    60.0
            2           7   33    93.0
            3           8   66     NaN
            df = FederatedDataFrame('data_cloudnode',
                filename_in_zip='patients.csv')
            df = df.isin(values = {"age": [77], "weight": [55]})
            df.preprocess_on_dummy()
            ```
            returns
            ```
               patient_id    age  weight
            0       False   True    True
            1       False  False   False
            2       False  False   False
            3       False  False   False
            ```

            ```
            df_other = FederatedDataFrame('data_cloudnode',
                filename_in_zip='other.csv')
            df = df.isin(df_other)
            df.preprocess_on_dummy()
            ```
            returns
            ```
               patient_id    age  weight
            0        True   True    True
            1        True   True    True
            2       False  False   False
            3       False  False   False
            ```

        Args:
            values: iterable, dict or FederatedDataFrame to check against.
                Returns True at each location if all the labels match,

                * if values is a Series, that's the index,
                * if values is a dict, the keys are expected to be column names,
                * if values is a FederatedDataFrame, both index and column labels must
                  match.

        Returns:
            new instance of the current object with updated graph.

        """
        if isinstance(values, FederatedDataFrame):
            return self._add_graph_dst_node_with_multiple_edges(
                node_label="isin",
                other_srcs=values,
                node_command=NodeCommands.isin.name,
                node_command_src_key="table",
                node_command_other_srcs_keys="values",
            )
        else:
            return self._add_graph_dst_node_with_edge(
                node_label="isin",
                node_command=NodeCommands.isin.name,
                node_command_src_key="table",
                node_command_kwargs={
                    "iterable_values": values,
                },
            )

    def groupby(
        self,
        by: Union[ColumnIdentifier, List[ColumnIdentifier]] = None,
        axis: int = 0,
        sort: bool = True,
        group_keys: bool = None,
        observed: bool = False,
        dropna: bool = True,
    ) -> _FederatedDataFrameGroupBy:
        """Group the data using a mapper. Notice that this operation must be followed by
        an aggregation (such as .last or .first) before further operations can be made.
        The arguments are similar to pandas' original groupby.
        The following arguments from pandas implementation are not supported:
        `axis`, `level`, `as_index`


        Example:
            Assume the dummy data for 'data_cloudnode' looks like this:
            ```
               patient_id  age  weight procedures  start_date
            0           1   77      55          a  2015-08-01
            1           1   77      55          b  2015-10-01
            2           2   88      60          a  2017-11-11
            3           3   93      83          c  2020-01-01
            4           3   93      83          b  2020-05-01
            5           3   93      83          a  2021-01-04
            df = FederatedDataFrame('data_cloudnode')
            grouped_first = df.groupby(by='patient_id').first()
            grouped_first.preprocess_on_dummy()
            ```
            returns
            ```
                        age  weight procedures start_date
            patient_id
            1            77      55          a 2015-08-01
            2            88      60          a 2017-11-11
            3            93      83          c 2020-01-01
            ```

            ```
            grouped_last = df.groupby(by='patient_id').last()
            grouped_last.preprocess_on_dummy()
            ```
            returns
            ```
                        age  weight procedures start_date
            patient_id
            1            77      55          b 2015-10-01
            2            88      60          a 2017-11-11
            3            93      83          a 2021-01-04
            ```

        Args:
            by: dictionary, series, label, or list of labels to determine the groups.
                Grouping with a custom function is not allowed.
                If a dict or Series is passed, the Series or dict VALUES will be used
                to determine the groups.
                If a list or ndarray of length equal to the selected axis is passed,
                the values are used as-is to determine the groups.
                A label or list of labels may be passed to group by the columns in self.
                Notice that a tuple is interpreted as a (single) key.
            axis: Split along rows (0 or "index") or columns (1 or "columns")
            sort: Sort group keys.
            group_keys: During aggregation, add group keys to index to identify groups.
            observed: Only applies to categorical grouping, if true, only show
                observed values, otherwise, show all values.
            dropna: if true and groups contain NaN values, they will be dropped
                together with the row/column, otherwise, treat NaN as key in groups.

        Returns:
            _FederatedGroupBy object to be used in combination with further aggregations.

        Raises:
            PrivacyException: if `by` is a function
        """
        if isinstance(by, Callable):
            raise PrivacyException(
                "Only predefined functions are allowed within a graph, "
                "so grouping by a function is not possible."
            )
        result = self._add_operation_to_graph(
            NodeCommands.groupby.name,
            args={
                "by": by,
                "axis": axis,
                "sort": sort,
                "group_keys": group_keys,
                "observed": observed,
                "dropna": dropna,
            },
        )
        return _FederatedDataFrameGroupBy(result)

    def rolling(
        self,
        window: Union[int, timedelta],
        min_periods: Optional[int] = None,
        center: bool = False,
        on: Optional[str] = None,
        axis: Optional[Union[int, str]] = 0,
        closed: Optional[str] = None,
    ) -> _FederatedDataFrameRolling:
        """
        Rolling window operation, similar to `pandas.DataFrame.rolling`
        Following pandas arguments are not supported: `win_type`, `method`, `step`
        """

        result = self._add_operation_to_graph(
            NodeCommands.rolling.name,
            args={
                "window": window,
                "min_periods": min_periods,
                "center": center,
                "on": on,
                "axis": axis,
                "closed": closed,
            },
        )
        return _FederatedDataFrameRolling(result)

    def drop_duplicates(
        self,
        subset: Union[ColumnIdentifier, List[ColumnIdentifier], None] = None,
        keep: Union[Literal["first"], Literal["last"], Literal[False]] = "first",
        ignore_index: bool = False,
    ) -> FederatedDataFrame:
        """Drop duplicates in a table or column, similar to pandas' drop_duplicates

        Example:
            Assume the dummy data for 'data_cloudnode' looks like this:
            ```
               patient_id  age  weight
            0           1   77      55
            1           2   88      83
            2           3   93      83
            3           3   93      83
            df = FederatedDataFrame('data_cloudnode')
            df1 = df.drop_duplicates()
            df1.preprocess_on_dummy()
            ```
            returns
            ```
               patient_id  age  weight
            0           1   77      55
            1           2   88      83
            2           3   93      83
            df2 = df.drop_duplicates(subset=['weight'])
            df2.preprocess_on_dummy()
            ```
            returns
            ```
               patient_id  age  weight
            0           1   77      55
            1           2   88      83
            ```

        Args:
            subset: optional column label or sequence of column labels to
                consider when identifying duplicates, uses all columns by default
            keep: string determining which duplicates to keep,
                can be "first" or "last" or set to False to keep no duplicates
            ignore_index: if set to True, the resulting axis will be re-labeled,
                defaults to False

        Returns:
            new instance of the current object with updated graph.

        """
        return self._add_operation_to_graph(
            command=NodeCommands.drop_duplicates.name,
            args={
                "subset": subset,
                "keep": keep,
                "ignore_index": ignore_index,
            },
        )

    def charlson_comorbidities(
        self, index_column: str, icd_columns: List[str], mapping: Dict[str, List] = None
    ) -> FederatedDataFrame:
        """Converts icd codes into comorbidities. If no comorbidity mapping is specified,
        the default mapping of the NCI is used. See function
        'apheris.datatools.transformations.utils.formats.get_default_comorbidity_mapping'
        for the mapping or the original SAS file maintained by the NCI:
        https://healthcaredelivery.cancer.gov/seermedicare/considerations/NCI.comorbidity.macro.sas

        Args:
            index_column: column name of the index column (e.g. patient_id)
            icd_columns: names of columns containing icd codes, contributing
                to comorbidity derivation
            mapping: dictionary that maps comorbidity strings to list of icd codes

        Returns:
            pandas.DataFrame with comorbidity columns according to the used mapping and
                index from given index column,
                containing comorbidity entries as boolean values.

        """
        if isinstance(icd_columns, str):
            icd_columns = [icd_columns]

        if mapping is None:
            mapping = get_default_comorbidity_mapping()

        return self._add_operation_to_graph(
            command=NodeCommands.charlson_comorbidities.name,
            args={
                "index_column": index_column,
                "icd_columns": icd_columns,
                "mapping": mapping,
            },
        )

    def charlson_comorbidity_index(
        self,
        index_column: str,
        icd_columns: Union[List[str], str],
        mapping: Dict[str, List] = None,
    ) -> FederatedDataFrame:
        """Converts icd codes into Charlson Comorbidity Index score.
        If no comorbidity mapping is specified,
        the default mapping of the NCI is used. See function
        'apheris.datatools.transformations.utils.formats.get_default_comorbidity_mapping'
        for the mapping or the original SAS file maintained by the NCI:
        https://healthcaredelivery.cancer.gov/seermedicare/considerations/NCI.comorbidity.macro.sas


        Args:
            index_column: column name of the index column (e.g. patient_id)
            icd_columns: names of columns containing icd codes, contributing
                to comorbidity derivation
            mapping: dictionary that maps comorbidity strings to list of icd codes

        Returns:
            pandas.DataFrame with containing comorbidity score per patient.

        """
        if isinstance(icd_columns, str):
            icd_columns = [icd_columns]

        if mapping is None:
            mapping = get_default_comorbidity_mapping()

        return self._add_operation_to_graph(
            command=NodeCommands.charlson_comorbidity_score.name,
            args={
                "index_column": index_column,
                "icd_columns": icd_columns,
                "mapping": mapping,
            },
        )

    def reset_index(self, drop: bool = False) -> FederatedDataFrame:
        """Resets the index, e.g., after a groupby operation, similar to pandas
        `reset_index`.
        The following arguments from pandas implementation are not supported:
        `level`, `inplace`, `col_level`, `col_fill`, `allow_duplicates`, `names`

        Example:
            Assume the dummy data for 'data_cloudnode' looks like this:
            ```
               patient_id  age  weight
            0           1   77      55
            1           2   88      83
            2           3   93      60
            3           4   18      72
            df = FederatedDataFrame('data_cloudnode')
            df1 = df.reset_index()
            df1.preprocess_on_dummy()
            ```
            returns
            ```
               index  Unnamed: 0  patient_id  age  weight
            0      0           0           1   77      55
            1      1           1           2   88      83
            2      2           2           3   93      60
            3      3           3           4   18      72
            ```

            ```
            df2 = df.reset_index(drop=True)
            df2.preprocess_on_dummy()
            ```
            returns
            ```
               Unnamed: 0  patient_id  age  weight
            0           0           1   77      55
            1           1           2   88      83
            2           2           3   93      60
            3           3           4   18      72
            ```

        Args:
            drop: If true, do not try to insert index into the data columns.
                This resets the index to the default integer index.
                Defaults to False.

        Returns:
            new instance of the current object with updated graph.

        """
        return self._add_operation_to_graph(
            command=NodeCommands.reset_index.name, args={"drop": drop}
        )

    def transform_columns(self, transformation: pd.DataFrame) -> FederatedDataFrame:
        """
        Transform columns of a FederatedDataFrame using a pandas DataFrame as
        Transformation Matrix.
        The DataFrame index must correspond to the columns of the original
        FederatedDataFrame. The transformation is applied row-wise, i.e. each row is
        transformed to a subspace of the original feature space defined by the columns
        of the original FederatedDataFrame.

        Args:
            transformation: DataFrame with the same index as the columns of the
                original FederatedDataFrame. The DataFrame must have the same number of
                rows as the original FederatedDataFrame has columns.

        Returns:
            new instance of the current object with updated graph.

        """
        return self._add_operation_to_graph(
            command=NodeCommands.transform_columns.name,
            args={"transformation": transformation.to_dict()},
        )

    ######################################################################################
    # graph visualization, import and export
    ######################################################################################
    def display_graph(self):
        """
        Convert DiGraph from networkx into pydot and output SVG

        Returns: SVG content

        """
        graph_visualizer = DiGraphVisualizer()
        return graph_visualizer.create_svg(
            graph=self._graph,
        )

    def save_graph_as_image(
        self,
        filepath: str,
        image_format: str = "svg",
    ):
        """
        Convert DiGraph from networkx into pydot and save SVG
        Args:
            filepath: path where to save an image on the disk
            image_format: image format to be specified,
                supported formats are taken from pydot library

        """
        DiGraphManager.save_graph_as_image(
            graph=self._graph,
            filepath=filepath,
            img_format=image_format,
        )

    def export(self) -> str:
        """
        Export FederatedDataFrame object as JSON which can be then imported when needed

        Example:
            ```
            df = FederatedDataFrame('data_cloudnode')
            df_json = df.export()
            # store df_json and later:
            df_imported = FederatedDataFrame(data_source=df_json)
            # go on using df_imported as you would use df
            ```

        Returns:
            JSON-like string containing graph and node uuid
        """
        return DiGraphManager.export_graph(
            graph=copy.deepcopy(self._graph),
            node_uuid=self._uuid,
        )

    def _import_graph(
        self,
        graph_json: str,
    ):
        """
        Imports JSON content applying properties to the current instance
        Args:
            graph_json: JSON-like string containing graph and node uuid

        """
        if isinstance(graph_json, str):
            self.__nx_graph, node_uuid = DiGraphManager.import_graph(
                graph_json=graph_json,
            )
            self.__uuid_instance = NodeUUID(initial_uuid=node_uuid)
        else:
            raise TransformationsInputTypeException(
                function_name=self._import_graph.__name__,
                argument_name="graph_json",
                argument_type=type(graph_json),
            )

    ######################################################################################
    # graph analytics
    ######################################################################################
    @staticmethod
    def _get_head_nodes_ids(graph):
        return [n for n, d in graph.in_degree() if d == 0]

    def get_privacy_policy(self) -> Dict[str, Any]:
        """
        Get the privacy policy of the FederatedDataFrame.
        This method is used to retrieve the privacy policy associated with the
        FederatedDataFrame, which may include information about data sources,
        transformations, and privacy settings.

        Returns:
            PrivacyPolicy object containing the privacy policy details.
        """
        head_nodes_ids = self._get_head_nodes_ids(self.__nx_graph)
        dataset_ids = []
        for head_node_id in head_nodes_ids:
            head_node = self.__nx_graph.nodes.get(head_node_id)
            node_command = head_node.get("node_command")
            node_command_kwargs = head_node.get("node_command_kwargs")
            if node_command and "read" in node_command and node_command_kwargs:
                dataset_id = node_command_kwargs.get("data_source")
                if dataset_id:
                    dataset_ids.append(dataset_id)
        return get_asset_policies(dataset_ids=dataset_ids)

    def _get_datasets_names(self):
        raise NotImplementedError(
            "This method hase been deprecated and will be removed in the future. "
            "Please use the `get_privacy_policy` method instead."
        )

    def get_data_sources(self) -> List[str]:
        data_sources = []
        for node in self._graph.nodes._nodes.values():
            if node["node_command"] in [
                NodeCommands.read_csv.name,
                NodeCommands.read_parquet.name,
                NodeCommands.read_zip.name,
            ]:
                data_sources.append(node["node_command_kwargs"]["data_source"])
        return data_sources

    def _get_unique_remote_functions_or_raise_exception(self):
        """
        Get all remote functions which are used in the computational graph
        Returns: set of remote functions

        """
        nodes_commands = DiGraphManager.get_nodes_commands(
            graph=copy.deepcopy(self._graph),
        )
        nodes_remote_functions = set()
        for nodes_command in nodes_commands:
            try:
                nodes_remote_function = NodeCommands[nodes_command].remote_function
            except KeyError:
                raise TransformationsModuleCommandNotFoundException(
                    command=nodes_command,
                )
            nodes_remote_functions.add(nodes_remote_function)
        return nodes_remote_functions

    ######################################################################################
    # extract remote functions from the nodes and run them
    ######################################################################################
    def _get_filepath_for_reading(
        self,
        data_source_from_command: str,
        filepaths: Optional[Dict],
        expected_input_format: InputFormat,
        reading_from_data_source_allowed: bool,
    ) -> str:
        """Helper function for overwriting the data source given during the object's
        init with a local file (that was passed to the .run method)
        or a dummy data path if the data source is a remote data id.
        Args:
            data_source_from_command: what the FederatedDataFrame was initialized with
            filepaths: optional dictionary overwriting data sources at runtime,
                used both for testing and from within flows
            expected_input_format: to check whether the given data source is a
                file already, or whether to attempt using the dummy data from
                a respective remote data object
            reading_from_data_source_allowed: If True, DummyData can be loaded from an
                external service. This is possible when a user runs a
                FederatedDataFrame locally. If False, no DummyData will be loaded from an
                external service. We need this setting when FederatedDataFrame is
                re-played in the encapsulated environment of a Data Custodian.
        Raises:
            TransformationsInvalidSourceDataException: If the dataset id is not
            valid
            TransformationsFileExtensionNotDefinedWarning: If file extension is not
            specified correctly
        """
        if filepaths is not None and data_source_from_command in filepaths:
            # remote run or local run with filepaths
            data_source = filepaths[data_source_from_command]
        else:
            if not reading_from_data_source_allowed:
                # remote run but dataset_id is None
                raise TransformationsInvalidSourceDataException(data_source_from_command)
            else:
                # preprocess on dummy data set data_source to dataset_id
                data_source = data_source_from_command
        # check if it is a path already
        is_path = False
        try:
            file_extension = self._parse_file_extension(
                filepath_or_filename=data_source, raise_warning=True
            )
            is_path = file_extension == expected_input_format.value
        except TransformationsFileExtensionNotDefinedWarning:
            pass
        except TransformationsFileExtensionNotSupportedException:
            pass

        # data_source is a dataset_id, not a path
        if not is_path and reading_from_data_source_allowed:
            # if the path is already cached and points to a valid file,
            # we can use it directly otherwise we need to download it
            if (
                data_source in self._remote_data_to_path_cache
                and isinstance(self._remote_data_to_path_cache[data_source], str)
                and Path(self._remote_data_to_path_cache[data_source]).exists()
            ):
                filepath = self._remote_data_to_path_cache[data_source]
            else:
                # if the file is not in the cache, we need to download it
                # and store the path in the cache
                filepath = self.get_dummy_data(dataset_id=data_source)
        else:
            filepath = data_source
        return filepath

    def get_dummy_data(self, dataset_id: str) -> Path:
        # here we get the settings for dummy data endpoint
        ds_path_mapping = download_dataset(
            dataset_id=dataset_id, folder=self._tmp_dummy_data_folder.name
        )

        return ds_path_mapping[dataset_id]

    def preprocess_on_dummy(self) -> pd.DataFrame:
        """
        Execute computations "recorded" inside the FederatedDataFrame object
        on the dummy data attached to the registered dataset.

        If no dummy data is available, this method will fail. If you have data for
        testing stored on your local machine, please use `preprocess_on_files`
        instead.

        Example:
            ```
            df = FederatedDataFrame('data_cloudnode')
            df["new_weight"] = df["weight"] + 100

            # executes the addition on the dummy data of 'data_cloudnode'
            df.preprocess_on_dummy()

            # the resulting dataframe is equivalent to:
            df_raw = pandas.read_csv(
                apheris_auth.RemoteData('data_cloudnode').dummy_data_path
            )
            df_raw["new_weight"] = df_raw["weight"] + 100
            ```

        Returns:
            resulting pandas.DataFrame after preprocessing has been applied to dummy
            data.
        """

        try:
            from apheris_utils.extras_simulator.data._settings import configure_env

            configure_env(self.get_data_sources())
            return self._run(filepaths=None, reading_from_data_source_allowed=True)
        except ImportError:
            raise ImportError(
                "The apheris_utils.extras_simulator package is not installed. "
                "Please install it to use the preprocess_on_dummy method."
            )

    def preprocess_on_files(self, filepaths: Dict[str, str]) -> pd.DataFrame:
        """
        Execute computations "recorded" inside the FederatedDataFrame object
        on local data.

        Args:
            filepaths: dictionary used during
                FederatedDataFrame initialization with other data sources from your
                local machine. Keys are expected to be dataset ids,
                values are expected to be file paths.

        Example:
            ```
            df = FederatedDataFrame('data_cloudnode')
            df["new_weight"] = df["weight"] + 100
            df.preprocess_on_files({'data_cloudnode':
                                    'myDirectory/local/replacement_data.csv'})

            # the resulting dataframe is equivalent to:
            df_raw = pd.read_csv('myDirectory/local/replacement_data.csv')
            df_raw["new_weight"] = df_raw["weight"] + 100
            ```

            Note that in case the FederatedDataFrame merges multiple dataset objects
            and you don't specify all their ids in the filepaths, we use dummy data for
            all "missing" ids (if available, otherwise, an exception is raised).

        Returns:
            resulting pandas.DataFrame after preprocessing has been applied to given file

        """
        return self._run(filepaths=filepaths, reading_from_data_source_allowed=True)

    def _run(
        self, filepaths: Dict[str, str] = None, reading_from_data_source_allowed=False
    ):
        """
        Execute computations "recorded" inside the FederatedDataFrame object
        on actual data.
        Args:
            filepaths: optionally overwrite data used during FederatedDataFrame
                initialization with other data sources.
            reading_from_data_source_allowed: If True, DummyData can be loaded from an
                external service. This is possible when a user runs a
                FederatedDataFrame locally. If False, no DummyData will be loaded from an
                external service. We need this setting when FederatedDataFrame is
                re-played in the encapsulated environment of a Data Custodian.

        When using the FederatedDataFrame object in a remote computation,
        the computation internally will ensure to run on real data
        using this function using the filepaths
        """
        graph = copy.deepcopy(self._graph)
        fulfilled_dependencies = set()
        known_commands = [c.name for c in NodeCommands]
        for _ in range(graph.number_of_nodes()):  # This is to avoid an infinite loop
            for key, content in graph.nodes.items():
                dependencies = [x for x in graph.predecessors(key)]
                if key in fulfilled_dependencies:
                    # We have already computed this node
                    continue

                elif not set(dependencies).issubset(fulfilled_dependencies):
                    # We cannot compute this node because the dependencies are not
                    # fulfilled
                    continue
                else:
                    command = content.get("node_command")
                    if command not in known_commands:
                        raise TransformationsUnknownCommandException(
                            function_name=command,
                        )
                    command_kwargs = content.get("node_command_kwargs", dict())

                    # All dependencies are fulfilled.
                    command_enum = NodeCommands[command]
                    args, kwargs = list(), dict()
                    if command_enum == NodeCommands.read_csv:
                        data_source = command_kwargs["data_source"]
                        filepath = self._get_filepath_for_reading(
                            data_source,
                            filepaths,
                            InputFormat.CSV,
                            reading_from_data_source_allowed,
                        )
                        args = [filepath]
                    elif command_enum == NodeCommands.read_zip:
                        data_source = command_kwargs["data_source"]
                        zip_filepath = self._get_filepath_for_reading(
                            data_source,
                            filepaths,
                            InputFormat.ZIP,
                            reading_from_data_source_allowed,
                        )
                        single_file_name = command_kwargs.get("read_args").get("filename")
                        args = [zip_filepath, single_file_name]
                    elif command_enum == NodeCommands.read_parquet:
                        data_source = command_kwargs["data_source"]
                        filepath = self._get_filepath_for_reading(
                            data_source,
                            filepaths,
                            InputFormat.PARQUET,
                            reading_from_data_source_allowed,
                        )
                        args = [filepath]
                    elif command_enum == NodeCommands.setitem:
                        if "column_to_add" in command_kwargs:
                            item = graph.nodes[command_kwargs["column_to_add"]]["result"]
                        elif "value_to_add" in command_kwargs:
                            item = command_kwargs["value_to_add"]
                        else:
                            raise TransformationsMissingArgumentWarning(
                                "None of the arguments column_to_add or value_to_add "
                                "were found, item is set to None."
                            )
                        kwargs = {
                            "table": graph.nodes[command_kwargs["table"]]["result"],
                            "item_to_add": item,
                            "index": command_kwargs["index"],
                        }
                    elif command_enum == NodeCommands.getitem:
                        kwargs = {
                            "column": command_kwargs["column"],
                            "df": graph.nodes[dependencies[0]]["result"],
                        }
                    elif command_enum == NodeCommands.getitem_at_index_table:
                        kwargs = {
                            "table": graph.nodes[command_kwargs["table"]]["result"],
                            "mask": graph.nodes[command_kwargs["index"]]["result"],
                        }
                    elif command_enum == NodeCommands.addition:
                        kwargs = {
                            "this": graph.nodes[command_kwargs["table"]]["result"],
                            "summand_column1": command_kwargs["summand_column1"],
                            "summand2": command_kwargs["summand2"],
                            "result_column": command_kwargs["result_column"],
                        }
                    elif command_enum == NodeCommands.negation:
                        kwargs = {
                            "table": graph.nodes[command_kwargs["table"]]["result"],
                            "column_to_negate": command_kwargs["column_to_negate"],
                            "result_column": command_kwargs["result_column"],
                        }
                    elif command_enum == NodeCommands.inv:
                        kwargs = {
                            "table": graph.nodes[command_kwargs["table"]]["result"],
                            "column_to_invert": command_kwargs["column_to_invert"],
                            "result_column": command_kwargs["result_column"],
                        }
                    elif command_enum == NodeCommands.subtraction:
                        kwargs = {
                            "this": graph.nodes[command_kwargs["table"]]["result"],
                            "left": command_kwargs["left"],
                            "right": command_kwargs["right"],
                            "result": command_kwargs["result"],
                        }
                    elif command_enum == NodeCommands.mult:
                        kwargs = {
                            "this": graph.nodes[command_kwargs["table"]]["result"],
                            "left": command_kwargs["left"],
                            "right": command_kwargs["right"],
                            "result": command_kwargs["result"],
                        }
                    elif command_enum == NodeCommands.div:
                        kwargs = {
                            "this": graph.nodes[command_kwargs["table"]]["result"],
                            "left": command_kwargs["left"],
                            "right": command_kwargs["right"],
                            "result": command_kwargs["result"],
                        }
                    elif command_enum == NodeCommands.compare_to_table:
                        kwargs = {
                            "left": graph.nodes[command_kwargs["left"]]["result"],
                            "right": graph.nodes[command_kwargs["right"]]["result"],
                            "comparison_type": command_kwargs["comparison_type"],
                        }
                    elif command_enum == NodeCommands.compare_to_value:
                        kwargs = {
                            "left": graph.nodes[command_kwargs["left"]]["result"],
                            "right": command_kwargs["right"],
                            "comparison_type": command_kwargs["comparison_type"],
                        }
                    elif command_enum == NodeCommands.to_datetime:
                        kwargs = command_kwargs["args"]
                        kwargs["table"] = graph.nodes[command_kwargs["table"]]["result"]
                        kwargs["column"] = command_kwargs["column"]
                        kwargs["result"] = command_kwargs["result"]
                    elif command_enum == NodeCommands.fillna_table:
                        kwargs = {
                            "table": graph.nodes[command_kwargs["table"]]["result"],
                            "value": graph.nodes[command_kwargs["value"]]["result"],
                        }
                    elif command_enum == NodeCommands.fillna:
                        kwargs = {
                            "table": graph.nodes[command_kwargs["table"]]["result"],
                            "value": command_kwargs["value"],
                            "column": command_kwargs["column"],
                            "result": command_kwargs["result"],
                        }
                    elif command_enum == NodeCommands.dropna:
                        kwargs = command_kwargs["args"]
                        kwargs["table"] = graph.nodes[command_kwargs["table"]]["result"]
                    elif command_enum == NodeCommands.isna:
                        kwargs = {
                            "table": graph.nodes[command_kwargs["table"]]["result"],
                            "column": command_kwargs["column"],
                            "result": command_kwargs["result"],
                        }
                    elif command_enum == NodeCommands.astype:
                        kwargs = {
                            "table": graph.nodes[command_kwargs["table"]]["result"],
                            "dtype": command_kwargs["dtype"],
                            "column": command_kwargs["column"],
                            "result": command_kwargs["result"],
                        }
                    elif command_enum == NodeCommands.str_contains:
                        kwargs = {
                            "table": graph.nodes[command_kwargs["table"]]["result"],
                            "pattern": command_kwargs["pattern"],
                        }
                    elif command_enum == NodeCommands.str_len:
                        kwargs = {
                            "table": graph.nodes[command_kwargs["table"]]["result"],
                        }
                    elif command_enum == NodeCommands.merge:
                        kwargs = {
                            "left": graph.nodes[command_kwargs["left"]]["result"],
                            "right": graph.nodes[command_kwargs["right"]]["result"],
                            "how": command_kwargs["how"],
                            "on": command_kwargs["on"],
                            "left_on": command_kwargs["left_on"],
                            "right_on": command_kwargs["right_on"],
                            "left_index": command_kwargs["left_index"],
                            "right_index": command_kwargs["right_index"],
                            "sort": command_kwargs["sort"],
                            "suffixes": command_kwargs["suffixes"],
                            "copy": command_kwargs["copy"],
                            "indicator": command_kwargs["indicator"],
                            "validate": command_kwargs["validate"],
                        }
                    elif command_enum == NodeCommands.concat:
                        kwargs = {
                            "table1": graph.nodes[command_kwargs.pop("table1")]["result"],
                            "table2": graph.nodes[command_kwargs.pop("table2")]["result"],
                        }
                        kwargs.update(command_kwargs)
                    elif command_enum == NodeCommands.rename:
                        kwargs = {
                            "table": graph.nodes[dependencies[0]]["result"],
                            "mapping": command_kwargs["mapping"],
                        }
                    elif command_enum == NodeCommands.drop_column:
                        kwargs = {
                            "table": graph.nodes[dependencies[0]]["result"],
                            "column": command_kwargs["column"],
                        }
                    elif command_enum == NodeCommands.add_table:
                        kwargs = {
                            "summand1": graph.nodes[command_kwargs["summand1"]]["result"],
                            "summand2": graph.nodes[command_kwargs["summand2"]]["result"],
                        }
                    elif command_enum == NodeCommands.add_number:
                        kwargs = {
                            "summand1": graph.nodes[command_kwargs["summand1"]]["result"],
                            "summand2": command_kwargs["summand2"],
                        }
                    elif command_enum in [
                        NodeCommands.divide,
                        NodeCommands.divide_by_constant,
                    ]:
                        kwargs = {
                            "dividend": graph.nodes[command_kwargs["dividend"]]["result"],
                        }
                        if command_enum == NodeCommands.divide:
                            kwargs["divisor"] = graph.nodes[command_kwargs["divisor"]][
                                "result"
                            ]
                        else:
                            kwargs["divisor"] = command_kwargs["divisor"]
                    elif command_enum in [
                        NodeCommands.multiply,
                        NodeCommands.multiply_by_constant,
                    ]:
                        kwargs = {
                            "multiplicand": graph.nodes[command_kwargs["multiplicand"]][
                                "result"
                            ],
                        }
                        if command_enum == NodeCommands.multiply:
                            kwargs["multiplier"] = graph.nodes[
                                command_kwargs["multiplier"]
                            ]["result"]
                        else:
                            kwargs["multiplier"] = command_kwargs["multiplier"]
                    elif command_enum in [
                        NodeCommands.logical_conjunction_table,
                        NodeCommands.logical_conjunction_number,
                    ]:
                        kwargs = {
                            "left": graph.nodes[command_kwargs["left"]]["result"],
                            "right": graph.nodes[command_kwargs["right"]]["result"],
                            "conjunction_type": command_kwargs["conjunction_type"],
                        }
                    elif command_enum == NodeCommands.sort_values:
                        kwargs = command_kwargs["args"]
                        kwargs["table"] = graph.nodes[command_kwargs["table"]]["result"]
                    elif command_enum == NodeCommands.groupby:
                        kwargs = command_kwargs["args"]
                        kwargs["table"] = graph.nodes[command_kwargs["table"]]["result"]
                    elif command_enum == NodeCommands.first:
                        kwargs = {
                            "table": graph.nodes[command_kwargs["table"]]["result"],
                        }
                    elif command_enum == NodeCommands.size:
                        kwargs = {
                            "table": graph.nodes[command_kwargs["table"]]["result"],
                        }
                    elif command_enum == NodeCommands.last:
                        kwargs = {
                            "table": graph.nodes[command_kwargs["table"]]["result"],
                        }
                    elif command_enum == NodeCommands.mean:
                        kwargs = {
                            "table": graph.nodes[command_kwargs["table"]]["result"],
                        }
                    elif command_enum == NodeCommands.sum:
                        kwargs = {
                            "table": graph.nodes[command_kwargs["table"]]["result"],
                        }
                    elif command_enum == NodeCommands.cumsum:
                        kwargs = {
                            "table": graph.nodes[command_kwargs["table"]]["result"],
                        }
                    elif command_enum == NodeCommands.count:
                        kwargs = {
                            "table": graph.nodes[command_kwargs["table"]]["result"],
                        }
                    elif command_enum == NodeCommands.diff:
                        kwargs = {
                            "table": graph.nodes[command_kwargs["table"]]["result"],
                            "periods": command_kwargs["args"]["periods"],
                            "axis": command_kwargs["args"]["axis"],
                        }
                    elif command_enum == NodeCommands.shift:
                        kwargs = {
                            "table": graph.nodes[command_kwargs["table"]]["result"],
                            "periods": command_kwargs["args"]["periods"],
                            "freq": command_kwargs["args"]["freq"],
                            "axis": command_kwargs["args"]["axis"],
                            "fill_value": command_kwargs["args"]["fill_value"],
                        }
                    elif command_enum == NodeCommands.rank:
                        kwargs = {
                            "table": graph.nodes[command_kwargs["table"]]["result"],
                            "method": command_kwargs["args"]["method"],
                            "ascending": command_kwargs["args"]["ascending"],
                            "na_option": command_kwargs["args"]["na_option"],
                            "pct": command_kwargs["args"]["pct"],
                            "axis": command_kwargs["args"]["axis"],
                        }
                    elif command_enum == NodeCommands.isin:
                        if "iterable_values" in command_kwargs:
                            # iterable mode:
                            kwargs = {
                                "table": graph.nodes[command_kwargs["table"]]["result"],
                                "values": command_kwargs["iterable_values"],
                            }
                        else:
                            # table mode
                            kwargs = {
                                "table": graph.nodes[command_kwargs["table"]]["result"],
                                "values": graph.nodes[command_kwargs["values"]]["result"],
                            }
                    elif command_enum == NodeCommands.drop_duplicates:
                        kwargs = command_kwargs["args"]
                        kwargs["table"] = graph.nodes[command_kwargs["table"]]["result"]
                    elif command_enum == NodeCommands.reset_index:
                        kwargs = command_kwargs["args"]
                        kwargs["table"] = graph.nodes[command_kwargs["table"]]["result"]
                    elif command_enum in [
                        NodeCommands.loc_setter,
                        NodeCommands.loc_getter,
                    ]:
                        other_srcs_keys = command_kwargs.get("other_srcs_keys", list())
                        index_mask = command_kwargs["index_mask"]
                        if "index_mask" in other_srcs_keys:
                            index_mask = graph.nodes[index_mask]["result"]
                        kwargs = {
                            "table": graph.nodes[command_kwargs["table"]]["result"],
                            "index_mask": index_mask,
                            "columns": command_kwargs["columns"],
                        }
                        if command_enum == NodeCommands.loc_setter:
                            values = command_kwargs["values"]
                            if "values" in other_srcs_keys:
                                values = graph.nodes[values]["result"]
                            kwargs["values"] = values
                    elif command == NodeCommands.prepare_sankey_plot:
                        kwargs = {
                            "table": graph.nodes[command_kwargs["table"]]["result"],
                            "time_col": command_kwargs["time_col"],
                            "group_col": command_kwargs["group_col"],
                            "observable_col": command_kwargs["observable_col"],
                        }
                    elif command_enum == NodeCommands.rolling:
                        kwargs = command_kwargs["args"]
                        kwargs["table"] = graph.nodes[command_kwargs["table"]]["result"]
                    elif command_enum == NodeCommands.rolling_sum:
                        kwargs = {}
                        kwargs["table"] = graph.nodes[command_kwargs["table"]]["result"]
                    elif command_enum == NodeCommands.rolling_mean:
                        kwargs = {}
                        kwargs["table"] = graph.nodes[command_kwargs["table"]]["result"]
                    elif command_enum == NodeCommands.charlson_comorbidities:
                        kwargs = command_kwargs["args"]
                        kwargs["table"] = graph.nodes[command_kwargs["table"]]["result"]
                    elif command_enum == NodeCommands.charlson_comorbidity_score:
                        kwargs = command_kwargs["args"]
                        kwargs["table"] = graph.nodes[command_kwargs["table"]]["result"]
                    elif command_enum == NodeCommands.transform_columns:
                        kwargs = command_kwargs["args"]
                        kwargs["table"] = graph.nodes[command_kwargs["table"]]["result"]
                    elif command_enum == NodeCommands.sample:
                        kwargs = command_kwargs["args"]
                        kwargs["table"] = graph.nodes[command_kwargs["table"]]["result"]
                    else:
                        # ex.: NodeCommands.neg, NodeCommands.datetime_like_properties
                        kwargs = command_kwargs
                        table_ref = command_kwargs.get("table")
                        if table_ref:
                            kwargs["table"] = graph.nodes[table_ref]["result"]
                    if args or kwargs:
                        graph.nodes[key]["result"] = command_enum.remote_function(
                            *args, **kwargs
                        )
                    fulfilled_dependencies.add(key)
        df_final = graph.nodes[self._uuid]["result"]
        if df_final is None:
            raise TransformationsFailedExecutionException()
        if isinstance(df_final, DataFrameGroupBy):
            raise TransformationsInvalidGraphException(
                reason="groupby was found as the last operation",
                do_that="define an aggregation after groupby",
            )
        return df_final

    ######################################################################################
    # read file helpers
    ######################################################################################
    @staticmethod
    def _validate_if_filename_for_zip_provided(
        read_format: Union[str, InputFormat, None] = None,
        filename_in_zip: Union[str, None] = None,
    ):
        """
        Raise exception if filename_in_zip is not provided for ZIP data source
        Args:
            read_format: format of data source
            filename_in_zip: used for ZIP format to identify which file out of ZIP to take
        """
        if isinstance(read_format, InputFormat):
            read_format = read_format.value
        if read_format and read_format == InputFormat.ZIP.value and not filename_in_zip:
            raise TransformationsMissingArgumentException(
                argument_name="filename_in_zip",
                function_name="preprocess",
                mark_as_mandatory=False,
            )

    @staticmethod
    def _validate_if_read_format_supported(
        read_format: Union[str, InputFormat, None] = None,
    ):
        """
        Raise exception if read_format is not supported
        Args:
            read_format: format of data source
        """
        if not isinstance(read_format, InputFormat):
            supported_file_extensions = InputFormat.get_supported_formats()
            if read_format and read_format not in supported_file_extensions:
                raise TransformationsFileExtensionNotSupportedException(
                    file_extension=read_format,
                    supported_file_extensions=supported_file_extensions,
                )

    @staticmethod
    def _parse_file_extension(
        filepath_or_filename: str,
        default_extension_handler: InputFormat = InputFormat.CSV,
        raise_warning: bool = False,
    ) -> str:
        """
        Filepath parser which takes file extension, removes dot and down-cases it
        Additional check is performed to validate if the format is supported
        Args:
            filepath_or_filename: filepath,
                if no extension is provided or a string is empty the default
                parser will be called
            default_extension_handler: default handler to be called if
                no extension or empty string was used as input
            raise_warning: bool, if True warning message regarding missing format
                and application of the default format will be displayed

        Returns: file extension as str

        """
        supported_file_extensions = InputFormat.get_supported_formats()
        extension_handler = default_extension_handler.value
        if filepath_or_filename and isinstance(filepath_or_filename, str):
            file_extension = Path(filepath_or_filename).suffix
            file_extension = file_extension.replace(".", "").lower()
        else:
            file_extension = None
        if not file_extension and raise_warning:
            raise TransformationsFileExtensionNotDefinedWarning(
                filepath=filepath_or_filename,
                default_extension=str(extension_handler),
            )
        elif not file_extension:
            pass
        elif file_extension in supported_file_extensions:
            extension_handler = file_extension
        else:
            raise TransformationsFileExtensionNotSupportedException(
                file_extension=file_extension,
                supported_file_extensions=supported_file_extensions,
            )
        return extension_handler

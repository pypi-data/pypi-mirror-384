import copy
import inspect
import json
import logging
from enum import Enum
from typing import Dict, List, Union

import networkx as nx

from .exceptions_handling import (
    TransformationsFileExtensionNotSupportedException,
    TransformationsInvalidJSONFormatException,
    TransformationsInvalidSourceDataException,
    TransformationsMissingArgumentException,
    TransformationsTypeConversionException,
)
from .lazy_loader import lazy_import
from .str_object_converter import StrObjectNodeCommandKwargsConverter

try:
    IPython = lazy_import("IPython.display")
except ImportError:
    IPython = None

pydot = lazy_import("pydot")  # imported inside nx.drawing.nx_pydot.to_pydot()

logger = logging.getLogger(__name__)

NODE_UUID_JSON_KEY = "export-graph-node-uuid"
DISPLAY_GRAPH_CREATION = False


class PyDotAction(Enum):
    """Prefixes of pydot functions
    which will be created when pydot graph gets initialized
    """

    CREATE = "create"
    WRITE = "write"


class DiGraph(nx.DiGraph):
    """NetworksX DiGraph with a couple of extra methods
    to simplify nodes and edges creation
    """

    @staticmethod
    def wrap_key_value_pair_as_string(key, value):
        """
        Wrapper to present better key-value pair as node labels
        Args:
            key: object used as a key in dict
            value: object used as a value in dict

        Returns:

        """
        extra_quotes_if_needed = "'" if isinstance(value, str) else ""
        return (
            str(key) + "=" + extra_quotes_if_needed + str(value) + extra_quotes_if_needed
        )

    def _add_graph_node(
        self,
        node_uuid: str,
        node_label: str,
        node_command: str,
        node_command_kwargs: dict = None,
        include_identifier: bool = True,
        **kwargs,
    ):
        """
        Adding a node to the graph
        Args:
            node_uuid: destination node uuid
            node_label: destination node label
            node_command: additional argument, used for FederatedDataFrame.run()
                to identify which remote function should be called
            node_command_kwargs: additional argument, used for FederatedDataFrame.run()
                to specify additional parameters remote function needs to be called
            include_identifier: bool, if True command arguments
                will be included in the node label
            **kwargs:

        Returns: destination node uuid

        """
        filtered_keys = set(kwargs.keys()) & {
            "URL",
            "color",
            "colorscheme",
            "comment",
            "distortion",
            "fillcolor",
            "fixedsize",
            "fontcolor",
            "fontname",
            "fontsize",
            "group",
            "height",
            "id",
            "image",
            "imagescale",
            "label",
            "labelloc",
            "layer",
            "margin",
            "nojustify",
            "orientation",
            "penwidth",
            "peripheries",
            "pin",
            "pos",
            "rects",
            "regular",
            "root",
            "samplepoints",
            "shape",
            "shapefile",
            "showboxes",
            "sides",
            "skew",
            "sortv",
            "style",
            "target",
            "tooltip",
            "vertices",
            "width",
            "z",
            # The following are attributes dot2tex
            "texlbl",
            "texmode",
        }  # inspiration was taken from pydot.NODE_ATTRIBUTES,
        # NOTE: left as constant as pydot library would be optional and required only for
        # graph display functionality
        filtered_kwargs = {
            filtered_key: kwargs.get(filtered_key) for filtered_key in filtered_keys
        }

        # Label generation
        node_command_signature = list()
        if "args" in node_command_kwargs.keys():
            node_command_kwargs_for_label = node_command_kwargs.get("args")
            node_command_kwargs_for_label = node_command_kwargs_for_label or dict()
        else:
            node_command_kwargs_for_label = node_command_kwargs
        for k, v in node_command_kwargs_for_label.items():
            if v is not None:
                node_command_signature.append(self.wrap_key_value_pair_as_string(k, v))
        node_command_signature = ", ".join(node_command_signature)
        updated_node_label = (
            [
                node_label,
                f"with {node_command_signature}",
            ]
            if include_identifier and node_command_signature
            else node_label
        )
        updated_node_label = (
            "\n".join(updated_node_label)
            if isinstance(updated_node_label, list)
            else str(updated_node_label)
        )
        if DISPLAY_GRAPH_CREATION:
            logger.debug(
                "Adding NX node: "
                + node_uuid
                + " | "
                + updated_node_label.replace("\n", " ")
            )
        super().add_node(
            node_for_adding=node_uuid,
            label=updated_node_label,
            node_command=node_command,
            node_command_kwargs=node_command_kwargs,
            **filtered_kwargs,
        )

        return node_uuid

    def add_graph_src_node(
        self,
        src_node_uuid: str,
        node_label: str,
        node_command: str,
        node_command_kwargs: dict = None,
        include_identifier: bool = True,
        **kwargs,
    ):
        """
        Adding a source node to the graph
        Args:
            src_node_uuid: source node uuid
            node_label: source node label
            node_command: additional argument, used for FederatedDataFrame.run()
                to identify which remote function should be called
            node_command_kwargs: additional argument, used for FederatedDataFrame.run()
                to specify additional parameters remote function needs to be called
            include_identifier: bool, if True command arguments
                will be included in the node label
            **kwargs:

        Returns: source node uuid

        """
        if "shape" not in kwargs:
            kwargs["shape"] = "box3d"
        if "style" not in kwargs:
            kwargs["style"] = "filled"
        return self._add_graph_node(
            node_uuid=src_node_uuid,
            node_label=node_label,
            node_command=node_command,
            node_command_kwargs=node_command_kwargs,
            include_identifier=include_identifier,
            **kwargs,
        )

    def add_graph_dst_node_with_edge(
        self,
        src_node_uuid: str,
        dst_node_uuid: str,
        node_label: str,
        node_command: str,
        node_command_kwargs: dict = None,
        include_identifier: bool = True,
        **kwargs,
    ):
        """
        Adding a destination node with an edge to the graph
        Args:
            src_node_uuid: source node uuid
            dst_node_uuid: destination node uuid
            node_label: destination node label
            node_command: additional argument, used for FederatedDataFrame.run()
                to identify which remote function should be called
            node_command_kwargs: additional argument, used for FederatedDataFrame.run()
                to specify additional parameters remote function needs to be called
            include_identifier: bool, if True command arguments
                will be included in the node label
            **kwargs:

        Returns: destination node uuid

        """
        if "shape" not in kwargs:
            kwargs["shape"] = "box"
        self._add_graph_node(
            node_uuid=dst_node_uuid,
            node_label=node_label,
            node_command=node_command,
            node_command_kwargs=node_command_kwargs,
            include_identifier=include_identifier,
            **kwargs,
        )
        if DISPLAY_GRAPH_CREATION:
            logger.debug(f"Adding EDGE node: from {src_node_uuid} to {dst_node_uuid}")
        self.add_edge(
            src_node_uuid,
            dst_node_uuid,
        )

    def add_graph_dst_node_with_multiple_edges(
        self,
        src_nodes_uuids: List[str],
        dst_node_uuid: str,
        node_label: str,
        node_command: str,
        node_command_kwargs: dict = None,
        edges_labels: Union[Dict, None] = None,
        include_identifier: bool = True,
        **kwargs,
    ):
        """
        Adding a destination node with multiple edges to the graph
        Args:
            src_nodes_uuids: source nodes uuids
            dst_node_uuid: destination node uuid
            node_label: destination node label
            node_command: additional argument, used for FederatedDataFrame.run()
                to identify which remote function should be called
            node_command_kwargs: additional argument used for FederatedDataFrame.run()
                to specify additional parameters remote function needs to be called
            edges_labels: optional labels for each edge defined between the
                dst and src nodes
            include_identifier: bool, if True command arguments
                will be included in the node label
            **kwargs:
        """
        self._add_graph_node(
            node_uuid=dst_node_uuid,
            node_label=node_label,
            node_command=node_command,
            node_command_kwargs=node_command_kwargs,
            include_identifier=include_identifier,
            **kwargs,
        )
        for src_node_uuid in src_nodes_uuids:
            if DISPLAY_GRAPH_CREATION:
                logger.debug(f"Adding EDGE node: from {src_node_uuid} to {dst_node_uuid}")
            edge_kwargs = dict()
            if edges_labels:
                edge_kwargs["label"] = edges_labels.get(src_node_uuid, "")
            self.add_edge(src_node_uuid, dst_node_uuid, **edge_kwargs)


class DiGraphVisualizer:
    """NetworkX DiGraph visualizer
    Used to convert networkx graph into pydot one, creates and saves a graph image
    """

    @staticmethod
    def _convert_to_pydot(graph: nx.DiGraph):
        """
        Converts NetworkX graph into pydot one
        Args:
            graph: nx.DiGraph which needs to be converted into pydot

        Returns: pydot Dot graph

        """
        if pydot:
            return nx.drawing.nx_pydot.to_pydot(graph)

    def call_pydot_visualization(
        self, graph: nx.DiGraph, action: PyDotAction, img_format: str = "svg", **kwargs
    ):
        """
        Validates if requested image format is supported by pydot and
            maps requested image format to the graph visualization functions
        Args:
            graph: NetworkX graph
            action: PyDotAction (create to create image and write to save it on disk)
            img_format: requested image format
            **kwargs: additional arguments to be passed to pydot visualization functions

        Returns: image content or None (for write_ function)

        """
        graph_to_display = copy.deepcopy(graph)
        for node in graph_to_display.nodes:
            for key_to_remove in ["node_command", "node_command_kwargs"]:
                if key_to_remove in graph_to_display.nodes[node]:
                    del graph_to_display.nodes[node][key_to_remove]
            for key_to_quote in ["label"]:
                if key_to_quote in graph_to_display.nodes[node]:
                    graph_to_display.nodes[node][key_to_quote] = '"{}"'.format(
                        graph_to_display.nodes[node][key_to_quote]
                    )
        pydot_graph = self._convert_to_pydot(graph=graph_to_display)
        if pydot_graph:
            supported_formats = pydot_graph.formats
            if img_format in supported_formats:
                try:
                    action_attr = "{action}_{fmt}".format(
                        action=action.value,
                        fmt=img_format,
                    )
                    return getattr(pydot_graph, action_attr)(**kwargs)
                except (FileNotFoundError, OSError):
                    logger.warning(
                        "To use this functionality please make sure that "
                        "graphviz is installed. To install on Linux please run: "
                        "`sudo apt-get install --yes graphviz`"
                    )
            else:
                raise TransformationsFileExtensionNotSupportedException(
                    file_extension=img_format,
                    supported_file_extensions=supported_formats,
                )
        else:
            logger.warning(
                "To use this functionality please make sure that "
                "pydot with prerequisites (graphviz) are installed. "
                "To install on Linux please run: "
                "`sudo apt-get install --yes graphviz` "
                "and then `pip install pydot`"
            )

    def create(
        self,
        graph: nx.DiGraph,
        img_format: str = "svg",
    ):
        """
        Convert DiGraph from networkx into pydot and output SVG content
        Args:
            graph: NetworkX graph
            img_format: requested image format

        Returns: image content
        """
        return self.call_pydot_visualization(
            graph=graph,
            action=PyDotAction.CREATE,
            img_format=img_format,
        )

    def create_svg(
        self,
        graph: nx.DiGraph,
    ):
        """
        Convert DiGraph from networkx into pydot and output SVG
        Args:
            graph: NetworkX graph

        Returns: SVG image
        """
        svg_content = self.create(
            graph=graph,
            img_format="svg",
        )
        if not svg_content:
            pass
        elif IPython:
            return IPython.SVG(svg_content)
        else:
            logger.warning(
                "Could not call IPython.display. "
                "Please make sure the package is properly installed."
            )
        return svg_content


class DiGraphManager:
    """Graph manager which
    - saves graph image to a disk
    - exports graph into JSON (converts it from DiGraph)
    - imports graph from JSON (converts it into DiGraph)
    """

    @staticmethod
    def save_graph_as_image(
        graph: nx.DiGraph,
        filepath: str,
        img_format: str = "svg",
    ):
        """
        Convert DiGraph from networkx into pydot and save SVG
        Args:
            graph: NetworkX graph
            filepath: path on a disk where to save an image
            img_format: requested image format (should be supported by pydot)

        """
        graph_visualizer = DiGraphVisualizer()
        graph_visualizer.call_pydot_visualization(
            graph=graph,
            action=PyDotAction.WRITE,
            img_format=img_format,
            path=filepath,
        )

    @staticmethod
    def export_graph(
        graph: nx.DiGraph,
        node_uuid: str,
    ) -> str:
        """
        Export DiGraph to JSON
        Args:
            graph: NetworkX graph
            node_uuid: node UUID which was stored in DiGraph (end node reference)

        Returns: JSON string
        """
        try:
            graph_data = nx.readwrite.json_graph.node_link_data(graph, edges="links")

            # Convert non-serializable objects
            graph_data = StrObjectNodeCommandKwargsConverter.to_serializable(
                graph_dict=graph_data,
            )
            graph_data[NODE_UUID_JSON_KEY] = node_uuid
            return json.dumps(graph_data, indent=2)
        except TypeError:
            raise TransformationsTypeConversionException(
                source_data="graph",
                expected_format="JSON",
            )

    @staticmethod
    def import_graph(
        graph_json: str,
    ):
        """
        Import JSON as nx.DiGraph with node UUID if specified
        Args:
            graph_json: JSON representation of the graph

        Returns: tuple with nx.DiGraph and node UUID (end node reference)
        """
        try:
            if graph_json:
                graph_data = json.loads(graph_json)
                if not graph_data.get("nodes") or not graph_data.get("directed"):
                    raise TransformationsInvalidSourceDataException(
                        source_data="graph JSON",
                    )
                node_uuid = graph_data.get(NODE_UUID_JSON_KEY)
                graph_data.pop(NODE_UUID_JSON_KEY, None)
                # Convert back not-serializable objects
                graph_data = StrObjectNodeCommandKwargsConverter.from_serializable(
                    graph_dict_serializable=graph_data
                )

                signature = inspect.signature(nx.readwrite.json_graph.node_link_graph)
                if "edges" in signature.parameters:
                    # networkx >=3.4
                    # We stay with the old default value to be backward-compatible
                    # see https://github.com/networkx/networkx/blob/networkx-3.4/networkx/readwrite/json_graph/node_link.py#L142  # noqa
                    di_graph = nx.readwrite.json_graph.node_link_graph(
                        graph_data, edges="links"
                    )
                else:
                    # networkx <3.4
                    di_graph = nx.readwrite.json_graph.node_link_graph(graph_data)

                # If not NODE_UUID_JSON_KEY is specified take the added node UUID
                if not node_uuid and len(di_graph.nodes) > 0:
                    node_uuid = list(di_graph.nodes)[-1]
                return di_graph, node_uuid
            else:
                raise TransformationsMissingArgumentException(
                    function_name="import_graph",
                    argument_name="graph_json",
                )
        except json.decoder.JSONDecodeError:
            raise TransformationsInvalidJSONFormatException(
                message="Data source cannot be loaded as JSON."
            )
        except (TypeError, KeyError):
            raise TransformationsTypeConversionException(
                source_data="JSON",
                expected_format="graph",
            )

    @staticmethod
    def get_nodes_commands(
        graph: nx.DiGraph,
    ) -> set:
        node_commands = set()
        for node in graph.nodes.values():
            node_command = node.get("node_command")
            if node_command:
                node_commands.add(node_command)
        return node_commands

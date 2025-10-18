import importlib
import logging
import re
from typing import Union

from pandas import DataFrame, Series, Timedelta, Timestamp

BUILT_IN_TYPES = tuple([float, int, str, bool])
BUILT_IN_TYPES_WITH_DICT = tuple([dict]) + BUILT_IN_TYPES
ARITHMETIC_TYPES = tuple([float, int, Timestamp, Timedelta])
ALL_SUPPORTED_TYPES = tuple([float, int, str, bool, Timestamp, Timedelta])
ALL_SUPPORTED_TYPES_WITH_SLICE = ALL_SUPPORTED_TYPES + (slice,)
PANDAS_DF_TYPES = tuple([DataFrame, Series])
ALL_SUPPORTED_TYPES_WITH_PANDAS_DF = ALL_SUPPORTED_TYPES + PANDAS_DF_TYPES + (list,)

logger = logging.getLogger(__name__)


class StrObjectConverter:
    """
    Serializer for values which are supported but are not built-in type,
    used before converting python dict into serializable JSON
    """

    @staticmethod
    def to_serializable(value: Union[ALL_SUPPORTED_TYPES_WITH_SLICE]):
        value_type = type(value)
        if value_type not in BUILT_IN_TYPES and value is not None:
            if isinstance(value, slice):  # special case
                value_representation = [
                    getattr(value, property_name)
                    for property_name in ["start", "stop", "step"]
                ]  # will be used for constructor, order matters
            else:
                value_representation = str(value)
            return {"type": str(value_type), "value": value_representation}
        else:
            return value

    @staticmethod
    def from_serializable(type_value_dict: Union[BUILT_IN_TYPES_WITH_DICT]):
        if isinstance(type_value_dict, dict):
            class_module_with_name = type_value_dict.get("type", "")
            if class_module_with_name:
                class_name = None
                value_representation = type_value_dict.get("value", "")
                class_module_with_name_match = re.match(
                    r"<class \'(?P<module>[A-Za-z._]+)\.(?P<class_name>[A-Za-z_]+)\'>$",
                    class_module_with_name,
                )
                if class_module_with_name_match:
                    module = class_module_with_name_match.group("module")
                    class_name = class_module_with_name_match.group("class_name")
                else:
                    module = "builtins"
                    class_name_match = re.match(
                        r"<class \'(?P<class_name>[A-Za-z_]+)\'>$",
                        class_module_with_name,
                    )
                    if class_name_match is not None:
                        class_name = class_name_match.group("class_name")
                    else:
                        # likely to occur only if previously serialized object
                        # is manipulated by user
                        logger.warning(
                            f"Could not parse class name in {class_module_with_name}"
                        )
                if module and class_name:
                    try:
                        # will raise ImportError if module cannot be loaded
                        imported_module = importlib.import_module(module)
                        # will raise AttributeError if class cannot be found
                        class_constructor = getattr(imported_module, class_name)
                        if isinstance(value_representation, list):
                            return class_constructor(*value_representation)
                        else:
                            return class_constructor(value_representation)
                    except ImportError as e:
                        logger.warning(f"Could not load module {module}: {e}")
                    except AttributeError as e:
                        logger.warning(f"Could not find class {class_name}: {e}")
        return type_value_dict


class StrObjectNodeCommandKwargsConverter:
    """
    Serializer for "node_command_kwargs" dict,
    used before converting python dict into serializable JSON
    """

    @staticmethod
    def to_serializable(graph_dict: dict):
        graph_dict_serializable = graph_dict
        for _, node_dict in enumerate(graph_dict_serializable.get("nodes", list())):
            node_command_kwargs = node_dict.get("node_command_kwargs", dict())
            for node_command_key, node_command_value in node_command_kwargs.items():
                if not isinstance(node_command_value, BUILT_IN_TYPES) and isinstance(
                    node_command_value, ALL_SUPPORTED_TYPES_WITH_SLICE
                ):
                    node_command_value = StrObjectConverter.to_serializable(
                        value=node_command_value,
                    )
                    node_command_kwargs[node_command_key] = node_command_value
        return graph_dict_serializable

    @staticmethod
    def from_serializable(graph_dict_serializable: dict):
        graph_dict = graph_dict_serializable
        for _, node_dict in enumerate(graph_dict.get("nodes", list())):
            node_command_kwargs = node_dict.get("node_command_kwargs", dict())
            for node_command_key, node_command_value in node_command_kwargs.items():
                if isinstance(node_command_value, dict) and node_command_value.get(
                    "type"
                ):
                    node_command_value = StrObjectConverter.from_serializable(
                        type_value_dict=node_command_value,
                    )
                    node_command_kwargs[node_command_key] = node_command_value
        return graph_dict

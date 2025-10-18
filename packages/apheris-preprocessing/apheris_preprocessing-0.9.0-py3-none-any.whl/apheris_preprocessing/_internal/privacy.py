from apheris_preprocessing._internal.utils.exceptions_handling import (
    RestrictedPreprocessingViolation,
)
from apheris_preprocessing._internal.utils.commands import NodeCommands
from apheris_preprocessing._internal.utils.digraph import DiGraph


class PrivacyChecker:
    @staticmethod
    def validate_merge_first(graph: DiGraph, node) -> None:
        """Validate that every predecessor of `node` in the given graph
        is a safe command with respect to the constant list above.
        Args:
            graph: The graph to check
            node: The merge node to start the check with,
                all nodes that are not predecessors of this node are ignored
        Raises:
            RestrictedPreprocessingViolation if a node with a non-permitted command
            is found
        """
        # List of commands that can be used in the graph before merging,
        # this list can be extended after careful privacy evaluation
        safe_commands_before_merge = [
            NodeCommands.read_csv.name,
            NodeCommands.read_zip.name,
            NodeCommands.read_parquet.name,
            NodeCommands.merge.name,
        ]

        dependencies = [x for x in graph.predecessors(node)]
        while len(dependencies) > 0:
            new_dependencies = []
            for d in dependencies:
                content = graph.nodes[d]
                command = content["node_command"]
                if command not in safe_commands_before_merge:
                    raise RestrictedPreprocessingViolation(
                        f"For privacy reasons, "
                        f"it is forbidden to do {command} before merging, "
                        f"please change the order of your preprocessing accordingly."
                    )
                else:
                    new_dependencies.extend([x for x in graph.predecessors(d)])
            dependencies = new_dependencies

    @staticmethod
    def validate_graph_has_no_privacy_violations(graph: DiGraph) -> None:
        """Validates the graph and raises a RestrictedPreprocessingViolation as soon as
        a not privacy-preserving function is detected.
        Args:
            graph: the entire graph to be checked
        Raises:
            RestrictedPreprocessingViolation
        """
        for key, content in graph.nodes.items():
            command = content["node_command"]
            if command == NodeCommands.merge.name:
                PrivacyChecker.validate_merge_first(graph, key)
                how = content["node_command_kwargs"]["how"]
                if how in ["cross", "outer"]:
                    raise RestrictedPreprocessingViolation(
                        f"The operation `merge` is non-privacy preserving "
                        f"if used with `how={how}. Please use left, right or inner."
                    )
            elif command == NodeCommands.setitem.name:
                # would allow for singling out attacks
                raise RestrictedPreprocessingViolation(
                    f"The operation '{command}' is not privacy-preserving. "
                    f"Please rewrite the graph to avoid "
                    f"using any {command} functionalities."
                )
            elif command in [
                NodeCommands.add_table.name,
                NodeCommands.add_number.name,
            ]:
                raise RestrictedPreprocessingViolation(
                    f"The operation '{command}' is not privacy preserving, "
                    f"use 'add' instead."
                )
            elif command in [
                NodeCommands.multiply.name,
                NodeCommands.multiply_by_constant.name,
            ]:
                raise RestrictedPreprocessingViolation(
                    f"The operation '{command}' is not privacy preserving, "
                    f"use 'mult' instead."
                )
            elif command in [
                NodeCommands.divide.name,
                NodeCommands.divide_by_constant.name,
            ]:
                raise RestrictedPreprocessingViolation(
                    f"The operation '{command}' is not privacy preserving, "
                    f"use 'truediv' instead."
                )
            elif command == NodeCommands.invert.name:
                raise RestrictedPreprocessingViolation(
                    f"The operation '{command}' is not privacy preserving, "
                    f"use 'invert' instead."
                )
            elif command in [
                NodeCommands.logical_conjunction_table.name,
                NodeCommands.logical_conjunction_number.name,
                NodeCommands.str_contains.name,
                NodeCommands.isin.name,
                NodeCommands.fillna_table,
                NodeCommands.compare_to_table,
                NodeCommands.loc_setter,
                NodeCommands.loc_getter,
                NodeCommands.invert.name,
                NodeCommands.divide.name,
                NodeCommands.divide_by_constant.name,
                NodeCommands.multiply.name,
                NodeCommands.multiply_by_constant.name,
                NodeCommands.prepare_sankey_plot.name,
                NodeCommands.count.name,
                NodeCommands.cumsum.name,
                NodeCommands.sum.name,
                NodeCommands.diff.name,
                NodeCommands.shift.name,
                NodeCommands.rank.name,
                NodeCommands.rolling.name,
                NodeCommands.charlson_comorbidities.name,
                NodeCommands.charlson_comorbidity_score.name,
                NodeCommands.transform_columns.name,
                NodeCommands.concat.name,
                NodeCommands.sample.name,
            ]:
                raise RestrictedPreprocessingViolation(
                    f"The operation '{command}' is not privacy preserving."
                )
            # other commands TBD

import random
from collections import defaultdict
from typing import Optional, Sequence

import torch.fx as fx

from wave_lang.support.logging import get_logger
from ..utils.general_utils import (
    is_shared_write,
    get_shared_memory_operand,
    ceildiv,
    propagate_loop_carried_vars,
)
from ...ops.wave_ops import (
    GatherToLDS,
    GetResult,
    IterArg,
    Write,
    get_custom,
)

logger = get_logger("wave.scheduling.loop_reconstruction_utils")


class ArgumentContext:
    """
    The argument context is used to store the mapping of arguments
    for each modulo pipelining stage.
    """

    def __init__(
        self,
        results: list[fx.Node],
        iter_args: list[fx.Node],
        init_args: list[fx.Node],
        num_stages: int,
    ) -> None:
        self.argument_map: list[list[dict[fx.Node, fx.Node]]] = [
            [{} for _ in range(num_stages)] for _ in range(num_stages)
        ]
        self.results = results
        self.iter_args = iter_args
        self.init_args = init_args
        self.num_stages = num_stages
        self.num_iterations = num_stages
        self.result_to_iter_arg: dict[fx.Node, fx.Node] = {}
        self.result_to_init_arg: dict[fx.Node, fx.Node] = {}

        for result, iter_arg in zip(results, iter_args):
            self.result_to_iter_arg[result] = iter_arg
        for result, init_arg in zip(results, init_args):
            self.result_to_init_arg[result] = init_arg

    def map_arg_all(self, from_: fx.Node, to_: fx.Node | Sequence[fx.Node]) -> None:
        """
        Maps the given argument from one to another into the argument context for all stages
        and for all iterations.
        """
        if isinstance(to_, Sequence):
            count = len(to_)
            for iteration in range(self.num_iterations):
                for stage in range(self.num_stages):
                    self.argument_map[iteration][stage][from_] = to_[iteration % count]
        else:
            for iteration in range(self.num_iterations):
                for stage in range(self.num_stages):
                    self.argument_map[iteration][stage][from_] = to_

    def map_arg_all_after_iteration(
        self, from_: fx.Node, to_: fx.Node, iteration: int
    ) -> None:
        """
        Maps the given argument from one to another into the argument context for all stages
        after the specified iteration.
        """
        for iteration in range(iteration + 1, self.num_iterations):
            for stage in range(self.num_stages):
                self.argument_map[iteration][stage][from_] = to_

    def map_arg_all_iterations(self, stage: int, from_: fx.Node, to_: fx.Node) -> None:
        """
        Maps the given argument from one to another into the argument context for all stages
        and for all iterations.
        """
        for iteration in range(self.num_iterations):
            self.argument_map[iteration][stage][from_] = to_

    def get_mapped_results(self, get_results: list[GetResult]) -> list[fx.Node]:
        """
        Gets the mapped results from the last iteration. If the result is not
        in the last iteration, then get it from the get result nodes.
        """
        mapped_results = []
        for result, get_result in zip(self.results, get_results):
            stage = result.scheduling_parameters["stage"]
            if result not in self.argument_map[self.num_iterations - 1][stage]:
                mapped_results.append(get_result.fx_node)
            else:
                mapped_results.append(
                    self.argument_map[self.num_iterations - 1][stage][result]
                )
        return mapped_results

    def get_kernel_iteration(self, stage: int) -> int:
        """
        Get the iteration from the stage for the kernel.
        """
        return self.num_stages - 1 - stage

    def get_kernel_results(self) -> list[fx.Node]:
        """
        Gets the mapped results for the kernel. Here there
        exists a fixed relationship between the iteration and stage.
        """
        mapped_results = []
        for result in self.results:
            stage = result.scheduling_parameters["stage"]
            iteration = self.get_kernel_iteration(stage)
            mapped_results.append(self.argument_map[iteration][stage][result])
        return mapped_results

    def __setitem__(self, key: tuple[int, fx.Node], value: fx.Node) -> None:
        """
        Sets the argument mapping for the given stage.
        """
        assert isinstance(key, tuple), "Argument context key must be a tuple"
        iteration, stage, from_ = key
        assert iteration < len(
            self.argument_map
        ), f"Iteration {iteration} not yet initialized"
        assert stage < len(self.argument_map), f"Stage {stage} not yet initialized"
        self.argument_map[iteration][stage][from_] = value

    def __getitem__(self, value: tuple[int, fx.Node]) -> fx.Node:
        """
        Gets the argument mapping for the given stage.
        """
        assert isinstance(value, tuple), "Argument context key must be a tuple"
        iteration, stage, key = value
        assert iteration < len(
            self.argument_map
        ), f"Iteration {iteration} not yet initialized"
        assert stage < len(self.argument_map), f"Stage {stage} not yet initialized"
        return self.argument_map[iteration][stage].get(key, None)

    def __contains__(self, key: fx.Node | tuple[int, fx.Node]) -> bool:
        """
        Checks if the argument context contains the given node at a specified
        iteration and stage or at all iterations and stages.
        """
        if isinstance(key, tuple):
            iteration, stage, key = key
            return key in self.argument_map[iteration][stage]
        return any(
            key in self.argument_map[iteration][stage]
            for iteration in range(self.num_iterations)
            for stage in range(self.num_stages)
        )

    def lookup(self, key: fx.Node) -> Optional[fx.Node]:
        """
        Looks up the argument mapping for the given node.
        """
        for iteration in range(self.num_iterations - 1, -1, -1):
            for stage in range(self.num_stages):
                if key in self.argument_map[iteration][stage]:
                    return self.argument_map[iteration][stage][key]
        return None

    def contains_in_iteration(self, iteration: int, key: fx.Node) -> bool:
        """
        Checks if the argument context contains the given node at a specified
        iteration.
        """
        return any(
            key in self.argument_map[iteration][stage]
            for stage in range(self.num_stages)
        )

    def get_from_iteration(self, iteration: int, key: fx.Node, stage: int) -> fx.Node:
        """
        Gets the argument mapping for the given iteration with
        preference to the given stage.
        """

        if stage and key in self.argument_map[iteration][stage]:
            return self.argument_map[iteration][stage][key]

        for stage in range(self.num_stages):
            if key in self.argument_map[iteration][stage]:
                return self.argument_map[iteration][stage][key]
        return None

    def dump(self):
        """
        Dump the argument context to the logger.
        """
        for iteration in range(self.num_iterations):
            for stage in range(self.num_stages):
                logger.debug(f"Iteration: {iteration}, Stage: {stage}")
                for key, value in self.argument_map[iteration][stage].items():
                    logger.debug(f"  {key} -> {value}")


def create_fill_stage_schedule(n: int) -> list[list[int]]:
    """
    Create the schedule of which stages need to be interleaved for the prologue (fill).
    This looks like:
    [0 None None None]
    [1    0 None None]
    [2    1    0 None]
    """
    schedule = []
    for i in range(n - 1):
        row = list(range(i, -1, -1))
        row.extend([None] * (n - i - 1))
        schedule.append(row)
    return schedule


def create_drain_stage_schedule(n: int) -> list[list[int]]:
    """
    Create the schedule of which stages need to be interleaved for the epilogue (drain).
    This looks like:
    [None    3    2 1]
    [None None    3 2]
    [None None None 3]
    """
    schedule = []
    for i in range(n - 1):
        row = [None] * (i + 1)
        row.extend(range(n - 1, i, -1))
        schedule.append(row)
    return schedule


def compute_lifetime(
    graph: fx.Graph, use_absolute_cycle: bool = False
) -> dict[fx.Node, int]:
    """
    Compute number of clocks each node result needs to be alive.
    """
    lifetime: dict[fx.Node, int] = defaultdict(int)
    name = "absolute_cycle" if use_absolute_cycle else "stage"
    for node in graph.nodes:
        custom = get_custom(node)
        if custom.scheduling_parameters is None:
            continue

        node_stage = custom.scheduling_parameters[name]
        for user in custom.users:
            if user.scheduling_parameters is None:
                continue

            user_stage = user.scheduling_parameters[name]
            user_lifetime = user_stage - node_stage

            logger.debug(
                f"Node: {node}, User: {user.fx_node}, lifetime: {user_lifetime}"
            )
            lifetime[node] = max(user_lifetime, lifetime[node])

    return lifetime


def liveness_analysis(graph: fx.Graph) -> dict[fx.Node, int]:
    """
    Perform liveness analysis on the graph to determine the live ranges of
    variables and use that to deduce how many rotating registers we need.
    """
    lifetime: dict[fx.Node, int] = compute_lifetime(graph, use_absolute_cycle=False)

    # Determine how many copies we need for each node. If the lifetime of a node
    # is l clocks and the initiation interval is T, then only ceil(l/T) values
    # of the node can be live at the same time. We need to create copies of only
    # those nodes that are live at more than one stage.
    num_rotating_registers: dict[fx.Node, int] = {}
    for node, l in lifetime.items():
        if node in num_rotating_registers:
            continue
        custom = get_custom(node)
        if is_shared_write(custom):
            continue

        if isinstance(custom, GatherToLDS):
            continue

        if l > 0:
            num_rotating_registers[node] = l

    return num_rotating_registers


def compute_multi_buffer_count(
    graph: fx.Graph, initiation_interval: int, multi_buffer_count: Optional[int] = None
) -> dict[fx.Node, int]:
    """
    Compute the number of buffers needed for each node.
    """
    lifetime: dict[fx.Node, int] = compute_lifetime(graph, use_absolute_cycle=True)
    result: dict[fx.Node, int] = defaultdict(int)
    for node in graph.nodes:
        if not isinstance(get_custom(node), (Write, GatherToLDS)):
            continue

        shared_memory_operand = get_shared_memory_operand(node)
        if shared_memory_operand is None:
            continue

        shared_memory_operand = propagate_loop_carried_vars(shared_memory_operand)
        if multi_buffer_count:
            result[shared_memory_operand] = multi_buffer_count
            continue

        assert node in lifetime, f"Node {node} not found in lifetime"
        # Lifetime returns 0 if node result only used on same clock, 1 if it used on next clock, etc,
        # so we need to add 1 to the lifetime to get the number of clocks the result is live.
        # Ceildiv is required for cases like (lifetime=3, initiation_interval=2) which would otherwise
        # result in buffer_count=1:
        # 000
        #   111
        #     222
        buffer_count = ceildiv(lifetime[node] + 1, initiation_interval)
        logger.debug(f"Node: {node}, Buffer count: {buffer_count}")
        if buffer_count < 2:
            continue

        result[shared_memory_operand] = max(result[shared_memory_operand], buffer_count)

    return result


def partition_graph_by_stage(
    graph: fx.Graph, num_stages: int
) -> list[dict[int, list[fx.Node]]]:
    """
    Partition the graph into stages based on the scheduling parameters.
    """
    partitioned_graph: list[dict[int, list[fx.Node]]] = [
        defaultdict(list) for _ in range(num_stages)
    ]
    for stage in range(num_stages):
        for node in graph.nodes:
            custom = get_custom(node)
            if custom.scheduling_parameters is None:
                continue
            if isinstance(custom, IterArg):
                continue
            if custom.scheduling_parameters["stage"] == stage:
                cycle = custom.scheduling_parameters["cycle"]
                partitioned_graph[stage][cycle].append(node)
    return partitioned_graph


def interleave_instructions(instructions: list[tuple[int, int, fx.Node]]):
    """
    Interleave the instructions that are scheduled in the same cycle.
    Currently, we just randomly shuffle them, but we could also sort
    them based on some criteria.
    """
    rng = random.Random(0)
    # rng.shuffle(instructions)

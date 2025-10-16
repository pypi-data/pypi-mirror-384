"""
This module provides utility functions for handling parameter dependencies and sampling
parameters within specified constraints.

Functions
---------
parse_bounds(bounds: Tuple[Any, Any]) -> Set[str]
    Parse the bounds of a parameter and extract any dependencies.

build_dependency_graph(param_dict: Dict[str, Tuple[Any, Any]]) -> Dict[str, Set[str]]
    Build a dependency graph based on parameter bounds.

topological_sort_util(node: str,
                      visited: Set[str],
                      stack: List[str],
                      graph: Dict[str, Set[str]],
                      temp_marks: Set[str])
                      -> None
    Helper function for performing a depth-first search in the topological sort.

topological_sort(graph: Dict[str, Set[str]]) -> List[str]
    Perform a topological sort on the dependency graph to determine the sampling order.

sample_parameters_from_constraints(param_dict: Dict[str, Tuple[Any, Any]],
                                   sample_size: int)
                                   -> Dict[str, np.ndarray]
    Sample parameters uniformly within specified bounds, respecting any dependencies.
"""  # noqa: D205, D404

from collections import defaultdict
from typing import Any

import numpy as np


def parse_bounds(bounds: tuple[Any, Any]) -> set[str]:
    """
    Parse the bounds of a parameter and extract any dependencies.

    Parameters
    ----------
        bounds (Tuple[Any, Any]): A tuple containing the lower and upper bounds,
                                  numeric or strings, indicating dependencies.

    Returns
    -------
        Set[str]: A set of parameter names that the bounds depend on.
    """
    dependencies = set()
    for value in bounds:
        if isinstance(value, str):
            dependencies.add(value)
    return dependencies


def build_dependency_graph(
    param_dict: dict[str, tuple[Any, Any]],
) -> dict[str, set[str]]:
    """
    Build a dependency graph based on parameter bounds.

    Parameters
    ----------
        param_dict (Dict[str, Tuple[Any, Any]]): A dictionary mapping parameter names
        to their bounds.

    Returns
    -------
        Dict[str, Set[str]]: A dictionary representing the dependency graph where keys
        are parameter names,
                             and values are sets of parameter names they depend on.
    """
    # Note: For the topological sort to work properly
    # we need to construct this graph so that
    # keys represent 'parents' and values represent sets
    # of 'children'!

    # e.g.
    # param_dict = {'a': (0, 5), 'b': (0, 'a'), 'c': ('b', 'a')}
    # resulting graph = {'a': {'b', 'c'}, 'b': {'c'}, 'c': set()}
    graph: dict[str, set[str]] = defaultdict(set)
    all_params = set(param_dict.keys())
    for param, bounds in param_dict.items():
        dependencies = parse_bounds(bounds)
        for dependency in dependencies:
            if dependency not in all_params:
                raise ValueError(f"Parameter '{dependency}' is not defined.")
            else:
                graph[dependency].add(param)
        all_params.update(dependencies)
    # Ensure all parameters are in the graph
    for param in all_params:
        if param not in graph:
            graph[param] = set()
    return graph


def topological_sort_util(
    node: str,
    visited: set[str],
    stack: list[str],
    graph: dict[str, set[str]],
    temp_marks: set[str],
) -> None:
    """
    Helper function for performing a depth-first search in the topological sort.

    Parameters
    ----------
        node (str): The current node being visited.
        visited (Set[str]): Set of nodes that have been permanently marked
        (fully processed).
        stack (List[str]): List representing the ordering of nodes.
        graph (Dict[str, Set[str]]): The dependency graph.
        temp_marks (Set[str]): Set of nodes that have been temporarily marked (currently
         being processed).

    Raises
    ------
        ValueError: If a circular dependency is detected.
    """  # noqa: D401
    if node in temp_marks:
        raise ValueError(f"Circular dependency detected involving '{node}'.")
    if node not in visited:
        temp_marks.add(node)
        for neighbor in graph.get(node, set()):
            topological_sort_util(neighbor, visited, stack, graph, temp_marks)
        temp_marks.remove(node)
        visited.add(node)
        stack.insert(0, node)  # Prepend node to the stack


def topological_sort(graph: dict[str, set[str]]) -> list[str]:
    """
    Perform a topological sort on the dependency graph to determine the sampling order.

    Parameters
    ----------
        graph (Dict[str, Set[str]]): The dependency graph.

    Returns
    -------
        List[str]: A list of parameter names in the order they should be sampled.

    Raises
    ------
        ValueError: If a circular dependency is detected.
    """
    visited: set[str] = set()
    temp_marks: set[str] = set()
    stack: list[str] = []
    for node in graph:
        if node not in visited:
            topological_sort_util(node, visited, stack, graph, temp_marks)
    return stack


def sample_parameters_from_constraints(
    param_dict: dict[str, tuple[Any, Any]], sample_size: int
) -> dict[str, np.ndarray]:
    """
    Sample parameters uniformly within specified bounds, respecting any dependencies.

    Parameters
    ----------
        param_dict (Dict[str, Tuple[Any, Any]]): Dictionary mapping parameter names to
        their bounds.
        sample_size (int): Number of samples to generate.

    Returns
    -------
        Dict[str, np.ndarray]: A dictionary mapping parameter names to arrays of sampled
         values.

    Raises
    ------
        ValueError: If dependencies cannot be resolved due to missing parameters or
         circular dependencies.
    """
    graph = build_dependency_graph(param_dict)
    try:
        sampling_order = topological_sort(graph)
    except ValueError as e:
        raise ValueError(f"Error in topological sorting: {e}") from e

    samples: dict[str, np.ndarray] = {}
    for param in sampling_order:
        # print('sampling :', param)
        bounds = param_dict.get(param)
        if bounds is None:
            # Skip if the parameter wasn't in param_dict (could be a dependency only)
            continue
        lower, upper = bounds

        # Resolve bounds if they are dependent on other parameters
        if isinstance(lower, str):
            if lower in samples:
                lower = samples[lower]
            else:
                raise ValueError(
                    f"Parameter '{lower}' must be defined before '{param}'."
                )
        if isinstance(upper, str):
            if upper in samples:
                upper = samples[upper]
            else:
                raise ValueError(
                    f"Parameter '{upper}' must be defined before '{param}'."
                )

        # Ensure lower bound is less than upper bound
        # TODO: #83 Improve this test to not only operate on sampled but on strict checks!  # noqa: FIX002
        if np.any(lower >= upper):
            raise ValueError(
                f"Lower bound '{lower}' must be less than upper bound '{upper}' for parameter '{param}'."  # noqa: E501
            )

        # Ensure lower and upper are arrays of the correct size
        lower_array = np.full(sample_size, lower) if np.isscalar(lower) else lower
        upper_array = np.full(sample_size, upper) if np.isscalar(upper) else upper

        # Sample uniformly within bounds
        try:
            samples[param] = np.random.uniform(
                low=lower_array, high=upper_array
            ).astype(np.float32)
        except ValueError as e:
            raise ValueError(f"Error sampling parameter '{param}': {e}") from e

    return samples

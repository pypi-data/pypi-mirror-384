"""
A module with a few ready-made data to test on, as well as a few data generators
in view of testing the visualization tools.

https://github.com/cosmograph-org/py_cosmograph/issues/1



- social_network_df: Tests clustering, label weighting, and categorical colors
- scientific_df: Tests numeric color scales and timeline features
- cities_df: Tests geographic-style layouts with lat/lon
- nodes_df + links_df: Tests network visualization with links
- minimal_df: Quick sanity check with minimal configuration

"""

# TODO: Figure out how to only need linked for the tests

# ------------------------------------------------------------------------------
# Point data

from networkx import clustering


# social_network_df: Tests clustering, label weighting, and categorical colors
# scientific_df: Tests numeric color scales and timeline features
# cities_df: Tests geographic-style layouts with lat/lon
# nodes_df + links_df: Tests network visualization with links
# minimal_df: Quick sanity check with minimal configuration
    
from functools import partial
import pandas as pd
import numpy as np

# Example 1: Simple social network with various attributes
social_network_data = {
    'id': ['alice', 'bob', 'charlie', 'diana', 'eve', 'frank', 'grace', 'henry'],
    'label': ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve', 'Frank', 'Grace', 'Henry'],
    'x': [0.1, 0.8, 0.3, 0.7, 0.2, 0.9, 0.4, 0.6],
    'y': [0.2, 0.3, 0.7, 0.8, 0.4, 0.2, 0.9, 0.5],
    'size': [10, 25, 15, 30, 20, 12, 18, 22],
    'color_category': ['A', 'B', 'A', 'B', 'C', 'A', 'C', 'B'],
    'label_weight': [1.0, 2.5, 1.5, 3.0, 2.0, 1.2, 1.8, 2.2],
    'cluster': ['group1', 'group2', 'group1', 'group2', 'group3', 'group1', 'group3', 'group2'],
    'cluster_strength': [0.8, 0.9, 0.7, 0.85, 0.75, 0.8, 0.7, 0.9],
}

social_network_df = pd.DataFrame(social_network_data)

# Usage:
# cosmo(
#     points=social_network_df,
#     point_id_by='id',
#     point_label_by='label',
#     point_x_by='x',
#     point_y_by='y',
#     point_size_by='size',
#     point_color_by='color_category',
#     point_label_weight_by='label_weight',
#     point_cluster_by='cluster',
#     point_cluster_strength_by='cluster_strength',
# )


# Example 2: Scientific data with numeric color values
scientific_data = {
    'id': [f'node_{i}' for i in range(12)],
    'label': [f'Sample {i}' for i in range(12)],
    'x': np.random.rand(12),
    'y': np.random.rand(12),
    'size': np.random.randint(5, 40, 12),
    'color_value': np.random.rand(12) * 100,  # Numeric color mapping
    'label_weight': np.random.rand(12) * 3,
    'timeline': pd.date_range('2024-01-01', periods=12, freq='M').astype(str),
}

scientific_df = pd.DataFrame(scientific_data)

# Usage:
# cosmo(
#     points=scientific_df,
#     point_id_by='id',
#     point_label_by='label',
#     point_x_by='x',
#     point_y_by='y',
#     point_size_by='size',
#     point_color_by='color_value',  # Numeric color scale
#     point_label_weight_by='label_weight',
#     point_timeline_by='timeline',
# )


# Example 3: Cities dataset with indexed approach
cities_data = {
    'city_id': ['NYC', 'LA', 'CHI', 'HOU', 'PHX', 'PHI', 'SA', 'SD'],
    'name': ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia', 'San Antonio', 'San Diego'],
    'population': [8336817, 3979576, 2693976, 2320268, 1680992, 1584064, 1547253, 1423851],
    'region': ['Northeast', 'West', 'Midwest', 'South', 'West', 'Northeast', 'South', 'West'],
    'lat': [40.7128, 34.0522, 41.8781, 29.7604, 33.4484, 39.9526, 29.4241, 32.7157],
    'lon': [-74.0060, -118.2437, -87.6298, -95.3698, -112.0740, -75.1652, -98.4936, -117.1611],
}

cities_df = pd.DataFrame(cities_data)

# Usage:
# cosmo(
#     points=cities_df,
#     point_id_by='city_id',
#     point_label_by='name',
#     point_x_by='lon',
#     point_y_by='lat',
#     point_size_by='population',
#     point_color_by='region',
# )


# Example 4: With links (network visualization)
nodes_data = {
    'id': ['A', 'B', 'C', 'D', 'E', 'F'],
    'label': ['Node A', 'Node B', 'Node C', 'Node D', 'Node E', 'Node F'],
    'size': [20, 15, 25, 18, 22, 16],
    'category': ['type1', 'type2', 'type1', 'type2', 'type3', 'type1'],
}

links_data = {
    'source': ['A', 'A', 'B', 'C', 'D', 'E'],
    'target': ['B', 'C', 'D', 'D', 'E', 'F'],
    'strength': [0.8, 0.6, 0.9, 0.7, 0.5, 0.85],
    'width': [2, 1.5, 3, 2.5, 1, 2.8],
}

nodes_df = pd.DataFrame(nodes_data)
links_df = pd.DataFrame(links_data)

# Usage:
# cosmo(
#     points=nodes_df,
#     links=links_df,
#     point_id_by='id',
#     point_label_by='label',
#     point_size_by='size',
#     point_color_by='category',
#     link_source_by='source',
#     link_target_by='target',
#     link_strength_by='strength',
#     link_width_by='width',
# )


# Example 5: Minimal example for quick testing
minimal_data = {
    'id': [1, 2, 3, 4, 5],
    'label': ['A', 'B', 'C', 'D', 'E'],
    'size': [10, 20, 15, 25, 12],
    'color': ['red', 'blue', 'red', 'green', 'blue'],
}

minimal_df = pd.DataFrame(minimal_data)

# Usage:
# cosmo(
#     points=minimal_df,
#     point_id_by='id',
#     point_label_by='label',
#     point_size_by='size',
#     point_color_by='color',
# )


# ------------------------------------------------------------------------------
# Graph data

from linked import mini_dot_to_graph_jdict as _mini_dot_to_graph_jdict


mini_dot_to_graph_jdict = partial(
    _mini_dot_to_graph_jdict, field_names={'nodes': 'points'}
)


class TestData:
    single_link = {
        'nodes': [{'id': '0'}, {'id': '1'}],
        'links': [{'source': '0', 'target': '1'}],
    }

    small_bipartite_graph = mini_dot_to_graph_jdict(
        """
        1, 2, 3, 4 -> 5, 6, 7
    """
    )

    pentagon = mini_dot_to_graph_jdict(
        """
        1 -> 2
        2 -> 3
        3 -> 4
        4 -> 5
        5 -> 1
    """
    )

    six_path = mini_dot_to_graph_jdict(
        """
        1 -> 2
        2 -> 3
        3 -> 4
        4 -> 5
        5 -> 6
    """
    )


class MkTestData:
    def path(self, n):
        return mini_dot_to_graph_jdict("\n".join(f"{i} -> {i+1}" for i in range(1, n)))

    def cycle(self, n):
        return mini_dot_to_graph_jdict(
            "\n".join(f"{i} -> {i+1}" for i in range(1, n)) + f"\n{n} -> 1"
        )

    def bipartite(self, n, m):
        return mini_dot_to_graph_jdict(
            "\n".join(
                f"{i} -> {j}" for i in range(1, n + 1) for j in range(n + 1, n + m + 1)
            )
        )

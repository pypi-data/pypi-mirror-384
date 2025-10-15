from mison.networks import DevComponentMapping
from mison.miner import Commit, CommitJSONEncoder

from typing import List, Set
from collections import Counter, defaultdict
from statistics import harmonic_mean
from itertools import pairwise
import json

import networkx as nx
from networkx import bipartite


__all__ = ['OrganizationalCoupling', 'LogicalCoupling', 'ComponentCoupling']

class ComponentCoupling(nx.Graph):
    def __init__(self, G):
        super().__init__(G)

    def to_json(self, path):
        net = nx.node_link_data(self, edges="edges")
        with open(path, 'w') as f:
            json.dump(net, f, cls=CommitJSONEncoder, indent=4)

class OrganizationalCoupling(ComponentCoupling):
    """
    Calculate the organizational coupling of components from a `DevComponentMapping` graph.

    This function measures the **organizational coupling** of software components by analyzing
    developer contributions, following the approach described in [1]. The coupling is based on
    two key factors:

    1. **Per-Component Contributions**:
       - For each developer and component, the function quantifies the number of modifications
         the developer has made to that component (microservice).

    2. **Cross-Component Contribution Switching**:
       - For each developer and a **pair of components**, the function counts how often the
         developer has switched contributions between the two components.
       - Higher switching frequency between two components indicates a **stronger organizational coupling**.

    ### Graph Structure:
    - **Nodes**: Components (microservices).
    - **Edges**: Weighted edges represent the **organizational coupling strength** between two components
      based on shared developer contributions.
    - **Edge Weights**: The weight of an edge is determined by the number of contributions and
      contribution switches to given components.

    ### Reference:
    [1] Li, Xiaozhou, Dario Amoroso d’Aragona, and Davide Taibi.
        "Evaluating Microservice Organizational Coupling Based on Cross-Service Contribution."
        *International Conference on Product-Focused Software Process Improvement.*
        Cham: Springer Nature Switzerland, 2023.

    :param G: A `DevComponentMapping` graph representing developer contributions to components.
    :return: A `ComponentCoupling` graph where nodes represent components, and edge weights indicate
             the level of organizational coupling between them.
    """

    def __init__(self, G:DevComponentMapping):
        devs, components = G.devs, G.components
        contribution_switch = defaultdict(float)  # Contributions switches between two components done by dev
        contribution_value = Counter()  # Contribution values for a components by devs
        dev_commits_to_ms = defaultdict(set)
        commits_to_ms_mapping = defaultdict(set)  # Mapping of a commit SHA to the components it touched
        for dev in devs:
            dev_commits_set: set[Commit] = set()
            for _, component, data in G.edges(dev, data=True):
                for commit in data["commits"]:
                    # Developer made this commit
                    dev_commits_set.add(commit)
                    # Developer made this commit to a specific service
                    dev_commits_to_ms[dev, component].add(commit.sha)
                    # Map commit SHA to component it touched
                    commits_to_ms_mapping[commit.sha].add(component)
                    # Calculate contribution value of dev to component by summing over all files of component
                    component_files = G.nodes[component]["files"]
                    contribution_value[(dev, component)] += sum((mod_file.additions + mod_file.deletions)
                                                                for mod_file in commit.modified_files
                                                                if mod_file.path in component_files)

            # Get the list of commits a dev made sequentially
            dev_commits_list: List[Commit] = sorted(dev_commits_set, key=lambda x: x.commit_date)
            # Get the list of components a dev touched with their commits sequentially
            dev_component_list: List[Set[str]] = [commits_to_ms_mapping.get(x.sha) for x in dev_commits_list]
            # Calculate contribution switches
            for prev_commit, next_commit in pairwise(dev_component_list):
                for new_ms in next_commit:
                    for old_ms in prev_commit:
                        if new_ms != old_ms:
                            n = len(dev_commits_to_ms[(dev, new_ms)] | dev_commits_to_ms[(dev, old_ms)])
                            contribution_weight = 1/(2*(n-1)) if n != 1 else 0.5
                            contribution_switch[frozenset([old_ms, new_ms, dev])] += contribution_weight

        def org_coupling(G, u, v):
            weight = 0.0
            for dev in devs:
                weight += contribution_switch.get(frozenset([u, v, dev]), 0.0) * harmonic_mean([contribution_value[(dev, u)], contribution_value[(dev, v)]])
            return weight

        D = bipartite.generic_weighted_projected_graph(G, components, org_coupling)
        super().__init__(D)


class LogicalCoupling(ComponentCoupling):
    """
    Calculate logical coupling between components from a `DevComponentMapping` graph.

    This function constructs a `ComponentCoupling` network where components are considered
    **logically coupled** if they have been modified in the same commit, following the
    approach described in [1].

    ### How Logical Coupling is Measured:
    - **Nodes**: Components (microservices).
    - **Edges**: A weighted edge exists between two components if they were modified together in at least
      one commit.
    - **Edge Weights**: The weight of an edge represents the **number of commits** in which
      the corresponding pair of components was co-modified.

    ### Important Considerations:
    - **Not all commits that co-modify components induce logical coupling** [2].

    ### References:
    [1] d’Aragona, D. A., Pascarella, L., Janes, A., Lenarduzzi, V., & Taibi, D. (2023, March).
        *Microservice logical coupling: A preliminary validation.*
        2023 IEEE 20th International Conference on Software Architecture Companion (ICSA-C), pp. 81-85, IEEE.

    [2] Amoroso d'Aragona, Dario, Xiaozhou Li, and Andrea Janes.
        *Understanding the causes of microservice logical coupling: an exploratory study.*
        Proceedings of the 1st International Workshop on New Trends in Software Architecture, 2024.

    :param G: A `DevComponentMapping` graph representing developer contributions to components.
    :return: A `ComponentCoupling` graph where nodes represent components, and edge weights indicate
             the level of logical coupling between them.
    """

    def __init__(self, G:DevComponentMapping):
        component_commits = defaultdict(set)
        components = G.components
        for component in components:
            for _, _, data in G.edges(component, data=True):
                component_commits[component].update(data["commits"])

        D = bipartite.generic_weighted_projected_graph(G, components, lambda G, u, v: len(component_commits[u] & component_commits[v]))
        super().__init__(D)
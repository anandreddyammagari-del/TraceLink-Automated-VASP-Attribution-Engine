import heapq
import logging
from collections import deque
from typing import Dict, List, Set, Tuple, Any, Optional
import networkx as nx

logger = logging.getLogger(__name__)

class DisjointSetUnion:
    """
    Disjoint Set Union (DSU / Union-Find) with path compression and union-by-rank.
    Enables incremental address cluster merging based on the common-input-ownership heuristic
    without full graph recomputation.
    """
    def __init__(self):
        self.parent: Dict[str, str] = {}
        self.rank: Dict[str, int] = {}
        self.cluster_metadata: Dict[str, Dict[str, Any]] = {}

    def make_set(self, x: str):
        x = x.lower()
        if x not in self.parent:
            self.parent[x] = x
            self.rank[x] = 0
            self.cluster_metadata[x] = {"size": 1, "created_at": None}

    def find(self, x: str) -> str:
        x = x.lower()
        if x not in self.parent:
            self.make_set(x)
            return x
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # Path compression
        return self.parent[x]

    def union(self, x: str, y: str) -> str:
        root_x = self.find(x)
        root_y = self.find(y)

        if root_x == root_y:
            return root_x

        # Union by rank
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
            self.cluster_metadata[root_y]["size"] += self.cluster_metadata[root_x]["size"]
            return root_y
        elif self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
            self.cluster_metadata[root_x]["size"] += self.cluster_metadata[root_y]["size"]
            return root_x
        else:
            self.parent[root_y] = root_x
            self.rank[root_x] += 1
            self.cluster_metadata[root_x]["size"] += self.cluster_metadata[root_y]["size"]
            return root_x

    def get_clusters(self) -> Dict[str, List[str]]:
        clusters: Dict[str, List[str]] = {}
        for element in list(self.parent.keys()):
            root = self.find(element)
            if root not in clusters:
                clusters[root] = []
            clusters[root].append(element)
        return clusters

    def cluster_addresses(self, co_spent_inputs: List[List[str]]) -> Dict[str, List[str]]:
        """
        Apply common-input-ownership heuristic:
        All inputs spent in the same transaction are controlled by the same criminal entity.
        """
        for inputs in co_spent_inputs:
            if not inputs:
                continue
            first = inputs[0].lower()
            self.make_set(first)
            for other in inputs[1:]:
                other_clean = other.lower()
                self.make_set(other_clean)
                self.union(first, other_clean)
        return self.get_clusters()


def build_networkx_graph(nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> nx.DiGraph:
    """Construct a NetworkX directed graph from forensic node and edge lists."""
    G = nx.DiGraph()
    for n in nodes:
        nid = n["id"].lower()
        G.add_node(
            nid,
            label=n.get("label", nid),
            category=n.get("category", "INTERMEDIARY"),
            risk_score=n.get("risk_score", 50.0),
            hop=n.get("hop", 0)
        )
    for e in edges:
        src = e["source"].lower()
        tgt = e["target"].lower()
        G.add_edge(
            src,
            tgt,
            value=float(e.get("value", 0.0)),
            token_symbol=e.get("token_symbol", "ETH"),
            tx_hash=e.get("tx_hash", ""),
            risk_flag=e.get("risk_flag", "NORMAL"),
            is_mixer=("mixer" in str(e.get("risk_flag", "")).lower()),
            timestamp=e.get("timestamp")
        )
    return G


def bfs_nearest_vasp(
    graph: nx.DiGraph,
    root_wallet: str,
    known_vasp_addresses: Set[str],
    max_hops: int = 6
) -> Dict[str, Any]:
    """
    Breadth-First Search (BFS) to identify the unweighted shortest hop-count path
    to the nearest Virtual Asset Service Provider (VASP) deposit cluster.
    """
    root = root_wallet.lower()
    known_vasps = {v.lower() for v in known_vasp_addresses}

    if root not in graph:
        return {"found": False, "reason": "Root wallet not present in graph"}

    queue = deque([(root, [root], 0)])
    visited = {root}

    while queue:
        curr, path, hops = queue.popleft()

        # Check if current node is a known VASP (excluding root)
        if hops > 0 and (curr in known_vasps or graph.nodes.get(curr, {}).get("category") == "VASP"):
            return {
                "found": True,
                "vasp_address": curr,
                "hop_distance": hops,
                "path": path,
                "terminal_node": graph.nodes.get(curr, {})
            }

        if hops < max_hops:
            for neighbor in graph.successors(curr):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor], hops + 1))

    return {"found": False, "reason": f"No known VASP reached within {max_hops} hops"}


def dfs_fan_out_trace(
    graph: nx.DiGraph,
    root_wallet: str,
    max_depth: int = 5
) -> Dict[str, Any]:
    """
    Depth-First Search (DFS) for exhaustive exploration of all fund-splitting
    branches, identifying terminal leaf nodes, layer depths, and peel points.
    """
    root = root_wallet.lower()
    if root not in graph:
        return {"paths": [], "terminal_nodes": [], "max_depth_reached": 0}

    all_paths: List[List[str]] = []
    terminal_nodes: Set[str] = set()

    def dfs(curr: str, current_path: List[str], depth: int):
        successors = list(graph.successors(curr))

        # Check if terminal or reached max depth
        if not successors or depth >= max_depth:
            all_paths.append(list(current_path))
            if not successors:
                terminal_nodes.add(curr)
            return

        for neighbor in successors:
            if neighbor not in current_path:  # Prevent infinite cycle
                dfs(neighbor, current_path + [neighbor], depth + 1)
            else:
                # Cycle detected
                all_paths.append(current_path + [f"CYCLE_{neighbor}"])

    dfs(root, [root], 0)

    max_d = max([len(p) - 1 for p in all_paths]) if all_paths else 0
    return {
        "total_branches": len(all_paths),
        "max_depth_reached": max_d,
        "paths": all_paths,
        "terminal_nodes": list(terminal_nodes)
    }


def dijkstra_confidence_weighted_path(
    graph: nx.DiGraph,
    root_wallet: str,
    target_vasp: str,
    mixer_penalty: float = 10.0,
    hop_penalty: float = 1.0,
    peel_penalty: float = 2.0
) -> Dict[str, Any]:
    """
    Dijkstra's Shortest Path routing where edge weights represent confidence decay penalties.
    Mixer hops, dust values, and high hop counts add large penalties.
    The path with minimal total penalty yields the highest evidentiary attribution confidence.
    """
    root = root_wallet.lower()
    target = target_vasp.lower()

    if root not in graph or target not in graph:
        return {"found": False, "reason": "Root or target not in graph"}

    # Priority queue storing (cumulative_penalty, current_node, path, details)
    pq = [(0.0, root, [root], [])]
    visited_costs = {root: 0.0}

    while pq:
        cost, curr, path, edge_details = heapq.heappop(pq)

        if curr == target:
            # Reached target
            # Confidence decreases exponentially with cost
            confidence_score = max(5.0, round(100.0 * (0.85 ** cost), 2))
            return {
                "found": True,
                "total_penalty": round(cost, 2),
                "confidence_score": confidence_score,
                "path": path,
                "edge_details": edge_details
            }

        for neighbor in graph.successors(curr):
            edge_data = graph.get_edge_data(curr, neighbor) or {}
            
            # Calculate penalty for this hop
            step_penalty = hop_penalty
            if edge_data.get("is_mixer") or "mixer" in str(edge_data.get("risk_flag", "")).lower():
                step_penalty += mixer_penalty
            if "peel" in str(edge_data.get("risk_flag", "")).lower():
                step_penalty += peel_penalty
            if edge_data.get("value", 1.0) < 0.01:  # Dust transaction penalty
                step_penalty += 3.0

            new_cost = cost + step_penalty
            if neighbor not in visited_costs or new_cost < visited_costs[neighbor]:
                visited_costs[neighbor] = new_cost
                new_edge_info = {
                    "from": curr,
                    "to": neighbor,
                    "value": edge_data.get("value", 0.0),
                    "token": edge_data.get("token_symbol", "ETH"),
                    "risk_flag": edge_data.get("risk_flag", "NORMAL"),
                    "hop_penalty": step_penalty
                }
                heapq.heappush(pq, (new_cost, neighbor, path + [neighbor], edge_details + [new_edge_info]))

    return {"found": False, "reason": "No path exists between root wallet and target VASP"}


def calculate_centrality_metrics(graph: nx.DiGraph) -> Dict[str, Dict[str, float]]:
    """
    Compute PageRank and Betweenness Centrality to surface critical mule aggregators
    and high-velocity intermediary nodes.
    """
    if len(graph) == 0:
        return {}

    try:
        pagerank = nx.pagerank(graph, alpha=0.85, max_iter=100)
    except Exception:
        pagerank = {n: 1.0 / len(graph) for n in graph.nodes()}

    try:
        betweenness = nx.betweenness_centrality(graph)
    except Exception:
        betweenness = {n: 0.0 for n in graph.nodes()}

    metrics = {}
    for node in graph.nodes():
        metrics[node] = {
            "pagerank": round(pagerank.get(node, 0.0), 4),
            "betweenness": round(betweenness.get(node, 0.0), 4),
            "in_degree": graph.in_degree(node),
            "out_degree": graph.out_degree(node)
        }
    return metrics

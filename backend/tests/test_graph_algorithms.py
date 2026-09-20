import pytest
import networkx as nx
from backend.services.graph_algorithms import (
    DisjointSetUnion,
    build_networkx_graph,
    bfs_nearest_vasp,
    dfs_fan_out_trace,
    dijkstra_confidence_weighted_path,
    calculate_centrality_metrics
)
from backend.services.chainalysis_service import KnownEntityService, known_entity_service
from backend.services.neo4j_service import neo4j_service

def test_union_find_address_clustering():
    dsu = DisjointSetUnion()
    
    # Simulate transaction 1 co-spending inputs A and B
    # Simulate transaction 2 co-spending inputs B and C
    # Expected: A, B, and C are merged into the same criminal cluster
    co_spent = [
        ["0xaddr_a", "0xaddr_b"],
        ["0xaddr_b", "0xaddr_c"],
        ["0xaddr_x", "0xaddr_y"]
    ]
    clusters = dsu.cluster_addresses(co_spent)
    
    # A, B, C must share the same root cluster
    root_a = dsu.find("0xaddr_a")
    root_b = dsu.find("0xaddr_b")
    root_c = dsu.find("0xaddr_c")
    assert root_a == root_b == root_c
    
    # X and Y must share a different root cluster
    root_x = dsu.find("0xaddr_x")
    root_y = dsu.find("0xaddr_y")
    assert root_x == root_y
    assert root_a != root_x

def test_bfs_shortest_hop_to_vasp():
    nodes = [
        {"id": "0xroot", "category": "SUSPECT_WALLET"},
        {"id": "0xhop1", "category": "INTERMEDIARY"},
        {"id": "0xhop2", "category": "INTERMEDIARY"},
        {"id": "0xvasp_direct", "category": "VASP"},
        {"id": "0xvasp_distant", "category": "VASP"}
    ]
    edges = [
        {"source": "0xroot", "target": "0xvasp_direct", "value": 5.0},     # 1-hop path
        {"source": "0xroot", "target": "0xhop1", "value": 10.0},
        {"source": "0xhop1", "target": "0xhop2", "value": 8.0},
        {"source": "0xhop2", "target": "0xvasp_distant", "value": 7.5}     # 3-hop path
    ]
    G = build_networkx_graph(nodes, edges)
    vasps = {"0xvasp_direct", "0xvasp_distant"}

    result = bfs_nearest_vasp(G, "0xroot", vasps, max_hops=4)
    assert result["found"] is True
    assert result["vasp_address"] == "0xvasp_direct"
    assert result["hop_distance"] == 1
    assert result["path"] == ["0xroot", "0xvasp_direct"]

def test_dfs_fan_out_and_cycle_prevention():
    nodes = [
        {"id": "0xroot"},
        {"id": "0xbranch1"},
        {"id": "0xbranch2"},
        {"id": "0xleaf1"},
        {"id": "0xleaf2"}
    ]
    edges = [
        {"source": "0xroot", "target": "0xbranch1", "value": 10.0},
        {"source": "0xroot", "target": "0xbranch2", "value": 5.0},
        {"source": "0xbranch1", "target": "0xleaf1", "value": 9.5},
        {"source": "0xbranch2", "target": "0xleaf2", "value": 4.8},
        {"source": "0xleaf2", "target": "0xroot", "value": 0.1} # Intentional cycle back to root
    ]
    G = build_networkx_graph(nodes, edges)

    result = dfs_fan_out_trace(G, "0xroot", max_depth=4)
    assert result["total_branches"] >= 2
    assert "0xleaf1" in result["terminal_nodes"]
    # Ensure cycle was caught and did not cause infinite loop
    assert any("CYCLE" in str(p) for p in result["paths"])

def test_dijkstra_penalizes_mixer_path():
    # Construct 2 alternate paths from root to VASP:
    # Path 1: 0xroot -> 0xclean1 -> 0xclean2 -> 0xvasp (3 hops, clean)
    # Path 2: 0xroot -> 0xmixer -> 0xvasp (2 hops, but traverses mixer)
    # Dijkstra should prefer Path 1 despite more hops because mixer carries penalty!
    nodes = [
        {"id": "0xroot"},
        {"id": "0xclean1"},
        {"id": "0xclean2"},
        {"id": "0xmixer", "category": "MIXER"},
        {"id": "0xvasp", "category": "VASP"}
    ]
    edges = [
        {"source": "0xroot", "target": "0xclean1", "value": 10.0, "risk_flag": "CLEAN"},
        {"source": "0xclean1", "target": "0xclean2", "value": 9.8, "risk_flag": "CLEAN"},
        {"source": "0xclean2", "target": "0xvasp", "value": 9.5, "risk_flag": "VASP_DEPOSIT"},
        {"source": "0xroot", "target": "0xmixer", "value": 10.0, "risk_flag": "TORNADO_MIXER"},
        {"source": "0xmixer", "target": "0xvasp", "value": 9.0, "risk_flag": "VASP_DEPOSIT"}
    ]
    G = build_networkx_graph(nodes, edges)

    result = dijkstra_confidence_weighted_path(G, "0xroot", "0xvasp", mixer_penalty=15.0, hop_penalty=1.0)
    assert result["found"] is True
    # The clean path has penalty 1 + 1 + 1 = 3.0
    # The mixer path has penalty (1 + 15) + 1 = 17.0
    # Therefore, optimal path MUST be the clean path!
    assert result["path"] == ["0xroot", "0xclean1", "0xclean2", "0xvasp"]
    assert result["confidence_score"] > 50.0

def test_known_entity_identification():
    service = KnownEntityService()
    
    # Test WazirX known cluster
    wazirx_addr = "0x503828976d22510aad0201ac7ec88293211d23dc"
    vasp = service.identify_vasp(wazirx_addr)
    assert vasp is not None
    assert "WazirX" in vasp["vasp_name"]
    assert vasp["fiu_registered"] is True

    # Test Tornado Cash Mixer
    tornado_addr = "0x7f367cc41522ce07553e823bf3be79a889debe1b"
    assert service.is_mixer(tornado_addr) is True
    cat_mixer = service.categorize_address(tornado_addr)
    assert cat_mixer["category"] == "MIXER"
    assert cat_mixer["risk_score"] > 90.0

    # Test Wormhole Bridge
    wormhole_addr = "0x98f3c9e6e3face36baad05fe09d375ef14642f88"
    assert service.is_bridge(wormhole_addr) is True
    cat_bridge = service.categorize_address(wormhole_addr)
    assert cat_bridge["category"] == "BRIDGE"

def test_centrality_metrics():
    nodes = [{"id": "0xroot"}, {"id": "0xmule_hub"}, {"id": "0xleafA"}, {"id": "0xleafB"}]
    edges = [
        {"source": "0xroot", "target": "0xmule_hub", "value": 10.0},
        {"source": "0xmule_hub", "target": "0xleafA", "value": 5.0},
        {"source": "0xmule_hub", "target": "0xleafB", "value": 5.0}
    ]
    G = build_networkx_graph(nodes, edges)
    metrics = calculate_centrality_metrics(G)
    assert "0xmule_hub" in metrics
    # Mule hub has highest betweenness in this star topology
    assert metrics["0xmule_hub"]["betweenness"] > metrics["0xroot"]["betweenness"]

def test_neo4j_offline_graceful_fallback():
    # Even without Neo4j running, calls must record locally without crashing
    neo4j_service.connect()
    neo4j_service.save_wallet_node("0xtestaddr", "SUSPECT_WALLET", 85.0, "CASE_1")
    neo4j_service.save_transaction_edge("0xtest1", "0xtest2", 1.5, "0xtx1", case_id="CASE_1")
    neo4j_service.save_transaction_edge("0xtest2", "0xtest3", 1.5, "0xtx2", case_id="CASE_2")
    
    # 0xtest2 appears in both CASE_1 and CASE_2
    cross_case = neo4j_service.find_cross_case_wallets()
    assert len(cross_case) >= 1
    assert any(w["address"] == "0xtest2" for w in cross_case)

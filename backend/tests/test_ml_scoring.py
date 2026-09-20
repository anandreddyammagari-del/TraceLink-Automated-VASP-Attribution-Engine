import pytest
from backend.services.ml_scoring import MLConfidenceEngine

def test_ml_scoring_initialization_and_training():
    engine = MLConfidenceEngine()
    assert engine.regressor is not None
    assert engine.anomaly_detector is not None
    assert engine._is_trained is True

def test_structuring_anomaly_detection():
    engine = MLConfidenceEngine()
    
    # Normal transaction: 10 ETH over 2 hours (7200 seconds)
    normal_score = engine.detect_structuring_anomaly(amount=10.0, delta_seconds=7200, output_count=1)
    
    # Smurfing pattern: 0.99 ETH transferred in 8 seconds with 20 fan-out outputs
    smurf_score = engine.detect_structuring_anomaly(amount=0.99, delta_seconds=8, output_count=20)
    
    assert 0.0 <= normal_score <= 1.0
    assert 0.0 <= smurf_score <= 1.0
    assert smurf_score > normal_score

def test_high_confidence_direct_vasp_attribution():
    engine = MLConfidenceEngine()
    
    # 1 hop, 95% volume preserved, no mixer, known cluster
    res = engine.calculate_confidence(
        hop_count=1,
        initial_volume=10.0,
        arriving_volume=9.5,
        time_delta_hours=1.0,
        mixer_hops=0,
        peel_layer_depth=0,
        is_known_cluster=True,
        anomaly_score=0.1
    )
    
    assert res["confidence_score"] >= 80.0
    assert res["confidence_tier"] == "HIGH"
    assert any("verified FIU-registered VASP" in factor for factor in res["evidence_breakdown"])
    assert any("Zero privacy mixer" in factor for factor in res["evidence_breakdown"])

def test_mixer_traversal_penalizes_confidence_to_low():
    engine = MLConfidenceEngine()
    
    # 2 hops, but traversed a mixer!
    res = engine.calculate_confidence(
        hop_count=2,
        initial_volume=10.0,
        arriving_volume=8.0,
        time_delta_hours=3.0,
        mixer_hops=1,
        peel_layer_depth=0,
        is_known_cluster=True,
        anomaly_score=0.2
    )
    
    # Traversed mixer must drop score to LOW (< 50.0%)
    assert res["confidence_score"] < 50.0
    assert res["confidence_tier"] == "LOW"
    assert any("CRITICAL OBFUSCATION DETECTED" in factor for factor in res["evidence_breakdown"])

def test_unverified_cluster_penalty():
    engine = MLConfidenceEngine()
    
    # Same parameters, but is_known_cluster = False vs True
    res_known = engine.calculate_confidence(
        hop_count=2,
        initial_volume=10.0,
        arriving_volume=8.0,
        time_delta_hours=5.0,
        mixer_hops=0,
        peel_layer_depth=1,
        is_known_cluster=True
    )
    
    res_unverified = engine.calculate_confidence(
        hop_count=2,
        initial_volume=10.0,
        arriving_volume=8.0,
        time_delta_hours=5.0,
        mixer_hops=0,
        peel_layer_depth=1,
        is_known_cluster=False
    )
    
    assert res_known["confidence_score"] > res_unverified["confidence_score"]
    assert any("unverified or secondary cluster" in factor for factor in res_unverified["evidence_breakdown"])

def test_confidence_score_boundaries():
    engine = MLConfidenceEngine()
    
    # Extreme bad case
    res_bad = engine.calculate_confidence(
        hop_count=8,
        initial_volume=100.0,
        arriving_volume=0.01,
        time_delta_hours=200.0,
        mixer_hops=3,
        peel_layer_depth=6,
        is_known_cluster=False,
        anomaly_score=0.9
    )
    assert 0.0 <= res_bad["confidence_score"] <= 100.0
    assert res_bad["confidence_tier"] == "LOW"

    # Extreme perfect case
    res_good = engine.calculate_confidence(
        hop_count=1,
        initial_volume=50.0,
        arriving_volume=50.0,
        time_delta_hours=0.1,
        mixer_hops=0,
        peel_layer_depth=0,
        is_known_cluster=True,
        anomaly_score=0.05
    )
    assert 0.0 <= res_good["confidence_score"] <= 100.0
    assert res_good["confidence_tier"] == "HIGH"

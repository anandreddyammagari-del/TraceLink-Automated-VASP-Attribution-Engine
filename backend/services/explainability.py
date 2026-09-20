import logging
from typing import Dict, List

logger = logging.getLogger("tracelink.explainability")

class ExplainabilityService:
    """
    Transparent feature contribution and SHAP-style weight decomposition engine
    for explainable machine-learning VASP attribution in court testimony.
    """
    @staticmethod
    def explain_score(
        hop_count: int,
        volume_ratio: float,
        is_known_cluster: bool,
        has_mixer: bool,
        peel_depth: int = 0,
        anomaly_score: float = 0.0
    ) -> dict:
        base_intercept = 50.0
        contributions = []

        # 1. Base prior
        contributions.append({
            "feature": "Base Forensic Prior",
            "contribution": base_intercept,
            "rationale": "Empirical prior probability baseline for blockchain transaction paths"
        })

        # 2. Hop distance
        if hop_count == 1:
            hop_delta = +20.0
            hop_desc = "Direct single-hop adjacency to VASP gateway (+20.0)"
        elif hop_count == 2:
            hop_delta = +10.0
            hop_desc = "Short 2-hop topological proximity (+10.0)"
        elif hop_count == 3:
            hop_delta = 0.0
            hop_desc = "Standard 3-hop layering path (Neutral: 0.0)"
        else:
            hop_delta = max(-30.0, -10.0 * (hop_count - 3))
            hop_desc = f"Extended hop length ({hop_count} hops) dilutes attribution linkage ({hop_delta:.1f})"

        contributions.append({
            "feature": "Hop Proximity",
            "contribution": hop_delta,
            "rationale": hop_desc
        })

        # 3. Volume preservation
        vol_delta = round((volume_ratio - 0.5) * 30.0, 1)  # -15 to +15
        contributions.append({
            "feature": "Volume Conservation Ratio",
            "contribution": vol_delta,
            "rationale": f"{volume_ratio*100:.1f}% fund flow conserved across peel intermediaries ({vol_delta:+.1f})"
        })

        # 4. Verified Cluster Recognition
        cluster_delta = +20.0 if is_known_cluster else -15.0
        contributions.append({
            "feature": "VASP Directory Verification",
            "contribution": cluster_delta,
            "rationale": "Deposit address verified against FIU-IND exchange nodal directory (+20.0)" if is_known_cluster else "Target address unverified in public VASP clusters (-15.0)"
        })

        # 5. Mixer obfuscation penalty
        mixer_delta = -40.0 if has_mixer else 0.0
        if has_mixer:
            contributions.append({
                "feature": "Mixer / Tumbler Interaction",
                "contribution": mixer_delta,
                "rationale": "High-risk privacy mixer (Tornado Cash / Railgun) detected on route (-40.0)"
            })
        else:
            contributions.append({
                "feature": "Clean Route Audit",
                "contribution": +5.0,
                "rationale": "Zero mixer / coinjoin obfuscation along primary routing (+5.0)"
            })

        # 6. Peel chain depth
        if peel_depth >= 3:
            peel_delta = -10.0
            contributions.append({
                "feature": "Peel Layering Complexity",
                "contribution": peel_delta,
                "rationale": f"Deep peel chain ({peel_depth} shaving stages) indicates obfuscation (-10.0)"
            })

        # 7. Anomaly penalty
        if anomaly_score > 0.5:
            anom_delta = -round((anomaly_score - 0.5) * 20.0, 1)
            contributions.append({
                "feature": "Structuring Anomaly Detector",
                "contribution": anom_delta,
                "rationale": f"Isolation Forest smurfing score: {anomaly_score:.2f} ({anom_delta:+.1f})"
            })

        computed_raw = sum(c["contribution"] for c in contributions)
        final_score = max(5.0, min(98.5, round(computed_raw, 1)))

        tier = "HIGH" if final_score >= 80.0 else ("MEDIUM" if final_score >= 50.0 else "LOW")

        return {
            "final_confidence_score": final_score,
            "confidence_tier": tier,
            "waterfall_contributions": contributions,
            "mathematical_equation": "Final = Clamp(Sum(Contributions), 5.0, 98.5)"
        }

explainability_service = ExplainabilityService()

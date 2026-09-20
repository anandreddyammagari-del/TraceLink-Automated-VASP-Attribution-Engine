import logging
from typing import Optional, Tuple

logger = logging.getLogger("tracelink.poisoning")

class AddressPoisoningDetector:
    """
    Detects address poisoning and vanity dust attacks designed to pollute
    investigator transaction histories and trick victims.
    """
    DUST_THRESHOLD_ETH = 0.0002
    DUST_THRESHOLD_USD = 0.50

    @classmethod
    def calculate_vanity_similarity(cls, addr1: str, addr2: str) -> dict:
        """
        Compares two hex addresses for vanity prefix and suffix character matches.
        """
        a1 = addr1.lower().strip()
        a2 = addr2.lower().strip()

        if a1 == a2:
            return {"exact_match": True, "prefix_match_len": len(a1), "suffix_match_len": len(a1), "is_spoofed_vanity": False}

        # Check prefix match (skipping 0x)
        p1 = a1[2:] if a1.startswith("0x") else a1
        p2 = a2[2:] if a2.startswith("0x") else a2

        prefix_len = 0
        for c1, c2 in zip(p1, p2):
            if c1 == c2:
                prefix_len += 1
            else:
                break

        # Check suffix match
        suffix_len = 0
        for c1, c2 in zip(reversed(p1), reversed(p2)):
            if c1 == c2:
                suffix_len += 1
            else:
                break

        # If prefix >= 4 and suffix >= 4 and middle differs -> classic vanity poisoning signature
        is_spoofed = (prefix_len >= 4 and suffix_len >= 4 and a1 != a2)

        return {
            "exact_match": False,
            "prefix_match_len": prefix_len,
            "suffix_match_len": suffix_len,
            "is_spoofed_vanity": is_spoofed
        }

    @classmethod
    def is_poisoning_transaction(cls, tx: dict, legitimate_addresses: list[str]) -> Tuple[bool, str]:
        """
        Evaluates if a transaction is a zero-value or dust poisoning attempt.
        Returns (is_poisoning: bool, rationale: str)
        """
        val = float(tx.get("value", 0.0))
        to_addr = (tx.get("to_address") or "").lower()
        from_addr = (tx.get("from_address") or "").lower()

        # Zero value or dust amount
        is_dust = (val <= cls.DUST_THRESHOLD_ETH)

        if not is_dust:
            return False, "Standard transaction value."

        for legit in legitimate_addresses:
            sim = cls.calculate_vanity_similarity(to_addr, legit)
            if sim["is_spoofed_vanity"]:
                return True, f"Address poisoning vanity match: {to_addr[:6]}...{to_addr[-4:]} mimics legitimate address {legit[:6]}...{legit[-4:]}"

            from_sim = cls.calculate_vanity_similarity(from_addr, legit)
            if from_sim["is_spoofed_vanity"]:
                return True, f"Inbound poisoning vanity match: sender mimics legitimate address {legit[:6]}...{legit[-4:]}"

        if val == 0.0:
            return True, "Zero-value token transfer signature."

        return False, "Low-value but no vanity spoofing detected."

poisoning_detector = AddressPoisoningDetector()

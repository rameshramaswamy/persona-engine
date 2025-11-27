import yaml
from pathlib import Path
from typing import Dict
from src.core.config import settings

class PolicyEngine:
    def __init__(self):
        # Load local policy definition
        policy_path = Path(__file__).parent.parent.parent / "data/policies/standard.yaml"
        with open(policy_path, 'r') as f:
            self.rules = yaml.safe_load(f)

    def evaluate(self, risk_scores: Dict[str, float], context: Dict) -> tuple[bool, str]:
        """
        Decides Allow/Block based on Risk Scores + Context (User Region, Tier).
        Returns: (is_allowed, reason)
        """
        user_region = context.get("region", "US")
        user_tier = context.get("tier", "free")

        # 1. Critical Failures (Global)
        if risk_scores.get("severe_toxicity", 0) > 0.9:
            return False, "Content flagged as severely toxic."

        # 2. Regional Compliance (e.g., GDPR or stricter regions)
        if user_region in ["AE", "CN", "SA"]:
            if risk_scores.get("sexual_explicit", 0) > 0.5:
                return False, "Content restricted in your region."

        # 3. Enterprise vs Free Tier
        # Free users have stricter filters to save costs/reputation
        threshold = settings.TOXICITY_THRESHOLD
        if user_tier == "enterprise":
            threshold = 0.99 # Relaxed for trusted enterprise users
        
        if risk_scores.get("toxicity", 0) > threshold:
            return False, "Content flagged as toxic."

        return True, "Safe"
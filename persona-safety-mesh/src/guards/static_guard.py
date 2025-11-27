from flashtext import KeywordProcessor
import re
import logging

logger = logging.getLogger("safety_mesh")

class StaticGuard:
    def __init__(self):
        # 1. FlashText for Blocklist
        self.keyword_processor = KeywordProcessor()
        # In prod, load this from a generic_banlist.txt
        self.keyword_processor.add_keywords_from_list([
            "badword1", "slur_a", "slur_b", "kill_yourself"
        ])

        # 2. Regex for PII (Simple, fast patterns)
        self.pii_patterns = {
            "EMAIL": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            "PHONE": re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
            "SSN":   re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
        }

    def sanitize(self, text: str) -> tuple[str, bool, str]:
        """
        Returns: (sanitized_text, is_blocked, reason)
        """
        # 1. Check Blocklist (Circuit Breaker)
        # extract_keywords is incredibly fast
        found_keywords = self.keyword_processor.extract_keywords(text)
        if found_keywords:
            return text, True, f"Blocked keywords found: {found_keywords[:3]}"

        # 2. Scrub PII
        # We don't block PII, we redact it so the model is safe to use.
        sanitized_text = text
        for pii_type, pattern in self.pii_patterns.items():
            sanitized_text = pattern.sub(f"<{pii_type}_REDACTED>", sanitized_text)
        
        return sanitized_text, False, None
import time
from src.guards.input_scanner import InputScanner
from src.guards.static_guard import StaticGuard
from src.policy.engine import PolicyEngine
from src.core.audit import log_safety_event
from fastapi import BackgroundTasks

class SafetyMesh:
    def __init__(self):
        self.static = StaticGuard()
        self.scanner = InputScanner() # ONNX
        self.policy = PolicyEngine()

    async def check_input(self, text: str, context: dict, background_tasks: BackgroundTasks) -> dict:
        start_time = time.perf_counter()
        user_id = context.get("user_id", "anon")
        
        # 1. OPTIMIZATION: Static Circuit Breaker (Microseconds)
        safe_text, is_blocked, reason = self.static.sanitize(text)
        
        if is_blocked:
            # Audit Log (Async)
            background_tasks.add_task(
                log_safety_event, user_id, text, {"static_ban": 1.0}, "BLOCKED_STATIC", 0.1
            )
            return {"allowed": False, "reason": reason, "text": text}

        # 2. Neural Scan (Milliseconds)
        # We use the sanitized text (PII removed) for the model
        risk_scores = await self.scanner.scan(safe_text)
        
        # 3. Policy Evaluation
        allowed, policy_reason = self.policy.evaluate(risk_scores, context)
        
        # 4. Audit Log (Async)
        latency = (time.perf_counter() - start_time) * 1000
        decision = "ALLOWED" if allowed else "BLOCKED_MODEL"
        
        background_tasks.add_task(
            log_safety_event, user_id, text, risk_scores, decision, latency
        )

        return {
            "allowed": allowed, 
            "reason": policy_reason, 
            "text": safe_text # Return sanitized text to be sent to LLM
        }
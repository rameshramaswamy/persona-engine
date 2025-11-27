import asyncio
from src.memory.cache_manager import CacheManager
from src.memory.vector_store import LoreStore

class RagEngine:
    def __init__(self):
        # In prod, use dependency injection/settings
        self.cache = CacheManager(host="redis") 
        self.lore = LoreStore(host="qdrant")
        
        # OPTIMIZATION: Budget constants (Llama-3 8k context)
        self.MAX_CONTEXT_TOKENS = 6000 # Leave 2k for generation
        self.EST_CHARS_PER_TOKEN = 4   # Rough heuristic (faster than running tokenizer)

    async def prepare_context(self, session_id: str, char_id: str, user_input: str) -> dict:
        """
        Parallel fetch + Token Budgeting.
        """
        # 1. Run fetches in parallel
        # We start the search task but await them together
        history_task = asyncio.create_task(self.cache.get_history(session_id))
        lore_task = asyncio.create_task(self.lore.search_lore(char_id, user_input))
        
        # Write user input to cache in background (fire and forget)
        asyncio.create_task(self.cache.add_message(session_id, "user", user_input))

        history, lore_text = await asyncio.gather(history_task, lore_task)

        # 2. Token Budgeting Strategy
        # Priority: System Prompt > Lore > Recent History > Old History
        
        budget = self.MAX_CONTEXT_TOKENS
        
        # Calculate Lore cost
        lore_tokens = len(lore_text) / self.EST_CHARS_PER_TOKEN
        if lore_tokens > 1000:
            # Truncate lore if it's somehow massive (safety net)
            lore_text = lore_text[:4000] 
            budget -= 1000
        else:
            budget -= lore_tokens

        # Prune History to fit remaining budget
        pruned_history = []
        current_tokens = 0
        
        # Iterate backwards (newest first)
        for msg in reversed(history):
            msg_len = len(msg['content']) / self.EST_CHARS_PER_TOKEN
            if current_tokens + msg_len > budget:
                break
            pruned_history.insert(0, msg)
            current_tokens += msg_len

        return {
            "history": pruned_history,
            "lore": lore_text
        }
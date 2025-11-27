from src.memory.vector_store import LoreStore
from src.memory.cache_manager import CacheManager
import asyncio

def setup_lore():
    print("📚 Ingesting Lore into Qdrant...")
    store = LoreStore(host="localhost", port=6333)
    
    char_id = "elara"
    lore_chunks = [
        "Elara was born in the Obsidian Spire during the Great Eclipse.",
        "She hates spiders because one bit her when she was casting a fireball.",
        "Her secret weakness is that she cannot lie on a full moon."
    ]
    
    for chunk in lore_chunks:
        store.add_lore(char_id, chunk)
        print(f"   -> Ingested: {chunk[:30]}...")
    
    # Test Retrieval
    print("\n🔍 Testing Retrieval:")
    results = store.search_lore(char_id, "Does she like spiders?")
    print(f"   Query: 'Does she like spiders?'\n   Result: {results}")

async def test_redis():
    print("\n💾 Testing Redis Session...")
    cache = CacheManager(host="localhost", port=6379)
    await cache.add_message("session_123", "user", "Hello!")
    hist = await cache.get_history("session_123")
    print(f"   History: {hist}")

if __name__ == "__main__":
    setup_lore()
    asyncio.run(test_redis())
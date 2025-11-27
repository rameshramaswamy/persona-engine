import time
import asyncio
import uuid
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, BackgroundTasks
from starlette.websockets import WebSocketState

# --- Internal Modules ---
from src.core.config import settings
from src.core.utils import fast_json_dumps
from src.services.prompt_engine import PromptEngine
from src.services.inference_client import InferenceClient
from src.memory.rag_engine import RagEngine
from src.memory.cache_manager import CacheManager
# Phase 3 Safety Modules
from src.manager import SafetyMesh  # The unified Safety Manager
from src.guards.input_scanner import InputScanner # Needed for output streaming check
from src.auth.deps import get_current_user
from src.middleware.rate_limit import RateLimiter


# Setup Logger
logger = logging.getLogger("uvicorn")

# Initialize Router
router = APIRouter()

# --- Optimization: Token Buffer ---
class TokenBuffer:
    """
    Aggregates small tokens into chunks to reduce WebSocket frame overhead.
    Nagle's algorithm adapted for LLM streaming.
    """
    def __init__(self, websocket: WebSocket, threshold: int = 20):
        self.ws = websocket
        self.buffer = []
        self.threshold = threshold

    async def push(self, token: str):
        self.buffer.append(token)
        current_text = "".join(self.buffer)
        
        # Flush if size limit reached or natural pause (punctuation/newline)
        if len(current_text) >= self.threshold or token in [" ", "\n", ".", ",", "!", "?"]:
            await self.flush()
    
    async def flush(self):
        if self.buffer:
            text = "".join(self.buffer)
            # Check connection state before sending to avoid runtime errors
            if self.ws.client_state == WebSocketState.CONNECTED:
                await self.ws.send_text(text)
            self.buffer = []

# --- Main WebSocket Endpoint ---
@router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    # 1. Auth Handshake (Query Param or Header Protocol)
    # WebSockets don't allow headers easily in JS, so we use protocols or query params
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return
    
    # Validate Token
    try:
        user = oauth2_scheme.decode_token(token)
        if not user:
            raise Exception("Invalid Token")
    except:
        await websocket.close(code=1008)
        return

    # 2. Rate Limit Check
    limiter = RateLimiter(host="redis")
    try:
        # Limit: 60 messages per minute per user
        await limiter.check_limit(f"user:{user['sub']}", 60, 60)
    except HTTPException:
        await websocket.close(code=1008, reason="Rate Limit Exceeded")
        return

    await websocket.accept()



    await websocket.accept()
    
    # 1. Session Initialization
    request_id = str(uuid.uuid4())
    session_id = websocket.query_params.get("session_id", "default_session")
    # In a real app, char_id comes from the client init payload or URL
    char_id = websocket.query_params.get("char_id", "mistral_base") 
    
    logger.info(f"🔌 WS Connected | ReqID: {request_id} | Session: {session_id}")

    # 2. Instantiate Services (Scoped to Request or Singletons)
    prompt_engine = PromptEngine()
    inference_client = InferenceClient()
    rag_engine = RagEngine()
    cache_manager = CacheManager(host="redis") # For saving assistant replies
    safety_mesh = SafetyMesh() # Phase 3: Input/Policy Guard
    output_scanner = InputScanner() # Phase 3: Fast Output Guard (ONNX)

    # Metrics
    session_start = time.time()
    turns_count = 0

    try:
        while True:
            # --- A. Receive User Input ---
            try:
                raw_data = await websocket.receive_text()
            except WebSocketDisconnect:
                break # Clean exit
            
            turns_count += 1
            turn_start = time.perf_counter()
            
            # --- B. Phase 3: Safety Shield (Input) ---
            # Create a localized BackgroundTasks container since WS doesn't inject it
            bg_tasks = BackgroundTasks()
            
            # Context for policy engine (e.g., user region from auth token)
            # In prod, extract this from websocket.scope or headers
            safety_context = {"user_id": session_id, "region": "US", "tier": "free"}
            
            safety_result = await safety_mesh.check_input(raw_data, safety_context, bg_tasks)
            
            # Execute audit logs manually (WS workaround)
            for task in bg_tasks.tasks:
                await task()

            if not safety_result["allowed"]:
                refusal_msg = f"[System]: Request refused. {safety_result['reason']}"
                await websocket.send_text(refusal_msg)
                await websocket.send_text("<<END_OF_TURN>>")
                continue # Skip this turn
            
            # Use the SANITIZED text (PII scrubbed) for all downstream logic
            user_input = safety_result["text"]

            # --- C. Phase 2: Memory & Context (RAG) ---
            # Fetches Redis history and Qdrant lore, and adds User Input to Redis
            context_data = await rag_engine.prepare_context(session_id, char_id, user_input)
            
            # --- D. Phase 1: Prompt Construction ---
            # We pass the RAG data into the Jinja2 template
            full_prompt = await prompt_engine.build_prompt(
                template_name="llama3_base.j2", # Or dynamic based on char_id
                character_name=char_id, # Should fetch real name from DB
                context_data=context_data, # Contains 'history' and 'lore'
                user_input=user_input
            )

            # --- E. Phase 1: Inference & Streaming ---
            buffer = TokenBuffer(websocket)
            
            # Variables for streaming metrics & safety
            first_token_received = False
            token_count = 0
            full_response_text = ""
            output_safety_buffer = ""
            output_violation = False
            
            # Start Streaming from vLLM
            async for token in inference_client.stream_chat(full_prompt, request_id):
                
                # 1. Metric: TTFT
                if not first_token_received:
                    ttft = (time.perf_counter() - turn_start) * 1000
                    logger.info(f"📊 [Metrics] ReqID={request_id} TTFT={ttft:.2f}ms")
                    first_token_received = True

                # 2. Phase 3: Output Safety (Streaming Scan)
                # Accumulate a small window to check for generated toxicity
                output_safety_buffer += token
                if len(output_safety_buffer) > 100: # Check every ~25 tokens
                    # Fast check (fire and forget await)
                    scores = await output_scanner.scan(output_safety_buffer)
                    if scores.get("toxicity", 0) > 0.95:
                        logger.warning(f"🛡️ [Safety] Output Redacted | ReqID={request_id}")
                        await websocket.send_text(" ... [Content Filtered by Safety Policy]")
                        output_violation = True
                        break # Stop generation loop
                    
                    # Keep a rolling window to catch toxicity spanning chunks
                    output_safety_buffer = output_safety_buffer[-20:]

                # 3. Buffer & Send
                await buffer.push(token)
                full_response_text += token
                token_count += 1
            
            # Flush remaining tokens
            if not output_violation:
                await buffer.flush()

            # --- F. Phase 2: Update Memory (Assistant) ---
            # Save the AI's response to Redis history so it remembers next turn
            if full_response_text and not output_violation:
                await cache_manager.add_message(session_id, "assistant", full_response_text)

            # --- G. Metrics & Finalize ---
            total_time = time.perf_counter() - turn_start
            tps = token_count / total_time if total_time > 0 else 0
            logger.info(f"📊 [Metrics] ReqID={request_id} TPS={tps:.2f} Len={token_count}")
            
            await websocket.send_text("<<END_OF_TURN>>")

    except WebSocketDisconnect:
        duration = time.time() - session_start
        logger.info(f"🔌 WS Disconnected | Session: {session_id} | Duration: {duration:.2f}s | Turns: {turns_count}")
        
    except Exception as e:
        logger.error(f"❌ WS Error: {str(e)}", exc_info=True)
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.close(code=1011)
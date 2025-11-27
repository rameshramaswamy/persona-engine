import asyncio
import websockets
import sys

async def chat_session():
    uri = "ws://localhost:8080/ws/chat"
    print(f"🔌 Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected! Type a message (or 'exit' to quit).")
            
            while True:
                user_input = input("\nYou: ")
                if user_input.lower() == "exit":
                    break
                
                await websocket.send(user_input)
                print("Bot: ", end="", flush=True)
                
                while True:
                    response = await websocket.recv()
                    if response == "<<END_OF_TURN>>":
                        break
                    print(response, end="", flush=True)
                print() # Newline after response

    except Exception as e:
        print(f"\n❌ Connection failed. Ensure server is running. Error: {e}")

if __name__ == "__main__":
    # Check Python version for Windows asyncio compatibility
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(chat_session())
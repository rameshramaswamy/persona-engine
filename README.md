

# Persona Engine


**Persona Engine** is a high-performance orchestration framework designed to create, manage, and deploy consistent digital personalities. It goes beyond simple system prompts by providing a stateful memory, emotional context, and multi-channel interaction capabilities for Large Language Models (LLMs).

##  Features

- **Stateful Personality Management:** Define personas using structured YAML/JSON profiles including background, traits, and speech patterns.
- **Contextual Memory:** Integrated vector database support (ChromaDB/Pinecone) for long-term character consistency and "lore" retention.
- **Dynamic Prompt Injection:** Automatically adjusts the LLM context based on user relationship history and emotional state.
- **Multi-Model Support:** Native integration with OpenAI, Anthropic, and local providers via LiteLLM or Ollama.
- **Voice & Visual Ready:** Hooks for TTS (Text-to-Speech) and Lip-syncing metadata for avatar integration.
- **Extensible Tooling:** Easy-to-implement function calling that allows personas to interact with external APIs while staying in character.

## Architecture

Persona Engine operates on a **modular pipeline**:
1. **Profile Loader**: Parses persona definitions.
2. **Context Manager**: Fetches relevant memories and history.
3. **Inference Engine**: Sends the enriched prompt to the LLM.
4. **Post-Processor**: Filters output for character alignment (e.g., ensuring a "pirate" doesn't use modern tech jargon).

##  Prerequisites

- Python 3.9+
- API Key for your preferred provider (OpenAI, Anthropic, etc.)
- (Optional) Docker for containerized deployment

##  Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/rameshramaswamy/persona-engine.git
   cd persona-engine
   ```

2. **Set up a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment:**
   Create a `.env` file in the root directory:
   ```env
   OPENAI_API_KEY=your_key_here
   DATABASE_URL=./data/persona_memory.db
   ```

##  Usage Quickstart

### 1. Define a Persona
Create a file `personas/dr_smith.yaml`:
```yaml
name: "Dr. Smith"
traits: ["Analytical", "Slightly Grumpy", "Highly Ethical"]
background: "A retired space biologist with 40 years of experience on Mars."
speech_pattern: "Uses scientific terminology, often sighs before answering."
```

### 2. Run the Engine
```python
from persona_engine import Engine

# Initialize the engine
engine = Engine(persona_path="personas/dr_smith.yaml")

# Generate a response
response = engine.chat("What do you think of the new soil samples?")
print(f"Dr. Smith: {response}")
```

##  Running Tests
```bash
pytest tests/
```

##  Contributing
Contributions are welcome! Please follow these steps:
1. Fork the Project.
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`).
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the Branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

##  License
Distributed under the MIT License. See `LICENSE` for more information.

---
*Maintained by [Ramesh Ramaswamy](https://github.com/rameshramaswamy)*

# AI Co-Worker Engine

AI-powered NPC engine that enables learners to collaborate with virtual co-workers inside job simulations.

## 📋 Overview

This system is a **minimal yet production-structured prototype** of an AI Co-Worker Engine that simulates an NPC (Non-Player Character) with the role of "Gucci Group CEO". The system is designed to be easily extensible for multiple NPCs with different personas.

## 🏗️ System Architecture

The system is built with a modular architecture consisting of independent components that are easy to maintain and extend:

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Server                       │
│                      (main.py)                          │
│                  POST /chat endpoint                    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                    NPCAgent                             │
│                  (npc_agent.py)                         │
│  Orchestrator: Manages entire processing flow           │
└─────┬──────────┬──────────┬──────────┬──────────────────┘
      │          │          │          │
      ▼          ▼          ▼          ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐
│ Persona │ │ State   │ │ Memory  │ │Supervisor│
│Registry │ │Manager  │ │Manager  │ │          │
└─────────┘ └─────────┘ └─────────┘ └──────────┘
      │          │          │          │
      └──────────┴──────────┴──────────┘
                     │
                     ▼
            ┌─────────────────┐
            │  Gemini API     │
            │  (LLM Call)     │
            └─────────────────┘
```

## 🔄 Processing Flow

When a user sends a message via the `/chat` API, the system performs the following steps:

### 1. **Pre-check**
- `Supervisor.pre_check()` analyzes the user's message
- Checks if the message is **off-topic** (unrelated to the domain)
- Uses keyword matching to determine if the message relates to luxury/brand/strategy

### 2. **State Update**
- `StateManager.update()` analyzes the message and updates internal metrics:
  - **trust_score**: Trust level (0.0 - 1.0)
  - **frustration_score**: Frustration level (0.0 - 1.0)
  - **alignment_score**: Alignment with objectives (0.0 - 1.0)
  - **objective_progress**: Progress toward objectives (0.0 - 1.0)
- Uses simple keyword-based heuristics:
  - Hostile language → increases frustration, decreases trust
  - Brand/strategy keywords → increases alignment, trust, progress
  - Confidential requests → decreases trust, alignment
  - Polite language → decreases frustration

### 3. **Memory Management**
- `MemoryManager.add()` saves the user's message to the conversation buffer
- Keeps the **last 10 messages** (configurable)
- Formats conversation history for the prompt

### 4. **System Prompt Construction**
- `_build_system_prompt()` creates a system prompt including:
  - **Persona definition**: Role, objectives, constraints, communication style
  - **Current state**: Current metrics (to adjust tone)
  - **Conversation history**: Chat history
  - **Tool context**: Information from tools (e.g., Group DNA)
  - **Tone modulation**: Adjusts tone based on frustration_score

### 5. **LLM Call**
- Sends prompt to **Gemini API** (model: gemini-2.0-flash or configured alternative)
- Receives response from LLM
- Handles errors (quota exceeded, network errors, etc.)

### 6. **Post-check**
- `Supervisor.post_check()` analyzes response and state
- If `frustration_score` is high or `alignment_score` is low:
  - Sets flag `inject_alignment_hint = True`
  - Adds hint to response to adjust conversation direction

### 7. **Response Assembly**
- Saves assistant message to memory
- Assembles response including:
  - `assistant_message`: Response from NPC
  - `state`: Current state (for UI display)
  - `flags`: Flags (off_topic, inject_alignment_hint, ok)

## 📦 Component Details

### 1. **persona_registry.py**
- **Purpose**: Defines personas (characters) in a data-driven way
- **Structure**: Each persona has:
  - `persona_id`: Unique identifier
  - `role`: NPC's role
  - `objectives`: List of objectives
  - `constraints`: Constraints (what not to do)
  - `communication_style`: Communication style
- **Extensibility**: Easy to add new personas by adding to `PERSONA_REGISTRY`

### 2. **state_manager.py**
- **Purpose**: Manages the NPC's internal state
- **Metrics**:
  - `trust_score`: Trust level (0.0 = no trust, 1.0 = complete trust)
  - `frustration_score`: Frustration level (0.0 = calm, 1.0 = very frustrated)
  - `alignment_score`: Alignment with objectives (0.0 = misaligned, 1.0 = fully aligned)
  - `objective_progress`: Progress toward objectives (0.0 = none, 1.0 = complete)
- **Heuristic**: Uses keyword matching to update state
- **Clamping**: All values are constrained to [0, 1]

### 3. **memory_manager.py**
- **Purpose**: Stores conversation history in memory
- **Mechanism**: 
  - Stores maximum N messages (default: 10)
  - Automatically removes old messages when limit exceeded
  - Formats history for prompt inclusion
- **No database**: Only stores in memory (suitable for prototype)

### 4. **supervisor.py**
- **Purpose**: Lightweight supervision layer to adjust behavior
- **Pre-check**:
  - Detects off-topic messages
  - Uses keyword matching with domain-specific terms
  - Avoids false positives with short messages
- **Post-check**:
  - Checks frustration threshold
  - Checks alignment threshold
  - Decides whether to inject hint
- **Non-intrusive**: Only emits flags/hints, doesn't modify response directly

### 5. **npc_agent.py**
- **Purpose**: Main orchestrator, coordinates all components
- **Functions**:
  - Initializes persona, state, memory, supervisor
  - Configures Gemini client
  - Executes end-to-end processing flow
  - Handles API errors
- **Main method**: `respond(user_message)` - processes a message and returns response

### 6. **tools.py**
- **Purpose**: Mock tools to provide context for NPC
- **Current**: `get_group_dna()` returns static string
- **Extensibility**: Can add real tools (API calls, database queries, etc.)

### 7. **main.py**
- **Purpose**: FastAPI application entry point
- **Endpoints**:
  - `GET /`: Chat UI (HTML interface)
  - `POST /chat`: API endpoint to chat with NPC
- **Error handling**: Handles errors and returns appropriate HTTP status codes

### 8. **config.py**
- **Purpose**: Manages configuration from environment variables
- **Settings**:
  - `GEMINI_API_KEY`: API key for Gemini
  - `GEMINI_MODEL`: Model name (default: gemini-2.0-flash)
- **Load from `.env`**: Uses python-dotenv to load from `.env` file

## 🎯 Design Features

### 1. **Modular Architecture**
- Each module has clear responsibilities
- Easy to test and maintain individual parts
- Can replace components without affecting others

### 2. **Scalable Design**
- Easy to add new personas (just add to registry)
- Can extend tools, state logic, supervisor rules
- Ready to integrate database, vector store, etc.

### 3. **Production-Ready Structure**
- Full type hints
- Clear error handling
- Clean code with comments
- No over-engineering

### 4. **Minimal Dependencies**
- Only uses necessary libraries
- No database, Redis, vector DB (as required)
- Easy to deploy and maintain

## 🚀 Usage

### Setup

1. **Create virtual environment**:
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows PowerShell
```

2. **Install dependencies**:
```bash
pip install -r ai_coworker_engine/requirements.txt
```

3. **Create `.env` file** in `ai_coworker_engine/` directory:
```env
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-1.5-flash
```

4. **Run server**:
```bash
cd ai_coworker_engine
uvicorn main:app --reload
```

5. **Access UI**:
- Open browser: `http://127.0.0.1:8000`
- Or call API: `POST http://127.0.0.1:8000/chat`

### API Usage

**Request**:
```json
POST /chat
{
  "persona_id": "gucci_ceo",
  "message": "How do we protect brand desirability while growing revenue?"
}
```

**Response**:
```json
{
  "assistant_message": "As CEO, I focus on...",
  "state": {
    "trust_score": 0.65,
    "frustration_score": 0.20,
    "alignment_score": 0.75,
    "objective_progress": 0.15
  },
  "flags": {
    "off_topic": false,
    "inject_alignment_hint": false,
    "ok": true
  }
}
```

## 🔍 Detailed State Logic

### Heuristic Rules

1. **Hostile Language Detection**:
   - Keywords: "stupid", "idiot", "useless", "shut up", "hate", "liar"
   - Effect: `frustration_score += 0.18`, `trust_score -= 0.10`

2. **Alignment Markers**:
   - Keywords: "brand", "positioning", "heritage", "craft", "desirability", "creative", "strategy", "luxury"
   - Effect: `alignment_score += 0.06`, `trust_score += 0.03`, `objective_progress += 0.04`

3. **Confidential Requests**:
   - Keywords: "confidential", "leak", "insider", "non-public", "nda"
   - Effect: `trust_score -= 0.12`, `frustration_score += 0.08`, `alignment_score -= 0.08`

4. **Polite Language**:
   - Keywords: "please", "thank you", "thanks", "appreciate"
   - Effect: `frustration_score -= 0.05`, `trust_score += 0.04`

5. **Off-topic Detection**:
   - If message doesn't contain domain keywords and is longer than 18 characters
   - Effect: `frustration_score += 0.06`, `alignment_score -= 0.06`

## 🎨 UI Features

- **Modern Chat Interface**: Modern, responsive chat interface
- **Real-time State Display**: Displays state metrics (trust, frustration, alignment)
- **Error Handling**: User-friendly error handling and display
- **Loading States**: Shows processing state
- **Auto-scroll**: Automatically scrolls to new messages

## 📝 Notes for Assignment

### Design Strengths:

1. **Separation of Concerns**: Each module has distinct responsibilities
2. **Extensibility**: Easy to add new personas, tools, state logic
3. **Maintainability**: Clean code with type hints and clear comments
4. **Scalability**: Can extend to database, caching, etc.
5. **Production-Ready**: Error handling, validation, proper HTTP status codes

### Future Improvements:

1. **Database Integration**: Store conversation history in database
2. **Vector Store**: Use embeddings for semantic search
3. **Advanced State Logic**: Replace heuristics with ML models
4. **Multi-turn Context**: Improve context management
5. **Authentication**: Add user authentication and session management

## 🛠️ Tech Stack

- **Python 3.10+**: Core language
- **FastAPI**: Web framework
- **Google Gemini API**: LLM provider
- **Uvicorn**: ASGI server
- **python-dotenv**: Environment variable management

## 📄 License

MIT License

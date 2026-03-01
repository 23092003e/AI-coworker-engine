## AI Co-Worker Engine (Minimal Prototype)

Minimal, production-structured prototype of an **AI Co-Worker Engine** that simulates an executive NPC (“Gucci Group CEO”).

### Architecture

- **`persona_registry.py`**: Data-driven persona definitions (role, objectives, constraints, comms style). Add more personas by extending `PERSONA_REGISTRY`.
- **`state_manager.py`**: Internal signals (all clamped to **0..1**) that modulate behavior:
  - `trust_score`
  - `frustration_score`
  - `alignment_score`
  - `objective_progress`
- **`memory_manager.py`**: In-memory conversation buffer (stores **last 10 messages**).
- **`supervisor.py`**: Lightweight governance layer:
  - **Pre-check**: `off_topic` detection
  - **Post-check**: `frustration_threshold` + low alignment triggers `inject_alignment_hint`
- **`npc_agent.py`**: Orchestrator (persona + state + memory + supervisor + Gemini model call).
- **`tools.py`**: Mock tool(s), currently `get_group_dna()` returning a static string for prompt context.
- **`main.py`**: FastAPI app exposing `POST /chat`.

### State Logic (Minimal Heuristics)

`StateManager.update()` adjusts state based on simple keyword heuristics:
- Hostile language increases `frustration_score`, reduces `trust_score`
- Brand/strategy keywords increase `alignment_score`, `trust_score`, `objective_progress`
- “Confidential/leak/insider” style requests reduce trust + alignment
- Polite language slightly reduces frustration

All values are clamped to **[0, 1]**.

### Supervisor Logic

- **Pre-check** (`Supervisor.pre_check`):
  - If message appears unrelated to luxury/brand/strategy and is not trivially short, flag `off_topic=True`
- **Post-check** (`Supervisor.post_check`):
  - If `frustration_score` is high or `alignment_score` is low, set `inject_alignment_hint=True`

The supervisor does not “take over” responses—only emits flags/hints.

### API

#### `POST /chat`

Input:

```json
{
  "persona_id": "gucci_ceo",
  "message": "..."
}
```

Output:
- `assistant_message`: NPC response
- `state`: current internal state dict
- `flags`: `{ off_topic, inject_alignment_hint, ok }`

### Setup

Create a `.env` file (optional) or export env vars:

- `GEMINI_API_KEY` (required)
- `GEMINI_MODEL` (optional, default: `gemini-2.0-flash`)

Install deps:

```bash
pip install -r requirements.txt
```

Run:

```bash
uvicorn main:app --reload
```

Then call:

```bash
curl -X POST http://127.0.0.1:8000/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"persona_id\":\"gucci_ceo\",\"message\":\"How do we protect brand desirability while growing revenue?\"}"
```


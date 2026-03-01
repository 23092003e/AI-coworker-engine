"""
NPC Agent.

Single-responsibility: orchestrate persona + state + memory + supervisor + LLM call.

This is intentionally synchronous and minimal (no async complexity).
"""

from __future__ import annotations

from dataclasses import asdict

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from config import Settings
from memory_manager import MemoryManager
from persona_registry import Persona, get_persona
from state_manager import StateManager
from supervisor import Supervisor
from tools import get_group_dna


def _tone_note(frustration_score: float) -> str:
    """
    Slightly modulate tone as frustration changes.
    Keep it executive, never petty.
    """

    if frustration_score >= 0.8:
        return "Tone: cool, firm, boundary-setting, de-escalating."
    if frustration_score >= 0.55:
        return "Tone: more direct and corrective, still composed."
    return "Tone: calm, strategic, confident."


def _build_system_prompt(persona: Persona, state: dict[str, float]) -> str:
    """
    Build a single system prompt that encodes persona + constraints + current state.
    """

    # Keep the prompt concise but explicit; models behave better with crisp rules.
    return "\n".join(
        [
            "You are an NPC in an AI Co-Worker Engine.",
            f"ROLE: {persona.role}",
            "",
            "OBJECTIVES:",
            *[f"- {o}" for o in persona.objectives],
            "",
            "CONSTRAINTS (must follow):",
            *[f"- {c}" for c in persona.constraints],
            "",
            "COMMUNICATION STYLE:",
            *[f"- {s}" for s in persona.communication_style],
            "",
            "STATE (0..1) — use to modulate tone and strategic posture:",
            f"- trust_score: {state['trust_score']:.2f}",
            f"- frustration_score: {state['frustration_score']:.2f}",
            f"- alignment_score: {state['alignment_score']:.2f}",
            f"- objective_progress: {state['objective_progress']:.2f}",
            _tone_note(state["frustration_score"]),
            "",
            "EXECUTIVE POLICY:",
            "- Speak strategically; avoid operational micromanagement.",
            "- Defend brand autonomy and creative integrity.",
            "- If asked for confidential/non-public info: refuse and offer a safe alternative.",
            "- If user is off-topic: gracefully re-anchor to brand/strategy.",
            "",
            f"OPTIONAL CONTEXT (tool): {get_group_dna()}",
        ]
    ).strip()


class NPCAgent:
    """
    Minimal NPC agent.

    Designed to be instantiated per persona (or later per session).
    """

    def __init__(
        self,
        *,
        persona_id: str,
        settings: Settings,
        state_manager: StateManager | None = None,
        memory_manager: MemoryManager | None = None,
        supervisor: Supervisor | None = None,
    ) -> None:
        self.persona_id = persona_id
        self.persona = get_persona(persona_id)
        self.state_manager = state_manager or StateManager()
        self.memory = memory_manager or MemoryManager(max_messages=10)
        self.supervisor = supervisor or Supervisor()

        # Configure Gemini client
        genai.configure(api_key=settings.gemini_api_key)
        self._model = genai.GenerativeModel(settings.gemini_model)

    def respond(self, user_message: str) -> dict:
        """
        Respond to a user message.

        Steps:
        1) Supervisor pre-check
        2) Update state
        3) Add to memory
        4) Build system prompt using persona + state
        5) Call OpenAI API
        6) Supervisor post-check
        7) Inject hint if needed
        8) Return { assistant_message, state, flags }
        """

        pre = self.supervisor.pre_check(user_message)

        state = self.state_manager.update(user_message, off_topic=pre.off_topic)
        state_dict = state.to_dict()

        self.memory.add("user", user_message)

        system_prompt = _build_system_prompt(self.persona, state_dict)
        history = self.memory.get_messages()

        # For Gemini, we keep it simple: turn history into a plain-text transcript.
        convo_lines: list[str] = []
        for m in history:
            if m.role == "user":
                convo_lines.append(f"User: {m.content}")
            elif m.role == "assistant":
                convo_lines.append(f"Assistant: {m.content}")

        conversation_block = "\n".join(convo_lines).strip()
        if conversation_block:
            full_prompt = f"{system_prompt}\n\nConversation so far:\n{conversation_block}\n\nRespond as the Gucci Group CEO to the latest user message."
        else:
            full_prompt = f"{system_prompt}\n\nRespond as the Gucci Group CEO to the user."

        try:
            response = self._model.generate_content(full_prompt)
            assistant_message = (getattr(response, "text", "") or "").strip()
        except google_exceptions.ResourceExhausted as e:
            error_msg = str(e)
            if "quota" in error_msg.lower() or "limit" in error_msg.lower():
                raise RuntimeError(
                    f"Gemini API quota exceeded. "
                    f"Please check your API quota at https://ai.dev/rate-limit or try again later. "
                    f"Error details: {error_msg[:200]}"
                ) from e
            raise RuntimeError(f"Gemini API error: {error_msg}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to generate response: {str(e)}") from e

        self.memory.add("assistant", assistant_message)

        post = self.supervisor.post_check(
            frustration_score=state_dict["frustration_score"],
            alignment_score=state_dict["alignment_score"],
        )

        injected = assistant_message
        if post.inject_alignment_hint:
            hint = (
                "\n\n(Executive note: Let’s stay anchored on brand equity, creative integrity, "
                "and long-term desirability—tell me the decision you’re trying to make.)"
            )
            injected = f"{assistant_message}{hint}"

        flags = {
            "off_topic": pre.off_topic,
            "inject_alignment_hint": post.inject_alignment_hint,
            "ok": pre.ok and post.ok,
        }

        return {
            "assistant_message": injected,
            "state": asdict(state),
            "flags": flags,
        }


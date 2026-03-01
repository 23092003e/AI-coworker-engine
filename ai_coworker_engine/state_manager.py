"""
State manager.

Tracks lightweight internal signals (0..1) that modulate the NPC's behavior.
This is intentionally heuristic and minimal; you can later replace it with
classifier models or policy rules without changing the agent interface.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


@dataclass
class NPCState:
    """
    Internal state for an NPC.

    - trust_score: How much the NPC trusts the user/request.
    - frustration_score: How annoyed/strained the NPC feels.
    - alignment_score: How aligned the user seems with the NPC's objectives/constraints.
    - objective_progress: Subjective progress toward the current objective (not "tasks").
    """

    trust_score: float = 0.6
    frustration_score: float = 0.2
    alignment_score: float = 0.6
    objective_progress: float = 0.1

    def to_dict(self) -> dict[str, float]:
        return asdict(self)

    def clamp(self) -> None:
        self.trust_score = _clamp01(self.trust_score)
        self.frustration_score = _clamp01(self.frustration_score)
        self.alignment_score = _clamp01(self.alignment_score)
        self.objective_progress = _clamp01(self.objective_progress)


class StateManager:
    """
    Minimal heuristic updater based on user input.

    This is not an "emotion model"—it's a pragmatic signal system to modulate tone.
    """

    def __init__(self, state: NPCState | None = None) -> None:
        self.state = state or NPCState()

    def update(self, user_message: str, *, off_topic: bool) -> NPCState:
        msg = (user_message or "").lower().strip()

        # --- Frustration heuristic ---
        hostile_markers = ["stupid", "idiot", "useless", "shut up", "hate", "liar"]
        if any(m in msg for m in hostile_markers):
            self.state.frustration_score += 0.18
            self.state.trust_score -= 0.10

        if off_topic:
            self.state.frustration_score += 0.06
            self.state.alignment_score -= 0.06

        # --- Alignment heuristic ---
        alignment_markers = [
            "brand",
            "positioning",
            "heritage",
            "craft",
            "desirability",
            "creative",
            "strategy",
            "luxury",
        ]
        if any(m in msg for m in alignment_markers):
            self.state.alignment_score += 0.06
            self.state.trust_score += 0.03
            self.state.objective_progress += 0.04

        # --- Confidential / risky requests reduce trust ---
        confidential_markers = ["confidential", "leak", "insider", "non-public", "nda"]
        if any(m in msg for m in confidential_markers):
            self.state.trust_score -= 0.12
            self.state.frustration_score += 0.08
            self.state.alignment_score -= 0.08

        # --- Soften if the user is polite ---
        polite_markers = ["please", "thank you", "thanks", "appreciate"]
        if any(m in msg for m in polite_markers):
            self.state.frustration_score -= 0.05
            self.state.trust_score += 0.04

        self.state.clamp()
        return self.state


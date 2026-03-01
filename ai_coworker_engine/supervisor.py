"""
Supervisor layer.

Two-phase checks:
- Pre-check: detect off-topic inputs (lightweight heuristic)
- Post-check: watch frustration threshold and decide whether to inject alignment hints

The supervisor does not generate the final content; it emits signals/flags.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SupervisorFlags:
    off_topic: bool
    inject_alignment_hint: bool
    ok: bool

    def to_dict(self) -> dict[str, bool]:
        return {
            "off_topic": self.off_topic,
            "inject_alignment_hint": self.inject_alignment_hint,
            "ok": self.ok,
        }


class Supervisor:
    """
    Minimal supervisor.

    Off-topic detection is deliberately conservative to avoid false positives.
    """

    def __init__(
        self,
        *,
        frustration_threshold: float = 0.78,
        alignment_hint_threshold: float = 0.45,
    ) -> None:
        self.frustration_threshold = frustration_threshold
        self.alignment_hint_threshold = alignment_hint_threshold

    def pre_check(self, user_message: str) -> SupervisorFlags:
        msg = (user_message or "").lower().strip()

        # Domain keywords for a Gucci Group CEO persona (strategy + luxury + brand).
        on_topic_markers = [
            "gucci",
            "luxury",
            "brand",
            "fashion",
            "creative",
            "heritage",
            "positioning",
            "craft",
            "runway",
            "collection",
            "leather",
            "retail",
            "pricing",
            "exclusivity",
            "desirability",
            "marketing",
            "culture",
            "ceo",
        ]

        # A short message can be ambiguous; avoid calling it off-topic too quickly.
        is_short = len(msg) < 18
        looks_on_topic = any(k in msg for k in on_topic_markers)
        off_topic = (not looks_on_topic) and (not is_short)

        return SupervisorFlags(off_topic=off_topic, inject_alignment_hint=False, ok=not off_topic)

    def post_check(self, *, frustration_score: float, alignment_score: float) -> SupervisorFlags:
        inject_alignment_hint = (
            frustration_score >= self.frustration_threshold
            or alignment_score <= self.alignment_hint_threshold
        )

        ok = frustration_score < 0.95  # beyond this, we still respond but we want de-escalation tone
        return SupervisorFlags(off_topic=False, inject_alignment_hint=inject_alignment_hint, ok=ok)


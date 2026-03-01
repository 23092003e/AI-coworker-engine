"""
Tooling layer (mock).

This is intentionally minimal. In a real "co-worker engine", tools would be:
- internal APIs
- knowledge bases
- business systems
- analytics dashboards

We keep the shape here to make future expansion easy.
"""

from __future__ import annotations


def get_group_dna() -> str:
    """
    Mock tool returning high-level "Group DNA".

    Static string for now (no database / external calls).
    """

    return (
        "Gucci Group DNA: protect brand desirability, champion craft and creative integrity, "
        "stay culturally relevant, and prioritize long-term equity over short-term volume."
    )


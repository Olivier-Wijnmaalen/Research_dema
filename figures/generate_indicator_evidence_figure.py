"""Generate a Word-ready figure of evidence records cited per DEMA indicator."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
SCORE_PATH = ROOT / "outputs" / "canonical_final" / "final_score.validated.json"
OUTPUT_PATH = ROOT / "figures" / "final_pipeline_evidence_per_indicator_with_dimensions.png"

NAVY = "#102A63"
GREY = "#667085"
GRID = "#D9DEE8"
DIMENSIONS = {
    "A": {"name": "Actors & Roles", "color": "#E89A2E", "background": "#FFF7E8"},
    "B": {"name": "Data Value Chain", "color": "#3478C9", "background": "#EEF5FD"},
    "C": {"name": "Data Ecosystem Governance", "color": "#16834A", "background": "#ECF7F0"},
}


def load_counts() -> tuple[list[str], list[int]]:
    wrapper = json.loads(SCORE_PATH.read_text(encoding="utf-8"))
    score = wrapper.get("result", wrapper)
    codes: list[str] = []
    counts: list[int] = []
    for assessment in score["indicator_assessments"]:
        references = {
            str(evidence_id)
            for field in ("evidence_supporting_score", "contrary_or_limiting_evidence")
            for evidence_id in assessment.get(field, [])
            if str(evidence_id).strip()
        }
        codes.append(str(assessment["indicator_code"]))
        counts.append(len(references))
    if len(codes) != 31 or len(set(codes)) != 31:
        raise ValueError("Expected 31 unique final DEMA indicators")
    return codes, counts


def add_dimension_card(fig: plt.Figure, x: float, width: float, letter: str) -> None:
    spec = DIMENSIONS[letter]
    card = FancyBboxPatch(
        (x, 0.875), width, 0.052,
        boxstyle="round,pad=0.006,rounding_size=0.009",
        transform=fig.transFigure,
        facecolor=spec["background"],
        edgecolor=spec["color"],
        linewidth=1.25,
    )
    fig.add_artist(card)
    fig.text(x + 0.012, 0.904, f"DIMENSION {letter}", color=spec["color"],
             fontsize=8.2, fontweight="bold")
    fig.text(x + 0.012, 0.884, spec["name"], color=NAVY, fontsize=8.8, fontweight="bold")


def main() -> None:
    codes, counts = load_counts()
    dimensions = [code[0] for code in codes]
    y = np.arange(len(codes))
    colors = [DIMENSIONS[dimension]["color"] for dimension in dimensions]

    plt.rcParams.update({"font.family": "DejaVu Sans"})
    fig, ax = plt.subplots(figsize=(8.15, 10.45), dpi=240)
    fig.patch.set_facecolor("white")

    fig.text(0.085, 0.975, "Evidence records referenced per DEMA indicator",
             fontsize=17, fontweight="bold", color=NAVY, va="top")
    fig.text(0.085, 0.947,
             "Unique evidence IDs cited in the final Stage 2 maturity assessment",
             fontsize=9.8, color=GREY, va="top")

    add_dimension_card(fig, 0.085, 0.25, "A")
    add_dimension_card(fig, 0.375, 0.25, "B")
    add_dimension_card(fig, 0.665, 0.25, "C")

    # Soft group bands make the dimension boundaries readable without adding clutter.
    group_ranges = {}
    for letter in ("A", "B", "C"):
        indices = [index for index, dimension in enumerate(dimensions) if dimension == letter]
        group_ranges[letter] = (min(indices), max(indices))
        start, end = group_ranges[letter]
        ax.axhspan(start - 0.48, end + 0.48, color=DIMENSIONS[letter]["background"], zorder=0)

    ax.barh(y, counts, color=colors, height=0.68, zorder=2)
    ax.set_yticks(y, labels=codes, fontsize=9.2, color=NAVY)
    ax.invert_yaxis()
    ax.set_xlim(0, max(counts) + 3.1)
    ax.set_xlabel("Unique evidence records referenced in each indicator assessment",
                  fontsize=10.2, color=NAVY, labelpad=8)
    ax.set_ylabel("DEMA indicator", fontsize=10.2, color=NAVY, labelpad=9)
    ax.grid(axis="x", color=GRID, linewidth=0.8, zorder=1)
    ax.set_axisbelow(True)
    ax.tick_params(axis="x", labelsize=8.8, colors=GREY)
    ax.tick_params(axis="y", length=0, pad=6)
    for spine in ax.spines.values():
        spine.set_visible(False)

    for index, count in enumerate(counts):
        ax.text(count + 0.25, index, str(count), va="center", ha="left",
                fontsize=8.8, fontweight="bold", color=NAVY)

    fig.text(
        0.085, 0.018,
        "Note. Counts combine supporting and contrary/limiting evidence IDs. The same record may be cited for multiple indicators; "
        "therefore, indicator counts are not additive. The final assessment contains 337 citation occurrences covering 238 distinct records.",
        fontsize=7.4, color=GREY, wrap=True,
    )

    plt.subplots_adjust(left=0.20, right=0.94, top=0.835, bottom=0.115)
    fig.savefig(OUTPUT_PATH, facecolor="white", bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()

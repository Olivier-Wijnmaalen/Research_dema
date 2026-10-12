"""Create a simple expert-workshop versus canonical LLM phase comparison."""

from __future__ import annotations

import json
from collections import OrderedDict
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch


ROOT = Path(__file__).resolve().parents[1]
SCORE_PATH = ROOT / "outputs" / "canonical_final" / "final_score.validated.json"
OUTPUT_PATH = ROOT / "figures" / "workshop_vs_canonical_llm_phase_comparison_simple.png"

NAVY = "#123B52"
EXPERT = "#E69A24"
LLM = "#176B87"
ARROW = "#70838C"
GRID = "#D5E0E5"

# Frozen expert-workshop values from original_in_country_workshop_assessment.json.
ROWS = OrderedDict(
    [
        ("WORKSHOP-001", ("Roles — all actors", 3, ["A.1.1"])),
        ("WORKSHOP-002", ("Roles — coordinator", 4, ["A.1.2"])),
        ("WORKSHOP-003", ("Diversity — users", 3, ["A.1.3"])),
        ("WORKSHOP-004", ("Diversity — producers", 3, ["A.1.4"])),
        ("WORKSHOP-005", ("Accessibility", 2, ["B.1.1"])),
        ("WORKSHOP-006", ("Quality results (aggregate)", 2, ["B.1.3a", "B.1.3c", "B.1.3d", "B.1.3e"])),
        ("WORKSHOP-007", ("Process quality", 3, ["A.2.4"])),
        ("WORKSHOP-008", ("Institutional quality", 3, ["A.2.2"])),
        ("WORKSHOP-009", ("Applications / use cases", 3, ["B.3.1"])),
        ("WORKSHOP-010", ("Supply meets demand", 3, ["B.3.2"])),
        ("WORKSHOP-011", ("Technical interoperability", 3, ["B.2.1"])),
        ("WORKSHOP-012", ("Common standards", 2, ["B.2.2"])),
        ("WORKSHOP-013", ("Trust", 4, ["C.1.1"])),
        ("WORKSHOP-014", ("Responsible data use", 4, ["C.1.2"])),
        ("WORKSHOP-015", ("Security", 2, ["C.1.4"])),
        ("WORKSHOP-016", ("Privacy / confidentiality", 3, ["C.1.5"])),
        ("WORKSHOP-017", ("Human capacity", 2, ["A.2.1"])),
        ("WORKSHOP-018", ("Institutional data capacity", 2, ["A.2.2"])),
        ("WORKSHOP-019", ("Institutional AI capacity", 1, ["A.2.3", "C.1.3"])),
        ("WORKSHOP-020", ("Data strategy / standards", 4, ["C.2.1"])),
        ("WORKSHOP-021", ("Dedicated budget", 3, ["C.2.2"])),
        ("WORKSHOP-022", ("Incentive policies", 4, ["C.2.3"])),
        ("WORKSHOP-023", ("Community engagement", 3, ["C.3.1"])),
        ("WORKSHOP-024", ("Inter-agency collaboration", 4, ["C.3.2"])),
    ]
)

GROUPS = [
    (0, 3, "ACTORS & ROLES"),
    (4, 7, "DATA SUPPLY"),
    (8, 9, "DATA DEMAND"),
    (10, 11, "INFRASTRUCTURE"),
    (12, 23, "DATA-ECOSYSTEM GOVERNANCE"),
]


def canonical_scores() -> dict[str, int]:
    wrapper = json.loads(SCORE_PATH.read_text(encoding="utf-8"))
    score = wrapper.get("result", wrapper)
    values = {
        str(item["indicator_code"]): int(item["phase_score"])
        for item in score["indicator_assessments"]
    }
    required = {code for _, _, codes in ROWS.values() for code in codes}
    missing = required - values.keys()
    if missing:
        raise ValueError(f"Canonical score is missing indicators: {sorted(missing)}")
    if values["B.1.3d"] != 3:
        raise ValueError("B.1.3d must be Phase 3 in the canonical comparison")
    return values


def main() -> None:
    llm_scores = canonical_scores()
    labels = [f"{row_id[-3:]}  {label}" for row_id, (label, _, _) in ROWS.items()]

    # Reserve a separate line for each section heading so headings never sit on
    # top of an indicator row when the figure is reduced to Word-page width.
    y_positions: list[float] = [0.0] * len(labels)
    group_layout: list[tuple[float, float, str]] = []
    cursor = 0.0
    for start, end, title in GROUPS:
        heading_y = cursor
        first_row_y = heading_y + 0.72
        for row_index in range(start, end + 1):
            y_positions[row_index] = first_row_y + (row_index - start)
        last_row_y = y_positions[end]
        group_layout.append((heading_y, last_row_y, title))
        cursor = last_row_y + 1.05

    plt.rcParams.update({"font.family": "DejaVu Sans"})
    fig, ax = plt.subplots(figsize=(8.15, 10.4), dpi=240)
    fig.patch.set_facecolor("white")
    fig.text(0.06, 0.975, "Expert workshop and documentary LLM comparison",
             fontsize=16.5, fontweight="bold", color=NAVY, va="top")
    fig.text(0.06, 0.947,
             "Conceptual crosswalk to the revised DEMA framework · canonical final Stage 2 scores",
             fontsize=9.2, color="#607782", va="top")

    # Alternating section bands and compact section headings.
    band_colours = ["#F7FAFB", "#EEF6F8"]
    for group_index, (heading_y, last_row_y, title) in enumerate(group_layout):
        ax.axhspan(heading_y - 0.25, last_row_y + 0.45,
                   color=band_colours[group_index % 2], zorder=0)
        ax.text(0.005, heading_y, title, transform=ax.get_yaxis_transform(),
                fontsize=7.2, fontweight="bold", color=LLM, va="center")

    for index, (_, (_, expert_phase, codes)) in enumerate(ROWS.items()):
        row_y = y_positions[index]
        phases = sorted({llm_scores[code] for code in codes})
        for offset_index, llm_phase in enumerate(phases):
            offset = 0 if len(phases) == 1 else (offset_index - (len(phases) - 1) / 2) * 0.16
            if expert_phase != llm_phase:
                arrow = FancyArrowPatch(
                    (expert_phase, row_y), (llm_phase, row_y + offset),
                    arrowstyle="-|>", mutation_scale=10, linewidth=1.25,
                    color=ARROW, shrinkA=7, shrinkB=7, zorder=2,
                )
                ax.add_patch(arrow)
                ax.scatter(expert_phase, row_y, marker="s", s=43, color=EXPERT,
                           edgecolor="white", linewidth=0.8, zorder=4)
                ax.scatter(llm_phase, row_y + offset, marker="o", s=44, color=LLM,
                           edgecolor="white", linewidth=0.8, zorder=5)
            else:
                ax.scatter(expert_phase, row_y, marker="o", s=76, facecolor="white",
                           edgecolor=LLM, linewidth=1.6, zorder=3)
                ax.scatter(expert_phase, row_y, marker="s", s=31, color=EXPERT,
                           edgecolor="white", linewidth=0.6, zorder=4)

        if len(codes) > 1:
            phase_label = ", ".join(f"{code}=P{llm_scores[code]}" for code in codes)
            ax.text(max(phases) + 0.10, row_y, phase_label, fontsize=6.7,
                    color=LLM, va="center", ha="left", fontweight="bold")

    ax.set_yticks(y_positions, labels=labels, fontsize=7.7, color="#263B45")
    ax.invert_yaxis()
    ax.set_xlim(0.72, 5.48)
    ax.set_xticks([1, 2, 3, 4, 5])
    ax.set_xticklabels(
        ["P1\nIncomplete", "P2\nRecognized", "P3\nManaged", "P4\nControlled", "P5\nTransformational"],
        fontsize=8.1, color=NAVY,
    )
    ax.xaxis.tick_top()
    ax.tick_params(axis="x", length=0, pad=7)
    ax.tick_params(axis="y", length=0, pad=7)
    ax.grid(axis="x", color=GRID, linewidth=0.9, zorder=1)
    for spine in ax.spines.values():
        spine.set_visible(False)

    legend = [
        Line2D([0], [0], marker="s", color="none", markerfacecolor=EXPERT,
               markeredgecolor="white", markersize=7, label="Expert workshop"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=LLM,
               markeredgecolor="white", markersize=7, label="Documentary LLM"),
        Line2D([0], [0], marker="o", color=LLM, markerfacecolor="white",
               markeredgewidth=1.4, markersize=8, linewidth=0, label="Same phase"),
    ]
    fig.legend(handles=legend, loc="lower center", bbox_to_anchor=(0.5, 0.033),
               ncol=3, frameon=False, fontsize=8.4, columnspacing=2.0)
    fig.text(
        0.06, 0.012,
        "Note. Arrows run from the expert-workshop score to the documentary LLM score. One-to-many crosswalks are labelled. "
        "B.1.3d (timeliness) is Phase 3 in the canonical final assessment.",
        fontsize=7.2, color="#607782",
    )

    plt.subplots_adjust(left=0.29, right=0.95, top=0.875, bottom=0.085)
    fig.savefig(OUTPUT_PATH, facecolor="white", bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()

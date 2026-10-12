"""Generate the one-page Stage 1 evidence / Stage 2 citation figure."""

from __future__ import annotations

import json
from collections import OrderedDict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
BANK_PATH = ROOT / "outputs" / "canonical_final" / "combined_evidence_bank.json"
SCORE_PATH = ROOT / "outputs" / "canonical_final" / "final_score.validated.json"
OUTPUT_PATH = ROOT / "figures" / "evidence_bank_and_stage2_citations.png"

DIMENSIONS = OrderedDict(
    [
        ("A.1  Roles", "A.1"),
        ("A.2  Capacity", "A.2"),
        ("B.1  Data supply", "B.1"),
        ("B.2  Data infrastructure", "B.2"),
        ("B.3  Data demand", "B.3"),
        ("C.1  Governance, ethics & trust", "C.1"),
        ("C.2  Policies, standards & resources", "C.2"),
        ("C.3  Collaboration & inclusion", "C.3"),
    ]
)

NAVY = "#102A63"
DEVELOPMENT = "#E89A2E"
HELD_OUT = "#2F73C9"
GREEN = "#16834A"
LIGHT_GREEN = "#E7F5EC"
LIGHT_GREY = "#F3F5F8"
MID_GREY = "#667085"


def load_data() -> tuple[list[dict], list[str]]:
    bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))
    wrapper = json.loads(SCORE_PATH.read_text(encoding="utf-8"))
    score = wrapper.get("result", wrapper)
    references: list[str] = []
    for assessment in score["indicator_assessments"]:
        references.extend(assessment.get("evidence_supporting_score", []))
        references.extend(assessment.get("contrary_or_limiting_evidence", []))
    return bank["evidence_items"], references


def dimension_code(value: str) -> str:
    for code in DIMENSIONS.values():
        if value.startswith(code):
            return code
    raise ValueError(f"Unmapped DEMA dimension: {value}")


def counts(items: list[dict], cited_ids: set[str] | None = None) -> tuple[np.ndarray, np.ndarray]:
    development = []
    held_out = []
    for code in DIMENSIONS.values():
        selected = [
            item
            for item in items
            if dimension_code(str(item["subdimension"])) == code
            and (cited_ids is None or str(item["evidence_id"]) in cited_ids)
        ]
        development.append(sum(str(item["evidence_id"]).startswith("V4ID-") for item in selected))
        held_out.append(sum(not str(item["evidence_id"]).startswith("V4ID-") for item in selected))
    return np.array(development), np.array(held_out)


def add_panel(
    ax: plt.Axes,
    development: np.ndarray,
    held_out: np.ndarray,
    title: str,
    subtitle: str,
    denominator: int,
) -> None:
    y = np.arange(len(DIMENSIONS))
    totals = development + held_out
    ax.barh(y, development, color=DEVELOPMENT, height=0.62, label="Development")
    ax.barh(y, held_out, left=development, color=HELD_OUT, height=0.62, label="Held-out")
    ax.set_yticks(y, labels=list(DIMENSIONS.keys()), fontsize=10.2, color=NAVY)
    ax.invert_yaxis()
    ax.set_title(title, loc="left", fontsize=14, fontweight="bold", color=NAVY, pad=18)
    ax.text(0, 1.025, subtitle, transform=ax.transAxes, fontsize=9.5, color=MID_GREY)
    ax.grid(axis="x", color="#D9DEE8", linewidth=0.8, alpha=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(axis="x", labelsize=9, colors=MID_GREY)
    ax.tick_params(axis="y", length=0, pad=8)
    for spine in ax.spines.values():
        spine.set_visible(False)

    max_total = int(totals.max())
    ax.set_xlim(0, max_total * 1.27)
    for index, (dev, held, total) in enumerate(zip(development, held_out, totals)):
        if dev >= max_total * 0.075:
            ax.text(dev / 2, index, str(dev), ha="center", va="center", color="white",
                    fontsize=9.3, fontweight="bold")
        else:
            ax.text(dev + 0.8, index - 0.17, str(dev), ha="left", va="center",
                    color=DEVELOPMENT, fontsize=8.7, fontweight="bold")
        if held >= max_total * 0.075:
            ax.text(dev + held / 2, index, str(held), ha="center", va="center", color="white",
                    fontsize=9.3, fontweight="bold")
        else:
            ax.text(dev + held + 0.8, index + 0.17, str(held), ha="left", va="center",
                    color=HELD_OUT, fontsize=8.7, fontweight="bold")
        ax.text(total + max_total * 0.035, index, f"{total}  ({100 * total / denominator:.1f}%)",
                va="center", fontsize=9.2, color=NAVY, fontweight="bold")


def callout(fig: plt.Figure, x: float, width: float, heading: str, value: str, note: str) -> None:
    box = FancyBboxPatch(
        (x, 0.032), width, 0.088,
        boxstyle="round,pad=0.008,rounding_size=0.012",
        transform=fig.transFigure,
        facecolor=LIGHT_GREEN,
        edgecolor=GREEN,
        linewidth=1.2,
    )
    fig.add_artist(box)
    fig.text(x + 0.016, 0.096, heading, fontsize=8.7, color=MID_GREY, fontweight="bold")
    fig.text(x + 0.016, 0.066, value, fontsize=15, color=GREEN, fontweight="bold")
    fig.text(x + 0.016, 0.044, note, fontsize=7.2, color=NAVY)


def main() -> None:
    items, references = load_data()
    cited_ids = set(references)
    bank_ids = {str(item["evidence_id"]) for item in items}
    unknown_ids = cited_ids - bank_ids
    if unknown_ids:
        raise ValueError(f"Unresolved Stage 2 evidence IDs: {sorted(unknown_ids)}")

    bank_dev, bank_held = counts(items)
    cited_dev, cited_held = counts(items, cited_ids)
    assert int(bank_dev.sum()) == 390
    assert int(bank_held.sum()) == 232
    assert int(cited_dev.sum()) == 161
    assert int(cited_held.sum()) == 77

    plt.rcParams.update({"font.family": "DejaVu Sans"})
    fig, axes = plt.subplots(2, 1, figsize=(8.15, 10.35), dpi=240)
    fig.patch.set_facecolor("white")
    fig.suptitle(
        "Evidence use across the DEMA pipeline",
        x=0.075, y=0.976, ha="left", fontsize=18, fontweight="bold", color=NAVY,
    )
    fig.text(
        0.075, 0.947,
        "Stage 1 evidence-bank composition and Stage 2 use in the final maturity justifications",
        fontsize=10.2, color=MID_GREY,
    )

    add_panel(
        axes[0], bank_dev, bank_held,
        "A. Evidence bank available to Stage 2",
        "Counts inside bars; labels at right show combined records and share of the 622-record bank.",
        622,
    )
    add_panel(
        axes[1], cited_dev, cited_held,
        "B. Distinct evidence records cited by Stage 2",
        "Counts inside bars; labels at right show cited records and share of the 238 distinct records cited.",
        238,
    )

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles, labels, loc="upper left", bbox_to_anchor=(0.075, 0.928), ncol=2,
        frameon=False, fontsize=9.5, handlelength=1.5, columnspacing=1.4,
    )

    callout(fig, 0.075, 0.255, "FINAL EVIDENCE BANK", "622 records", "390 development + 232 held-out")
    callout(fig, 0.372, 0.255, "STAGE 2 COVERAGE", "38.3%", "238 of 622 records cited")
    callout(fig, 0.669, 0.255, "IDENTIFIER RESOLUTION", "100%", "337/337 citation occurrences resolved*")
    fig.text(
        0.075, 0.014,
        "*Thirty citation-format occurrences required deterministic repair before final validation. Percentages may differ by 0.1 due to rounding.",
        fontsize=7.2, color=MID_GREY,
    )

    plt.subplots_adjust(left=0.345, right=0.94, top=0.875, bottom=0.15, hspace=0.36)
    fig.savefig(OUTPUT_PATH, facecolor="white", bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()

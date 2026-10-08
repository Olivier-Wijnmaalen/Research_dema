"""Plot evidence-bank coverage and final-justification references by source."""
from collections import Counter
import json
import re

import matplotlib.pyplot as plt

from dema.config import PROJECT_ROOT


ROOT = PROJECT_ROOT
BANK_PATH = ROOT / "dema_run" / "combined_evidence_bank.json"
SCORE_PATH = ROOT / "dema_run" / "stage2" / "final_score.json"
OUTPUT_PATH = ROOT / "final_pipeline_source_usage.png"

SOURCE_LABELS = {
    "001": "ANPC Bulletin No. 33",
    "005": "UNDRR/GCF/BOAD training",
    "006": "ANAMET agro-hydro-climatic advisory",
    "007": "National meteorological-data mapping",
    "008": "GIZ digital transformation in Togo",
    "010": "National DRR Strategy",
    "011": "Multi-hazard early-warning framework",
    "015": "AU Digital Transformation Strategy",
    "018": "Open Data Day Togo report",
    "019": "WMO Togo Hydromet/EWS",
    "020": "ECOWAS early-warning monitors",
    "022": "ANPC training activities",
    "023": "Digital training for Togolese SMEs",
    "024": "Data Protection Africa: Togo",
    "026": "ANPC regional DRR platforms",
    "027": "PDNA report 2024",
    "028": "Post-disaster detailed assessment",
    "029": "National Civil Protection Policy 2030",
    "030": "National Contingency Plan 2022",
    "031": "Meteo Togo report",
    "032": "MENTD-BM PANT/PEES",
    "033": "GeoData Togo",
}


def source_id(item: dict) -> str:
    explicit = str(item.get("source_id", ""))
    if re.fullmatch(r"\d{3}", explicit):
        return explicit
    for field in ("source_chunk", "source_file"):
        match = re.search(r"(?<!\d)(\d{3})(?!\d)", str(item.get(field, "")))
        if match:
            return match.group(1)
    raise ValueError(f"Could not identify source for {item.get('evidence_id')}")


bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))
score = json.loads(SCORE_PATH.read_text(encoding="utf-8"))

evidence_source = {
    str(item["evidence_id"]): source_id(item) for item in bank["evidence_items"]
}
bank_counts = Counter(evidence_source.values())

references = []
for assessment in score["indicator_assessments"]:
    references.extend(assessment.get("evidence_supporting_score", []))
    references.extend(assessment.get("contrary_or_limiting_evidence", []))
reference_counts = Counter(evidence_source[reference] for reference in references)


def ranked_rows(counts: Counter, include_zero: bool = True):
    source_ids = SOURCE_LABELS.keys() if include_zero else counts.keys()
    return sorted(
        ((source, counts.get(source, 0)) for source in source_ids),
        key=lambda row: (-row[1], row[0]),
    )


def plot_panel(ax, rows, color, title, xlabel):
    labels = [SOURCE_LABELS.get(source, source) for source, _ in rows]
    values = [value for _, value in rows]
    positions = list(range(len(rows)))
    ax.barh(positions, values, color=color, height=0.7)
    ax.set_yticks(positions, labels=labels, fontsize=8.5)
    ax.invert_yaxis()
    ax.set_title(title, loc="left", fontsize=12, fontweight="bold", pad=10)
    ax.set_xlabel(xlabel, fontsize=9.5)
    ax.grid(axis="x", color="#dddddd", linewidth=0.7)
    ax.set_axisbelow(True)
    ax.set_xlim(0, max(values) * 1.14)
    for position, value in zip(positions, values):
        ax.text(value + max(values) * 0.012, position, str(value), va="center", fontsize=8)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)


fig, axes = plt.subplots(1, 2, figsize=(16, 10.5))
source_order = ranked_rows(bank_counts)
plot_panel(
    axes[0],
    source_order,
    "#386890",
    "A. Evidence items available in the final bank",
    "Evidence items (N = 622)",
)
plot_panel(
    axes[1],
    [(source, reference_counts.get(source, 0)) for source, _ in source_order],
    "#C87533",
    "B. Evidence references in final score justifications",
    "References across 31 indicator assessments (N = 337)",
)
fig.subplots_adjust(left=0.22, right=0.98, bottom=0.08, top=0.93, wspace=0.62)
fig.savefig(OUTPUT_PATH, dpi=300, bbox_inches="tight", facecolor="white")
plt.close(fig)

print(OUTPUT_PATH)
print("Top bank sources:", bank_counts.most_common(5))
print("Top justification sources:", reference_counts.most_common(5))

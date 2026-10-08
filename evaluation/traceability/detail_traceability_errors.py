"""Show token-level differences for the six held-out traceability failures."""
from difflib import SequenceMatcher
from pathlib import Path
import json
import re
import unicodedata


ROOT = Path(__file__).resolve().parents[2]
REJECTED = json.loads((ROOT / "dema_run" / "stage1_rejected_rows.json").read_text(encoding="utf-8"))
CHUNKS = ROOT / "final_substantive_corpus_files" / "chunks"


def tokens(text):
    text = unicodedata.normalize("NFKC", text)
    return re.findall(r"\w+(?:[’']\w+)*|[^\w\s]", text, flags=re.UNICODE)


def clipped(values, limit=45):
    if len(values) <= limit:
        return " ".join(values)
    head = " ".join(values[: limit // 2])
    tail = " ".join(values[-limit // 2 :])
    return f"{head} … [{len(values) - limit} tokens omitted] … {tail}"


for rejected in REJECTED:
    row = rejected["row"]
    quote_tokens = tokens(row["supporting_quote"])
    source_text = (CHUNKS / Path(rejected["chunk"])).read_text(encoding="utf-8")
    source_tokens = tokens(source_text)
    matcher = SequenceMatcher(None, quote_tokens, source_tokens, autojunk=False)
    blocks = [block for block in matcher.get_matching_blocks() if block.size]
    start = min(block.b for block in blocks)
    end = max(block.b + block.size for block in blocks)
    window_start = max(0, start - 15)
    window_end = min(len(source_tokens), end + 15)
    local_source = source_tokens[window_start:window_end]
    local_matcher = SequenceMatcher(None, quote_tokens, local_source, autojunk=False)
    edits = []
    for tag, i1, i2, j1, j2 in local_matcher.get_opcodes():
        if tag == "equal":
            continue
        # Ignore source context deliberately added outside the quotation.
        if tag == "insert" and (i1 == 0 or i1 == len(quote_tokens)):
            continue
        edits.append({
            "operation": tag,
            "generated_quote": clipped(quote_tokens[i1:i2]),
            "source_text": clipped(local_source[j1:j2]),
            "generated_token_span": [i1, i2],
            "source_token_span_in_chunk": [window_start + j1, window_start + j2],
        })
    print(json.dumps({
        "evidence_id": row["evidence_id"],
        "chunk": rejected["chunk"],
        "page_number": row.get("page_number"),
        "generated_quote": row["supporting_quote"],
        "longest_contiguous_match_tokens": max(block.size for block in blocks),
        "generated_quote_tokens": len(quote_tokens),
        "edits": edits,
    }, ensure_ascii=False, indent=2))

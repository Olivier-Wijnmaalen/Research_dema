import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


root = Path(__file__).resolve().parents[1]
here = Path(__file__).resolve().parent
source = here / "prompt_versions" / "P4_full_prompt.txt"
target = root / "DEMA_Maturity_Final_Scoring_Prompt_FROZEN.txt"
data = source.read_bytes()
target.write_bytes(data)
digest = hashlib.sha256(data).hexdigest().upper()
manifest = {
    "status": "frozen",
    "selected_version": "P4",
    "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
    "source_path": str(source.resolve()),
    "frozen_prompt_path": str(target.resolve()),
    "sha256": digest,
    "selection_basis": "45/45 prespecified calibration checks; 12/12 complete calibration cases; no unresolved systematic calibration failure; selected before the test run.",
    "test_result": "23/23 prespecified checks; 6/6 complete cases; temporally separated but not independently blinded.",
    "post_test_prompt_changes": 0,
}
(here / "frozen_prompt_manifest.json").write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
print(json.dumps(manifest, indent=2))

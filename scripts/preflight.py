"""Check local DEMA pipeline readiness without network or model calls."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV = ROOT / "pipeline" / ".env"
DEFAULT_CHUNKS = ROOT / "data" / "final_assessment" / "chunks"
DEFAULT_BASE_BANK = ROOT / "data" / "final_assessment" / "base_evidence_bank.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env", type=Path, default=DEFAULT_ENV)
    parser.add_argument("--chunks", type=Path, default=DEFAULT_CHUNKS)
    parser.add_argument("--base-bank", type=Path, default=DEFAULT_BASE_BANK)
    parser.add_argument(
        "--require-credentials",
        action="store_true",
        help="fail when the selected provider or Langfuse variables are absent",
    )
    return parser.parse_args()


def env_file_values(path: Path) -> dict[str, str]:
    """Read simple KEY=VALUE entries without exporting or displaying secrets."""
    if not path.is_file():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def main() -> int:
    args = parse_args()
    file_env = env_file_values(args.env)

    def configured(key: str) -> bool:
        return bool(os.environ.get(key) or file_env.get(key))

    failures: list[str] = []
    print(f"Python: {sys.version.split()[0]} ({sys.executable})")
    if sys.version_info < (3, 12):
        failures.append("Python 3.12 or newer is required by the documented environment")

    chunks = args.chunks.resolve()
    if not chunks.is_dir():
        failures.append(f"Chunk directory is missing: {chunks}")
        chunk_count = 0
    else:
        chunk_count = sum(1 for _ in chunks.rglob("*.md"))
        if chunk_count == 0:
            failures.append(f"No Markdown chunks found under: {chunks}")
    print(f"Chunks: {chunk_count} Markdown file(s) in {chunks}")

    bank_path = args.base_bank.resolve()
    evidence_count = 0
    if not bank_path.is_file():
        failures.append(f"Base evidence bank is missing: {bank_path}")
    else:
        try:
            bank = json.loads(bank_path.read_text(encoding="utf-8-sig"))
            items = bank.get("evidence_items")
            if not isinstance(items, list):
                raise ValueError("top-level evidence_items is not an array")
            evidence_count = len(items)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            failures.append(f"Base evidence bank cannot be read: {exc}")
    print(f"Base bank: {evidence_count} evidence record(s) in {bank_path}")

    snapshots = [
        ROOT / "prompts" / "stage1" / "frozen" / "prompt_stage1.json",
        ROOT / "prompts" / "stage2" / "frozen" / "prompt_stage2.json",
    ]
    missing_snapshots = [str(path) for path in snapshots if not path.is_file()]
    if missing_snapshots:
        failures.append("Frozen prompt snapshot(s) missing: " + ", ".join(missing_snapshots))
    print(f"Frozen prompt snapshots: {len(snapshots) - len(missing_snapshots)}/2 present")

    provider = (os.environ.get("AI_PROVIDER") or file_env.get("AI_PROVIDER") or "azure").lower()
    provider_keys = {
        "azure": ["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY"],
        "openai": ["OPENAI_API_KEY"],
    }
    if provider not in provider_keys:
        failures.append("AI_PROVIDER must be azure or openai")
        required_model_keys: list[str] = []
    else:
        required_model_keys = provider_keys[provider]
    required_keys = required_model_keys + [
        "LANGFUSE_PUBLIC_KEY",
        "LANGFUSE_SECRET_KEY",
        "LANGFUSE_HOST",
    ]
    missing_keys = [key for key in required_keys if not configured(key)]
    credential_state = "configured" if not missing_keys else "not configured"
    print(f"External services: {credential_state} for provider '{provider}'")
    if args.require_credentials and missing_keys:
        failures.append("Missing required environment variables: " + ", ".join(missing_keys))

    if failures:
        print("\nPreflight failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Preflight passed. No network or model call was made.")
    if missing_keys:
        print("Credentials are optional for this check; use --require-credentials before a paid rerun.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

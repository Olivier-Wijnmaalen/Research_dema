import argparse
import hashlib
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

from openai import OpenAI


ROOT = Path(__file__).resolve().parents[1]
ENV_FALLBACK = Path(r"C:\Users\olivi\OneDrive\Documenten\OPENAI_AZURE_V1\.env")
DEFAULT_ENDPOINT = "https://510-ai-research.services.ai.azure.com/openai/v1"
DEFAULT_MODEL = "gpt-4.1-students"


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def compile_request(prompt_text: str, case: dict) -> str:
    marker = "{{databank}}"
    if prompt_text.count(marker) != 1:
        raise ValueError(f"Prompt must contain exactly one {marker} placeholder")
    payload = {
        "country": case["country"],
        "scoring_scope": case["scoring_scope"],
        "instruction": "Score only the indicator in scoring_scope using this fictional evidence bank.",
        "indicator": case["indicator"],
        "evidence_items": case["evidence_items"],
    }
    return prompt_text.replace(marker, json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", type=Path, required=True)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", default=os.getenv("AZURE_OPENAI_DEPLOYMENT", DEFAULT_MODEL))
    parser.add_argument("--max-output-tokens", type=int, default=4000)
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    load_dotenv(ENV_FALLBACK)
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("AZURE_OPENAI_API_KEY is not configured")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", DEFAULT_ENDPOINT).rstrip("/")
    client = OpenAI(base_url=endpoint, api_key=api_key)

    prompt_text = args.prompt.read_text(encoding="utf-8-sig")
    suite = json.loads(args.cases.read_text(encoding="utf-8-sig"))
    cases = suite["cases"]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    request_dir = args.output_dir / "requests"
    raw_dir = args.output_dir / "raw"
    parsed_dir = args.output_dir / "parsed"
    request_dir.mkdir(exist_ok=True)
    raw_dir.mkdir(exist_ok=True)
    parsed_dir.mkdir(exist_ok=True)

    run = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "prompt_path": str(args.prompt.resolve()),
        "prompt_sha256": sha256(args.prompt),
        "cases_path": str(args.cases.resolve()),
        "cases_sha256": sha256(args.cases),
        "model_requested": args.model,
        "temperature": 0,
        "max_output_tokens": args.max_output_tokens,
        "endpoint_origin": endpoint.split("/openai/")[0],
        "python": sys.version,
        "platform": platform.platform(),
        "results": [],
    }
    (args.output_dir / "run_manifest.started.json").write_text(json.dumps(run, indent=2), encoding="utf-8")

    for case in cases:
        cid = case["case_id"]
        request = compile_request(prompt_text, case)
        request_path = request_dir / f"{cid}.txt"
        request_path.write_text(request, encoding="utf-8")
        item = {"case_id": cid, "request_sha256": sha256(request_path), "status": "started"}
        try:
            response = client.responses.create(
                model=args.model,
                input=request,
                temperature=0,
                max_output_tokens=args.max_output_tokens,
            )
            raw = response.output_text or ""
            raw_path = raw_dir / f"{cid}.txt"
            raw_path.write_text(raw, encoding="utf-8")
            item.update({
                "status": "completed",
                "response_id": getattr(response, "id", None),
                "model_returned": getattr(response, "model", None),
                "raw_sha256": sha256(raw_path),
                "usage": getattr(getattr(response, "usage", None), "model_dump", lambda: None)(),
            })
            try:
                parsed = json.loads(raw)
                (parsed_dir / f"{cid}.json").write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8")
                item["json_valid"] = True
            except json.JSONDecodeError as exc:
                item["json_valid"] = False
                item["parse_error"] = str(exc)
        except Exception as exc:
            item.update({"status": "technical_error", "error_type": type(exc).__name__, "error": str(exc)})
        run["results"].append(item)
        print(f"{cid}: {item['status']}, json_valid={item.get('json_valid')}")
        (args.output_dir / "run_manifest.progress.json").write_text(json.dumps(run, indent=2), encoding="utf-8")

    run["completed_at"] = datetime.now(timezone.utc).isoformat()
    (args.output_dir / "run_manifest.json").write_text(json.dumps(run, indent=2), encoding="utf-8")
    print(f"Completed {sum(x['status']=='completed' for x in run['results'])}/{len(cases)} calls")


if __name__ == "__main__":
    main()

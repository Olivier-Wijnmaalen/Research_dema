"""Retrieve the two authoritative DEMA prompts from Langfuse."""

from __future__ import annotations

from typing import Any

from .config import (
    EXTRACTION_PROMPT_NAME,
    EXTRACTION_PROMPT_SHA256,
    EXTRACTION_PROMPT_VERSION,
    SCORING_PROMPT_API_SHA256,
    SCORING_PROMPT_CRLF_SHA256,
    SCORING_PROMPT_NAME,
    SCORING_PROMPT_VERSION,
)
from .storage import sha256_text


def get_langfuse_client() -> Any:
    from langfuse import get_client

    client = get_client()
    if not client.auth_check():
        raise RuntimeError("Langfuse authentication failed")
    return client


def get_extraction_prompt(langfuse: Any) -> Any:
    prompt = langfuse.get_prompt(
        EXTRACTION_PROMPT_NAME,
        version=EXTRACTION_PROMPT_VERSION,
        type="text",
    )
    _verify_text_prompt(prompt, EXTRACTION_PROMPT_SHA256)
    return prompt


def get_scoring_prompt(langfuse: Any) -> Any:
    prompt = langfuse.get_prompt(
        SCORING_PROMPT_NAME,
        version=SCORING_PROMPT_VERSION,
        type="text",
    )
    _verify_text_prompt(
        prompt,
        SCORING_PROMPT_API_SHA256,
        crlf_sha256=SCORING_PROMPT_CRLF_SHA256,
    )
    return prompt


def scoring_prompt_snapshot(prompt: Any) -> dict[str, Any]:
    """Return the reproducibility record stored beside every Stage 2 run."""
    return {
        "name": prompt.name,
        "version": prompt.version,
        "api_sha256": sha256_text(prompt.prompt),
        "crlf_sha256": sha256_text(
            prompt.prompt.replace("\r\n", "\n").replace("\n", "\r\n")
        ),
        "config": prompt.config,
        "prompt": prompt.prompt,
    }


def _verify_text_prompt(
    prompt: Any,
    expected_sha256: str,
    *,
    crlf_sha256: str | None = None,
) -> None:
    if not isinstance(prompt.prompt, str):
        raise TypeError(f"Langfuse prompt {prompt.name!r} is not a text prompt")
    api_hash = sha256_text(prompt.prompt)
    if api_hash != expected_sha256:
        raise RuntimeError(f"Prompt hash mismatch for {prompt.name}: {api_hash}")
    if crlf_sha256 is not None:
        normalized_hash = sha256_text(
            prompt.prompt.replace("\r\n", "\n").replace("\n", "\r\n")
        )
        if normalized_hash != crlf_sha256:
            raise RuntimeError(
                f"CRLF prompt hash mismatch for {prompt.name}: {normalized_hash}"
            )


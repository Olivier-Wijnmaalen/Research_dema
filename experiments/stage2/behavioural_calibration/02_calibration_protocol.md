# Step 2: Prespecified calibration protocol

Status: fixed before synthetic case construction and before any model output is viewed.

## 1. Baseline prompt (P0)

P0 is `DEMA_Final_Scoring_Prompt_Documentary_Gap_Aware.txt` as it existed when this protocol was written.

- SHA-256: `8BC0F174945D09EE0B8BFDBA1B14CC978B39220726143775E45E5DC6BD3EDAED`
- Size: 73,337 bytes
- Last modified (UTC, filesystem metadata): 2026-09-02 12:43:39

The hash is the authoritative identity. A file with different bytes is a different prompt version. The prompt's embedded `AUTHORITATIVE CURRENT DEMA MATURITY FRAMEWORK` is used for all cases. Each case will include only the relevant indicator and its five phase descriptions in the model input, so the behavioural task matches the framework while remaining small enough to diagnose.

P0 is already documentary-gap-aware and therefore is not an untouched pre-refinement prompt. Results must be described as calibration of this selected baseline, not evidence that it was the first prompt historically used in the study.

## 2. Study design

- Calibration set: 12 cases, labelled `CAL-01` through `CAL-12`.
- Held-out set: 6 cases, labelled `HOLD-01` through `HOLD-06`.
- Unit of analysis: one fictional organisation and one DEMA indicator per case.
- Each case tests a deliberately difficult phase boundary or evidence-handling behaviour.
- All organisations, policies, systems, dates, places, quotations, and evidence statements are fictional.
- No Togo evidence, Togo scores, or paraphrases of distinctive Togo records may appear in a synthetic case.
- Each input contains the same field types needed by the scoring prompt: country, scoring scope, indicator name and code, five phase descriptions, and an evidence bank using production-style evidence fields.
- Calibration answer keys are completed and frozen before P0 is run.
- Held-out cases and answer keys must be sealed before calibration runs begin. The person refining the prompt must not inspect their contents until P0–Pn is frozen.

If independent custody of the hold-out set is unavailable, this limitation must be reported. Cases authored or inspected by the prompt refiner are a test set separated in time, but cannot be claimed as a blinded hold-out set.

## 3. Model configuration

The target configuration is:

- Model family: GPT-4.1.
- Exact provider/deployment: recorded from the successful API response and environment at run time; the label `gpt-4.1-students` alone is insufficient proof of model identity.
- Temperature: 0.
- Prompt: exact versioned prompt plus exactly one case payload per request.
- Output schema: the P0 JSON schema, restricted to exactly the one in-scope indicator.
- Maximum output tokens: 4,000 per case, unless a dry run establishes that this truncates otherwise valid outputs. Any change must be made before the first scored run and recorded here.
- Tool use, web access, retrieval, and external knowledge: disabled/unavailable to the scoring model.
- Seed: record if supported; otherwise record `not exposed`.
- One primary model call per case and prompt version.

The current `run_final_score.py` is not the calibration runner: its `call_model` function sets temperature to 0.2, defaults to a mutable Langfuse production prompt, and batches empirical indicators. A separate harness will freeze the local prompt bytes, construct one-case requests, and preserve the actual configuration.

## 4. Exact case-input contract

Each case JSON will contain:

```json
{
  "case_id": "CAL-01",
  "country": "Fictional country name",
  "scoring_scope": "Indicator X only: X.0.0 — exact indicator name",
  "indicator": {
    "indicator_code": "X.0.0",
    "indicator_name": "exact framework name",
    "subdimension": "exact framework subdimension",
    "phase_descriptions": {
      "1": "exact framework text",
      "2": "exact framework text",
      "3": "exact framework text",
      "4": "exact framework text",
      "5": "exact framework text"
    }
  },
  "evidence_items": [
    {
      "evidence_id": "E0001",
      "source_number": "S01",
      "source_file": "fictional filename",
      "reference_source_url": "",
      "page_number": "1",
      "dimension": "retrieval metadata",
      "subdimension": "retrieval metadata",
      "evidence_scope": "national/local/etc.",
      "country_specificity": "fictional-country specific",
      "evidence_statement": "fictional evidence statement",
      "evidence_directly_proves": "bounded interpretation",
      "limitations_or_weaknesses": "explicit boundary",
      "supporting_quote": "short fictional quotation"
    }
  ]
}
```

Empty fields remain present where production data may contain them. Evidence IDs are unique within a case. Source lineage will be explicit where records repeat another source.

## 5. Answer-key contract

Every case key must be written without model output and contain:

- case ID and primary rule(s) tested;
- acceptable phase or phase range;
- supported phase requirements, written as atomic propositions;
- unsupported phase requirements, written as atomic propositions;
- contrary or limiting evidence that must be retained;
- required reasoning behaviours;
- prohibited claims or reasoning behaviours;
- case-specific binary checks, each mapped to R1–R8;
- whether each check is critical;
- a short adjudication note explaining any acceptable range.

Exact phase should be used whenever the framework permits it. A range is allowed only for prespecified framework ambiguity, such as A.1.1's duplicated Phase 2/3 language, and must never be introduced after observing output.

## 6. Planned behavioural coverage

The 12 calibration cases collectively test:

1. clear lower-phase evidence plus one isolated advanced practice;
2. policy intention without implementation;
3. three records repeating one originating claim;
4. direct contradiction between an implementation report and an audit;
5. documentary silence versus explicit evidence of absence;
6. substantively irrelevant evidence with matching metadata;
7. relevant evidence filed under mismatching metadata;
8. complementary independent records satisfying separate phase elements;
9. local pilot evidence that must not be generalised nationally;
10. differences in authority, specificity, recency, and scope between sources;
11. a formal-policy phase that does not require operational implementation;
12. an ambiguous/non-nested DEMA boundary requiring qualified scoring.

The six held-out cases will cover the same eight rules in new combinations without copying calibration narratives.

## 7. Scoring and adjudication

Each prespecified case-specific check receives `PASS` or `FAIL`. No partial credit and no weighted composite score will be used.

Checks that can be verified mechanically include:

- valid JSON;
- exactly one assessment for the requested indicator;
- phase value is an integer from 1 to 5 and falls within the acceptable phase/range;
- all cited evidence IDs exist in the case;
- required output fields are present;
- IDs marked prohibited by the answer key are not listed as support.

Semantic checks require human adjudication against the answer key, including whether the response correctly distinguishes intention from implementation, documentary silence from factual absence, independent from duplicated support, and unresolved from resolvable contradiction. Text matching may flag passages for review but cannot determine these checks by itself.

One primary researcher codes all cases. For stronger reliability, a second coder should independently code at least all held-out cases and a prespecified subset of calibration cases. Disagreements are reported and resolved using the frozen key; post-output changes to a key must be logged as protocol deviations and cannot be silently applied.

An invalid or truncated model response fails all output-dependent checks for that attempt. It is not dropped from the denominator.

## 8. Metrics

Report raw numerators and denominators alongside both measures:

`Rule adherence rate = passed behavioural checks / applicable behavioural checks`

`Complete-case pass rate = cases passing every critical applicable check / cases tested`

Also report results by R1–R8 so a high aggregate cannot conceal a systematic rule failure. Noncritical formatting checks are reported separately and do not determine complete-case behavioural success.

## 9. Technical retry policy

A retry is permitted only for a provider/network failure, empty response, explicit server error, or truncation at the configured token limit. The same frozen request and configuration must be used. Both attempts and the reason for retry are retained. Schema-invalid but complete responses are substantive failures and are not retried merely to obtain a better answer.

## 10. Prompt refinement and stopping rule

- Evaluate at most five prompt versions total: P0 through P4.
- After each calibration version, perform qualitative failure analysis by rule and case.
- Each revision must address an observed systematic failure and change only the responsible instruction where practicable.
- Maintain a version log containing prompt hash, exact change, motivating failures, metrics, and new/regressed failures.
- Select the earliest version for which every critical calibration check passes and qualitative review identifies no unresolved systematic failure.
- If no version meets that condition by P4, freeze the best prespecified version using: (1) greatest number of critical checks passed, then (2) greatest number of complete cases, then (3) earlier version as tie-breaker. Report every remaining failure.
- Do not use held-out performance to select among prompt versions.

## 11. Freeze and held-out test

After selection, record the final prompt hash and run all six held-out cases once under the same configuration. Do not revise the prompt after inspecting held-out inputs or outputs. Any later revision starts a new calibration cycle with a newly sequestered test set; the six exposed cases are no longer held out.

## 12. Separation from empirical evaluation

Calibration measures adherence to prespecified scoring behaviours under controlled conditions. The held-out test measures whether those behaviours transfer to unseen synthetic conditions. Neither estimates the accuracy of actual Togo maturity scores. Empirical comparison, expert defensibility, usefulness, and residual failure analysis remain separate evaluations performed only after the prompt is frozen.

No cases, answer keys, model outputs, adherence values, or pass rates have been generated at this step.

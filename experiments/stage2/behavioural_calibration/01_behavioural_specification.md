# Step 1: DEMA behavioural specification

Status: source-derived draft, written before constructing synthetic cases or running calibration. No calibration results are claimed.

## Sources and scope

The working framework is the block headed `AUTHORITATIVE CURRENT DEMA MATURITY FRAMEWORK` in `DEMA_Maturity_Final_Scoring_Prompt_20aug.txt`. Its framework block is identical to the block in `DEMA_Final_Scoring_Prompt_Documentary_Gap_Aware.txt` (checked 9 September 2026). This establishes local consistency, not independent verification against an original DEMA publication.

The rules below distinguish framework requirements from existing scoring instructions and additional methodological operationalisation. The Togo reference scores, empirical evidence contents, and model assessment outputs were not used to derive these rules.

## Eight behavioural rules

### R1. Assign only a substantively supported phase

Award the highest phase whose applicable substantive requirements are fully supported by the supplied evidence. An isolated advanced practice does not establish the other requirements of that phase. Do not average evidence into a phase.

Basis: framework introductory instruction and existing scoring prompt evidence rule 5. A.2.1 distinguishes sporadic training, regular programmes with career incentives, and institutionalised capacity extending to local levels. An advanced activity alone cannot demonstrate that broader coverage.

Pass condition: the phase lies within the answer key's predefined acceptable phase or range, and the justification does not claim unsupported required characteristics.

Failure: an advanced example substitutes for missing criteria of the assigned phase.

Qualification: do not mechanically require every literal statement from all lower phases. Lower descriptions can contain deficiencies that higher phases resolve. DEMA also contains overlapping and non-nested descriptions. Any necessary intermediate capability must follow from the indicator's substantive wording; universal cumulative scoring is not established by the framework text alone.

### R2. Distinguish formal intention from implementation

Treat plans, recommendations, policy adoption, operational practice, and demonstrated effects as distinct evidential states. Credit a policy where the indicator requires a policy; require implementation evidence where the phase requires implementation.

Basis: A.1.1 Phase 4 requires an institutional framework that is both endorsed and operationalised. C.2.1 Phase 3 expressly concerns a formal strategy or policy framework. The existing prompt's institutional distinctions reinforce this interpretation.

Pass condition: formal documents support only the relevant formal requirements unless they also substantiate practice; operational requirements remain unsupported where appropriate.

Failure: a promised platform is described as operating, or a formal-strategy criterion is rejected solely because platform operation is undocumented.

### R3. Treat documentary silence as an evidence gap

Distinguish a source explicitly reporting absence or weakness from the absence of a supporting record. Do not turn silence into a factual claim that a national capability does not exist.

Basis: existing scoring prompt evidence rule 6; expanded explicitly in the documentary-gap-aware version. This is a scoring convention, not a deduction from DEMA's phase labels.

Pass condition: unsupported characteristics are described as not demonstrated in the supplied evidence; factual absence claims have direct evidence.

Failure: missing documentation becomes a claim of real-world nonexistence.

Qualification: the existing schema forces a Phase 1 fallback when no criterion is supported. In that situation the output must identify the score as a documentary fallback, not falsely claim that Phase 1's substantive deficiency has been observed.

### R4. Do not count duplicate claims as independent corroboration

Repeated records, reprints, or sources repeating one originating claim do not establish independent confirmation or wider implementation. Assess their underlying provenance and substantive contribution.

Basis: methodological operationalisation of criterion-based scoring and the existing prohibition on strengthening claims beyond the evidence. DEMA does not itself specify a duplicate-record rule. The runner removes some exact duplicates, but this does not establish independence of remaining records.

Pass condition: repetitions do not raise the phase or inflate claims of corroboration, coverage, or routine practice.

Failure: three repetitions of one report are treated as three independent implementations or confirmations.

### R5. Retain and address material contrary or limiting evidence

Consider relevant contradictions and limits alongside positive evidence. Explain disagreements using directness, specificity, authority, recency, and scope; do not automatically choose the newest source when it measures something different. Preserve uncertainty when the conflict cannot be resolved.

Basis: existing scoring prompt evidence rules 4 and 7 and its contrary-evidence output fields.

Pass condition: answer-key-designated material limiting records are retained and their implications explained without unsupported resolution.

Failure: a conflicting operational audit is ignored, or its conclusion is silently replaced by a promotional claim.

### R6. Judge relevance from substantive content

Use records only for requirements they actually address, respecting institutional, geographic, temporal, and implementation scope. Retrieval labels do not establish relevance. A record may support multiple indicators if each use is justified.

Basis: indicator-specific DEMA definitions and existing scoring prompt evidence rules 2–4.

Pass condition: irrelevant records do not support the score; relevant records with imperfect retrieval labels remain eligible.

Failure: matching metadata alone is used as support, or evidence of a local pilot is generalised to national coverage.

### R7. Combine complementary evidence without inventing links

Use compatible evidence jointly where separate records substantiate different requirements of the same phase. Do not require a single record to prove the whole phase. Establish that the records concern compatible entities, periods, and scope before combining them.

Basis: operationalisation of the existing highest-fully-supported-phase rule and evidence-by-evidence justification. For example, C.2.2 Phase 3 includes allocations for information sharing, a coordinating unit, and training, which may be documented separately. DEMA does not prescribe a source-count threshold.

Pass condition: complementary support is recognised, each material requirement has traceable evidence, and no unstated connection is assumed.

Failure: an otherwise fully supported phase is rejected because support spans records, or unrelated programmes are combined into an invented national system.

### R8. Explain the boundary to a higher phase

Identify the actual higher-phase requirements that remain unsubstantiated or contradicted, with criterion-specific reasoning. Where relevant, explain why isolated higher-phase evidence is insufficient. Do not invent a Phase 6 for a Phase 5 assessment.

Basis: DEMA phase descriptions and the existing prompt's explanatory standard, required reasoning content, and `next_phase_gap` field.

Pass condition: `next_phase_gap` identifies the predefined missing characteristics and correctly distinguishes evidence gaps from documented weaknesses; Phase 5 states that no higher framework phase exists.

Failure: a generic recommendation replaces the phase boundary, or the output states that a supported criterion is missing.

## Issues to resolve before fixing answer keys

1. A.1.1 Phases 2 and 3 are substantively identical. Do not invent a distinction. Avoid this boundary for exact-phase calibration; if it is tested, prespecify an acceptable range and require acknowledgement of the ambiguity.
2. A.1.4 Phase 4 changes emphasis to a regularly updated data strategy and standards. This reinforces the need for indicator-specific reasoning rather than assuming uniformly nested phase descriptions.
3. Confirm whether the embedded local framework is the study's authoritative version. If a separate original framework exists, reconcile it before constructing answer keys.
4. P0 has now been selected as the documentary-gap-aware prompt and is frozen by hash in Step 2. It should not be described as an untouched historical baseline. A live Langfuse `production` label remains mutable and is not the authoritative P0 identity.
5. Reconcile model configuration. The inspected `run_final_score.py` requests temperature 0.2 and defaults to deployment `gpt-4.1-students`; the proposed calibration protocol requests GPT-4.1 at temperature 0. Deployment name alone does not verify the underlying model version. The runner sends a compiled prompt as `input` rather than a separately declared system message. Preserve and report the actual message structure and output schema.

## Subsequent steps, in order

2. Fix the protocol, input contract, baseline, configuration, stopping rule, and grading definitions. Use 12 calibration and 6 held-out cases if feasible. Treat all applicable R1–R8 checks as critical, with a maximum of five evaluated prompt versions including P0. Stop earlier when all critical calibration checks pass and qualitative review finds no unresolved systematic failure. If the cap is reached, report remaining failures rather than claiming successful calibration.
3. Construct fictional calibration cases with exact framework excerpts and production-shaped evidence banks. Write acceptable phases, supported and unsupported requirements, required reasoning, and failures before any model run. Freeze answer keys with hashes and timestamps. Keys drafted by this assistant require researcher review before being called researcher-defined.
4. Have a separate custodian construct and seal held-out cases against the frozen specifications. The prompt refiner must not inspect those cases or their outputs before prompt freeze. Merely placing cases in another folder does not establish blindness; self-authored cases must be disclosed as such if independent custody is unavailable.
5. Run P0 on calibration cases; preserve complete raw responses, requests, prompt/configuration hashes, errors, and run metadata. Score structural criteria deterministically. Use explicit human coding for semantic behaviours; keyword presence alone does not establish correct reasoning. Never expose keys to the scoring model.
6. Analyse failures and make targeted prompt changes. Log each change, its motivating failed checks, and subsequent results. Keep the denominator fixed; invalid outputs fail required checks, while transport failures are recorded separately and rerun under a predefined technical-retry policy.
7. Freeze the selected prompt and run the held-out set once. Report behavioural checks passed / checks tested and complete cases passed / cases tested, separately for calibration and hold-out. Disclose unresolved failures and any human-coding uncertainty. Do not tune on held-out findings.
8. Only then apply the frozen prompt to empirical evidence and evaluate defensibility and usefulness separately. Existing Togo runs cannot retrospectively be described as having occurred after this new calibration. A prospective rerun or an explicitly retrospective validation description is necessary.

No synthetic cases, answer keys, model runs, prompt revisions, or empirical re-scoring have been completed in Step 1.

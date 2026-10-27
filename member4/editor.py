"""Evidence-conditioned editor.

C and D use one structured prompt. B is the direct-rewrite baseline.
Invalid model text is saved and is not rewritten. Nothing is written into
Member 5's evaluation folder.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent

METHOD_BY_CONDITION = {
    "full_source": "B",
    "gold": "C",
    "automatic": "D",
    "candidate_not_gold": "dev_abstention",
}
EXPERIMENT_CONDITIONS = ("full_source", "gold", "automatic")
CONDITION_ORDER = {"full_source": 0, "gold": 1, "automatic": 2, "candidate_not_gold": 3}
DECISIONS = {"revise", "unchanged", "abstain"}
ABSTAIN_TOKEN = "ABSTAIN"
MODEL_KEYS = {
    "input_id",
    "example_id",
    "method_code",
    "evidence_condition",
    "original_claim",
    "evidence_passage",
    "prompt_version",
    "prompt_sha256",
    "counts_as_experiment",
}
CLAIM_MARK = "<<ORIGINAL_CLAIM>>"
EVIDENCE_MARK = "<<EVIDENCE>>"


class EditorError(Exception):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def new_run_id(exploratory: bool) -> str:
    """Microseconds plus a random suffix, so two runs in one second stay distinct."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    label = "_exploratory" if exploratory else ""
    return f"{stamp}_{uuid.uuid4().hex[:8]}{label}"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_config() -> dict:
    return json.loads((ROOT / "config.json").read_text(encoding="utf-8"))


def repo_path(path_str: str) -> Path:
    path = Path(path_str)
    return path if path.is_absolute() else (ROOT / path).resolve()


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def load_prompt(config: dict, condition: str) -> tuple[str, str]:
    if condition == "full_source":
        version = config["baseline_prompt_version"]
        path = repo_path(config["baseline_prompt"])
    elif condition in {"gold", "automatic", "candidate_not_gold"}:
        version = config["prompt_version"]
        path = repo_path(config["structured_prompt"])
    else:
        raise EditorError(f"Unknown evidence condition: {condition}")
    text = path.read_text(encoding="utf-8")
    if CLAIM_MARK not in text or EVIDENCE_MARK not in text:
        raise EditorError(f"Prompt is missing placeholders: {path}")
    return version, text


def render_prompt(template: str, claim: str, evidence: str) -> str:
    return template.replace(CLAIM_MARK, claim, 1).replace(EVIDENCE_MARK, evidence, 1)


def index_rows(rows: list[dict], label: str) -> dict[str, dict]:
    indexed = {}
    for row in rows:
        example_id = row["example_id"]
        if example_id in indexed:
            raise EditorError(f"Duplicate {label} id: {example_id}")
        indexed[example_id] = row
    return indexed


def model_row(example_id, claim, condition, evidence, prompt_version, prompt_hash, experiment) -> dict:
    row = {
        "input_id": f"{example_id}__{condition}",
        "example_id": example_id,
        "method_code": METHOD_BY_CONDITION[condition],
        "evidence_condition": condition,
        "original_claim": claim,
        "evidence_passage": evidence,
        "prompt_version": prompt_version,
        "prompt_sha256": prompt_hash,
        "counts_as_experiment": experiment,
    }
    if set(row) != MODEL_KEYS or evidence == "":
        raise EditorError(f"Bad model input for {example_id} {condition}")
    return row


def load_inputs(config: dict | None = None) -> tuple[list[dict], dict[str, dict]]:
    """Build model rows from Member 1 and Member 2 files. Labels stay in the audit dict."""
    config = config or load_config()
    paths = config["evidence"]
    calibration = [
        json.loads(line)
        for line in repo_path(paths["calibration_file"]).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    by_id = index_rows(calibration, "calibration")
    gold_rows = index_rows(read_csv(repo_path(paths["gold_file"])), "gold")
    automatic_rows = index_rows(read_csv(repo_path(paths["automatic_file"])), "automatic")
    review_rows = index_rows(read_csv(repo_path(paths["review_file"])), "review")
    structured_version, structured_text = load_prompt(config, "gold")
    baseline_version, baseline_text = load_prompt(config, "full_source")
    automatic_version, automatic_text = load_prompt(config, "automatic")
    if structured_text != automatic_text or structured_version != automatic_version:
        raise EditorError("Conditions C and D must use the same prompt.")
    structured_hash = sha256_text(structured_text)
    baseline_hash = sha256_text(baseline_text)
    gold_field = paths["gold_text_field"]
    automatic_field = paths["automatic_text_field"]
    candidate_field = paths["candidate_text_field"]

    rows = []
    audit = {}
    for example_id in sorted(by_id):
        record = by_id[example_id]
        annotation = record["annotation"]
        review = review_rows.get(example_id)
        if review is None or review["claim_text"] != record["original_claim"]:
            raise EditorError(f"{example_id} does not match the evidence review claim.")
        claim = record["original_claim"]
        audit[example_id] = {
            "evaluation_eligible": bool(annotation["evaluation_eligible"]),
            "calibration_use": annotation["calibration_use"],
            "expected_action": annotation["expected_action"],
        }
        rows.append(model_row(
            example_id, claim, "full_source", record["source_text"],
            baseline_version, baseline_hash, True,
        ))
        gold = gold_rows.get(example_id)
        verified = (
            gold is not None
            and review["review_status"] == "verified"
            and review["evidence_sufficient"] == "yes"
            and gold[gold_field].strip() != ""
        )
        if verified:
            rows.append(model_row(
                example_id, claim, "gold", gold[gold_field],
                structured_version, structured_hash, True,
            ))
        else:
            candidate = review[candidate_field]
            if candidate.strip() == "":
                raise EditorError(f"{example_id} has no gold passage and no candidate passage.")
            rows.append(model_row(
                example_id, claim, "candidate_not_gold", candidate,
                structured_version, structured_hash, False,
            ))
        automatic = automatic_rows.get(example_id)
        if automatic is None or automatic[automatic_field].strip() == "":
            raise EditorError(f"{example_id} has no automatic evidence.")
        rows.append(model_row(
            example_id, claim, "automatic", automatic[automatic_field],
            structured_version, structured_hash, True,
        ))

    rows.sort(key=lambda row: (row["example_id"], CONDITION_ORDER[row["evidence_condition"]]))
    strong_id = config["supported_strong_causal_example_id"]
    if audit[strong_id]["calibration_use"] != "supported_causal_control_example":
        raise EditorError(f"{strong_id} is not the supported causal control.")
    strong = {
        row["evidence_condition"]
        for row in rows
        if row["example_id"] == strong_id and row["counts_as_experiment"]
    }
    if strong != {"full_source", "gold", "automatic"}:
        raise EditorError(f"{strong_id} must be present under B, C, and D.")
    return rows, audit


def empty_check() -> dict:
    return {
        "parse_status": "unparseable",
        "failures": ["unparseable_json"],
        "output_action": None,
        "quote_check": "",
        "span_check": "",
        "decision": None,
        "original_claim": None,
        "revised_claim": None,
        "evidence_passage": None,
        "explanation": None,
        "claim_span": None,
        "span_start": None,
        "span_end": None,
    }


def _text_field(payload: dict, key: str, failures: list[str]) -> str | None:
    value = payload.get(key)
    if key not in payload:
        failures.append(f"missing_field:{key}")
        return None
    if not isinstance(value, str):
        failures.append(f"{key}_not_string")
        return None
    return value


def _offset_field(payload: dict, key: str, failures: list[str]):
    if key not in payload:
        failures.append(f"missing_field:{key}")
        return None
    return payload[key]


def check_claim_span(claim: str, span: str | None, start, end, failures: list[str], decision: str | None) -> str:
    """Accept a span only when its offsets select that exact claim text."""
    if span is None:
        return "missing_span"
    if span == "":
        if start is not None or end is not None:
            failures.append("empty_span_has_offsets")
            return "invalid_offsets"
        if decision == "revise":
            failures.append("claim_span_missing")
            return "missing_span"
        return "empty_span"
    if not isinstance(start, int) or not isinstance(end, int) or isinstance(start, bool) or isinstance(end, bool):
        failures.append("claim_offsets_not_integers")
        return "invalid_offsets"
    if start < 0 or end > len(claim) or start >= end or claim[start:end] != span:
        failures.append("claim_offsets_mismatch")
        return "offset_mismatch"
    if decision == "unchanged":
        failures.append("unchanged_has_claim_span")
    return "exact_span"


def validate_structured(raw_text: str | None, claim: str, evidence: str) -> dict:
    """Check the editor JSON. Model strings and offsets are returned unchanged."""
    result = empty_check()
    if raw_text is None:
        return result
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        return result
    if not isinstance(payload, dict):
        result["failures"] = ["json_not_object"]
        return result

    failures: list[str] = []
    decision = payload.get("decision")
    revised = _text_field(payload, "revision", failures)
    quote = _text_field(payload, "evidence_passage", failures)
    explanation = _text_field(payload, "explanation", failures)
    span = _text_field(payload, "claim_span", failures)
    start = _offset_field(payload, "span_start", failures)
    end = _offset_field(payload, "span_end", failures)
    if decision not in DECISIONS:
        failures.append("invalid_decision")
        decision = decision if isinstance(decision, str) else None
    if quote is None:
        quote_check = "missing_quote"
    elif quote == "" and decision == "abstain":
        quote_check = "empty_quote_on_abstention"
    elif quote == "":
        failures.append("evidence_passage_missing")
        quote_check = "missing_quote"
    elif quote in evidence:
        quote_check = "exact_match"
    else:
        failures.append("evidence_passage_not_exact")
        quote_check = "quote_not_in_evidence"
    if explanation is not None and explanation.strip() == "":
        failures.append("explanation_missing")
    span_check = check_claim_span(claim, span, start, end, failures, decision)
    if decision == "unchanged" and revised is not None and revised != claim:
        failures.append("unchanged_text_changed")
    if decision == "revise" and revised == "":
        failures.append("revise_empty_revision")
    if decision == "revise" and revised == claim:
        failures.append("revise_text_unchanged")
    if decision == "abstain" and revised not in (None, ""):
        failures.append("abstain_nonempty_revision")

    result.update({
        "parse_status": "ok" if not failures else "schema_invalid",
        "failures": failures,
        "output_action": decision if not failures else None,
        "quote_check": quote_check,
        "span_check": span_check,
        "decision": decision,
        "revised_claim": revised,
        "evidence_passage": quote,
        "explanation": explanation,
        "claim_span": span,
        "span_start": start,
        "span_end": end,
    })
    return result


def validate_baseline(raw_text: str | None, claim: str) -> dict:
    result = empty_check()
    result["quote_check"] = "not_requested_for_baseline"
    result["span_check"] = "not_requested_for_baseline"
    if raw_text is None:
        return result
    if raw_text == "":
        result["parse_status"] = "schema_invalid"
        result["failures"] = ["empty_baseline_output"]
        result["revised_claim"] = raw_text
        return result
    if raw_text == ABSTAIN_TOKEN:
        action = "abstain"
        revised = ""
    elif raw_text == claim:
        action = "unchanged"
        revised = raw_text
    else:
        action = "revise"
        revised = raw_text
    result.update({
        "parse_status": "ok",
        "failures": [],
        "output_action": action,
        "decision": action,
        "revised_claim": revised,
    })
    return result


def validate_output(raw_text: str | None, condition: str, claim: str, evidence: str) -> dict:
    if condition == "full_source":
        return validate_baseline(raw_text, claim)
    return validate_structured(raw_text, claim, evidence)


def select_inputs(rows, conditions, example_ids=None) -> list[dict]:
    selected = []
    for row in rows:
        if row["evidence_condition"] not in conditions:
            continue
        if example_ids is not None and row["example_id"] not in example_ids:
            continue
        selected.append(row)
    return selected


def generation_settings(config: dict) -> dict:
    generation = config["generation"]
    if config.get("model_identifier") != "Qwen/Qwen2.5-7B-Instruct":
        raise EditorError("B, C, and D share Qwen/Qwen2.5-7B-Instruct.")
    if generation.get("do_sample") is not False or generation.get("max_new_tokens") != 512:
        raise EditorError("B, C, and D use greedy decoding and a 512-token output limit.")
    if config.get("fine_tuned"):
        raise EditorError("The pilot uses the released generator without task-specific fine-tuning.")
    return {"do_sample": False, "max_new_tokens": 512}


def load_generator(config: dict):
    """Load the shared generator before a run directory is created."""
    settings = generation_settings(config)
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as exc:
        raise EditorError("Install torch and transformers. No output was written.") from exc
    model_name = config["model_identifier"]
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype="auto", device_map="auto")
    model.eval()
    return tokenizer, model, torch, settings


def generate_text(tokenizer, model, torch_module, prompt: str, settings: dict) -> str:
    messages = [{"role": "user", "content": prompt}]
    chat = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(chat, return_tensors="pt")
    inputs = {key: value.to(model.device) for key, value in inputs.items()}
    with torch_module.no_grad():
        output = model.generate(**inputs, do_sample=settings["do_sample"], max_new_tokens=settings["max_new_tokens"])
    new_tokens = output[0, inputs["input_ids"].shape[-1]:]
    return tokenizer.decode(new_tokens, skip_special_tokens=True)


def guard_evaluation(selected, audit, config, evaluation_run: bool) -> None:
    eligible = sorted({
        row["example_id"]
        for row in selected
        if audit.get(row["example_id"], {}).get("evaluation_eligible")
    })
    if not eligible:
        return
    if not evaluation_run or not config.get("frozen_for_evaluation"):
        raise EditorError(
            "Reserved evaluation inputs stay unused until frozen_for_evaluation is true."
        )


def run_batch(args, config: dict | None = None) -> Path:
    config = config or load_config()
    rows, audit = load_inputs(config)
    if args.exploratory:
        conditions = {"gold"}
        example_ids = set(config["exploratory_example_ids"])
    elif args.condition == "all":
        conditions = set(EXPERIMENT_CONDITIONS)
        if args.include_abstention_practice:
            conditions.add("candidate_not_gold")
        example_ids = {item.strip() for item in args.examples.split(",") if item.strip()} or None
    else:
        conditions = {args.condition}
        example_ids = {item.strip() for item in args.examples.split(",") if item.strip()} or None
    selected = select_inputs(rows, conditions, example_ids)
    if not selected:
        raise EditorError("No inputs matched.")
    guard_evaluation(selected, audit, config, args.evaluation_run)
    tokenizer, model, torch_module, settings = load_generator(config)
    model_name = config["model_identifier"]
    exploratory = bool(args.exploratory)
    measured = bool(args.evaluation_run and config.get("frozen_for_evaluation") and not exploratory)
    run_id = new_run_id(exploratory)
    run_dir = ROOT / "data" / "outputs" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    raw_rows = []
    parsed_rows = []
    for item in selected:
        version, template = load_prompt(config, item["evidence_condition"])
        if version != item["prompt_version"]:
            raise EditorError("Prompt version changed. Review config.json before running.")
        rendered = render_prompt(template, item["original_claim"], item["evidence_passage"])
        raw_text = None
        model_error = ""
        try:
            raw_text = generate_text(tokenizer, model, torch_module, rendered, settings)
        except Exception as exc:
            model_error = str(exc)
        raw_rows.append({
            "input_id": item["input_id"],
            "example_id": item["example_id"],
            "method_code": item["method_code"],
            "evidence_condition": item["evidence_condition"],
            "prompt_version": version,
            "prompt_sha256": item["prompt_sha256"],
            "rendered_prompt": rendered,
            "model_identifier": model_name,
            "generation_settings": settings,
            "raw_text": raw_text,
            "model_error": model_error,
            "created_utc": utc_now(),
            "run_id": run_id,
            "exploratory": exploratory,
        })
        checked = validate_output(
            raw_text, item["evidence_condition"], item["original_claim"], item["evidence_passage"]
        )
        if model_error:
            checked["parse_status"] = "model_error"
            checked["failures"] = ["model_error"]
            checked["output_action"] = None
        accepted = checked["parse_status"] == "ok"
        parsed_rows.append({
            "input_id": item["input_id"],
            "example_id": item["example_id"],
            "method_code": item["method_code"],
            "evidence_condition": item["evidence_condition"],
            "prompt_version": version,
            "prompt_sha256": item["prompt_sha256"],
            "model_identifier": model_name,
            "generation_settings": settings,
            "input_original_claim": item["original_claim"],
            "supplied_evidence": item["evidence_passage"],
            "run_id": run_id,
            "exploratory": exploratory,
            "counts_as_measured_quality": measured,
            "output_text": checked["revised_claim"] if accepted else "",
            "output_action": checked["output_action"] if accepted else "",
            "parse_status": checked["parse_status"],
            "validation_failures": checked["failures"],
            "quote_check": checked["quote_check"],
            "span_check": checked["span_check"],
            "model_decision": checked["decision"],
            "model_claim_span": checked["claim_span"],
            "model_span_start": checked["span_start"],
            "model_span_end": checked["span_end"],
            "model_revised_claim": checked["revised_claim"],
            "model_evidence_passage": checked["evidence_passage"],
            "model_explanation": checked["explanation"],
        })
    write_jsonl(run_dir / "raw.jsonl", raw_rows)
    write_jsonl(run_dir / "parsed.jsonl", parsed_rows)
    (run_dir / "run_manifest.json").write_text(json.dumps({
        "run_id": run_id,
        "created_utc": utc_now(),
        "exploratory": exploratory,
        "counts_as_measured_quality": measured,
        "input_ids": [row["input_id"] for row in selected],
        "model_identifier": model_name,
        "generation_settings": settings,
        "rerun_policy": "No automatic retry. A replacement run uses a new run_id.",
        "repair_invalid_outputs": False,
    }, indent=2) + "\n", encoding="utf-8")
    failures = [row["input_id"] for row in parsed_rows if row["parse_status"] != "ok"]
    print(f"Run directory: {run_dir}")
    print(f"Inputs: {len(parsed_rows)}. Failures: {len(failures)}.")
    if exploratory:
        print("Exploratory run. A handpicked result is not a measured quality score.")
    return run_dir


def assert_member4_output(path: Path) -> Path:
    resolved = path.resolve()
    root = ROOT.resolve()
    evaluation = (REPO / "evaluation").resolve()
    if root != resolved and root not in resolved.parents:
        raise EditorError("Handoff files stay inside member4.")
    if evaluation == resolved or evaluation in resolved.parents:
        raise EditorError("evaluation/ belongs to Member 5.")
    return resolved


def export_run(run_dir: Path, config: dict | None = None) -> dict[str, Path]:
    config = config or load_config()
    run_dir = assert_member4_output(run_dir)
    parsed_path = run_dir / "parsed.jsonl"
    if not parsed_path.exists():
        raise EditorError(f"No parsed outputs at {parsed_path}")
    codes = config["anonymized_method_codes"]
    internal, rater, failures, output_map = [], [], [], []
    rater_count = 0
    for row in read_jsonl(parsed_path):
        accepted = row["parse_status"] == "ok" and row["method_code"] in codes
        rater_id = ""
        if accepted:
            rater_count += 1
            rater_id = f"{row['run_id']}__R{rater_count:03d}"
            output_map.append({
                "rater_output_id": rater_id,
                "internal_output_id": f"{row['run_id']}__{row['input_id']}",
                "editor_method_code": row["method_code"],
                "anonymized_method_code": codes[row["method_code"]],
                "evidence_condition": row["evidence_condition"],
                "example_id": row["example_id"],
            })
        record = {
            "output_id": rater_id if accepted else f"{row['run_id']}__{row['input_id']}",
            "example_id": row["example_id"],
            "method_code": codes[row["method_code"]] if accepted else "",
            "editor_method_code": row["method_code"],
            "evidence_condition": row["evidence_condition"],
            "original_claim": row["input_original_claim"],
            "output_text": row["output_text"] if accepted else "",
            "output_action": row["output_action"] if accepted else "",
            "evidence_passage": row["supplied_evidence"],
            "explanation": row["model_explanation"] or "",
            "decision": row["model_decision"] or "",
            "parse_status": row["parse_status"],
            "validation_failures": "|".join(row["validation_failures"]),
            "quote_check": row["quote_check"],
            "prompt_version": row["prompt_version"],
            "model_identifier": row["model_identifier"],
            "run_id": row["run_id"],
            "exploratory": row["exploratory"],
            "model_revised_claim": row["model_revised_claim"] or "",
        }
        internal.append(record)
        if accepted:
            rater.append({key: record[key] for key in (
                "output_id", "example_id", "method_code", "original_claim",
                "output_text", "output_action", "evidence_passage", "explanation",
            )})
        else:
            failures.append(record)
    paths = {
        "internal": run_dir / "member5_handoff.csv",
        "rater": run_dir / "rater_sheet_seed.csv",
        "failures": run_dir / "parse_failures.csv",
        "key": run_dir / "anonymization_key.json",
    }
    for name, columns in (
        ("internal", list(internal[0]) if internal else ["output_id"]),
        ("rater", [
            "output_id", "example_id", "method_code", "original_claim",
            "output_text", "output_action", "evidence_passage", "explanation",
        ]),
        ("failures", [
            "output_id", "example_id", "editor_method_code", "evidence_condition",
            "parse_status", "validation_failures", "run_id",
        ]),
    ):
        with paths[name].open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
            writer.writeheader()
            source = {"internal": internal, "rater": rater, "failures": failures}[name]
            writer.writerows(source)
    paths["key"].write_text(json.dumps({
        "rater_visibility": "withhold_from_raters",
        "method_codes": codes,
        "meaning": {
            "B": "direct rewrite with the full source",
            "C": "structured editor with gold evidence",
            "D": "structured editor with automatic evidence",
        },
        "output_map": output_map,
    }, indent=2) + "\n", encoding="utf-8")
    return paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evidence-conditioned editor")
    commands = parser.add_subparsers(dest="command", required=True)
    run_parser = commands.add_parser("run")
    run_parser.add_argument(
        "--condition",
        choices=["all", "full_source", "gold", "automatic", "candidate_not_gold"],
        default="gold",
    )
    run_parser.add_argument("--examples", default="")
    run_parser.add_argument("--exploratory", action="store_true")
    run_parser.add_argument("--include-abstention-practice", action="store_true")
    run_parser.add_argument("--evaluation-run", action="store_true")
    export_parser = commands.add_parser("export")
    export_parser.add_argument("--run", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "run":
        run_dir = run_batch(args)
        failed = any(row["parse_status"] != "ok" for row in read_jsonl(run_dir / "parsed.jsonl"))
        return 1 if failed else 0
    for name, path in export_run(args.run).items():
        print(f"{name}: {path}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except EditorError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)

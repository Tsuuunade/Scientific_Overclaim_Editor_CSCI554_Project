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
import os
import sys
import urllib.error
import urllib.request
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
DECISIONS = {"supported", "overclaim", "insufficient_evidence"}
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


def _text_field(payload: dict, key: str, failures: list[str]) -> str | None:
    value = payload.get(key)
    if key not in payload:
        failures.append(f"missing_field:{key}")
        return None
    if not isinstance(value, str):
        failures.append(f"{key}_not_string")
        return None
    return value


def validate_structured(raw_text: str | None, claim: str, evidence: str) -> dict:
    """Check the editor JSON. Model strings are returned unchanged."""
    result = {
        "parse_status": "unparseable",
        "failures": ["unparseable_json"],
        "output_action": None,
        "quote_check": "",
        "decision": None,
        "original_claim": None,
        "revised_claim": None,
        "evidence_passage": None,
        "explanation": None,
    }
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
    original = _text_field(payload, "original_claim", failures)
    revised = _text_field(payload, "revised_claim", failures)
    quote = _text_field(payload, "evidence_passage", failures)
    explanation = _text_field(payload, "explanation", failures)
    if decision not in DECISIONS:
        failures.append("invalid_decision")
        decision = decision if isinstance(decision, str) else None
    if original is not None and original != claim:
        failures.append("original_claim_mismatch")
    if quote is None:
        quote_check = "missing_quote"
    elif quote == "" and decision == "insufficient_evidence":
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
    if decision == "supported" and revised is not None and revised != claim:
        failures.append("supported_text_changed")
    if decision == "overclaim" and revised == "":
        failures.append("overclaim_empty_revision")
    if decision == "overclaim" and revised == claim:
        failures.append("overclaim_text_unchanged")
    if decision == "insufficient_evidence" and revised not in (None, ""):
        failures.append("abstain_nonempty_revision")

    action = None
    if not failures and decision == "supported" and revised == claim:
        action = "unchanged"
    elif not failures and decision == "overclaim":
        action = "revise"
    elif not failures and decision == "insufficient_evidence" and revised == "":
        action = "abstain"
    result.update({
        "parse_status": "ok" if not failures else "schema_invalid",
        "failures": failures,
        "output_action": action,
        "quote_check": quote_check,
        "decision": decision,
        "original_claim": original,
        "revised_claim": revised,
        "evidence_passage": quote,
        "explanation": explanation,
    })
    return result


def validate_baseline(raw_text: str | None, claim: str) -> dict:
    result = {
        "parse_status": "unparseable",
        "failures": ["empty_baseline_output"] if raw_text == "" else ["unparseable_json"],
        "output_action": None,
        "quote_check": "not_requested_for_baseline",
        "decision": None,
        "original_claim": None,
        "revised_claim": raw_text if raw_text is not None else None,
        "evidence_passage": None,
        "explanation": None,
    }
    if raw_text:
        result.update({
            "parse_status": "ok",
            "failures": [],
            "output_action": "unchanged" if raw_text == claim else "revise",
        })
    elif raw_text == "":
        result["parse_status"] = "schema_invalid"
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


def require_model(config: dict) -> str:
    api = config["api"]
    if not os.environ.get(api["api_key_env"], "").strip():
        raise EditorError(f"Set {api['api_key_env']}. No output was written.")
    model = os.environ.get(api["model_env"], "").strip() or config.get("model_identifier", "")
    if not model:
        raise EditorError(f"Set {api['model_env']} or config model_identifier.")
    return model


def call_model(messages: list[dict], config: dict, model: str) -> dict:
    api = config["api"]
    settings = dict(config["generation"])
    body = {"model": model, "messages": messages, **settings}
    base_url = os.environ.get(api["base_url_env"], "").strip() or api["default_base_url"]
    request = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {os.environ[api['api_key_env']].strip()}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    result = {"model": model, "settings": settings, "raw_text": None, "http_status": None, "api_error": ""}
    try:
        with urllib.request.urlopen(request, timeout=api["timeout_seconds"]) as response:
            payload = json.loads(response.read().decode("utf-8"))
            result["http_status"] = response.status
            result["raw_text"] = payload["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as exc:
        result["http_status"] = exc.code
        result["api_error"] = exc.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, KeyError, IndexError, TypeError) as exc:
        result["api_error"] = str(getattr(exc, "reason", exc))
    return result


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
    model = require_model(config)
    exploratory = bool(args.exploratory)
    measured = bool(args.evaluation_run and config.get("frozen_for_evaluation") and not exploratory)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + ("_exploratory" if exploratory else "")
    run_dir = ROOT / "data" / "outputs" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    raw_rows = []
    parsed_rows = []
    for item in selected:
        version, template = load_prompt(config, item["evidence_condition"])
        if version != item["prompt_version"]:
            raise EditorError("Prompt version changed. Review config.json before running.")
        rendered = render_prompt(template, item["original_claim"], item["evidence_passage"])
        api_result = call_model([{"role": "user", "content": rendered}], config, model)
        raw_rows.append({
            "input_id": item["input_id"],
            "example_id": item["example_id"],
            "method_code": item["method_code"],
            "evidence_condition": item["evidence_condition"],
            "prompt_version": version,
            "prompt_sha256": item["prompt_sha256"],
            "rendered_prompt": rendered,
            "model_identifier": api_result["model"],
            "generation_settings": api_result["settings"],
            "http_status": api_result["http_status"],
            "raw_text": api_result["raw_text"],
            "api_error": api_result["api_error"],
            "created_utc": utc_now(),
            "run_id": run_id,
            "exploratory": exploratory,
        })
        checked = validate_output(
            api_result["raw_text"], item["evidence_condition"], item["original_claim"], item["evidence_passage"]
        )
        if api_result["api_error"]:
            checked["parse_status"] = "api_error"
            checked["failures"] = ["api_error"]
            checked["output_action"] = None
        accepted = checked["parse_status"] == "ok"
        parsed_rows.append({
            "input_id": item["input_id"],
            "example_id": item["example_id"],
            "method_code": item["method_code"],
            "evidence_condition": item["evidence_condition"],
            "prompt_version": version,
            "prompt_sha256": item["prompt_sha256"],
            "model_identifier": api_result["model"],
            "generation_settings": api_result["settings"],
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
            "model_decision": checked["decision"],
            "model_original_claim": checked["original_claim"],
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
        "model_identifier": model,
        "generation_settings": config["generation"],
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

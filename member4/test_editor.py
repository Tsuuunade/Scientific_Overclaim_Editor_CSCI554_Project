"""Offline checks for the evidence-conditioned editor."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import editor

CLAIM = "X prevents Y."
EVIDENCE = "Passage 1:\nX was associated with lower Y."
SUPPORTED = "The Endog gene influences heart-wall thickness in rats and mice."


def structured(**overrides) -> str:
    span = "prevents"
    payload = {
        "decision": "revise",
        "claim_span": span,
        "span_start": CLAIM.index(span),
        "span_end": CLAIM.index(span) + len(span),
        "evidence_passage": "X was associated with lower Y.",
        "explanation": "The evidence reports an association.",
        "revision": "X was associated with lower Y.",
    }
    payload.update(overrides)
    return json.dumps(payload)


class EditorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = editor.load_config()
        cls.rows, cls.audit = editor.load_inputs(cls.config)

    def test_run_ids_differ_within_the_same_second(self):
        ids = [editor.new_run_id(False) for _ in range(20)]
        self.assertEqual(len(set(ids)), len(ids))
        second_length = len("20261027T185500Z")
        self.assertTrue(all(len(item.split("_")[0]) > second_length for item in ids))

    def test_report_generator_settings(self):
        self.assertEqual(self.config["model_identifier"], "Qwen/Qwen2.5-7B-Instruct")
        self.assertFalse(self.config["fine_tuned"])
        self.assertEqual(editor.generation_settings(self.config), {"do_sample": False, "max_new_tokens": 512})

    def test_supported_claim_stays_exact(self):
        result = editor.validate_structured(
            structured(
                decision="unchanged",
                claim_span="",
                span_start=None,
                span_end=None,
                revision=SUPPORTED,
                evidence_passage="influences heart-wall thickness",
                explanation="The evidence supports the causal wording.",
            ),
            SUPPORTED,
            "Endog influences heart-wall thickness in the reported animals.",
        )
        self.assertEqual(result["parse_status"], "ok")
        self.assertEqual(result["output_action"], "unchanged")
        self.assertEqual(result["span_check"], "empty_span")

    def test_invalid_edit_is_not_rewritten(self):
        weakened = "X is associated with Y."
        result = editor.validate_structured(
            structured(decision="unchanged", claim_span="", span_start=None, span_end=None, revision=weakened),
            CLAIM,
            EVIDENCE,
        )
        self.assertEqual(result["parse_status"], "schema_invalid")
        self.assertEqual(result["revised_claim"], weakened)
        self.assertIsNone(result["output_action"])

    def test_claim_offsets_must_match_the_span(self):
        result = editor.validate_structured(structured(span_start=0, span_end=1), CLAIM, EVIDENCE)
        self.assertIn("claim_offsets_mismatch", result["failures"])
        self.assertEqual(result["claim_span"], "prevents")
        self.assertEqual(result["revised_claim"], "X was associated with lower Y.")

    def test_abstention_rejects_a_guessed_sentence(self):
        guessed = "X was associated with lower Y."
        result = editor.validate_structured(
            structured(decision="abstain", claim_span="", span_start=None, span_end=None, revision=guessed),
            CLAIM,
            EVIDENCE,
        )
        self.assertIn("abstain_nonempty_revision", result["failures"])
        self.assertEqual(result["revised_claim"], guessed)

    def test_empty_abstention_and_exact_quote(self):
        accepted = editor.validate_structured(
            structured(
                decision="abstain",
                claim_span="",
                span_start=None,
                span_end=None,
                revision="",
                evidence_passage="",
                explanation="The claimed quantity is absent.",
            ),
            CLAIM,
            EVIDENCE,
        )
        self.assertEqual(accepted["output_action"], "abstain")
        rejected = editor.validate_structured(
            structured(evidence_passage="X was linked to lower Y."), CLAIM, EVIDENCE
        )
        self.assertIn("evidence_passage_not_exact", rejected["failures"])

    def test_markdown_fence_is_left_unparsed(self):
        result = editor.validate_structured("```json\n" + structured() + "\n```", CLAIM, EVIDENCE)
        self.assertEqual(result["parse_status"], "unparseable")
        self.assertIsNone(result["revised_claim"])

    def test_baseline_whitespace_is_a_change(self):
        same = editor.validate_baseline(CLAIM, CLAIM)
        changed = editor.validate_baseline(CLAIM + " ", CLAIM)
        abstained = editor.validate_baseline("ABSTAIN", CLAIM)
        self.assertEqual(same["output_action"], "unchanged")
        self.assertEqual(changed["output_action"], "revise")
        self.assertEqual(abstained["output_action"], "abstain")
        self.assertEqual(abstained["revised_claim"], "")

    def test_c_and_d_share_a_prompt_and_exclude_labels(self):
        gold = {row["prompt_sha256"] for row in self.rows if row["evidence_condition"] == "gold"}
        automatic = {row["prompt_sha256"] for row in self.rows if row["evidence_condition"] == "automatic"}
        self.assertEqual(gold, automatic)
        structured = (editor.ROOT / self.config["structured_prompt"]).read_text(encoding="utf-8")
        baseline = (editor.ROOT / self.config["baseline_prompt"]).read_text(encoding="utf-8")
        self.assertIn("only when", baseline)
        self.assertIn("ABSTAIN", baseline)
        self.assertNotIn("claim_span", baseline)
        self.assertIn("population", structured)
        self.assertIn("claim_span", structured)
        for decision in ("revise", "unchanged", "abstain"):
            self.assertIn(decision, structured)
        corrections = []
        calibration = editor.repo_path(self.config["evidence"]["calibration_file"])
        for line in calibration.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            correction = record["annotation"]["working_correction"]
            if correction and correction != record["original_claim"]:
                corrections.append(correction)
        self.assertTrue(corrections)
        encoded = json.dumps(self.rows)
        for correction in corrections:
            self.assertNotIn(correction, structured)
            self.assertNotIn(correction, encoded)

    def test_supported_causal_control_and_gold_boundary(self):
        strong_id = self.config["supported_strong_causal_example_id"]
        present = {
            row["evidence_condition"]
            for row in self.rows
            if row["example_id"] == strong_id and row["counts_as_experiment"]
        }
        self.assertEqual(present, {"full_source", "gold", "automatic"})
        self.assertEqual(self.audit[strong_id]["expected_action"], "unchanged")
        gold_ids = {row["example_id"] for row in self.rows if row["evidence_condition"] == "gold"}
        self.assertNotIn("CAL-03", gold_ids)
        self.assertNotIn("CAL-04", gold_ids)
        practice = [row for row in self.rows if row["evidence_condition"] == "candidate_not_gold"]
        self.assertEqual([row["example_id"] for row in practice], ["CAL-03", "CAL-04"])
        self.assertTrue(all(row["method_code"] == "dev_abstention" for row in practice))

    def test_handoff_stays_out_of_the_rater_view(self):
        parsed = [
            {
                "run_id": "testrun",
                "input_id": "CAL-01__gold",
                "example_id": "CAL-01",
                "method_code": "C",
                "evidence_condition": "gold",
                "prompt_version": "structured_editor_v1",
                "model_identifier": "test-model",
                "input_original_claim": CLAIM,
                "supplied_evidence": EVIDENCE,
                "exploratory": True,
                "output_text": "X was associated with lower Y.",
                "output_action": "revise",
                "parse_status": "ok",
                "validation_failures": [],
                "quote_check": "exact_match",
                "model_decision": "overclaim",
                "model_explanation": "The evidence reports an association.",
                "model_revised_claim": "X was associated with lower Y.",
            },
            {
                "run_id": "testrun",
                "input_id": "CAL-06__gold",
                "example_id": "CAL-06",
                "method_code": "C",
                "evidence_condition": "gold",
                "prompt_version": "structured_editor_v1",
                "model_identifier": "test-model",
                "input_original_claim": SUPPORTED,
                "supplied_evidence": EVIDENCE,
                "exploratory": True,
                "output_text": "",
                "output_action": "",
                "parse_status": "schema_invalid",
                "validation_failures": ["unchanged_text_changed"],
                "quote_check": "exact_match",
                "model_decision": "supported",
                "model_explanation": "Changed anyway.",
                "model_revised_claim": "The gene is associated with thickness.",
            },
        ]
        with tempfile.TemporaryDirectory(dir=editor.ROOT) as tmp:
            run_dir = Path(tmp)
            (run_dir / "parsed.jsonl").write_text(
                "".join(json.dumps(row) + "\n" for row in parsed), encoding="utf-8"
            )
            paths = editor.export_run(run_dir, self.config)
            rater = paths["rater"].read_text(encoding="utf-8")
            self.assertEqual(paths["internal"].name, "member5_handoff.csv")
            self.assertIn("M-42", rater)
            self.assertNotIn("gold", rater)
            self.assertNotIn("CAL-06", rater)
            self.assertIn("unchanged_text_changed", paths["failures"].read_text(encoding="utf-8"))
            key = json.loads(paths["key"].read_text(encoding="utf-8"))
            self.assertEqual(key["output_map"][0]["evidence_condition"], "gold")

    def test_export_refuses_member5_folder(self):
        with self.assertRaises(editor.EditorError):
            editor.export_run(editor.REPO / "evaluation")


if __name__ == "__main__":
    unittest.main()

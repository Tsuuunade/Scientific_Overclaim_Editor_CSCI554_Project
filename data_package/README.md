# Scientific Overclaim Editor Data Package

Version 3.0 | October 23 2026

This package contains the original datasets and the prepared examples used to develop and evaluate the Scientific Overclaim Editor.

## Layout

~~~text
data_package/
├── README.md
├── manifest.json
├── raw/
│   ├── paired_dataset/
│   └── auxiliary_strength/
├── prepared/
│   ├── calibration_examples.jsonl
│   ├── pilot_candidates.jsonl
│   ├── train_original_labels.jsonl
│   └── abstracts/
└── docs/
    ├── annotation_guide.md
    └── data_dictionary.md
~~~

## Original data

All original raw files retain their complete contents, including every row, original label and empty upstream file. Their hashes and row counts are recorded in manifest.json.

| Collection | File | Records |
|---|---|---:|
| Training claim-source pairs | raw/paired_dataset/data/insciout_train.jsonl | 100 |
| Reserved test claim-source pairs | raw/paired_dataset/data/insciout_test.jsonl | 563 |
| Abstract sentences labeled for claim strength | raw/auxiliary_strength/annotated_pubmed.csv | 3,061 |
| Press-release sentences labeled for claim strength | raw/auxiliary_strength/annotated_eureka.csv | 2,076 |

The paired collection contains 144 exaggerates, 406 same and 113 downplays labels across its 663 records. Each record pairs a press-release claim with an aligned abstract excerpt.

The paired dataset folder also retains the authors' supporting data: 94,920 unlabeled sentences and their aligned identifiers, 1,138 training and 355 development sentences for conclusion detection, and alternate PET data formats. These records remain available in their original subfolders.

## Prepared data

- **calibration_examples.jsonl:** eight training examples with complete abstracts, publication identifiers, evidence passages, working decisions, expected corrections and rationales. Each example includes its annotation and associated review records in one place.
- **pilot_candidates.jsonl:** all 44 selected training candidates, with original labels, selection details, source availability and proposed splits.
- **train_original_labels.jsonl:** all 100 training pairs with original labels, row numbers and stable source-record keys.
- **abstracts/:** eight readable abstracts, eight original provider responses and metadata.jsonl with the eight source records.

The eight calibration examples are included in the 44 candidates and the 100 training pairs. All eight are development examples. Their working decisions are three overclaims, three supported claims and two insufficient-evidence cases.

## How to use the package

Use the raw paired files for the original exaggeration-detection task. Use the prepared calibration file to inspect evidence and expected editing behavior. The auxiliary files support sentence-level claim-strength classification.

Read [annotation_guide.md](docs/annotation_guide.md) for the labeling and scoring rules and [data_dictionary.md](docs/data_dictionary.md) for column definitions and the pilot plan.

Load the eight prepared examples from the repository root:

~~~python
import json
from pathlib import Path

path = Path("data_package/prepared/calibration_examples.jsonl")
examples = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
print(examples[0]["original_claim"])
print(examples[0]["annotation"]["working_label"])
~~~

Use the claim and supplied evidence as model inputs. Labels, reference corrections and review records are reference outputs for development and evaluation.

## Data integrity

manifest.json records the source versions, original raw-file hashes and row counts, the candidate-selection settings, and hashes for the current package files.

Verify all packaged file hashes from the repository root:

~~~python
import hashlib
import json
from pathlib import Path

package = Path("data_package")
manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
for item in manifest["files"]:
    actual = hashlib.sha256((package / item["path"]).read_bytes()).hexdigest()
    assert actual == item["sha256"], item["path"]
print("All package files verified.")
~~~

JSONL files use UTF-8. CSV files retain their original encoding and headers. Character offsets are zero-based and end-exclusive.

## Sources

- [Wright and Augenstein (2021)](https://aclanthology.org/2021.emnlp-main.845/) and the [paired dataset repository](https://github.com/copenlu/scientific-exaggeration-detection).
- [Auxiliary claim-strength dataset](https://github.com/junwang4/correlation-to-causation-exaggeration).
- Abstract retrieval URLs, identifiers and recorded article license information are in prepared/abstracts/metadata.jsonl.

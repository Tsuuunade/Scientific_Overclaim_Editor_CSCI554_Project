# development_v1 results

development feasibility; all eight papers previously exposed.

Counts: 1 causal overclaim; 2 clean supported controls; 1 source-insufficient case; 2 scope-only cases; 2 unresolved/flagged cases.

| Method | Valid outputs | Edits on 2 supported controls | Abstentions on 1 source-insufficient case | Mean evidence characters |
|---|---:|---:|---:|---:|
| A | 8/8 | 0/2 | 0/1 | 0.0 |
| B | 8/8 | 1/2 | 1/1 | 1861.8 |
| C | 0/8 | 0/2 | 0/1 | 1372.8 |

C-D use identical model weights, generation settings and structured prompt; supplied evidence differs. D_matched matches the number of selected sentences in D_v2, not the token count.

Valid source IDs and JSON do not establish semantic correctness. The original v1 C outputs had 0/8 strict validation passes. The revised C workflow uses schema-constrained JSON and derives offsets/citations from source text. This is an implementation change, not evidence of improved factual quality.

Human evidence review is not human output scoring. Independent human editor-output ratings are still pending. No held-out accuracy claim is made.

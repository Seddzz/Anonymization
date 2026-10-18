<p align="center">
  <img src="docs/assets/github.jpg" alt="Nemo" width="600" />
</p>

# Nemo

Anonymize English documents locally via REST API, CLI, or MCP — replace PII with stable placeholders like `[PERSON_1]` and `[IBAN_1]`, then restore when needed.

## Model limitations

The NER layer uses `dslim/bert-base-NER` and inherits its trade-offs — most notably
capitalization sensitivity (lowercase names are often missed). See
[`docs/ner-limitations.md`](docs/ner-limitations.md) for the full analysis, observed
failure cases, and the improvement roadmap.

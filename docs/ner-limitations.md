# NER Detector — Limitations & Analysis

Notes on the transformer-based detector in `src/anonymizer/detectors/ner.py`.
This documents what the model does well, where it breaks, and the trade-offs we
accepted for the first (MVP) version — plus what we deliberately defer.

---

## 1. What we use

| Item | Value |
| --- | --- |
| Model | `dslim/bert-base-NER` |
| Backbone | `bert-base-cased` (case-sensitive) |
| Fine-tuned on | CoNLL-2003 (English news wire) |
| Output labels | `PER`, `ORG`, `LOC`, `MISC` |
| Mapped to | `PERSON`, `ORGANIZATION`, `LOCATION`, `MISC` |
| Aggregation | `aggregation_strategy="simple"` (merges sub-word tokens) |
| Confidence filter | `confidence_threshold = 0.5` (default) |
| Source tag | `"ner"` on every `Entity` |

The model is wrapped behind the project-wide `Detector` protocol
(`detect(text) -> list[Entity]`), so it is interchangeable with the regex and
checksum detectors and can be replaced later without touching the API, CLI or MCP
layers.

---

## 2. Primary limitation — capitalization sensitivity

This is the single most important behaviour to understand.

**Observation.** For lowercase input:

```python
text = "marcus aurelius, and I live in New York City."
# raw pipeline (no aggregation) ->
# [
#   {"entity": "B-LOC", "word": "New",  "start": 31, "end": 34, "score": 0.9995},
#   {"entity": "I-LOC", "word": "York", "start": 35, "end": 39, "score": 0.9992},
#   {"entity": "I-LOC", "word": "City", "start": 40, "end": 44, "score": 0.9996},
# ]
```

`New York City` is found, but `marcus aurelius` is **missed entirely**.

**Why.** The backbone is `bert-base-cased`, which treats letter case as a feature.
CoNLL-2003 contains almost exclusively capitalized proper nouns, so the model
learned a strong correlation: *capitalized token → likely `B-PER`/`B-ORG`*.
Lowercase personal names are effectively out-of-distribution.

**Practical consequence.**
- Real PDFs and typed documents keep their capitalization, so in the normal
  pipeline the limitation rarely bites.
- Any upstream processing that lowercases text (normalization, scraping, some OCR
  post-processing) will silently destroy recall. **Do not case-fold text before
  detection.**

**Related quirk.** Without `aggregation_strategy`, `New York City` arrives as three
tokens (`B-LOC`, `I-LOC`, `I-LOC`). We use `"simple"` so the span is emitted once as
`New York City`, which keeps downstream redaction clean.

---

## 3. Other limitations

1. **Context window (512 tokens).** Long documents are truncated by the tokenizer.
   Documents longer than the window need sliding-window chunking with offset
   correction — **not yet implemented** (tracked as a follow-up in the detector).
2. **Domain shift.** Trained on news; weaker on legal, medical, financial and
   scientific prose where entity surface forms differ from news style.
3. **Coarse label set.** Only 4 semantic types; there is no `ADDRESS`, `DATE`,
   `MONEY`, `URL`. Those are covered structurally by the regex/checksum layers, so
   the gap is acceptable — but NER alone is not sufficient.
4. **No deterministic guarantee.** Scores are probabilistic; borderline spans can
   flip between runs/models. Regex and checksum detectors stay at `score = 1.0`.
5. **Threshold trade-off.** `0.5` balances precision/recall. Raising it cuts false
   positives but drops recall; lowering it does the reverse. Exposed as a
   constructor arg.
6. **No coreference / dedup.** The same name repeated in a document yields several
   separate `Entity` spans. Redaction is still correct; placeholder de-duplication
   is the anonymizer stage's job, not the detector's.
7. **Aggregation edge cases.** `"simple"` merges greedily — adjacent one-word
   entities of the same type can be fused, and punctuation boundaries can split a
   true span.
8. **English only.** The model is monolingual. French identifiers (SIREN/SIRET/NIR,
   IBAN) are handled by the checksum layer, not NER.
9. **Cold start / cost.** The model weights are downloaded on first use and CPU
   inference is not free; this is why models get baked into the Docker image.

---

## 4. Strengths (why it earns its place)

- Catches free-text names, organizations and locations that regex fundamentally
  cannot express.
- Emits **character offsets** (`start`/`end`) that align with the rest of the
  pipeline, so spans compose with regex/checksum results.
- High precision on capitalized, in-domain text (frequently >0.99 confidence).
- Fully pluggable behind `Detector`; swapping the model is a one-line change.

---

## 5. Why this is fine for the MVP

Nemo is a **layered** system, not a single model:

| Layer | Catches | Nature |
| --- | --- | --- |
| Checksum | IBAN, card, SIREN/SIRET/NIR | deterministic |
| Regex | email, phone, ZIP, date | deterministic |
| NER | person, organization, location | probabilistic |

The deterministic layers carry the structured PII that matters most for
compliance. NER adds semantic coverage for names in prose. Isolating it behind a
protocol means the whole service ships and is reliable **now**, while the NER layer
can be upgraded independently later without a rewrite.

---

## 6. Mitigations & roadmap

- [ ] Preserve original casing end-to-end (extraction already keeps case).
- [ ] Add sliding-window chunking + offset correction for documents > 512 tokens.
- [ ] Expose per-detector enable/disable and threshold in the detection engine.
- [ ] Quantify with the eval harness — precision / recall / F1 per label.
- [ ] Evaluate alternatives: an uncased fine-tuned NER, **GLiNER**, spaCy, Stanza.
- [ ] Optional light normalization (title-casing) + span de-duplication before
      redaction.

---

## 7. Reproduce the observation

```python
from transformers import AutoModelForTokenClassification, AutoTokenizer, pipeline

tok = AutoTokenizer.from_pretrained("dslim/bert-base-NER")
mdl = AutoModelForTokenClassification.from_pretrained("dslim/bert-base-NER")
nlp = pipeline("ner", model=mdl, tokenizer=tok, aggregation_strategy="simple")

print(nlp("marcus aurelius, and I live in New York City."))
# -> only "New York City" (LOCATION); "marcus aurelius" is missed.
print(nlp("Marcus Aurelius, and I live in New York City."))
# -> "Marcus Aurelius" (PERSON) + "New York City" (LOCATION).
```

---

## 8. References

- `dslim/bert-base-NER` model card (Hugging Face).
- CoNLL-2003 shared task (Tjong Kim Sang & De Meulder, 2003).

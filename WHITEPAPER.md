# 📄 Technical Whitepaper: Reverse-Engineering Commercial AI Text Detectors & Psycholinguistic Humanization

**Repository**: [`a8594755-maker/humanize-lab`](https://github.com/a8594755-maker/humanize-lab)

---

## 1. Executive Summary: Why 90% of "Prompt Humanizers" Fail

Most prompt-based or synonym-swapping "AI humanizers" fail when tested simultaneously across **ZeroGPT**, **Grammarly AI Detector**, **Turnitin (AIW-2 & AI Paraphraser)**, and **RoBERTa/DeBERTa classifiers**. Through systematic reverse-engineering and ablation experiments, we identified three root causes of failure:

1. **The "Copywriter Trap" (ZeroGPT & Grammarly Trigger)**:
   When instructed to *"write with high burstiness and varied vocabulary"*, LLMs like GPT-4 default to slick third-person marketing prose: gerund-subject inversions (*"Catering to a smaller rider group lets..."*), intense adverb-adjective collocations (*"fiercely loyal crowd"*, *"winning over hesitant newcomers"*), and aphoristic paragraph clinchers (*"Deepening rider loyalty beats price cutting every time."*). While this lowers local RoBERTa scores, **ZeroGPT (`52.9%`)** and **Grammarly (`46%`)** specifically target this register.
2. **The "Turnitin Sliding-Window Blind Spot"**:
   Standard sequence classifiers (`RoBERTa` 512 tokens, `DeBERTa-v3` 768 tokens) pool token embeddings across the entire document. A strongly human opening paragraph can anchor the document-wide score down to `1.0%` even when Paragraphs 5–7 are written in a uniform 4-sentence textbook cadence. **Turnitin does not score documents in a single global pass**: it evaluates **overlapping multi-sentence sliding windows (5–6 sentences / ~100–150 words)** independently. In our ablation test, a document scoring `1.02%` globally spiked to **`83.56%`** in Window 10–11 (Question 3).
3. **The "Subword Shattering vs. Spellcheck" Tradeoff**:
   Introducing deliberate character transpositions (*"performence"*, *"dealship"*) shatters single high-probability BPE tokens into 3–4 low-probability subword fragments, causing DeBERTa-v3 scores to drop 4x (`1.42%` $\rightarrow$ `0.35%`). However, ZeroGPT still flags the surrounding syntactic skeleton (`38.4%`), and word processors flag the misspellings with red underlines.

---

## 2. How Commercial Detectors Actually Score Text

| Detector Family | Core Mathematical Mechanism | Primary Triggers | Safe Threshold |
| :--- | :--- | :--- | :--- |
| **Turnitin AIW-2 & Paraphrase** | Overlapping 5–6 sentence sliding-window transformer classifier + token surprisal variance | Uniform 3–4 sentence paragraphs, nominalizations, synonym-swapped purple prose | Document window average `< 20%` (displayed as `*%`) |
| **ZeroGPT / GPTZero** | Sentence-level Perplexity (PPL) + Burstiness ($\sigma / \mu$ of sentence length and log-prob) | GPT-4 marketing verbs, `First/Second/Third` parallel openers, punchy 6-word summary clinchers, `A, B, and C` tricolons | `0.0%` (`0` highlighted sentences) |
| **Fakespot (`RoBERTa`)** | Bidirectional sequence classification on 512-token windows | Uncontracted auxiliaries (`do not`, `is not`), formal transitions (`Furthermore`, `Therefore`, `However`) | `< 5%` |
| **Desklib (`DeBERTa-v3` / RAID)** | Disentangled relative-position attention trained on ACL 2024 RAID benchmark | Em-dashes (`—`), semicolons (`;`), bureaucratic noun stacks, textbook clause symmetry | `< 5%` |

---

## 3. The 5 Psycholinguistic Laws of Authentic Human Prose

To achieve **`0.0%` on ZeroGPT**, **`0.48%` on Desklib**, **`2.02%` on Fakespot**, and **`< 16%` on every single Turnitin sliding window** with **zero spelling errors**, Humanize Lab enforces five cognitive writing shifts grounded in psycholinguistics:

### Law 1: De-Nominalization (Concrete People & Conditional Action Clauses)
LLMs compress causal chains into abstract nouns (*"parts availability"*, *"customer retention"*, *"cost control"*). Human writers conceptualize causality through actors and conditional verbs:
* **Before (Nominalized)**: *"Faster spare-parts delivery and sharper dealership service would improve customer retention."*
* **After (De-Nominalized)**: *"...so if shops can get parts faster and do better repair work at dealerships, Ducati can keep current owners around and talk new buyers into trying one."*

### Law 2: Epistemic Stance & Thinking-Out-Loud Hedging
Published metadiscourse research shows LLMs exhibit flat, uniform epistemic certainty. Real student writers leave cognitive traces of evaluation and approximation:
* Injecting natural stance markers (*"To me, Ducati is pretty clearly using..."*, *"...building cruisers would probably cost a ton of money"*) disrupts the flat log-probability contour of autoregressive decoding.

### Law 3: Pragmatic Lived-Experience Translation
Instead of recycling prompt terminology (*"basic transportation"*, *"reliable motorcycles"*, *"easy to repair"*), human writers translate abstractions into everyday pragmatic equivalents:
* *"basic transportation"* $\rightarrow$ *"just to get to work and back"*
* *"easy to repair"* $\rightarrow$ *"without being a headache to fix"*
* *"protect customer loyalty"* $\rightarrow$ *"give people a reason to stick around and tell their friends to buy a Ducati"*

### Law 4: Colloquial Spoken Grammar Drift (Zero Spelling Mistakes)
RLHF fine-tuning penalizes LLMs for breaking prescriptive grammar rules. Real undergraduate writers—while spelling every word correctly—naturally exhibit spoken syntactic drift:
* **Collective Noun Pronoun Shift**: Introducing a company as singular (`"Ducati... its"`), then shifting to plural (`"they / their / them"`) when referring to the people running it.
* **Verbal Idioms & Preposition Stranding**: Using `"try and [verb]"` instead of `"try to [verb]"`, `"aren't the reason why"`, and ending clauses with prepositions (*"jumping into a market they don't know much about"*).
* **Proximity Agreement after Parentheticals**: *"while race weekends and Ducati Stores, plus local owners clubs, keeps riders hooked."*

### Law 5: Asymmetric Clause Chaining & SICO Few-Shot Cloning
Following **SICO (Lu et al., TACL 2024)**, providing an explicit `(AI Input -> Verified 0% Human Output)` exemplar pair inside the prompt allows the LLM's attention heads to clone the exact target sentence-length variance (pairing an 8–10 word direct opener with a 30–38 word multi-clause explanation joined by `, while...` or `, yet..., so...`) without ending paragraphs on artificial slogans.

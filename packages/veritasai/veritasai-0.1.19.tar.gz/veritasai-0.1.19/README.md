# VeritasAI

[![PyPI - Version](https://img.shields.io/pypi/v/veritasai.svg)](https://pypi.org/project/veritasai/)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-alpha-orange.svg)](#project-status)

**Multilingual fact checker that uses provided knowledge bases to make sure that its claims are reliable.**

VeritasAI is a **fact verification** toolkit designed for multilingual settings and domains where **traceable evidence** matters (e.g., medical). It works **with your own knowledge base**—raw text is sufficient—and verifies that any claim produced by the pipeline can be traced back to a specific **line or paragraph** in that corpus.

> **Alpha notice:** the API may change. Contributions are not currently accepted; feel free to open issues.

---

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Requirements](#requirements)
- [Quickstart](#quickstart)
- [Usage & API Overview](#usage--api-overview)
  - [Core classes](#core-classes)
  - [Wrapper pipeline](#wrapper-pipeline)
- [Preparing a Knowledge Base](#preparing-a-knowledge-base)
- [Project Status](#project-status)
- [Roadmap](#roadmap)
- [Limitations](#limitations)
- [Why VeritasAI vs Alternatives](#why-veritasai-vs-alternatives)
- [Documentation & Support](#documentation--support)
- [License](#license)
- [Citation](#citation)

---

## Features

- **Multilingual**: works across languages as long as a relevant knowledge base is supplied.
- **Evidence-grounded**: every verified claim links back to a **line/paragraph** in your corpus.
- **Modular pipeline**: separate components for claim extraction, evidence retrieval, and claim verification.
- **GPU-first**: CUDA support for efficient large-model inference.
- **No telemetry**: VeritasAI does **not** collect any usage data.

> _Benchmarks and end-to-end demos are coming; see the Colab links once they are published._

## Installation

```bash
pip install veritasai
```

### Optional heavy dependencies (usually auto-installed)

- `torch`, `transformers`, `accelerate`, `bitsandbytes`, `peft`, `spacy`, `sentence-transformers`

## Requirements

- **Python**: 3.12
- **OS**: Linux, macOS, or Windows
- **Hardware**: NVIDIA GPU with CUDA

## Quickstart

> A full **Colab notebook** will be linked [here](https://colab.research.google.com/drive/1C8caA_1QsIpfWnEB19CoCgtKNinwg0dC?usp=sharing). For now, here’s a minimal illustrative example using the high-level wrapper.  
> _Note: function names below reflect the intended design; adjust if your local API differs._

```python
from veritasai import veritasai  # wrapper that runs extraction → retrieval → verification

# A very small raw-text knowledge base (list of passages or documents)
kb = [
    "Aspirin (acetylsalicylic acid) can help reduce fever and relieve minor aches.",
    "For adults, typical oral doses of ibuprofen are 200–400 mg every 4–6 hours as needed.",
    "Type 2 diabetes is characterized by insulin resistance."
]

# Initialize the pipeline (no extra config required)
vai = veritasai() 

texts = ["Aspirin reduces fever in adults."]
result = vai.extract_claims(texts,kb,top_n=1,score_limit=0.5)  # returns a structured object with claims, evidence, and verdicts

# Inspect the claims from first document
first = result[0]
print(first)
```

## Usage & API Overview

### Core classes

VeritasAI exposes three core building blocks (plus a wrapper). Typical usage wires them in sequence:

- **`claim_extractor.py`** — finds atomic claims in raw text.
- **`evidence_retriever.py`** — retrieves candidate evidence spans from the knowledge base.
- **`claim_verifier.py`** — classifies each (claim, evidence) pair (e.g., SUPPORTED/REFUTED/INSUFFICIENT).

### Wrapper pipeline

- **`veritasai`** using individual functions.
  - Example sketch:

    ```python
    from veritasai import claim_extractor,claim_verifier, evidence_retriever
	# A very small raw-text knowledge base (list of passages or documents)
	kb = [
		"Aspirin (acetylsalicylic acid) can help reduce fever and relieve minor aches.",
		"For adults, typical oral doses of ibuprofen are 200–400 mg every 4–6 hours as needed.",
		"Type 2 diabetes is characterized by insulin resistance."
	]

	# Initialize the indivual functions (no extra config required)
	ce = claim_extractor()
	cv = claim_verifier()
	er = evidence_retriever()

	text = "Aspirin reduces fever in adults."
	text_out, claims = ce.extract_claims(text,max_new_tokens = 512, temperature= 0.1, top_p= 0.80)
	hits = er.evidence_search(claims,kb,top_n=1,score_function=er.cos_sim2,score_limit=0.5)

	fact_check=[]
	for i in range(len(claims)):
		sentences=[]
		for hit in hits[i]:
			sentences.append(hit["sentence"])
		raw, parsed = cv.verify_claim(claims[i],sentences)
		fact_check.append({"claim":claims[i], "evidence":sentences, "labels":parsed})
	print(fact_check)
    ```

> **No config needed:** the defaults should work out-of-the-box; customize models/parameters as needed once those knobs are exposed.

## Preparing a Knowledge Base

VeritasAI expects **raw text** as the knowledge source. You can start simple:

```python
kb = [
  "Paragraph 1 ...",
  "Paragraph 2 ...",
  # ...
]
```


## Project Status

- **Stage**: Alpha (API subject to change)
- **CLI**: None at the moment
- **Public API**: Not finalized
- **Telemetry**: None collected

## Roadmap

- Public Colab notebooks (Quickstart, evaluation, domain-specific demos)
- Configurable models and retrieval backends
- Evaluation scripts and reproducible benchmarks
- Expanded multilingual tests and domain examples (e.g., clinical, legal)
- Optional CLI once the API stabilizes

## Limitations

- Requires a **GPU + CUDA** for practical performance.
- Quality depends heavily on your **knowledge base coverage** and cleanliness.
- The verifier may be conservative without sufficient domain evidence.

## Why VeritasAI vs Alternatives

- **Evidence requirement by design**: the pipeline prioritizes **traceability** to your own corpus.
- **Modular**: you can inspect or replace any stage (extraction / retrieval / verification) as the system evolves.
- **Multilingual**: leverages modern multilingual embeddings and LMs to work across languages (subject to model availability).

> If you’re comparing with generic RAG toolkits: VeritasAI focuses specifically on **claim-level verification** with explicit evidence spans rather than general question answering.

## Documentation & Support

- **Issues**: use the repository’s Issues tab for bugs/questions.
- **Contributing**: external contributions aren’t accepted yet—please open an issue to discuss.
- **Security**: please open a private security advisory in the repo if you discover a vulnerability.

## License

MIT. See [LICENSE](LICENSE).

## Citation

If you use VeritasAI in academic work, please cite it. A BibTeX entry will be provided here.

```text
# (To be added)
```

---

<sub>README generated on 2025-10-04.</sub>
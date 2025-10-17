# aiter-metric

![PyPI](https://img.shields.io/pypi/v/aiter-metric.svg)
![Python](https://img.shields.io/badge/python-%3E%3D3.9-blue)

AITER is an evaluation metric for large language models (LLMs) focused on veracity.

It measures how factually consistent a generated answer is with respect to a reference text, inspired by the [HTER (Human Translation Error Rate)](https://aclanthology.org/2010.jec-1.5/) approach.

## Method description

For each input **request** (the user question), we consider:

* **Hypothesis**: the model’s answer to the request
* **Reference**: an ideal answer written by a human expert
* **Context**: all the useful supporting information that may help with corrections

The pipeline runs in three stages:

1. **Off-topic filtering (LLM):**
   Using the context, an LLM removes irrelevant or out-of-scope fragments from the hypothesis, producing a filtered hypothesis that only keeps content actually addressing the request.

2. **Correction (LLM):**
   Using the reference and context, an LLM produces a corrected hypothesis that minimally edits the hypothesis to make it factually consistent.

3. **Edit-distance scoring (TER):**
   We compute [**TER (Translation Edit Rate)**](https://aclanthology.org/2006.amta-papers.25/) to quantify both veracity and tendency to digress:

   * `TER(hypothesis → corrected_hypothesis)` — how much the original answer must change to be factually correct.
   * `TER(hypothesis → filtered_hypothesis)` — how much unrelated content had to be removed.
   * `TER(filtered_hypothesis → corrected_hypothesis)` — how much of the relevant content is factually correct.

Lower TER means fewer edits are needed.


## Installation

Install from PyPI:

```bash
pip install aiter-metric
```

Or from source:

```bash
git clone https://github.com/dieuantoine/aiter-metric.git
cd aiter-metric
pip install -e .
```

## Setup

This package requires access to LLM APIs from Mistral and Gemini.
Before using the metric, you must set up your API keys so that the package can query these models.

You can export your keys as environment variables (recommended):
```bash
export MISTRAL_API_KEY="your_mistral_api_key"
export GEMINI_API_KEY="your_gemini_api_key"
```

Alternatively, you can use a `.env` file or pass the key when initializing the metric.

## Quick Start

This package exposes a single entry point:

```python
from aiter import Scorer
```

<details> <summary> Inputs and Outputs</summary>

### Dataframe

`Scorer` expects a **pandas DataFrame** with the following columns:

* `request_id` — unique identifier of the example
* `request` — the user question / prompt given to the conversational agent
* `reference` — the ideal human-written answer
* `context` — additional information to support correction (can be empty if none)
* `hypothesis` — the model’s answer to evaluate

### Version/config dictionary

You must also pass a `version` dictionary to select the method and language:

* `CODE_VERSION`: `"1"`, `"2"`, or `"3"` (**recommended: `"3"`**)
* `LANG`: language of your data (`"en"`, `"fr"`)
* `REFORMULATION_MODEL`: the **Gemini** or **Mistral** model name to use for filtering/correction
  (e.g., `"gemini-2.5-pro"` or `"mistral-medium-latest"`)

The method `get_available_models()` returns a list of all supported Gemini and Mistral model identifiers available for use in the `REFORMULATION_MODEL` parameter.

French ("fr") is available for all code versions ("1", "2", and "3"), while English ("en") is currently supported only for version 3.

### Output

After calling the methods `reformulation()` and `scoring()`, the `results` attribute returns a dictionary containing the aggregated mean scores over all evaluated examples and `df` returns a pandas DataFrame aligned with your input, enriched with additional columns that describe the different processing stages and scores:

| Column                 | Description                                                                                                                                                                                      |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `filtered_hypothesis`  | The hypothesis after removing off-topic or irrelevant content (produced by the filtering LLM).                                                                                                   |
| `corrected_hypothesis` | The minimally corrected version of the hypothesis, made factually consistent with the reference and context.                                                                                     |
| `cor_score`            | **Correction score** = TER(filtered_hypothesis → corrected_hypothesis)|
| `ot_score`             | **Off-topic score** = TER(hypothesis → filtered_hypothesis)|
| `score`                | **Global score** = TER(hypothesis → corrected_hypothesis)|

</details>

<details><summary>Example</summary>

```python
import os
import pandas as pd
from aiter import Scorer

df = pd.DataFrame([
    {
        "request_id": "001",
        "request": "Where is the Eiffel Tower located?",
        "reference": "The Eiffel Tower is located in Paris, France.",
        "context": "The Eiffel Tower is a landmark in Paris, inaugurated in 1889.",
        "hypothesis": "The Eiffel Tower is in Berlin."
    }
])

version = {
    "CODE_VERSION": "3",
    "LANG": "en",
    "REFORMULATION_MODEL": "gemini-2.5-pro"
}

scorer = Scorer(
    df,
    version,
    # api_key="YOUR_API_KEY"  # if not env vars
)

scorer.reformulation()
scorer.scoring()

print(scorer.head())
```

</details>

## Repository Structure

```
aiter/
├── config/         # Configuration files and default settings for the APIs
├── llm_api/        # Wrappers and utilities to interact with external LLM APIs
├── metric/         # Core implementation of the metric
├── utils/          # Utils functions
└── prompts/        # Prompt templates
```


## License

Distributed under the MIT license.
See [LICENSE](LICENSE) for more details.

## Authors

[Antoine Dieu](mailto:dieu.antoine92@gmail.com) @[ALT-EDIC](https://www.alt-edic.eu/)

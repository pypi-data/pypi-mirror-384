![](./assets/img.png)

# Citention

This package enables generating LLM responses with citations from generation ("[4] [6]"), attention scores and retriever scores, and is published alongside the paper [Citation Failure: Definition, Analysis and Efficient Mitigation](TODO add link) (Buchmann et al., 2025). The code builds on [AT2](https://github.com/MadryLab/AT2/tree/main) (Cohen-Wang et al., 2025) and [Huggingface Transformers](https://huggingface.co/). 

---

Contact: [Jan Buchmann](mailto:jan.buchmann@tu-darmstadt.de)

[UKP Lab](https://www.ukp.tu-darmstadt.de/) | [TU Darmstadt](https://www.tu-darmstadt.de/)

## Installation

```bash
pip install citention
```

**PermissionError from NLTK**: If you get a `PermissionError` from NLTK, set the `NLTK_DATA` environment variable to a writable directory.

## Repository Structure

```bash
├── assets/
│   └── test_instance.json # Example input for testing
├── src/
│   └── citention/
│       ├── citation_scorers/ # Classes for obtaining citation scores from generation, attention or retrieval
│       ├── model/
│       │   ├── attention_attributor.py # Computes attention scores to source documents
│       │   ├── citention_model.py # Contains central CitentionModel class
│       │   ├── score_combinator.py # Implements score combination
│       │   ├── score_estimator.py # Obtains raw attention scores and weighs them
│       │   └── task.py # Handles generation
│       ├── retrievers/ # Classes for obtaining retrieval scores
│       ├── trainers/ # Trainer classes 
│       └── util/ # Utility functions and response processing
└── tests/ # Basic tests

```

## Usage

### Generation and Citation

The main functionality of this package is provided in the [CitentionModel](src/citention/model/citention_model.py) class. It enables generating text with citations, where the citations can be obtained from generation, attention, retrieval and their combination. 

The code below shows how to initialize a model, create a small prompt and get a response and citations from generation and attention. For more usage examples see the [main repo](https://github.com/UKPLab/arxiv2025-citation-failure) of our paper.

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

from citention.model.citention_model import CitentionModel

# Load base LLM and tokenizer
llm_hf_id = 'Qwen/Qwen3-1.7B'
llm = AutoModelForCausalLM.from_pretrained(llm_hf_id)
tokenizer = AutoTokenizer.from_pretrained(llm_hf_id)

# Define citation methods
# Currently available methods: "generation", "attention", "bm25", "sbert_dual"
citation_scorer_class_names = ['generation', 'attention']
# Define paths to pre-trained parameters (not needed for all methods)
citation_scorer_model_names_or_paths = [None, None]

# Initialize model
model = CitentionModel(
    model_name=llm_hf_id,
    llm=llm,
    tokenizer=tokenizer,
    citation_scorer_class_names=citation_scorer_class_names,
    citation_scorer_model_names_or_paths=citation_scorer_model_names_or_paths,
    calibrate_attention_scores=False,
    seed=12345,
    citation_prediction_method='top_k'
)

# Dummy source documents that can be used and cited
source_candidates = [
    'Albert Einstein: <some_content>',
    'Nicola Tesla: <some_content>',
    'Marie Curie: <some_content>'
]
# Format source candidates by adding integer identifiers in square brackets ("[i]")
formatted_source_candidates = '\n'.join([
    f'[{i}] {source_candidates[i]}'
    for i in range(len(source_candidates))
])
instruction = 'You are given a list of source documents and a question. Answer the question only using information from the source documents. Add the ids of the relevant source documents after each response sentence.'
question = 'Who came up with special relativity theory?'

# Create prompt
messages = [{
    'role': 'user',
    'content': f'{instruction}\n{source_candidates}\n{question}'
}]
prompt = tokenizer.apply_chat_template(
    messages,
    add_generation_prompt=True
)
# Add opening and closing thinking tokens as this currently can't be handled
prompt += '<think>\n</think>'

# Get character spans of source candidates and question
# Get char spans
char_spans = {
    'source_candidates': [],
    'question': (0, 0),
}
offset = 0
for i, source_candidate in enumerate(source_candidates):
    formatted_source_candidate = f'[{i}] {source_candidate}'
    start = prompt[offset:].find(formatted_source_candidate) + offset
    id_span = (start, start + len(f'[{i}]'))
    content_span = (id_span[1] + 1, id_span[1] + 1 + len(source_candidate))
    char_spans['source_candidates'].append({
        'id': id_span,
        'content': content_span
    })
    offset += len(formatted_source_candidate)

question_start = prompt.find(question)
char_spans['question'] = (question_start, question_start + len(question))

(
    raw_generation,
    predicted_statement,
    predicted_citations,
    combined_scores,
    citation_scores
) = model.generate_and_cite(
    prompt=prompt,
    max_new_tokens=100,
    multiple_statements=True,
    char_spans=char_spans,
    include_source_candidate_ids_in_ranges=False,
    attention_query='statement',
    retriever_query='question_and_statement',
    citation_k=2
)

```

### Training

#### Training QRHEAD

The QRHEAD paper (Zhang et al., 2025) describes the selection of Query-Focused Retrieval Heads to improved attention-based reranking. We provide a simple [QRHeadTrainer class](src/citention/trainers/qr_head_trainer.py) for this purpose. See [tests/test_qr_head.py](tests/test_qr_head.py) for an example of training and passing the path of the saved attention head parameters to `CitentionModel`.

#### Training AT2

The AT2 paper (Cohen-Wang et al., 2025) describes the training of attention head parameters through context perturbation. Paremeters trained with the trainer class from the [AT2 package](https://github.com/MadryLab/AT2/tree/main) can be directly used in `CitentionModel`.

#### Training BM25 

Usage of BM25 retrieval requires pre-computation of token frequency statistics. The [BM25Trainer class](src/citention/trainers/bm25_trainer.py) fulfills this purpose. See [tests/test_bm25.py](tests/test_bm25.py) for an example of training and passing the path of the saved BM25 parameters to `CitentionModel`.

#### Training a Score Combinator

By default, the `CitentionModel` will compute a uniform average of scores from all citation scorers. To change this to a weighted average, the weights need to be optimized using the [ScoreCombinatorTrainer class](src/citention/trainers/score_combinator_trainer.py). See [tests/test_score_combinator.py](tests/test_score_combinator.py) for an example of training and passing the path of the saved score combinator parameters to `CitentionModel`.

## Citation

TODO add Citation Failure paper

## References

Cohen-Wang, B., Chuang, Y., & Madry, A. (2025). Learning to Attribute with Attention. ArXiv, abs/2504.13752.

Zhang, W., Yin, F., Yen, H., Chen, D., & Ye, X. (2025). Query-Focused Retrieval Heads Improve Long-Context Reasoning and Re-ranking. ArXiv, abs/2506.09944.

## Disclaimer

> This repository contains experimental software and is published for the sole purpose of giving additional background details on the respective publication. 
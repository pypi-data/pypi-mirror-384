from dataclasses import dataclass

@dataclass
class TrainExample:
    """
    Defines common attributes of train examples
    """
    prompt: str
    char_spans: dict
    ground_truth_citations: list[int] | list[list[int]]
    source_candidates: list[str]
    max_new_tokens: int
    multiple_statements: bool
    attention_query: str
    retriever_query: str
    include_source_candidate_ids_in_ranges: bool
    generation: str = None
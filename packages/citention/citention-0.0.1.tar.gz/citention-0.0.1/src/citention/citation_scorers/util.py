from transformers import PreTrainedModel

from .base_citation_scorer import BaseCitationScorer
from .citation_scorers import (
    GenerationCitationScorer,
    AttentionCitationScorer,
    RetrievalCitationScorer
)


def load_citation_scorer(
        citation_scorer_class_name: str,
        model_name_or_path: str | None,
        llm: PreTrainedModel,
) -> BaseCitationScorer:
    """
    Load citation scorer instance
    :param citation_scorer_class_name: Available options:
        'generation' - GenerationCitationScorer
        'attention' - AttentionCitationScorer
        'bm25' - RetrievalCitationScorer with BM25 retriever
        'sbert_dual' - RetrievalCitationScorer with SBERT dual encoder retriever
    :param model_name_or_path: Path to model or model name or None if not needed
    :param llm: LLM model instance
    :return: 
    """
    if citation_scorer_class_name == 'generation':
        citation_scorer = GenerationCitationScorer()
    elif citation_scorer_class_name == 'attention':
        citation_scorer = AttentionCitationScorer(
            score_estimator_path=model_name_or_path,
            model=llm,
        )
    elif citation_scorer_class_name in [
        'bm25',
        'sbert_dual'
    ]:
        citation_scorer = RetrievalCitationScorer(
            retriever_class_name=citation_scorer_class_name,
            model_name_or_path=model_name_or_path
        )
    else:
        raise ValueError(f'Unknown citation scorer class {citation_scorer_class_name}')

    return citation_scorer

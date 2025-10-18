
from citention.model.citention_model import CitentionModel
from util import load_llm_and_tokenizer, validate_generate_and_cite


def test_cite_sbert_dual(
        llm_hf_id: str = 'Qwen/Qwen3-1.7B',
        retriever_name: str = 'dragon'
) -> None:
    llm, tokenizer = load_llm_and_tokenizer(
        llm_hf_id
    )
    citation_scorer_class_names = [
        'sbert_dual'
    ]
    citation_scorer_model_names_or_paths = [
        retriever_name
    ]

    # Load model
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

    validate_generate_and_cite(model, tokenizer)

def test_cite_attention(
        hf_id: str = 'Qwen/Qwen3-1.7B'
) -> None:
    llm, tokenizer = load_llm_and_tokenizer(
        hf_id
    )
    citation_scorer_class_names = [
        'attention'
    ]

    # Load model
    model = CitentionModel(
        model_name=hf_id,
        llm=llm,
        tokenizer=tokenizer,
        citation_scorer_class_names=citation_scorer_class_names,
        citation_scorer_model_names_or_paths=[None],
        calibrate_attention_scores=False,
        seed=12345,
        citation_prediction_method='top_k'
    )

    validate_generate_and_cite(model, tokenizer)

def test_generation(
        hf_id: str = 'Qwen/Qwen3-1.7B'
) -> None:
    llm, tokenizer = load_llm_and_tokenizer(
        hf_id
    )
    citation_scorer_class_names = [
        'generation'
    ]

    # Load model
    model = CitentionModel(
        model_name=hf_id,
        llm=llm,
        tokenizer=tokenizer,
        citation_scorer_class_names=citation_scorer_class_names,
        citation_scorer_model_names_or_paths=[None],
        calibrate_attention_scores=False,
        seed=12345,
        citation_prediction_method='top_k'
    )

    validate_generate_and_cite(model, tokenizer)


def test_score_combination(
        hf_id: str = 'Qwen/Qwen3-1.7B',
        retriever_name: str = 'dragon'
):
    llm, tokenizer = load_llm_and_tokenizer(
        hf_id
    )
    citation_scorer_class_names = [
        'sbert_dual',
        'attention',
        'generation'
    ]
    citation_scorer_model_names_or_paths = [
        retriever_name,
        None,
        None
    ]

    # Load model
    model = CitentionModel(
        model_name=hf_id,
        llm=llm,
        tokenizer=tokenizer,
        citation_scorer_class_names=citation_scorer_class_names,
        citation_scorer_model_names_or_paths=citation_scorer_model_names_or_paths,
        calibrate_attention_scores=False,
        seed=12345,
        citation_prediction_method='top_k'
    )

    validate_generate_and_cite(model, tokenizer)

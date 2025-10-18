import os
import shutil
from pathlib import Path

from transformers import PreTrainedModel, PreTrainedTokenizer

from citention.model.citention_model import CitentionModel
from citention.trainers.score_combinator_trainer import ScoreCombinatorTrainer
from util import load_test_example, load_llm_and_tokenizer, validate_generate_and_cite


def train_score_combinator(
        out_dir_path: Path,
        llm: PreTrainedModel,
        tokenizer: PreTrainedTokenizer,
        citation_scorer_class_names: list[str],
        citation_scorer_model_names_or_paths: list[str | Path | None],
        calibrate_attention_scores: bool
):
    trainer = ScoreCombinatorTrainer(
        feature_names=citation_scorer_class_names
    )

    trainer.init_model(
        model_name='test',
        llm=llm,
        tokenizer=tokenizer,
        citation_scorer_class_names=citation_scorer_class_names,
        citation_scorer_model_names_or_paths=citation_scorer_model_names_or_paths,
        calibrate_attention_scores=calibrate_attention_scores,
        seed=12345
    )

    example = load_test_example(tokenizer)
    trainer.train(
        out_dir_path=out_dir_path,
        train_examples=[example]
    )


def test_score_combinator(
        tmp_path: Path,
        llm_hf_id: str = 'meta-llama/Llama-3.2-1B-Instruct',
) -> None:

    citation_scorer_class_names = [
        'generation',
        'attention',
        'sbert_dual'
    ]
    citation_scorer_model_names_or_paths = [
        None,
        None,
        'dragon'
    ]

    # Load llm and tokenizer
    llm, tokenizer = load_llm_and_tokenizer(
        llm_hf_id
    )

    # train score combinator
    score_combinator_save_path = tmp_path / 'score_combinator'
    os.mkdir(score_combinator_save_path)
    train_score_combinator(
        out_dir_path=score_combinator_save_path,
        llm=llm,
        tokenizer=tokenizer,
        citation_scorer_class_names=citation_scorer_class_names,
        citation_scorer_model_names_or_paths=citation_scorer_model_names_or_paths,
        calibrate_attention_scores=False
    )

    # Load model
    model = CitentionModel(
        model_name=llm_hf_id,
        llm=llm,
        tokenizer=tokenizer,
        citation_scorer_class_names=citation_scorer_class_names,
        citation_scorer_model_names_or_paths=citation_scorer_model_names_or_paths,
        calibrate_attention_scores=False,
        seed=12345,
        citation_prediction_method='top_k',
        citation_score_combinator_path=score_combinator_save_path
    )

    # Validate
    validate_generate_and_cite(model, tokenizer)
    shutil.rmtree(tmp_path, ignore_errors=True)
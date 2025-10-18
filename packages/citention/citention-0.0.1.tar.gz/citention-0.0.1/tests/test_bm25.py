import os
import shutil
from pathlib import Path

from citention.model.citention_model import CitentionModel
from citention.trainers.bm25_trainer import BM25Trainer
from util import load_test_instance, load_llm_and_tokenizer, validate_generate_and_cite


def train_bm25(
        save_path: Path
):
    # Load source candidates of example as corpus
    example = load_test_instance()
    corpus = example['source_candidates']

    # Train
    trainer = BM25Trainer()
    trainer.train(
        corpus=corpus,
        out_dir=save_path
    )


def test_bm25(
        tmp_path: Path,
        llm_hf_id: str = 'meta-llama/Llama-3.2-1B-Instruct',
) -> None:
    # Train BM25
    bm25_save_path = tmp_path / 'bm25'
    os.mkdir(bm25_save_path)
    train_bm25(bm25_save_path)

    # Load model
    llm, tokenizer = load_llm_and_tokenizer(
        llm_hf_id
    )
    citation_scorer_class_names = [
        'bm25'
    ]
    citation_scorer_model_names_or_paths = [
        bm25_save_path
    ]
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

    # Validate
    validate_generate_and_cite(model, tokenizer)

    shutil.rmtree(tmp_path, ignore_errors=True)
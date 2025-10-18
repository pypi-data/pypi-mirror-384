import os
import shutil
from pathlib import Path

from transformers import PreTrainedModel, PreTrainedTokenizer

from citention.model.citention_model import CitentionModel
from citention.trainers.qr_head_trainer import QRHEADTrainer
from util import load_test_example, load_llm_and_tokenizer, validate_generate_and_cite


def train_qr_head(
        save_path: Path,
        model: PreTrainedModel,
        tokenizer: PreTrainedTokenizer
):
    # Load source candidates of example as corpus
    example = load_test_example(tokenizer)

    trainer = QRHEADTrainer(
        model=model,
        tokenizer=tokenizer,
        calibrate_attention_scores=False,
        seed=12345
    )

    trainer.train(
        train_examples=[example],
        top_k=16,
        out_dir=save_path
    )


def test_qr_head(
        tmp_path: Path,
        llm_hf_id: str = 'Qwen/Qwen3-1.7B',
) -> None:
    # Load model and tokenizer
    llm, tokenizer = load_llm_and_tokenizer(
        llm_hf_id
    )

    # Train QR Head
    qr_head_save_path = tmp_path
    train_qr_head(
        qr_head_save_path,
        model=llm,
        tokenizer=tokenizer
    )

    citation_scorer_class_names = [
        'attention'
    ]
    citation_scorer_model_names_or_paths = [
        qr_head_save_path / 'estimators' / 'saved'
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
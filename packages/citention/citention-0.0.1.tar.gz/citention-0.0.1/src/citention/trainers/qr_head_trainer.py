import logging
from pathlib import Path

import torch
from transformers import PreTrainedModel, PreTrainedTokenizer
from tqdm import tqdm

from .util import TrainExample
from ..model.citention_model import CitentionModel
from ..model.task import AttributionTask

logger = logging.getLogger()


def get_source_scores_per_head(
        model: CitentionModel,
        train_example: TrainExample,
) -> torch.Tensor:
    """
    Get attention scores per head and source
    :param model: Instance of CitentionModel. It is assumed that the first entry
        in model.citation_scorers is a "neutral" (newly initialized)
        AttentionCitationScorer
    :param train_example: Instance of TrainExample to get attention scores for
    :return: tensor [num_targets, num_sources, num_layers * num_heads]
    """
    # Initialize task
    task = AttributionTask(
        prompt=train_example.prompt,
        char_spans=train_example.char_spans,
        model=model.model,
        tokenizer=model.tokenizer,
        max_new_tokens=train_example.max_new_tokens,
        include_source_candidate_ids_in_ranges=train_example.include_source_candidate_ids_in_ranges,
        attention_query=train_example.attention_query,
        multiple_statements=train_example.multiple_statements
    )
    # Make tensor to store attention scores in
    # Shape [num_targets, num_sources, num_layers * num_heads]
    scores_per_source = torch.zeros(
        (
            len(task.get_sub_target_token_ranges()),
            task.num_sources,
            model.citation_scorers[0].score_estimator.linear.weight.shape[1]
        ),
        device=model.model.device
    )
    # Iterate over targets (statements) and get scores for each
    for target_idx, (attribution_start, attribution_end) in enumerate(
            task.get_sub_target_token_ranges()
    ):
        if attribution_end - attribution_start < 1:
            # No attribution query, set to all zero scores
            # -> [num_sources, num_layers * num_heads]
            scores_per_source[target_idx] = torch.zeros(
                (
                    task.num_sources,
                    model.citation_scorers[0].score_estimator.linear.weight.shape[1]
                ),
                device=model.model.device
            )
            continue

        # Features: [num_target_tokens, num_tokens, num_heads*num_layers]
        features = model.citation_scorers[0].score_estimator.feature_extractor(
            task,
            attribution_start,
            attribution_end
        )

        # Sum features over document ranges
        # -> [num_target_tokens, num_sources, num_layers * num_heads]
        features_per_source = torch.zeros(
            (
                features.shape[0],
                task.num_sources,
                features.shape[2]
            ),
            device=model.model.device
        )
        for i, (s, e) in enumerate(task.source_token_ranges):
            features_per_source[:, i, :] = features[:, s: e, :].sum(dim=1)

        # Average over target tokens -> [num_sources, num_layers * num_heads]
        scores_per_source[target_idx] = features_per_source.mean(dim=0)

    return scores_per_source  # [num_sources, num_layers * num_heads]


class QRHEADTrainer:
    """
    Trains attention head parameters by getting the best attention heads for a given train dataset as described in the
    paper "Query-Focused Retrieval Heads Improve Long-Context Reasoning and Re-ranking"
    by Zhang et al, 2025.
    https://github.com/princeton-pli/QRHead
    """
    def __init__(
            self,
            model: PreTrainedModel,
            tokenizer: PreTrainedTokenizer,
            calibrate_attention_scores,
            seed: int = None
    ):
        """
        :param model: LLM for generation
        :param tokenizer: Tokenizer for model
        :param calibrate_attention_scores: Whether attention scores should be
            calibrated
        :param seed: Random seed for generation
        """
        self.model = CitentionModel(
            model_name='default',
            llm=model,
            tokenizer=tokenizer,
            citation_scorer_class_names=['attention'],
            citation_scorer_model_names_or_paths=[None],
            calibrate_attention_scores=calibrate_attention_scores,
            seed=seed,
            citation_prediction_method='top_k',
            citation_score_combinator_path=None
        )

    def train(
            self,
            train_examples: list[TrainExample],
            top_k: int,
            out_dir: Path,
    ):
        """
        Get the top_k attention heads that produce the highest scores for the ground
        truth source documents in the given train examples. Set their weight to
        1/top_k in the resulting parameters and the weights for all other
        attention heads to 0.
        :param train_examples: List of TrainExample instances to get attention
            scores for.
        :param top_k: Number of attention heads to select.
        :param out_dir: Directory to store parameters (score estimator) in.
        :return:
        """
        # Make tensor that stores scores for each attention head [num_layers * num_heads]
        accumulated_scores = torch.zeros_like(
            self.model.citation_scorers[0].score_estimator.linear.weight,
            device=self.model.model.device
        )

        # Get scores for true sources for each head and add to tensor
        for train_example in tqdm(train_examples,
            total=len(train_examples),
            desc='Calculating scores for true sources'
        ):
            if train_example.multiple_statements:
                raise NotImplementedError
            source_scores_per_head = get_source_scores_per_head(
                model=self.model,
                train_example=train_example,
            ).squeeze() # [num_sources, num_layers * num_heads]
            for idx in train_example.ground_truth_citations:
                # Get score for source idx
                source_score = source_scores_per_head[idx]
                # Add to accumulated scores
                accumulated_scores += source_score

        # Get indices of top k heads with highest scores
        logger.info('Getting top k heads')
        top_k_indices = torch.topk(accumulated_scores, top_k).indices.squeeze()

        # Overwrite linear layer of score estimator, using 1/top_k for all top_k heads
        # and 0 for all others
        logger.info('Overwriting score estimator')
        new_weights = torch.zeros_like(self.model.citation_scorers[0].score_estimator.linear.weight)
        for idx in top_k_indices:
            new_weights[0][idx] = 1 / top_k

        self.model.citation_scorers[0].score_estimator.linear.weight = torch.nn.Parameter(new_weights)

        # Save score estimator
        save_dir = out_dir / 'estimators' / 'saved'
        save_dir.mkdir(parents=True, exist_ok=True)
        self.model.citation_scorers[0].score_estimator.save(save_dir / 'score_estimator.pt')
        logger.info(f'Saved score estimator to {save_dir / "score_estimator.pt"}')

        return
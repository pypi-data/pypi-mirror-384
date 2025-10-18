from pathlib import Path
import logging

import numpy as np
import torch
from numpy._typing import ArrayLike
from transformers import PreTrainedModel, PreTrainedTokenizer
from tqdm import tqdm

from .util import TrainExample
from ..model.citention_model import CitentionModel
from ..model.score_combinator import LinearScoreCombinator

logger = logging.getLogger()


class ScoreCombinatorTrainer:
    """
    Trains score combinator and saves to disk.
    """
    def __init__(
            self,
            feature_names: list[str]
    ):
        """
        :param feature_names: Feature names for score combinator
        """
        # Initialization of model is not always needed, so we initialize the
        # attribute with None
        self.model: CitentionModel | None = None
        # Initialize new score combinator
        self.score_combinator = self.init_score_combinator(feature_names)

    def init_model(
            self,
            model_name: str,
            llm: PreTrainedModel,
            tokenizer: PreTrainedTokenizer,
            citation_scorer_class_names: list[str],
            citation_scorer_model_names_or_paths: list[str | None],
            calibrate_attention_scores: bool,
            seed: int = None
    ):
        """
        Initialize CitentionModel.
        :param model_name: Name of model (choose any)
        :param llm: LLM for generation
        :param tokenizer: Tokenizer for LLM
        :param citation_scorer_class_names: List of citation scorer class names.
            See citation_scorers.util.load_citation_scorer for all available class
            names.
        :param citation_scorer_model_names_or_paths: List of model names of save
            paths for citation scorers. Must have same length as
            citation_scorer_class_names.
        :param calibrate_attention_scores: Whether to calibrate attention scores
        :param seed:
        :return:
        """
        # Initialize citention model with "neutral" score combinator
        self.model = CitentionModel(
            model_name=model_name,
            llm=llm,
            tokenizer=tokenizer,
            citation_scorer_class_names=citation_scorer_class_names,
            citation_scorer_model_names_or_paths=citation_scorer_model_names_or_paths,
            calibrate_attention_scores=calibrate_attention_scores,
            seed=seed,
            citation_prediction_method='top_k',
            citation_score_combinator_path=None
        )

    @staticmethod
    def init_score_combinator(
            feature_names: list[str]
    ):
        """
        Initialize score combinator
        :param feature_names:
        :return: Initialized score combinator
        """
        score_combinator = LinearScoreCombinator(
            feature_names=feature_names,
            weighted=True
        )

        return score_combinator

    def get_citation_scores(
            self,
            train_examples: list[TrainExample],
    ) -> np.ndarray:
        """
        Run model on prompts and return array of citation
        scores
        :param train_examples: List of train examples to get scores for
        :return: Array of citation scores of shape [num_citers, num_sources]
        """
        assert self.model is not None, (
            'Model not initialized. Call init_model() first.'
        )

        citation_scores = []
        for example in tqdm(
                train_examples,
                desc='Getting citation scores'
        ):
            if example.multiple_statements:
                raise NotImplementedError

            _, _, _, _, citation_scores_for_prompt = self.model.generate_and_cite(
                prompt=example.prompt,
                max_new_tokens=example.max_new_tokens,
                multiple_statements=example.multiple_statements,
                char_spans=example.char_spans,
                include_source_candidate_ids_in_ranges=example.include_source_candidate_ids_in_ranges,
                attention_query=example.attention_query,
                retriever_query=example.retriever_query,
                citation_k=1,
                generation=example.generation
            )
            citation_scores.append(citation_scores_for_prompt.cpu().permute(1, 0))

        citation_scores = torch.cat(citation_scores, dim=0).numpy()

        return citation_scores

    @staticmethod
    def make_ground_truth_citations_array(
            train_examples: list[TrainExample]
    ):
        """
        Make 1-D array of ground truth citations from train examples. The
        output array has a 1 for ground truth source documents (citations) and
        0 for all others.
        :param train_examples: List of train examples
        :return: Array of shape [n_train_examples * n_source_candidates]
        """
        ground_truth_citations_array = []
        for example in train_examples:
            # Get the number of source candidates
            n_sources = len(example.source_candidates)
            # Make array of shape [n_source_candidates]
            citations_array = np.zeros(n_sources, dtype=int)
            for idx in example.ground_truth_citations:
                # Set entries to 1 for ground truth citations
                citations_array[idx] = 1
            ground_truth_citations_array.append(citations_array)
        # Concatenate arrays for individual train examples
        ground_truth_citations_array = np.concatenate(ground_truth_citations_array, axis=0)
        return ground_truth_citations_array

    def train(
            self,
            out_dir_path: Path,
            train_examples: list[TrainExample],
            citation_scores: ArrayLike = None, # [n_prompts * n_sources, n_citation_scorers]
    ):
        """
        Train score combinator and save to disk.
        If citation_scores are not given, they are computed first (requires
        initialization of model).
        :param out_dir_path:
        :param train_examples:
        :param citation_scores:
        :return:
        """
        if citation_scores is None:
            # Get citation scores by running model
            logger.info('Getting citation scores by running model on prompts...')
            citation_scores = self.get_citation_scores(
                train_examples=train_examples,
            )

        # Get array of ground truth citations
        ground_truth_citations = self.make_ground_truth_citations_array(
            train_examples
        )

        # Fit score combinator
        logger.info('Fitting score combinator')
        self.score_combinator.fit(
            citation_scores,
            ground_truth_citations
        )

        # Save
        logger.info(f'Saving score combinator to {out_dir_path}')
        self.score_combinator.save(
            out_dir_path
        )



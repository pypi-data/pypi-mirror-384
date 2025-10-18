import logging
import os
from pathlib import Path

import torch
from transformers import PreTrainedModel, PreTrainedTokenizer

from ..util.misc import get_top_k_indices
from .score_combinator import load_score_combinator
from ..citation_scorers.util import load_citation_scorer
from ..citation_scorers.base_citation_scorer import BaseCitationScorer
from .task import AttributionTask

logger = logging.getLogger(__name__)


class CitentionModel:
    """
    Generates responses to prompts and computes citation scores. Based on citation
    scores from one or multiple citation scorers (methods), citations are
    predicted.
    """
    def __init__(
            self,
            model_name: str,
            llm: PreTrainedModel,
            tokenizer: PreTrainedTokenizer,
            citation_scorer_class_names: list[str],
            citation_scorer_model_names_or_paths: list[str | Path | None],
            calibrate_attention_scores: bool,
            seed: int,
            citation_prediction_method: str,
            citation_score_combinator_path: str | Path = None
    ):
        """
        :param model_name: Name of the model. Can be any string.
        :param llm: HF model for response generation and computing attention
            scores.
        :param tokenizer: Tokenizer corresponding to llm.
        :param citation_scorer_class_names: List of citation scorer class names.
            See citation_scorers.util.load_citation_scorer for a full list of
            available classes.
        :param citation_scorer_model_names_or_paths: Name of citation scorer model
            (e.g. "dragon") or path to saved model from training. Has to have the
            same length as citation_scorer_class_names,
        :param calibrate_attention_scores: Whether attention scores shoud be
            calibrated.
        :param seed: Seed for generation.
        :param citation_prediction_method: How to predict citations from scores.
            Available options:
            - "generation": Predict citations as those that were generated
                explicitly in the response. Only works if at least one citation
                scorer is of class "generation".
            - "threshold": Binarize scores using a threshold. This only works well
                if a score combinator was loaded, as the default threshold is
                probably useless.
            - "top_k": Select the top k citations per statement. Requires that
                citation_k is passed to generate_and_cite().
        :param citation_score_combinator_path: Path to saved score combinator.
        """
        self.model_name = model_name
        self.model = llm
        self.tokenizer = tokenizer
        self.seed=seed
        self.calibrate_attention_scores = calibrate_attention_scores
        self.citation_prediction_method = citation_prediction_method

        if self.citation_prediction_method == 'generation':
            assert citation_scorer_class_names == ['generation'], (
                'If citation_prediction_method is "generation", '
                'citation_scorer_class_names has to be ["generation"].'
            )

        # Put LLM on GPU if possible.
        if torch.cuda.is_available():
            self.model = self.model.to('cuda')

        # Set pad token as eos token
        self.tokenizer.add_special_tokens({'pad_token': self.tokenizer.eos_token})

        # Initialize citation scorers
        self.citation_scorers: list[BaseCitationScorer] = []
        for (
            citation_scorer_class_name,
            model_name_or_path
        ) in zip(
            citation_scorer_class_names,
            citation_scorer_model_names_or_paths
        ):
            citation_scorer = load_citation_scorer(
                citation_scorer_class_name=citation_scorer_class_name,
                model_name_or_path=model_name_or_path,
                llm=self.model,
            )
            self.citation_scorers.append(citation_scorer)

        # Load score combinator
        self.score_combinator = load_score_combinator(
            score_combinator_path=citation_score_combinator_path,
            feature_names=citation_scorer_class_names
        )

    def generate_and_cite(
            self,
            prompt: str,
            max_new_tokens: int,
            multiple_statements: bool,
            char_spans: dict,
            include_source_candidate_ids_in_ranges: bool,
            attention_query: str = 'statement',
            retriever_query: str = 'question_and_statement',
            citation_k: int = 2,
            generation: str = None
    ) -> tuple[
        str,
        str | list[str],
        list[int] | list[list[int]],
        torch.Tensor, # [num_targets, num_sources] | [num_sources]
        torch.Tensor # [num_citers, num_targets, num_sources] | [num_citers, num_sources]
    ]:
        """
        Generate response to prompt, compute citation scores and predict
        citations.
        :param prompt: Input prompt
        :param max_new_tokens: Maximum number of tokens to be generated.
        :param multiple_statements: Whether response is expected to consist of one
            or multiple statements. If True, response will be split. The shapes
            of some outputs depend on this.
        :param char_spans: Character spans of relevant prompt elements. Required
            Required shape:
            {
                "source_candidates": [
                    {
                        "id": (20, 23), # Span of id (e.g. "[0]")
                        "content": (24, 103) # Span of content
                    },
                    {...},
                    ...
                ]
                "question": (120, 151) # Span of question (only required for retriever)
            }
        :param include_source_candidate_ids_in_ranges: Whether ids of source
            candidates should be included when computing attention scores.
        :param attention_query: What to use as query / target when computing attention
            scores. Available options:
            - "statement": Only the response statement
            - "question": Only the question (requires "question" key in char_spans)
            - "statement_and_citations": The response statement with generated citations.
            - "citations": Only the generated citations for a given response statement.
        :param retriever_query: What to use as query for retrieval citation scorers.
            Available options:
            - "question": Only the question (requires "question" key in char_spans)
            - "statement": Only the response statement
            - "question_and_statement": The question and the response statement
        :param citation_k: If citation_prediction_method was set to "top_k" during
            initialization., how many citations to predict per statement.
        :param generation: Pre-computed generated text. If passed, no generation
            will be performed.
        :return: A tuple of (
            raw_generation: str, # Raw generated text
            predicted_statement: str | list[str], # Predicted response statement(s) without citations
            predicted_citations: list[int] | list[list[int]], # Predicted citations
            combined_scores: torch.Tensor, # [num_targets, num_sources] | [num_sources]
            citation_scores: torch.Tensor # [num_citers, num_targets, num_sources] | [num_citers, num_sources]
        )
        """
        cache = {}
        if generation is not None:
            # Add text to cache
            cache = {'text': prompt + generation}

        # Initialize AttributionTask
        task = AttributionTask(
            prompt=prompt,
            char_spans=char_spans,
            model=self.model,
            tokenizer=self.tokenizer,
            max_new_tokens=max_new_tokens,
            include_source_candidate_ids_in_ranges=include_source_candidate_ids_in_ranges,
            attention_query=attention_query,
            multiple_statements=multiple_statements,
            cache=cache
        )

        # Get generated text
        raw_generation = task.generation

        # Initialize tensor of citation scorer
        # [num_citers, num_targets, num_sources]
        citation_scores = torch.zeros(
            size=(
                len(self.citation_scorers),
                len(task.get_sub_target_token_ranges()),
                len(task.source_token_ranges)
            ),
            dtype=torch.float
        )
        # Get citation scores from individual scorers
        for i, citer in enumerate(self.citation_scorers):
            citation_scores[i] = citer.get_citation_scores(
                task=task,
                calibrate_attention_scores=self.calibrate_attention_scores,
                retriever_query=retriever_query
            )

        if self.score_combinator:
            # Combine scores per target and write to tensor [num_targets, num_sources]
            combined_scores = torch.zeros(
                size=(
                    citation_scores.shape[1],
                    citation_scores.shape[2]
                ),
                dtype=torch.float
            )

            # Iterate over scores viewed as [num_targets, num_sources, num_citers]
            for i, citation_scores_for_target in enumerate(citation_scores.permute(1, 2, 0)):
                # Score combinator expects [n_observations, n_features]
                # Returns np array [n_observations, 1]
                combined_scores_for_target = self.score_combinator.predict_proba(
                    citation_scores_for_target
                )
                # Convert np array to tensor
                combined_scores_for_target = torch.from_numpy(combined_scores_for_target)
                combined_scores[i] = combined_scores_for_target.squeeze()

        else:
            # Remove num_citers dimension
            combined_scores = citation_scores[0,:,:]

        # Predict citations from scores
        predicted_citations = self.predict_citations(
            scores=combined_scores,
            citation_k=citation_k
        )

        # Get predicted response statements
        predicted_statement = [
            task.text[statement_start: statement_end]
            for statement_start, statement_end in task.char_spans['statement']
        ]
        if not multiple_statements:
            # Remove num_targets dimension
            predicted_statement = predicted_statement[0]
            combined_scores = combined_scores[0]
            predicted_citations = predicted_citations[0]
            citation_scores = citation_scores[:, 0, :]

        return (
            raw_generation,
            predicted_statement,
            predicted_citations,
            combined_scores,
            citation_scores
        )

    def predict_citations(
            self,
            scores: torch.Tensor,
            citation_k: int = None
    ) -> list[list[int]]:
        """
        Predict citations from scores and return one list per generated statement.
        :param scores: Tensor of citation scores of shape [num_targets, num_sources]
        :param citation_k: If citation_prediction_method was set to "top_k" during
            initialization, how many citations to predict per statement.
        :return: List of shape [num_targets, num_citations] where each entry is the index
            of a predicted citation.
        """
        if self.citation_prediction_method == 'generation':
            # Predict citations as those that were generated (i.e. that have a
            # nonzero score).
            predicted_citations = [
                [i for i, score in enumerate(score_list) if score > 0]
                for score_list in scores.tolist()
            ]
        elif self.citation_prediction_method == 'threshold':
            binary_predictions = torch.zeros_like(
                scores,
                dtype=torch.bool
            )
            # Binarize scores
            for i, scores_for_target in enumerate(scores):
                binary_predictions_for_target = self.score_combinator.scores_to_binary(
                    scores_for_target
                )
                # Convert to tensor and set values in binary_predictions
                binary_predictions[i] = torch.from_numpy(binary_predictions_for_target)

            # Make list of shape [num_targets, num_citations] where binary_predictions
            # is 1
            predicted_citations = [
                [i for i, score in enumerate(binary_prediction) if score == 1]
                for binary_prediction in binary_predictions
            ]

        elif self.citation_prediction_method == 'top_k':
            # Select top k scores for each target
            scores = scores.tolist()
            predicted_citations = get_top_k_indices(
                scores,
                citation_k
            )

        else:
            raise ValueError(
                f'Invalid citation prediction method: {self.citation_prediction_method}. '
                f'Valid methods are: threshold, top_k'
            )

        return predicted_citations

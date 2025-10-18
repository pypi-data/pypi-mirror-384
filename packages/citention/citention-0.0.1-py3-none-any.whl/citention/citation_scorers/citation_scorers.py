from pathlib import Path
import logging

import torch
from transformers import PreTrainedModel

from at2.attribution import AttentionFeatureExtractor

from .base_citation_scorer import BaseCitationScorer
from ..model.attention_attributor import AttentionAttributor
from ..model.score_estimator import AttentionScoreEstimator
from ..model.task import AttributionTask
from ..retrievers.util import load_retriever

logger = logging.getLogger()


class GenerationCitationScorer(BaseCitationScorer):
    """
    Gets citation scores from generation probabilities.
    """
    def get_citation_scores(
            self,
            task: AttributionTask,
            **kwargs
    ) -> torch.Tensor:
        """
        Get citation scores from generation probabilities of individual citations.
        Citation scores for documents that were not cited are set to 0.
        :param task: Instance of AttributionTask class.
        :param kwargs:
        :return: A tensor of citation scores. Shape: [num_targets, num_sources]
        """
        def get_sequence_probability(
                char_start: int,
                char_end: int
        ) -> float:
            """
            Get mean sequence probability of character span
            :return:
            """
            if None in (char_start, char_end):
                return -1.0
            token_range = task.char_range_to_token_range(
                char_start, char_end
            )
            return task.get_mean_sequence_probability(
                *token_range
            )

        # Initialize tensor of citation scores of shape [num_statements, num_sources]
        citation_scores = torch.zeros(
            (
                len(task.get_sub_target_token_ranges()),
                len(task.source_token_ranges)
            ),
            dtype=torch.float
        )

        # Obtain sequence probabilities of generated citations
        # Iterate over response statements and corresponding generated citations
        for statement_idx, (char_span_list, citation_int_list) in enumerate(zip(
            task.char_spans['individual_citations'],
            task.generated_citations
        )):
            # Iterate over character spans of generated citations
            for (start, end), citation_int in zip(
                    char_span_list, citation_int_list
            ):
                if citation_int not in range(0, len(task.source_token_ranges)):
                    # Cited source does not exist
                    continue
                # Get sequence probability of citation and write to citation scores
                seq_prob = get_sequence_probability(start, end)
                citation_scores[statement_idx][citation_int] = seq_prob

        return citation_scores


class AttentionCitationScorer(BaseCitationScorer):
    """
    Gets citation scores from attention to source documents.
    """
    def __init__(
            self,
            score_estimator_path: Path | str = None,
            model: PreTrainedModel = None,
    ):
        """
        :param score_estimator_path: Path to saved score estimator (i.e. attention
        head parameters). Can be obtained from training according to QRHEAD or AT2.
        :param model: If no score estimator path is provided, a new score estimator
            is initialized for the provided model.
        """

        if score_estimator_path is not None:
            # Load score estimator
            logger.info(f'Loading score estimator from path: {score_estimator_path}')
            self.score_estimator = AttentionScoreEstimator.load(
                path=score_estimator_path
            ).to(model.device)
        else:
            # Initialize new score estimator
            logger.info('Initializing new score estimator')
            feature_extractor = AttentionFeatureExtractor.from_model(
                model
            )
            self.score_estimator = AttentionScoreEstimator(
                feature_extractor=feature_extractor,
            ).to(model.device)

    def get_citation_scores(
            self,
            task: AttributionTask,
            calibrate_attention_scores: bool = False,
            **kwargs
    ) -> torch.Tensor:
        """
        Get citation scores from attention scores to source documents.
        :param task: Instance of AttributionTask class.
        :param calibrate_attention_scores: Whether to calibrate attention scores.
            Calibration is performed as described in [In-Context Reranking](https://github.com/OSU-NLP-Group/In-Context-Reranking/tree/main).
            (Sun et al., ICLR 2025).
        :param kwargs:
        :return:
        """
        null_query_token_scores = None
        if calibrate_attention_scores:
            # Compute attention scores for null query
            null_query_token_scores = self._get_null_query_token_scores(task)

        # Initialize attributor and get scores
        attributor = AttentionAttributor(
            task=task,
            score_estimator=self.score_estimator,
            calibrate_scores=calibrate_attention_scores,
            null_query_token_scores=null_query_token_scores
        )
        scores = attributor.scores

        return scores

    def _get_null_query_token_scores(
            self,
            task: AttributionTask
    ):
        """
        Compute null query attention scores for calibration
        :param task: Attribution task
        :return:
        """
        null_query = 'N/A'
        # Replace original query with null query
        original_query_start = task.char_spans[task.attention_query][0][0]
        text_with_null_query = task.text[:original_query_start] + null_query

        # Update char spans
        char_spans = task.char_spans.copy()
        char_spans['statement'] = [(
            original_query_start,
            original_query_start + len(null_query)
        )]

        # Initialize task object with pre-set 'text' attribute  in cache
        task_with_null_query = AttributionTask(
            prompt=task.prompt,
            char_spans=char_spans,
            model=task.model,
            tokenizer=task.tokenizer,
            max_new_tokens=task.generate_kwargs['max_new_tokens'],
            include_source_candidate_ids_in_ranges=task.include_source_candidate_ids_in_ranges,
            attention_query='statement',
            multiple_statements=False,
            cache={'text': text_with_null_query}
        )

        # Initialize Attributor
        attributor = AttentionAttributor(
            task=task_with_null_query,
            score_estimator=self.score_estimator,
            calibrate_scores=False
        )

        # Obtain per token scores
        null_query_token_scores = attributor.token_scores[0]
        # Shorten to end before null query
        # Target token ranges might not have the same beginning because of
        # tokenization of space before query / null query
        # We find the target token range that begins earlier
        query_start = min(
            task.get_sub_target_token_ranges()[0][0],
            task_with_null_query.get_sub_target_token_ranges()[0][0]
        )
        null_query_token_scores = null_query_token_scores[
            : query_start
        ]

        del attributor
        del task

        return null_query_token_scores


class RetrievalCitationScorer(BaseCitationScorer):
    """
    Gets citation scores from a retrieval model.
    """
    def __init__(
            self,
            retriever_class_name: str,
            model_name_or_path: Path | str
    ):
        """
        :param retriever_class_name: Class name of the retriever to use. Available
            options: "bm25", "sbert_dual".
        :param model_name_or_path: Model name or path for the retriever.

        """
        self.retriever = load_retriever(
            retriever_class_name=retriever_class_name,
            model_name_or_path=model_name_or_path
        )

    def get_citation_scores(
            self,
            task: AttributionTask,
            retriever_query: str = None,
            **kwargs
    ) -> torch.Tensor:
        """
        Get citation scores from a retrieval model.
        :param task:
        :param retriever_query: Query to use for retrieval. Options:
            - 'question': Use the question as query.
            - 'statement': Use the generated statements as queries.
            - 'question_and_statement': Use the question and the generated statements
        :param kwargs:
        :return:
        """
        # Get generated statements as strings by indexing task.text
        statement_char_spans = task.char_spans['statement']
        statements = [
            task.text[start: end]
            for start, end in statement_char_spans
        ]
        # Get question
        question = ''
        if retriever_query in [
            'question',
            'question_and_statement'
        ]:
            question_start, question_end = task.char_spans['question']
            question = task.text[
                question_start: question_end
            ]

        # Build queries
        if retriever_query == 'statement':
            queries = statements
        elif retriever_query == 'question':
            queries = [question for _ in statements]
        elif retriever_query == 'question_and_statement':
            queries = [question + ' ' + statement for statement in statements]
        else:
            raise ValueError(
                f'Invalid retriever query: {retriever_query}. '
                f'Valid queries are: question, statement, question_and_statement'
            )

        # Get source documents by indexing task.text
        documents = [
            task.text[start: end]
            for start, end in task.document_ranges
        ]

        # Get retriever scores
        citation_scores = torch.zeros(
            (
                len(task.get_sub_target_token_ranges()),
                len(task.source_token_ranges)
            ),
            dtype=torch.float
        )
        for i, query in enumerate(queries):
            citation_scores[i] = (
                self.retriever.score(
                    query=query,
                    docs=documents
                )
            )

        return citation_scores

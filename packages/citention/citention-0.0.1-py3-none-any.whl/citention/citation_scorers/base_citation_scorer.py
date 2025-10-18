import torch

from ..model.task import AttributionTask


class BaseCitationScorer:

    def get_citation_scores(
            self,
            task: AttributionTask,
            calibrate_attention_scores: bool = False,
            retriever_query: str = None
    ) -> torch.Tensor:
        """

        :param task: Instance of AttributionTask class
        :param null_query_token_scores: Whether attention scores should be
            calibrated.
        :param retriever_query: The parts of the prompt and generation to be
            used as retriever query. Available options: "question", "statement",
            "question_and_statement".
        :return: A tensor of citation scores. Shape: [num_targets, num_sources]
        """
        raise NotImplementedError

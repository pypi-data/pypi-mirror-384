from typing import Any

import torch
from at2.attribution import ScoreEstimationAttributor

from .score_estimator import AttentionScoreEstimator
from .task import AttributionTask


class AttentionAttributor(ScoreEstimationAttributor):
    """
    Computes attention scores.
    """
    def __init__(
            self,
            task: AttributionTask,
            score_estimator: AttentionScoreEstimator,
            calibrate_scores: bool,
            null_query_token_scores: torch.Tensor = None, # [num_tokens]
            cache: dict[str, Any] = None
    ):
        """
        :param task: Instance of AttributionTask.
        :param score_estimator: Instance of ScoreEstimator.
        :param calibrate_scores: Whether to calibrate attention scores.
        :param null_query_token_scores: Attention scores for null query for score
            calibration.
        :param cache: Pre-filled cache dict
        """
        super().__init__(
            task=task,
            score_estimator=score_estimator,
            cache=cache
        )

        self.calibrate_scores = calibrate_scores
        self.null_query_token_scores = null_query_token_scores

    def _get_token_scores(self):
        """
        Get per-token attention scores from targets to sources
        :return: Tensor of shape [num_targets, num_tokens]
        """
        all_scores = []
        with torch.no_grad():
            for token_range in self.task.get_sub_target_token_ranges():
                token_scores = self.score_estimator.get_scores(
                    self.task, *token_range
                )  # [num_tokens]
                all_scores.append(token_scores)
        all_scores = torch.stack(all_scores, dim=0)  # [num_targets, num_tokens]
        return all_scores

    @property
    def token_scores(self):
        if self._cache.get('token_scores') is None:
            self._cache['token_scores'] = self._get_token_scores()
        return self._cache['token_scores']

    def _get_scores(self):
        """
        Get per-source attention scores from targets to sources
        :return:
        """
        # Get token scores
        scores = self.token_scores # [num_targets, num_tokens]

        # Apply calibration if necessary
        if self.calibrate_scores:
            scores = self._calibrate_token_scores(scores)

        # Sum per document to get shape [num_targets, num_documents]
        scores = [scores[:, s:e].sum(dim=-1) for s, e in self.task.source_token_ranges]
        scores = torch.stack(scores, dim=1)

        return scores.nan_to_num(nan=-1.0).cpu().type(torch.float32)

    def _calibrate_token_scores(
            self,
            token_scores: torch.Tensor # shape [num_targets, num_tokens]
    ):
        """
        Calibration as implemented in https://github.com/princeton-pli/QRHead/blob/a08c24f6ff4a594d94e8deb1192c2bea7f098e5f/src/qrretriever/attn_retriever.py
        The summed attention scores from a null query are subtracted from
        the attention scores of the actual query.
        Then, all resulting scores under a certain threshold are removed.
        :param token_scores:
        :return:
        """
        # [num_targets, num_tokens]
        calibrated_token_scores = token_scores

        calibrated_token_scores[:,:self.null_query_token_scores.shape[0]] = (
            calibrated_token_scores[:,:self.null_query_token_scores.shape[0]]
            - self.null_query_token_scores
        )

        # Remove abnormal scores
        # https://github.com/princeton-pli/QRHead/blob/a08c24f6ff4a594d94e8deb1192c2bea7f098e5f/src/qrretriever/attn_retriever.py#L229
        for start, end in self.task.source_token_ranges:
            # Get token scores for current document [num_targets, num_tokens_in_doc]
            curr_src_token_scores = calibrated_token_scores[:, start: end]
            # Compute threshold [num_targets]
            threshold = curr_src_token_scores.mean(dim=1) - 2 * curr_src_token_scores.std(dim=1)
            # [num_targets, 1]
            threshold = threshold.view(threshold.shape[0], 1)
            # Compute mask [num_targets, num_tokens_in_doc]
            tok_mask = (curr_src_token_scores > threshold).to(calibrated_token_scores.device)
            # Apply mask
            calibrated_token_scores[:, start: end] = (
                calibrated_token_scores[:, start: end]
                * tok_mask
            )

        return token_scores

    @property
    def scores(self) -> torch.Tensor:
        if self._cache.get('scores') is None:
            self._cache['scores'] = self._get_scores()

        return self._cache['scores']

    def _get_attribution_scores_for_token_range(self, token_start, token_end, **kwargs):
        raise NotImplementedError(
            'This function should not be used. Directly use the .scores property'
        )

    def get_attribution_scores(
        self,
        start=None,
        end=None,
        token_start=None,
        token_end=None,
        verbose=False,
        **kwargs,
    ):
        raise NotImplementedError(
            'This function should not be used. Directly use the .scores property'
        )

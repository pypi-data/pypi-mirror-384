from pathlib import Path
from typing import Optional, Union

import torch

from at2.attribution import LinearScoreEstimator, FeatureExtractor
from at2.tasks import AttributionTask


class AttentionScoreEstimator(LinearScoreEstimator):
    """
    Extracts per-head attention scores and applies linear layer
    """
    def __init__(
            self,
            feature_extractor: FeatureExtractor,
            normalize: bool = True,
            non_negative: bool = False,
            bias: bool = False,
            **kwargs
    ):
        super().__init__(
            feature_extractor=feature_extractor,
            normalize=normalize,
            non_negative=non_negative,
            bias=bias,
        )

    @classmethod
    def load(
            cls,
            path: Path,
            device: Optional[Union[str, torch.device]] = None
    ) -> "AttentionScoreEstimator":
        """
        Load a estimator from the specified path.
        :param path: Directory where the score estimator is saved.
        :param device: Device to map the model to.
        :return: The loaded AttentionScoreEstimator.
        """
        path = path / 'score_estimator.pt'
        save_dict = torch.load(path, map_location=device, weights_only=False)
        state_dict = save_dict["state_dict"]
        kwargs = save_dict["kwargs"]
        extras = save_dict["extras"]
        feature_extractor = FeatureExtractor.deserialize(save_dict["feature_extractor"])
        estimator = cls(feature_extractor, **kwargs, extras=extras)
        estimator.load_state_dict(state_dict)
        return estimator

    def forward(
            self,
            features: torch.Tensor
    ) -> torch.Tensor:
        """
        Forward pass through the estimator. Applies linear layer and averages
        over target tokens.
        :param features: Extracted features. Shape: [num_target_tokens, num_tokens, num_heads*num_layers]
        :return: Scores for each token. Shape: [num_tokens]
        """
        # Features: [num_target_tokens, num_tokens, num_heads*num_layers]
        num_target_tokens, num_tokens, _ = features.shape
        # Apply linear
        scores = self.linear(features).view((num_target_tokens, num_tokens)) # [num_target_tokens, num_tokens]

        # Average over target tokens
        scores = scores.mean(dim=0) # [num_tokens]

        return scores

    def get_scores(
            self,
            task: AttributionTask,
            attribution_start: int,
            attribution_end: int
    ):
        """
        Get scores by extracting features and passing them through the estimator.
        :param task: The attribution task.
        :param attribution_start: Start token index of the attribution span.
        :param attribution_end: End token index of the attribution span.
        :return: Scores for each token. Shape: [num_tokens]
        """
        features = self.feature_extractor(task, attribution_start, attribution_end)
        return self.forward(features)

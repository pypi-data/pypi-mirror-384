from abc import ABC, abstractmethod
import logging
from pathlib import Path
import pickle

import numpy as np
import torch
from numpy.typing import ArrayLike
from sklearn.metrics import precision_recall_curve
from sklearn.linear_model import LinearRegression

logger = logging.getLogger(__name__)

class BaseScoreCombinator(ABC):
    """
    Base class for combination of scores.
    """
    def __init__(
            self,
            feature_names: list[str],
            **kwargs
    ):
        """
        :param feature_names: Names of input features
        :param kwargs:
        """
        self.feature_names = feature_names
        self._model = None
        self._threshold = None
        self._input_normalize_min = None
        self._input_normalize_max = None

    @abstractmethod
    def fit(
            self,
            x: ArrayLike, # [n_observations, n_features]
            y: ArrayLike # [n_observations]
    ):
        """
        Fit the model and optimal threshold
        :param x: Input features, shape [n_observations, n_features]
        :param y: Binary labels, shape [n_observations]
        :return:
        """

    def fit_threshold(
            self,
            y_scores: ArrayLike,
            y_true: ArrayLike
    ):
        """
        Fit optimal threshold for binary predictions
        :param y_scores: Scores for positive class, shape [n_observations]
        :param y_true: True binary labels, shape [n_observations]
        """
        prec, rec, thresh = precision_recall_curve(y_true, y_scores)
        f1s = 2 * prec * rec / (prec + rec + 1e-8)
        best_idx = np.argmax(f1s)
        self._threshold = thresh[best_idx]

    def fit_input_normalize(
            self,
            x: ArrayLike
    ):
        """
        Fit column-wise (dimension 1) min-max normalization to input array
        :param x: Input features, shape [n_observations, n_features]
        """
        self._input_normalize_min = np.min(x, axis=0)
        self._input_normalize_max = np.max(x, axis=0)
        if np.any(self._input_normalize_max - self._input_normalize_min == 0):
            logger.warning("Some features have constant values. Normalization will not be applied to these features.")

    def input_normalize(
            self,
            x: ArrayLike # [n_observations, n_features]
    ) -> np.ndarray:
        """
        Apply column-wise input normalization
        :param x: Input features, shape [n_observations, n_features]
        :return: Normalized input features, shape [n_observations, n_features]
        """
        if self._input_normalize_min is None or self._input_normalize_max is None:
            raise ValueError("Normalization parameters not set. Call fit_input_normalize first.")

        normalized_x = (x - self._input_normalize_min) / (self._input_normalize_max - self._input_normalize_min)
        return normalized_x

    @abstractmethod
    def predict_proba(
            self,
            x: ArrayLike,
    ) -> np.ndarray:
        """
        Predict scores for the given input
        :param x: Input features, shape [n_observations, n_features]
        :return: Scores for positive class, shape [n_observations]
        """

    @abstractmethod
    def predict_binary(
            self,
            x: ArrayLike
    ) -> np.ndarray:
        """
        Predict binary labels for the given input
        :param x: Input features, shape [n_observations, n_features]
        :return: Binary labels, shape [n_observations]
        """

    @abstractmethod
    def scores_to_binary(
            self,
            scores
    ) -> np.ndarray:
        """
        Predict binary labels for the given scores
        :param scores: Scores for positive class, shape [n_observations]
        :return: Binary labels, shape [n_observations]
        """

    def save(
            self,
            save_dir_path: Path
    ):
        """
        Save parameters to disk
        :param save_dir_path: Path to directory where parameters should be saved.
        :return:
        """
        self._save_pkl(save_dir_path)

    @classmethod
    def load(
            cls,
            load_dir_path: Path
    ):
        """
        Load parameters from disk
        :param load_dir_path: Path to directory where parameters are saved.
        :return:
        """
        return cls._load_pkl(load_dir_path)

    def _save_pkl(
            self,
            save_dir_path: Path
    ):
        """
        Save model to a pickle file
        :param save_dir_path: Path to directory where model should be saved.
        """
        with open(save_dir_path / 'score_combinator.pkl', 'wb') as f:
            pickle.dump(self, f)

    @classmethod
    def _load_pkl(
            cls,
            load_dir_path: Path
    ):
        """
        Load model from a pickle file
        :param load_dir_path: Path to directory where model is saved.
        """
        with open(load_dir_path / 'score_combinator.pkl', 'rb') as f:
            loaded_model = pickle.load(f)

        if not isinstance(loaded_model, cls):
            raise ValueError(f"Loaded model is not of type {cls.__name__}.")
        return loaded_model


class LinearScoreCombinator(BaseScoreCombinator):
    """
    Normalizes scores and combines them linearly.
    """
    def __init__(
            self,
            feature_names: list[str],
            weighted: bool
    ):
        """

        :param feature_names: Names of input features
        :param weighted: If True, learn weights for linear combination. If False,
        use uniform weights (only learn normalization and threshold).
        """
        super().__init__(
            feature_names=feature_names
        )

        self.weighted = weighted

    def fit(
            self,
            x: ArrayLike,
            y: ArrayLike
    ):
        """
        Fit the model and optimal threshold
        :param x: Input features [n_observations, n_features]
        :param y: Binary labels [n_observations]
        :return:
        """
        self._model = LinearRegression()

        # Fit normalization
        self.fit_input_normalize(x)

        # Normalize input
        x = self.input_normalize(x)

        if self.weighted:
            self._model.fit(x, y)

        else:
            # Set parameters to uniform weights summing to 1
            weights = np.ones(x.shape[1]) / x.shape[1]
            # Make intercept of all 0
            intercept = np.array(0.0)
            self._model.coef_ = weights
            self._model.intercept_ = intercept


        # Fit threshold
        self.fit_threshold(
            y_scores=self.predict_proba(x, is_normalized=True),
            y_true=y
        )

    def predict_proba(
            self,
            x: ArrayLike, # [n_observations, n_features]
            is_normalized: bool = False
    ) -> np.ndarray: # [n_observations]
        """
        Predict scores for the given input
        :param x: Input features, shape [n_observations, n_features]
        :param is_normalized: Whether input is already normalized
        :return: Scores for positive class, shape [n_observations]
        """
        if self._model is None:
            raise ValueError("Model not fitted. Call fit first.")

        # Normalize input
        if not is_normalized:
            x = self.input_normalize(x)

        # Predict scores
        return self._model.predict(x)

    def predict_binary(
            self,
            x: ArrayLike,
            is_normalized: bool = False
    ) -> np.ndarray: # [n_observations]
        """
        Predict binary labels for the given input
        :param x: Input features, shape [n_observations, n_features]
        :param is_normalized: Whether input is already normalized
        :return: Binary labels, shape [n_observations]
        """
        if self._threshold is None:
            raise ValueError("Threshold not set. Call fit first.")

        # Get scores
        scores = self.predict_proba(
            x=x,
            is_normalized=is_normalized
        )

        # Apply threshold
        return self.scores_to_binary(scores)

    def scores_to_binary(
            self,
            scores: ArrayLike
    ) -> np.ndarray:
        """
        Predict binary labels for the given scores
        :param scores: Scores for positive class, shape [n_observations]
        :return: Binary labels, shape [n_observations]
        """
        if isinstance(scores, torch.Tensor):
            scores = scores.cpu().numpy()

        return (scores >= self._threshold).astype(bool)


def load_score_combinator(
        score_combinator_path: str | Path | None,
        feature_names: list[str] = None
) -> BaseScoreCombinator:
    """
    Load score combinator from path, or initialize a new one if path is None.
    :param score_combinator_path: Path to score combinator directory, or None to initialize a new one.
    :param feature_names: Names of features. Must be given if score_combinator_path is None.
    :return: Score combinator.
    """
    if score_combinator_path is None:
        assert feature_names is not None, ('feature_names must be given when '
                                           'score_combinator_path is None')
        # Initialize
        score_combinator = LinearScoreCombinator(
            feature_names=feature_names,
            weighted=False
        )
        # Pseudo-fit to dummy data
        dummy_x = [
            [1.0 for _ in feature_names],
            [0.0 for _ in feature_names]
        ]
        dummy_y = [1,0]
        score_combinator.fit(
            x=dummy_x,
            y=dummy_y
        )
    else:
        score_combinator = BaseScoreCombinator.load(score_combinator_path)

    return score_combinator

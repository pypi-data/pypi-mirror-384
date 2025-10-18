from abc import abstractmethod, ABC
from pathlib import Path

import torch


class BaseRetriever(ABC):
    """
    Base interface for retriever
    """
    def __init__(self):
        pass

    @classmethod
    @abstractmethod
    def load(
            cls,
            save_dir_path_or_id: Path | str
    ):
        """
        Load retriever from path
        :param save_dir_path_or_id:
        :return:
        """

    @abstractmethod
    def save(
            self,
            save_dir_path: Path | str
    ):
        """
        Save retriever to path
        :param save_dir_path:
        :return:
        """

    @abstractmethod
    def score(
            self,
            query: str,
            docs: list[str]
    ) -> torch.Tensor:
        """
        Score unseen documents.
        :param query: Query string
        :param docs: List of documents to score
        :return: List of scores for each document
        """

from pathlib import Path

import torch
from sentence_transformers import SentenceTransformer

from .base_retriever import BaseRetriever


class SBERTDualRetriever(BaseRetriever):
    """
    Retriever based on dual encoder architecture
    """
    def __init__(
            self,
            query_encoder: SentenceTransformer,
            doc_encoder: SentenceTransformer
    ):
        super().__init__()
        self.query_encoder = query_encoder
        self.doc_encoder = doc_encoder

    @classmethod
    def load(
            cls,
            save_dir_path_or_id: Path | str
    ):
        """
        Load model by id or path
        :param save_dir_path_or_id:
        :return:
        """
        if save_dir_path_or_id == 'dragon':
            query_encoder = SentenceTransformer('nthakur/dragon-plus-query-encoder')
            candidate_encoder = SentenceTransformer('nthakur/dragon-plus-context-encoder')
            return cls(
                query_encoder=query_encoder,
                doc_encoder=candidate_encoder
            )
        else:
            raise NotImplementedError

    def save(
            self,
            save_dir_path: Path | str
    ):
        raise NotImplementedError

    def score(
            self,
            query: str,
            docs: list[str]
    ) -> torch.Tensor:
        """
        Score unseen documents.
        :param query: Query string
        :param docs: List of documents to score
        :return:
        """
        query_embeddings = self.query_encoder.encode([query], convert_to_tensor=True)
        candidate_embeddings = self.doc_encoder.encode(docs, convert_to_tensor=True)
        scores = query_embeddings @ candidate_embeddings.transpose(1, 0)

        return scores[0]
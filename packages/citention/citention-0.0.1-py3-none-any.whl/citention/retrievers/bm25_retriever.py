import json
from collections import Counter
from pathlib import Path

import torch
from rank_bm25 import BM25Okapi

from .base_retriever import BaseRetriever


class BM25Retriever(BaseRetriever):
    def __init__(
            self,
            idf: dict[str, float],
            avgdl: float,
            k1: float,
            b: float
    ):
        """
        :param idf: Dictionary of inverse document frequencies
        :param avgdl: average document length
        :param k1:
        :param b:
        """
        super().__init__()
        self._idf = idf
        self._avgdl = avgdl
        self._k1 = k1
        self._b = b

    def score(
            self,
            query: str,
            docs: list[str]
    ) -> torch.Tensor:
        """
        Score unseen documents using the trained BM25 model's IDF stats.
        :param query: search query string
        :param docs: list of doc strings to score
        :return tensor of scores of shape (len(docs))
        """
        tokenized_query = query.split()
        idf = self._idf
        avgdl = self._avgdl
        k1 = self._k1
        b = self._b

        scores = torch.zeros(
            (len(docs))
        )
        for i, doc in enumerate(docs):
            tokenized_doc = doc.split()
            doc_len = len(tokenized_doc)
            freq = Counter(tokenized_doc)

            score = 0.0
            for q in tokenized_query:
                if q not in freq:
                    continue
                tf = freq[q]
                idf_q = idf.get(q, 0.0)  # if term not in training corpus, IDF = 0

                numerator = tf * (k1 + 1)
                denominator = tf + k1 * (1 - b + b * doc_len / avgdl)
                score += idf_q * (numerator / denominator)

            scores[i] = score
        return scores

    @classmethod
    def from_corpus(cls, corpus: list[str]):
        """
        Initialize from a corpus
        :param corpus: list of corpus documents
        """
        tokenized_corpus = [doc.split() for doc in corpus]
        bm25 = BM25Okapi(tokenized_corpus)
        return cls(
            idf=bm25.idf,
            avgdl=bm25.avgdl,
            k1=bm25.k1,
            b=bm25.b
        )

    @classmethod
    def load(cls, save_dir_path_or_id: Path | str):
        """
        Load BM25 from disk.
        """
        if isinstance(save_dir_path_or_id, str):
            save_dir_path_or_id = Path(save_dir_path_or_id)
        save_path = save_dir_path_or_id / "bm25.json"
        if not save_path.exists():
            raise FileNotFoundError(f"BM25 index not found at {save_path}")
        with open(save_path, "r") as f:
            save_dict = json.load(f)
        return cls(
            idf=save_dict["idf"],
            avgdl=save_dict["avgdl"],
            k1=save_dict["k1"],
            b=save_dict["b"]
        )

    def save(self, save_dir_path: Path):
        """
        Save BM25 index to disk.
        """
        save_dict = {
            "idf": self._idf,
            "avgdl": self._avgdl,
            "k1": self._k1,
            "b": self._b
        }

        save_path = save_dir_path / "bm25.json"
        with open(save_path, "w") as f:
            json.dump(save_dict, f)


if __name__ == '__main__':
    # Test
    corpus = [
        "the quick brown fox jumps over the lazy dog",
        "the dog is lazy but the fox is quick",
        "a fast brown fox and a lazy dog"
    ]
    bm25 = BM25Retriever.from_corpus(corpus)
    query = "quick fox"
    docs = [
        "the quick brown fox jumps over the lazy dog",
        "the dog is lazy but the fox is quick",
        "a fast brown fox and a lazy dog"
    ]
    scores = bm25.score(query, docs)
    print("Scores from our implementation:", scores)

    tokenized_corpus = [
        doc.split() for doc in corpus
    ]
    bm25_rank = BM25Okapi(tokenized_corpus)
    scores_rank = bm25_rank.get_scores(query.split())
    print("Scores from rank_bm25:", scores_rank)
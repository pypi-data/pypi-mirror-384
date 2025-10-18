from pathlib import Path
import logging

from ..retrievers.bm25_retriever import BM25Retriever

logger = logging.getLogger()

class BM25Trainer:
    """
    Computes token statistics for given corpus and saves to disk.
    """
    def train(
            self,
            corpus: list[str],
            out_dir: Path | str
    ):
        """
        Compute token statistics for corpus and save to out_dir
        :param corpus:
        :param out_dir:
        :return:
        """
        # Fit BM25
        logger.info('Fitting BM25 retriever...')
        bm25 = BM25Retriever.from_corpus(
            corpus
        )
        logger.info('BM25 retriever fitted successfully')

        # Save BM25 retriever
        logger.info(f'Saving BM25 retriever to {out_dir}')
        bm25.save(out_dir)
        logger.info('BM25 retriever saved successfully')

        return
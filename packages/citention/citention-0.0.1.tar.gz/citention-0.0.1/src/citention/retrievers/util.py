from ..retrievers.base_retriever import BaseRetriever


def load_retriever(
        retriever_class_name: str,
        model_name_or_path: str
) -> BaseRetriever:
    """
    Load retriever by class name
    :param retriever_class_name: Name of retriever class. Options: 'bm25', 'sbert_dual'
    :param model_name_or_path: Path to model or model name
    :return:
    """
    if retriever_class_name == 'bm25':
        from ..retrievers.bm25_retriever import BM25Retriever
        retriever = BM25Retriever.load(model_name_or_path)

    elif retriever_class_name == 'sbert_dual':
        from ..retrievers.sbert_retriever import SBERTDualRetriever
        retriever = SBERTDualRetriever.load(
            model_name_or_path
        )

    else:
        raise ValueError

    return retriever

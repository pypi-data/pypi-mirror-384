

def get_top_k_indices(
        scores: list[float] | list[list[float]],
        k: int
) -> list[int] | list[list[int]]:
    """
    Get top k indices from list or list of lists
    :param scores: Single list of scores or list of lists of scores
    :param k: Number of top-scoring indices to return per list of scores
    :return: List of top k indices or list of lists of top k indices
    """
    def get_top_k(
            scores_
    ) -> list[int]:
        """
        Get top k indices from single list of scores
        :param scores_:
        :return:
        """
        return sorted(range(len(scores_)), key=lambda i: scores_[i], reverse=True)[:k]

    if isinstance(scores[0], list):
        top_k_indices = [
            get_top_k(score)
            for score in scores
        ]
    else:
        top_k_indices = get_top_k(scores)

    return top_k_indices

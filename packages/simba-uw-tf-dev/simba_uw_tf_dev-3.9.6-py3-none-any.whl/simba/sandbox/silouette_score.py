import numpy as np
from sklearn.datasets import make_blobs
from scipy.spatial.distance import cdist
from sklearn.metrics import silhouette_score as sklearn_silhouette



def silouette_score_cp


def silhouette_score(x: np.ndarray, y: np.ndarray) -> float:
    """
    Compute the silhouette score for the given dataset and labels.

    :param np.ndarray x: The dataset as a 2D NumPy array of shape (n_samples, n_features).
    :param np.ndarray y: Cluster labels for each data point as a 1D NumPy array of shape (n_samples,).
    :returns: The average silhouette score for the dataset.
    :rtype: float

    :example:
    >>> x, y = make_blobs(n_samples=10000, n_features=400, centers=5, cluster_std=10, center_box=(-1, 1))
    >>> score = silhouette_score(x=x, y=y)

    >>> from sklearn.metrics import silhouette_score as sklearn_silhouette # SKLEARN ALTERNATIVE
    >>> score_sklearn = sklearn_silhouette(x, y)

    """
    dists = cdist(x, x)
    results = np.full(x.shape[0], fill_value=-1.0, dtype=np.float32)
    cluster_ids = np.unique(y)
    cluster_indices = {cluster_id: np.argwhere(y == cluster_id).flatten() for cluster_id in cluster_ids}

    for i in range(x.shape[0]):
        intra_idx = cluster_indices[y[i]]
        if len(intra_idx) <= 1:
            a_i = 0.0
        else:
            intra_distances = dists[i, intra_idx]
            a_i = np.sum(intra_distances) / (intra_distances.shape[0] - 1)
        b_i = np.inf
        for cluster_id in cluster_ids:
            if cluster_id != y[i]:
                inter_idx = cluster_indices[cluster_id]
                inter_distances = dists[i, inter_idx]
                b_i = min(b_i, np.mean(inter_distances))
        results[i] = (b_i - a_i) / max(a_i, b_i)

    return np.mean(results)



x, y = make_blobs(n_samples=5000, n_features=20, centers=5, cluster_std=10, center_box=(-1, 1))
score = silhouette_score(x=x, y=y)
#
# # Example Usage
# x, y = make_blobs(n_samples=10000, n_features=400, centers=5, cluster_std=10, center_box=(-1, 1))
# score = silhouette_score(x=x, y=y)
# print(f"Silhouette Score: {score}")
#
# score_sklearn = sklearn_silhouette(x, y)
# print(f"Silhouette Score: {score_sklearn}")

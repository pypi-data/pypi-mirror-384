import numpy as np
from sklearn.datasets import make_blobs
from scipy.spatial.distance import cdist
from itertools import combinations

def cop_index(x: np.ndarray, y: np.ndarray, epsilon: float = 1e-16) -> float:
    """
    Computes the Clustering Overall Performance (COP) Index for evaluating clustering quality.

    The COP Index is defined as the ratio of the average intra-cluster compactness (C)
    to the average inter-cluster separation (S). A lower COP index indicates better clustering,
    as it implies tight clusters and greater separation between them.

    :param np.ndarray x: A 2D array of shape (n_samples, n_features) representing the feature vectors of the data points.
    :param np.ndarray y: A 1D array of shape (n_samples,) containing the cluster labels for each data point.
    :returns: The COP index value. Lower values indicate better clustering.
    :rtype: float

    :references:
    .. [1] Gurrutxaga, I., Albisua, I., Arbelaitz, O., Martín, J. I., Muguerza, J., Pérez, J. M., & Perona, I. (2011).
           SEP/COP: An efficient method to find the best partition in hierarchical clustering based on a new cluster validity index.
           Pattern Recognition, 44(4), 810-820. https://doi.org/10.1016/j.patcog.2010.10.002

    :example:
    >>> X, y = make_blobs(n_samples=50000, centers=10, n_features=3, random_state=0, cluster_std=1)
    >>> cop_index(x=X, y=y)
    """

    unique_clusters = np.unique(y)
    cluster_combinations = list(combinations(unique_clusters, 2))
    intra_cluster_dists = np.full(shape=(len(unique_clusters)), fill_value=np.nan, dtype=np.float64)
    inter_cluster_dists = np.full(shape=(len(cluster_combinations)), fill_value=np.nan, dtype=np.float32)

    for cluster_cnt, cluster_id in enumerate(unique_clusters):
        cluster_x = x[np.argwhere(y == cluster_id).flatten()]
        intra_cluster_dist = np.sum(cdist(cluster_x, cluster_x))
        intra_cluster_dists[cluster_cnt] = intra_cluster_dist / (len(cluster_x) ** 2)

    C = np.mean(intra_cluster_dists)
    for cnt, (k, j) in enumerate(cluster_combinations):
        cluster_k = x[np.argwhere(y == k).flatten()]
        cluster_j = x[np.argwhere(y == j).flatten()]
        inter_cluster_dists[cnt] = np.min(cdist(cluster_k, cluster_j))

    S = np.mean(inter_cluster_dists)

    return C / (S + epsilon)

X, y = make_blobs(n_samples=50000, centers=10, n_features=3, random_state=0, cluster_std=1)
cop_index(x=X, y=y)


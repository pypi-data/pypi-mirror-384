import numpy as np


def bouguessa_wang_sun_v2(x: np.ndarray, y: np.ndarray) -> float:
    """
    Compute the Bouguessa-Wang-Sun (BWS) index using covariance matrices and means.

    :param np.ndarray x: A 2D array of shape (n_samples, n_features) representing the feature vectors of the data points.
    :param np.ndarray y: A 1D array of shape (n_samples,) containing the cluster labels for each data point.
    :returns: The BWS index value. Lower values indicate better clustering.
    :rtype: float

    :example:
    >>> from sklearn.datasets import make_blobs
    >>> X, y = make_blobs(n_samples=500, centers=3, random_state=42)
    >>> bouguessa_wang_sun_v2(X, y)

    :references:
    .. [1] Bouguessa, Wang & Sun (2006).Bouguessa M, Wang S, Sun H. An objective approach to cluster validation.
           Pattern Recognition Letters. 2006;27:1419–1430. doi: 10.1016/j.patrec.2006.01.015.
    """

    unique_y = np.unique(y)
    global_mean = np.mean(x, axis=0)
    compactness, separation = 0, 0

    for cluster_id in unique_y:
        cluster_data = x[y == cluster_id]
        cluster_mean = np.mean(cluster_data, axis=0)
        cov_matrix = np.cov(cluster_data, rowvar=False)
        compactness += np.trace(cov_matrix)
        diff_mean = cluster_mean - global_mean
        separation += len(cluster_data) * np.outer(diff_mean, diff_mean)

    separation_trace = np.trace(separation)
    return separation_trace / compactness

from sklearn.datasets import make_blobs
X, y = make_blobs(n_samples=1000000, centers=30, random_state=42, cluster_std=1)
bouguessa_wang_sun_v2(X, y)
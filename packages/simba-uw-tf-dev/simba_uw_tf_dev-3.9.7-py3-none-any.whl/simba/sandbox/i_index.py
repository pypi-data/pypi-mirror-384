import numpy as np
from sklearn.datasets import make_blobs

def i_index(x: np.ndarray, y: np.ndarray):

    """
    Calculate the I-Index for evaluating clustering quality.

    The I-Index is a metric that measures the compactness and separation of clusters.
    A higher I-Index indicates better clustering with compact and well-separated clusters.

    :example:
    >>> X, y = make_blobs(n_samples=5000, centers=20, n_features=3, random_state=0, cluster_std=0.1)
    >>> i_index(x=X, y=y)

    :refrerences:
    >>> #Sum-of-Squares Based Cluster Validity Index and Significance Analysis
    """

    unique_y = np.unique(y)
    n_y = unique_y.shape[0]
    global_centroid = np.mean(x, axis=0)
    sst = np.sum(np.linalg.norm(x - global_centroid, axis=1) ** 2)

    swc = 0
    for cluster_cnt, cluster_id in enumerate(unique_y):
        cluster_obs = x[np.argwhere(y == cluster_id).flatten()]
        cluster_centroid = np.mean(cluster_obs, axis=0)
        swc += np.sum(np.linalg.norm(cluster_obs - cluster_centroid, axis=1) ** 2)

    return sst / (n_y * swc)

X, y = make_blobs(n_samples=5000, centers=20, n_features=3, random_state=0, cluster_std=0.1)
i_index(x=X, y=y)
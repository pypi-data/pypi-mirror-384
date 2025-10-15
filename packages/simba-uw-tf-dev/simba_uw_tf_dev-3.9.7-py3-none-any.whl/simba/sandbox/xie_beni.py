import numpy as np
from sklearn.datasets import make_blobs
from scipy.spatial.distance import cdist

def xie_beni(x: np.ndarray, y: np.ndarray):
    """
    Computes the Xie-Beni index for clustering evaluation.

    :example:
    >>> X, y = make_blobs(n_samples=100000, centers=40, n_features=600, random_state=0, cluster_std=0.3)
    >>> xie_beni(x=X, y=y)

    :references:
    .. [1] X. L. Xie, G. Beni (1991). A validity measure for fuzzy clustering.
           In: IEEE Transactions on Pattern Analysis and Machine Intelligence 13(8), 841 - 847. DOI: 10.1109/34.85677
    """

    cluster_ids = np.unique(y)
    centroids = np.full(shape=(cluster_ids.shape[0], x.shape[1]), fill_value=-1.0, dtype=np.float32)
    intra_centroid_distances = np.full(shape=(y.shape[0]), fill_value=-1.0, dtype=np.float32)
    obs_cnt = 0
    for cnt, cluster_id in enumerate(cluster_ids):
        cluster_obs = x[np.argwhere(y == cluster_id).flatten()]
        centroids[cnt] = np.mean(cluster_obs, axis=0)
        intra_dist = np.linalg.norm(cluster_obs - centroids[cnt], axis=1)
        intra_centroid_distances[obs_cnt: cluster_obs.shape[0]+obs_cnt] = intra_dist
        obs_cnt += cluster_obs.shape[0]
    compactness = np.mean(np.square(intra_centroid_distances))
    cluster_dists = cdist(centroids, centroids).flatten()
    d = np.sqrt(cluster_dists[np.argwhere(cluster_dists > 0).flatten()])
    separation = np.min(d)

    return compactness / separation

#
# X, y = make_blobs(n_samples=100000, centers=40, n_features=600, random_state=0, cluster_std=0.3)
# xie_beni(x=X, y=y)





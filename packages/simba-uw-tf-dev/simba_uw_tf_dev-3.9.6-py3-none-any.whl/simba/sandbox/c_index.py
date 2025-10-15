import numpy as np
from sklearn.datasets import make_blobs
from scipy.spatial.distance import cdist

"""
The C Index is calculated as cindex = (Sw - Smin) / (Smax - Smin)

Sw is the sum of within-cluster distance measurements 
(only point-wise combinations of data are summed within each cluster - not between clusters) Smin is the sum 
of the Nw smallest point-wise distances between points within the entire dataset Smax is the sum of the nw largest 
point-wise distances between points within the entire dataset. Nw is the total number of pairs of observations belonging 
to the same cluster. It is the same as total combinations of points within clusters taken two at a time

"""

def c_index(x: np.ndarray, y: np.ndarray) -> float:
    """
    Calculate the C Index for clustering evaluation.

    :param np.ndarray x: A 2D array of shape (n_samples, n_features) containing the data points.
    :param np.ndarray x: A 1D array of shape (n_samples,) containing cluster labels for the data points.
    :return: The C Index value, ranging from 0 to 1.
    :rtype: float

    The C Index ranges from 0 to 1:
       - 0 indicates perfect clustering (clusters are as compact as possible).
       - 1 indicates worst clustering (clusters are highly spread out).

    :example:
    >>> X, y = make_blobs(n_samples=800, centers=2, n_features=3, random_state=0, cluster_std=0.1)
    >>> c_index(x=X, y=y)
    """

    unique_y = np.unique(y)
    S_w = 0
    N_w = 0
    for cluster_id in unique_y:
        cluster_obs = x[np.argwhere(y == cluster_id).flatten()]
        dists = cdist(cluster_obs, cluster_obs)
        # Use upper triangle without diagonal
        triu_indices = np.triu_indices_from(dists, k=1)
        S_w += np.sum(dists[triu_indices])
        N_w += len(triu_indices[0])

    all_dists = cdist(x, x)
    triu_indices = np.triu_indices_from(all_dists, k=1)
    sorted_dists = np.sort(all_dists[triu_indices])

    # Calculate S_min and S_max
    S_min = np.sum(sorted_dists[:N_w])
    S_max = np.sum(sorted_dists[-N_w:])

    return (S_w - S_min) / (S_max - S_min)



X, y = make_blobs(n_samples=800, centers=2, n_features=3, random_state=0, cluster_std=0.1)
c_index(x=X, y=y)
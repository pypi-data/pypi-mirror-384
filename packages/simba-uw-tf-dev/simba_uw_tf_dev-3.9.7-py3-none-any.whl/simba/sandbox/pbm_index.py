import numpy as np
from sklearn.datasets import make_blobs
from scipy.spatial.distance import cdist
from simba.utils.checks import check_valid_array
from simba.utils.enums import Formats
from simba.utils.read_write import get_unique_values_in_iterable

def pbm_index(x: np.ndarray, y: np.ndarray) -> float:
    """
    Compute the PBM (Performance of the Best Matching) Index, a measure of clustering quality that combines the compactness
    of the clusters and the separation between them. The PBM index evaluates how well-defined the clusters are in terms
    of their intra-cluster distance and the distance between their centroids.

    Higher values indicates better clustering.

    :param np.ndarray x: A 2D array of shape (n_samples, n_features) containing the data points.
    :param np.ndarray x: A 1D array of shape (n_samples,) containing cluster labels for the data points.
    :return: The PBM Index value.
    :rtype: float

    :references:
    .. [1] Pakhira, M. K., Bandyopadhyay, S., & Maulik, U. (2004). Validity index for crisp and fuzzy clusters.
           Pattern Recognition, 37(4), 487–501. https://doi.org/10.1016/j.patcog.2003.09.021

    :example:
    >>> X, y = make_blobs(n_samples=5, centers=2, n_features=3, random_state=0, cluster_std=5)
    >>> pbm_index(x=X, y=y)

    """

    check_valid_array(data=x, accepted_ndims=(2,), accepted_dtypes=Formats.NUMERIC_DTYPES.value)
    check_valid_array(data=y, accepted_ndims=(1,), accepted_dtypes=Formats.NUMERIC_DTYPES.value, accepted_axis_0_shape=[x.shape[0], ])
    unique_clusters, X_cnt = np.unique(y), x.shape[1]
    N_clusters = get_unique_values_in_iterable(data=y, name=pbm_index.__name__, min=2)
    x_center = np.mean(x, axis=0)
    center_dists = np.linalg.norm(x - x_center, axis=1)
    E1 = np.sum(center_dists)
    intra_cluster_dists = np.full(shape=(len(unique_clusters)), fill_value=np.nan, dtype=np.float64)
    cluster_centers = np.full(shape=(len(unique_clusters), X_cnt), fill_value=np.nan, dtype=np.float64)
    for cnt, cluster_id in enumerate(unique_clusters):
        cluster_x = x[np.argwhere(y == cluster_id).flatten()]
        cluster_centers[cnt] = np.mean(cluster_x, axis=0)
        center_center_dists = np.linalg.norm(cluster_x - cluster_centers[cnt], axis=1)
        intra_cluster_dists[cnt] = np.sum(center_center_dists)

    EK = np.sum(intra_cluster_dists)

    cluster_dists = cdist(cluster_centers, cluster_centers)
    cluster_dists[cluster_dists == 0] = np.inf
    Dmin = np.min(cluster_dists)

    return (((1/N_clusters) * E1) ** 2) / (EK * Dmin)

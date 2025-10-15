import numpy as np
from sklearn.datasets import make_blobs
from simba.utils.enums import Formats
from simba.utils.checks import check_valid_array
from simba.utils.read_write import get_unique_values_in_iterable

def krzanowski_lai_index(x: np.ndarray, y: np.ndarray, epsilon: float = 1e-16) -> float:
    """
    Computes the Krzanowski-Lai (KL) Index for a given clustering result.

    :param np.ndarray x: A 2D array of shape (n_samples, n_features) representing the feature vectors of the data points.
    :param np.ndarray y: A 1D array of shape (n_samples,) containing the cluster labels for each data point.
    :param float epsilon: Small correction factor to avoid division by zero. Default 1e-16.
    :returns: The KL index value. Higher values indicate better clustering.
    :rtype: float

    :references:
    .. [1] Krzanowski, W. J., & Lai, Y. T. (1988). A criterion for determining the number of groups in a data set using sum-of-squares clustering.
           Biometrics, 44(1), 23–34. https://doi.org/10.2307/2531893

    :example:
    >>> X, y = make_blobs(n_samples=100, centers=10, n_features=3, random_state=0, cluster_std=100)
    >>> krzanowski_lai_index(x=X, y=y)
    """

    check_valid_array(data=x, accepted_ndims=(2,), accepted_dtypes=Formats.NUMERIC_DTYPES.value)
    check_valid_array(data=y, accepted_ndims=(1,), accepted_dtypes=Formats.NUMERIC_DTYPES.value, accepted_axis_0_shape=[x.shape[0], ])
    unique_clusters = np.unique(y)
    _ = get_unique_values_in_iterable(data=y, name=krzanowski_lai_index.__name__, min=2)
    x_center = np.mean(x, axis=0)
    BSS, WSS = 0.0, 0.0
    for cluster_id in unique_clusters:
        cluster_x = x[y == cluster_id]
        cluster_center = np.mean(cluster_x, axis=0)
        BSS += cluster_x.shape[0] * np.linalg.norm(cluster_center - x_center) ** 2
        WSS += np.sum(np.linalg.norm(cluster_x - cluster_center, axis=1) ** 2)
    return BSS / (WSS + epsilon)

# X, y = make_blobs(n_samples=100, centers=10, n_features=3, random_state=0, cluster_std=100)
# d = krzanowski_lai_index(x=X, y=y)
# print(d)

"""
A Criterion for Determining the Number of Groups in a Data
Set Using Sum-of-Squares Clustering
"""
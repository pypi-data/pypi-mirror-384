import numpy as np
from sklearn.datasets import make_blobs
from simba.utils.enums import Formats
from simba.utils.checks import check_valid_array
from simba.utils.read_write import get_unique_values_in_iterable

def rmsstd(x: np.ndarray, y: np.ndarray) -> float:
    """
    Compute the Root-Mean-Square Standard Deviation (RMSSTD) for a clustering result.

    :param np.ndarray x: A 2D array of shape (n_samples, n_features) representing the feature vectors of the data points.
    :param np.ndarray y: A 1D array of shape (n_samples,) containing the cluster labels for each data point.
    :returns: The RMSSTD index value. Lower values indicate better clustering.
    :rtype: float

    :references:
    .. [1] Milligan, G. W., & Cooper, M. C. (1985). An examination of procedures for determining the number of clusters in a data set.
           Psychometrika, 50(2), 159–179. https://doi.org/10.1007/BF02294245

    :example:
    >>> X, y = make_blobs(n_samples=100, centers=10, n_features=3, random_state=0, cluster_std=0.1)
    >>> d = rmsstd(x=X, y=y)
    """

    check_valid_array(data=x, accepted_ndims=(2,), accepted_dtypes=Formats.NUMERIC_DTYPES.value)
    check_valid_array(data=y, accepted_ndims=(1,), accepted_dtypes=Formats.NUMERIC_DTYPES.value, accepted_axis_0_shape=[x.shape[0], ])
    _ = get_unique_values_in_iterable(data=y, name=rmsstd.__name__, min=2)
    unique_clusters = np.unique(y)
    p = x.shape[1]
    numerator, denominator = 0, 0
    for cluster_id in unique_clusters:
        cluster_points = x[y == cluster_id]
        cluster_mean = np.mean(cluster_points, axis=0)
        squared_diff = np.sum((cluster_points - cluster_mean) ** 2)
        numerator += squared_diff
        denominator += (cluster_points.shape[0] - 1) * p

    return np.sqrt(numerator / denominator)

X, y = make_blobs(n_samples=100, centers=10, n_features=3, random_state=0, cluster_std=0.1)
d = rmsstd(x=X, y=y)
print(d)

import numpy as np
from sklearn.datasets import make_blobs

def sd_index(x: np.ndarray, y: np.ndarray):
    """
    Compute the SD (Scatter and Discriminant) Index for evaluating the quality of a clustering solution.

    :param np.ndarray x: A 2D array of shape (n_samples, n_features) representing the feature vectors of the data points.
    :param np.ndarray y: A 1D array of shape (n_samples,) containing the cluster labels for each data point.
    :returns: The SD Index value. Lower values indicate better clustering quality with more compact and well-separated clusters.
    :rtype: float

    :references:
    .. [1] Halkidi, M., Vazirgiannis, M., Batistakis, Y. (2000). Quality Scheme Assessment in the Clustering Process. In: Zighed, D.A., Komorowski, J., Żytkow, J. (eds) Principles of Data Mining and Knowledge Discovery. PKDD 2000.
           Lecture Notes in Computer Science(), vol 1910. Springer, Berlin, Heidelberg. https://doi.org/10.1007/3-540-45372-5_26
    """

    global_std = np.std(x)
    global_m = np.mean(x, axis=0)
    unique_clusters = np.unique(y)
    cnt_y = unique_clusters.shape[0]
    scat, dis = 0, 0

    centroids = np.full(shape=(cnt_y, x.shape[1]), fill_value=-1.0, dtype=np.float32)
    for cnt, cluster in enumerate(unique_clusters):
        cluster_data = x[y == cluster]
        centroids[cnt] = np.mean(cluster_data, axis=0)
        scat += np.mean(np.std(cluster_data, axis=0)) / global_std

    for i in range(cnt_y):
        for j in range(i + 1, cnt_y):
            dist_between_clusters = np.linalg.norm(centroids[i] - centroids[j])
            dist_to_global = (np.linalg.norm(centroids[i] - global_m) + np.linalg.norm(centroids[j] - global_m)) / 2
            dis += dist_between_clusters / dist_to_global

    scat /= cnt_y
    dis /= (cnt_y * (cnt_y - 1) / 2)

    return scat + dis



# for std in [0.000000000001, 0.000001, 0.01, 0.1, 0.2, 0.4, 1, 10, 100, 150, 500]:
#     #print(f"\nCluster Std: {std}")
#     X, y = make_blobs(n_samples=2000, centers=100, random_state=42, cluster_std=std, n_features=40)
#     f = sd_index(X, y)
#     print(f)


# from sklearn.datasets import make_blobs
# X, y = make_blobs(n_samples=2000, centers=100, random_state=42, cluster_std=100, n_features=3)
# sd_index(X, y)
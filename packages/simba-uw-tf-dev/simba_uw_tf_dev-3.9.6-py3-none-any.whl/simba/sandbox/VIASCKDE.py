from sklearn.neighbors import KernelDensity
import numpy as np
from numba import jit

@jit(nopython=True)
def _viasckde_kernel(x: np.ndarray, y: np.ndarray, iso: np.ndarray):
    x = x.astype(np.float64)

    ASC_size = np.sum(np.array([np.sum(y == i) for i in np.unique(y)]))
    ASC = np.zeros((ASC_size))
    CoSeD = np.zeros(ASC_size)
    numC = np.zeros(np.unique(y).shape[0])

    dist_cnts = 0
    for cluster_cnt, k in enumerate(np.unique(y)):
        cluster_obs = x[np.argwhere(y == k).flatten()]
        cluster_isos = iso[np.argwhere(y == k).flatten()]
        other_obs = x[np.argwhere(y != k).flatten()]
        isos = (cluster_isos-np.min(cluster_isos))/(np.max(cluster_isos)-np.min(cluster_isos))
        for j in range(cluster_obs.shape[0]):
            xx = cluster_obs[j]
            A = np.inf
            for p in range(cluster_obs.shape[0]):
                if p != j:
                    A = min(A, np.linalg.norm(cluster_obs[p] - xx))
            B = np.inf
            for q in range(other_obs.shape[0]):
                B = min(B, np.linalg.norm(other_obs[q] - xx))
            if max(A, B) * isos[j] == 0.0:
                p = 0
            else:
                p = ((B - A) / max(A, B)) * isos[j]
            ASC[dist_cnts] = p
            dist_cnts +=1
        #numC[cluster_cnt] =
        print(CoSeD)


    #
    #         #min_extra_distance = min(min_extra_distance, np.linalg.norm(cluster_obs[p] - cluster_obs[j]))
    #
    #         #print(row)
    #
    #



def viasckde(x: np.ndarray, y: np.ndarray, kernel: str = 'gaussian', bandwidth: float = 2.0):


    kde = KernelDensity(kernel=kernel, bandwidth=bandwidth).fit(x)
    iso = kde.score_samples(x)
    _viasckde_kernel(x=x, y=y, iso=iso)






x = np.random.randint(0, 10, (100, 2))
y = np.random.randint(0, 5, (100,))


viasckde(x=x, y=y)
import numpy as np
from simba.utils.checks import check_valid_array
from simba.utils.enums import Formats

def get_confusion_matrix(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """
    Compute a confusion matrix

    .. note::
       Adapted from mucunwuxian's Stack Overflow answer: https://stackoverflow.com/a/67747070

    :param np.ndarray x: Predicted cluster labels (1D array of integers).
    :param np.ndarray y: Ground truth class labels (1D array of integers, same length as `x`).
    :returns: A 2D confusion matrix of shape (n_labels, n_labels), where entry (i, j) is the number of times label `i` in `x` coincided with label `j` in `y`.
    :rtype: np.ndarray

    :example:
    >>> x = np.random.randint(0, 5, (100000,))
    >>> y = np.random.randint(0, 5, (100000,))
    >>> c = get_confusion_matrix(x=x, y=y)
    """

    check_valid_array(data=x, source=f'{get_confusion_matrix.__name__} x', accepted_ndims=(1,), accepted_dtypes=Formats.INTEGER_DTYPES.value)
    check_valid_array(data=y, source=f'{get_confusion_matrix.__name__} y', accepted_ndims=(1,), accepted_axis_0_shape=[x.shape[0]], accepted_dtypes=Formats.INTEGER_DTYPES.value)
    N = max(max(x), max(y)) + 1
    y = N * x + y
    y = np.bincount(y, minlength=N * N)
    return y.reshape(N, N)

@staticmethod
def get_clustering_purity(x: np.ndarray, y: np.ndarray) -> float:
    """
    Compute clustering quality using purity score.

    An external evaluation metric for clustering quality. It measures the extent to which clusters contain a single class.
    The score ranges from 0 to 1, where 1 indicates perfect purity.

    .. note::
       Adapted from Ugurite's Stack Overflow answer: https://stackoverflow.com/a/51672699


    :param np.ndarray x: Predicted cluster labels (1D array of integers).
    :param np.ndarray y: Ground truth class labels (1D array of integers, same length as `x`).
    :returns: Purity score in the range [0, 1].
    :rtype: float

    :example:
    >>> x = np.random.randint(0, 5, (100000,))
    >>> y = np.random.randint(0, 4, (100000,))
    >>> p = Statistics.get_clustering_purity(x=x, y=y)

    :references:
       .. [1] Evaluation of clustering. *Introduction to Information Retrieval*. Available at: https://nlp.stanford.edu/IR-book/html/htmledition/evaluation-of-clustering-1.html
    """

    check_valid_array(data=x, source=f'{Statistics.get_clustering_purity.__name__} x', accepted_ndims=(1,),
                      accepted_dtypes=Formats.INTEGER_DTYPES.value)
    check_valid_array(data=y, source=f'{Statistics.get_clustering_purity.__name__} y', accepted_ndims=(1,),
                      accepted_axis_0_shape=[x.shape[0]], accepted_dtypes=Formats.INTEGER_DTYPES.value)
    c = get_confusion_matrix(x=x, y=y)
    return np.sum(np.amax(c, axis=0)) / np.sum(c)





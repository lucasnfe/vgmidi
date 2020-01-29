import numpy  as np

from dtaidistance               import dtw
from sklearn.metrics.pairwise   import pairwise_distances

def sign(x):
    if x >= 0:
        return 1
    return -1

def normalize(x):
    if np.std(x) == 0:
        return x

    # Time series normalization (z-score)
    return (x - np.mean(x)) / np.std(x)

def affinity(x):
    # Calculate distance matrix using dynamic time warping distance
    distance_matrix = pairwise_distances(x, metric=dtw.distance, n_jobs=2)

    # Normalize distance matrix
    distance_matrix_norm = normalize(distance_matrix)

    return distance_matrix_norm

def mean(xs):
    # Time series mean
    return np.mean(xs, axis=0)

def nearest_to_centroid(xs):
    centroid = mean(xs)

    dists = []
    for x in xs:
        dists.append(dtw.distance(x, centroid))
    min_i = np.argmin(dists)

    return xs[min_i]

def median(xs):
    return np.median(xs, axis=0)

def std(xs):
    # Time series standard deviation
    return np.std(xs, axis=0)

def variance(xs):
    return np.var(xs, axis=0)

def kendall_w(xs):
    xs = np.array(xs)
    if xs.ndim != 2:
        raise 'Matrix must be 2-dimensional'

    m = xs.shape[0] #raters
    n = xs.shape[1] # items rated

    denom = m**2*(n**3-n)
    xs_sums = np.sum(xs, axis=0)
    s = m*np.var(xs_sums)

    return 12*s/denom

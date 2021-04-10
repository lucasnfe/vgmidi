import numpy as np

from sklearn.preprocessing import normalize
from sklearn.cluster import AgglomerativeClustering
from tslearn.clustering import TimeSeriesKMeans

def moving_average(x, w):
    return np.convolve(x, np.ones(w), 'valid') / w

def nearest_to_centroid(xs):
    centroid = np.mean(xs, axis=0)
    dist = np.linalg.norm(xs - centroid, axis=1)
    return xs[np.argmin(dist)]

def cluster_annotation_dimension(data, n_clusters=3):
    data = np.array([list(moving_average(d, 2)) for d in data])

    clustering = TimeSeriesKMeans(n_clusters=n_clusters, metric="euclidean")
    clustering.fit(data)

    clusters = []
    for cluster_ix in range(n_clusters):
        cl = np.where(clustering.labels_ == cluster_ix)[0]
        clusters.append(data[cl])

    return clusters

def seperate_annotation_dimension(data):
    positive = []
    negative = []

    data_mean = np.mean(data, axis=1)
    positive_ixs = np.where(data_mean > 0)[0]
    negative_ixs = np.where(data_mean < 0)[0]

    positive = data[positive_ixs]
    negative = data[negative_ixs]
    return [negative, positive]

def cluster_annotations(data):
    clustering = seperate_annotation_dimension(data)
    majority_cluster = get_majority_cluster(clustering)

    return clustering, majority_cluster

def get_majority_cluster(clustering):
    cl_lens = []
    for i in range(len(clustering)):
        cl_lens.append(len(clustering[i]))

    j = np.argmax(cl_lens)

    # If there is a tie, get the one with higher absolute mean
    means = []
    for i in range(len(clustering)):
        if len(clustering[i]) == len(clustering[j]):
            m = abs(np.mean(clustering[i]))
            means.append((i, m))

    sorted_means = sorted(means, key=lambda k: k[1])
    majority_cluster_ix = sorted_means[-1][0]

    if len(means) > 1:
        print("BREAKING TIE!")
        print(sorted_means)
        print("Selected", majority_cluster_ix)

    return majority_cluster_ix

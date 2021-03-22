import pandas as pd
import numpy as np

from sklearn.cluster import AgglomerativeClustering

from .tsmath import affinity, variance, normalize

def cluster_annotation_dimension(data, n_clusters=3, smoothing_window=2):
    # Normalize
    # data = np.apply_along_axis(normalize, 0, data)

    # Apply moving average smoother
    # moving_average = lambda v : pd.Series(v).rolling(smoothing_window).mean()[smoothing_window-1:]
    # data = np.apply_along_axis(moving_average, 0, data)

    clustering = AgglomerativeClustering(n_clusters=n_clusters)
    clustering.fit(data)

    return clustering.labels_

def cluster_annotations(data):
    labels = cluster_annotation_dimension(data)
    clustering = get_cluster_series_from_labels(data, labels)
    cluster_with_higher_agreement = get_cluster_with_higher_agreement(clustering)

    return clustering, cluster_with_higher_agreement

def get_cluster_with_higher_agreement(clustering):
    cl_lens = []
    for i in range(len(clustering)):
        cl_lens.append(len(clustering[i]))

    first = np.argsort(cl_lens)[-1]

    return first

def get_cluster_series_from_labels(series, labels):
    n_clusters = len(set(labels))

    clusters = []
    for cluster_ix in range(n_clusters):
        cl = []

        # Plot series within cluster cluster_ix
        for i in np.where(labels == cluster_ix)[0]:
            cl.append(series[i])
        clusters.append(cl)

    return clusters

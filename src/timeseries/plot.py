# External imports
import matplotlib.pyplot as plt
from matplotlib import gridspec

# Local imports
from .cluster import *
from .tsmath import *

def plot_annotation(piece_annotations, y_axis="", subtitle=""):
    fig, axarr = plt.subplots(2, sharex=True, figsize=(15, 5))
    fig.suptitle(subtitle)

    for an_val in piece_annotations["valence"]:
        axarr[0].plot(an_val)
    axarr[0].set(ylabel=y_axis)

    for an_aro in piece_annotations["arousal"]:
        axarr[1].plot(an_aro)
    axarr[1].set(ylabel='Arousal')

    plt.savefig("plots/" + subtitle + "_annotations.png", format="png")

    fig.clf()
    plt.clf()
    plt.close();

def plot_cluster(series, clustering, y_axis="", subtitle="", filename="clustering.png"):
    # Plot figure with subplots of different sizes
    fig = plt.figure()

    n_clusters = len(clustering)

    ts_ax = plt.subplot2grid((3, n_clusters), (0, 0), colspan=n_clusters)
    ts_ax.set_title("Annotation", fontsize=12)

    plt.axis([0, len(series[0]), -1, 1])
    plt.xticks(np.arange(0, len(series[0]), 5))
    plt.xlabel('Measures')
    plt.ylabel(y_axis)

    # large subplot
    for x in series:
        plt.plot(x)

    # small subplot 1
    for i in range(len(clustering)):
        ts_ax = plt.subplot2grid((3, n_clusters), (1, i), colspan=1)
        ts_ax.set_title("Cluster " + str(i+1), fontsize=12)

        plt.axis([0, len(clustering[i][0]), -1, 1])
        plt.xticks(np.arange(0,  len(clustering[i][0]), 5))
        plt.xlabel('Measures')
        plt.ylabel(y_axis)
        for x in clustering[i]:
            plt.plot(x)

    h_ix = get_cluster_with_higher_agreement(clustering)

    ts_ax = plt.subplot2grid((3, n_clusters), (2, 0), colspan=n_clusters)
    ts_ax.set_title("Median of the cluster " + str(h_ix + 1) , fontsize=12)

    plt.axis([0, len(clustering[h_ix][0]), -1, 1])
    # plt.xticks(np.arange(0, len(clustering[h_ix][0]), 5))
    plt.xlabel('Measures')
    plt.ylabel(y_axis)

    plt.plot(median(clustering[h_ix]))

    # Plot splitting points
    # plt.vlines(split_points, -1, 1, colors='r', linestyles='dashed')

    # fit subplots and save fig
    fig.tight_layout()
    fig.savefig(filename, format="png")

    fig.clf()
    plt.clf()
    plt.close()

    #
    # fig = plt.figure()
    # ax1 = plt.subplot2grid((3,2), (0, 0), colspan=2)
    # ax2 = plt.subplot2grid((3,2), (1, 0), colspan=1)
    # ax3 = plt.subplot2grid((3,2), (1, 1), colspan=1)
    # ax4 = plt.subplot2grid((3,2), (2, 0), colspan=2)
    #
    # fig.tight_layout()
    #
    # fig.savefig(filename, format="png")

def plot_means(means, filename, y_axis="", title="", color=(0,0,1,1)):
    fig = plt.figure(figsize=(7,2))

    plt.axis([0, len(means[0]), -1, 1])
    plt.xlabel('Measures')
    plt.ylabel(y_axis)

    plt.title(title, fontsize=16)

    r,g,b,a = color
    for m in means:
        if r > 0:
            r *= 0.75
        if g > 0:
            g *= 0.75
        if b > 0:
            b *= 0.75

        plt.plot(m, color=(r,g,b,a))

    fig.tight_layout()
    fig.savefig(filename, format="png")

    fig.clf()
    plt.clf()
    plt.close()

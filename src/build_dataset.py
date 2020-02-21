import os
import sys
import argparse
import numpy as np

import timeseries as ts
import dataset as ds

# Parse arguments
parser = argparse.ArgumentParser(description='train_generative.py')
parser.add_argument('--annotations', type=str, required=True, help="Dir with annotation files.")
parser.add_argument('--midi' , type=str, required=True, help="Dir with annotated midi files.")
parser.add_argument('--phrases' , type=str, required=True, help="Phrases output path.")
parser.add_argument('--plots' , type=str, required=True, help="Plots output path.")
parser.add_argument('--dupli', dest='rmdup', action='store_false')
parser.set_defaults(rmdup=True)

opt = parser.parse_args()

# Parse music annotaion into a dict of pieces
pieces = ds.parse.parse_annotation(opt.annotations)

# Cluster pieces
annotated_data = []

# Means
means_pos, means_neg = [], []

for i, piece_id in enumerate(pieces):
    # Get midi name without extension
    midi_name = os.path.basename(pieces[piece_id]["midi"])
    print("Processing...", midi_name)

    # Clamp examples with length greater than the min length
    valence_min_length = min([len(d) for d in pieces[piece_id]["valence"]])
    valence_data = np.array([d[:valence_min_length] for d in pieces[piece_id]["valence"]])

    # Remove annotations with very high variance (noise)
    valence_data_without_noise = []
    for x in valence_data:
        if np.var(x) < 0.1:
            valence_data_without_noise.append(x)

    # Cluster annotations of this midi file
    clustering, cluster_with_higher_agreement = ts.cluster.cluster_annotations(valence_data_without_noise)

    # In the valence dimension, find the nearest curve to the centroid
    mean_annotation = ts.tsmath.median(clustering[cluster_with_higher_agreement])

    # Split the nearest curve to the centroid at the points of sentiment change (from -1 to 1 or from 1 to -1)
    split_valence = ts.split.split_annotation_by_sentiment(mean_annotation)

    # Split midi file at the points of sentiment change (from -1 to 1 or from 1 to -1)
    midi_path = os.path.join(opt.midi, midi_name)

    measure_length = pieces[piece_id]["duration"]/pieces[piece_id]["measures"]
    midi_sent_parts = ts.split.split_midi(piece_id, midi_path, split_valence, measure_length, opt.phrases)

    annotated_data += midi_sent_parts

    # Plot valence
    plot_path = os.path.join(opt.plots, os.path.splitext(midi_name)[0] + "_valence.png")
    ts.plot.plot_cluster(valence_data_without_noise, clustering, "Clustering Valence", plot_path)

train, test = ds.split.generate_data_splits(annotated_data, remove_duplicates=opt.rmdup)
ds.parse.persist_annotated_mids(train, "vgmidi_sent_train.csv")
ds.parse.persist_annotated_mids(test, "vgmidi_sent_test.csv")

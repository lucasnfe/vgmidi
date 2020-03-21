import os
import sys
import argparse
import numpy as np

import timeseries as ts
import dataset as ds

def parse_emotion_dimension(piece, dimension_name, max_variance=0.1):
    # Clamp examples with length greater than the min length
    min_length = min([len(d) for d in piece[dimension_name]])
    data_dimension = np.array([d[:min_length] for d in piece[dimension_name]])

    rows_to_delete = np.where(np.var(data_dimension, axis=1) > max_variance)
    data_dimension = np.delete(data_dimension, rows_to_delete, axis=0)

    return data_dimension

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
valence_phrases = []
arousal_phrases= []

# Means
means_pos, means_neg = [], []

for i, piece_id in enumerate(pieces):
    # Get midi name without extension and path
    midi_name = os.path.basename(pieces[piece_id]["midi"])
    midi_path = os.path.join(opt.midi, midi_name)

    print("Processing...", midi_name)

    valence_data = parse_emotion_dimension(pieces[piece_id], "valence")
    arousal_data = parse_emotion_dimension(pieces[piece_id], "arousal")

    # Cluster annotations of this midi file
    valence_clustering, valence_best_cluster = ts.cluster.cluster_annotations(valence_data)
    arousal_clustering, arousal_best_cluster = ts.cluster.cluster_annotations(arousal_data)

    # Find the medians of the best clusters
    valence_median = ts.tsmath.median(valence_clustering[valence_best_cluster])
    arousal_median = ts.tsmath.median(arousal_clustering[arousal_best_cluster])

    # Make sure number of measures is the same for both dimensions
    assert len(valence_median) == len(arousal_median)

    # Split medians at the points of axis changes (from -1 to 1 or from 1 to -1)
    split_valence = ts.split.split_annotation_by_emotion(valence_median)
    split_arousal = ts.split.split_annotation_by_emotion(arousal_median)

    # Calculate measure length
    measure_length = pieces[piece_id]["duration"]/pieces[piece_id]["measures"]

    # Split midi file considering the median splits
    midi_valence_parts = ts.split.split_midi(piece_id, midi_path, split_valence, measure_length, os.path.join(opt.phrases, "valence"))
    midi_arousal_parts = ts.split.split_midi(piece_id, midi_path, split_arousal, measure_length, os.path.join(opt.phrases, "arousal"))

    valence_phrases += midi_valence_parts
    arousal_phrases += midi_arousal_parts

    # Plot data
    plot_valence_path = os.path.join(os.path.join(opt.plots, "valence"), os.path.splitext(midi_name)[0] + ".png")
    plot_arousal_path = os.path.join(os.path.join(opt.plots, "arousal"), os.path.splitext(midi_name)[0] + ".png")

    ts.plot.plot_cluster(valence_data, valence_clustering, "Clustering Valence", plot_valence_path)
    ts.plot.plot_cluster(arousal_data, arousal_clustering, "Clustering Arousal", plot_arousal_path)

train, test = ds.split.generate_data_splits(valence_phrases, remove_duplicates=opt.rmdup)
ds.parse.persist_annotated_mids(train, "vgmidi_valence_train.csv")
ds.parse.persist_annotated_mids(test, "vgmidi_valence_test.csv")

train, test = ds.split.generate_data_splits(arousal_phrases, remove_duplicates=opt.rmdup)
ds.parse.persist_annotated_mids(train, "vgmidi_arousal_train.csv")
ds.parse.persist_annotated_mids(test, "vgmidi_arousal_test.csv")

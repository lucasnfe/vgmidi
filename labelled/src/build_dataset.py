import os
import sys
import argparse
import numpy as np

from parse   import *
from split   import *
from cluster import *
from plot    import plot_cluster

# Parse arguments
parser = argparse.ArgumentParser(description='train_generative.py')
parser.add_argument('--annotations', type=str, required=True, help="Dir with annotation files.")
parser.add_argument('--midi' , type=str, required=True, help="Dir with annotated midi files.")
parser.add_argument('--phrases' , type=str, required=True, help="Phrases output path.")
parser.add_argument('--plots' , type=str, required=True, help="Plots output path.")
parser.add_argument('--at' , type=float, default=0.0, help="Ambiguity Threshold.")
parser.set_defaults(rmdup=True)
opt = parser.parse_args()

# Parse music annotaion into a dict of pieces
pieces = parse_annotation(opt.annotations)

emotion_phrases = []
for i, piece_id in enumerate(pieces):
    # Get midi name without extension and path
    midi_name = os.path.basename(pieces[piece_id]["midi"])
    midi_path = os.path.join(opt.midi, midi_name)

    print("Processing...", midi_name)

    valence_data = parse_emotion_dimension(pieces[piece_id], "valence")
    arousal_data = parse_emotion_dimension(pieces[piece_id], "arousal")

    # Cluster annotations of this midi file
    valence_clustering, valence_best_cluster = cluster_annotations(valence_data)
    arousal_clustering, arousal_best_cluster = cluster_annotations(arousal_data)

    # Find the medians of the best clusters
    valence_median = np.mean(valence_clustering[valence_best_cluster], axis=0)
    arousal_median = np.mean(arousal_clustering[arousal_best_cluster], axis=0)

    # Make sure number of measures is the same for both dimensions
    assert len(valence_median) == len(arousal_median)

    # Split medians at the points of axis changes (from -1 to 1 or from 1 to -1)
    emotion_chunks = split_annotation_by_emotion(valence_median, arousal_median, opt.at)

    # Calculate measure length
    measure_length = pieces[piece_id]["duration"]/pieces[piece_id]["measures"]

    # Split midi file considering the median splits
    midi_valence_parts = split_midi(piece_id, midi_path, emotion_chunks, measure_length, opt.phrases)
    emotion_phrases += midi_valence_parts

    # Plot data
    plot_valence_path = os.path.join(opt.plots, "valence")
    if not os.path.isdir(plot_valence_path):
        os.makedirs(plot_valence_path)

    plot_valence_path = os.path.join(plot_valence_path, os.path.splitext(midi_name)[0] + ".png")
    plot_cluster(valence_data, valence_clustering, valence_best_cluster, "Valence", "Clustering Valence", plot_valence_path)

    plot_arousal_path = os.path.join(opt.plots, "arousal")
    if not os.path.isdir(plot_arousal_path):
        os.makedirs(plot_arousal_path)

    plot_arousal_path = os.path.join(plot_arousal_path, os.path.splitext(midi_name)[0] + ".png")
    plot_cluster(arousal_data, arousal_clustering, arousal_best_cluster, "Arousal", "Clustering Arousal", plot_arousal_path)

persist_annotated_mids(emotion_phrases, "vgmidi.csv")

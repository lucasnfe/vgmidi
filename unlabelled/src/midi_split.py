import os
import csv
import shutil
import argparse
import numpy as np

from sklearn.model_selection import GroupShuffleSplit

def get_data_for_training(midi_csv, midi_dir):
    x, y, groups = [], [], []

    for row in csv.DictReader(open(midi_csv, "r")):
        midi_filename = row["midi"].split("/")[-1]
        midi_path = os.path.join(midi_dir, midi_filename)

        if os.path.isfile(midi_path):
            x.append(int(row["id"]))
            y.append(midi_filename)
            groups.append(row["game"])

    return np.array(x), np.array(y), np.array(groups)

# Parse arguments
parser = argparse.ArgumentParser(description='download_midi.py')
parser.add_argument('--csv', type=str, required=True, help="URL to download files from.")
parser.add_argument('--midi', type=str, required=True, help="Path to midi files.")
parser.add_argument('--out', type=str, default=".", help="Output dir.")
opt = parser.parse_args()

# Load midi data
xs, ys, groups = get_data_for_training(opt.csv, opt.midi)

# Create train and test directories
os.mkdir(os.path.join(opt.out, "train"))
os.mkdir(os.path.join(opt.out, "test"))

# Split dataset
kfold = GroupShuffleSplit(n_splits=1, train_size=.85, test_size=.15, random_state=42)
for train_index, test_index in kfold.split(xs, ys, groups):
    y_train, y_test = ys[train_index], ys[test_index]

    for y in y_train:
        midi_path = os.path.join(opt.midi, y)
        shutil.copyfile(midi_path, os.path.join(opt.out, "train", y))

    for y in y_test:
        midi_path = os.path.join(opt.midi, y)
        shutil.copyfile(midi_path, os.path.join(opt.out, "test", y))

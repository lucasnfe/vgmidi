import os
import csv
import json
import argparse
import numpy as np

def parse_json(filename):
    file = open(filename, "r")
    parsed_json = json.loads(file.read())
    return parsed_json

def parse_annotation(annotations_path):
    annotation_rounds = []

    for filename in os.listdir(annotations_path):
        if os.path.splitext(filename)[1] != ".json":
            continue

        data = parse_json(os.path.join(annotations_path, filename))

        pieces = {}
        for annotation_id in data['annotations']:
            piece_id = annotation_id.split("_")[0]
            if piece_id not in data['pieces']:
                continue

            if piece_id not in pieces:
                pieces[piece_id] = {}
                pieces[piece_id]["name"] = data["pieces"][piece_id]["name"]
                pieces[piece_id]["midi"] = data["pieces"][piece_id]["midi"]
                pieces[piece_id]["measures"] = data["pieces"][piece_id]["measures"]
                pieces[piece_id]["duration"] = data["pieces"][piece_id]["duration"]
                pieces[piece_id]["arousal"] = []
                pieces[piece_id]["valence"] = []

            pieces[piece_id]["arousal"].append(data['annotations'][annotation_id]['arousal'])
            pieces[piece_id]["valence"].append(data['annotations'][annotation_id]['valence'])

        annotation_rounds.append(pieces)

    joint_pieces = {}

    joint_piece_id = 0
    for pieces in annotation_rounds:
        for id, piece in pieces.items():
            joint_pieces["piece_" + str(joint_piece_id)] = piece
            joint_piece_id += 1

    return joint_pieces

def parse_demographics(annotations_path):
    total_annotations = 0

    age, gender, musicianship = {}, {}, {}
    for filename in os.listdir(annotations_path):
        if os.path.splitext(filename)[1] != ".json":
            continue

        data = parse_json(os.path.join(annotations_path, filename))

        for ann in data["annotations"]:
            piece_ann = data["annotations"][ann]

            if piece_ann["gender"] not in gender:
                gender[piece_ann["gender"]] = 0
            gender[piece_ann["gender"]] += 1

            if piece_ann["age"] not in age:
                age[piece_ann["age"]] = 0
            age[piece_ann["age"]] += 1

            if piece_ann["musicianship"] not in musicianship:
                musicianship[piece_ann["musicianship"]] = 0
            musicianship[piece_ann["musicianship"]] += 1

            total_annotations += 1

    age = {k: v/total_annotations for k,v in age.items()}
    gender = {k: v/total_annotations for k,v in gender.items()}
    musicianship = {k: v/total_annotations for k,v in musicianship.items()}

    return age, gender, musicianship

def parse_emotion_dimension(piece, dimension_name, max_variance=0.1):
    # Get most frequent_len
    lens = [len(d) for d in piece[dimension_name]]
    most_frequent_len = max(set(lens), key = lens.count)

    # Remove annotations with different sizes
    data_dimension = []
    for d in piece[dimension_name]:
        if len(d) == most_frequent_len:
            data_dimension.append(d)

    data_dimension = np.array(data_dimension)

    # Remove annotations with very high variance. They are consided annotation noise.
    rows_to_delete = np.where(np.var(data_dimension, axis=1) > max_variance)
    data_dimension = np.delete(data_dimension, rows_to_delete, axis=0)

    return data_dimension

def persist_annotated_mids(annotated_pieces, output_path):
    fieldnames = ['id','series','console', 'game', 'piece', 'midi', 'valence', 'arousal']

    with open(output_path, mode='w') as fp:
        fp_writer = csv.DictWriter(fp, fieldnames=fieldnames)
        fp_writer.writeheader()

        for piece in sorted(annotated_pieces, key=lambda k: k['midi']):
            fp_writer.writerow(piece)

if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser(description='train_generative.py')
    parser.add_argument('--annotations', type=str, required=True, help="Dir with annotation files.")
    opt = parser.parse_args()

    age, gender, musicianship = parse_demographics(opt.annotations)

    print(age)
    print(gender)
    print(musicianship)

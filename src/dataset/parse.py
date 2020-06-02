import os
import csv
import json

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

def persist_annotated_mids(annotated_pieces, output_path):
    with open(output_path, mode='w') as fp:
        fieldnames = ['label', 'id', 'part', 'repeat', 'filepath']
        fp_writer = csv.DictWriter(fp, fieldnames=fieldnames)

        fp_writer.writeheader()
        for piece in annotated_pieces:
            for phrase in piece:
                fp_writer.writerow({"label": phrase["label"],
                                       "id": phrase["id"],
                                     "part": phrase["part"],
                                   "repeat": phrase["repeat"],
                                 "filepath": phrase["filepath"]})

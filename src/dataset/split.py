import math
import random
from collections import OrderedDict

def get_pieces(annotated_mids, remove_duplicates):
    pieces = {}

    n_parts = 0
    for an in annotated_mids:
        piece_id = an["id"]
        piece_part_label = an["label"]
        piece_part_repeat = an["repeat"]

        # Discard repeated pieces
        if remove_duplicates and piece_part_repeat > -1:
            continue

        if piece_id not in pieces:
            pieces[piece_id] = {"pos": 0, "neg": 0, "parts": []}

        if piece_part_label > 0:
            pieces[piece_id]["pos"] += 1
        else:
            pieces[piece_id]["neg"] += 1

        pieces[piece_id]["parts"].append(an)
        n_parts += 1

    return pieces, n_parts

def generate_data_splits(annotated_mids, test_percentage=0.1, remove_duplicates=True):
    train, test = {}, {}

    # Get pieces
    pieces, n_parts = get_pieces(annotated_mids, remove_duplicates)

    # Build test set
    n_pos, n_neg = 0, 0
    while n_pos + n_neg < int(test_percentage * n_parts):
        min_sent_dist = math.inf
        min_sent_piece_id = None
        for piece_id, piece in pieces.items():
            sent_dist = abs((n_pos + piece["pos"]) - (n_neg + piece["neg"]))
            if sent_dist < min_sent_dist:
                min_sent_dist = sent_dist
                min_sent_piece_id = piece_id

        # Remove selected piece
        min_sent_piece = pieces.pop(min_sent_piece_id)

        n_pos += min_sent_piece["pos"]
        n_neg += min_sent_piece["neg"]

        test[min_sent_piece_id] = min_sent_piece["parts"]

    # Build train set
    for piece_id, piece in pieces.items():
        if piece_id not in test:
            train[piece_id] = piece["parts"]

    train_set = []
    for piece_id, piece_parts in train.items():
        train_set += piece_parts

    test_set = []
    for piece_id, piece_parts in test.items():
        test_set += piece_parts

    return train_set, test_set

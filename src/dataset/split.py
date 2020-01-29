from collections import OrderedDict

def get_pieces(annotated_mids, remove_duplicates):
    pieces = {}

    n_pos, n_neg = 0, 0
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
            n_pos += 1
            pieces[piece_id]["pos"] += 1
        else:
            n_neg += 1
            pieces[piece_id]["neg"] += 1

        pieces[piece_id]["parts"].append(an)

    return pieces, n_pos, n_neg

def sort_pieces(pieces, n_neg, n_pos):
    max_parts = max([len(value["parts"]) for key, value in pieces.items()])

    for pc in pieces:
        neg_diff = (n_neg - pieces[pc]["neg"])/n_neg if n_neg > 0 else 0
        pos_diff = (n_pos - pieces[pc]["pos"])/n_pos if n_pos > 0 else 0
        parts = (max_parts - len(pieces[pc]["parts"]))/max_parts if max_parts > 0 else 0

        pieces[pc]["fitness"] = neg_diff + pos_diff + parts

    ordered_pieces = OrderedDict(sorted(pieces.items(), key=lambda t: t[1]["fitness"]))

    return ordered_pieces

def generate_data_splits(annotated_mids, test_percentage=0.1, remove_duplicates=True):
    # Get pieces
    pieces, n_pos, n_neg = get_pieces(annotated_mids, remove_duplicates)

    # Rank pieces according to amount of negative and positve parts
    ordered_pieces = sort_pieces(pieces, n_pos, n_neg)

    n_test_parts = 0
    test_parts = {}

    train, test = [], []

    # Build test set
    n_pieces = n_pos + n_neg

    while n_test_parts < int(test_percentage * n_pieces):
        test_piece_id, test_piece_data = ordered_pieces.popitem(last=False)
        n_test_parts += len(test_piece_data["parts"])

        test_parts[test_piece_id] = pieces[test_piece_id]["parts"]
        test += sorted([an for an in pieces[test_piece_id]["parts"]], key = lambda i: i['part'])

    # Build train set
    for pc in pieces:
        train_piece_id = pieces[pc]["parts"][0]["id"]
        if train_piece_id not in test_parts:
            train += sorted([an for an in pieces[train_piece_id]["parts"]], key = lambda i: i['part'])

    return train, test

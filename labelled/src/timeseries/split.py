import os
import hashlib
import pretty_midi
import numpy as np
from .tsmath import *

MIN_PIECE_ID = 8000

def emotion(v, a):
    emotion = np.array([0,0])

    if v >= 0:
        emotion[0] = 1
    if a >= 0:
        emotion[1] = 1

    return emotion

def split_annotation_by_emotion(valence, arousal, ambiguity_threshold=0.0, ambiguity_allowed=1.0):
    n_ambiguous_measures_valence = 0
    n_ambiguous_measures_arousal = 0

    last_emotion = None

    ix, chunks = -1, []
    for v,a in zip(valence, arousal):
        # Count ambiguous measures (have annotations "close" to zero.)
        if abs(v) < ambiguity_threshold:
            n_ambiguous_measures_valence += 1

        if abs(a) < ambiguity_threshold/2:
            n_ambiguous_measures_arousal += 1

        # Create emotion as numpy array
        current_emotion = emotion(v, a)

        if (current_emotion != last_emotion).any():
            chunks.append([current_emotion])
            ix += 1
        else:
            chunks[ix].append(current_emotion)

        last_emotion = current_emotion

    # Discard pieces that have more ambiguity than the allowed
    valence_ambiguity = n_ambiguous_measures_valence/len(valence)
    arousal_ambiguity = n_ambiguous_measures_arousal/len(arousal)

    if valence_ambiguity > ambiguity_allowed or arousal_ambiguity > ambiguity_allowed:
        print("--- Discaring ambiguous piece !!!")
        return []

    return chunks

def slice_chunk_with_emotion(chunk, split_size):
    slices = []
    for i in range(0, len(chunk), split_size):
        sl = chunk[i:i+split_size]
        slices.append(sl)

    return slices

def slice_midi(midi_data, start, end):
    notes = []

    for instrument in midi_data.instruments:
        if not instrument.is_drum:
            for note in instrument.notes:
                if note.start >= start and note.start < end:
                    note.start -= start
                    note.end -= start
                    notes.append(note)

    midi_slice = create_midi_slice(notes, midi_data.resolution)

    return midi_slice

def create_midi_slice(notes, resolution):
    # Create a PrettyMIDI object
    midi = pretty_midi.PrettyMIDI(resolution=resolution)

    # Create an Instrument instance for a piano instrument
    piano_program = pretty_midi.instrument_name_to_program('Acoustic Grand Piano')
    piano = pretty_midi.Instrument(program=piano_program)

    # Add notes
    for n in notes:
        piano.notes.append(n)
    midi.instruments.append(piano)

    return midi

def get_midi_note_count(midi_data):
    note_count = 0
    for instrument in midi_data.instruments:
        if not instrument.is_drum:
            for note in instrument.notes:
                note_count += 1

    return note_count

def split_midi(piece_id, midi_path, labeled_splits, measure_length, splits_path):
    # Load midi data
    midi_data = pretty_midi.PrettyMIDI(midi_path)

    # Parse midi metadata from name
    midi_root, midi_ext = os.path.splitext(os.path.basename(midi_path))
    id      = MIN_PIECE_ID + int(piece_id.split("_")[-1])
    series  = midi_root.split("_")[0]
    console = midi_root.split("_")[1]
    game    = midi_root.split("_")[2]
    piece   = midi_root.split("_")[3]

    # Dictionary to store the midi slices
    annotated_data = {}

    split_init = 0
    split_count = 0
    for split in labeled_splits:
        split_size = len(split)

        # Get midi for this entire chunk
        split_start = (split_init * measure_length)
        split_end   = (split_init + split_size) * measure_length
        split_midi_data = slice_midi(midi_data, split_start, split_end)

        # Get valence of arousal of this chunk
        split_valence = split[0][0]
        split_arousal = split[0][1]

        # Save midi chunk
        split_name = os.path.join(splits_path, midi_root + "_" + str(split_count) + ".mid")
        split_midi_data.write(split_name)

        # Add split to the dataset
        with open(split_name, "rb") as midi_file:
            ch_key = hashlib.md5(midi_file.read()).hexdigest()

        if ch_key not in annotated_data:
            annotated_data[ch_key] = {"id": id,
                                  "series": series,
                                 "console": console,
                                    "game": game,
                                   "piece": piece,
                                    "midi": split_name,
                                 "valence": split_valence,
                                 "arousal": split_arousal}

            split_count += 1
        else:
            print(ch_key, "is repeated")

        split_init += split_size

    # Sort annotated data by game name
    annotated_data = list(annotated_data.values())
    annotated_data = sorted(annotated_data, key=lambda k: k['game'])

    return annotated_data

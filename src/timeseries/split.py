import os
import hashlib
import pretty_midi
import numpy as np
from .tsmath import *

def sentiment(x):
    if x >= 0:
        return 1
    return 0

def split_annotation_by_sentiment(annotation, split_size=4):
    labeled_phrases = []
    for i in range(0, len(annotation), split_size):
        phrase = annotation[i:i+split_size]

        n_pos_neg = [0, 0]
        for x in phrase:
            n_pos_neg[sentiment(x)] += 1

        phrase_sentiment = np.argmax(n_pos_neg)
        labeled_phrases.append((phrase, phrase_sentiment))

    return labeled_phrases

def slice_midi_data(midi_data, start, end):
    notes = []

    for instrument in midi_data.instruments:
        if not instrument.is_drum:
            for note in instrument.notes:
                if note.start >= start and note.start < end:
                    note.start -= start
                    note.end -= start
                    notes.append(note)

    return notes

def save_midi_slice(notes, resolution, path):
    # Create a PrettyMIDI object
    midi = pretty_midi.PrettyMIDI(resolution=resolution)

    # Create an Instrument instance for a piano instrument
    piano_program = pretty_midi.instrument_name_to_program('Acoustic Grand Piano')
    piano = pretty_midi.Instrument(program=piano_program)

    # Add notes
    for n in notes:
        piano.notes.append(n)

    midi.instruments.append(piano)
    midi.write(path)

    return midi

def split_midi(piece_id, midi_path, labeled_phrases, measure_length, phrases_path):
    # Load midi data
    midi_data = pretty_midi.PrettyMIDI(midi_path)

    # Dictionary to store the midi slices
    annotated_data = {}

    slice_init = 0
    velocity, duration = None, None
    for i, phrase in enumerate(labeled_phrases):
        phrase_valence, phrase_label = phrase
        phrase_length = len(phrase_valence)

        # Slice midi given measure length in seconds
        start, end = slice_init * measure_length, (slice_init + phrase_length) * measure_length
        notes = slice_midi_data(midi_data, start, end)

        # Define name for this midi chunk
        midi_root, midi_ext = os.path.splitext(os.path.basename(midi_path))
        ch_midi_name = os.path.join(phrases_path, midi_root + "_" + str(i) + ".mid")

        # Save midi chunk
        save_midi_slice(notes, midi_data.resolution, ch_midi_name)

        # Add split to the dataset
        with open(ch_midi_name, "rb") as midi_file:
            ch_key = hashlib.md5(midi_file.read()).hexdigest()

        if ch_key in annotated_data:
            print(ch_key, "is repeated")
            annotated_data[ch_key + str(i)] = {"id": piece_id,
                                             "part": i,
                                         "filepath": ch_midi_name,
                                            "label": annotated_data[ch_key]["label"],
                                           "repeat": annotated_data[ch_key]["part"]}
        else:
            annotated_data[ch_key] = {"id": piece_id,
                                         "part": i,
                                     "filepath": ch_midi_name,
                                        "label": phrase_label,
                                       "repeat": -1}

        slice_init += phrase_length

    return annotated_data.values()

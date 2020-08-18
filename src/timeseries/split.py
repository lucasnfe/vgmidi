import os
import hashlib
import pretty_midi
import numpy as np
from .tsmath import *

def emotion(v, a):
    emotion = np.array([0,0])

    if v >= 0:
        emotion[0] = 1
    if a >= 0:
        emotion[1] = 1

    return emotion

def slice_sequence_with_emotion(phrase, split_size):
    # Calculate step and make sure it is always greater or equal to 1
    step = max(1, len(phrase)//split_size)

    slices = []
    for i in range(0, len(phrase), step):
        sl = phrase[i:i+step]
        slices.append(sl)

    return slices

def split_annotation_by_emotion(valence, arousal, max_split=1):
    phrases = []
    ix = 0
    last_emotion = np.array([0,0])
    for v,a in zip(valence, arousal):
        current_emotion = emotion(v, a)
        if (current_emotion != last_emotion).all():
            phrases.append([current_emotion])
            if len(phrases) > 1:
                ix += 1
        else:
            if len(phrases) == 0:
                phrases.append([])

            phrases[ix].append(current_emotion)

        last_emotion = current_emotion

    # Augment data by including sub-sequences in the dataset
    labeled_phrases = []
    for phrase in phrases:
        split_size = 1
        while split_size <= max_split:
            slices = slice_sequence_with_emotion(phrase, split_size=split_size)
            labeled_phrases.append((split_size, slices))
            split_size <<= 1

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
        # phrase_valence, phrase_label = phrase
        phrase_valence = phrase[0][0]
        phrase_arousal = phrase[0][1]

        phrase_length = len(phrase)

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
                                            "valence": annotated_data[ch_key]["valence"],
                                            "arousal": annotated_data[ch_key]["arousal"],
                                           "repeat": annotated_data[ch_key]["part"]}
        else:
            annotated_data[ch_key] = {"id": piece_id,
                                         "part": i,
                                     "filepath": ch_midi_name,
                                        "valence": phrase_valence,
                                        "arousal": phrase_arousal,
                                       "repeat": -1}

        slice_init += phrase_length

    return list(annotated_data.values())

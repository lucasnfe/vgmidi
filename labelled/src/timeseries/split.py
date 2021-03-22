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

    last_emotion = emotion(0, 0)

    ix, chunks = 0, []
    for v,a in zip(valence, arousal):
        # Count ambiguous measures (have annotations "close" to zero.)
        if abs(v) < ambiguity_threshold:
            n_ambiguous_measures_valence += 1

        if abs(a) < ambiguity_threshold:
            n_ambiguous_measures_arousal += 1

        # Create emotion as numpy array
        current_emotion = emotion(v, a)

        if (current_emotion != last_emotion).any():
            chunks.append([current_emotion])
            if len(chunks) > 1:
                ix += 1
        else:
            if len(chunks) == 0:
                chunks.append([])

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

def split_midi(piece_id, midi_path, labeled_chunks, measure_length, phrases_path, slice_size=4, slice_length=2):
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

    # Start slice count
    slice_count = 0

    chunk_init = 0
    for chunk in labeled_chunks:
        chunk_size = len(chunk)

        if chunk_size < slice_size:
            continue

        # Get midi for this entire chunk
        chunk_start = (chunk_init * measure_length)
        chunk_end   = (chunk_init + chunk_size) * measure_length
        chunk_midi_data = slice_midi(midi_data, chunk_start, chunk_end)

        # Get valence of arousal of this chunk
        slice_valence = chunk[0][0]
        slice_arousal = chunk[0][1]

        # Split this chunk into "phrases" of the same length
        velocity, duration = None, None

        slice_init = 0
        for i in range(0, chunk_size, slice_size):
            # Slice midi given measure length in seconds
            slice_start = (slice_init * slice_length)
            slice_end   = (slice_init + slice_size) * slice_length
            slice_midi_data = slice_midi(chunk_midi_data, slice_start, slice_end)

            if get_midi_note_count(slice_midi_data) == 0:
                continue

            # Save midi chunk
            slice_name = os.path.join(phrases_path, midi_root + "_" + str(slice_count) + ".mid")
            slice_midi_data.write(slice_name)

            # Add split to the dataset
            with open(slice_name, "rb") as midi_file:
                ch_key = hashlib.md5(midi_file.read()).hexdigest()

            if ch_key not in annotated_data:
                annotated_data[ch_key] = {"id": id,
                                      "series": series,
                                     "console": console,
                                        "game": game,
                                       "piece": piece,
                                        "midi": slice_name,
                                     "valence": slice_valence,
                                     "arousal": slice_arousal}

                slice_count += 1
            else:
                print(ch_key, "is repeated")

            slice_init += slice_size

        chunk_init += chunk_size

    return list(annotated_data.values())

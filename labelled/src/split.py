import os
import hashlib
import pretty_midi
import numpy as np

MIN_PIECE_ID = 8000

def discretize_emotion(emotion, emotion_threshold, context):
    d_emotion = 0

    if emotion < -emotion_threshold:
        d_emotion = -1
    elif emotion > emotion_threshold:
        d_emotion = 1

    # Check context to solve ambiguity
    if d_emotion == 0:
        if len(context) > 0:
            d_emotion = max(set(context), key=context.count)
        else:
            if emotion < 0:
                d_emotion = -1
            elif emotion > 0:
                d_emotion = 1

    return d_emotion

def emotion(v, a, emotion_threshold, v_context=[], a_context=[]):
    v = discretize_emotion(v, emotion_threshold, v_context)
    a = discretize_emotion(a, emotion_threshold/2, a_context)
    return np.array([v, a])

def split_annotation_by_emotion(valence, arousal, ambiguity_threshold=0.0):
    last_emotion = None

    v_context = []
    a_context = []

    ix, chunks = -1, []
    for v,a in zip(valence, arousal):
        # Create emotion as numpy array
        current_emotion = emotion(v, a, ambiguity_threshold, v_context, a_context)

        if (current_emotion != last_emotion).any():
            chunks.append([current_emotion])
            ix += 1
        else:
            chunks[ix].append(current_emotion)

        if current_emotion[0] != 0:
            v_context.append(current_emotion[0])

        if current_emotion[1] != 0:
            a_context.append(current_emotion[1])

        last_emotion = current_emotion

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

    if len(notes) > 0:
        return create_midi_slice(notes, midi_data.resolution)

    return None

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
        if split_midi_data is None:
            print("Empty split!")
            continue

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

    return list(annotated_data.values())

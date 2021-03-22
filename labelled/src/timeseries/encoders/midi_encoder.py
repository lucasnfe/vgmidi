import os
import json
import argparse
import pretty_midi

MIN_NOTE_MULTIPLIER = 0.125
MIDI_EXTENSIONS = [".mid", ".midi"]

def load(datapath, pitch_range=(30, 96), velocity_range=(32, 127, 4), fs=1000, tempo=120, augmentation=(1, 1, 1)):
    vocab = set()

    if os.path.isfile(datapath):
        vocab = load_file(datapath, pitch_range, velocity_range, fs, tempo, augmentation)
    else:
        vocab = load_dir(datapath, pitch_range, velocity_range, fs, tempo, augmentation)

    return vocab

def load_dir(dirpath, pitch_range, velocity_range, fs, tempo, augmentation):
    vocab = set()

    for dir, _ , files in os.walk(dirpath):
        for i, f in enumerate(files):
            filepath = os.path.join(dir, f)

            file_vocab = load_file(filepath, pitch_range, velocity_range, fs, tempo, augmentation)
            vocab = vocab | file_vocab

    return vocab

def load_file(filepath, pitch_range, velocity_range, fs, tempo, augmentation):
    text = []

    # Check if it is a midi file
    filename, extension = os.path.splitext(filepath)
    if extension.lower() in MIDI_EXTENSIONS:
        print("Encoding file...", filepath)

        # If txt version of the midi already exists, load data from it
        if os.path.isfile(filename + ".txt"):
            with open(filename + ".txt", "r") as midi_txt:
                text = midi_txt.read().split(" ")
        else:
            try:
                midi_data = pretty_midi.PrettyMIDI(filepath)
            except KeyboardInterrupt:
                print("Exiting due to keyboard interrupt")
                quit()
            except:
                return set(text)

            text = midi2text(midi_data, pitch_range, velocity_range, fs, tempo, augmentation)
            with open(filename + ".txt", "w") as midi_txt:
                midi_txt.write(" ".join(text))

    return set(text)

def midi2text(midi_data, pitch_range, velocity_range, fs, tempo, augmentation):
    text = []

    # Parse notes and tempo changes from the midi data
    midi_notes = parse_notes_from_midi(midi_data, fs)

    transpose, time_stretch, velo_stretch = augmentation
    transpose_range    = (-transpose//2 + 1, transpose//2 + 1)
    time_stretch_range = (-time_stretch//2 + 1, time_stretch//2 + 1)
    velo_stretch_range = (-velo_stretch//2 + 1, velo_stretch//2 + 1)

    for i in range(transpose_range[0], transpose_range[1]):
        for j in range(time_stretch_range[0], time_stretch_range[1]):
            for k in range(velo_stretch_range[0], velo_stretch_range[1]):
                last_start = last_duration = last_velocity = 0;

                for start, time_step_notes in sorted(midi_notes.items()):
                    wait_duration = get_note_duration((start - last_start)/fs, tempo, stretch=j)
                    if wait_duration > 0:
                        if wait_duration != last_duration:
                            text.append("d_" + str(wait_duration))
                            last_duration = wait_duration

                        text.append(".")

                    for note in time_step_notes:
                        note_pitch  = clamp_pitch(note["pitch"] + i, pitch_range)
                        note_velocity = clamp_velocity(note["velocity"] + k * 8 * velocity_range[2], velocity_range)
                        note_duration = get_note_duration(note["duration"]/fs, tempo, stretch=j)

                        if note_velocity > 0 and note_duration > 0:
                            if note_velocity != last_velocity:
                                text.append("v_" + str(note_velocity))
                                last_velocity = note_velocity

                            if note_duration != last_duration:
                                text.append("d_" + str(note_duration))
                                last_duration = note_duration

                            text.append("n_" + str(note_pitch))

                    last_start = start

                text.append("\n")

    return text

def parse_notes_from_midi(midi_data, fs):
    notes = {}

    for instrument in midi_data.instruments:
        for note in instrument.notes:
            start, end = int(fs * note.start), int(fs * note.end)

            if start not in notes:
                notes[start] = []

            notes[start].append({
                "pitch": note.pitch,
             "duration": end - start,
             "velocity": note.velocity})

    return notes

def text2midi(text, tempo):
    notes = parse_notes_from_text(text, tempo)

    # Create a PrettyMIDI object
    midi = pretty_midi.PrettyMIDI(initial_tempo=tempo)

    # Create an Instrument instance for a piano instrument
    piano_program = pretty_midi.instrument_name_to_program('Acoustic Grand Piano')
    piano = pretty_midi.Instrument(program=piano_program)

    # Add notes
    for n in notes:
        piano.notes.append(n)

    midi.instruments.append(piano)

    return midi

def parse_notes_from_text(text, tempo):
    notes = []

    # Set default velocity
    velocity = 100

    # Compute duration of shortest note
    min_duration = MIN_NOTE_MULTIPLIER * 60/tempo

    i = 0
    for token in text.split(" "):
        if token[0] == ".":
            i += duration

        elif token[0] == "n":
            pitch = int(token.split("_")[1])
            note = pretty_midi.Note(velocity, pitch, start=i * min_duration, end=(i + duration) * min_duration)
            notes.append(note)

        elif token[0] == "d":
            duration = int(token.split("_")[1])

        elif token[0] == "v":
            velocity = int(token.split("_")[1])

    return notes

def clamp_velocity(velocity, velocity_range):
    min_velocity, max_velocity, step = velocity_range

    velocity = max(min(velocity, max_velocity), min_velocity)
    velocity = (velocity//step) * step

    return velocity

def clamp_pitch(pitch, pitch_range):
    min, max = pitch_range

    while pitch < min:
        pitch += 12
    while pitch >= max:
        pitch -= 12

    return pitch

def get_note_duration(dt, tempo, stretch=0, max_duration=56, percentage=0.15):
    min_duration = MIN_NOTE_MULTIPLIER * 60/tempo

    dt += dt * percentage * stretch

    # Compute how many 32th notes fit inside the given note
    note_duration = round(dt/min_duration)

    # Clamp note duration
    note_duration = min(note_duration, max_duration)

    return note_duration

def save_vocab(vocab, vocab_path):
    # Create dict to support char to index conversion
    char2idx = { char:i for i,char in enumerate(sorted(vocab)) }

    # Save char2idx encoding as a json file for generate midi later
    with open(vocab_path, "w") as f:
        json.dump(char2idx, f)

def write(text, path, tempo=120):
    midi = text2midi(text, tempo)
    midi.write(path)

if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser(description='midi_encoder.py')
    parser.add_argument('--midi',   type=str, required=True, help="Path to midi data.")
    parser.add_argument('--transp', type=int, default=1, help="Transpose range.")
    parser.add_argument('--tempo',   type=int, default=1, help="Time stretch range.")
    parser.add_argument('--vel',    type=int, default=1, help="Time stretch range.")
    parser.add_argument('--vocab',  type=str, required=True, help="Path to save vocab.")

    opt = parser.parse_args()

    # Load data and encoded it
    vocab = load(opt.midi, augmentation=(opt.transp, opt.tempo, opt.vel))

    # Save vocab as json file
    save_vocab(vocab, vocab_path=opt.vocab)

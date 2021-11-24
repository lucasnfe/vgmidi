import os
import csv
import shutil
import argparse
import unidecode
import pretty_midi

# Define min length in seconds for a midi file
MIN_LENGTH=15

# Games to remove from the unlabelled list. This is useful if you
# want to fine-tune a classifier with some part of the games
IGNORED_GAMES=["Banjo-Kazooie",
               "Banjo-Tooie",
               "Battle of Olympus",
               "Chrono Trigger",
               "Donkey Kong Country 2 Diddys Kong Quest",
               "Dragon Quest",
               "Final Fantasy VII",
               "Indiana Jones and the Fate of Atlantis",
               "Indiana Jones and the Last Crusade",
               "Secret of Mana",
               "GoldenEye 007",
               "Ghosts n Goblins",
               "Tetris",
               "Age of Empires II The Age of Kings",
               "Age of Empires",
               "Aion Tower of Eternity",
               "The Sims",
               "Warcraft II",
               "Warcraft III Reign of Chaos",
               "World of Warcraft Warlords of Draenor",
               "World of Warcraft Wrath of the Lich King",
               "Shadow of the Colossus",
               "Star Fox Adventures",
               "Star Fox",
               "Super Mario 64",
               "Super Mario Bros",
               "Super Mario World",
               "The Legend of Zelda Majoras Mask",
               "The Legend of Zelda Ocarina of Time",
               "Xenogears"]

# Parse arguments
parser = argparse.ArgumentParser(description='midi_clean.py')
parser.add_argument('--csv', type=str, required=True, help="Midi dataset.")
parser.add_argument('--out', type=str, required=True, help="Output dir.")
opt = parser.parse_args()

# Define csv header
cleaned_csv_columns = ['id','series','console', 'game', 'piece', 'midi', 'pdf']

# Cleaned csv name
cleaned_csv_filename = "vgmidi_metadata_cleaned.csv"
cleaned_csv_filename = os.path.join(opt.out, cleaned_csv_filename)

# Create set of ignored games
ingnored_games = set(IGNORED_GAMES)

# Create midi and pdf dirs
os.mkdir(os.path.join(opt.out, "midi"))
os.mkdir(os.path.join(opt.out, "pdf"))

total_piece, total_time = 0, 0
with open(cleaned_csv_filename, 'w') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=cleaned_csv_columns)
    writer.writeheader()

    for row in csv.DictReader(open(opt.csv, "r")):
        # Remove midi for two pianos and four hands
        if "Two Pianos" not in row['piece'] and "Four Hands" not in row['piece']:
            if row['game'] not in ingnored_games:
                print("Copying piece...", row['piece'])

                pdf_path = unidecode.unidecode(row['pdf'].split("/")[-1])
                midi_path = unidecode.unidecode(row['midi'].split("/")[-1])

                if os.path.isfile(row['pdf']) and os.path.isfile(row['midi']):
                    try:
                        # Get midi length in seconds
                        midi_data = pretty_midi.PrettyMIDI(row['midi'])
                    except:
                        print("----", "Midi file seems corruct.")
                        continue

                    # Check midi file has only piano tracks
                    non_piano_instruments = 0
                    for inst in midi_data.instruments:
                        # Only consider instruments from the piano family
                        if pretty_midi.program_to_instrument_class(inst.program) != "Piano":
                            non_piano_instruments += 1

                    if non_piano_instruments == 0:
                        # Check midi is not too short
                        midi_length = midi_data.get_end_time()

                        if midi_length > MIN_LENGTH:
                            shutil.copyfile(row['pdf'], os.path.join(opt.out, "pdf", pdf_path))
                            shutil.copyfile(row['midi'], os.path.join(opt.out, "midi", midi_path))

                            row['series'] = unidecode.unidecode(row['series'])
                            row['game'] = unidecode.unidecode(row['game'])
                            row['pdf'] = os.path.join(opt.out, "pdf", pdf_path)
                            row['midi'] = os.path.join(opt.out, "midi", midi_path)

                            writer.writerow(row)

                            # Compute stats
                            total_piece += 1
                            total_time  += midi_data.get_end_time()
                        else:
                            print("----", "Midi file is too short.")
                    else:
                        print("----", "Midi file has non-piano instruments.")
                else:
                    print("----", "Either midi of pdf do not exist.")

print("Total pieces:", total_piece)
print("Total time (in seconds):", total_time)

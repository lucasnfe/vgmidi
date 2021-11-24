import os
import re
import ssl
import csv
import unidecode
import urllib.request
import argparse

from bs4 import BeautifulSoup

MIDI_EXTENSIONS = [".mid", ".midi", ".MID", ".MIDI"]

def clean_name(name, invalid_chars=[":", "_", ".", "~", "'", '"', "/"]):
    # Remove invalid chars
    valid_name = ''.join(c for c in name if c not in invalid_chars)
    valid_name_and_spaces = " ".join(valid_name.split())

    # Get ascii encoding
    ascii_encoding = unidecode.unidecode(valid_name_and_spaces)

    return ascii_encoding

def get_series_metadata(series_url):
    print("Parsing...", series_url)
    games = {}

    # Download html from game url
    context = ssl._create_unverified_context()
    with urllib.request.urlopen(series_url, context=context) as response:
        game_html = response.read()

    # Parse game html
    game_soup = BeautifulSoup(game_html, features="html.parser")

    # Get list of all games
    games_list = game_soup.find_all("section", {"class": "game"})

    # Get all games in html
    for divtag in games_list:
        # Get game name
        game_name = divtag.find("div", {"class": "heading-text"}).find("h3").string

        # Get console name
        console_name = divtag.find("div", {"class": "gameInfo"}).find("li").find("a").get("title")

        # Get midis from that game
        game_metadata = divtag.find("ul", {"class": "tableList"})

        for litag in game_metadata.find_all("li", {"class": "tableList-row--sheet"}):
            midi_id = litag.get("id").split("sheet")[-1]
            midi_name = litag.find("div", {"class": "tableList-cell--sheetTitle"}).string

            pdf_url = litag.find("a", {"class": "tableList-buttonCell--sheetPdf"}).get("href")
            midi_url = litag.find("a", {"class": "tableList-buttonCell--sheetMid"}).get("href")

            games[midi_id] = {"console": clean_name(console_name),
                                 "game": clean_name(game_name),
                                "piece": clean_name(midi_name),
                              "pdf_url": opt.url + pdf_url,
                             "midi_url": opt.url + midi_url }

    return games

# Parse arguments
parser = argparse.ArgumentParser(description='midi_download.py')
parser.add_argument('--url', type=str, required=True, help="URL to download files from.")
parser.add_argument('--out', type=str, default=".", help="Output dir.")
parser.set_defaults(local=False)
opt = parser.parse_args()

# Download html from url
context = ssl._create_unverified_context()
with urllib.request.urlopen(opt.url + "/browse/series", context=context) as response:
    html = response.read()

# Create parser from html
soup = BeautifulSoup(html, features="html.parser")

# Create csv file
csv_columns = ['id','series','console', 'game', 'piece', 'midi', 'pdf']

# Get list of all game series
series_list = soup.find("ul", {"class": "browseCategoryList"})

# Parse each game series
all_games = []
for litag in series_list.find_all('a'):
    series_url = opt.url + litag.get('href')
    series_name = clean_name(litag.string)
    series_games = get_series_metadata(series_url)

    for id, metadata in series_games.items():
        print(id)
        print(metadata)

        # Define local filename
        local_filename = series_name + "_" + metadata["console"] + "_" + metadata["game"] + "_" + metadata["piece"]

        pdf_filename = os.path.join(opt.out, "pdf", local_filename + ".pdf")
        midi_filename = os.path.join(opt.out, "midi", local_filename + ".mid")

        try:
            # Download pdf file
            with urllib.request.urlopen(metadata["pdf_url"], context=context) as response:
                with open(pdf_filename, "wb") as fp:
                    fp.write(response.read())

            # Download midi file
            with urllib.request.urlopen(metadata["midi_url"], context=context) as response:
                with open(midi_filename, "wb") as fp:
                    fp.write(response.read())

            # Include in the final dict
            all_games.append({'id': id,
                          'series': series_name,
                         'console': metadata["console"],
                            'game': metadata["game"],
                           'piece': metadata["piece"],
                            'midi': midi_filename,
                             'pdf': pdf_filename})
        except:
            print("Could not download file.")

        print("==========")

csv_filename = "vgmidi_metadata.csv"
csv_filename = os.path.join(opt.out, csv_filename)

with open(csv_filename, 'w') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
    writer.writeheader()

    for data in all_games:
        writer.writerow(data)

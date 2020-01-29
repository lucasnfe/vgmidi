import json

data = json.loads(open("../data/adl-music-annotation.json").read())

age, gender, musicianship = {}, {}, {}

for ann in data["annotations"]:
    piece_ann = data["annotations"][ann]

    if piece_ann["gender"] not in gender:
        gender[piece_ann["gender"]] = 0
    gender[piece_ann["gender"]] += 1

    if piece_ann["age"] not in age:
        age[piece_ann["age"]] = 0
    age[piece_ann["age"]] += 1

    if piece_ann["musicianship"] not in musicianship:
        musicianship[piece_ann["musicianship"]] = 0
    musicianship[piece_ann["musicianship"]] += 1

age = {k: v/len(data["annotations"]) for k,v in age.items()}
gender = {k: v/len(data["annotations"]) for k,v in gender.items()}
musicianship = {k: v/len(data["annotations"]) for k,v in musicianship.items()}

print(age)
print(gender)
print(musicianship)

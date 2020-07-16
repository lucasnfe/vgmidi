# VGMIDI Dataset

VGMIDI is a dataset of 200 MIDI labelled piano pieces (966 phrases of 4 bars) and 728 non-labelled ones, all
piano arrangements of video game soundtracks. Each piece was annotated by 30 human subjects according to a
valence-arousal (dimensional) model of emotion. The sentiment of each piece was then extracted by summarizing
the 30 annotations and mapping the valence axis to sentiment.

## Data Annotation

We designed a custom web tool to annotate the video game soundtracks in MIDI format. The source code for this tool
can be found [here](https://github.com/lucasnfe/adl-music-annotation) and the details on the annotation process can be found in [this paper](http://www.lucasnferreira.com/papers/2019/ismir-learning.pdf).

## Citing this Dataset

This dataset was presented in [this paper](http://www.lucasnferreira.com/papers/2019/ismir-learning.pdf), so if you use it, please cite:

```
@article{ferreira_ismir_2019,
  title={Learning to Generate Music with Sentiment},
  author={Ferreira, Lucas N. and Whitehead, Jim},
  booktitle = {Proceedings of the Conference of the International Society for Music Information Retrieval},
  series = {ISMIR'19},
  year={2019},
}
```

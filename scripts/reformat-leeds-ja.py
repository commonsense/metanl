from metanl import japanese
from metanl.leeds_corpus_reader import translate_leeds_corpus

translate_leeds_corpus('../metanl/data/source-data/internet-ja-forms.num',
    '../metanl/data/leeds-internet-ja.txt', japanese.normalize)

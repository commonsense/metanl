from metanl import euro
from metanl.leeds_corpus_reader import translate_leeds_corpus

for language in euro.languages:
    translate_leeds_corpus(
        '../metanl/data/source-data/internet-%s-forms.num' % language,
        '../metanl/data/leeds-internet-%s.txt' % language,
        euro.languages[language].normalize
    )


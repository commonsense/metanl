from metanl import freeling
from metanl.leeds_corpus_reader import translate_leeds_corpus

for language in freeling.languages:
    if language != 'cy':
        # we don't have data for Welsh
        print language
        translate_leeds_corpus(
            '../metanl/data/source-data/internet-%s-forms.num' % language,
            '../metanl/data/leeds-internet-%s.txt' % language,
            freeling.languages[language].normalize
        )


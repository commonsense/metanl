from metanl import freeling
from metanl.leeds_corpus_reader import translate_leeds_corpus

for language in freeling.LANGUAGES:
    if language != 'cy' and language != 'en':
        # we don't have data for Welsh, and we have better data for English
        print language
        translate_leeds_corpus(
            '../metanl/data/source-data/internet-%s-forms.num' % language,
            '../metanl/data/wordlists/leeds-internet-%s.txt' % language,
            freeling.LANGUAGES[language].normalize
        )


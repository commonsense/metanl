from metanl.leeds_corpus_reader import translate_leeds_corpus
import socket, time

def make_rosette_normalizer(lcode):
    from lumi_pipeline.text_readers import get_reader
    reader = get_reader('rosette.%s' % lcode)
    def normalizer(text):
        try:
            triples = reader.text_to_token_triples(text)
        except socket.error:
            time.sleep(1)
            print 'backing off'
            return normalizer(text)
        normalized = u' '.join(lemma for lemma, pos, token in triples)
        return normalized
    return normalizer

def main():
    for language in ('pt', 'ru', 'es', 'fr', 'it'):
        print language
        translate_leeds_corpus(
            '../metanl/data/source-data/internet-%s-forms.num' % language,
            '../metanl/data/wordlists/leeds-internet-%s.txt' % language,
            make_rosette_normalizer(language)
        )

if __name__ == '__main__':
    main()

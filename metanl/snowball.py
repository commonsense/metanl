# -*- coding: utf-8 -*-
"""
This module provides NLP functions for various European languages using the
Snowball stemmer. The supported languages are identified in
MetaSnowball.LANGUAGES by their ISO language code:

- es: Spanish
- fr: French
- it: Italian
- pt: Portuguese

These are also made available as the objects `spanish`, `french`, etc.

Stemming is provided by the Snowball stemmer, a generalization of the Porter
stemmer. This means that the normalized text will be mangled to the point where
it is difficult to recognize, and may conflate unrelated stems.

>>> print spanish.normalize(u'esta es una prueba')
esta es prueb
"""

from metanl.general import (preprocess_text, tokenize_list, untokenize_list)
from metanl.wordlist import Wordlist

class MetaSnowball(object):
    LANGUAGES = ['es', 'fr', 'it', 'pt']
    STOPWORDS_BY_LANG = {
        'es': ['el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'a', 'al'],
        'fr': ['la', 'le', 'l', 'les', 'un', 'une', 'à', 'au', 'aux'],

        # The polysemy of words such as 'degli' (plural indefinite article, or
        # contraction of 'di' and a definite article) requires us to use a
        # slightly larger stopword list in Italian:
        'it': [
            # definite articles
            'il', 'lo', 'la', 'le', 'i', 'gli', 'l',
            # singular indefinite articles
            'un', 'uno', 'una',
            # preposition 'to' and its contractions
            'a', 'al', 'allo', 'all', 'àlla', 'ai', 'agli', 'alle',
            # preposition 'of' and its contractions
            'd', 'di', 'del', 'dello', 'dell', 'della', 'dei', 'degli', 'delle',
        ],
        'pt': [
            # definite articles
            'a', 'o', 'as', 'os',
            # indefinite aricles
            'um', 'uma',
            # contractions of 'to', which is already included as 'a':
            'à', 'ao', 'às', 'aos',
        ],
    }
    def __init__(self, lang):
        assert lang in self.LANGUAGES
        self.lang = lang
        self.stopwords = self.STOPWORDS_BY_LANG[lang]

    @property
    def stemmer(self):
        if not hasattr(self, '_stemmer'):
            from Stemmer import Stemmer
            self._stemmer = Stemmer(self.lang)
        return self._stemmer

    def snowball_stem(self, word):
        return self.stemmer.stemWord(word.strip("'").lower())

    def good_lemma(self, word):
        word = word.strip("'").lower()
        return word and word not in self.stopwords and word[0].isalnum()

    def is_stopword(self, word):
        return not self.good_lemma(word)

    def normalize_list(self, text):
        """
        Get a list of word stems that appear in the text. Stopwords and an initial
        'to' will be stripped.
        """
        pieces = [self.snowball_stem(word) for word in tokenize_list(text) if self.good_lemma(word)]
        if not pieces:
            return text
        return pieces

    def normalize(self, text):
        """
        Get a string made from the non-stopword word stems in the text. See
        normalize_list().
        """
        return untokenize_list(self.normalize_list(text))

    def word_frequency(self, word, default_freq=0):
        """
        Looks up the word's frequency in the Leeds Internet corpus for the
        appropriate language.

        FIXME: this returns 0 for words that stem differently in FreeLing when
        we use FreeLing frequencies, and that's most of the words
        """
        freqs = Wordlist.load('leeds-internet-%s.txt' % self.lang)
        word = self.snowball_stem(word)
        if " " in word:
            raise ValueError("word_frequency only can only look up single words, but %r contains a space" % word)
        word = preprocess_text(word.strip("'")).lower()
        return freqs.get(word, default_freq)

languages = {}
french = languages['fr'] = MetaSnowball('fr')
spanish = languages['es'] = MetaSnowball('es')
italian = languages['it'] = MetaSnowball('it')
portuguese = languages['pt'] = MetaSnowball('pt')

if __name__ == '__main__':
    # put nifty demo here
    pass


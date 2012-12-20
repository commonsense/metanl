# -*- coding: utf-8 -*-
u"""
This module provides some basic Japanese NLP by wrapping the output of MeCab.
It can tokenize and normalize Japanese words, detect and remove stopwords,
and it can even respell words in kana or romaji.

This requires mecab to be installed separately. On Ubuntu:
    sudo apt-get install mecab mecab-ipadic-utf8

>>> print normalize(u'これはテストです')
テスト
>>> tag_and_stem(u'これはテストです。')
[(u'\\u3053\\u308c', 'STOP', u'\\u3053\\u308c'), (u'\\u306f', 'STOP', u'\\u306f'), (u'\\u30c6\\u30b9\\u30c8', 'TERM', u'\\u30c6\\u30b9\\u30c8'), (u'\\u3067\\u3059', 'STOP', u'\\u3067\\u3059'), (u'\\u3002', '.', u'\\u3002')]
"""

from metanl.general import preprocess_text, untokenize
from metanl.wordlist import Wordlist, get_frequency
from metanl.extprocess import ProcessWrapper, ProcessError
import unicodedata


class MeCabError(ProcessError):
    pass


# MeCab outputs the part of speech of its terms. We can simply identify
# particular (coarse or fine) parts of speech as containing stopwords.

STOPWORD_CATEGORIES = set([
    u'助詞',          # coarse: particle
    u'連体詞',        # coarse: adnominal adjective ("rentaishi")
    u'助動詞',        # coarse: auxiliary verb
    u'接続詞',        # coarse: conjunction
    u'フィラー',      # coarse: filler
    u'記号',          # coarse: symbol
    u'助詞類接続',    # fine: particle connection
    u'代名詞',        # fine: pronoun
    u'接尾',          # fine: suffix
])


# Forms of particular words should also be considered stopwords sometimes.
#
# A thought: Should the rare kanji version of suru not be a stopword?
# I'll need to ask someone who knows more Japanese, but it may be
# that if they're using the kanji it's for particular emphasis.
STOPWORD_ROOTS = set([
    u'する',          # suru: "to do"
    u'為る',          # suru in kanji (very rare)
    u'くる',          # kuru: "to come"
    u'来る',          # kuru in kanji
    u'いく',          # iku: "to go"
    u'行く',          # iku in kanji
    u'もの',          # mono: "thing"
    u'物',            # mono in kanji
    u'よう',          # yō: "way"
    u'様',            # yō in kanji
])


class MeCabWrapper(ProcessWrapper):
    """
    Handle Japanese text using the command-line version of MeCab.
    (mecab-python is convenient, but its installer is too flaky to rely on.)

    ja_cabocha gives more sophisticated results, but requires a large number of
    additional dependencies. Using this tool for Japanese requires only
    MeCab to be installed and accepting UTF-8 text.
    """
    def _get_command(self):
        return ['mecab']

    def _get_process(self):
        try:
            proc = ProcessWrapper._get_process(self)
        except (OSError, ProcessError):
            raise MeCabError("MeCab didn't start. See README.txt for details "
                             "about installing MeCab and other Japanese NLP tools.")
        self.mecab_encoding = self._detect_mecab_encoding(proc)
        return proc

    def _detect_mecab_encoding(self, proc):
        """
        Once we've found a MeCab binary, it may be installed in UTF-8 or it
        may be installed in EUC-JP. We need to determine which one by
        experimentation.
        """
        proc.stdin.write(u'a\n')
        out = proc.stdout.readline()

        # out is now a string in an unknown encoding, and might not even be
        # valid in *any* encoding before the tab character. But after the
        # tab, it should all be in the encoding of the installed dictionary.
        encoding = 'utf-8'
        try:
            out.decode('utf-8')
        except UnicodeDecodeError:
            try:
                out.decode('euc-jp')
                encoding = 'euc-jp'
            except UnicodeDecodeError:
                raise MeCabError("I can't understand MeCab in either UTF-8 or "
                                 "EUC-JP. Check the configuration of MeCab and "
                                 "its dictionary.")
        if proc.stdout.readline() != 'EOS\n':
            raise MeCabError("Sorry! I got unexpected lines back from MeCab "
                             "and don't know what to do next.")
        return encoding

    def get_record_root(self, record):
        """
        Given a MeCab record, return the root word.
        """
        if record[7] == '*':
            return record[0]
        else:
            return record[7]

    def get_record_token(self, record):
        return record[0]

    def analyze(self, text):
        """
        Runs a line of text through MeCab, and returns the results as a
        list of lists ("records") that contain the MeCab analysis of each
        word.
        """
        try:
            self.process  # make sure things are loaded
            text = preprocess_text(text).lower()
            n_chunks = (len(text) + 1024) // 1024
            results = []
            for chunk in xrange(n_chunks):
                chunk_text = text[chunk*1024:(chunk+1)*1024].encode(self.mecab_encoding)
                self.send_input(chunk_text+'\n')
                #self.input_log.write(text+'\n')
                out_line = ''
                while True:
                    out_line = self.receive_output_line()
                    #self.output_log.write(out_line)
                    out_line = out_line.decode(self.mecab_encoding)

                    if out_line == u'EOS\n':
                        break

                    word, info = out_line.strip(u'\n').split(u'\t')
                    record = [word] + info.split(u',')

                    # special case for detecting nai -> n
                    if record[0] == u'ん' and record[5] == u'不変化型':
                        record[7] = record[1] = u'ない'

                    results.append(record)
            return results
        except ProcessError:
            self.restart_process()
            return self.analyze(text)

    def is_stopword_record(self, record, common_words=False):
        """
        Determine whether a single MeCab record represents a stopword.

        By default this only strips out particles and auxiliary verbs,
        but if common_words is set to True it will also strip common verbs
        and nouns such as くる and よう.
        """
        # preserve negations
        if record[7] == u'ない':
            return False
        return (record[1] in STOPWORD_CATEGORIES or
                record[2] in STOPWORD_CATEGORIES or
                (common_words and record[7] in STOPWORD_ROOTS))

class NoStopwordMeCabWrapper(MeCabWrapper):
    """
    This version of the MeCabWrapper doesn't label anything as a stopword. It'
    used in building ConceptNet because discarding stopwords based on MeCab
    categories loses too much information.
    """
    def is_stopword_record(self, record, common_words=False):
        return False


def word_frequency(word, default_freq=0):
    """
    Looks up the word's frequency in the Leeds Internet Japanese corpus.
    """
    return get_frequency(word, 'ja', default_freq)


def get_wordlist():
    return Wordlist.load('leeds-internet-ja.txt')


# Define the classes of characters we'll be trying to transliterate
NOT_KANA, KANA, NN, SMALL, SMALL_Y, SMALL_TSU, PROLONG = range(7)

def to_kana(text):
    """
    Use MeCab to turn any text into its phonetic spelling, as katakana
    separated by spaces.
    """
    records = MECAB.analyze(text)
    kana = []
    for record in records:
        if len(record) > 9:
            kana.append(record[9])
        elif len(record) > 8:
            kana.append(record[8])
        else:
            kana.append(record[0])
    return ' '.join(k for k in kana if k)


def get_kana_info(char):
    """
    Return two things about each character:

    - Its transliterated value (in Roman characters, if it's a kana)
    - A class of characters indicating how it affects the romanization
    """
    try:
        name = unicodedata.name(char)
    except ValueError:
        return char, NOT_KANA

    # The names we're dealing with will probably look like
    # "KATAKANA CHARACTER ZI".
    if (name.startswith('HIRAGANA LETTER') or name.startswith('KATAKANA LETTER')
    or name.startswith('KATAKANA-HIRAGANA')):
        names = name.split()
        syllable = unicode(names[-1].lower())

        if name.endswith('SMALL TU'):
            # The small tsu (っ) doubles the following consonant.
            # It'll show up as 't' on its own.
            return u't', SMALL_TSU
        elif names[-1] == 'N':
            return u'n', NN
        elif names[1] == 'PROLONGED':
            # The prolongation marker doubles the previous vowel.
            # It'll show up as '_' on its own.
            return u'_', PROLONG
        elif names[-2] == 'SMALL':
            # Small characters tend to modify the sound of the previous
            # kana. If they can't modify anything, they're appended to
            # the letter 'x' instead.
            if syllable.startswith('y'):
                return u'x' + syllable, SMALL_Y
            else:
                return u'x' + syllable, SMALL

        return syllable, KANA
    else:
        if char in ROMAN_PUNCTUATION_TABLE:
            char = ROMAN_PUNCTUATION_TABLE[char]
        return char, NOT_KANA


def respell_hepburn(syllable):
    while syllable[:2] in HEPBURN_TABLE:
        syllable = HEPBURN_TABLE[syllable[:2]] + syllable[2:]
    return syllable


def romanize(text, respell=respell_hepburn):
    if respell is None:
        respell = lambda x: x

    kana = to_kana(unicode(text))
    pieces = []
    prevgroup = NOT_KANA

    for char in kana:
        roman, group = get_kana_info(char)
        if prevgroup == NN:
            # When the previous syllable is 'n' and the next syllable would
            # make it ambiguous, add an apostrophe.
            if group != KANA or roman[0] in 'aeinouy':
                if unicodedata.category(roman[0])[0] == 'L':
                    pieces[-1] += "'"

        # Determine how to spell the current character
        if group == NOT_KANA:
            pieces.append(roman)
        elif group == SMALL_TSU or group == NN:
            pieces.append(roman)
        elif group == SMALL_Y:
            if prevgroup == KANA:
                # Modify the previous syllable, if that makes sense. For example,
                # 'ni' + 'ya' becomes 'nya'.
                if not pieces[-1].endswith('i'):
                    pieces.append(roman)
                else:
                    modifier = roman[1:]
                    modified = pieces[-1]
                    pieces[-1] = modified[:-1] + modifier
            else:
                pieces.append(roman)
        elif group == SMALL:
            # We don't respell other kinds of small vowels, because the result would
            # be ambiguous. The word for "tea", which is "te" + small "i", will show
            # up as "texi", which is what you'd type into a word processor anyway.
            pieces.append(roman)
        elif group == PROLONG:
            if prevgroup in (KANA, SMALL_Y, SMALL):
                pieces[-1] = pieces[-1][:-1] + respell(pieces[-1][-1] + '_')
            else:
                pieces.append(roman)
        else:  # this is a normal kana
            if prevgroup == SMALL_TSU:
                if roman[0] in 'aeiouy':
                    # wait, there's no consonant there; cope by respelling the
                    # previous kana as 'xtu'
                    pieces[-1] = 'xtu'
                else:
                    # Turn the previous 't' into a copy of the first consonant
                    pieces[-1] = roman[0]
            elif prevgroup == NN:
                # Let Hepburn respell 'n' as 'm' in words such as 'shimbun'.
                try_respell = respell(pieces[-1] + roman[0])
                if try_respell[:-1] != pieces[-1]:
                    pieces[-1] = try_respell[:-1]
            pieces.append(roman)
        prevgroup = group

    return untokenize(u''.join(respell(piece) for piece in pieces))


# Hepburn romanization is the most familiar to English speakers. It involves
# respelling certain parts of romanized words to better match their
# pronunciation. For example, the name for Mount Fuji is respelled from
# "huzi-san" to "fuji-san".
HEPBURN_TABLE = {
    u'si': u'shi',
    u'sy': u'sh',
    u'ti': u'chi',
    u'ty': u'ch',
    u'tu': u'tsu',
    u'hu': u'fu',
    u'zi': u'ji',
    u'di': u'ji',
    u'zy': u'j',
    u'dy': u'j',
    u'nm': u'mm',
    u'nb': u'mb',
    u'np': u'mp',
    u'a_': u'aa',
    u'e_': u'ee',
    u'i_': u'ii',
    u'o_': u'ou',
    u'u_': u'uu'
}
ROMAN_PUNCTUATION_TABLE = {
    u'・': u'.',
    u'。': u'.',
    u'、': u',',
    u'！': u'!',
    u'「': u'``',
    u'」': u"''",
    u'？': u'?',
    u'〜': u'~'
}

# Provide externally available functions.
MECAB = MeCabWrapper()

normalize = MECAB.normalize
normalize_list = MECAB.normalize_list
tokenize = MECAB.tokenize
tokenize_list = MECAB.tokenize_list
analyze = MECAB.analyze
tag_and_stem = MECAB.tag_and_stem
is_stopword = MECAB.is_stopword

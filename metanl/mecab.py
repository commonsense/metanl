# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
"""
This module provides some basic Japanese NLP by wrapping the output of MeCab.
It can tokenize and normalize Japanese words, detect and remove stopwords,
and it can even respell words in kana or romaji.

This requires mecab to be installed separately. On Ubuntu:
    sudo apt-get install mecab mecab-ipadic-utf8

>>> print(normalize('これはテストです'))
テスト
>>> tag_and_stem('これはテストです。')
[('\u3053\u308c', '~\u540d\u8a5e', '\u3053\u308c'), ('\u306f', '~\u52a9\u8a5e', '\u306f'), ('\u30c6\u30b9\u30c8', '\u540d\u8a5e', '\u30c6\u30b9\u30c8'), ('\u3067\u3059', '~\u52a9\u52d5\u8a5e', '\u3067\u3059'), ('\u3002', '.', '\u3002')]
"""

from metanl.token_utils import string_pieces
from metanl.extprocess import ProcessWrapper, ProcessError, render_safe
from collections import namedtuple
import unicodedata
import re
import sys
if sys.version_info.major == 2:
    range = xrange
    str_func = unicode
else:
    str_func = str


class MeCabError(ProcessError):
    pass

MeCabRecord = namedtuple('MeCabRecord',
    [
        'surface',
        'pos',
        'subclass1',
        'subclass2',
        'subclass3',
        'conjugation',
        'form',
        'root',
        'reading',
        'pronunciation'
    ]
)


# MeCab outputs the part of speech of its terms. We can simply identify
# particular (coarse or fine) parts of speech as containing stopwords.

STOPWORD_CATEGORIES = set([
    '助詞',          # coarse: particle
    '助動詞',        # coarse: auxiliary verb
    '接続詞',        # coarse: conjunction
    'フィラー',      # coarse: filler
    '記号',          # coarse: symbol
    '非自立',        # fine: 'not independent'
])


# Forms of particular words should also be considered stopwords sometimes.
#
# A thought: Should the rare kanji version of suru not be a stopword?
# I'll need to ask someone who knows more Japanese, but it may be
# that if they're using the kanji it's for particular emphasis.
STOPWORD_ROOTS = set([
    'する',          # suru: "to do"
    '為る',          # suru in kanji (very rare)
    'くる',          # kuru: "to come"
    '来る',          # kuru in kanji
    'いく',          # iku: "to go"
    '行く',          # iku in kanji
    'いる',          # iru: "to be" (animate)
    '居る',          # iru in kanji
    'ある',          # aru: "to exist" or "to have"
    '有る',          # aru in kanji
    'もの',          # mono: "thing"
    '物',            # mono in kanji
    'よう',          # yō: "way"
    '様',            # yō in kanji
    'れる',          # passive suffix
    'これ',          # kore: "this"
    'それ',          # sore: "that"
    'あれ',          # are: "that over there"
    'この',          # kono: "this"
    'その',          # sono: "that"
    'あの',          # ano: "that over there", "yon"
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
                             "about installing MeCab and other Japanese NLP "
                             "tools.")
        return proc

    def get_record_root(self, record):
        """
        Given a MeCab record, return the root word.
        """
        if record.root == '*':
            return record.surface
        else:
            return record.root

    def get_record_token(self, record):
        return record.surface

    def analyze(self, text):
        """
        Runs a line of text through MeCab, and returns the results as a
        list of lists ("records") that contain the MeCab analysis of each
        word.
        """
        try:
            self.process  # make sure things are loaded
            text = render_safe(text).replace('\n', ' ').lower()
            results = []
            for chunk in string_pieces(text):
                self.send_input((chunk + '\n').encode('utf-8'))
                while True:
                    out_line = self.receive_output_line().decode('utf-8')
                    if out_line == 'EOS\n':
                        break

                    word, info = out_line.strip('\n').split('\t')
                    record_parts = [word] + info.split(',')

                    # Pad the record out to have 10 parts if it doesn't
                    record_parts += [None] * (10 - len(record_parts))
                    record = MeCabRecord(*record_parts)

                    # special case for detecting nai -> n
                    if (record.surface == 'ん' and
                        record.conjugation == '不変化型'):
                        # rebuild the record so that record.root is 'nai'
                        record_parts[MeCabRecord._fields.index('root')] = 'ない'
                        record = MeCabRecord(*record_parts)

                    results.append(record)
            return results
        except ProcessError:
            self.restart_process()
            return self.analyze(text)

    def is_stopword_record(self, record):
        """
        Determine whether a single MeCab record represents a stopword.

        This mostly determines words to strip based on their parts of speech.
        If common_words is set to True (default), it will also strip common
        verbs and nouns such as くる and よう. If more_stopwords is True, it
        will look at the sub-part of speech to remove more categories.
        """
        # preserve negations
        if record.root == 'ない':
            return False
        return (
            record.pos in STOPWORD_CATEGORIES or
            record.subclass1 in STOPWORD_CATEGORIES or
            record.root in STOPWORD_ROOTS
        )

    def get_record_pos(self, record):
        """
        Given a record, get the word's part of speech.

        Here we're going to return MeCab's part of speech (written in
        Japanese), though if it's a stopword we prefix the part of speech
        with '~'.
        """
        if self.is_stopword_record(record):
            return '~' + record.pos
        else:
            return record.pos


class NoStopwordMeCabWrapper(MeCabWrapper):
    """
    This version of the MeCabWrapper doesn't label anything as a stopword. It's
    used in building ConceptNet because discarding stopwords based on MeCab
    categories loses too much information.
    """
    def is_stopword_record(self, record, common_words=False):
        return False


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
        if record.pronunciation:
            kana.append(record.pronunciation)
        elif record.reading:
            kana.append(record.reading)
        else:
            kana.append(record.surface)
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
    if (name.startswith('HIRAGANA LETTER') or
        name.startswith('KATAKANA LETTER') or
        name.startswith('KATAKANA-HIRAGANA')):
        names = name.split()
        syllable = str_func(names[-1].lower())

        if name.endswith('SMALL TU'):
            # The small tsu (っ) doubles the following consonant.
            # It'll show up as 't' on its own.
            return 't', SMALL_TSU
        elif names[-1] == 'N':
            return 'n', NN
        elif names[1] == 'PROLONGED':
            # The prolongation marker doubles the previous vowel.
            # It'll show up as '_' on its own.
            return '_', PROLONG
        elif names[-2] == 'SMALL':
            # Small characters tend to modify the sound of the previous
            # kana. If they can't modify anything, they're appended to
            # the letter 'x' instead.
            if syllable.startswith('y'):
                return 'x' + syllable, SMALL_Y
            else:
                return 'x' + syllable, SMALL

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

    kana = to_kana(str_func(text))
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
                # Modify the previous syllable, if that makes sense. For
                # example, 'ni' + 'ya' becomes 'nya'.
                if not pieces[-1].endswith('i'):
                    pieces.append(roman)
                else:
                    modifier = roman[1:]
                    modified = pieces[-1]
                    pieces[-1] = modified[:-1] + modifier
            else:
                pieces.append(roman)
        elif group == SMALL:
            # Don't respell small vowels _yet_. We'll handle that at the end.
            # This may be a bit ambiguous, but nobody expects to see "tea"
            # spelled "texi".
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
                    # previous kana as 't-'
                    pieces[-1] = 't-'
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

    romantext = ''.join(respell(piece) for piece in pieces)
    romantext = re.sub(r'[aeiou]x([aeiou])', r'\1', romantext)
    return romantext


# Hepburn romanization is the most familiar to English speakers. It involves
# respelling certain parts of romanized words to better match their
# pronunciation. For example, the name for Mount Fuji is respelled from
# "huzi-san" to "fuji-san".
HEPBURN_TABLE = {
    'si': 'shi',
    'sy': 'sh',
    'ti': 'chi',
    'ty': 'ch',
    'tu': 'tsu',
    'hu': 'fu',
    'zi': 'ji',
    'di': 'ji',
    'zy': 'j',
    'dy': 'j',
    'nm': 'mm',
    'nb': 'mb',
    'np': 'mp',
    'a_': 'aa',
    'e_': 'ee',
    'i_': 'ii',
    'o_': 'ou',
    'u_': 'uu'
}
ROMAN_PUNCTUATION_TABLE = {
    '・': '.',
    '。': '.',
    '、': ',',
    '！': '!',
    '「': '``',
    '」': "''",
    '？': '?',
    '〜': '~'
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

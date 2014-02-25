# coding: utf-8
from __future__ import unicode_literals
"""
This file contains some generally useful operations you would perform to
separate and join tokens. The tools apply most to English, but should also
be able to do their job in any Western language that uses spaces.
"""

import re
import unicodedata


def tokenize(text):
    """
    Split a text into tokens (words, morphemes we can separate such as
    "n't", and punctuation).
    """
    return list(_tokenize_gen(text))


def _tokenize_gen(text):
    import nltk
    for sent in nltk.sent_tokenize(text):
        for word in nltk.word_tokenize(sent):
            yield word


def untokenize(words):
    """
    Untokenizing a text undoes the tokenizing operation, restoring
    punctuation and spaces to the places that people expect them to be.

    Ideally, `untokenize(tokenize(text))` should be identical to `text`,
    except for line breaks.
    """
    text = ' '.join(words)
    step1 = text.replace("`` ", '"').replace(" ''", '"').replace('. . .', '...')
    step2 = step1.replace(" ( ", " (").replace(" ) ", ") ")
    step3 = re.sub(r' ([.,:;?!%]+)([ \'"`])', r"\1\2", step2)
    step4 = re.sub(r' ([.,:;?!%]+)$', r"\1", step3)
    step5 = step4.replace(" '", "'").replace(" n't", "n't").replace(
        "can not", "cannot")
    step6 = step5.replace(" ` ", " '")
    return step6.strip()


# This expression scans through a reversed string to find segments of
# camel-cased text. Comments show what these mean, forwards, in preference
# order:
CAMEL_RE = re.compile(r"""
    ^( [A-Z]+                 # A string of all caps, such as an acronym
     | [^A-Z0-9 _]+[A-Z _]    # A single capital letter followed by lowercase
                              #   letters, or lowercase letters on their own
                              #   after a word break
     | [^A-Z0-9 _]*[0-9.]+    # A number, possibly followed by lowercase
                              #   letters
     | [ _]+                  # Extra word breaks (spaces or underscores)
     | [^A-Z0-9]*[^A-Z0-9_ ]+ # Miscellaneous symbols, possibly with lowercase
                              #   letters after them
     )
""", re.VERBOSE)


def un_camel_case(text):
    r"""
    Splits apart words that are written in CamelCase.

    Bugs:

    - Non-ASCII characters are treated as lowercase letters, even if they are
      actually capital letters.

    Examples:

    >>> un_camel_case('1984ZXSpectrumGames')
    '1984 ZX Spectrum Games'

    >>> un_camel_case('aaAa aaAaA 0aA  AAAa!AAA')
    'aa Aa aa Aa A 0a A AA Aa! AAA'

    >>> un_camel_case('MotörHead')
    'Mot\xf6r Head'

    >>> un_camel_case('MSWindows3.11ForWorkgroups')
    'MS Windows 3.11 For Workgroups'

    This should not significantly affect text that is not camel-cased:

    >>> un_camel_case('ACM_Computing_Classification_System')
    'ACM Computing Classification System'

    >>> un_camel_case('Anne_Blunt,_15th_Baroness_Wentworth')
    'Anne Blunt, 15th Baroness Wentworth'

    >>> un_camel_case('Hindi-Urdu')
    'Hindi-Urdu'
    """
    revtext = text[::-1]
    pieces = []
    while revtext:
        match = CAMEL_RE.match(revtext)
        if match:
            pieces.append(match.group(1))
            revtext = revtext[match.end():]
        else:
            pieces.append(revtext)
            revtext = ''
    revstr = ' '.join(piece.strip(' _') for piece in pieces
                      if piece.strip(' _'))
    return revstr[::-1].replace('- ', '-')


# see http://www.fileformat.info/info/unicode/category/index.htm
BOUNDARY_CATEGORIES = {'Cc',  # control characters
                       'Cf',  # format characters
                       'Cn',  # "other, not assigned"
                       'Pc',  # connector punctuation
                       'Pd',  # dash
                       'Pe',  # close-punctuation
                       'Pf',  # final-quote
                       'Pi',  # initial-quote
                       'Po',  # other punctuation
                       'Zl',  # line separator
                       'Zp',  # paragraph separator
                       'Zs',  # space separator
                       }

def string_pieces(s, maxlen=1024):
    """
    Takes a (unicode) string and yields pieces of it that are at most `maxlen`
    characters, trying to break it at punctuation/whitespace. This is an
    important step before using a tokenizer with a maximum buffer size.
    """
    if not s:
        return
    i = 0
    while True:
        j = i + maxlen
        if j >= len(s):
            yield s[i:]
            return
        # Using "j - 1" keeps boundary characters with the left chunk
        while unicodedata.category(s[j - 1]) not in BOUNDARY_CATEGORIES:
            j -= 1
            if j == i:
                # No boundary available; oh well.
                j = i + maxlen
                break
        yield s[i:j]
        i = j


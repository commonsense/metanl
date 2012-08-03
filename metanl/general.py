# -*- coding: utf-8 -*-
"""
Useful NLP functions that are not language-specific.
"""

import re
import unicodedata

TOKENIZER_REGEXES = [
    # transform quotation marks
    ('"([^"]*)"', r" `` \1 '' "),
    # sequences of punctuation
    (r'([.,:;^_*?!%()\[\]{}][-.,:;^_*?!%()\[\]{}]*) ', r" \1 "),
    # final sequences of punctuation
    (r'([.,:;^_*?!%()\[\]{}][-.,:;^_*?!%()\[\]{}]*)$', r" \1"),
    # word-preceding punctuation
    (r'([*$({\[]+)(\w)', r"\1 \2"),
    # ellipses
    (r'(\.\.+)(\w)', r" \1 \2"),
    # long dashes
    (r'(--+)(\w)', r" \1 \2"),
    # ending punctuation + parentheses
    (r' ([.?!])([()\[\]{}])', r" \1 \2"),
    # squish extra spaces
    (r'  +', ' ')]

COMPILED_TOKENIZER_REGEXES = [(re.compile(regex), replacement)
                              for regex, replacement in TOKENIZER_REGEXES]

# Make a mapping from control characters to reasonable things.
CONTROL_CHARS = {}
for i in xrange(256):
    if unicodedata.category(unichr(i)) == 'Cc':
        CONTROL_CHARS[i] = None

CONTROL_CHARS[ord('\t')] = u' '
CONTROL_CHARS[ord('\n')] = u' '

def preprocess_text(text):
    """
    Given any basestring as input, make its representation consistent:

    - Ensure that it is a Unicode string, converting from UTF-8 if
      necessary.
    - Detect whether the text was incorrectly encoded into UTF-8 and fix it,
      as defined in `fix_bad_unicode`.
    - Normalize it with Unicode normalization form KC, which applies the
      following relevant transformations:
      - Combine characters and diacritics that are written using separate
        code points, such as converting "e" plus an acute accent modifier
        into "é", or converting "ka" (か) plus a dakuten into the
        single character "ga" (が).
      - Replace characters that are functionally equivalent with the most
        common form: for example, half-width katakana will be replaced with
        full-width, and full-width Roman characters will be replaced with
        ASCII characters.
    - Replace newlines and tabs with spaces.
    - Remove all other control characters.
    """
    text = fix_bad_unicode(text)
    return unicodedata.normalize('NFKC', text.translate(CONTROL_CHARS))

def tokenize(text):
    r"""
    Tokenizing a sentence inserts spaces in such a way that it separates
    punctuation from words, splits up contractions, and generally does what
    a lot of natural language tools (especially parsers) expect their
    input to do.

    This is derived from the Treebank tokenization process, but we add rules
    that keep together symbols such as smileys and complex punctuation.

        >>> tokenize("Time is an illusion. Lunchtime, doubly so.")
        u'Time is an illusion . Lunchtime , doubly so .'
        >>> untok = '''
        ... "Very deep," said Arthur, "you should send that in to the
        ... Reader's Digest. They've got a page for people like you."
        ... '''
        >>> tok = tokenize(untok)
        >>> tok
        u"`` Very deep , '' said Arthur , `` you should send that in to the Reader 's Digest . They 've got a page for people like you . ''"
        >>> untokenize(tok)
        u'"Very deep," said Arthur, "you should send that in to the Reader\'s Digest. They\'ve got a page for people like you."'
        >>> untokenize(tok) == untok.replace('\n', ' ').strip()
        True
    """
    step0 = preprocess_text(text).replace('\r', '').replace('\n', ' ')
    cur = step0.replace(" '", " ` ").replace("'", " '").replace("n 't",
    " n't").replace("cannot", "can not")
    for regex, replacement in COMPILED_TOKENIZER_REGEXES:
        cur = regex.sub(replacement, cur)
    return cur.strip()

def tokenize_list(text):
    """
    Take text and split it into a list of tokens, as defined by `tokenize`.
    We recommend using this instead of `tokenize` itself, because lists are
    more sensible things to work with than space-separated string pieces.
    """
    return tokenize(text).split()

def untokenize(text):
    """
    Untokenizing a text undoes the tokenizing operation, restoring
    punctuation and spaces to the places that people expect them to be.

    Ideally, `untokenize(tokenize(text))` should be identical to `text`,
    except for line breaks.
    """
    step1 = text.replace("`` ", '"').replace(" ''", '"')
    step2 = step1.replace(" ( ", " (").replace(" ) ", ") ")
    step3 = re.sub(r' ([.,:;?!%]+)([ \'"`])', r"\1\2", step2)
    step4 = re.sub(r' ([.,:;?!%]+)$', r"\1", step3)
    step5 = step4.replace(" '", "'").replace(" n't", "n't").replace(
      "can not", "cannot")
    step6 = step5.replace(" ` ", " '")
    return step6.strip()

def untokenize_list(words):
    return untokenize(' '.join(words))

# This expression scans through a reversed string to find segments of
# camel-cased text. Comments show what these mean, forwards, in preference
# order:
CAMEL_RE = re.compile(ur"""
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
    ur"""
    Splits apart words that are written in CamelCase.

    Bugs:

    - Non-ASCII characters are treated as lowercase letters, even if they are
      actually capital letters.

    Examples:

    >>> un_camel_case('1984ZXSpectrumGames')
    '1984 ZX Spectrum Games'

    >>> un_camel_case('aaAa aaAaA 0aA  AAAa!AAA')
    'aa Aa aa Aa A 0a A AA Aa! AAA'

    >>> un_camel_case(u'MotörHead')
    u'Mot\xf6r Head'

    >>> un_camel_case(u'MSWindows3.11ForWorkgroups')
    u'MS Windows 3.11 For Workgroups'
    
    This should not significantly affect text that is not camel-cased:
    
    >>> un_camel_case('ACM_Computing_Classification_System')
    'ACM Computing Classification System'
    
    >>> un_camel_case(u'Anne_Blunt,_15th_Baroness_Wentworth')
    u'Anne Blunt, 15th Baroness Wentworth'

    >>> un_camel_case(u'Hindi-Urdu')
    u'Hindi-Urdu'
    """
    revtext = text[::-1]
    pieces = []
    while revtext:
        match = CAMEL_RE.match(revtext)
        if match:
            pieces.append(match.group(1))
            revtext = revtext[match.end():]
        else:
            print revtext
            pieces.append(revtext)
            revtext = ''
    revstr = ' '.join(piece.strip(' _') for piece in pieces if piece.strip(' _'))
    return revstr[::-1].replace('- ', '-')

def asciify(text):
    u"""
    Remove accents from characters, and discard other non-ASCII characters.
    Outputs a plain ASCII string. Use responsibly.

    >>> print asciify(u'ædœomycodermis')
    aedoeomycodermis

    >>> print asciify('Zürich')
    Zurich

    >>> print asciify(u'-نہیں')
    -

    """
    if not isinstance(text, unicode):
        text = text.decode('utf-8', 'ignore')
    # Deal with annoying British vowel ligatures
    text = fix_bad_unicode(text)
    text = text.replace(u'Æ', 'AE').replace(u'Œ', 'OE')\
               .replace(u'æ', 'ae').replace(u'œ', 'oe')
    return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore')

CP1252_GREMLINS = u''.join([
    # from http://www.microsoft.com/typography/unicode/1252.htm
    # adapted from http://effbot.org/zone/unicode-gremlins.htm
    u"\u20AC", # EURO SIGN
    u"\u201A", # SINGLE LOW-9 QUOTATION MARK
    u"\u0192", # LATIN SMALL LETTER F WITH HOOK
    u"\u201E", # DOUBLE LOW-9 QUOTATION MARK
    u"\u2020", # DAGGER
    u"\u2021", # DOUBLE DAGGER
    u"\u02C6", # MODIFIER LETTER CIRCUMFLEX ACCENT
    u"\u2030", # PER MILLE SIGN
    u"\u0160", # LATIN CAPITAL LETTER S WITH CARON
    u"\u2039", # SINGLE LEFT-POINTING ANGLE QUOTATION MARK
    u"\u0152", # LATIN CAPITAL LIGATURE OE
    u"\u017D", # LATIN CAPITAL LETTER Z WITH CARON
    u"\u2022", # BULLET
    u"\u02DC", # SMALL TILDE
    u"\u0161", # LATIN SMALL LETTER S WITH CARON
    u"\u0153", # LATIN SMALL LIGATURE OE
    u"\u017E", # LATIN SMALL LETTER Z WITH CARON
    u"\u0178", # LATIN CAPITAL LETTER Y WITH DIAERESIS
])

CP1252_MORE_GREMLINS = u''.join([
    u"\u2026", # HORIZONTAL ELLIPSIS
    u"\u2018", # LEFT SINGLE QUOTATION MARK
    u"\u2019", # RIGHT SINGLE QUOTATION MARK
    u"\u201C", # LEFT DOUBLE QUOTATION MARK
    u"\u201D", # RIGHT DOUBLE QUOTATION MARK
    u"\u2013", # EN DASH
    u"\u2014", # EM DASH
    u"\u2122", # TRADE MARK SIGN
    u"\u203A", # SINGLE RIGHT-POINTING ANGLE QUOTATION MARK
])

PAIRS_START = u''.join(unichr(x) for x in xrange(194, 224))
PAIRS_SAFE_START = u''.join(unichr(x) for x in xrange(195, 202))
PAIRS_REST = u''.join(unichr(x) for x in xrange(128, 192))

TRIPLES_START = u''.join(unichr(x) for x in xrange(225, 240))
TRIPLES_HIGH_SECOND = u''.join(unichr(x) for x in xrange(160, 192))
TRIPLES_REST = u''.join(unichr(x) for x in xrange(128, 192))

TRIPLES_WITH_GREMLINS = TRIPLES_REST + CP1252_GREMLINS

BAD_UNICODE_SEQUENCES = [
    u'[%s][%s]' % (PAIRS_START, PAIRS_REST),
    u'[%s][%s]' % (PAIRS_SAFE_START, PAIRS_REST + CP1252_GREMLINS),
    u'\xc3[%s]' % (PAIRS_REST + CP1252_GREMLINS + CP1252_MORE_GREMLINS),
    u'[%s][%s][%s]' % (TRIPLES_START, TRIPLES_REST, TRIPLES_REST),
    u'\xe0[%s][%s]' % (TRIPLES_HIGH_SECOND, TRIPLES_REST),
    u'\xe2[%s][%s]' % (TRIPLES_WITH_GREMLINS,
        TRIPLES_WITH_GREMLINS + CP1252_MORE_GREMLINS),
]
BAD_UNICODE_REGEX = u'(' + (u'|'.join(BAD_UNICODE_SEQUENCES)) + u')'
BAD_UNICODE_RE = re.compile(BAD_UNICODE_REGEX)

def fix_bad_unicode(text):
    u"""
    Something you will find all over the place, in real-world text, is text
    that's mistakenly encoded as utf-8, decoded in some ugly format like
    latin-1 or even Windows codepage 1252, and encoded as utf-8 again.
    
    This causes your perfectly good Unicode-aware code to end up with garbage
    text because someone else (or maybe "someone else") made a mistake.

    This function looks for the evidence of that having happened and fixes it.
    It searches for the nonsense character sequences that are incorrect latin-1
    representations of all UTF-8 characters in the Basic Multilingual Plane,
    and replaces them with the Unicode character they were clearly meant to
    represent.

    Do not ever run binary data through this function.

        >>> print fix_bad_unicode(u'Ãºnico')
        único

        >>> print fix_bad_unicode(u'This text is fine already :þ')
        This text is fine already :þ

    Because these characters often come from Microsoft products, we also allow
    for the possibility that we get not just Unicode characters 128-255, but
    also Windows's conflicting idea of what characters 128-160 are. However,
    because some pairs of these characters are actually useful, we only correct
    them in sets of three or more.

        >>> print fix_bad_unicode(u'This â€” should be an em dash')
        This — should be an em dash
    
    This even fixes multiple levels of badness:

        >>> print fix_bad_unicode(u'what the f\xc3\x83\xc2\x85\xc3\x82\xc2\xb1ck')
        what the fűck
    """
    # Astute observers will recognize that this makes certain character
    # sequences impossible to encode. I can say with confidence that currently,
    # 100% of these character sequences that appear in text are actually
    # mis-encoded. But we don't know how language will be used in the future,
    # so this code is not necessarily future-proof.
    #
    # In particular: If, in the future, the Euro collapses, and Germany and the
    # UK then form their own monetary union and introduce a currency called the
    # Deutschpound (Ð£), this function will be erroneous.
    #
    # *Particularly* astute observers will notice that this function would also
    # erroneously encode its own documentation and test cases.

    # Make sure we're dealing with Unicode. Decode it from utf-8 if not.
    if isinstance(text, str):
        remaining = text.decode('utf-8', 'replace')
    else:
        remaining = text

    # Collect chunks of text with Unicode glitches fixed. If there were no
    # glitches in the first place, great, there will only be one chunk.
    chunks = []
    while remaining:
        match = BAD_UNICODE_RE.search(remaining)
        if match:
            before = remaining[0:match.start()]
            to_fix = remaining[match.start():match.end()]
            try:
                # We found some tell-tale nonsense! First get the bytes that
                # result from encoding them as latin-1.
                encoded = to_fix.encode('latin-1')
            except UnicodeEncodeError:
                # As we've seen, some nonsense characters you come across
                # aren't even in latin-1. They've been run through a Microsoft
                # product, so they're instead in Windows codepage 1252. That's
                # where you get stuff like the euro and trademark sign.
                encoded = to_fix.encode('cp1252')
            
            fixed = encoded.decode('utf-8')
            chunks.extend([before, fixed])
            remaining = remaining[match.end():]
        else:
            chunks.append(remaining)
            remaining = ''
    result = u''.join(chunks)

    # Check the result to make sure we have no glitches left. If we do, then
    # the text was probably incorrectly encoded *twice*, so we run the function
    # again recursively.
    if BAD_UNICODE_RE.search(result):
        return fix_bad_unicode(result)
    return result

def unicode_is_punctuation(text):
    u"""
    Test if a token is made entirely of Unicode characters of the following
    classes:

    - P: punctuation
    - S: symbols
    - Z: separators
    - M: combining marks
    - C: control characters

    >>> unicode_is_punctuation(u'word')
    False
    >>> unicode_is_punctuation(u'。')
    True
    >>> unicode_is_punctuation(u'-')
    True
    >>> unicode_is_punctuation(u'-3')
    False
    >>> unicode_is_punctuation(u'あ')
    False
    """
    for char in unicode(text):
        category = unicodedata.category(char)[0]
        if category not in 'PSZMC':
            return False
    return True


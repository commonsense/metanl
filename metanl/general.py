# -*- coding: utf-8 -*-
"""
Useful NLP functions that are not language-specific.
"""

import re
import unicodedata
import htmlentitydefs
from ftfy import fix_bad_encoding, fix_text
fix_bad_unicode = fix_bad_encoding

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
    - Replace HTML entities with their equivalent characters.
    - Replace newlines and tabs with spaces.
    - Remove all other control characters.
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
    """
    if isinstance(text, str):
        text = text.decode('utf-8')
    text = fix_bad_unicode(text)
    text = unescape_html(text)
    text = text.translate(CONTROL_CHARS)
    return unicodedata.normalize('NFKC', text)

HTML_ENTITY_RE = re.compile("&#?\w+;")
def unescape_html(text):
    """
    Decode all three types of HTML entities/character references.

    Code by Fredrik Lundh of effbot.org.
    """
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text  # leave as is
    return HTML_ENTITY_RE.sub(fixup, text)

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
    step1 = text.replace("`` ", '"').replace(" ''", '"').replace('. . .', '...')
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
    text = preprocess_text(text)
    text = text.replace(u'Æ', 'AE').replace(u'Œ', 'OE')\
               .replace(u'æ', 'ae').replace(u'œ', 'oe')
    return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore')

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


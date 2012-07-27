# -*- coding: utf-8 -*-
import re
import unicodedata

tokenizer_regexes = [
    ('"([^"]*)"', r" `` \1 '' "),         # transform quotation marks
    (r'([.,:;^_*?!%()\[\]{}][-.,:;^_*?!%()\[\]{}]*) ', r" \1 "),  # sequences of punctuation
    (r'([.,:;^_*?!%()\[\]{}][-.,:;^_*?!%()\[\]{}]*)$', r" \1"),   # final sequences of punctuation
    (r'([*$({\[]+)(\w)', r"\1 \2"),          # word-preceding punctuation
    (r'(\.\.+)(\w)', r" \1 \2"),          # ellipses
    (r'(--+)(\w)', r" \1 \2"),            # long dashes
    (r' ([.?!])([()\[\]{}])', r" \1 \2"),   # ending punctuation + parentheses
    (r'  +', ' ')]                        # squish extra spaces

compiled_tokenizer_regexes = [(re.compile(regex), replacement)
                              for regex, replacement in tokenizer_regexes]

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
    - Normalize it with Unicode normalization form KC, which applies the
      following relevant transformations:
      - Combines characters and diacritics that are written using separate
        code points, such as converting "e" plus an acute accent modifier
        into "é", or converting "ka" (か) plus a dakuten into the
        single character "ga" (が).
      - Replaces characters that are functionally equivalent with the most
        common form: for example, half-width katakana will be replaced with
        full-width, and full-width Roman characters will be replaced with
        ASCII characters.
    - Replace newlines and tabs with spaces.
    - Remove all other control characters.
    """
    if isinstance(text, str):
        text = text.decode('utf-8', 'replace')
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
    for regex, replacement in compiled_tokenizer_regexes:
        cur = regex.sub(replacement, cur)
    return cur.strip()

def tokenize_list(text):
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

def un_camel_case(text):
    u"""
    Splits apart words that are written in CamelCase.

    Bugs:

    - When a word begins with a digit, this splits off the numeric part as
      a separate word. This may not be what is desired.
    - Non-ASCII characters are treated as lowercase letters, even if they are
      actually capital letters.

    Examples:

    >>> un_camel_case('1984ZXSpectrumGames')
    '1984 ZX Spectrum Games'

    >>> un_camel_case('aaAa aaAaA 0aA AAAa!AAA')
    'aa Aa aa Aa A 0 a A AA Aa! AAA'

    >>> un_camel_case(u'MotörHead')
    u'Mot\xf6r Head'

    This should not significantly affect text that is not camel-cased:
    
    >>> un_camel_case('ACM_Computing_Classification_System')
    'ACM Computing Classification System'
    
    >>> un_camel_case(u'Anne_Blunt,_15th_Baroness_Wentworth')
    u'Anne Blunt, 15 th Baroness Wentworth'

    >>> un_camel_case(u'Hindi-Urdu')
    u'Hindi-Urdu'
    """
    revtext = text[::-1]
    pieces = []
    while revtext:
        match = re.match(ur'^([A-Z]+|[^A-Z0-9 _]+[A-Z _]|[0-9]+|[ _]+|[^A-Z0-9]*[^A-Z0-9_ ]+)(.*)$', revtext)
        if match:
            pieces.append(match.group(1))
            revtext = match.group(2)
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


pairs_1 = u''.join(unichr(x) for x in xrange(194, 224))
pairs_2 = u''.join(unichr(x) for x in xrange(128, 192))

triples_1 = u''.join(unichr(x) for x in xrange(224, 240))
triples_2 = u''.join(unichr(x) for x in xrange(160, 192))
triples_3 = u''.join(unichr(x) for x in xrange(128, 192))

BAD_UNICODE_RE = re.compile(u'([%s][%s]|[%s][%s][%s])' % (pairs_1, pairs_2,
    triples_1, triples_2, triples_3))

def fix_bad_unicode(text):
    u"""
    Something you will find all over the place, in real-world text, is text
    that's mistakenly encoded as utf-8, decoded as latin-1, and encoded as
    utf-8 again. This causes your perfectly good Unicode-aware code to end up
    with garbage text because someone else screwed up.

    This function looks for the evidence of that having happened and fixes it,
    by looking for the latin-1 representations of all utf-8 characters in the
    Basic Multilingual Plane and replacing them with the Unicode character they
    were clearly meant to represent.

    Astute observers will recognize that this makes certain character sequences
    impossible to encode. I can say with confidence that currently, 100% of
    these character sequences that appear in text are actually mis-encoded. But
    we don't know how language will be used in the future, so this code is not
    necessarily future-proof.
    
    In particular: If, in the future, the Euro collapses, and Germany and the
    UK then form their own monetary union and introduce a currency called the
    Deutschpound (Ð£), this function will be erroneous.

    *Particularly* astute observers will notice that this function would also
    erroneously encode its own documentation.

    Do not ever run binary data through this function.

    >>> print fix_bad_unicode(u'Ãºnico')
    único

    >>> print fix_bad_unicode(u'This text is fine already :þ')
    This text is fine already :þ
    
    This even fixes multiple levels of badness:

    >>> print fix_bad_unicode(u'what the f\xc3\x83\xc2\x85\xc3\x82\xc2\xb1ck')
    what the fűck
    """
    if isinstance(text, str):
        remaining = text.decode('utf-8', errors='replace')
    else:
        remaining = text
    chunks = []
    while remaining:
        match = BAD_UNICODE_RE.search(remaining)
        if match:
            before = remaining[0:match.start()]
            fixed = remaining[match.start():match.end()].encode('latin-1').decode('utf-8')
            chunks.extend([before, fixed])
            remaining = remaining[match.end():]
        else:
            chunks.append(remaining)
            remaining = ''
    result = u''.join(chunks)
    if BAD_UNICODE_RE.search(result):
        return fix_bad_unicode(result)
    return result




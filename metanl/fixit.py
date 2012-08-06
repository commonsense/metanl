# -*- coding: utf-8 -*-
"""
This module deals with bad text, and aims to turn it into less-bad text.

The interesting function in it is fix_bad_unicode, which corrects for two ugly
things that unaware programs can do to Unicode text; see its documentation for
details.
"""
import re

# Start with an inventory of "gremlins", which are characters from all over
# Unicode that Windows has instead assigned to the control characters
# 0x80-0x9F. We might encounter them in their Unicode forms and have to figure
# out what they were originally.

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

# We've separated out these characters because they are actually punctuation
# that could occur after, say, an accented letter. They appear in combinations
# that could be intentional and meaningful, or could be misinterpretations of
# other Unicode characters in UTF-8. So we treat them with caution, and only
# convert them in one situation where they are very unilkely to be intentional.

CP1252_MORE_GREMLINS = CP1252_GREMLINS + (u''.join([
    u"\u2026", # HORIZONTAL ELLIPSIS
    u"\u2018", # LEFT SINGLE QUOTATION MARK
    u"\u2019", # RIGHT SINGLE QUOTATION MARK
    u"\u201C", # LEFT DOUBLE QUOTATION MARK
    u"\u201D", # RIGHT DOUBLE QUOTATION MARK
    u"\u2013", # EN DASH
    u"\u2014", # EM DASH
    u"\u2122", # TRADE MARK SIGN
    u"\u203A", # SINGLE RIGHT-POINTING ANGLE QUOTATION MARK
]))

# PAIRS_START contains the Latin-1 characters that are the first bytes of all
# possible two-byte UTF-8 characters.
PAIRS_START = u''.join(unichr(x) for x in xrange(0xc2, 0xe0))

# PAIRS_SAFE_START contains Latin-1 characters that are the first bytes of
# *very common* UTF-8 characters. We'll allow converting these when they appear
# next to one of the more obscure gremlins.
PAIRS_SAFE_START = u''.join(unichr(x) for x in xrange(0xc3, 0xca))

# PAIRS_REST contains Latin-1 characters that are valid second bytes of UTF-8
# characters.
PAIRS_REST = u''.join(unichr(x) for x in xrange(0x80, 0xc0))

# TRIPLES_START cointains Latin-1 characters that are valid first bytes of
# three-byte UTF-8 characters.
TRIPLES_START = u''.join(unichr(x) for x in xrange(0xe1, 0xf0))

# TRIPLES_REST contains the valid second and third bytes.
TRIPLES_REST = u''.join(unichr(x) for x in xrange(0x80, 0xc0))

# TRIPLES_HIGH_SECOND contains the valid second bytes that can appear after the
# byte 0xe0; any lower bytes than that would be invalid UTF-8.
TRIPLES_HIGH_SECOND = u''.join(unichr(x) for x in xrange(0xa0, 0xc0))

# Make a list of regexes representing sequences that we want to correct.
BAD_UNICODE_SEQUENCES = [
    u'[%s][%s]' % (PAIRS_START, PAIRS_REST),
    u'[%s][%s]' % (PAIRS_SAFE_START, CP1252_GREMLINS),
    u'\xc3[%s]' % (PAIRS_REST + CP1252_MORE_GREMLINS),
    u'[%s][%s][%s]' % (TRIPLES_START, TRIPLES_REST, TRIPLES_REST),
    u'\xe0[%s][%s]' % (TRIPLES_HIGH_SECOND, TRIPLES_REST),
    u'\xe2[%s][%s]' % (TRIPLES_REST + CP1252_GREMLINS,
        TRIPLES_REST + CP1252_MORE_GREMLINS),
]

# Join them all together into one big ugly regex, and compile it.
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

    We might have to deal with both Windows characters and raw control
    characters at the same time, especially when dealing with characters like
    \x81 that have no mapping in Windows.

        >>> print fix_bad_unicode(u'This text is sad â\x81”..')
        This text is sad ⁔..
    
    This function even fixes multiple levels of badness:

        >>> print fix_bad_unicode(u'what the f\xc3\x83\xc2\x85\xc3\x82\xc2\xb1ck')
        what the fűck
    """
    # Astute observers will recognize that this makes certain character
    # sequences impossible to encode. This function takes various steps to make
    # sure that it's not destroying meaningful sequences of characters. But we
    # don't know how language will be used in the future, so this code is not
    # necessarily future-proof.
    #
    # For example: If, in the future, the Euro collapses, and Germany and the
    # UK then form their own monetary union and introduce a currency called the
    # Deutschpound (Ð£), this function will be erroneous.
    #
    # Particularly astute observers will notice that this function would also
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
                encoded = recode_from_windows(to_fix).encode('latin-1')
            
            # Now that we've identified the nonsense and gotten the bytes out
            # of it, decode those bytes as UTF-8 to get the character they were
            # probably supposed to be.
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

def recode_from_windows(text):
    """
    Take the high-unicode "gremlin" characters that show up as a result of
    decoding Windows CP1252, and replace them with their equivalent characters
    between 0x80 and 0x9F, which is what they would be if decoded as Latin-1.
    """
    chars = []
    for char in text:
        if char in CP1252_MORE_GREMLINS:
            chars.append(char.encode('cp1252').decode('latin-1'))
        else:
            chars.append(char)
    return u''.join(chars)

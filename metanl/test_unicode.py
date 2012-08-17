# -*- coding: utf-8 -*-
from metanl.fixit import fix_bad_unicode

def test_all_bmp_characters():
    for index in xrange(0, 65535):
        garble = unichr(index).encode('utf-8').decode('latin-1')
        assert fix_bad_unicode(garble) == unichr(index)

def test_valid_phrases():
    phrases = [
        u"\u201CI'm not such a fan of Charlotte Brontë\u2026\u201D",
        u"\u201CI'm not such a fan of Charlotte Brontë\u2026\u201D",
        u"\u2039ALLÍ ESTÁ\u203A",
        u"\u2014ALLÍ ESTÁ\u2014",
        u"I want to buy an Ikea sofa with a name like ÅBBÅ™\u2026",
        u"\u2014radius of 10 Å\u2014",
        u"MY CHARACTER IS NAMED ÉŸ OF THE NIGHTFALL",
    ]
    for phrase in phrases:
        assert fix_bad_unicode(phrase) == phrase


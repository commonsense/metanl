# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from metanl.token_utils import (tokenize, untokenize, un_camel_case,
                                string_pieces)
from nose.tools import eq_
import nltk

def test_tokenize():
    # a snippet from Hitchhiker's Guide that just happens to have
    # most of the examples of punctuation we're looking for.
    #
    # TODO: test wacky behavior with "n't" and "cannot" and stuff.
    text1 = "Time is an illusion. Lunchtime, doubly so."
    text2 = ('"Very deep," said Arthur, "you should send that in to the '
             'Reader\'s Digest. They\'ve got a page for people like you."')
    eq_(tokenize(text1),
        ['Time', 'is', 'an', 'illusion', '.', 'Lunchtime', ',',
         'doubly', 'so', '.']
    )
    eq_(untokenize(tokenize(text1)), text1)
    if nltk.__version__ >= '3':
        eq_(untokenize(tokenize(text2)), text2)

def test_camel_case():
    eq_(un_camel_case('1984ZXSpectrumGames'), '1984 ZX Spectrum Games')
    eq_(un_camel_case('aaAa aaAaA 0aA AAAa!AAA'),
        'aa Aa aa Aa A 0a A AA Aa! AAA')
    eq_(un_camel_case('MotörHead'),
        'Mot\xf6r Head')
    eq_(un_camel_case('MSWindows3.11ForWorkgroups'),
        'MS Windows 3.11 For Workgroups')

    # This should not significantly affect text that is not camel-cased
    eq_(un_camel_case('ACM_Computing_Classification_System'),
        'ACM Computing Classification System')
    eq_(un_camel_case('Anne_Blunt,_15th_Baroness_Wentworth'),
        'Anne Blunt, 15th Baroness Wentworth')
    eq_(un_camel_case('Hindi-Urdu'),
        'Hindi-Urdu')


def test_string_pieces():
    # Break as close to whitespace as possible
    text = "12 12 12345 123456 1234567-12345678"
    eq_(list(string_pieces(text, 6)),
        ['12 12 ', '12345 ', '123456', ' ', '123456', '7-', '123456', '78'])

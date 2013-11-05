# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from metanl.general import un_camel_case
from nose.tools import eq_


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

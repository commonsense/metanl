# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from metanl.freeling import english, spanish
from metanl.mecab import normalize, tag_and_stem
from metanl.extprocess import unicode_is_punctuation
from nose.tools import eq_


def test_english():
    test_text = "This is a test.\n\nIt has two paragraphs, and that's okay."
    expected_result = [('this', 'DT', 'This'), ('be', 'VBZ', 'is'),
                       ('a', 'DT', 'a'), ('test', 'NN', 'test'),
                       ('.', '.', '.'), ('it', 'PRP', 'It'),
                       ('have', 'VBZ', 'has'), ('two', 'DT', 'two'),
                       ('paragraph', 'NNS', 'paragraphs'), (',', '.', ','),
                       ('and', 'CC', 'and'), ('that', 'PRP', 'that'),
                       ('be', 'VBZ', "'s"), ('okay', 'JJ', 'okay'),
                       ('.', '.', '.')]
    eq_(english.tag_and_stem(test_text), expected_result)

    test_text = "this has\ntwo lines"
    expected_result = [('this', 'DT', 'this'), ('have', 'VBZ', 'has'),
                       ('two', 'DT', 'two'), ('line', 'NNS', 'lines')]
    eq_(english.tag_and_stem(test_text), expected_result)
        

def test_spanish():
    # Spanish works, even with a lot of unicode characters
    test_text = '¿Dónde está mi búfalo?'
    expected_result = [('¿', '.', '¿'),
                       ('dónde', 'P', 'Dónde'),
                       ('estar', 'V', 'está'),
                       ('mi', 'D', 'mi'),
                       ('búfalo', 'N', 'búfalo'),
                       ('?', '.', '?')]
    eq_(spanish.tag_and_stem(test_text), expected_result)


def test_japanese():
    eq_(normalize('これはテストです'), 'テスト')
    this_is_a_test = [('これ', 'STOP', 'これ'),
                      ('は', 'STOP', 'は'),
                      ('テスト', '名詞', 'テスト'),
                      ('です', 'STOP', 'です'),
                      ('。', '.', '。')]
    eq_(tag_and_stem('これはテストです。'), this_is_a_test)


def test_unicode_is_punctuation():
    assert unicode_is_punctuation('word') is False
    assert unicode_is_punctuation('。') is True
    assert unicode_is_punctuation('-') is True
    assert unicode_is_punctuation('-3') is False
    assert unicode_is_punctuation('あ') is False

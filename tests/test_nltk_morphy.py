from __future__ import unicode_literals

from metanl.nltk_morphy import normalize_list, tag_and_stem
from nose.tools import eq_

def test_normalize_list():
    # Strip away articles, unless there's only an article
    eq_(normalize_list('the dog'), ['dog'])
    eq_(normalize_list('the'), ['the'])

    # strip out pluralization
    eq_(normalize_list('big dogs'), ['big', 'dog'])


def test_tag_and_stem():
    the_big_dogs = [(u'the', 'DT', u'the'),
                    (u'big', 'JJ', u'big'),
                    (u'dog', 'NNS', u'dogs')]
    eq_(tag_and_stem('the big dogs'), the_big_dogs)

    the_big_hashtag = [(u'the', 'DT', u'the'),
                       (u'#', 'NN', u'#'),
                       (u'big', 'JJ', u'big'),
                       (u'dog', 'NN', u'dog')]
    eq_(tag_and_stem('the #big dog'), the_big_hashtag)

    two_sentences = [(u'i', 'PRP', u'I'),
                     (u'can', 'MD', u'ca'),
                     (u'not', 'RB', u"n't"),
                     (u'.', '.', u'.'),
                     (u'avoid', 'NNP', u'Avoid'),
                     (u'fragment', 'NNS', u'fragments'),
                     (u'.', '.', u'.')]
    eq_(tag_and_stem("I can't. Avoid fragments."), two_sentences)

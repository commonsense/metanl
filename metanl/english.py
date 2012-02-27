# -*- coding: utf-8 -*-
import nltk
from nltk.corpus import wordnet
from metanl.general import (preprocess_text, tokenize, untokenize,
        tokenize_list, untokenize_list, un_camel_case)
from metanl.wordlist import Wordlist
import re

try:
    morphy = wordnet._morphy
except LookupError:
    nltk.download('wordnet')
    morphy = wordnet._morphy

STOPWORDS = ['the', 'a', 'an']

EXCEPTIONS = {
    # Avoid obsolete and obscure roots, the way lexicographers don't.
    'wrought': 'wrought',   # not 'work'
    'media': 'media',       # not 'medium'
    'installed': 'install', # not 'instal'
    'installing': 'install',# not 'instal'
    'synapses': 'synapse',  # not 'synapsis'
    'soles': 'sole',        # not 'sol'
    'pubes': 'pube',        # not 'pubis'
    'dui': 'dui',           # not 'duo'
    'taxis': 'taxi',        # not 'taxis'

    # Work around errors that Morphy makes.
    'alas': 'alas',
    'corps': 'corps',
    'cos': 'cos',
    'enured': 'enure',
    'fiver': 'fiver',
    'hinder': 'hinder',
    'lobed': 'lobe',
    'offerer': 'offerer',
    'outer': 'outer',
    'sang': 'sing',
    'singing': 'sing',
    'solderer': 'solderer',
    'tined': 'tine',
    'twiner': 'twiner',
    'us': 'us',

    # Stem common nouns whose plurals are apparently ambiguous
    'teeth': 'tooth',
    'things': 'thing',
    'people': 'person',

    # Tokenization artifacts
    'wo': 'will',
    'ca': 'can',
    "n't": 'not',
}

AMBIGUOUS_EXCEPTIONS = {
    # Avoid nouns that shadow more common verbs.
    'am': 'be',
    'as': 'as',
    'are': 'be',
    'ate': 'eat',
    'bent': 'bend',
    'drove': 'drive',
    'fell': 'fall',
    'felt': 'feel',
    'found': 'find',
    'has': 'have',
    'lit': 'light',
    'lost': 'lose',
    'sat': 'sit',
    'saw': 'see',
    'sent': 'send',
    'shook': 'shake',
    'shot': 'shoot',
    'slain': 'slay',
    'spoke': 'speak',
    'stole': 'steal',
    'sung': 'sing',
    'thought': 'think',
    'tore': 'tear',
    'was': 'be',
    'won': 'win',
}

def _word_badness(word):
    if word.endswith('e'):
        return len(word) - 2
    elif word.endswith('ess'):
        return len(word) - 10
    elif word.endswith('ss'):
        return len(word) - 4
    else:
        return len(word)

def morphy_best(word, pos=None):
    results = []
    if pos is None:
        pos = 'nvar'
    for pos_item in pos:
        results.extend(morphy(word, pos_item))
    if not results:
        return None
    results.sort(key=lambda x: _word_badness(x))
    return results[0]

def morphy_stem(word, pos=None):
    word = word.lower()
    if pos is not None:
        if pos.startswith('NN'):
            pos = 'n'
        elif pos.startswith('VB'):
            pos = 'v'
        elif pos.startswith('JJ'):
            pos = 'a'
        elif pos.startswith('RB'):
            pos = 'r'
    if pos is None and word.endswith('ing') or word.endswith('ed'):
        pos = 'v'
    if pos is not None and pos not in 'nvar':
        pos = None
    if word in EXCEPTIONS:
        return EXCEPTIONS[word]
    if pos is None:
        if word in AMBIGUOUS_EXCEPTIONS:
            return AMBIGUOUS_EXCEPTIONS[word]
    return morphy_best(word, pos) or word

def tag_and_stem(text):
    """
    Returns a list of (stem, tag, token) triples:

    - stem: the word's uninflected form
    - tag: the word's part of speech
    - token: the original word, so we can reconstruct it later
    """
    tokens = tokenize(preprocess_text(text))
    tagged = nltk.pos_tag(tokens)
    out = []
    for token, tag in tagged:
        if token.startswith('#'):
            out.append((token, 'TAG', token))
        else:
            stem = morphy_stem(token, tag)
            out.append((stem, tag, token))
    return out

def good_lemma(lemma):
    return lemma and lemma not in STOPWORDS and lemma[0].isalnum()

def normalize_list(text):
    pieces = [morphy_stem(word) for word in tokenize_list(text)]
    pieces = [piece for piece in pieces if good_lemma(piece)]
    if not pieces:
        return text
    if pieces[0] == 'to':
        pieces = pieces[1:]
    return pieces

def normalize(text):
    return untokenize_list(normalize_list(text))

def normalize_topic(topic):
    # find titles of the form Foo (bar)
    topic = topic.replace('_', ' ')
    match = re.match(r'([^(]+) \(([^)]+)\)', topic)
    if not match:
        return normalize(topic), None
    else:
        return normalize(match.group(1)), 'n/'+match.group(2).strip(' _')

def word_frequency(word):
    freqs = Wordlist.load('google-unigrams.txt')
    return freqs.get(word)

if __name__ == '__main__':
    print normalize("this is a test")


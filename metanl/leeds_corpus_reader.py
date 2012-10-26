import codecs
from collections import defaultdict
from ftfy import ftfy
import re

NUMBER_RE = re.compile('[0-9]+')

def leeds_corpus_frequencies(corpusfile, stemmer):
    if stemmer is None:
        stemmer = lambda x: x

    infile = codecs.open(corpusfile, encoding='utf-8')

    freqs = defaultdict(int)
    tokenfreqs = defaultdict(int)
    for line in infile:
        line = ftfy(line.strip())
        if line:
            rank = line.split(' ')[0]
            if NUMBER_RE.match(rank) and line.count(' ') == 2:
                rank, freq, token = line.split(' ')
                stemmed = stemmer(token)
                print "%s -> %s" % (token, stemmed)
                freq = float(freq)
                freq_int = int(freq*100)
                for word in stemmed.split(' '):
                    if ',' not in word:
                        freqs[word] += freq_int
                if ',' not in token:
                    tokenfreqs[token.lower()] += freq_int
    for key in tokenfreqs:
        if tokenfreqs[key] > freqs[key]:
            freqs[key] = tokenfreqs[key]
    return freqs

def translate_leeds_corpus(infile, outfile, stemmer):
    out = codecs.open(outfile, 'w', encoding='utf-8')
    freqs = leeds_corpus_frequencies(infile, stemmer)
    items = freqs.items()
    items.sort(key=lambda x: -x[1])
    for token, freq_int in items:
        print >> out, u"%s,%d" % (token, freq_int)
        print u"%s,%d" % (token, freq_int)

    out.close()


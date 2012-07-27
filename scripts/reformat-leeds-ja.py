import codecs
from metanl import japanese
from collections import defaultdict

infile = codecs.open('leeds/internet-ja-forms.num', encoding='utf-8')
outfile = codecs.open('../metanl/data/leeds-internet-ja.txt', 'w', encoding='utf-8')

freqs = defaultdict(int)

for line in infile:
    line = line.strip()
    if line:
        rank, freq, token = line.split(' ')
        token = japanese.normalize(token)
        freq = float(freq)
        freq_int = int(freq*100)
        for word in token.split(' '):
            if ',' not in word:
                freqs[word] += freq_int

items = freqs.items()
items.sort(key=lambda x: -x[1])
for token, freq_int in items:
    print >> outfile, u"%s,%d" % (token, freq_int)
    print u"%s,%d" % (token, freq_int)

outfile.close()

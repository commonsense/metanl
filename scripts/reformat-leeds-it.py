import codecs
from simplenlp import get_nl
infile = codecs.open('leeds-internet-it.num', encoding='utf-8')
outfile = codecs.open('../metanl/data/leeds-internet-it.txt', 'w', encoding='utf-8')
it_nl = get_nl('it')

for line in infile:
    line = line.strip()
    if line:
        rank, freq, token = line.split(' ')
        token = it_nl.normalize(token)
        freq = float(freq)
        freq_int = int(freq*100)
        if ',' not in token:
            print >> outfile, u"%s,%d" % (token, freq_int)
            print u"%s,%d" % (token, freq_int)
outfile.close()

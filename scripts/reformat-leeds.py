import codecs
infile = codecs.open('leeds-internet-ja.num', encoding='utf-8')
outfile = codecs.open('../metanl/data/leeds-internet-ja.txt', 'w', encoding='utf-8')

for line in infile:
    line = line.strip()
    if line:
        rank, freq, token = line.split(' ')
        freq = float(freq)
        freq_int = int(freq*100)
        if ',' not in token:
            print >> outfile, u"%s,%d" % (token, freq_int)
            print u"%s,%d" % (token, freq_int)
outfile.close()
